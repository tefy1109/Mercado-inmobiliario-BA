#!/usr/bin/env python3
"""
Script para extraer datos de ZonaProp usando Selenium con configuración avanzada
"""

import os
import time
import random
import re
import json
import csv
from datetime import datetime
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

def create_directories():
    """Crear directorios necesarios"""
    dirs = ['output', 'logs', 'data']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directorio {directory} creado/verificado")

def setup_webdriver():
    """Configurar y retornar instancia de WebDriver"""
    print("Configurando navegador Chrome...")
    
    # Opciones de Chrome con parámetros avanzados para evitar detección y timeouts
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--dns-prefetch-disable")
    
    # Evitar detección de bot
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Seleccionar User-Agent aleatorio
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Aumentar los tiempos de espera
    try:
        # Aumentar tiempos de conexión para evitar timeouts
        service = Service()
        service.connection_timeout = 180  # 3 minutos
        driver = webdriver.Chrome(options=chrome_options, service=service)
        driver.set_page_load_timeout(180)  # 3 minutos para cargar páginas
        driver.set_script_timeout(180)  # 3 minutos para scripts
        
        # Ocultar la automatización
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print(f"Error al configurar WebDriver: {e}")
        raise

def human_like_delay():
    """Genera un delay aleatorio para simular comportamiento humano"""
    return random.uniform(2.0, 5.0)

def scrape_property(property_element, driver):
    """Extrae datos de una propiedad individual"""
    item = {}
    
    try:
        # Scroll al elemento para asegurarse que esté visible
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", property_element)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Intentar múltiples selectores para el precio
        selectors = [
            'div[data-qa="POSTING_CARD_PRICE"]',
            'div.price-data',
            'div.postingCard-module__price',
            'div.postingPrice'
        ]
        
        price_element = None
        for selector in selectors:
            try:
                price_element = property_element.find_element(By.CSS_SELECTOR, selector).text
                if price_element:
                    break
            except NoSuchElementException:
                continue
        
        if price_element:
            # Limpia el precio (remueve $ y puntos)
            price_clean = re.sub(r'[^\d]', '', price_element)
            item['precio_alquiler'] = int(price_clean) if price_clean else None
        else:
            item['precio_alquiler'] = None
            
        # Buscar expensas con varios selectores posibles
        expense_selectors = [
            'div[data-qa="expensas"]',
            'div.expensas',
            'span.postingCardExpenses'
        ]
        
        expenses_element = None
        for selector in expense_selectors:
            try:
                expenses_element = property_element.find_element(By.CSS_SELECTOR, selector).text
                if expenses_element:
                    break
            except NoSuchElementException:
                continue
                
        if expenses_element:
            expenses_clean = re.sub(r'[^\d]', '', expenses_element)
            item['expensas'] = int(expenses_clean) if expenses_clean else None
        else:
            item['expensas'] = None
            
        # Resto de datos con la misma estrategia de selectores múltiples
        # ... (implementación para dirección, características, etc.)
        
        # Timestamp
        item['scraped_at'] = datetime.now().isoformat()
        
        return item
    except Exception as e:
        print(f"Error procesando propiedad: {e}")
        return None

def save_results(properties):
    """Guardar resultados en formatos JSON y CSV"""
    if not properties:
        print("No hay propiedades para guardar")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Guardar JSON
    json_filename = f'output/zonaprop_propiedades_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(properties, f, ensure_ascii=False, indent=2)
    print(f"Guardados {len(properties)} ítems en {json_filename}")
    
    # Guardar CSV
    csv_filename = f'output/zonaprop_propiedades_{timestamp}.csv'
    # Si hay propiedades, usar las claves de la primera para las columnas
    if properties:
        fieldnames = properties[0].keys()
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for prop in properties:
                writer.writerow(prop)
        print(f"Guardados {len(properties)} ítems en {csv_filename}")

