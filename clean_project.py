#!/usr/bin/env python3
"""
Script para limpiar archivos innecesarios del proyecto.
Elimina archivos de debug HTML, logs extensos, y otros archivos temporales.
"""

import os
import sys
import argparse
import glob
import shutil
import time
from datetime import datetime, timedelta

def clean_debug_files():
    """Elimina todos los archivos HTML de debug"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    debug_dir = os.path.join(project_dir, 'debug')
    
    if os.path.exists(debug_dir):
        print(f"Eliminando directorio de debug: {debug_dir}")
        try:
            shutil.rmtree(debug_dir)
            print(f"✅ Directorio de debug eliminado correctamente")
        except Exception as e:
            print(f"❌ Error al eliminar el directorio debug: {str(e)}")
    else:
        print(f"El directorio de debug no existe: {debug_dir}")

def clean_log_files(days_old=None):
    """Elimina archivos de log antiguos"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    log_files = glob.glob(os.path.join(project_dir, "*.log"))
    log_files += glob.glob(os.path.join(project_dir, "scrapy_*.log"))
    
    count = 0
    for log_file in log_files:
        delete = True
        
        # Si se especifica days_old, verificar la fecha de modificación
        if days_old:
            mtime = os.path.getmtime(log_file)
            file_date = datetime.fromtimestamp(mtime)
            cutoff_date = datetime.now() - timedelta(days=days_old)
            if file_date > cutoff_date:
                delete = False
        
        if delete:
            try:
                os.remove(log_file)
                count += 1
            except Exception as e:
                print(f"❌ Error al eliminar {log_file}: {str(e)}")
    
    print(f"✅ Eliminados {count} archivos de log")

def clean_temp_files():
    """Elimina archivos temporales y de caché"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Eliminar archivos .pyc
    pyc_files = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    count = 0
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            count += 1
        except Exception as e:
            print(f"❌ Error al eliminar {pyc_file}: {str(e)}")
    
    print(f"✅ Eliminados {count} archivos .pyc")
    
    # Eliminar directorios __pycache__
    pycache_dirs = []
    for root, dirs, files in os.walk(project_dir):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir_name))
    
    count = 0
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            count += 1
        except Exception as e:
            print(f"❌ Error al eliminar {pycache_dir}: {str(e)}")
    
    print(f"✅ Eliminados {count} directorios __pycache__")

def main():
    parser = argparse.ArgumentParser(description='Limpiar archivos innecesarios del proyecto')
    parser.add_argument('--all', action='store_true', help='Eliminar todos los archivos innecesarios')
    parser.add_argument('--debug', action='store_true', help='Eliminar archivos de debug (HTML)')
    parser.add_argument('--logs', action='store_true', help='Eliminar archivos de log')
    parser.add_argument('--temp', action='store_true', help='Eliminar archivos temporales (.pyc, __pycache__)')
    parser.add_argument('--days', type=int, help='Eliminar solo archivos más antiguos que N días')
    
    args = parser.parse_args()
    
    # Si no se especifica ninguna opción, mostrar la ayuda
    if not (args.all or args.debug or args.logs or args.temp):
        parser.print_help()
        return
    
    if args.all or args.debug:
        clean_debug_files()
    
    if args.all or args.logs:
        clean_log_files(args.days)
    
    if args.all or args.temp:
        clean_temp_files()
    
    print("\n✅ Limpieza completada")

if __name__ == "__main__":
    main()
