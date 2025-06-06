# Análisis del Mercado Inmobiliario de Buenos Aires

Este proyecto realiza web scraping y análisis de datos del mercado inmobiliario de Buenos Aires, Argentina, utilizando técnicas de extracción automatizada para obtener información de propiedades en alquiler desde ZonaProp.

## 🎯 Objetivos del Proyecto

- **Web Scraping Avanzado**: Extracción automatizada de datos inmobiliarios de ZonaProp
- **Análisis de Datos**: Obtener información detallada de precios de alquiler y analizar los mismo, visualizando el resultado en Power BI
- **Datos Estructurados**: Generar datasets en formatos JSON y CSV
- **Escalabilidad**: Procesamiento de múltiples páginas con manejo de errores

## 📁 Estructura del Proyecto

    Mercado-inmobiliario-BA/
    ├── selenium_zonaprop.py           # Script principal de web scraping
    ├── test_connection.py             # Script para probar conectividad 
    ├── output/                        # Datos extraídos (JSON y CSV)
    ├── etl/                          # Limpieza, tratado y extracción
    │   └── etl_propiedades.py        # Script de transformación de datos
    ├── data/                         # Datos procesados y base de datos
    ├── powerBI/                      # Análisis de datos con Power BI
    └── README.md                     # Documentación del proyecto

## 📚 Librerías Requeridas

### Para Web Scraping (selenium_zonaprop.py y test_connection.py)
```bash
# Selenium para automatización web
pip install selenium

# Requests para pruebas de conectividad HTTP
pip install requests

# WebDriver Manager (opcional, para gestión automática de drivers)
pip install webdriver-manager
```

**Uso de librerías:**
- **selenium**: Automatización del navegador web para extraer datos de páginas dinámicas
- **requests**: Realizar peticiones HTTP para probar conectividad antes del scraping
- **webdriver-manager**: Gestión automática de ChromeDriver (opcional)

### Para ETL y Análisis (etl_propiedades.py)
```bash
# Librerías principales de análisis de datos
pip install pandas numpy

# Visualización de datos
pip install matplotlib seaborn

# Base de datos y formatos adicionales
pip install sqlalchemy openpyxl
```

**Uso de librerías:**
- **pandas**: Manipulación y análisis de datos estructurados
- **numpy**: Operaciones numéricas y matrices
- **matplotlib**: Creación de gráficos y visualizaciones básicas
- **seaborn**: Visualizaciones estadísticas avanzadas
- **sqlalchemy**: Conexión y operaciones con bases de datos
- **openpyxl**: Lectura y escritura de archivos Excel

### Instalación Completa
```bash
# Instalar todas las dependencias de una vez
pip install selenium requests pandas numpy matplotlib seaborn sqlalchemy openpyxl webdriver-manager
```

## 🚀 Ejecución del Proyecto

### Paso 1: Verificar Conectividad
Antes de realizar el scraping, es recomendable verificar que ZonaProp sea accesible:

```bash
python test_connection.py
```

**¿Qué hace este script?**
- Prueba la conectividad con ZonaProp usando requests HTTP
- Verifica si el sitio está bloqueando conexiones automáticas
- Genera un archivo `test_connection_response.html` para inspección manual
- Detecta posibles captchas o páginas de bloqueo

**Salida esperada:**
```
✅ Conexión exitosa!
✅ El contenido parece ser el esperado (listado de propiedades)
Respuesta guardada en 'test_connection_response.html'
```

### Paso 2: Extracción de Datos (Web Scraping)
Una vez verificada la conectividad, ejecutar el scraper principal:

```bash
python selenium_zonaprop.py
```

**¿Qué hace este script?**
- Automatiza Chrome con Selenium para navegar ZonaProp
- Extrae información de propiedades de múltiples páginas
- Implementa estrategias anti-detección (user-agents rotativos, delays humanos)
- Maneja captchas y errores de conexión
- Genera archivos de debug en caso de problemas

**Archivos generados:**
- `output/zonaprop_propiedades_YYYYMMDD_HHMMSS.json`
- `output/zonaprop_propiedades_YYYYMMDD_HHMMSS.csv`
- Screenshots de debug (si es necesario)

**Salida esperada:**
```
🚀 Iniciando scraper avanzado de ZonaProp con Selenium
✓ Directorio output creado/verificado
Procesando página 1: https://www.zonaprop.com.ar/...
✅ Página 1 scrapeada exitosamente. 20 propiedades extraídas.
✅ Proceso completado. Se extrajeron 150 propiedades de múltiples páginas.
```

