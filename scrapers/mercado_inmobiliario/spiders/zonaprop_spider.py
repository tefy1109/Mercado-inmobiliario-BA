import scrapy
import re
import random
import time
from urllib.parse import urljoin


class ZonapropSpider(scrapy.Spider):
    name = 'zonaprop_spider'
    allowed_domains = ['zonaprop.com.ar']
    start_urls = [
        'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html',
    ]
    
    def parse(self, response):
        """Extrae los datos de las propiedades desde la página principal"""
        # Debug - Guardar la respuesta para inspección
        with open('debug_response.html', 'wb') as f:
            f.write(response.body)
        
        self.logger.info(f"Status: {response.status}, URL: {response.url}")
        
        # Si obtenemos un 403, no podemos continuar
        if response.status == 403:
            self.logger.error("Recibimos un error 403 Forbidden. El sitio está bloqueando nuestras solicitudes.")
            return
            
        # Selector para los contenedores de propiedades
        property_containers = response.css('div.postingCard')
        self.logger.info(f"Encontrados {len(property_containers)} contenedores de propiedades")
        
        # Si no encontramos propiedades con el selector habitual, intentamos con otros selectores
        if not property_containers:
            property_containers = response.css('div[data-qa="posting PROPERTY"]')
            self.logger.info(f"Segundo intento: Encontrados {len(property_containers)} contenedores de propiedades")
        
        for container in property_containers:
            item = {}
            
            try:
                # Precio de alquiler
                price_element = container.css('div.postingCard-module__price-container div:first-child::text').get()
                if price_element:
                    # Limpia el precio (remueve $ y puntos)
                    price_clean = re.sub(r'[^\d]', '', price_element)
                    item['precio_alquiler'] = int(price_clean) if price_clean else None
                else:
                    item['precio_alquiler'] = None
                
                # Expensas
                expenses_element = container.css('div.postingCard-module__price-container div:nth-child(2)::text').get()
                if expenses_element:
                    expenses_clean = re.sub(r'[^\d]', '', expenses_element)
                    item['expensas'] = int(expenses_clean) if expenses_clean else None
                else:
                    item['expensas'] = None
                
                # Dirección - Utilizando el selector proporcionado
                address_element = container.css('div.postingCard-module__posting-container div.postingCard-module__posting-top div:nth-child(1) div:nth-child(2) div div::text').get()
                if not address_element:
                    # Selector alternativo si el primero no funciona
                    address_element = container.css('div.postingCard-module__location::text').get()
                
                item['direccion'] = address_element.strip() if address_element else None
                self.logger.info(f"Dirección extraída: {item['direccion']}")
                
                # Zona hardcodeada como "Flores" según tu ejemplo
                # Extraer el barrio de la URL como alternativa
                barrio_match = re.search(r'-alquiler-([^\.]+)\.html', response.url)
                item['zona'] = barrio_match.group(1).capitalize() if barrio_match else 'Flores'
                
                # Características de la propiedad (superficie, ambientes, habitaciones, baños)
                # Apuntamos al contenedor h3 que contiene los spans con las características
                feature_container = container.css('div.postingCard-module__posting-container div.postingCard-module__posting-top div.postingCard-module__posting-card-row h3')
                
                # Inicializar valores por defecto
                item['superficie'] = None
                item['ambientes'] = None
                item['habitaciones'] = None
                item['banos'] = None
                
                # Si encontramos el contenedor, extraemos los spans
                if feature_container:
                    # Extraer todos los spans dentro del h3
                    feature_spans = feature_container.css('span::text').getall()
                    self.logger.info(f"Features encontradas: {feature_spans}")
                    
                    # Procesar cada característica encontrada
                    for i, feature in enumerate(feature_spans):
                        feature_clean = feature.strip()
                        
                        # Superficie (m²)
                        if 'm²' in feature_clean:
                            surface_match = re.search(r'(\d+)', feature_clean)
                            item['superficie'] = int(surface_match.group(1)) if surface_match else None
                        
                        # Ambientes
                        elif 'amb' in feature_clean.lower():
                            amb_match = re.search(r'(\d+)', feature_clean)
                            ambientes = int(amb_match.group(1)) if amb_match else None
                            item['ambientes'] = ambientes
                            
                            # Si ambientes = 1, entonces habitaciones = 0
                            if ambientes == 1:
                                item['habitaciones'] = 0
                        
                        # Habitaciones/Dormitorios
                        elif 'dorm' in feature_clean.lower() or 'hab' in feature_clean.lower():
                            hab_match = re.search(r'(\d+)', feature_clean)
                            item['habitaciones'] = int(hab_match.group(1)) if hab_match else None
                        
                        # Baños
                        elif 'baño' in feature_clean.lower():
                            bath_match = re.search(r'(\d+)', feature_clean)
                            item['banos'] = int(bath_match.group(1)) if bath_match else None
                
                # Si no hemos encontrado la información con el método anterior, 
                # intentamos con el método original como fallback
                if all(v is None for v in [item['superficie'], item['ambientes'], item['habitaciones'], item['banos']]):
                    features = container.css('h3 span::text').getall()
                    
                    # Procesar las características en orden (método original)
                    for i, feature in enumerate(features):
                        feature_clean = feature.strip()
                        
                        if i == 0:  # Superficie
                            surface_match = re.search(r'(\d+)', feature_clean)
                            item['superficie'] = int(surface_match.group(1)) if surface_match else None
                        
                        elif i == 1:  # Ambientes
                            amb_match = re.search(r'(\d+)', feature_clean)
                            ambientes = int(amb_match.group(1)) if amb_match else None
                            item['ambientes'] = ambientes
                            
                            # Si ambientes = 1, entonces habitaciones = 0
                            if ambientes == 1:
                                item['habitaciones'] = 0
                        
                        elif i == 2:  # Habitaciones (solo si ambientes != 1)
                            if item['ambientes'] != 1:
                                hab_match = re.search(r'(\d+)', feature_clean)
                                item['habitaciones'] = int(hab_match.group(1)) if hab_match else None
                        
                        elif i == 3:  # Baños
                            bath_match = re.search(r'(\d+)', feature_clean)
                            item['banos'] = int(bath_match.group(1)) if bath_match else None
                
                # Descripción/Título - Usando el selector específico proporcionado
                description_element = container.css('div.postingCard-module__posting-container div.postingCard-module__posting-top h3 a::text').get()
                if not description_element:
                    # Selector alternativo si el primero no funciona
                    description_element = container.css('h3 a::text').get()
                
                item['descripcion'] = description_element.strip() if description_element else None
                self.logger.info(f"Descripción extraída: {item['descripcion']}")
                
                # URL de la propiedad (opcional, para referencia) - Usando el mismo selector para a href
                property_url = container.css('div.postingCard-module__posting-container div.postingCard-module__posting-top h3 a::attr(href)').get()
                if not property_url:
                    # Selector alternativo si el primero no funciona
                    property_url = container.css('h3 a::attr(href)').get()
                
                item['url'] = urljoin(response.url, property_url) if property_url else None
                
                # Si conseguimos extraer los datos básicos, consideramos que la propiedad es válida
                if item['descripcion'] and (item['precio_alquiler'] is not None or item['direccion']):
                    yield item
                else:
                    self.logger.warning(f"Propiedad descartada por falta de datos básicos: {item}")
                
            except Exception as e:
                self.logger.error(f"Error procesando propiedad: {e}")
                continue
            
            # Sleep aleatorio entre ítems para parecer más humano
            time.sleep(random.uniform(0.5, 2.0))
        
        # Paginación con delay adicional para parecer más humano
        # Intenta encontrar la página actual usando el selector proporcionado
        current_page_element = response.css('a.paging-module__page-item.paging-module__page-item-current::text').get()
        if not current_page_element:
            # Si no encuentra el elemento con ese selector, intenta con otros o extrae de la URL
            current_page_match = re.search(r'pagina-(\d+)', response.url)
            current_page = int(current_page_match.group(1)) if current_page_match else 1
        else:
            current_page = int(current_page_element.strip())
        
        next_page = current_page + 1
        self.logger.info(f"Página actual: {current_page}, Siguiente página: {next_page}")
        
        # Construir la URL para la siguiente página según el patrón observado
        next_page_url = f'https://www.zonaprop.com.ar/departamentos-alquiler-flores-pagina-{next_page}.html'
        
        # Verificar si existe el botón de siguiente página o si estamos en la última
        next_button = response.css('a.pagination-module__next')
        # Si hay un botón de siguiente o estamos en una página con contenido válido
        if next_button or len(property_containers) > 0:
            self.logger.info(f"Navegando a la siguiente página: {next_page_url}")
            # Delay aleatorio antes de ir a la siguiente página
            time.sleep(random.uniform(5.0, 10.0))
            
            headers = {
                'Referer': response.url,  # La página actual como referer
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0'
                ])
            }
            
            yield response.follow(
                next_page_url, 
                callback=self.parse, 
                headers=headers,
                meta={'cookiejar': response.meta.get('cookiejar')},  # Mantener las cookies
                dont_filter=True  # No filtrar URLs duplicadas
            )
        else:
            self.logger.info("Llegamos al final de las páginas disponibles")