"""
Configuración de proxies para evadir bloqueos de sitios web
Este script proporciona funciones para configurar y probar proxies
"""

import requests
import random
import time
import logging

logger = logging.getLogger(__name__)

# Lista de proxies gratuitos (reemplazar con proxies pagados para mejor rendimiento)
FREE_PROXIES = [
    # Formato: "http://usuario:contraseña@ip:puerto" o "http://ip:puerto"
    # Reemplazar estos con proxies reales y funcionando
    "http://example-proxy.com:8080",
]

# Lista de proxies pagados (si tienes acceso a servicio de proxies)
PAID_PROXIES = [
    # Tus proxies pagados aquí
]

def get_random_proxy(paid=False):
    """Obtiene un proxy aleatorio de la lista"""
    if paid and PAID_PROXIES:
        return random.choice(PAID_PROXIES)
    elif FREE_PROXIES:
        return random.choice(FREE_PROXIES)
    return None

def test_proxy(proxy_url):
    """Prueba si un proxy funciona correctamente"""
    try:
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Usamos un servicio que devuelve la IP para verificar
        response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
        if response.status_code == 200:
            ip_data = response.json()
            logger.info(f"Proxy funcionando. IP detectada: {ip_data.get('origin', 'desconocida')}")
            return True
        else:
            logger.warning(f"Proxy devolvió código de estado: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error probando proxy {proxy_url}: {str(e)}")
        return False

def find_working_proxy(max_attempts=5):
    """Busca un proxy que funcione entre los disponibles"""
    attempts = 0
    
    # Primero intentar con proxies pagados si están disponibles
    if PAID_PROXIES:
        for proxy in PAID_PROXIES:
            if test_proxy(proxy):
                return proxy
    
    # Luego intentar con proxies gratuitos
    while attempts < max_attempts and FREE_PROXIES:
        proxy = get_random_proxy()
        if test_proxy(proxy):
            return proxy
        attempts += 1
        time.sleep(1)  # Esperar un segundo entre intentos
    
    return None

def configure_proxy_for_scrapy(settings):
    """Configura un proxy para ser usado con Scrapy"""
    proxy = find_working_proxy()
    if proxy:
        settings['HTTPPROXY_ENABLED'] = True
        # Hay dos formas de configurar el proxy:
        
        # 1. Usando el middleware de proxy de Scrapy
        settings['DOWNLOADER_MIDDLEWARES']['scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware'] = 750
        settings['HTTP_PROXY'] = proxy
        
        # 2. Usando un middleware personalizado si necesitas más control
        # settings['DOWNLOADER_MIDDLEWARES']['proyecto.middlewares.ProxyMiddleware'] = 750
        
        logger.info(f"Proxy configurado correctamente: {proxy}")
        return True
    else:
        logger.warning("No se encontró ningún proxy funcional")
        return False

if __name__ == "__main__":
    # Configuración para pruebas
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    # Probar la funcionalidad
    logger.info("Probando proxies disponibles...")
    working_proxy = find_working_proxy()
    
    if working_proxy:
        logger.info(f"Proxy encontrado y funcionando: {working_proxy}")
    else:
        logger.error("No se encontró ningún proxy funcional. Por favor actualiza la lista de proxies.")
