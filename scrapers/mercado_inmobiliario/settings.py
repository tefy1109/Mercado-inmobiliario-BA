# Scrapy settings for mercado_inmobiliario project

BOT_NAME = "mercado_inmobiliario"

SPIDER_MODULES = ["mercado_inmobiliario.spiders"]
NEWSPIDER_MODULE = "mercado_inmobiliario.spiders"

# User-Agent por defecto (usar uno muy reciente)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

# Desactivar robots.txt para poder acceder a páginas restringidas
ROBOTSTXT_OBEY = False

# Aumentar velocidad de scraping
CONCURRENT_REQUESTS = 2  # Aumentado a 2 para mayor velocidad
DOWNLOAD_DELAY = 2  # Reducido a 2 segundos entre solicitudes
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = True
DOWNLOAD_TIMEOUT = 90  # Reducido a 90 segundos

# Configuraciñon optimizada para Selenium
SELENIUM_ENABLED = True
SELENIUM_HEADLESS = True  # Modo headless para mayor velocidad

# Permitir que el spider maneje los códigos de error 403
HTTPERROR_ALLOWED_CODES = [403, 429]

# Estos deben estar habilitados también en run_scraper_advanced.py
ITEM_PIPELINES = {
    "mercado_inmobiliario.pipelines.MercadoInmobiliarioPipeline": 300,
    "mercado_inmobiliario.pipelines.SQLitePipeline": 400,
}

# Estos middlewares también deben configurarse en run_scraper_advanced.py
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "mercado_inmobiliario.middlewares.RotateUserAgentMiddleware": 100,
    "mercado_inmobiliario.middlewares.CustomRetryMiddleware": 550,
    "mercado_inmobiliario.middlewares.SeleniumMiddleware": 600,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# Configuración de base de datos
SQLITE_DB_PATH = "data/propiedades.db"

# Configuración de reintentos
RETRY_ENABLED = True
RETRY_TIMES = 3  # Reducido a 3 para no perder tiempo en reintentos
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 429]

# Reducir cantidad de logs
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(levelname)s: %(message)s"
LOG_SHORT_NAMES = True
LOG_DATEFORMAT = "%H:%M:%S" 

# Configuración de AutoThrottle optimizada
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2  # Reducido para iniciar más rápido
AUTOTHROTTLE_MAX_DELAY = 15  # Reducido para evitar esperas largas
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.5  # Aumentado para mayor velocidad

# Desactivar logs de componentes específicos
LOG_FILTER_NAMES = [
    'scrapy.core.engine',
    'scrapy.middleware',
    'scrapy.utils.log',
    'scrapy.crawler',
    'scrapy.core.scraper', 
    'scrapy.extensions',
    'urllib3.connectionpool',
    'selenium.webdriver.remote.remote_connection'
]

# Desactivar caché HTTP
HTTPCACHE_ENABLED = False
