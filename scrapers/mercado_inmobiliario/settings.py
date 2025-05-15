# Scrapy settings for mercado_inmobiliario project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "mercado_inmobiliario"

SPIDER_MODULES = ["mercado_inmobiliario.spiders"]
NEWSPIDER_MODULE = "mercado_inmobiliario.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "mercado_inmobiliario (+http://www.yourdomain.com)"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Obey robots.txt rules - desactivar para eludir restricciones
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy - reducir para evitar bloqueos
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 5  # Aumentar el retraso entre solicitudes
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Configurar tiempo máximo de espera
DOWNLOAD_TIMEOUT = 180

# Configure item pipelines
ITEM_PIPELINES = {
    "mercado_inmobiliario.pipelines.MercadoInmobiliarioPipeline": 300,
}

# Habilitar middlewares personalizados
DOWNLOADER_MIDDLEWARES = {
    "mercado_inmobiliario.middlewares.TooManyRequestsRetryMiddleware": 543,
    "mercado_inmobiliario.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,  # Deshabilitar el middleware de retry por defecto
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# Configurar manejo de reintentos
RETRY_ENABLED = True
RETRY_TIMES = 10  # Aumentar número de reintentos
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 429]

# Permitir manejar errores 403 en lugar de simplemente ignorarlos
HTTPERROR_ALLOWED_CODES = [403]

# Enable logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy.log'

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Cache HTTP responses para reducir solicitudes
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 horas
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [403, 429, 500, 502, 503, 504]

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 43200 #12 horas
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
HTTPERROR_ALLOW_ALL=True

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