### Paso 3: Procesamiento y Limpieza de Datos (ETL)
Transformar los datos extraídos para análisis:

```bash
python etl/etl_propiedades.py
```

**¿Qué hace este script?**
- **Extract**: Carga datos del archivo JSON generado por el scraper
- **Transform**: 
  - Detecta y convierte precios en USD a pesos argentinos
  - Limpia direcciones y extrae barrios
  - Calcula métricas derivadas (precio por m², costo total)
  - Categoriza propiedades por tamaño
  - Maneja valores nulos y duplicados
- **Load**: Guarda datos en múltiples formatos

**Archivos generados:**
- `data/propiedades_transformadas.csv` - Dataset limpio en CSV
- `data/propiedades_transformadas.xlsx` - Dataset en Excel
- `data/propiedades.db` - Base de datos SQLite
- `output/reporte_propiedades.json` - Reporte estadístico
- `output/precios_por_moneda.png` - Visualización de precios por moneda
- `output/superficie_vs_precio.png` - Gráfico superficie vs precio

**Transformaciones principales:**
1. **Conversión de monedas**: Precios < $5000 se consideran USD y se convierten a ARS
2. **Limpieza de direcciones**: Extracción de barrios y normalización
3. **Métricas calculadas**: 
   - Precio por m²
   - Costo total (alquiler + expensas)
   - Categorías de tamaño
4. **Manejo de nulos**: Estrategias específicas por tipo de dato

**Salida esperada:**
```
Iniciando proceso ETL...
Número de registros cargados: 150
Registros después de eliminar duplicados: 148
Propiedades por tipo de moneda:
ARS    120
USD     28
Se convirtieron 28 precios de USD a ARS (tasa: 1 USD = 1000 ARS)
Datos guardados en CSV: /home/estefany/cursos/Mercado-inmobiliario-BA/data/propiedades_transformadas.csv
Proceso ETL completado con éxito!
```
## 🛠 Características del Scraper

### Funcionalidades Principales

- ✅ **Anti-detección**: User-agents rotativos y comportamiento humano simulado
- ✅ **Manejo de errores robusto**: Reintentos automáticos y recovery
- ✅ **Múltiples páginas**: Navegación automática entre páginas de resultados
- ✅ **Captcha handling**: Detección y pausa para resolución manual
- ✅ **Navegación natural**: Simulación de búsquedas en Google antes del scraping
- ✅ **Delays aleatorios**: Tiempos de espera variables para evitar detección
- ✅ **Screenshots debug**: Capturas automáticas para depuración

### Datos Extraídos

El scraper extrae la siguiente información de cada propiedad:

```json
{
  "precio_alquiler": 150000,
  "expensas": 25000,
  "direccion": "Av. Rivadavia 7500, Flores",
  "zona": "Flores",
  "superficie": 45,
  "ambientes": 2,
  "habitaciones": 1,
  "banos": 1,
  "descripcion": "Departamento 2 ambientes en Flores",
  "url": "https://www.zonaprop.com.ar/...",
  "pagina": 1,
  "scraped_at": "2024-01-15T10:30:00"
}
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- **Python 3.7+**
- **Google Chrome** (última versión)
- **ChromeDriver** (automáticamente gestionado por Selenium)

### Dependencias del Sistema

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# macOS (con Homebrew)
brew install --cask google-chrome

# Windows
# Descargar e instalar Chrome desde https://www.google.com/chrome/
```

## 🎮 Uso del Scraper

### Configuración Personalizada

El script incluye parámetros configurables en la función `main()`:

```python
# Modificar estos valores según necesidades
base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-flores.html'
max_retries = 3      # Reintentos por página
max_pages = 15       # Máximo de páginas a procesar
```

### Personalizar Zona de Búsqueda

Para cambiar la zona de búsqueda, modificar la `base_url`:

```python
# Ejemplos de URLs para diferentes zonas
base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-palermo.html'
base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-recoleta.html'
base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-belgrano.html'
```

## 📊 Estructura de Datos

### Archivos de Salida

El scraper genera dos tipos de archivos con timestamp:

- **JSON**: `output/zonaprop_propiedades_YYYYMMDD_HHMMSS.json`
- **CSV**: `output/zonaprop_propiedades_YYYYMMDD_HHMMSS.csv`

