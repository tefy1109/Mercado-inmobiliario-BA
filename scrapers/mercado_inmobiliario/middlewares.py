# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import NotConfigured
from scrapy.utils.response import response_status_message
import logging
import random
import time

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class MercadoInmobiliarioSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class MercadoInmobiliarioDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        if response.status in [403, 429]:  # Forbidden or Too Many Requests
            # Aumentar el retraso paulatinamente para evitar bloqueos
            delay = random.uniform(10, 30)
            spider.logger.warning(f"Recibido código {response.status}. Esperando {delay:.1f} segundos antes de reintentar.")
            time.sleep(delay)

            # Cambiar el user agent para el siguiente intento
            request.headers['User-Agent'] = random.choice(spider.user_agents)

            # Agregar más headers para parecer más humano
            request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            request.headers['Accept-Language'] = 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3'
            request.headers['Referer'] = 'https://www.google.com/'

            # Usamos la clase padre para manejar el reintento
            reason = f"TooManyRequests o Forbidden: {response.status}"
            return self._retry(request, reason, spider) or response

        # Si es otro tipo de error HTTP, usamos la clase padre
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class RandomUserAgentMiddleware:
    """Middleware para cambiar aleatoriamente el User-Agent en cada solicitud"""

    def __init__(self, user_agents):
        self.user_agents = user_agents
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        user_agents = crawler.spider.user_agents if hasattr(crawler.spider, 'user_agents') else [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        return cls(user_agents)

    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        self.logger.debug(f"Usando User-Agent: {user_agent}")
        return None
