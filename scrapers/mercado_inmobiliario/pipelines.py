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
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.data_dir = os.path.join(project_dir, 'data', 'raw')
            
            # Verificar si el directorio existe y crearlo si no existe
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
            
            # Crear un archivo JSON para cada ejecución con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.filename = f"{spider.name}_{timestamp}.json"
            self.filepath = os.path.join(self.data_dir, self.filename)
            
            # Asegurar que podemos escribir en el archivo
            self.file = open(self.filepath, 'w', encoding='utf-8')
            self.file.write('[\n')
            self.first_item = True
            
            logging.info(f"Guardando datos en: {self.filepath}")
            
            # Guardar información sobre calidad de los datos
            self.items_count = 0
            self.empty_items_count = 0
            
            # Crear un archivo simple con información sobre la extracción
            info_file = os.path.join(self.data_dir, f"{spider.name}_{timestamp}_info.txt")
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Extracción iniciada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Spider: {spider.name}\n")
                f.write(f"URLs iniciales: {spider.start_urls}\n")
                f.write(f"Páginas máximas: {spider.max_pages}\n")
                
        except Exception as e:
            logging.error(f"Error al inicializar pipeline: {str(e)}")
            raise
    
    def close_spider(self, spider):
        try:
            # Añadir un elemento vacío si no se encontró ningún item, para evitar JSON inválido
            if self.first_item:
                self.file.write('{}')
                
            self.file.write('\n]')
            self.file.close()
            
            # Verificar que el archivo JSON se haya creado correctamente
            if os.path.exists(self.filepath):
                file_size = os.path.getsize(self.filepath)
                if file_size > 10:  # Al menos debe tener los corchetes y algún contenido
                    logging.info(f"Archivo JSON creado correctamente: {self.filepath} ({file_size} bytes)")
                else:
                    logging.warning(f"El archivo JSON parece estar vacío o corrupto: {self.filepath}")
                    
                    # Intentar reparar el archivo si está corrupto
                    try:
                        with open(self.filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if content.strip() == '[' or content.strip() == '[\n':
                            with open(self.filepath, 'w', encoding='utf-8') as f:
                                f.write('[\n{}]')  # JSON válido
                            logging.info(f"Archivo JSON reparado con contenido vacío")
                    except:
                        logging.error(f"No se pudo reparar el archivo JSON")
            else:
                logging.error(f"El archivo JSON no fue creado: {self.filepath}")
            
            # Actualizar el archivo de información
            timestamp = self.filename.split('_')[1].split('.')[0]
            info_file = os.path.join(self.data_dir, f"{spider.name}_{timestamp}_info.txt")
            if os.path.exists(info_file):
                with open(info_file, 'a', encoding='utf-8') as f:
                    f.write(f"Extracción finalizada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Items extraídos: {self.items_count}\n")
                    f.write(f"Items vacíos: {self.empty_items_count}\n")
            
            logging.info(f"Extracción finalizada. Items procesados: {self.items_count}, vacíos: {self.empty_items_count}")
            
        except Exception as e:
            logging.error(f"Error al cerrar pipeline: {str(e)}")
    
    def process_item(self, item, spider):
        try:
            self.items_count += 1
            
            # Verificar si el item está vacío (todos los campos excepto url son None)
            if all(v is None for k, v in item.items() if k != 'url'):
                self.empty_items_count += 1
                logging.warning(f"Item vacío detectado para URL: {item.get('url', 'URL desconocida')}")
            
            # Convertir el item a formato compatible con JSON
            line = json.dumps(dict(item), ensure_ascii=False)
            
            if self.first_item:
                self.first_item = False
            else:
                self.file.write(',\n')
            self.file.write(line)
            
            # Forzar escritura al disco periódicamente para evitar pérdida de datos
            if self.items_count % 10 == 0:
                self.file.flush()
                os.fsync(self.file.fileno())
            
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
                precio TEXT,
                moneda TEXT,
                expensas TEXT,
                superficie_total TEXT,
                superficie_cubierta TEXT,
                ambientes TEXT,
                banos TEXT,
                dormitorios TEXT,
                direccion TEXT,
                barrio_zona TEXT,
                descripcion TEXT,
                fecha_extraccion TEXT,
                fuente TEXT
            )
            ''')
            self.conn.commit()
            self.logger.info(f"Conexión establecida con base de datos: {self.db_path}")
            
            # Contadores para estadísticas
            self.items_processed = 0
            self.items_saved = 0
        except Exception as e:
            self.logger.error(f"Error al inicializar base de datos: {str(e)}")
            raise
    
    def close_spider(self, spider):
        """Cerrar la conexión a la base de datos."""
        try:
            self.conn.close()
            self.logger.info(f"Conexión a base de datos cerrada. Items procesados: {self.items_processed}, guardados: {self.items_saved}")
        except Exception as e:
            self.logger.error(f"Error al cerrar base de datos: {str(e)}")
    
    def process_item(self, item, spider):
        """Procesar cada item y guardarlo en la base de datos."""
        try:
            self.items_processed += 1
            
            # Extraer moneda del precio si está disponible
            precio = item.get('precio')
            moneda = None
            
            if precio:
                # Intentar extraer moneda del precio (USD, $, etc.)
                if 'USD' in precio or 'U$S' in precio or 'U$D' in precio:
                    moneda = 'USD'
                elif '$' in precio:
                    moneda = 'ARS'
            
            # Verificar si hay datos significativos para guardar
            if not any([item.get('precio'), item.get('direccion'), item.get('barrio_zona'), 
                        item.get('superficie'), item.get('ambientes')]):
                self.logger.warning(f"Item sin datos significativos para {item.get('url')}, no se guardará en BD")
                return item
            
            # Utilizar REPLACE para actualizar si la URL ya existe (previene duplicados)
            self.cursor.execute('''
            INSERT OR REPLACE INTO propiedades 
            (url, precio, moneda, expensas, superficie_total, superficie_cubierta, 
             ambientes, banos, dormitorios, direccion, barrio_zona, descripcion, fecha_extraccion, fuente)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                item.get('url'),
                item.get('precio'),
                moneda,
                item.get('expensas'),
                item.get('superficie'),
                item.get('superficie_cubierta'),
                item.get('ambientes'),
                item.get('baños'),
                item.get('dormitorios'),
                item.get('direccion'),
                item.get('barrio_zona'),
                item.get('descripcion'),
                item.get('fecha_extraccion'),
                item.get('fuente')
            ))
            self.conn.commit()
            self.items_saved += 1
            self.logger.debug(f"Guardado en BD: {item.get('url')}")
            return item
        except Exception as e:
            self.logger.error(f"Error guardando item en DB: {str(e)}")
            return item