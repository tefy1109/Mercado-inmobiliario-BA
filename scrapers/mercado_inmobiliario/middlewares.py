# Define here the models for your spider middleware

from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message
from scrapy.http import HtmlResponse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
import random
import time

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

class RotateUserAgentMiddleware:
    """Middleware para rotar user agents"""
    
    def __init__(self, user_agents):
        self.user_agents = user_agents
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def from_crawler(cls, crawler):
        user_agents = crawler.settings.getlist('USER_AGENT_LIST')
        if not user_agents:
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            ]
        return cls(user_agents)
    
    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        
        # Añadir más headers para simular un navegador real
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Chromium";v="123", "Google Chrome";v="123"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        })
        
        # Referrer aleatorio para parecer tráfico más natural
        referrers = [
            'https://www.google.com/search?q=alquileres+en+buenos+aires',
            'https://www.bing.com/search?q=departamentos+alquiler+zona+norte',
            'https://ar.yahoo.com/search?p=alquileres+baratos+buenos+aires',
            'https://www.facebook.com/',
            'https://www.instagram.com/',
        ]
        request.headers['Referer'] = random.choice(referrers)
        self.logger.debug(f"Request {request.url} usando User-Agent: {user_agent}")
        return None

class CustomRetryMiddleware(RetryMiddleware):
    """Middleware personalizado para reintentos con retrasos adaptables"""
    
    def __init__(self, crawler):
        super(CustomRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_response(self, request, response, spider):
        if response.status in [403, 429]:
            self.logger.warning(f"Recibido código {response.status} para {response.url}")
            
            # Guardar una copia de la respuesta para debugging
            filename = f"error_{response.status}_{int(time.time())}.html"
            with open(filename, 'wb') as f:
                f.write(response.body)
            self.logger.info(f"Respuesta guardada en {filename}")
            
            # Esperar un tiempo más largo entre reintentos
            delay = random.uniform(20, 60)
            self.logger.info(f"Esperando {delay:.1f} segundos antes de reintentar...")
            time.sleep(delay)
            
            # Cambiar el referer y otros headers para el siguiente intento
            request.headers['Referer'] = 'https://www.google.com/search?q=alquiler+departamentos+buenos+aires'
            request.headers['User-Agent'] = random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            ])
            
            # Eliminar cookies para el reintento
            request.meta['dont_merge_cookies'] = True
            
            reason = f"Error {response.status}: {response_status_message(response.status)}"
            return self._retry(request, reason, spider) or response
        
        # Manejar otros códigos de error configurados para reintento
        if response.status in self.retry_http_codes:
            reason = f"Error {response.status}: {response_status_message(response.status)}"
            return self._retry(request, reason, spider) or response
            
        return response

    def process_exception(self, request, exception, spider):
        # Manejar excepciones de red
        self.logger.error(f"Error en la solicitud {request.url}: {exception}")
        time.sleep(random.uniform(5, 15))  # Esperar antes de reintentar
        return super(CustomRetryMiddleware, self).process_exception(request, exception, spider)

class SeleniumMiddleware:
    """Middleware que utiliza Selenium para casos donde otras estrategias fallan"""
    
    def __init__(self, crawler):
        self.logger = logging.getLogger(__name__)
        self.selenium_enabled = crawler.settings.getbool('SELENIUM_ENABLED', False)
        self.selenium_headless = crawler.settings.getbool('SELENIUM_HEADLESS', True)
        self.driver = None
        self.debug_count = 0
        # Máximo número de archivos debug a guardar para Selenium
        self.max_debug_files = 3
        
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def init_driver(self):
        """Inicializa el driver de Selenium si es necesario"""
        if self.driver:
            return
            
        try:
            self.logger.info(f"Iniciando driver de Selenium (modo headless: {self.selenium_headless})...")
            chrome_options = Options()
            
            if self.selenium_headless:
                chrome_options.add_argument("--headless=new")  # Versión más moderna de headless
                
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Añadir un user agent aleatorio
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            ]
            user_agent = random.choice(user_agents)
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Opciones para evitar detección de bots
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Opciones avanzadas para evadir la detección antibot
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_setting_values.cookies": 2,
                "profile.managed_default_content_settings.javascript": 1,
                "profile.managed_default_content_settings.plugins": 2,
                "profile.managed_default_content_settings.popups": 2,
                "profile.managed_default_content_settings.geolocation": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Inicializar el driver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Ejecutar JavaScript para ocultar WebDriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Driver de Selenium inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar Selenium: {str(e)}")
            self.selenium_enabled = False
            self.driver = None  # Asegurarse de que sea None en caso de error
    
    def spider_closed(self, spider):
        """Cierra el driver de Selenium cuando la araña termina"""
        if self.driver:
            self.logger.info("Cerrando driver de Selenium...")
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error al cerrar el driver: {str(e)}")
            finally:
                self.driver = None
                self.logger.info("Driver de Selenium cerrado")
    
    def process_request(self, request, spider):
        """Usa Selenium para procesar la solicitud si está habilitado"""
        if not self.selenium_enabled:
            return None
        
        # Inicializar el driver (si aún no está inicializado)
        if self.driver is None:
            self.init_driver()
            
        # Si después de intentar inicializar el driver aún es None, no continuar
        if self.driver is None:
            self.logger.error("No se pudo inicializar el driver de Selenium, procesando request normalmente")
            return None
        
        try:
            # Usar el user agent del request para mayor consistencia
            user_agent = request.headers.get('User-Agent', None)
            if user_agent:
                self.logger.debug(f"Estableciendo User-Agent en Selenium: {user_agent.decode()}")
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{user_agent.decode()}'}});")
            
            self.logger.info(f"Usando Selenium para abrir {request.url}")
            self.driver.get(request.url)
            
            # Tiempos de espera optimizados
            wait_time = 5  # Reducido a 5 segundos para mayor eficiencia
            self.logger.info(f"Esperando {wait_time} segundos para carga inicial...")
            time.sleep(wait_time)
            
            # Verificar si hay desafío de Cloudflare
            if "Just a moment" in self.driver.page_source or "Cloudflare" in self.driver.page_source:
                self.logger.warning("Detectado desafío de Cloudflare, esperando 15 segundos...")
                time.sleep(15)  # Tiempo reducido pero suficiente
            
            # Hacer scroll de manera más eficiente
            self.logger.debug("Haciendo scroll simplificado...")
            try:
                # Un solo scroll al 70% de la página suele ser suficiente
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                time.sleep(2)
                
                # Y luego al final para cargar todo el contenido
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Error durante scroll: {str(e)}")
            
            # Obtener el HTML generado por Selenium
            body = self.driver.page_source
            
            # Guardar solo algunos archivos de debug para evitar llenado de disco
            if self.debug_count < self.max_debug_files:
                debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                html_file = os.path.join(debug_dir, f"selenium_{int(time.time())}.html")
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(body)
                self.logger.info(f"HTML de Selenium guardado en {html_file}")
                self.debug_count += 1
            
            # Crear una respuesta de Scrapy a partir del HTML de Selenium
            response = HtmlResponse(
                url=request.url,
                body=body.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Error al procesar la solicitud con Selenium: {str(e)}")
            # Intentar reiniciar el driver en caso de error
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
            self.driver = None
            self.init_driver()
            return None
