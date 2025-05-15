import scrapy
import re
import logging
from datetime import datetime
import random
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

class ZonapropSpider(scrapy.Spider):
    name = 'zonaprop'
    allowed_domains = ['zonaprop.com.ar']
    
    # URLs para departamentos en venta en Buenos Aires Capital
    start_urls = [
        'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html',
    ]
    
    # Configurar número máximo de páginas a scrapear (para desarrollo)
    max_pages = 50
    current_page = 1
    
    # Lista de user agents para rotación
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
    ]
    
    # Configuraciones personalizadas
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # Desactivar obediencia al robots.txt
        'DOWNLOAD_DELAY': 3,  # Aumentar el retraso entre solicitudes
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'COOKIES_ENABLED': True,  # Habilitar cookies
        'CONCURRENT_REQUESTS': 1,  # Reducir solicitudes concurrentes
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 5,  # Aumentar número de reintentos
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 522, 524, 408, 403, 429],  # Incluir 403 en códigos de reintento
        'HTTPERROR_ALLOWED_CODES': [403],  # Permitir código 403
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
    }
    
    def __init__(self, max_pages=None, *args, **kwargs):
        super(ZonapropSpider, self).__init__(*args, **kwargs)
        if max_pages:
            self.max_pages = int(max_pages)
        self.logger.info(f"Spider inicializado con max_pages={self.max_pages}")
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=self.get_headers())
    
    def get_headers(self):
        """Genera headers para simular un navegador real"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def parse(self, response):
        # Verificar si hemos sido bloqueados (código 403)
        if response.status == 403:
            self.logger.warning(f"Recibido código 403 para {response.url}. Intentando manejar...")
            # Podríamos implementar una lógica específica aquí si es necesario
            # Por ahora, confiaremos en el middleware de reintento
        
        # Extraer listado de propiedades - selector actualizado
        property_listings = response.css('div.postings-container .posting-card, div.postings-container .postingCard')
        self.logger.info(f"Encontradas {len(property_listings)} propiedades en {response.url}")
        
        for listing in property_listings:
            # Obtener la URL del detalle de la propiedad (selector actualizado)
            detail_url = listing.css('a.go-to-posting::attr(href), a.postingCard-link::attr(href)').get()
            if detail_url:
                # Asegurarse de que la URL sea absoluta
                if not detail_url.startswith('http'):
                    detail_url = response.urljoin(detail_url)
                # Llamar a la página de detalle para obtener información completa
                self.logger.info(f"Siguiendo: {detail_url}")
                yield response.follow(detail_url, callback=self.parse_property)
        
        # Paginación: ir a la siguiente página si existe y no hemos llegado al límite
        if self.current_page < self.max_pages:
            next_page = response.css('a.pagination__page-next::attr(href), li.pagination__next > a::attr(href)').get()
            if next_page:
                self.current_page += 1
                self.logger.info(f"Navegando a página {self.current_page}: {next_page}")
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("No se encontró siguiente página")

    def parse_property(self, response):
        """Extraer la información detallada de una propiedad"""
        try:
            self.logger.info(f"Procesando propiedad: {response.url}")
            
            # Extraer precio y moneda - selectores actualizados
            price_text = response.css('div.price-items span.first-price ::text').get() or \
                        response.xpath('//div[contains(@class, "price-container")]//span[contains(@class, "price")]//text()').get()
            
            currency = None
            price = None
            
            if price_text:
                price_text = price_text.strip()
                self.logger.debug(f"Precio encontrado: {price_text}")
                if 'U$S' in price_text or 'USD' in price_text:
                    currency = 'USD'
                    price = self.extract_numbers(price_text)
                elif '$' in price_text or 'ARS' in price_text:
                    currency = 'ARS'
                    price = self.extract_numbers(price_text)
            
            # Extraer características - selectores actualizados
            # Superficie total - actualizar selector para zonaprop
            superficie_total = response.css("span.main-features__item-value::text, span.main-features__attribute-value::text").get()
            
            # Superficie cubierta - actualizar selector para zonaprop
            superficie_cubierta = response.xpath("(//span[contains(@class, 'main-features__item-value') or contains(@class, 'main-features__attribute-value')])[2]/text()").get()
            
            # Ambientes - selector actualizado
            ambientes = response.xpath("//span[contains(@class, 'main-features') and contains(text(), 'amb') or contains(text(), 'amb.')]/text()").get()
            
            # Baños - selector actualizado
            banos = response.xpath("//span[contains(@class, 'main-features') and contains(text(), 'baño') or contains(text(), 'Baño')]/text()").get()
            
            # Dormitorios - selector actualizado
            dormitorios = response.xpath("//span[contains(@class, 'main-features') and contains(text(), 'dorm') or contains(text(), 'Dorm')]/text()").get()

            # Extraer ubicación - selector actualizado
            location_text = response.css("h2.title-location::text, div.location-container h2::text").get() or \
                           response.xpath("//div[contains(@class, 'location')]//h2//text()").get()
            
            location = None
            if location_text:
                location_text = location_text.strip()
                self.logger.debug(f"Ubicación encontrada: {location_text}")
                # Extraer solo la calle y número (antes de "piso", "," o cualquier otro separador)
                location_match = re.search(r'^(.*?)(?:piso|,|\s-)', location_text, re.IGNORECASE)
                if location_match:
                    location = location_match.group(1).strip()
                else:
                    location = location_text.strip()
            
            # Extraer título - selector actualizado
            titulo = response.css("div.title-container h1::text, h1.title::text").get()
            if titulo:
                titulo = titulo.strip()
            else:
                titulo = "Sin título"
            
            # Extraer amenities - selector actualizado
            amenities = []
            amenities_items = response.css('div.amenities ul li, section.amenities ul li')
            for item in amenities_items:
                amenity = item.css('::text').get()
                if amenity:
                    amenities.append(amenity.strip())
            
            # Extraer descripción completa - selector actualizado
            full_description = ' '.join(
                response.css('div.description-container p::text, div.description p::text').getall() or \
                response.xpath('//div[contains(@class, "description")]//p//text()').getall()
            )
            
            description = None
            if full_description:
                full_description = full_description.strip()
                # Buscar secciones típicas de condiciones
                conditions_patterns = [
                    r'(?:CONDICIONES|Condiciones|condiciones)[:\s]+(.*?)(?:\n\n|\Z)',
                    r'(?:REQUISITOS|Requisitos|requisitos)[:\s]+(.*?)(?:\n\n|\Z)',
                    r'(?:SE REQUIERE|Se requiere|se requiere)[:\s]+(.*?)(?:\n\n|\Z)',
                    r'(?:GARANTÍA|Garantía|garantía)[:\s]+(.*?)(?:\n\n|\Z)',
                ]
                
                for pattern in conditions_patterns:
                    match = re.search(pattern, full_description, re.DOTALL | re.IGNORECASE)
                    if match:
                        description = match.group(1).strip()
                        break
                
                # Si no se encontraron condiciones específicas, usar toda la descripción
                if not description:
                    description = full_description.strip()
            
            # Fecha de extracción
            extraction_date = datetime.now().strftime('%Y-%m-%d')
            
            # Generar el item final
            yield {
                'url': response.url,
                'titulo': titulo,
                'precio': price,
                'moneda': currency,
                'superficie_total': self.extract_numbers(superficie_total) if superficie_total else None,
                'superficie_cubierta': self.extract_numbers(superficie_cubierta) if superficie_cubierta else None,
                'ambientes': self.extract_numbers(ambientes) if ambientes else None,
                'banos': self.extract_numbers(banos) if banos else None,
                'dormitorios': self.extract_numbers(dormitorios) if dormitorios else None,
                'ubicacion': location,
                'amenities': amenities,
                'descripcion': description,
                'fecha_extraccion': extraction_date,
                'fuente': 'zonaprop'
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando {response.url}: {str(e)}", exc_info=True)
    
    def extract_numbers(self, text):
        """Extraer números de un texto"""
        if not text:
            return None
        numbers = re.findall(r'\d+[.,]?\d*', text)
        if numbers:
            # Convertir a float, reemplazando coma por punto si es necesario
            return float(numbers[0].replace(',', '.'))
        return None