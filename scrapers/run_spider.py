#!/usr/bin/env python3
"""
Script para ejecutar el spider de ZonaProp
"""

import os
import sys
import subprocess
from datetime import datetime


def create_directories():
    """Crear directorios necesarios"""
    dirs = ['output', 'logs', 'data']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directorio {directory} creado/verificado")


def run_spider():
    """Ejecutar el spider"""
    print("🕷️  Iniciando spider de ZonaProp...")
    
    # Cambiar al directorio raíz del proyecto Scrapy si no estamos ahí
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists('scrapy.cfg') and os.path.exists(os.path.join(project_root, 'scrapy.cfg')):
        print(f"Cambiando al directorio raíz del proyecto: {project_root}")
        os.chdir(project_root)
    
    # Comando para ejecutar el spider
    cmd = [
        'scrapy', 'crawl', 'zonaprop_spider',  # Cambiado de 'zonaprop' a 'zonaprop_spider' para coincidir con el nombre en el archivo del spider
        '-s', 'USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Spider ejecutado exitosamente")
            print("📊 Resultados guardados en el directorio 'output'")
        else:
            print("❌ Error ejecutando el spider:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌ Error: Scrapy no está instalado o no está en el PATH")
        print("💡 Instala Scrapy con: pip install scrapy")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


def main():
    """Función principal"""
    print("🚀 Configurando entorno para ZonaProp Spider")
    print("=" * 50)
    
    # Crear directorios
    create_directories()
    
    # Verificar que estamos en un proyecto Scrapy
    if not os.path.exists('scrapy.cfg'):
        print("⚠️  Advertencia: No se detectó scrapy.cfg")
        print("💡 Asegúrate de estar en la raíz del proyecto Scrapy")
    
    # Ejecutar spider
    run_spider()
    
    print("=" * 50)
    print("🎉 Proceso completado")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()