# Scrapy settings for zonaprop project

BOT_NAME = 'mercado_inmobiliario'

SPIDER_MODULES = ['mercado_inmobiliario.spiders']
NEWSPIDER_MODULE = 'mercado_inmobiliario.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Configure delays
DOWNLOAD_DELAY = 5  # Aumentado de 3 a 5
RANDOMIZE_DOWNLOAD_DELAY = True

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'mercado_inmobiliario.middlewares.ZonapropSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'mercado_inmobiliario.middlewares.ZonapropDownloaderMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'mercado_inmobiliario.middlewares.RotateUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
    'mercado_inmobiliario.middlewares.DelayMiddleware': 351,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'mercado_inmobiliario.pipelines.ValidationPipeline': 300,
    'mercado_inmobiliario.pipelines.CleaningPipeline': 400,
    'mercado_inmobiliario.pipelines.JsonPipeline': 500,
    'mercado_inmobiliario.pipelines.CsvPipeline': 600,
}

# Configure output
FEEDS = {
    'output/propiedades_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
    },
    'output/propiedades_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    },
}

# Cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'

# Retry settings - Incluye código 403 para reintentar
RETRY_ENABLED = True
RETRY_TIMES = 5  # Aumentado de 3 a 5
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504, 408]  # Agregado 403

# Log settings
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'logs/zonaprop.log'

# Request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# Configura manejo de HTTP Codes
HTTPERROR_ALLOWED_CODES = [403]  # Procesar páginas 403 en vez de ignorarlas

# Configura el comportamiento de cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = True

# Para depurar problemas de conectividad
DUPEFILTER_DEBUG = True

# Configuraciones específicas para el spider ZonaProp
# (trasladadas desde custom_settings del spider)
ZONAPROP_SPIDER_SETTINGS = {
    'DOWNLOAD_DELAY': 7,
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'CONCURRENT_REQUESTS': 1,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'HTTPCACHE_ENABLED': False,
    'RETRY_TIMES': 8,
}

# Headers personalizados para ZonaProp
ZONAPROP_DEFAULT_HEADERS = {
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
