# Estructura de datos del proyecto Mercado Inmobiliario BA

Este directorio contiene los datos extraídos por los scrapers del proyecto.

## Estructura

- `raw/`: Carpeta donde se guardan los datos JSON sin procesar directamente extraídos por los scrapers
- `propiedades.db`: Base de datos SQLite que contiene todos los datos procesados y estructurados

## Formato de archivos JSON

Los archivos JSON en la carpeta `raw/` tienen el formato `{nombre_spider}_{timestamp}.json` y contienen una lista de propiedades con la siguiente estructura:

```json
[
  {
    "id_propiedad": "id123456",
    "precio": "USD 120.000",
    "moneda": "USD",
    "expensas": "$45.000",
    "direccion": "Av. Ejemplo 1234",
    "barrio_zona": "Palermo",
    "superficie": "65 m²",
    "ambientes": "3",
    "dormitorios": "2",
    "baños": "1",
    "url": "https://www.ejemplo.com/propiedad/id123456",
    "fecha_extraccion": "2023-05-01",
    "fuente": "ZonaProp"
  },
  // Más propiedades...
]
```

## Base de datos SQLite

La base de datos `propiedades.db` contiene una tabla principal llamada `propiedades` con los siguientes campos:

- `url`: URL de la propiedad (clave primaria)
- `precio`: Precio de la propiedad (texto, incluye el formato original)
- `moneda`: Moneda del precio (USD o ARS)
- `expensas`: Valor de las expensas (texto)
- `superficie_total`: Superficie total en metros cuadrados
- `superficie_cubierta`: Superficie cubierta en metros cuadrados
- `ambientes`: Número de ambientes
- `banos`: Número de baños
- `dormitorios`: Número de dormitorios
- `direccion`: Dirección de la propiedad
- `barrio_zona`: Barrio o zona donde se encuentra la propiedad
- `descripcion`: Descripción completa de la propiedad
- `fecha_extraccion`: Fecha en que se extrajo la información
- `fuente`: Fuente de los datos (ZonaProp, MercadoLibre, etc.)
