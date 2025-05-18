# Scrapy settings for mercado_inmobiliario project

BOT_NAME = "mercado_inmobiliario"

SPIDER_MODULES = ["mercado_inmobiliario.spiders"]
NEWSPIDER_MODULE = "mercado_inmobiliario.spiders"

# Lista de User Agents para rotación
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0",
]

# User-Agent por defecto
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"

# Desactivar robots.txt para poder acceder a páginas restringidas
ROBOTSTXT_OBEY = False

# Configuración para evitar bloqueos
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 8  # 8 segundos entre solicitudes
RANDOMIZE_DOWNLOAD_DELAY = True
COOKIES_ENABLED = True
DOWNLOAD_TIMEOUT = 180

# Configuración específica por spider
ZONAPROP_MAX_PAGES = 3  # Limitar a 3 páginas inicialmente para pruebas
ZONAPROP_DOWNLOAD_DELAY = 8  # Aumentado para evitar bloqueos

# IMPORTANTE: Permitir que el spider maneje los códigos de error 403
HTTPERROR_ALLOWED_CODES = [403]

# Activar los middleware personalizados
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,  # Deshabilitar el middleware de UA predeterminado
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    "mercado_inmobiliario.middlewares.RandomUserAgentMiddleware": 100,
    "mercado_inmobiliario.middlewares.CustomRetryMiddleware": 110,
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "mercado_inmobiliario.pipelines.MercadoInmobiliarioPipeline": 300,
    "mercado_inmobiliario.pipelines.SQLitePipeline": 400,  # Añadir el nuevo pipeline SQLite
}

# Configuración de base de datos
SQLITE_DB_PATH = "data/propiedades.db"

# Configuración de reintentos
RETRY_ENABLED = True
RETRY_TIMES = 10  # Aumentar número de reintentos
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 403, 429]

# Niveles de logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# Configuración de AutoThrottle para adaptar la velocidad de manera dinámica
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Configuración de caché HTTP
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [403, 429, 500, 502, 503, 504]
