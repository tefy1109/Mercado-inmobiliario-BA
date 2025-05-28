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
        
        # Precio de alquiler - usando los mismos selectores del spider
        price_selectors = [
            'div.postingCard-module__price-container div:first-child',
            'div[data-qa="POSTING_CARD_PRICE"]',
            'div.price-data',
            'div.postingPrice'
        ]
        
        price_element = None
        for selector in price_selectors:
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
            
        # Expensas - usando los mismos selectores del spider
        expense_selectors = [
            'div.postingCard-module__price-container div:nth-child(2)',
            'div[data-qa="expensas"]',
            'div.expensas',
            'span.postingCardExpenses'
        ]
        
        expenses_element = None
        for selector in expense_selectors:
            try:
                expenses_element = property_element.find_element(By.CSS_SELECTOR, selector).text
                if expenses_element and ('expensa' in expenses_element.lower() or '$' in expenses_element):
                    break
            except NoSuchElementException:
                continue
                
        if expenses_element:
            expenses_clean = re.sub(r'[^\d]', '', expenses_element)
            item['expensas'] = int(expenses_clean) if expenses_clean else None
        else:
            item['expensas'] = None
        
        # Dirección - usando los mismos selectores del spider
        address_selectors = [
            'div.postingCard-module__posting-container div.postingCard-module__posting-top div:nth-child(1) div:nth-child(2) div div',
            'div.postingCard-module__location',
            'div[data-qa="POSTING_CARD_LOCATION"]'
        ]
        
        address_element = None
        for selector in address_selectors:
            try:
                address_element = property_element.find_element(By.CSS_SELECTOR, selector).text
                if address_element:
                    break
            except NoSuchElementException:
                continue
        
        item['direccion'] = address_element.strip() if address_element else None
        
        # Extracción de barrio/zona de la URL actual o de la dirección
        current_url = driver.current_url
        barrio_match = re.search(r'-alquiler-([^\.]+)\.html', current_url)
        item['zona'] = barrio_match.group(1).capitalize() if barrio_match else 'Flores'
        
        # Características de la propiedad (superficie, ambientes, habitaciones, baños)
        # Usando la misma lógica mejorada del spider
        feature_container_selectors = [
            'div.postingCard-module__posting-container div.postingCard-module__posting-top div.postingCard-module__posting-card-row h3',
            'h3[data-qa="POSTING_CARD_FEATURES"]'
        ]
        
        feature_container = None
        for selector in feature_container_selectors:
            try:
                feature_container = property_element.find_element(By.CSS_SELECTOR, selector)
                if feature_container:
                    break
            except NoSuchElementException:
                continue
        
        # Inicializar valores por defecto
        item['superficie'] = None
        item['ambientes'] = None
        item['habitaciones'] = None
        item['banos'] = None
        
        # Si encontramos el contenedor, extraemos los spans
        if feature_container:
            # Extraer todos los spans dentro del h3
            feature_spans = feature_container.find_elements(By.CSS_SELECTOR, 'span')
            feature_texts = [span.text.strip() for span in feature_spans if span.text.strip()]
            
            # Procesar cada característica encontrada
            for feature in feature_texts:
                feature_clean = feature.strip()
                
                # Superficie (m²)
                if 'm²' in feature_clean:
                    surface_match = re.search(r'(\d+)', feature_clean)
                    item['superficie'] = int(surface_match.group(1)) if surface_match else None
                
                # Ambientes
                elif 'amb' in feature_clean.lower():
                    amb_match = re.search(r'(\d+)', feature_clean)
                    ambientes = int(amb_match.group(1)) if amb_match else None
                    item['ambientes'] = ambientes
                    
                    # Si ambientes = 1, entonces habitaciones = 0
                    if ambientes == 1:
                        item['habitaciones'] = 0
                
                # Habitaciones/Dormitorios
                elif 'dorm' in feature_clean.lower() or 'hab' in feature_clean.lower():
                    hab_match = re.search(r'(\d+)', feature_clean)
                    item['habitaciones'] = int(hab_match.group(1)) if hab_match else None
                
                # Baños
                elif 'baño' in feature_clean.lower():
                    bath_match = re.search(r'(\d+)', feature_clean)
                    item['banos'] = int(bath_match.group(1)) if bath_match else None
        
        # Descripción/Título - usando los mismos selectores del spider
        description_selectors = [
            'div.postingCard-module__posting-container div.postingCard-module__posting-top h3 a',
            'h3[data-qa="POSTING_CARD_TITLE"] a',
            'h3 a'
        ]
        
        description_element = None
        for selector in description_selectors:
            try:
                description_element = property_element.find_element(By.CSS_SELECTOR, selector).text
                if description_element:
                    break
            except NoSuchElementException:
                continue
        
        item['descripcion'] = description_element.strip() if description_element else None
        
        # URL de la propiedad - usando los mismos selectores que para la descripción
        property_url = None
        for selector in description_selectors:
            try:
                property_url = property_element.find_element(By.CSS_SELECTOR, selector).get_attribute('href')
                if property_url:
                    break
            except NoSuchElementException:
                continue
        
        item['url'] = property_url
        
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

