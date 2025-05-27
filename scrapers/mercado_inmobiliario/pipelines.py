import json
import csv
import os
from datetime import datetime
from scrapy.exceptions import DropItem
import logging


class ValidationPipeline:
    """Pipeline para validar los items extraídos"""
    
    def process_item(self, item, spider):
        # Validar que tenga al menos precio o dirección
        if not item.get('precio_alquiler') and not item.get('direccion'):
            raise DropItem(f"Item sin precio ni dirección: {item}")
        
        # Validar tipos de datos
        numeric_fields = ['precio_alquiler', 'expensas', 'superficie', 'ambientes', 'habitaciones', 'banos']
        for field in numeric_fields:
            if item.get(field) is not None:
                try:
                    item[field] = int(item[field]) if item[field] != '' else None
                except (ValueError, TypeError):
                    spider.logger.warning(f"Valor inválido en {field}: {item.get(field)}")
                    item[field] = None
        
        return item


class CleaningPipeline:
    """Pipeline para limpiar y normalizar los datos"""
    
    def process_item(self, item, spider):
        # Limpiar strings
        string_fields = ['direccion', 'zona', 'descripcion']
        for field in string_fields:
            if item.get(field):
                # Remover espacios extra y caracteres especiales
                item[field] = ' '.join(item[field].split())
                item[field] = item[field].strip()
        
        # Normalizar zona
        if item.get('zona'):
            item['zona'] = item['zona'].title()
        
        # Agregar timestamp
        item['scraped_at'] = datetime.now().isoformat()
        
        # Calcular precio total (alquiler + expensas)
        if item.get('precio_alquiler') and item.get('expensas'):
            item['precio_total'] = item['precio_alquiler'] + item['expensas']
        elif item.get('precio_alquiler'):
            item['precio_total'] = item['precio_alquiler']
        else:
            item['precio_total'] = None
        
        # Agregar URL limpia si existe
        if item.get('url'):
            item['url'] = item['url'].split('?')[0]  # Remover parámetros de query
        
        return item


class DuplicatesPipeline:
    """Pipeline para filtrar items duplicados"""
    
    def __init__(self):
        self.seen = set()
    
    def process_item(self, item, spider):
        # Crear un identificador único basado en dirección y precio
        identifier = f"{item.get('direccion', '')}_{item.get('precio_alquiler', '')}"
        
        if identifier in self.seen:
            raise DropItem(f"Item duplicado: {item}")
        else:
            self.seen.add(identifier)
            return item


class JsonPipeline:
    """Pipeline para guardar en formato JSON"""
    
    def __init__(self):
        self.items = []
    
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider):
        # Crear directorio si no existe
        os.makedirs('output', exist_ok=True)
        
        # Nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'output/zonaprop_propiedades_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"Guardados {len(self.items)} items en {filename}")


class CsvPipeline:
    """Pipeline para guardar en formato CSV"""
    
    def __init__(self):
        self.items = []
        self.fieldnames = [
            'precio_alquiler', 'expensas', 'precio_total', 'direccion', 'zona',
            'superficie', 'ambientes', 'habitaciones', 'banos', 'descripcion',
            'url', 'scraped_at'
        ]
    
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item
    
    def close_spider(self, spider):
        if not self.items:
            return
        
        # Crear directorio si no existe
        os.makedirs('output', exist_ok=True)
        
        # Nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'output/zonaprop_propiedades_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            
            for item in self.items:
                # Asegurar que todos los campos existan
                row = {field: item.get(field, '') for field in self.fieldnames}
                writer.writerow(row)
        
        spider.logger.info(f"Guardados {len(self.items)} items en {filename}")


class StatsPipeline:
    """Pipeline para generar estadísticas"""
    
    def __init__(self):
        self.items_count = 0
        self.price_stats = []
        self.zona_stats = {}
    
    def process_item(self, item, spider):
        self.items_count += 1
        
        # Estadísticas de precios
        if item.get('precio_alquiler'):
            self.price_stats.append(item['precio_alquiler'])
        
        # Estadísticas por zona
        zona = item.get('zona', 'Sin zona')
        self.zona_stats[zona] = self.zona_stats.get(zona, 0) + 1
        
        return item
    
    def close_spider(self, spider):
        spider.logger.info(f"=== ESTADÍSTICAS DEL SCRAPING ===")
        spider.logger.info(f"Total de propiedades: {self.items_count}")
        
        if self.price_stats:
            spider.logger.info(f"Precio promedio: ${sum(self.price_stats) / len(self.price_stats):,.0f}")
            spider.logger.info(f"Precio mínimo: ${min(self.price_stats):,.0f}")
            spider.logger.info(f"Precio máximo: ${max(self.price_stats):,.0f}")
        
        spider.logger.info(f"Propiedades por zona:")
        for zona, count in self.zona_stats.items():
            spider.logger.info(f"  {zona}: {count}")


class DatabasePipeline:
    """Pipeline para guardar en base de datos (SQLite como ejemplo)"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def open_spider(self, spider):
        try:
            import sqlite3
            
            # Crear directorio para la base de datos
            os.makedirs('data', exist_ok=True)
            
            self.connection = sqlite3.connect('data/zonaprop.db')
            self.cursor = self.connection.cursor()
            
            # Crear tabla si no existe
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS propiedades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    precio_alquiler INTEGER,
                    expensas INTEGER,
                    precio_total INTEGER,
                    direccion TEXT,
                    zona TEXT,
                    superficie INTEGER,
                    ambientes INTEGER,
                    habitaciones INTEGER,
                    banos INTEGER,
                    descripcion TEXT,
                    url TEXT,
                    scraped_at TEXT,
                    UNIQUE(direccion, precio_alquiler)
                )
            ''')
            self.connection.commit()
            
        except ImportError:
            spider.logger.warning("SQLite no disponible. Pipeline de base de datos deshabilitado.")
            self.connection = None
    
    def process_item(self, item, spider):
        if not self.connection:
            return item
        
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO propiedades 
                (precio_alquiler, expensas, precio_total, direccion, zona, superficie, 
                 ambientes, habitaciones, banos, descripcion, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('precio_alquiler'),
                item.get('expensas'),
                item.get('precio_total'),
                item.get('direccion'),
                item.get('zona'),
                item.get('superficie'),
                item.get('ambientes'),
                item.get('habitaciones'),
                item.get('banos'),
                item.get('descripcion'),
                item.get('url'),
                item.get('scraped_at')
            ))
            self.connection.commit()
            
        except Exception as e:
            spider.logger.error(f"Error guardando en base de datos: {e}")
        
        return item
    
    def close_spider(self, spider):
        if self.connection:
            self.connection.close()