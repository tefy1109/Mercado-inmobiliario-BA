#!/usr/bin/env python3

"""
Script para probar el acceso a ZonaProp y diagnosticar problemas
Este script intenta acceder a ZonaProp de diferentes maneras para identificar
la mejor estrategia para evitar bloqueos.
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import argparse
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_direct_access():
    """Prueba el acceso directo usando requests"""
    logger.info("Probando acceso directo con requests...")
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/search?q=zonaprop+alquiler+departamentos',
    }
    
    try:
        response = requests.get("https://www.zonaprop.com.ar/departamentos-alquiler-flores.html", 
                              headers=headers,
                              timeout=30)
        
        logger.info(f"Código de estado: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Acceso directo exitoso")
            if "Just a moment" in response.text:
                logger.warning("⚠️ Pero detectado desafío de Cloudflare")
            
            # Guardar página para análisis
            with open("test_direct_access.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info("Página guardada en test_direct_access.html")
            
            return True
        else:
            logger.error(f"❌ Acceso fallido con código {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error en acceso directo: {str(e)}")
        return False

def test_selenium_access(headless=True):
    """Prueba el acceso usando Selenium"""
    logger.info(f"Probando acceso con Selenium ({'modo headless' if headless else 'navegador visible'})...")
    
    try:
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        # Anti-detección
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Iniciar navegador
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Eliminar rastros de automatización
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Navegar a la página
        logger.info("Abriendo página...")
        driver.get("https://www.zonaprop.com.ar/departamentos-alquiler-flores.html")
        
        # Esperar carga
        time.sleep(5)
        
        # Verificar si hay desafío de Cloudflare
        page_source = driver.page_source
        if "Just a moment" in page_source:
            logger.warning("⚠️ Detectado desafío de Cloudflare")
            
            # Esperar más tiempo para resolverlo
            for i in range(5):
                logger.info(f"Esperando resolución del desafío... {i+1}/5")
                time.sleep(5)
                page_source = driver.page_source
                if "Just a moment" not in page_source and "Cloudflare" not in page_source:
                    logger.info("✅ Desafío superado")
                    break
        
        # Comprobar resultado
        title = driver.title
        logger.info(f"Título de la página: {title}")
        
        # Guardar la página
        with open(f"test_selenium_{'headless' if headless else 'visible'}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"Página guardada en test_selenium_{'headless' if headless else 'visible'}.html")
        
        # Tomar captura de pantalla
        driver.save_screenshot(f"test_selenium_{'headless' if headless else 'visible'}.png")
        logger.info(f"Captura guardada en test_selenium_{'headless' if headless else 'visible'}.png")
        
        # Verificar éxito
        success = "Just a moment" not in driver.page_source and "403 Forbidden" not in driver.page_source
        if success:
            logger.info("✅ Acceso con Selenium exitoso")
        else:
            logger.error("❌ Selenium no pudo acceder correctamente")
        
        driver.quit()
        return success
    except Exception as e:
        logger.error(f"❌ Error en acceso con Selenium: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prueba el acceso a ZonaProp")
    parser.add_argument("--all", action="store_true", help="Probar todas las formas de acceso")
    parser.add_argument("--direct", action="store_true", help="Probar acceso directo con requests")
    parser.add_argument("--selenium", action="store_true", help="Probar acceso con Selenium headless")
    parser.add_argument("--selenium-visible", action="store_true", help="Probar acceso con Selenium visible")
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna opción, probar todo
    if not (args.all or args.direct or args.selenium or args.selenium_visible):
        args.all = True
    
    # Crear directorio para resultados
    os.makedirs("test_results", exist_ok=True)
    os.chdir("test_results")
    
    results = []
    
    # Ejecutar pruebas seleccionadas
    if args.all or args.direct:
        success = test_direct_access()
        results.append(("Acceso directo", success))
    
    if args.all or args.selenium:
        success = test_selenium_access(headless=True)
        results.append(("Selenium headless", success))
    
    if args.all or args.selenium_visible:
        success = test_selenium_access(headless=False)
        results.append(("Selenium visible", success))
    
    # Mostrar resumen
    logger.info("\n" + "=" * 50)
    logger.info("RESULTADOS DE LAS PRUEBAS:")
    for test, result in results:
        status = "✅ ÉXITO" if result else "❌ FALLÓ"
        logger.info(f"{test}: {status}")
    logger.info("=" * 50)
    
    # Recomendar mejor método
    successful_methods = [method for method, success in results if success]
    if not successful_methods:
        logger.error("❌ Ningún método fue exitoso. Recomendación: usar un proxy o esperar antes de reintentar.")
    else:
        logger.info(f"✅ Método(s) exitoso(s): {', '.join(successful_methods)}")
        if "Selenium visible" in successful_methods:
            logger.info("⚠️ Selenium visible funcionó mejor, considera usar esta opción pero requiere interfaz gráfica.")
        elif "Selenium headless" in successful_methods:
            logger.info("✅ Recomendación: usa Selenium en modo headless en tu scraper.")
        elif "Acceso directo" in successful_methods:
            logger.info("✅ Recomendación: puedes usar acceso directo sin Selenium.")
