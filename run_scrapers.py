#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_scraper(spider_name, pages=None, debug=False):
    """Ejecuta un scraper específico con opciones de configuración"""
    try:
        # Asegurarse de que estamos en el directorio del proyecto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Añadir el directorio de scrapers al path para poder importar los módulos
        sys.path.insert(0, os.path.join(project_dir, 'scrapers'))
        
        # Importar spiders
        if spider_name == 'zonaprop':
            from scrapers.mercado_inmobiliario.spiders.zonaprop_spider import ZonapropSpider as SpiderClass
        elif spider_name == 'mercadolibre':
            from scrapers.mercado_inmobiliario.spiders.mercadolibre_spider import MercadolibreSpider as SpiderClass
        else:
            logging.error(f"Spider no reconocido: {spider_name}")
            return
        
        # Configurar el proceso de crawling
        settings = get_project_settings()
        
        # Ajustar configuraciones en modo debug si es necesario
        if debug:
            settings['LOG_LEVEL'] = 'DEBUG'
            settings['CLOSESPIDER_PAGECOUNT'] = 3  # Límite para testing
        
        # Ajustar el número máximo de páginas si se especificó
        if pages:
            settings['CLOSESPIDER_PAGECOUNT'] = pages
        
        # Crear e iniciar el proceso
        process = CrawlerProcess(settings)
        
        # IMPORTANTE: Pasar la clase del spider, no una instancia
        # Usamos kwargs para pasar argumentos al spider
        spider_kwargs = {}
        if pages:
            spider_kwargs['max_pages'] = int(pages)
            
        process.crawl(SpiderClass, **spider_kwargs)
        
        # Iniciar el proceso
        logging.info(f"Iniciando scraper {spider_name}...")
        process.start()
        logging.info(f"Scraper {spider_name} finalizado.")
        
    except Exception as e:
        logging.error(f"Error ejecutando scraper {spider_name}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ejecutar scrapers de mercado inmobiliario')
    parser.add_argument('spider', choices=['zonaprop', 'mercadolibre'], help='Nombre del spider a ejecutar')
    parser.add_argument('--pages', type=int, help='Número máximo de páginas a procesar')
    parser.add_argument('--debug', action='store_true', help='Ejecutar en modo debug')
    
    args = parser.parse_args()
    
    run_scraper(args.spider, args.pages, args.debug)
