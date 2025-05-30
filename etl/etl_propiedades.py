import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys
import os

# Verificar y crear directorios necesarios
os.makedirs('/home/estefany/cursos/Mercado-inmobiliario-BA/data', exist_ok=True)
os.makedirs('/home/estefany/cursos/Mercado-inmobiliario-BA/output', exist_ok=True)

# Función para verificar dependencias
def check_dependencies():
    missing_deps = []
    try:
        import sqlalchemy
    except ImportError:
        missing_deps.append("sqlalchemy")
    
    # Verificar openpyxl para Excel
    try:
        import openpyxl
    except ImportError:
        missing_deps.append("openpyxl")
    
    if missing_deps:
        print("\n⚠️ ADVERTENCIA: Faltan las siguientes dependencias:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPor favor, instale las dependencias faltantes con el siguiente comando:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    return True

# Carga de datos desde el archivo JSON
print("Iniciando proceso ETL...")
try:
    ruta_json = '/home/estefany/cursos/Mercado-inmobiliario-BA/output/zonaprop_propiedades_20250528_024151.json'
    df = pd.read_json(ruta_json)
except FileNotFoundError:
    print(f"Error: No se encontró el archivo JSON en la ruta: {ruta_json}")
    print("Verifique la ubicación del archivo y vuelva a ejecutar el script.")
    sys.exit(1)
except Exception as e:
    print(f"Error al cargar los datos: {str(e)}")
    sys.exit(1)

# Visualizar las primeras filas para entender la estructura de datos
print("Número de registros cargados:", len(df))
print("\nPrimeras filas del DataFrame:")
print(df.head())

# Información básica del DataFrame
print("\nInformación del DataFrame:")
print(df.info())

# Estadísticas descriptivas
print("\nEstadísticas descriptivas:")
print(df.describe())

# Limpieza y transformación de los datos

# 1. Eliminar registros duplicados
df_limpio = df.drop_duplicates().reset_index(drop=True)
print(f"Registros después de eliminar duplicados: {len(df_limpio)}")

# 2. Identificar y marcar precios en dólares
# Asumimos que los precios menores a 5000 son en dólares mientras que los mayores son en pesos
df_limpio['moneda_original'] = 'ARS'
mascara_dolares = df_limpio['precio_alquiler'] < 5000
df_limpio.loc[mascara_dolares, 'moneda_original'] = 'USD'

# Convertir precios en dólares a pesos (tasa: 1 USD = 1000 ARS)
tasa_cambio = 1000  # Definir la tasa de cambio USD a ARS
df_limpio['precio_alquiler_original'] = df_limpio['precio_alquiler']  # Guardar el precio original
df_limpio.loc[mascara_dolares, 'precio_alquiler'] = df_limpio.loc[mascara_dolares, 'precio_alquiler'] * tasa_cambio

# Mostrar cuántas propiedades tenían precios en USD vs ARS
conteo_monedas = df_limpio['moneda_original'].value_counts()
print("\nPropiedades por tipo de moneda:")
print(conteo_monedas)
print(f"Se convirtieron {conteo_monedas.get('USD', 0)} precios de USD a ARS (tasa: 1 USD = {tasa_cambio} ARS)")

# 3. Extraer el barrio de la columna 'zona' (eliminando 'pagina-X')
df_limpio['barrio'] = df_limpio['zona'].str.replace(r'-pagina-\d+$', '', regex=True)

# 4. Convertir 'scraped_at' a datetime si no lo está
df_limpio['scraped_at'] = pd.to_datetime(df_limpio['scraped_at'])

# Eliminar columnas redundantes
df_limpio = df_limpio.drop(columns=['zona', 'fecha_scrap'], errors='ignore')
print("Columnas eliminadas: 'zona' y 'fecha_scrap'")

# 5. Manejar valores nulos en columnas numéricas
cols_numericas = ['precio_alquiler', 'expensas', 'superficie', 'ambientes', 'habitaciones', 'banos']
for col in cols_numericas:
    # Identificar cuántos nulos hay en cada columna
    nulos = df_limpio[col].isna().sum()
    print(f"Valores nulos en {col}: {nulos}")

# 6. Calcular precio por m² para análisis de valor (usando el precio en pesos)
df_limpio['precio_por_m2'] = df_limpio['precio_alquiler'] / df_limpio['superficie']

# 7. Calcular precio total (alquiler + expensas) para tener el costo real en pesos
df_limpio['costo_total'] = df_limpio['precio_alquiler'] + df_limpio['expensas'].fillna(0)

# 8. Crear categorías de tamaño basadas en superficie
df_limpio['categoria_tamano'] = pd.cut(
    df_limpio['superficie'],
    bins=[0, 30, 50, 80, 150, float('inf')],
    labels=['Muy pequeño', 'Pequeño', 'Mediano', 'Grande', 'Muy grande']
)

# 9. Relacionar el número de ambientes con el precio de alquiler
df_limpio['ambientes'] = df_limpio['ambientes'].fillna(0).astype(int)  # Asegurar que ambientes sea entero

# Ver el resultado de las transformaciones
print("\nDataFrame después de las transformaciones:")
print(df_limpio.head())
print(df_limpio.info())

# Análisis específico de propiedades en USD vs ARS
print("\nEstadísticas de precios por moneda original:")
for moneda in df_limpio['moneda_original'].unique():
    subset = df_limpio[df_limpio['moneda_original'] == moneda]
    print(f"\nPropiedades en {moneda}:")
    print(f"Cantidad: {len(subset)}")
    print(f"Precio original promedio: {subset['precio_alquiler_original'].mean():.2f}")
    if moneda == 'USD':
        print(f"Precio en pesos (convertido) promedio: {subset['precio_alquiler'].mean():.2f}")
    print(f"Rango de precios originales: {subset['precio_alquiler_original'].min()} - {subset['precio_alquiler_original'].max()}")

# Guardar los datos transformados en diferentes formatos

# 1. Guardar en CSV
ruta_csv_salida = '/home/estefany/cursos/Mercado-inmobiliario-BA/data/propiedades_transformadas.csv'
df_limpio.to_csv(ruta_csv_salida, index=False)
print(f"\nDatos guardados en CSV: {ruta_csv_salida}")

# 2. Guardar en formato Excel (útil para análisis posterior) - Con manejo de errores
ruta_excel = '/home/estefany/cursos/Mercado-inmobiliario-BA/data/propiedades_transformadas.xlsx'
try:
    df_limpio.to_excel(ruta_excel, index=False)
    print(f"Datos guardados en Excel: {ruta_excel}")
except ImportError:
    print("\n⚠️ No se pudo guardar en formato Excel porque falta la librería 'openpyxl'")
    print("Para habilitar esta función, ejecute el siguiente comando:")
    print("pip install openpyxl")

# 3. Guardar en una base de datos SQL - Con manejo de errores
try:
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:////home/estefany/cursos/Mercado-inmobiliario-BA/data/propiedades.db')
    df_limpio.to_sql('propiedades', engine, if_exists='replace', index=False)
    print("Datos guardados en base de datos SQLite")
except ImportError:
    print("\n⚠️ No se pudo guardar en la base de datos SQLite porque falta la librería 'sqlalchemy'")
    print("Para habilitar esta función, ejecute el siguiente comando:")
    print("pip install sqlalchemy")
except Exception as e:
    print(f"\n⚠️ Error al guardar en base de datos: {str(e)}")

# Verificar dependencias antes de continuar con visualizaciones
if check_dependencies():
    print("\nProceso ETL completado con éxito!")

    # Opcional: Realizar análisis adicionales específicos por moneda
    try:
        # Visualizar distribución de precios por moneda original
        plt.figure(figsize=(12, 6))
        sns.boxplot(x='moneda_original', y='precio_alquiler_original', data=df_limpio)
        plt.title('Distribución de precios de alquiler originales por moneda')
        plt.yscale('log')  # Usar escala logarítmica para mejor visualización
        plt.tight_layout()
        plt.savefig('/home/estefany/cursos/Mercado-inmobiliario-BA/output/precios_por_moneda.png')
        
        # Visualizar la distribución de precios por barrio, distinguiendo moneda original
        plt.figure(figsize=(14, 8))
        for moneda, marker in zip(['ARS', 'USD'], ['o', 'x']):
            subset = df_limpio[df_limpio['moneda_original'] == moneda]
            plt.scatter(
                subset['superficie'], 
                subset['precio_alquiler'], 
                alpha=0.6,
                marker=marker,
                label=f'Original en {moneda}'
            )
        plt.xlabel('Superficie (m²)')
        plt.ylabel('Precio Alquiler (ARS)')
        plt.title('Relación entre superficie y precio de alquiler por moneda original')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('/home/estefany/cursos/Mercado-inmobiliario-BA/output/superficie_vs_precio_por_moneda.png')
        
        # Visualizar la relación entre superficie y precio
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='superficie', y='precio_alquiler', hue='ambientes', data=df_limpio)
        plt.title('Relación entre superficie y precio de alquiler')
        plt.tight_layout()
        plt.savefig('/home/estefany/cursos/Mercado-inmobiliario-BA/output/superficie_vs_precio.png')
        
        print("Visualizaciones generadas correctamente.")
    except Exception as e:
        print(f"\n⚠️ Error al generar visualizaciones: {str(e)}")

    # Generar un informe con las principales estadísticas, incluyendo información sobre monedas
    try:
        reporte = {
            'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_propiedades': len(df_limpio),
            'propiedades_por_moneda_original': df_limpio['moneda_original'].value_counts().to_dict(),
            'precio_promedio_ars': float(df_limpio[df_limpio['moneda_original'] == 'ARS']['precio_alquiler_original'].mean()),
            'precio_promedio_usd': float(df_limpio[df_limpio['moneda_original'] == 'USD']['precio_alquiler_original'].mean()),
            'precio_promedio_total_ars': float(df_limpio['precio_alquiler'].mean()),
            'precio_mediano_total_ars': float(df_limpio['precio_alquiler'].median()),
            'superficie_promedio': float(df_limpio['superficie'].mean()),
            'distribucion_ambientes': {str(k): int(v) for k, v in df_limpio['ambientes'].value_counts().to_dict().items()},
            'propiedades_por_barrio': {str(k): int(v) for k, v in df_limpio['barrio'].value_counts().to_dict().items()},
            'tasa_conversion_usd_ars': tasa_cambio
        }

        import json
        with open('/home/estefany/cursos/Mercado-inmobiliario-BA/output/reporte_propiedades.json', 'w') as f:
            json.dump(reporte, f, indent=4)

        print("\nReporte estadístico generado.")
    except Exception as e:
        print(f"\n⚠️ Error al generar el reporte: {str(e)}")
else:
    print("\n⚠️ Proceso ETL completado parcialmente. Por favor instale las dependencias faltantes para funcionalidad completa.")
    print("Para instalar todas las dependencias necesarias, ejecute:")
    print("pip install pandas numpy matplotlib seaborn sqlalchemy openpyxl")
