#!/usr/bin/env python3
"""
Script para extraer datos de ZonaProp usando Selenium
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Crear directorios necesarios
os.makedirs('output', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Configurar el navegador
chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Valores para user-agent aleatorios
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
]

chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

# Lista de propiedades para almacenar
properties = []

def human_like_delay():
    """Genera un delay que simula comportamiento humano"""
    return random.uniform(1.5, 4.0)

def scrape_property(property_element):
    """Extrae datos de una propiedad individual"""
    item = {}
    
    try:
        # Precio de alquiler
        try:
            price_element = property_element.find_element(By.CSS_SELECTOR, 'div[data-qa="POSTING_CARD_PRICE"]').text
            if price_element:
                # Limpia el precio (remueve $ y puntos)
                price_clean = re.sub(r'[^\d]', '', price_element)
                item['precio_alquiler'] = int(price_clean) if price_clean else None
        except (NoSuchElementException, ValueError):
            item['precio_alquiler'] = None

        # Expensas
        try:
            expenses_element = property_element.find_element(By.CSS_SELECTOR, 'div[data-qa="expensas"]').text
            if expenses_element:
                expenses_clean = re.sub(r'[^\d]', '', expenses_element)
                item['expensas'] = int(expenses_clean) if expenses_clean else None
        except (NoSuchElementException, ValueError):
            item['expensas'] = None

        # Dirección
        try:
            address_element = property_element.find_element(By.CSS_SELECTOR, 'div[data-qa="POSTING_CARD_LOCATION"]').text
            item['direccion'] = address_element.strip() if address_element else None
        except NoSuchElementException:
            item['direccion'] = None

        # Zona
        item['zona'] = 'Flores'  # Hardcoded según la búsqueda

        # Características (superficie, ambientes, habitaciones, baños)
        item['superficie'] = None
        item['ambientes'] = None
        item['habitaciones'] = None
        item['banos'] = None

        try:
            features = property_element.find_elements(By.CSS_SELECTOR, 'div[data-qa="POSTING_CARD_FEATURES"] span')
            
            for i, feature in enumerate(features):
                feature_text = feature.text.strip()
                
                if 'm²' in feature_text:  # Superficie
                    match = re.search(r'(\d+)', feature_text)
                    if match:
                        item['superficie'] = int(match.group(1))
                
                elif 'amb' in feature_text:  # Ambientes
                    match = re.search(r'(\d+)', feature_text)
                    if match:
                        item['ambientes'] = int(match.group(1))
                
                elif 'dorm' in feature_text:  # Habitaciones
                    match = re.search(r'(\d+)', feature_text)
                    if match:
                        item['habitaciones'] = int(match.group(1))
                
                elif 'baño' in feature_text:  # Baños
                    match = re.search(r'(\d+)', feature_text)
                    if match:
                        item['banos'] = int(match.group(1))
        
        except NoSuchElementException:
            pass  # No hay características disponibles
        
        # Título/Descripción
        try:
            description_element = property_element.find_element(By.CSS_SELECTOR, 'h2[data-qa="POSTING_CARD_TITLE"]').text
            item['descripcion'] = description_element.strip() if description_element else None
        except NoSuchElementException:
            item['descripcion'] = None
        
        # URL
        try:
            property_url = property_element.find_element(By.CSS_SELECTOR, 'a[data-qa="POSTING_CARD_LINK"]').get_attribute('href')
            item['url'] = property_url
        except NoSuchElementException:
            item['url'] = None

        # Timestamp
        item['scraped_at'] = datetime.now().isoformat()
        
        return item
    
    except Exception as e:
        print(f"Error procesando propiedad: {e}")
        return None

def save_results():
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
    fieldnames = [
        'precio_alquiler', 'expensas', 'direccion', 'zona',
        'superficie', 'ambientes', 'habitaciones', 'banos', 
        'descripcion', 'url', 'scraped_at'
    ]
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for prop in properties:
            # Asegurar que todos los campos existan
            row = {field: prop.get(field, '') for field in fieldnames}
            writer.writerow(row)
    print(f"Guardados {len(properties)} ítems en {csv_filename}")

def main():
    """Función principal de scraping"""
    print("🚀 Iniciando scraping de ZonaProp con Selenium...")
    
    # Iniciar el navegador
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(user_agents)})
    
    try:
        # Primero visitar Google para disimular
        driver.get('https://www.google.com')
        time.sleep(human_like_delay())
        
        # Buscar en Google
        try:
            search_box = driver.find_element(By.NAME, 'q')
            search_term = "alquiler departamentos flores zonaprop"
            for char in search_term:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))  # Simular tipeo humano
            time.sleep(human_like_delay())
            search_box.submit()
            time.sleep(human_like_delay())
        except Exception:
            # Si falla, continuar directamente a ZonaProp
            print("No se pudo buscar en Google, continuando directamente...")

        # Navegar a ZonaProp
        target_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html'
        print(f"Navegando a {target_url}")
        driver.get(target_url)
        time.sleep(human_like_delay() * 2)  # Esperar más tiempo en la página inicial
        
        # Si hay un captcha o pop-up, dar tiempo para resolverlo manualmente
        input("Si aparece un captcha o pop-up, resuélvelo manualmente y luego presiona Enter para continuar...")
        
        # Número máximo de páginas a scrapear (ajustar según necesidad)
        max_pages = 5
        current_page = 1
        
        while current_page <= max_pages:
            print(f"Scrapeando página {current_page}...")
            
            # Esperar a que las propiedades se carguen
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-qa="posting PROPERTY"]'))
                )
            except TimeoutException:
                print("No se pudieron cargar las propiedades, verificando posibles alternativas...")
                
                # Intentar un selector alternativo
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.postingCard'))
                    )
                except TimeoutException:
                    print("No se encontraron propiedades en esta página")
                    # Verificar si hay un mensaje de error o bloqueo
                    page_source = driver.page_source
                    if "403" in page_source or "Forbidden" in page_source or "Robot" in page_source:
                        print("Detectada página de bloqueo (403 Forbidden)")
                        break
            
            # Guardar el HTML para depuración
            with open(f'debug_page_{current_page}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            # Intentar encontrar propiedades con diferentes selectores
            property_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-qa="posting PROPERTY"]')
            
            if not property_elements:
                property_elements = driver.find_elements(By.CSS_SELECTOR, 'div.postingCard')
            
            print(f"Encontradas {len(property_elements)} propiedades en la página {current_page}")
            
            # Procesar cada propiedad
            for property_element in property_elements:
                # Scroll hasta el elemento para asegurar que esté visible
                driver.execute_script("arguments[0].scrollIntoView(true);", property_element)
                time.sleep(random.uniform(0.5, 1.0))
                
                item = scrape_property(property_element)
                if item:
                    properties.append(item)
                    print(f"Propiedad extraída: {item.get('direccion', 'Sin dirección')} - ${item.get('precio_alquiler', 'N/A')}")
                
                time.sleep(human_like_delay())
            
            # Buscar el botón de siguiente página
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Siguiente"]')
                if next_button.is_enabled():
                    # Scroll hasta el botón
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(human_like_delay())
                    
                    # Hacer clic en siguiente
                    next_button.click()
                    current_page += 1
                    time.sleep(human_like_delay() * 2)  # Esperar que cargue la nueva página
                else:
                    print("Botón de siguiente página deshabilitado, fin del scraping")
                    break
            except NoSuchElementException:
                print("No se encontró botón de siguiente página, fin del scraping")
                break
        
        # Guardar resultados
        save_results()
        print(f"✅ Scraping completado. Se extrajeron {len(properties)} propiedades.")
    
    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")
    finally:
        # Cerrar el navegador
        driver.quit()

if __name__ == "__main__":
    main()
