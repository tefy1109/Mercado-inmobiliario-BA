# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PropiedadItem(scrapy.Item):
    """Item para almacenar datos de propiedades de ZonaProp"""
    
    # Datos económicos
    precio_alquiler = scrapy.Field()
    expensas = scrapy.Field()
    precio_total = scrapy.Field()
    
    # Ubicación
    direccion = scrapy.Field()
    zona = scrapy.Field()
    
    # Características físicas
    superficie = scrapy.Field()
    ambientes = scrapy.Field()
    habitaciones = scrapy.Field()
    banos = scrapy.Field()
    
    # Información adicional
    descripcion = scrapy.Field()
    url = scrapy.Field()
    
    # Metadatos
    scraped_at = scrapy.Field()
