#!/usr/bin/env python3
"""
Script para verificar la estructura de directorios del proyecto y los archivos de datos.
Asegura que existen las carpetas necesarias y que los permisos son correctos.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def verify_directory_structure():
    """Verifica la estructura de directorios del proyecto."""
    
    # Obtener la ruta base del proyecto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Directorio del proyecto: {project_dir}")
    
    # Definir los directorios que deben existir
    required_dirs = [
        os.path.join(project_dir, 'data'),
        os.path.join(project_dir, 'data', 'raw'),
        os.path.join(project_dir, 'debug'),
    ]
    
    # Verificar y crear cada directorio
    for directory in required_dirs:
        if os.path.exists(directory):
            logging.info(f"✓ Directorio existe: {directory}")
            # Verificar permisos
            try:
                test_file = os.path.join(directory, '.test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logging.info(f"  ✓ Permisos de escritura OK")
            except Exception as e:
                logging.error(f"  ✗ Error de permisos: {str(e)}")
        else:
            logging.warning(f"✗ Directorio faltante: {directory}")
            try:
                os.makedirs(directory, exist_ok=True)
                logging.info(f"  ✓ Directorio creado correctamente")
            except Exception as e:
                logging.error(f"  ✗ No se pudo crear el directorio: {str(e)}")

def check_json_files():
    """Verifica si hay archivos JSON en data/raw."""
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(project_dir, 'data', 'raw')
    
    if not os.path.exists(raw_dir):
        logging.warning(f"El directorio {raw_dir} no existe")
        return
    
    json_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
    
    if not json_files:
        logging.warning(f"No se encontraron archivos JSON en {raw_dir}")
        
        # Crear un archivo JSON de ejemplo si no hay ninguno
        example_file = os.path.join(raw_dir, 'ejemplo_datos.json')
        try:
            with open(example_file, 'w', encoding='utf-8') as f:
                example_data = [
                    {
                        "id_propiedad": "id123456",
                        "precio": "USD 120.000",
                        "moneda": "USD",
                        "expensas": "$45.000",
                        "direccion": "Av. Ejemplo 1234",
                        "barrio_zona": "Palermo",
                        "superficie": "65 m²",
                        "ambientes": "3",
                        "dormitorios": "2",
                        "baños": "1",
                        "url": "https://www.ejemplo.com/propiedad/id123456",
                        "fecha_extraccion": datetime.now().strftime('%Y-%m-%d'),
                        "fuente": "Ejemplo"
                    }
                ]
                json.dump(example_data, f, indent=2, ensure_ascii=False)
            logging.info(f"Se ha creado un archivo JSON de ejemplo: {example_file}")
        except Exception as e:
            logging.error(f"Error al crear archivo de ejemplo: {str(e)}")
    else:
        logging.info(f"Se encontraron {len(json_files)} archivos JSON en {raw_dir}")
        # Mostrar el archivo más reciente
        newest_file = max(json_files, key=lambda x: os.path.getmtime(os.path.join(raw_dir, x)))
        logging.info(f"Archivo más reciente: {newest_file} ({datetime.fromtimestamp(os.path.getmtime(os.path.join(raw_dir, newest_file))).strftime('%Y-%m-%d %H:%M:%S')})")
        
        # Verificar el contenido del archivo más reciente
        try:
            with open(os.path.join(raw_dir, newest_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logging.info(f"  ✓ El archivo contiene {len(data)} propiedades")
                    if data:
                        # Mostrar campos de la primera propiedad
                        first_item = data[0]
                        logging.info(f"  ✓ Ejemplo de propiedad:")
                        for key, value in first_item.items():
                            if value and key != 'descripcion':
                                logging.info(f"    - {key}: {value}")
                else:
                    logging.warning(f"  ✗ El formato del archivo no es una lista JSON")
        except Exception as e:
            logging.error(f"Error al leer el archivo JSON: {str(e)}")

def check_sqlite_db():
    """Verifica la base de datos SQLite."""
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_dir, 'data', 'propiedades.db')
    
    if not os.path.exists(db_path):
        logging.warning(f"La base de datos {db_path} no existe")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla propiedades existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='propiedades'")
        if cursor.fetchone():
            logging.info(f"✓ La tabla 'propiedades' existe en la base de datos")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM propiedades")
            count = cursor.fetchone()[0]
            logging.info(f"  ✓ La tabla contiene {count} registros")
            
            if count > 0:
                # Mostrar algunos campos de la propiedad más reciente
                cursor.execute("SELECT url, precio, moneda, barrio_zona, fecha_extraccion FROM propiedades ORDER BY fecha_extraccion DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    logging.info(f"  ✓ Propiedad más reciente:")
                    logging.info(f"    - URL: {row[0]}")
                    logging.info(f"    - Precio: {row[1]} {row[2]}")
                    logging.info(f"    - Barrio: {row[3]}")
                    logging.info(f"    - Fecha: {row[4]}")
        else:
            logging.warning(f"✗ La tabla 'propiedades' no existe en la base de datos")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error al verificar la base de datos: {str(e)}")

def main():
    """Función principal."""
    print("\n" + "="*70)
    print(" VERIFICACIÓN DE ESTRUCTURA DE DATOS DEL MERCADO INMOBILIARIO ".center(70, "="))
    print("="*70 + "\n")
    
    verify_directory_structure()
    print("\n" + "-"*70)
    check_json_files()
    print("\n" + "-"*70)
    check_sqlite_db()
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
