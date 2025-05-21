#!/usr/bin/env python3
"""
Script para listar y visualizar los archivos de datos extraídos.
Ayuda a encontrar y analizar rápidamente los archivos JSON generados.
"""

import os
import argparse
import json
from datetime import datetime
import sqlite3
import glob

def list_json_files(data_dir='data/raw', n=5):
    """Lista los archivos JSON más recientes en el directorio de datos"""
    # Obtener el directorio absoluto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_dir, data_dir)
    
    if not os.path.exists(data_path):
        print(f"⚠️  El directorio {data_path} no existe")
        return []
    
    # Obtener todos los archivos JSON
    json_files = glob.glob(os.path.join(data_path, "*.json"))
    
    if not json_files:
        print(f"⚠️  No se encontraron archivos JSON en {data_path}")
        return []
    
    # Ordenar por fecha de modificación (más reciente primero)
    json_files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"\n📁 ARCHIVOS JSON MÁS RECIENTES ({min(n, len(json_files))} de {len(json_files)}):")
    print("-" * 80)
    
    # Mostrar solo los N más recientes
    for i, file_path in enumerate(json_files[:n]):
        filename = os.path.basename(file_path)
        size_kb = os.path.getsize(file_path) / 1024
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # Contar items en el archivo
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                item_count = len(data) if isinstance(data, list) else 1
        except:
            item_count = "Error"
        
        print(f"{i+1}. {filename}")
        print(f"   📄 Ruta: {os.path.abspath(file_path)}")
        print(f"   📊 Items: {item_count}  |  📦 Tamaño: {size_kb:.1f} KB")
        print(f"   🕒 Fecha: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
    
    return json_files[:n]

def show_database_stats():
    """Muestra estadísticas de la base de datos SQLite"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_dir, 'data', 'propiedades.db')
    
    if not os.path.exists(db_path):
        print(f"⚠️  Base de datos no encontrada: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener el conteo total de propiedades
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        total = cursor.fetchone()[0]
        
        # Obtener conteo por fuente
        cursor.execute("SELECT fuente, COUNT(*) FROM propiedades GROUP BY fuente")
        sources = cursor.fetchall()
        
        # Obtener conteo por fechas de extracción (top 5)
        cursor.execute("SELECT fecha_extraccion, COUNT(*) FROM propiedades GROUP BY fecha_extraccion ORDER BY fecha_extraccion DESC LIMIT 5")
        dates = cursor.fetchall()
        
        print("\n📊 ESTADÍSTICAS DE LA BASE DE DATOS:")
        print("-" * 80)
        print(f"📂 Base de datos: {os.path.abspath(db_path)}")
        print(f"📈 Total propiedades: {total}")
        
        print("\nFuentes de datos:")
        for source, count in sources:
            print(f"  - {source}: {count} propiedades")
        
        print("\nÚltimas extracciones:")
        for date, count in dates:
            print(f"  - {date}: {count} propiedades")
        
        conn.close()
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {str(e)}")

def view_json_contents(file_path, limit=5):
    """Muestra el contenido de un archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            data = [data]
            
        print(f"\n📑 CONTENIDO DEL ARCHIVO: {os.path.basename(file_path)}")
        print(f"📊 Total de items: {len(data)}")
        print("-" * 80)
        
        # Mostrar solo los primeros N items
        for i, item in enumerate(data[:limit]):
            print(f"Item {i+1}:")
            # Mostrar solo algunos campos clave
            for key in ['id_propiedad', 'precio', 'moneda', 'direccion', 'barrio_zona', 'ambientes', 'url']:
                if key in item and item[key] is not None:
                    value = item[key]
                    # Truncar textos largos
                    if isinstance(value, str) and len(value) > 80:
                        value = value[:77] + "..."
                    print(f"  - {key}: {value}")
            print()
            
        if len(data) > limit:
            print(f"... y {len(data) - limit} items más")
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Herramienta para listar y analizar datos extraídos')
    parser.add_argument('--dir', default='data/raw', help='Directorio donde buscar los archivos JSON')
    parser.add_argument('--view', type=int, help='Ver contenido del archivo número N de la lista')
    parser.add_argument('--limit', type=int, default=5, help='Cantidad máxima de archivos o items a mostrar')
    parser.add_argument('--db', action='store_true', help='Mostrar estadísticas de la base de datos')
    
    args = parser.parse_args()
    
    # Listar archivos JSON
    json_files = list_json_files(args.dir, args.limit)
    
    # Ver contenido de un archivo específico
    if args.view is not None and json_files:
        if 1 <= args.view <= len(json_files):
            view_json_contents(json_files[args.view - 1], args.limit)
        else:
            print(f"⚠️  Número de archivo inválido. Debe ser entre 1 y {len(json_files)}")
    
    # Mostrar estadísticas de la base de datos
    if args.db:
        show_database_stats()

if __name__ == "__main__":
    main()
