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
import shutil

# Configurar logging básico y conciso
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def clean_debug_directory():
    """Elimina el directorio de debug y sus archivos"""
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        debug_dir = os.path.join(project_dir, 'debug')
        
        if os.path.exists(debug_dir):
            # Antes de eliminar todo, verificar si hay demasiados archivos
            files = os.listdir(debug_dir)
            if len(files) > 20:  # Si hay más de 20 archivos
                logger.info(f"Limpiando directorio de debug ({len(files)} archivos)...")
                # Ordenar archivos por fecha de modificación (más antiguos primero)
                files.sort(key=lambda x: os.path.getmtime(os.path.join(debug_dir, x)))
                # Mantener solo los 5 archivos más recientes
                files_to_keep = files[-5:] if len(files) > 5 else []
                files_to_remove = [f for f in files if f not in files_to_keep]
                
                # Eliminar los archivos antiguos
                for file in files_to_remove:
                    try:
                        os.remove(os.path.join(debug_dir, file))
                    except Exception as e:
                        logger.error(f"Error al eliminar archivo {file}: {e}")
                
                logger.info(f"Se eliminaron {len(files_to_remove)} archivos debug antiguos")
            else:
                # Si hay pocos archivos, eliminar el directorio completo si se solicitó
                if args.clean_debug:
                    shutil.rmtree(debug_dir)
                    logger.info(f"Directorio de debug eliminado correctamente")
        else:
            logger.info(f"El directorio de debug no existe, no hay nada que eliminar")
    except Exception as e:
        logger.error(f"Error al limpiar el directorio de debug: {str(e)}")

