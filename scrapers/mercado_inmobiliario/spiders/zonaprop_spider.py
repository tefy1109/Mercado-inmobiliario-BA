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
    
    custom_settings = {
        'DOWNLOAD_DELAY': 7,  # Mayor delay
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        # Desactivar cache para evitar problemas con 403
        'HTTPCACHE_ENABLED': False,
        # Más intentos de retry
        'RETRY_TIMES': 8,
        # Headers personalizados
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
    }

    def start_requests(self):
        """Método para iniciar las solicitudes"""
        for url in self.start_urls:
            # Usar Google como referer para la primera solicitud
            headers = {
                'Referer': 'https://www.google.com/search?q=alquiler+departamentos+flores+zonaprop',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            }
            
            # Añadir cookies que simulan navegación previa
            cookies = {
                'visita_id': str(random.randint(1000000, 9999999)),
                'c_user_id': str(random.randint(1000000, 9999999)),
                'c_visitor_id': str(random.randint(1000000, 9999999)),
                'gdpr': 'true',
                '_ga': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
                '_gid': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
            }
            
            # Simulamos que venimos de Google
            self.logger.info(f"Iniciando solicitud a {url} con referer de Google")
            yield scrapy.Request(
                url=url, 
                callback=self.parse,
                headers=headers,
                cookies=cookies,
                meta={'cookiejar': 1},  # Usar un cookiejar para mantener las cookies
                dont_filter=True
            )

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
                
                # Dirección
                address_element = container.css('div.postingCard-module__location::text').get()
                item['direccion'] = address_element.strip() if address_element else None
                
                # Zona hardcodeada como "Flores" según tu ejemplo
                item['zona'] = 'Flores'
                
                # Características de la propiedad (superficie, ambientes, habitaciones, baños)
                features = container.css('h3 span::text').getall()
                
                # Inicializar valores por defecto
                item['superficie'] = None
                item['ambientes'] = None
                item['habitaciones'] = None
                item['banos'] = None
                
                # Procesar las características en orden
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
                
                # Descripción/Título
                description_element = container.css('h3 a::text').get()
                item['descripcion'] = description_element.strip() if description_element else None
                
                # URL de la propiedad (opcional, para referencia)
                property_url = container.css('h3 a::attr(href)').get()
                item['url'] = urljoin(response.url, property_url) if property_url else None
                
                yield item
                
            except Exception as e:
                self.logger.error(f"Error procesando propiedad: {e}")
                continue
            
            # Sleep aleatorio entre ítems para parecer más humano
            time.sleep(random.uniform(0.5, 2.0))
        
        # Paginación con delay adicional para parecer más humano
        next_page = response.css('a.pagination-module__next::attr(href)').get()
        if next_page:
            self.logger.info(f"Siguiente página encontrada: {next_page}")
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
                next_page, 
                callback=self.parse, 
                headers=headers,
                meta={'cookiejar': response.meta.get('cookiejar')},  # Mantener las cookies
                dont_filter=True  # No filtrar URLs duplicadas
            )