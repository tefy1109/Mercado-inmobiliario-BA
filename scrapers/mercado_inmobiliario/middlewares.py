import random
import time
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class ZonapropSpiderMiddleware:
    """Spider middleware para ZonaProp"""
    
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


class ZonapropDownloaderMiddleware:
    """Downloader middleware para ZonaProp"""
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Añadir cookies para parecer navegador legítimo
        request.cookies = {
            'accept_cookies': 'true',
            'session_id': f"{random.randint(1000000, 9999999)}",
            'user_preference': 'language=es'
        }
        
        # Añadir referer para parecer que venimos de Google
        if "google.com" not in request.url:
            request.headers['Referer'] = 'https://www.google.com/'
            
        return None

    def process_response(self, request, response, spider):
        # Si recibimos 403, podemos intentar una estrategia diferente
        if response.status == 403:
            spider.logger.info(f"Recibido 403 para {request.url}, intentando con otra estrategia")
            new_request = request.copy()
            
            # Cambiando user-agent a uno de móvil
            mobile_agents = [
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Android 12; Mobile; rv:98.0) Gecko/98.0 Firefox/98.0',
                'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1'
            ]
            
            new_request.headers['User-Agent'] = random.choice(mobile_agents)
            new_request.headers['X-Forwarded-For'] = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            new_request.dont_filter = True
            
            return new_request
            
        return response

    def process_exception(self, request, exception, spider):
        pass


class RotateUserAgentMiddleware:
    """Middleware para rotar User-Agents"""
    
    def __init__(self):
        self.user_agent_list = [
            # Navegadores de escritorio actualizados
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 12.3; rv:98.0) Gecko/20100101 Firefox/98.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/99.0.1150.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko', # IE
            # Dispositivos móviles
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36',
        ]

    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        
        # Añadir variación a headers para parecer navegador real
        request.headers['Accept-Language'] = random.choice([
            'es-ES,es;q=0.9,en;q=0.8',
            'en-US,en;q=0.9,es;q=0.8',
            'es-AR,es;q=0.9,en;q=0.8'
        ])
        
        return None


class DelayMiddleware:
    """Middleware para agregar delays adicionales"""
    
    def __init__(self):
        self.delays = [1, 2, 3, 4, 5]
    
    def process_request(self, request, spider):
        delay = random.choice(self.delays)
        time.sleep(delay)
        return None


class RetryWithBackoffMiddleware(RetryMiddleware):
    """Middleware personalizado de reintentos con backoff exponencial"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    def retry(self, request, reason, spider):
        retry_times = request.meta.get('retry_times', 0) + 1
        
        if retry_times <= self.max_retry_times:
            spider.logger.debug(f"Retrying {request.url} (failed {retry_times} times): {reason}")
            
            # Backoff exponencial
            delay = 2 ** retry_times
            time.sleep(delay)
            
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retry_times
            retry_req.dont_filter = True
            retry_req.priority = request.priority + self.priority_adjust
            
            return retry_req
        else:
            spider.logger.debug(f"Gave up retrying {request.url} (failed {retry_times} times): {reason}")


class JavaScriptMiddleware:
    """Middleware para manejar contenido JavaScript (placeholder)"""
    
    def process_request(self, request, spider):
        # Aquí podrías integrar Selenium o Splash si necesitas JS
        return None
    
    def process_response(self, request, response, spider):
        # Verificar si la respuesta necesita procesamiento JS
        if b'javascript' in response.body.lower():
            spider.logger.warning(f"JavaScript detected in {request.url}")
        return response


class ZonapropStartRequestsMiddleware:
    """Middleware para modificar las solicitudes iniciales de ZonaProp"""
    
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        return s
        
    def process_start_request(self, request, spider):
        """Procesa las solicitudes iniciales"""
        if spider.name == 'zonaprop_spider':
            # Modificar referer para aparentar venir de Google
            request.headers['Referer'] = 'https://www.google.com/search?q=alquiler+departamentos+flores+zonaprop'
            request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            
            # Añadir cookies para simular navegación previa
            request.cookies = {
                'visita_id': str(random.randint(1000000, 9999999)),
                'c_user_id': str(random.randint(1000000, 9999999)),
                'c_visitor_id': str(random.randint(1000000, 9999999)),
                'gdpr': 'true',
                '_ga': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
                '_gid': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
            }
            
            # Configurar para usar cookiejar y no filtrar
            request.meta['cookiejar'] = 1
            request.meta['dont_filter'] = True
        
        return request
