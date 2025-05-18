# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

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


class RandomUserAgentMiddleware:
    """Middleware para cambiar aleatoriamente el User-Agent en cada solicitud"""
    
    def __init__(self, user_agents):
        self.user_agents = user_agents
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        # Obtener la lista de user agents desde settings
        user_agents = crawler.settings.getlist('USER_AGENT_LIST')
        if not user_agents:
            # Si no hay lista definida, usar un user agent por defecto
            user_agent = crawler.settings.get('USER_AGENT')
            user_agents = [user_agent] if user_agent else ['Mozilla/5.0']
            crawler.logger.warning("USER_AGENT_LIST no configurada, usando USER_AGENT por defecto")
        
        return cls(user_agents)
        
    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        # Añadir headers adicionales para parecer más un navegador real
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/',
        })
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
            
            # Cambiar el referer para el siguiente intento
            request.headers['Referer'] = 'https://www.google.com/search?q=alquiler+departamentos+buenos+aires'
            
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
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.5; rv:90.0) Gecko/20100101 Firefox/90.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
            ]
        return cls(user_agents)
    
    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        self.logger.debug(f"Usando User-Agent: {user_agent}")
        
        # Añadir más headers para simular un navegador real
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        request.headers['Accept-Language'] = 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3'
        request.headers['Accept-Encoding'] = 'gzip, deflate, br'
        request.headers['Connection'] = 'keep-alive'
        request.headers['Upgrade-Insecure-Requests'] = '1'
        request.headers['Cache-Control'] = 'max-age=0'
        
        # Referrer aleatorio para parecer tráfico más natural
        referrers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://ar.yahoo.com/',
            'https://www.instagram.com/',
            'https://www.facebook.com/',
        ]
        request.headers['Referer'] = random.choice(referrers)
        return None

class AdvancedRetryMiddleware(RetryMiddleware):
    """Middleware para reintentar solicitudes con diferentes estrategias"""
    
    def __init__(self, crawler):
        super(AdvancedRetryMiddleware, self).__init__(crawler.settings)
        self.crawler = crawler
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_response(self, request, response, spider):
        if response.status in [403, 429]:
            self.logger.info(f"Recibido {response.status} para {request.url}. Intentando estrategias alternativas.")
            
            # 1. Probar con una solicitud usando requests para obtener cookies
            try:
                headers = {
                    'User-Agent': request.headers.get('User-Agent', b'').decode(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Referer': 'https://www.google.com/',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                # Usar requests para obtener cookies y contenido
                session = requests.Session()
                resp = session.get(request.url, headers=headers, timeout=30)
                
                if resp.status_code == 200:
                    self.logger.info(f"Solicitud alternativa con requests exitosa para {request.url}")
                    # Replicar respuesta de requests en scrapy
                    return HtmlResponse(
                        url=request.url,
                        body=resp.content,
                        encoding='utf-8',
                        request=request,
                        status=200
                    )
            except Exception as e:
                self.logger.warning(f"Error en solicitud con requests: {e}")
            
            # Si todavía fallamos, probar el reintento normal
            return self._retry(request, f"Recibido código {response.status}", spider) or response
        
        # Para otros códigos, usar el comportamiento normal
        if response.status in self.retry_http_codes:
            return self._retry(request, response_status_message(response.status), spider) or response
        
        return response

class SeleniumMiddleware:
    """Middleware que utiliza Selenium para casos donde otras estrategias fallan"""
    
    def __init__(self, crawler):
        self.logger = logging.getLogger(__name__)
        self.selenium_enabled = crawler.settings.getbool('SELENIUM_ENABLED', True)
        self.driver = None
        self.MAX_RETRIES = 3
        
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
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Añadir un user agent aleatorio
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.logger.info("Driver de Selenium inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar Selenium: {e}")
            self.selenium_enabled = False
    
    def process_request(self, request, spider):
        # Usar Selenium solo para solicitudes marcadas o para zonaprop
        if not self.selenium_enabled or not ('zonaprop.com.ar' in request.url):
            return None
            
        self.logger.info(f"Procesando {request.url} con Selenium")
        
        # Inicializar el driver si aún no existe
        try:
            self.init_driver()
            if not self.driver:
                return None
                
            # Obtener la página con Selenium
            self.driver.get(request.url)
            time.sleep(5)  # Esperar a que cargue la página
            
            body = self.driver.page_source
            url = self.driver.current_url
            
            # Construir la respuesta con el contenido de Selenium
            return HtmlResponse(
                url=url,
                body=body,
                encoding='utf-8',
                request=request
            )
        except Exception as e:
            self.logger.error(f"Error al procesar con Selenium: {e}")
            return None
    
    def spider_closed(self):
        """Cierra el driver de Selenium cuando termina el spider"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver de Selenium cerrado")

# Clase base para Spider Middlewares
class MercadoInmobiliarioSpiderMiddleware:
    # No modificado, clase creada automáticamente por scrapy

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
