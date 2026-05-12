# mock_data.py - Script para generar datos de prueba para el pipeline de análisis
# Este script crea una base de datos SQLite con una tabla de ventas históricas y un archivo CSV de inventario, inyectando inconsistencias como fechas en formatos mixtos, duplicados y valores nulos para simular un entorno realista de datos sucios.
# Se utiliza la librería logging para mostrar mensajes informativos sobre el progreso de la generación de datos, incluyendo detalles sobre la cantidad de registros generados, duplicados y nulos inyectados, y las rutas de los archivos creados. Este script es esencial para preparar un entorno de prueba robusto para el desarrollo y validación del pipeline de datos en el proyecto de análisis global de retail y comportamiento del cliente.
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import sqlite3
import json
import random
from datetime import datetime, timedelta
import logging

# Configuración del logging para mostrar mensajes informativos con timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generar_ventas_sql(db_path: str = 'ventas_historicas.sqlite', num_records: int = 5000):
    """ Genera la tabla SQL de ventas con fechas en formatos inconsistentes. """
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
    base_date = datetime(2026, 1, 1)
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

def generar_perfiles_json(file_path='perfiles_usuarios.json', num_records=1900):
    """Genera perfiles de usuario detallados con alta variabilidad."""
    import random
    logging.info(f"Generando {num_records} perfiles de usuario enriquecidos...")
    
    categorias = ["Electrónica", "Hogar", "Ropa", "Deportes", "Belleza", "Libros"]
    paises = ["México", "España", "Colombia", "Argentina", "Chile", "Perú"]
    
    perfiles = []
    for i in range(num_records):
        user_id = 100 + i
        perfiles.append({
            "id_cliente": user_id,
            "info_personal": {
                "edad": random.randint(18, 75),
                "genero": random.choice(["M", "F"]),
                "pais": random.choice(paises),
                "email": f"user_{user_id}@example.com"
            },
            "preferencias": {
                "categoria_principal": random.choice(categorias),
                "suscripcion_premium": random.choice([True, False]),
                "notificaciones": random.choice(["Email", "SMS", "Push", "Ninguna"])
            }
        })
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(perfiles, f, ensure_ascii=False, indent=4)
    logging.info("Archivo perfiles_usuarios.json finalizado.")  

def generar_inventario_csv(file_path: str = 'inventario.csv', num_records: int = 500):
    """ Genera un CSV de inventario inyectando 5% de duplicados y 10% de nulos. """
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

def generar_catalogos_xml(file_path='catalogos.xml'):
    """Genera un catálogo de productos estructurado y jerárquico."""
    logging.info("Enriqueciendo catálogo XML...")
    
    data = {
        "Electrónica": [("Smartphones", "Gama alta y media"), ("Laptops", "Trabajo y Gaming")],
        "Hogar": [("Muebles", "Salón y dormitorio"), ("Cocina", "Electrodomésticos pequeños")],
        "Deportes": [("Fitness", "Pesas y cardio"), ("Outdoor", "Camping y senderismo")]
    }

    root = ET.Element("ComercioGlobal")
    cat_element = ET.SubElement(root, "Catalogos")

    for cat_name, subcats in data.items():
        categoria = ET.SubElement(cat_element, "Categoria", nombre=cat_name)
        for sub_name, desc in subcats:
            item = ET.SubElement(categoria, "Subcategoria")
            name = ET.SubElement(item, "Nombre")
            name.text = sub_name
            description = ET.SubElement(item, "Descripcion")
            description.text = desc

    tree = ET.ElementTree(root)
    # Formateo básico para que el XML sea legible
    ET.indent(tree, space="  ", level=0)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    logging.info("Archivo catalogos.xml enriquecido.")

def generar_logs_servidor(file_path='logs_servidor.txt', num_lines=500):
    """Genera logs de tráfico web realistas."""
    logging.info(f"Generando {num_lines} líneas de logs de servidor...")
    with open(file_path, 'w', encoding='utf-8') as f:
        fecha_ini = datetime.now() - timedelta(days=30)
        endpoints = ["/login", "/products", "/cart/add", "/checkout", "/search"]
        
        for _ in range(num_lines):
            timestamp = fecha_ini + timedelta(seconds=random.randint(0, 2592000))
            lvl = random.choices(['INFO', 'WARN', 'ERROR'], weights=[80, 15, 5])[0]
            ip = f"192.168.1.{random.randint(1, 254)}"
            path = random.choice(endpoints)
            status = 200 if lvl == 'INFO' else (404 if lvl == 'WARN' else 500)
            
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {lvl} - {ip} - GET {path} - {status}\n")
    logging.info(f"Archivo de logs guardado en: {file_path}")

def generar_metas_xlsx(file_path='metas_anuales.xlsx'):     
    """ 
    Genera un plan de metas anuales detallado con desglose trimestral 
    y KPIs de rentabilidad por región. 
    """
    logging.info("Generando plan estratégico de metas anuales XLSX...")
    
    data = {
        'ID_Region': [1, 2, 3, 4],
        'Region': ['LATAM', 'EMEA', 'APAC', 'NA'],
        'Meta_Anual_M_USD': [1.5, 2.8, 3.2, 4.0],
        'Margen_Ebitda_Objetivo': [0.22, 0.25, 0.18, 0.28], # 22%, 25%, etc.
        'Meta_Nuevos_Clientes': [500, 1200, 1500, 2000],
        'Q1_Target_M': [0.30, 0.60, 0.70, 0.90],
        'Q2_Target_M': [0.35, 0.70, 0.80, 1.00],
        'Q3_Target_M': [0.40, 0.75, 0.85, 1.05],
        'Q4_Target_M': [0.45, 0.75, 0.85, 1.05], # Q4 suele ser más alto por Navidad
        'KPI_Retencion_Min': [0.85, 0.90, 0.88, 0.92],
        'Presupuesto_Ads_USD': [150000, 250000, 300000, 450000],
        'Prioridad': ['Alta', 'Media', 'Alta', 'Crítica']
    }
    
    df = pd.DataFrame(data)
    
    # Añadimos una columna calculada simple para que el archivo sea más "vivo"
    df['Costo_Adquisicion_Objetivo'] = (df['Presupuesto_Ads_USD'] / df['Meta_Nuevos_Clientes']).round(2)
    
    # Guardar a Excel
    df.to_excel(file_path, index=False, sheet_name='Plan_Anual_2024')
    logging.info(f"Archivo Excel estratégico guardado en: {file_path}")

# Este bloque asegura que la generación de datos solo se ejecute cuando se ejecute este script directamente, evitando que se ejecute si se importa como módulo en otro script (como main.py).
if __name__ == "__main__":
    logging.info("=== GENERANDO DATOS DE PRUEBA ===")
    generar_ventas_sql()
    generar_inventario_csv()
    generar_perfiles_json()
    generar_catalogos_xml()
    generar_logs_servidor()
    generar_metas_xlsx()
    logging.info("=== GENERACIÓN DE DATOS COMPLETADA ===")