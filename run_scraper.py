#!/usr/bin/env python3
"""
Script unificado para extraer datos de ZonaProp
Intenta primero con Scrapy y si falla usa Selenium
"""

import os
import sys
import subprocess
import importlib.util
from datetime import datetime

def create_directories():
    """Crear directorios necesarios"""
    dirs = ['output', 'logs', 'data']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directorio {directory} creado/verificado")

def run_scrapy_spider():
    """Ejecutar el spider de Scrapy"""
    print("🕷️  Intentando extracción con Scrapy...")
    
    # Cambiar al directorio raíz del proyecto Scrapy
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scrapers')
    if os.path.exists(os.path.join(project_root, 'scrapy.cfg')):
        os.chdir(project_root)
    
    # Comando para ejecutar el spider
    cmd = [
        'scrapy', 'crawl', 'zonaprop_spider',
        '-s', 'USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verificar si hay errores 403 en la salida
        if "403 Forbidden" in result.stderr or "403 Forbidden" in result.stdout:
            print("⚠️  El sitio está bloqueando las solicitudes de Scrapy (Error 403)")
            return False
            
        if result.returncode == 0:
            print("✅ Spider ejecutado exitosamente")
            print("📊 Resultados guardados en el directorio 'output'")
            return True
        else:
            print("❌ Error ejecutando el spider:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Error: Scrapy no está instalado o no está en el PATH")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def run_selenium_scraper():
    """Ejecutar el scraper basado en Selenium"""
    print("🌐 Intentando extracción con Selenium...")
    
    # Verificar que el módulo selenium_zonaprop existe
    selenium_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selenium_zonaprop.py')
    
    if not os.path.exists(selenium_path):
        print("❌ No se encontró el script de Selenium en:", selenium_path)
        return False
    
    try:
        # Cargar el módulo dinámicamente
        spec = importlib.util.spec_from_file_location("selenium_zonaprop", selenium_path)
        selenium_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(selenium_module)
        
        # Ejecutar la función principal
        print("Iniciando scraper con Selenium...")
        selenium_module.main()
        return True
        
    except ImportError:
        print("❌ Error: Selenium no está instalado")
        print("💡 Instala Selenium con: pip install selenium")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando el scraper de Selenium: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando extracción de datos de ZonaProp")
    print("=" * 50)
    
    # Crear directorios necesarios
    create_directories()
    
    # Intentar primero con Scrapy
    scrapy_success = run_scrapy_spider()
    
    # Si Scrapy falla, intentar con Selenium
    if not scrapy_success:
        print("🔄 Scrapy no pudo completar la extracción, probando con Selenium...")
        selenium_success = run_selenium_scraper()
        
        if selenium_success:
            print("✅ Extracción con Selenium completada exitosamente")
        else:
            print("❌ La extracción con Selenium también falló")
            print("💡 Considera revisar manualmente el sitio web para entender las protecciones anti-bot")
    else:
        print("✅ Extracción con Scrapy completada exitosamente")
    
    print("=" * 50)
    print("🎉 Proceso finalizado")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