def scrape_with_retry(url, max_retries=3):
    """Scrapear con reintentos en caso de fallos"""
    properties = []
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Intento {attempt} de {max_retries}")
            driver = setup_webdriver()
            
            try:
                # Navegar primero a Google para establecer cookies y referrer
                print("Visitando Google primero...")
                driver.get('https://www.google.com')
                time.sleep(human_like_delay())
                
                # Buscar en Google para simular navegación natural
                try:
                    search_box = driver.find_element(By.NAME, 'q')
                    search_terms = ["alquileres departamentos buenos aires", 
                                   "departamentos alquiler flores"]
                    search_term = random.choice(search_terms)
                    
                    # Simular tipeo humano
                    for char in search_term:
                        search_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                        
                    search_box.submit()
                    time.sleep(human_like_delay())
                    
                    # Buscar resultado de ZonaProp
                    try:
                        links = driver.find_elements(By.PARTIAL_LINK_TEXT, "zonaprop")
                        if links:
                            print("Encontrado link de ZonaProp en resultados de Google")
                            # Clic en el resultado para una navegación más natural
                            links[0].click()
                            time.sleep(human_like_delay() * 2)
                        else:
                            # Si no encontramos el link en Google, ir directo
                            print("Link no encontrado en Google, navegando directamente")
                            driver.get(url)
                    except:
                        print("No se encontró el link en Google, navegando directamente")
                        driver.get(url)
                except Exception as e:
                    print(f"Error en búsqueda de Google: {e}, navegando directamente")
                    driver.get(url)
                
                time.sleep(human_like_delay() * 2)
                
                # Comprobar si hay captcha o pantalla de bloqueo
                page_source = driver.page_source.lower()
                if "captcha" in page_source or "robot" in page_source:
                    print("⚠️ Detectado posible CAPTCHA o verificación anti-bot")
                    # Guardar screenshot para revisar manualmente
                    driver.save_screenshot('captcha_detected.png')
                    print("Screenshot guardado como 'captcha_detected.png'")
                    
                    # Esperar interacción manual
                    input("Por favor, resuelve el CAPTCHA en el navegador y presiona Enter para continuar...")
                
                # Esperar a que las propiedades se carguen
                wait = WebDriverWait(driver, 30)
                try:
                    # Intentar varios selectores posibles
                    selectors = [
                        'div.postingCard', 
                        'div[data-qa="posting PROPERTY"]',
                        'div.PostingCard',
                        'article.PostingCard'
                    ]
                    
                    property_elements = []
                    for selector in selectors:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            property_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if property_elements:
                                print(f"Encontrados {len(property_elements)} propiedades con selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not property_elements:
                        print("No se pudieron encontrar propiedades con ningún selector")
                        # Guardar HTML para depuración
                        with open('debug_page.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        print("HTML guardado como 'debug_page.html'")
                        continue
                    
                    # Procesar cada propiedad
                    for prop_element in property_elements:
                        item = scrape_property(prop_element, driver)
                        if item:
                            properties.append(item)
                            print(f"Propiedad extraída: {item.get('direccion', 'Sin dirección')} - ${item.get('precio_alquiler', 'N/A')}")
                        
                        time.sleep(human_like_delay())
                    
                    # Si llegamos aquí y tenemos propiedades, el scraping fue exitoso
                    if properties:
                        print(f"✅ Scraping exitoso en el intento {attempt}. {len(properties)} propiedades extraídas.")
                        break
                        
                except Exception as e:
                    print(f"Error durante el scraping: {e}")
                    # Guardar HTML para depuración
                    with open(f'error_page_{attempt}.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print(f"HTML guardado como 'error_page_{attempt}.html'")
                
            finally:
                # Cerrar el navegador
                driver.quit()
                
        except WebDriverException as e:
            print(f"Error de WebDriver en el intento {attempt}: {e}")
            time.sleep(10)  # Esperar antes de reintentar
    
    return properties

def main():
    """Función principal"""
    print("🚀 Iniciando scraper avanzado de ZonaProp con Selenium")
    print("=" * 50)
    
    # Crear directorios necesarios
    create_directories()
    
    # URL a scrapear
    url = 'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html'
    
    # Ejecutar scraping con reintentos
    properties = scrape_with_retry(url, max_retries=3)
    
    # Guardar resultados
    if properties:
        save_results(properties)
        print(f"✅ Proceso completado. Se extrajeron {len(properties)} propiedades.")
    else:
        print("❌ No se pudieron extraer propiedades")
    
    print("=" * 50)
    print("🎉 Proceso finalizado")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
