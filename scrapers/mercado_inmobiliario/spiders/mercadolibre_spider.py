import scrapy
import re
import logging
from datetime import datetime

class MercadolibreSpider(scrapy.Spider):
    name = 'mercadolibre'
    allowed_domains = ['mercadolibre.com.ar']
    
    # URLs para departamentos en venta en Buenos Aires Capital
    start_urls = [
        'https://www.mercadolibre.com.ar/departamentos-venta-capital-federal.html',
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
            price_text = response.css('div.price-container span.price::text').get()
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
            
            # Extraer características
            features = {}
            feature_items = response.css('ul.main-features li')
            for item in feature_items:
                feature_text = ' '.join(item.css('*::text').getall()).strip()
                if 'dormitorio' in feature_text.lower() or 'ambiente' in feature_text.lower():
                    features['dormitorios'] = self.extract_numbers(feature_text)
                elif 'baño' in feature_text.lower():
                    features['banos'] = self.extract_numbers(feature_text)
                elif 'm² totales' in feature_text.lower():
                    features['superficie_total'] = self.extract_numbers(feature_text)
                elif 'm² cubiertos' in feature_text.lower():
                    features['superficie_cubierta'] = self.extract_numbers(feature_text)
            
            # Extraer ubicación
            location = response.css('h2.title-location::text').get()
            neighborhood = None
            district = None
            
            if location:
                location_parts = location.strip().split(',')
                if len(location_parts) >= 1:
                    neighborhood = location_parts[0].strip()
                if len(location_parts) >= 2:
                    district = location_parts[1].strip()
            
            # Extraer tipo de propiedad
            property_type = response.css('div.title-container h3.title::text').get()
            if property_type:
                property_type = property_type.strip()
            
            # Extraer amenities
            amenities = []
            amenities_items = response.css('div.amenities ul.amenities-list li')
            for item in amenities_items:
                amenity = item.css('::text').get()
                if amenity:
                    amenities.append(amenity.strip())
            
            # Extraer descripción
            description = ' '.join(response.css('div.description-container p::text').getall())
            if description:
                description = description.strip()
            
            # Fecha de extracción
            extraction_date = datetime.now().strftime('%Y-%m-%d')
            
            # Generar el item final
            yield {
                'url': response.url,
                'titulo': response.css('div.title-container h3.title::text').get().strip(),
                'tipo_propiedad': property_type,
                'precio': price,
                'moneda': currency,
                'barrio': neighborhood,
                'distrito': district,
                'dormitorios': features.get('dormitorios'),
                'banos': features.get('banos'),
                'superficie_total': features.get('superficie_total'),
                'superficie_cubierta': features.get('superficie_cubierta'),
                'amenities': amenities,
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
