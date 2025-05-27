#!/usr/bin/env python3
"""
Script para probar la conexión con ZonaProp
"""

import requests
import sys
import time
import random

def test_connection():
    """Probar conexión directa con ZonaProp"""
    url = 'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/search?q=alquiler+departamentos+flores+zonaprop',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    
    cookies = {
        'visita_id': str(random.randint(1000000, 9999999)),
        'c_user_id': str(random.randint(1000000, 9999999)),
        'c_visitor_id': str(random.randint(1000000, 9999999)),
        'gdpr': 'true',
        '_ga': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
        '_gid': f'GA1.3.{random.randint(1000000, 9999999)}.{int(time.time())}',
    }
    
    print(f"Probando conexión a {url}")
    print("=" * 50)
    print("Usando headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    print("=" * 50)
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('Content-Type')}")
        print(f"Encoding: {response.encoding}")
        print("=" * 50)
        
        if response.status_code == 200:
            print("✅ Conexión exitosa!")
            
            # Guardar la respuesta HTML para inspección
            with open('test_connection_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print("Respuesta guardada en 'test_connection_response.html'")
            
            # Verificar si es la página esperada o un captcha/bloqueo
            if 'postingCards' in response.text or 'postingCard' in response.text:
                print("✅ El contenido parece ser el esperado (listado de propiedades)")
            else:
                print("❌ El contenido no parece ser un listado de propiedades (posible captcha o bloqueo)")
                
        else:
            print(f"❌ Error en la conexión: {response.status_code}")
            print(response.text[:500])  # Mostrar parte del texto de error
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
if __name__ == "__main__":
    test_connection()
