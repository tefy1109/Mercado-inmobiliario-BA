# Define your item pipelines here
import json
import os
from datetime import datetime

class JsonWriterPipeline:
    def open_spider(self, spider):
        # Crear directorio para datos si no existe
        self.data_dir = '../../data/raw'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Crear un archivo JSON para cada ejecución con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.data_dir}/{spider.name}_{timestamp}.json"
        self.file = open(filename, 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True
    
    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()
    
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False)
        if self.first_item:
            self.first_item = False
        else:
            self.file.write(',\n')
        self.file.write(line)
        return item