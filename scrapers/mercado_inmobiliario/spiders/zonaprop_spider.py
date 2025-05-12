import scrapy
import re
import logging
from datetime import datetime

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
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  # Tiempo entre solicitudes para evitar bloqueos
        'ROBOTSTXT_OBEY': True
    }
    
    def parse(self, response):
        # Extraer listado de propiedades
        property_listings = response.css('div.postings-container div.posting-card')
        
        for listing in property_listings:
            # Obtener la URL del detalle de la propiedad
            detail_url = listing.css('a.go-to-posting::attr(href)').get()
            if detail_url:
                # Llamar a la página de detalle para obtener información completa
                yield response.follow(detail_url, callback=self.parse_property)
        
        # Paginación: ir a la siguiente página si existe y no hemos llegado al límite
        if self.current_page < self.max_pages:
            next_page = response.css('a.pagination__page-next::attr(href)').get()
            if next_page:
                self.current_page += 1
                yield response.follow(next_page, callback=self.parse)
    
    def parse_property(self, response):
        """Extraer la información detallada de una propiedad"""
        try:
            # Extraer precio y moneda
            price_text = response.xpath('//*[@id="article-container"]/div[1]/div/div[1]/span[1]/span::text').get()
            currency = None
            price = None
            
            if price_text:
                price_text = price_text.strip()
                if 'U$S' in price_text:
                    currency = 'USD'
                    price = self.extract_numbers(price_text)
                elif '$' in price_text:
                    currency = 'ARS'
                    price = self.extract_numbers(price_text)
                elif 'AR$' in price_text:
                    currency = 'ARS'
                    price = self.extract_numbers(price_text)
            
            # Extraer características
            def parse(self, response):
                # Extraer superficie total
                superficie_total = response.css("i.icon-stotal::text").get()
                
                # Superficie cubierta
                superficie_cubierta = response.css("i.icon-scubierta::text").get()
                
                # Ambientes
                ambientes = response.xpath("//li[contains(., 'amb.')]/text()").get()
                
                # Baños
                banos = response.xpath("//li[contains(., 'baño')]/text()").get()
                
                # Dormitorios
                dormitorios = response.xpath("//li[contains(., 'dorm.')]/text()").get()

                # Extraer ubicación
                location_text = response.xpath('//*[@id="map-section"]/div[1]/h4/text()').get()
                location = None
                if location_text:
                    # Extraer solo la calle y número (antes de "piso", "," o cualquier otro separador)
                    location_match = re.search(r'^(.*?)(?:piso|,|\s-)', location_text, re.IGNORECASE)
                    if location_match:
                        location = location_match.group(1).strip()
                    else:
                        location = location_text.strip()
                
                # Extraer amenities
                amenities = []
                amenities_items = response.css('div.amenities ul.amenities-list li')
                for item in amenities_items:
                    amenity = item.css('::text').get()
                    if amenity:
                        amenities.append(amenity.strip())
                
                # Extraer descripción, enfocándose en las condiciones
                full_description = ' '.join(response.xpath('//*[@id="longDescription"]/div//text()').getall())
                description = None

                if full_description:
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
                    'titulo': response.css('div.title-container h3.title::text').get().strip(),
                    'precio': price,
                    'moneda': currency,
                    'superficie_total': superficie_total,
                    'superficie_cubierta': superficie_cubierta,
                    'ambientes': ambientes,
                    'banos': banos,
                    'dormitorios': dormitorios,                    'amenities': amenities,
                    'descripcion': description,
                    'fecha_extraccion': extraction_date,
                    'fuente': 'zonaprop'
                }
                
        except Exception as e:
            logging.error(f"Error procesando {response.url}: {str(e)}")
    
    def extract_numbers(self, text):
        """Extraer números de un texto"""
        if not text:
            return None
        numbers = re.findall(r'\d+[.,]?\d*', text)
        if numbers:
            # Convertir a float, reemplazando coma por punto si es necesario
            return float(numbers[0].replace(',', '.'))
        return None