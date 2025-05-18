# Define your item pipelines here
import json
import os
import logging
from datetime import datetime
import sqlite3
from scrapy.exceptions import NotConfigured

class MercadoInmobiliarioPipeline:
    def open_spider(self, spider):
        try:
            # Usar una ruta relativa al directorio del proyecto en lugar de '../../data/raw'
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Crear un archivo JSON para cada ejecución con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.filename = f"{self.data_dir}/{spider.name}_{timestamp}.json"
            self.file = open(self.filename, 'w', encoding='utf-8')
            self.file.write('[\n')
            self.first_item = True
            logging.info(f"Creando archivo {self.filename}")
        except Exception as e:
            logging.error(f"Error al inicializar pipeline: {str(e)}")
            raise
    
    def close_spider(self, spider):
        try:
            self.file.write('\n]')
            self.file.close()
            logging.info(f"Archivo guardado: {self.filename}")
        except Exception as e:
            logging.error(f"Error al cerrar pipeline: {str(e)}")
    
    def process_item(self, item, spider):
        try:
            line = json.dumps(dict(item), ensure_ascii=False)
            if self.first_item:
                self.first_item = False
            else:
                self.file.write(',\n')
            self.file.write(line)
            return item
        except Exception as e:
            logging.error(f"Error procesando item: {str(e)}")
            return item

class SQLitePipeline:
    """Pipeline para almacenar items en una base de datos SQLite."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        # Obtener la ruta de la base de datos desde settings.py
        db_path = crawler.settings.get('SQLITE_DB_PATH')
        if not db_path:
            # Usar una ruta por defecto si no se especificó en settings
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_dir, 'data', 'propiedades.db')
        
        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return cls(db_path)
        
    def open_spider(self, spider):
        """Inicializar la conexión a la base de datos y crear la tabla si no existe."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Crear tabla si no existe con la estructura solicitada
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS propiedades (
                url TEXT PRIMARY KEY,
                titulo TEXT,
                precio REAL,
                moneda TEXT,
                superficie_total REAL,
                superficie_cubierta REAL,
                ambientes INTEGER,
                banos INTEGER,
                dormitorios INTEGER,
                ubicacion TEXT,
                condiciones TEXT,
                fecha_extraccion DATE,
                fuente TEXT
            )
            ''')
            self.conn.commit()
            self.logger.info(f"Conexión establecida con base de datos: {self.db_path}")
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos: {str(e)}")
            raise
    
    def close_spider(self, spider):
        """Cerrar la conexión a la base de datos."""
        try:
            self.conn.close()
            self.logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            self.logger.error(f"Error al cerrar base de datos: {str(e)}")
    
    def process_item(self, item, spider):
        """Procesar cada item y guardarlo en la base de datos."""
        try:
            # Utilizar REPLACE para actualizar si la URL ya existe (previene duplicados)
            self.cursor.execute('''
            INSERT OR REPLACE INTO propiedades 
            (url, titulo, precio, moneda, superficie_total, superficie_cubierta, 
             ambientes, banos, dormitorios, ubicacion, condiciones, fecha_extraccion, fuente)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                item.get('url'),
                item.get('titulo'),
                item.get('precio'),
                item.get('moneda'),
                item.get('superficie_total'),
                item.get('superficie_cubierta'),
                item.get('ambientes'),
                item.get('banos'),
                item.get('dormitorios'),
                item.get('ubicacion'),
                item.get('descripcion'),  # Usando descripcion como condiciones
                item.get('fecha_extraccion'),
                item.get('fuente')
            ))
            self.conn.commit()
            self.logger.debug(f"Guardado en BD: {item.get('url')}")
            return item
        except Exception as e:
            self.logger.error(f"Error guardando item en DB: {str(e)}")
            return item