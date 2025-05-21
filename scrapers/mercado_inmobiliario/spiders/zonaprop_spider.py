import scrapy
from scrapy.exceptions import CloseSpider
import logging
import time
import random
import os
from urllib.parse import urlparse

class ZonapropSpider(scrapy.Spider):
    name = 'zonaprop_spider'
    allowed_domains = ['zonaprop.com.ar']
    start_urls = ['https://zonaprop.com.ar/departamentos-alquiler-flores.html']
    
    max_pages = 20
    pages_visited = 0
    debug_enabled = False  # Deshabilitar debug por defecto
    properties_found = 0

    def __init__(self, *args, **kwargs):
        super(ZonapropSpider, self).__init__(*args, **kwargs)
        if 'max_pages' in kwargs:
            self.max_pages = int(kwargs.get('max_pages'))
        if 'start_url' in kwargs:
            self.start_urls = [kwargs.get('start_url')]
        
        # Crear directorio de debug solo una vez
        self.debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'debug')
        
        # Configuración para reducir la cantidad de archivos debug
        self.save_debug_every_n_pages = 5  # Solo guardar debug cada N páginas
        self.save_properties_debug = False  # No guardar debug de páginas de propiedades

    def parse(self, response):
        self.pages_visited += 1
        
        # Verificar si fuimos bloqueados o hay un desafío de Cloudflare
        if response.status in [403, 429]:
            self.logger.error(f"Acceso bloqueado con código {response.status}. URL: {response.url}")
            yield {
                'url': response.url,
                'error': f"Error {response.status} - Acceso denegado",
                'fecha_extraccion': time.strftime('%Y-%m-%d'),
                'fuente': 'ZonaProp',
            }
            return
        
        # Verificar si estamos en un desafío de Cloudflare
        if "Just a moment" in response.text or "Cloudflare" in response.text:
            self.logger.warning(f"Posible desafío de Cloudflare en {response.url}")
            return
            
        # Solo guardar debug para algunas páginas para reducir sobrecarga
        if self.pages_visited % self.save_debug_every_n_pages == 1:
            os.makedirs(self.debug_dir, exist_ok=True)
            debug_file = os.path.join(self.debug_dir, f"zonaprop_page_{self.pages_visited}.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.info(f"HTML guardado en {debug_file} para diagnóstico")

        # Extraer enlaces a propiedades - Selectores optimizados basados en el HTML actual
        property_links = []
        
        # Reducir cantidad de selectores para mayor eficiencia, usando los más efectivos
        main_selectors = [
            '//div[contains(@class, "postingCard-module__posting-description")]/a/@href',
            '//h3[contains(@class, "postingCard-module__posting-description")]/a/@href',
            '//div[contains(@class, "postingCardLayout-module__posting-card-layout")]/@data-to-posting',
            '//div[contains(@data-qa, "posting PROPERTY")]/@data-to-posting'
        ]
        
        # Probar con cada selector principal
        for selector in main_selectors:
            links = response.xpath(selector).getall()
            if links:
                property_links.extend(links)
                self.logger.debug(f"Selector exitoso: {selector} - Encontrados: {len(links)}")
        
        # Si no se encontró nada, intentar con selectores secundarios
        if not property_links:
            backup_selectors = [
                '//a[contains(@href, "propiedades/clasificado")]/@href',
                '//div[contains(@class, "postingsList-module__card-container")]//a/@href'
            ]
            for selector in backup_selectors:
                links = response.xpath(selector).getall()
                if links:
                    property_links.extend(links)

        # Eliminar duplicados y filtrar enlaces de propiedades
        seen = set()
        property_links = [x for x in property_links if not (x in seen or seen.add(x))]
        property_links = [link for link in property_links if 
                         not any(exclude in link for exclude in ['contacto', 'login', 'registro', 'ayuda', 'terminos', '#'])]

        self.properties_found += len(property_links)
        self.logger.info(f"Página {self.pages_visited}: Encontradas {len(property_links)} propiedades (Total: {self.properties_found})")

        # Procesar cada propiedad encontrada
        for link in property_links:
            if not link.startswith('http'):
                link = f"https://www.zonaprop.com.ar{link}" if link.startswith('/') else f"https://www.zonaprop.com.ar/{link}"
            
            # Reducir el delay entre propiedades para acelerar el proceso
            yield response.follow(link, callback=self.parse_property)

        # Buscar enlace a la página siguiente
        next_page_selectors = [
            '//a[@aria-label="Siguiente"]/@href',
            '//a[contains(@class, "pagination") and contains(text(), "Siguiente")]/@href',
            '//li[contains(@class, "pagination")]/a[contains(text(), "Siguiente") or contains(@rel, "next")]/@href',
            '//a[contains(@class, "pagination-next")]/@href'
        ]
        
        next_page = None
        for selector in next_page_selectors:
            next_page = response.xpath(selector).get()
            if next_page:
                break
            
        # Navegar a la siguiente página si existe y no hemos superado el límite
        if next_page and self.pages_visited < self.max_pages:
            self.logger.info(f"Navegando a la siguiente página: {next_page}")
            # Reducir el tiempo de espera para acelerar el proceso
            yield response.follow(next_page, callback=self.parse)
        else:
            self.logger.info(f"Finalizada la extracción después de {self.pages_visited} páginas, encontradas {self.properties_found} propiedades")

    def parse_property(self, response):
        # Extraer datos optimizando los selectores
        property_id = self.extract_property_id(response.url)
        
        # Extraer datos usando los mejores selectores basados en los debugs
        precio_principal, moneda = self.extract_price_and_currency(response)
        expensas = self.extract_expensas(response)
        direccion = self.extract_location(response)
        barrio_zona = self.extract_zone(response)
        superficie = self.extract_area(response)
        ambientes = self.extract_rooms(response)
        dormitorios = self.extract_bedrooms(response)
        baños = self.extract_bathrooms(response)
        descripcion = self.extract_description(response)
                
        item = {
            'id_propiedad': property_id,
            'precio': precio_principal.strip() if precio_principal else None,
            'moneda': moneda,
            'expensas': expensas.strip() if expensas else None,
            'direccion': direccion.strip() if direccion else None,
            'barrio_zona': barrio_zona.strip() if barrio_zona else None,
            'superficie': superficie.strip() if superficie else None,
            'ambientes': ambientes.strip() if ambientes else None,
            'dormitorios': dormitorios.strip() if dormitorios else None,
            'baños': baños.strip() if baños else None,
            'descripcion': descripcion[:500] if descripcion else None,
            'url': response.url,
            'fecha_extraccion': time.strftime('%Y-%m-%d'),
            'fuente': 'ZonaProp',
        }
        
        # Registrar si falta información clave para depuración
        if not precio_principal or not direccion or not barrio_zona:
            self.logger.debug(f"Datos incompletos para URL: {response.url}")
        
        yield item

    def extract_property_id(self, url):
        """Extrae el ID de la propiedad desde la URL"""
        try:
            # Método más directo para extraer ID
            if '-' in url:
                parts = url.strip('/').split('-')
                last_part = parts[-1]
                if last_part.isdigit():
                    return last_part
                
            # Método alternativo
            parsed_url = urlparse(url)
            path = parsed_url.path
            if path.endswith('.html'):
                path = path[:-5]
            parts = path.split('-')
            for part in parts:
                if part.isdigit() and len(part) > 5:
                    return part
        except:
            pass
        return None
    
    def extract_price_and_currency(self, response):
        """Extrae el precio y la moneda"""
        # Selectores más precisos basados en los debugs analizados
        precio_selectors = [
            '//div[contains(@class, "postingPrices-module__price") and @data-qa="POSTING_CARD_PRICE"]/text()',
            '//div[contains(@class, "postingPrices-module__precio")]/text()',
            '//div[@data-qa="POSTING_CARD_PRICE"]/text()'
        ]
        
        precio_principal = None
        moneda = None
        
        # Intentar con XPath
        for selector in precio_selectors:
            precio_principal = response.xpath(selector).get()
            if precio_principal:
                precio_principal = precio_principal.strip()
                if 'USD' in precio_principal or 'U$S' in precio_principal or 'U$D' in precio_principal:
                    moneda = 'USD'
                elif '$' in precio_principal:
                    moneda = 'ARS'
                break
        
        return precio_principal, moneda
    
    def extract_expensas(self, response):
        """Extrae el valor de las expensas"""
        expensas_selectors = [
            '//div[contains(@class, "postingPrices-module__expenses") and @data-qa="expensas"]/text()',
            '//div[contains(@class, "postingPrices-module__expenses-property-listing")]/text()'
        ]
        
        expensas = None
        for selector in expensas_selectors:
            expensas = response.xpath(selector).get()
            if expensas:
                expensas = expensas.strip()
                break
        
        return expensas
    
    def extract_location(self, response):
        """Extrae la dirección de la propiedad"""
        direccion_selectors = [
            '//div[contains(@class, "postingLocations-module__location-address-in-listing")]/text()',
            '//div[contains(@class, "postingLocations-module__location-address")]/text()'
        ]
        
        direccion = None
        for selector in direccion_selectors:
            direccion = response.xpath(selector).get()
            if direccion:
                direccion = direccion.strip()
                break
        
        return direccion
    
    def extract_zone(self, response):
        """Extrae el barrio o zona de la propiedad"""
        barrio_selectors = [
            '//h2[contains(@class, "postingLocations-module__location-text") and @data-qa="POSTING_CARD_LOCATION"]/text()',
            '//h2[contains(@class, "postingLocations-module__location-text")]/text()'
        ]
        
        barrio_zona = None
        for selector in barrio_selectors:
            barrio_zona = response.xpath(selector).get()
            if barrio_zona:
                barrio_zona = barrio_zona.strip()
                break
        
        return barrio_zona
    
    def extract_area(self, response):
        """Extrae la superficie total de la propiedad"""
        superficie_selectors = [
            '//span[contains(@class, "postingMainFeatures-module__posting-main-features-span") and contains(text(), "m² tot")]/text()',
            '//h3[contains(@class, "postingMainFeatures-module__posting-main-features-block")]//span[contains(text(), "m² tot")]/text()'
        ]
        
        superficie = None
        for selector in superficie_selectors:
            superficie = response.xpath(selector).get()
            if superficie:
                superficie = superficie.strip()
                break
        
        return superficie
    
    def extract_rooms(self, response):
        """Extrae cantidad de ambientes"""
        ambientes_selectors = [
            '//span[contains(@class, "postingMainFeatures-module__posting-main-features-span") and contains(text(), "amb")]/text()',
            '//h3[contains(@class, "postingMainFeatures-module__posting-main-features-block")]//span[contains(text(), "amb")]/text()'
        ]
        
        ambientes = None
        for selector in ambientes_selectors:
            ambientes = response.xpath(selector).get()
            if ambientes:
                ambientes = ambientes.strip()
                break
        
        return ambientes
    
    def extract_bedrooms(self, response):
        """Extrae cantidad de dormitorios"""
        dormitorios_selectors = [
            '//span[contains(@class, "postingMainFeatures-module__posting-main-features-span") and contains(text(), "dorm")]/text()',
            '//h3[contains(@class, "postingMainFeatures-module__posting-main-features-block")]//span[contains(text(), "dorm")]/text()'
        ]
        
        dormitorios = None
        for selector in dormitorios_selectors:
            dormitorios = response.xpath(selector).get()
            if dormitorios:
                dormitorios = dormitorios.strip()
                break
        
        return dormitorios
    
    def extract_bathrooms(self, response):
        """Extrae cantidad de baños"""
        baños_selectors = [
            '//span[contains(@class, "postingMainFeatures-module__posting-main-features-span") and contains(text(), "baño")]/text()',
            '//h3[contains(@class, "postingMainFeatures-module__posting-main-features-block")]//span[contains(text(), "baño")]/text()'
        ]
        
        baños = None
        for selector in baños_selectors:
            baños = response.xpath(selector).get()
            if baños:
                baños = baños.strip()
                break
        
        return baños
    
    def extract_description(self, response):
        """Extrae la descripción de la propiedad"""
        descripcion_selectors = [
            '//h3[contains(@class, "postingCard-module__posting-description")]//a/text()',
            '//div[contains(@class, "postingCard-module__posting-description")]/a/text()',
            '//p[contains(@class, "description")]/text()'
        ]
        
        descripcion_items = []
        for selector in descripcion_selectors:
            items = response.xpath(selector).getall()
            if items:
                descripcion_items.extend(items)
                
        if descripcion_items:
            return ' '.join([d.strip() for d in descripcion_items])
            
        return None