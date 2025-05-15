import scrapy
import re
import logging
from datetime import datetime

class MercadolibreSpider(scrapy.Spider):
    name = 'mercadolibre'
    allowed_domains = ['mercadolibre.com.ar']
    
    # URLs para departamentos en venta en Buenos Aires Capital
    start_urls = [
        'https://inmuebles.mercadolibre.com.ar/departamentos/venta/capital-federal/',
    ]
    
    # Configurar número máximo de páginas a scrapear (para desarrollo)
    max_pages = 50
    current_page = 1
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  # Tiempo entre solicitudes para evitar bloqueos
        'ROBOTSTXT_OBEY': True
    }
    
    def __init__(self, max_pages=None, *args, **kwargs):
        super(MercadolibreSpider, self).__init__(*args, **kwargs)
        if max_pages:
            self.max_pages = int(max_pages)
        self.logger.info(f"Spider inicializado con max_pages={self.max_pages}")
    
    def parse(self, response):
        # Extraer listado de propiedades - selector actualizado más flexible
        property_listings = response.css('ol.ui-search-layout li.ui-search-layout__item, div.ui-search-results div[class*="ui-search-result"]')
        
        self.logger.info(f"Encontradas {len(property_listings)} propiedades en {response.url}")
        
        for listing in property_listings:
            # Obtener la URL del detalle de la propiedad - selector actualizado
            detail_url = listing.css('a.ui-search-result__content::attr(href), a.ui-search-link::attr(href)').get()
            if detail_url:
                # Llamar a la página de detalle para obtener información completa
                self.logger.info(f"Siguiendo: {detail_url}")
                yield response.follow(detail_url, callback=self.parse_property)
        
        # Paginación: ir a la siguiente página si existe y no hemos llegado al límite
        if self.current_page < self.max_pages:
            next_page = response.css('a.andes-pagination__link[title="Siguiente"]::attr(href), a.ui-search-link[title="Siguiente"]::attr(href), li.andes-pagination__button--next a::attr(href)').get()
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
            price_text = response.css('span.andes-money-amount__fraction::text, span.price-tag-fraction::text').get()
            currency_text = response.css('span.andes-money-amount__currency-symbol::text, span.price-tag-symbol::text').get()
            
            self.logger.debug(f"Precio encontrado: {price_text}, Moneda: {currency_text}")
            
            currency = None
            price = None
            
            if price_text:
                price = self.extract_numbers(price_text)
                
            if currency_text:
                currency_text = currency_text.strip().upper()
                if 'U$S' in currency_text or 'USD' in currency_text:
                    currency = 'USD'
                elif '$' in currency_text or 'ARS' in currency_text or 'PESOS' in currency_text:
                    currency = 'ARS'
            
            # Extraer características - selectores más flexibles
            features = {}
            
            # Métodos de extracción de características
            # 1. Desde las especificaciones destacadas
            feature_items = response.css('div.ui-vip-highlighted-specs__specs-item, div[class*="highlighted-specs"] div[class*="specs-item"]')
            for item in feature_items:
                label = item.css('p[class*="key-text"]::text, span[class*="label"]::text').get()
                value = item.css('p[class*="value-text"]::text, span[class*="value"]::text').get()
                
                if label and value:
                    self.extract_feature(label, value, features)
            
            # 2. Desde la tabla de especificaciones
            spec_rows = response.css('div.ui-pdp-specs__table div.ui-pdp-specs__table-row, table[class*="specs"] tr')
            for row in spec_rows:
                label = row.css('th::text, td:first-child::text').get()
                value = row.css('td::text, td:last-child::text').get()
                
                if label and value:
                    self.extract_feature(label, value, features)
            
            # 3. Desde otros formatos comunes
            ambientes = response.xpath('//p[contains(text(), "ambiente") or contains(text(), "Ambiente")]/text()').get()
            if ambientes:
                features['ambientes'] = self.extract_numbers(ambientes)
            
            dormitorios = response.xpath('//p[contains(text(), "dormitorio") or contains(text(), "Dormitorio") or contains(text(), "habitación")]/text()').get()
            if dormitorios:
                features['dormitorios'] = self.extract_numbers(dormitorios)
                
            banos = response.xpath('//p[contains(text(), "baño") or contains(text(), "Baño")]/text()').get()
            if banos:
                features['banos'] = self.extract_numbers(banos)
            
            # Extraer ubicación - selector actualizado
            location = response.css('div.ui-vip-location p::text, div[class*="location"] p::text, h3[class*="location"]::text').get()
            neighborhood = None
            district = None
            
            if location:
                location_parts = location.strip().split(',')
                if len(location_parts) >= 1:
                    neighborhood = location_parts[0].strip()
                if len(location_parts) >= 2:
                    district = location_parts[1].strip()
            
            # Extraer tipo de propiedad - selector actualizado
            property_type = response.css('div.ui-pdp-header__subtitle::text, p[class*="subtitle"]::text').get()
            if property_type:
                property_type = property_type.strip()
            
            # Extraer descripción - selector actualizado
            description = ' '.join(
                response.css('div.ui-pdp-description__content p::text, div[class*="description"] p::text').getall() or \
                response.xpath('//div[contains(@class, "description")]//p//text()').getall()
            )
            
            if description:
                description = description.strip()
            
            # Fecha de extracción
            extraction_date = datetime.now().strftime('%Y-%m-%d')
            
            # Generar el item final
            yield {
                'url': response.url,
                'titulo': response.css('h1.ui-pdp-title::text').get().strip() if response.css('h1.ui-pdp-title::text').get() else "Sin título",
                'tipo_propiedad': property_type,
                'precio': price,
                'moneda': currency,
                'barrio': neighborhood,
                'distrito': district,
                'dormitorios': features.get('dormitorios'),
                'banos': features.get('banos'),
                'ambientes': features.get('ambientes'),
                'superficie_total': features.get('superficie_total'),
                'superficie_cubierta': features.get('superficie_cubierta'),
                'amenities': amenities,
                'descripcion': description,
                'fecha_extraccion': extraction_date,
                'fuente': 'mercadolibre'  # Corregido de 'zonaprop' a 'mercadolibre'
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando {response.url}: {str(e)}", exc_info=True)
    
    def extract_feature(self, label, value, features):
        """Extrae y categoriza características basadas en etiquetas"""
        if not label or not value:
            return
            
        label = label.lower().strip()
        value = value.strip()
        
        if any(term in label for term in ['dormitorio', 'habitacion', 'habitación', 'cuarto']):
            features['dormitorios'] = self.extract_numbers(value)
        elif any(term in label for term in ['baño', 'banio']):
            features['banos'] = self.extract_numbers(value)
        elif any(term in label for term in ['superficie total', 'área total', 'm² totales']):
            features['superficie_total'] = self.extract_numbers(value)
        elif any(term in label for term in ['superficie cubierta', 'área cubierta', 'm² cubiertos']):
            features['superficie_cubierta'] = self.extract_numbers(value)
        elif any(term in label for term in ['ambiente', 'ambientes']):
            features['ambientes'] = self.extract_numbers(value)
    
    def extract_numbers(self, text):
        """Extraer números de un texto"""
        if not text:
            return None
        numbers = re.findall(r'\d+[.,]?\d*', text)
        if numbers:
            # Convertir a float, reemplazando coma por punto si es necesario
            return float(numbers[0].replace(',', '.'))
        return None