def verify_data_directory():
    """Verifica que el directorio data/raw exista antes de iniciar el scraping."""
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(project_dir, 'data')
        raw_dir = os.path.join(data_dir, 'raw')
        
        logger.info("Verificando directorios para almacenamiento de datos...")
        
        if not os.path.exists(data_dir):
            logger.info(f"Creando directorio: {data_dir}")
            os.makedirs(data_dir, exist_ok=True)
        
        if not os.path.exists(raw_dir):
            logger.info(f"Creando directorio: {raw_dir}")
            os.makedirs(raw_dir, exist_ok=True)
        
        # Verificar permisos de escritura
        test_file = os.path.join(raw_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("✅ Permisos de escritura verificados correctamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error de permisos en {raw_dir}: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error al verificar directorios: {str(e)}")
        return False

def check_selenium_dependencies():
    """Verifica que las dependencias de Selenium estén instaladas"""
    try:
        # Verificar Chrome/Chromium
        import shutil
        chrome_path = shutil.which('google-chrome') or shutil.which('chromium-browser')
        if not chrome_path:
            logger.warning("⚠️ No se detectó Google Chrome o Chromium. Puede que Selenium no funcione correctamente.")
        else:
            logger.info(f"✅ Navegador detectado en: {chrome_path}")
        
        # Verificar chromedriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            ChromeDriverManager().install()
            logger.info("✅ ChromeDriver instalado correctamente")
        except Exception as e:
            logger.warning(f"⚠️ Error al verificar ChromeDriver: {str(e)}")
            logger.warning("Es posible que Selenium no funcione correctamente.")
        
        # Verificar Selenium
        try:
            from selenium import webdriver
            logger.info(f"✅ Selenium instalado: versión {webdriver.__version__}")
        except Exception as e:
            logger.error(f"❌ Error al cargar Selenium: {str(e)}")
            logger.error("Por favor, instala Selenium: pip install selenium")
            
        return True
    except Exception as e:
        logger.error(f"❌ Error al verificar dependencias de Selenium: {str(e)}")
        return False

def run_scraper(spider_name, pages=None, delay=None, user_agent=None, visible=False, use_proxy=False, clean_debug=False):
    """
    Ejecuta un scraper con opciones avanzadas de configuración
    
    Args:
        spider_name: Nombre del spider a ejecutar ('zonaprop' o 'mercadolibre')
        pages: Número máximo de páginas a procesar
        delay: Tiempo de espera entre solicitudes en segundos
        user_agent: User-Agent personalizado
        visible: Si se debe mostrar el navegador de Selenium (no headless)
        use_proxy: Si se debe usar proxy
        clean_debug: Si se deben limpiar archivos de debug antes de ejecutar
    """
    try:
        # Limpiar el directorio de debug si se solicita
        if clean_debug:
            clean_debug_directory()
            
        # Verificar estructura de directorios antes de iniciar
        if not verify_data_directory():
            logger.error("No se pudo verificar/crear la estructura de directorios. Abortando.")
            return
        
        # Si vamos a usar Selenium (para ZonaProp o con --visible), verificar dependencias
        if spider_name == 'zonaprop' or visible:
            logger.info("Verificando dependencias de Selenium...")
            if not check_selenium_dependencies():
                logger.warning("Hay problemas con las dependencias de Selenium, pero intentaremos continuar.")
            
        # Asegurarse de que estamos en el directorio del proyecto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Corregir la ruta de importación de los spiders
        scrapers_path = os.path.join(project_dir, 'scrapers')
        sys.path.insert(0, scrapers_path)
        
        # Importar el spider adecuado
        if spider_name == 'zonaprop':
            from mercado_inmobiliario.spiders.zonaprop_spider import ZonapropSpider as SpiderClass
        elif spider_name == 'mercadolibre':
            from mercado_inmobiliario.spiders.mercadolibre_spider import MercadolibreSpider as SpiderClass
        else:
            logger.error(f"Spider no reconocido: {spider_name}")
            return
        
        # Configurar settings
        settings = get_project_settings()
        
        # Mensaje de inicio más explícito
        logger.info("=" * 50)
        logger.info(f"🕷️  INICIANDO SCRAPER: {spider_name}")
        logger.info(f"⚙️  Páginas máximas: {pages if pages else 'Sin límite'}")
        logger.info(f"⏱️  Delay: {delay if delay else settings.get('DOWNLOAD_DELAY', 'Default')} segundos")
        logger.info(f"🌐  Navegador visible: {'✓ Sí' if visible else '✗ No'}")
        logger.info("=" * 50)
        
        # CRÍTICO: Habilitar explícitamente los pipelines
        settings['ITEM_PIPELINES'] = {
            'mercado_inmobiliario.pipelines.MercadoInmobiliarioPipeline': 300,
            'mercado_inmobiliario.pipelines.SQLitePipeline': 400,
        }
        
        # Habilitar manejo de códigos de error HTTP
        settings['HTTPERROR_ALLOWED_CODES'] = [403, 429]
        
        # Configurar logging para scrapy (limitar la cantidad de logs)
        settings['LOG_ENABLED'] = True
        settings['LOG_LEVEL'] = 'INFO'
        settings['LOG_FORMAT'] = '%(levelname)s: %(message)s'
        settings['LOG_FILE'] = None  # Desactivar archivo de log
        
        if delay:
            settings['DOWNLOAD_DELAY'] = delay
            logger.info(f"Configurando DOWNLOAD_DELAY a {delay} segundos")
        
        if user_agent:
            settings['USER_AGENT'] = user_agent
        else:
            # Si no se proporciona user_agent, usar uno moderno por defecto
            modern_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            settings['USER_AGENT'] = modern_ua
        
        # Asegurar que SELENIUM_ENABLED esté activado para zonaprop
        if spider_name == 'zonaprop':
            settings['SELENIUM_ENABLED'] = True
            # Configurar el modo headless basado en el parámetro 'visible'
            settings['SELENIUM_HEADLESS'] = not visible
            
            logger.info(f"Activando Selenium para ZonaProp (modo {'visible' if visible else 'headless'})")
            
            # Aumentar significativamente el delay para ZonaProp
            if not delay:
                delay = 8.0  # Valor predeterminado más alto para ZonaProp
                settings['DOWNLOAD_DELAY'] = delay
                logger.info(f"Configurando DOWNLOAD_DELAY para ZonaProp a {delay} segundos")
            
            # IMPORTANTE: Configurar explícitamente los middlewares para evitar bloqueos
            settings['DOWNLOADER_MIDDLEWARES'] = {
                "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
                "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
                "mercado_inmobiliario.middlewares.RotateUserAgentMiddleware": 100,
                "mercado_inmobiliario.middlewares.CustomRetryMiddleware": 550,
                "mercado_inmobiliario.middlewares.SeleniumMiddleware": 600,
                "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
            }
            
            # Crear directorio de debug para guardar el HTML
            debug_dir = os.path.join(project_dir, 'debug')
            if clean_debug and os.path.exists(debug_dir):
                logger.info(f"Limpiando directorio de debug...")
                shutil.rmtree(debug_dir)
            os.makedirs(debug_dir, exist_ok=True)
            logger.info(f"Directorio de debug: {debug_dir}")
        
        # Preparar argumentos para el spider
        spider_kwargs = {}
        if pages:
            spider_kwargs['max_pages'] = int(pages)
        
        # Configurar proxy si es necesario
        if use_proxy:
            logger.warning("La opción use-proxy está activada pero no hay configuración real de proxy")
        
        # Crear e iniciar el proceso
        process = CrawlerProcess(settings)
        
        # Añadir el spider al proceso
        process.crawl(SpiderClass, **spider_kwargs)
        
        # Iniciar el proceso
        process.start()  # Este método es bloqueante
        
        # Mostrar mensaje final con información sobre dónde encontrar los datos
        project_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(project_dir, 'data', 'raw')
        logger.info("=" * 50)
        logger.info("✅ PROCESO FINALIZADO")
        logger.info(f"📁 Los datos se encuentran en: {data_dir}")
        
        # Verificar si se generaron archivos
        files = os.listdir(data_dir)
        json_files = [f for f in files if f.endswith('.json')]
        if json_files:
            latest_file = max([os.path.join(data_dir, f) for f in json_files], key=os.path.getctime)
            logger.info(f"📄 Último archivo generado: {os.path.basename(latest_file)}")
            file_size = os.path.getsize(latest_file)
            logger.info(f"📊 Tamaño del archivo: {file_size} bytes")
            
            if file_size < 100:
                logger.warning("⚠️ El archivo generado es muy pequeño, puede contener errores")
        else:
            logger.warning("⚠️ No se encontraron archivos JSON generados")
        
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error ejecutando scraper {spider_name}: {str(e)}")
        # Mostrar más información sobre el error para facilitar la depuración
        import traceback
        logger.error(f"Detalles del error:\n{traceback.format_exc()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ejecutar scraper con opciones avanzadas')
    
    parser.add_argument('spider', choices=['zonaprop', 'mercadolibre'], help='Nombre del spider a ejecutar')
    parser.add_argument('--pages', type=int, help='Número máximo de páginas a procesar')
    parser.add_argument('--delay', type=float, help='Tiempo de espera entre solicitudes (segundos)')
    parser.add_argument('--user-agent', help='User-Agent personalizado')
    parser.add_argument('--visible', action='store_true', help='Mostrar navegador durante la ejecución (no headless)')
    parser.add_argument('--use-proxy', action='store_true', help='Usar proxy (necesita configuración adicional)')
    parser.add_argument('--clean-debug', action='store_true', help='Eliminar archivos de debug antes de ejecutar')
    
    args = parser.parse_args()
    
    run_scraper(
        args.spider, 
        pages=args.pages, 
        delay=args.delay,
        user_agent=args.user_agent,
        visible=args.visible,
        use_proxy=args.use_proxy,
        clean_debug=args.clean_debug
    )
