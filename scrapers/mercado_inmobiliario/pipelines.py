# Define your item pipelines here
import json
import os
from datetime import datetime
import logging

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