### Campos de Datos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `precio_alquiler` | Integer | Precio mensual de alquiler (ARS) |
| `expensas` | Integer | Expensas mensuales (ARS) |
| `direccion` | String | Dirección completa de la propiedad |
| `zona` | String | Barrio/zona de ubicación |
| `superficie` | Integer | Superficie en metros cuadrados |
| `ambientes` | Integer | Cantidad de ambientes |
| `habitaciones` | Integer | Cantidad de habitaciones |
| `banos` | Integer | Cantidad de baños |
| `descripcion` | String | Título/descripción de la propiedad |
| `url` | String | URL completa de la propiedad |
| `pagina` | Integer | Número de página donde se encontró |
| `scraped_at` | String | Timestamp de extracción (ISO format) |

## 🔧 Características Técnicas

### Configuración del WebDriver

```python
# Opciones anti-detección
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Timeouts aumentados
driver.set_page_load_timeout(180)  # 3 minutos
driver.set_script_timeout(180)     # 3 minutos
```

### Selectores CSS Utilizados

El scraper utiliza múltiples selectores de respaldo para mayor robustez:

```python
price_selectors = [
    'div.postingCard-module__price-container div:first-child',
    'div[data-qa="POSTING_CARD_PRICE"]',
    'div.price-data',
    'div.postingPrice'
]
```

### Estrategias Anti-Detección

1. **User-Agents Rotativos**: 4 user-agents diferentes
2. **Navegación Natural**: Búsqueda previa en Google
3. **Delays Humanos**: Tiempos aleatorios entre acciones
4. **Scroll Suave**: Simulación de comportamiento de lectura
5. **Tipeo Simulado**: Entrada de texto carácter por carácter

## 🐛 Depuración y Monitoreo

### Archivos de Debug

- `captcha_detected.png`: Screenshot cuando se detecta CAPTCHA
- `debug_page.html`: HTML de página para análisis
- `error_page_X_attempt_Y.html`: HTML de páginas con error

### Logging

El script incluye logging detallado:

```
✓ Directorio output creado/verificado
Configurando navegador Chrome...
Procesando página 1: https://www.zonaprop.com.ar/...
Intento 1 de 3 para la página 1
Visitando Google primero...
Encontrados 20 propiedades con selector: div.postingCard
Propiedad extraída: Av. Rivadavia 7500 - $150000
✅ Página 1 scrapeada exitosamente. 20 propiedades extraídas.
```

## ⚠️ Consideraciones Legales y Éticas

- **Respeto a robots.txt**: Verificar términos de uso de ZonaProp
- **Uso responsable**: No sobrecargar los servidores
- **Datos personales**: No almacenar información personal identificable
- **Propósito educativo**: Este proyecto es para análisis y aprendizaje

## 🔮 Mejoras Futuras

- [ ] **Paralelización**: Múltiples instancias de navegador
- [ ] **Base de datos**: Almacenamiento en PostgreSQL/MongoDB
- [ ] **API REST**: Endpoint para consultar datos
- [ ] **Análisis temporal**: Tracking de cambios de precios
- [ ] **Notificaciones**: Alertas de nuevas propiedades
- [ ] **Filtros avanzados**: Por precio, superficie, etc.
- [ ] **Visualizaciones**: Mapas de calor y gráficos
- [ ] **ML Models**: Predicción de precios

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para contribuir:

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/mejora-scraper`)
3. Commit cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/mejora-scraper`)
5. Abre un Pull Request

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~400 líneas
- **Selectores CSS**: 15+ selectores de respaldo
- **Campos extraídos**: 12 campos por propiedad
- **Formatos de salida**: JSON y CSV
- **Zonas soportadas**: Todas las disponibles en ZonaProp

## 🆘 Troubleshooting

### Problemas Comunes

1. **ChromeDriver no encontrado**
   ```bash
   pip install webdriver-manager
   ```

2. **Timeout en carga de página**
   - Verificar conexión a internet
   - Aumentar timeout en el código

3. **CAPTCHA frecuentes**
   - Reducir velocidad de scraping
   - Cambiar user-agent
   - Usar proxy/VPN

4. **Selectores no funcionan**
   - ZonaProp cambió la estructura
   - Actualizar selectores CSS
   - Revisar archivos debug HTML

## 📧 Contacto

Para preguntas, sugerencias o reportar bugs, crear un issue en este repositorio.

