# mock_data.py - Script para generar datos de prueba para el pipeline de análisis
# Este script crea una base de datos SQLite con una tabla de ventas históricas y un archivo CSV de inventario, inyectando inconsistencias como fechas en formatos mixtos, duplicados y valores nulos para simular un entorno realista de datos sucios.
# Se utiliza la librería logging para mostrar mensajes informativos sobre el progreso de la generación de datos, incluyendo detalles sobre la cantidad de registros generados, duplicados y nulos inyectados, y las rutas de los archivos creados. Este script es esencial para preparar un entorno de prueba robusto para el desarrollo y validación del pipeline de datos en el proyecto de análisis global de retail y comportamiento del cliente.
import pandas as pd
import numpy as np
import sqlite3
import random
from datetime import datetime, timedelta
import logging

# Configuración del logging para mostrar mensajes informativos con timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def generar_ventas_sql(db_path: str = 'ventas_historicas.sqlite', num_records: int = 5000):
    """Genera la tabla SQL de ventas con fechas en formatos inconsistentes."""
    logging.info(f"Generando {num_records} registros de ventas SQL...")
    
    # Generación de datos base.
    data = {
        'id_transaccion': range(1, num_records + 1),
        'id_cliente': [random.randint(100, 2000) for _ in range(num_records)],
        'monto': [round(random.uniform(50.0, 5000.0), 2) for _ in range(num_records)],
        'id_tienda': [random.randint(1, 50) for _ in range(num_records)]
    }
    
    # Genera fechas inconsistentes (mezclando formatos YYYY-MM-DD y DD/MM/YYYY).
    fechas = []
    base_date = datetime(2023, 1, 1)
    for _ in range(num_records):
        random_days = random.randint(0, 365)
        fecha_obj = base_date + timedelta(days=random_days)
        if random.choice([True, False]):
            # Formato ISO
            fechas.append(fecha_obj.strftime('%Y-%m-%d')) 
        else:
            # Formato Día/Mes/Año
            fechas.append(fecha_obj.strftime('%d/%m/%Y')) 
    
    # Agregar las fechas al DataFrame.        
    data['fecha'] = fechas
    df_ventas = pd.DataFrame(data)
    
    # Guardar en SQLite.
    with sqlite3.connect(db_path) as conn:
        df_ventas.to_sql('ventas_historicas', conn, if_exists='replace', index=False)
    logging.info(f"Base de datos guardada en: {db_path}")

def generar_inventario_csv(file_path: str = 'inventario.csv', num_records: int = 500):
    """Genera un CSV de inventario inyectando 5% de duplicados y 10% de nulos."""
    logging.info(f"Generando {num_records} registros de inventario CSV...")
    
    # Creación de datos limpios.
    data = {
        'id_producto': [f"PROD_{i:04d}" for i in range(1, num_records + 1)],
        'categoria': random.choices(["Electrónica", "Ropa", "Hogar", "mex", "México", "mx"], k=num_records),
        'stock': [random.randint(0, 500) for _ in range(num_records)],
        'precio_unitario': [round(random.uniform(10.0, 1000.0), 2) for _ in range(num_records)]
    }
    # Crea el DataFrame.
    df_inventario = pd.DataFrame(data)
    
    # Inyección del 5% de datos duplicados.
    num_duplicados = int(num_records * 0.05)
    duplicados = df_inventario.sample(n=num_duplicados, random_state=42)
    df_inventario = pd.concat([df_inventario, duplicados], ignore_index=True)
    logging.info(f"Se inyectaron {num_duplicados} filas duplicadas.")
    
    # Inyeccón del 10% de valores nulos dentro de columnas específicas.
    num_nulos = int(len(df_inventario) * 0.10)
    for _ in range(num_nulos):
        row_idx = random.randint(0, len(df_inventario) - 1)
        col_name = random.choice(['stock', 'precio_unitario'])
        df_inventario.at[row_idx, col_name] = np.nan
    logging.info(f"Se inyectaron {num_nulos} valores nulos.")
    
    # Guardar a CSV.
    df_inventario.to_csv(file_path, index=False)
    logging.info(f"Archivo guardado en: {file_path}")

if __name__ == "__main__":
    generar_ventas_sql()
    generar_inventario_csv()