import scrapy
from scrapy.exceptions import CloseSpider
import logging

class ZonapropSpider(scrapy.Spider):
    name = 'zonaprop_spider'
    allowed_domains = ['zonaprop.com.ar']
    start_urls = ['https://www.zonaprop.com.ar/departamentos-alquiler-flores.html']
    
    # Variables de configuración
    max_pages = 20  # Límite de páginas a recorrer
    
    # Contador de páginas
    pages_visited = 0
    
    def parse(self, response):
        """
        Método principal para procesar las páginas de listado de propiedades
        """
        self.pages_visited += 1
        
        # Extraer los enlaces a los detalles de cada propiedad
        # Basado en la estructura vista en la imagen
        property_links = response.xpath('//div[contains(@class, "postingCardLayout-module__posting-card-layout")]/a/@href').getall()
        
        if not property_links:
            # Intentar con otro selector si el primero no funciona
            property_links = response.xpath('//div[contains(@data-qa, "posting PROPERTY")]/@data-to-posting').getall()
        
        self.logger.info(f"Encontradas {len(property_links)} propiedades en {response.url}")
        
        # Seguir cada enlace de propiedad para extraer detalles
        for link in property_links:
            # Si el enlace no comienza con http, añadir el dominio
            if not link.startswith('http'):
                link = f"https://www.zonaprop.com.ar/propiedades/clasificado/{link}"
            yield response.follow(link, callback=self.parse_property)
        
        # Verificar si hay una página siguiente
        next_page = response.xpath('//a[@aria-label="Siguiente"]/@href').get()
        if not next_page:
            next_page = response.xpath('//a[contains(@class, "pagination") and contains(text(), "Siguiente")]/@href').get()
        
        if next_page and self.pages_visited < self.max_pages:
            self.logger.info(f"Navegando a la siguiente página: {next_page}")
            yield response.follow(next_page, callback=self.parse)
    
    def parse_property(self, response):
        """
        Método para procesar las páginas de detalle de propiedades
        """
        # Extraer toda la información relevante de la propiedad
        precio_principal = response.xpath('//*[@id="article-container"]/div[1]/div/div[1]/span[1]/span/text()').get()
        if not precio_principal:
            precio_principal = response.xpath('//div[@class="price-value"]//span/span/text()').get()
        
        expensas = response.xpath('//*[@id="article-container"]/div[1]/div/div[3]/span/text()').get()
        if not expensas:
            expensas = response.xpath('/html//div[2]/main/div/div/article/div/div[1]/div/div[3]/span/text()').get()
        
        direccion = response.xpath('//*[@id="map-section"]/div[1]/h4').get()
        if not direccion:
            direccion = response.xpath('/html//div[2]/main/div/div/article/div/section[2]/div[1]/h4').get()
        
        barrio_zona = response.xpath('//h2[contains(@class, "title-location")]/following-sibling::span/text()').get()
        
        # Características básicas
        superficie = response.xpath('//*[@id="article-container"]/h2').get()
        ambientes = response.xpath('//*[@id="article-container"]/h2').get()
        dormitorios = response.xpath('//span[contains(text(), "Dormitorios")]/following-sibling::span/text()').get()
        baños = response.xpath('//span[contains(text(), "Baños")]/following-sibling::span/text()').get()
        
        # Descripción
        descripcion = response.xpath('//div[contains(@class, "description")]//p/text()').getall()
        if not descripcion:
            descripcion = response.xpath('//div[contains(@class, "description")]/text()').getall()

        
        yield {
            'precio': precio_principal.strip() if precio_principal else None,
            'expensas': expensas.strip() if expensas else None,
            'direccion': direccion.strip() if direccion else None,
            'barrio_zona': barrio_zona.strip() if barrio_zona else None,
            'superficie': superficie.strip() if superficie else None,
            'ambientes': ambientes.strip() if ambientes else None,
            'dormitorios': dormitorios.strip() if dormitorios else None,
            'baños': baños.strip() if baños else None,
            'descripcion': ' '.join([d.strip() for d in descripcion]) if descripcion else None,
            'url': response.url,
        }
    
    def __init__(self, *args, **kwargs):
        super(ZonapropSpider, self).__init__(*args, **kwargs)
        # Puedes configurar parámetros desde la línea de comandos
        if 'max_pages' in kwargs:
            self.max_pages = int(kwargs.get('max_pages'))
        if 'start_url' in kwargs:
            self.start_urls = [kwargs.get('start_url')]

# Para ejecutar:
# scrapy crawl zonaprop_spider -o propiedades.json