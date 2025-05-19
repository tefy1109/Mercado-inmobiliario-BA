#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import time
import random
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_scraper(spider_name, pages=None, debug=False, delay=None, user_agent=None, use_proxy=False):
    """Ejecuta un scraper con opciones avanzadas de configuración"""
    try:
        # Asegurarse de que estamos en el directorio del proyecto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Añadir el directorio de scrapers al path
        sys.path.insert(0, os.path.join(project_dir, 'scrapers'))
        
        # Importar el spider adecuado
        if spider_name == 'zonaprop':
            from scrapers.mercado_inmobiliario.spiders.zonaprop_spider import ZonapropSpider as SpiderClass
        elif spider_name == 'mercadolibre':
            from scrapers.mercado_inmobiliario.spiders.mercadolibre_spider import MercadolibreSpider as SpiderClass
        else:
            logger.error(f"Spider no reconocido: {spider_name}")
            return
        
        # Configurar settings
        settings = get_project_settings()
        
        # Aplicar configuraciones específicas
        if debug:
            settings['LOG_LEVEL'] = 'DEBUG'
        
        if delay:
            settings['DOWNLOAD_DELAY'] = delay
            logger.info(f"Configurando DOWNLOAD_DELAY a {delay} segundos")
        
        if user_agent:
            settings['USER_AGENT'] = user_agent
            logger.info(f"Usando User-Agent personalizado: {user_agent}")
        
        # Preparar argumentos para el spider
        spider_kwargs = {}
        if pages:
            spider_kwargs['max_pages'] = int(pages)
        
        # Configurar proxy si es necesario
        if use_proxy:
            # Aquí puedes configurar el proxy que desees utilizar
            # Por ejemplo, usando un servicio de proxy como Luminati, BrightData, etc.
            # O simplemente usar un proxy gratuito (no recomendado para producción)
            proxy = 'http://usuario:contraseña@proxy.servicio:puerto'
            settings['DOWNLOADER_MIDDLEWARES']['scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware'] = 750
            settings['HTTPPROXY_ENABLED'] = True
            settings['HTTP_PROXY'] = proxy
            settings['HTTPS_PROXY'] = proxy
            logger.info("Proxy configurado")
        
        # Crear e iniciar el proceso
        process = CrawlerProcess(settings)
        
        # Añadir el spider al proceso - IMPORTANTE: pasar la clase, no una instancia
        process.crawl(SpiderClass, **spider_kwargs)
        
        # Introducir una pequeña espera aleatoria antes de comenzar
        time.sleep(random.uniform(1, 5))
        
        # Iniciar el proceso
        logger.info(f"Iniciando scraper {spider_name}...")
        process.start()  # Este método es bloqueante
        logger.info(f"Scraper {spider_name} finalizado.")
        
    except Exception as e:
        logger.error(f"Error ejecutando scraper {spider_name}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ejecutar scraper con opciones avanzadas')
    
    parser.add_argument('spider', choices=['zonaprop', 'mercadolibre'], help='Nombre del spider a ejecutar')
    parser.add_argument('--pages', type=int, help='Número máximo de páginas a procesar')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    parser.add_argument('--delay', type=float, help='Tiempo de espera entre solicitudes (segundos)')
    parser.add_argument('--user-agent', help='User-Agent personalizado')
    parser.add_argument('--use-proxy', action='store_true', help='Usar proxy (necesita configuración adicional)')
    
    args = parser.parse_args()
    
    run_scraper(
        args.spider, 
        pages=args.pages, 
        debug=args.debug, 
        delay=args.delay,
        user_agent=args.user_agent,
        use_proxy=args.use_proxy
    )