def scrape_with_retry(base_url, max_retries=3, max_pages=10):
    """Scrapear con reintentos en caso de fallos"""
    properties = []
    current_page = 1
    
    while current_page <= max_pages:
        # Construir la URL para la página actual
        if current_page == 1:
            url = base_url
        else:
            # Construir la URL para las siguientes páginas según el patrón observado
            url = base_url.replace('.html', f'-pagina-{current_page}.html')
        
        print(f"Procesando página {current_page}: {url}")
        
        success = False
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Intento {attempt} de {max_retries} para la página {current_page}")
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
                        page_properties = []
                        for prop_element in property_elements:
                            item = scrape_property(prop_element, driver)
                            if item:
                                # Añadir información de la página
                                item['pagina'] = current_page
                                page_properties.append(item)
                                print(f"Propiedad extraída: {item.get('direccion', 'Sin dirección')} - ${item.get('precio_alquiler', 'N/A')}")
                            
                            time.sleep(human_like_delay())
                        
                        # Si llegamos aquí y tenemos propiedades, el scraping de esta página fue exitoso
                        if page_properties:
                            properties.extend(page_properties)
                            print(f"✅ Página {current_page} scrapeada exitosamente. {len(page_properties)} propiedades extraídas.")
                            success = True
                            break  # Salir del bucle de intentos
                        
                        # Verificar si hay más páginas comprobando la existencia de elementos en esta página
                        has_next = len(page_properties) > 0
                        if not has_next:
                            print(f"No se encontraron propiedades en la página {current_page}. Parece ser la última página.")
                            return properties  # Terminar la extracción
                            
                    except Exception as e:
                        print(f"Error durante el scraping de la página {current_page}: {e}")
                        # Guardar HTML para depuración
                        with open(f'error_page_{current_page}_attempt_{attempt}.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        print(f"HTML guardado como 'error_page_{current_page}_attempt_{attempt}.html'")
                
                finally:
                    # Cerrar el navegador
                    driver.quit()
                    
            except WebDriverException as e:
                print(f"Error de WebDriver en el intento {attempt} de la página {current_page}: {e}")
                time.sleep(10)  # Esperar antes de reintentar
        
        # Si tuvimos éxito en esta página, avanzamos a la siguiente
        if success:
            current_page += 1
            # Esperar entre páginas para simular comportamiento humano
            delay = random.uniform(5.0, 10.0)
            print(f"Esperando {delay:.2f} segundos antes de pasar a la siguiente página...")
            time.sleep(delay)
        else:
            print(f"No se pudo extraer la página {current_page} después de {max_retries} intentos.")
            # Si fallamos en la primera página, terminamos
            if current_page == 1:
                break
            # Si fallamos en una página posterior, devolvemos lo que tenemos hasta ahora
            else:
                print("Continuando con la siguiente página...")
                current_page += 1
    
    return properties

def main():
    """Función principal"""
    print("🚀 Iniciando scraper avanzado de ZonaProp con Selenium")
    print("=" * 50)
    
    # Crear directorios necesarios
    create_directories()
    
    # URL base para scrapear (sin número de página)
    base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html'
    
    # Ejecutar scraping con reintentos y múltiples páginas
    properties = scrape_with_retry(base_url, max_retries=3, max_pages=15)
    
    # Guardar resultados
    if properties:
        save_results(properties)
        print(f"✅ Proceso completado. Se extrajeron {len(properties)} propiedades de múltiples páginas.")
    else:
        print("❌ No se pudieron extraer propiedades")
    
    print("=" * 50)
    print("🎉 Proceso finalizado")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
