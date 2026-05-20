"""
Módulo: simulador_datos.py
Descripción: Genera datos sintéticos avanzados con lógica de negocio real
para simular un ecosistema de retail (SQL, JSON, CSV).
"""

import sqlite3
import json
import random
import pandas as pd
import logging
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CONSTANTES DE RUTAS 
RUTA_VENTAS_SQL = 'bodega_datos/1_brutos/ventas_historicas.sqlite'
RUTA_PERFILES_JSON = 'bodega_datos/1_brutos/perfiles_usuarios.json'
RUTA_INVENTARIO_CSV = 'bodega_datos/1_brutos/inventario.csv'
RUTA_CATALOGOS_XML = 'bodega_datos/1_brutos/catalogos.xml'
RUTA_METAS_EXCEL = 'bodega_datos/1_brutos/metas_anuales.xlsx'
RUTA_LOGS_TXT = 'bodega_datos/1_brutos/logs_servidor.txt'

# =============================================================================
# DICCIONARIOS DE DATOS MAESTROS (Para generar datos realistas)
# =============================================================================
CATALOGO_PRODUCTOS = {
    'Tecnología': [('Laptop gamer', 16999.0), ('Jaifon X', 9800.0), ('Auriculares Bluetooth', 100.0), ('Monitor 27"', 5500.0), ('XBOX SERIES X', 12980.0), ('Cargador tipo C', 150.0), ('Smartwatch Deportivo', 1200.0), ('Teclado Mecánico', 750.0), ('Mouse Inalámbrico', 350.0), ('Audifonos para Computadora', 1180.0)],
    'Hogar': [('Sofá 3 Plazas', 6500.0), ('Cafetera Espresso', 2350.0), ('Lámpara de Pie', 450.0), ('Set de Sartenes', 4090.0), ('Colchón King Size', 10999.0), ('Comedor', 7890.0), ('Juego de Toallas', 250.0), ('Ganchos para ropa "paquete de 10 pzs"', 150.0)],
    'Moda': [('Chaqueta de Cuero', 1890.0), ('Zapatillas Running', 900.0), ('Reloj Clásico', 850.0), ('Pantalón Denim', 170.0), ('Vestido de Fiesta', 550.0), ('Bolso de Mano', 800.0), ('Gafas de Sol', 400.0), ('Cinturón de Piel', 100.0), ('Camisa Polo', 200.0), ('Set de Ropa Interior', 80.0)],
    'Deportes': [('Bicicleta de Montaña', 9500.0), ('Set de Mancuernas', 1500.0), ('Tienda de Campaña', 3450.0), ('Tapete de Yoga', 150.0), ('Balón de Fútbol Oficial', 300.0), ('Zapatillas de Baloncesto', 1200.0), ('Reloj GPS para Correr', 2200.0), ('Raqueta de Tenis', 800.0)]
}

CIUDADES = ['CDMX', 'Guadalajara', 'Monterrey', 'Culiacán', 'Veracruz', 'Chihuahua', 'Puebla', 'Toluca']
NOMBRES = ['Ana', 'Carlos', 'María', 'Jorge', 'Lucía', 'Miguel', 'Sofía', 'Luis', 'Elena', 'Diego']
APELLIDOS = ['García', 'López', 'Martínez', 'Rodríguez', 'Pérez', 'Sánchez', 'Ramírez', 'Gómez']

PRODUCTOS_MAESTROS = []
_id_contador = 1
for categoria, productos in CATALOGO_PRODUCTOS.items():
    for nombre, precio in productos:
        PRODUCTOS_MAESTROS.append({
            'id_producto': _id_contador,
            'nombre_producto': nombre,
            'categoria': categoria,
            'precio_unitario': precio
        })
        _id_contador += 1

CLIENTES_MAESTROS = []
categorias_nombres = list(CATALOGO_PRODUCTOS.keys())
niveles_fidelidad = ['Bronce', 'Plata', 'Oro', 'Platino']

# Corregimos el rango para que genere IDs exactamente del 100 al 2000
for identificador in range(100, 2001): 
    perfil = {
        "id_cliente": identificador,
        "nombre_completo": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
        "edad": random.randint(18, 70),
        "ciudad": random.choice(CIUDADES),
        "nivel_fidelidad": random.choices(niveles_fidelidad, weights=[50, 30, 15, 5])[0],
        "preferencia": random.choice(categorias_nombres)
    }
    CLIENTES_MAESTROS.append(perfil)

def generar_inventario_csv(ruta_archivo: str = RUTA_INVENTARIO_CSV) -> None:
    """ Genera un archivo CSV utilizando la fuente de verdad unificada. """
    datos = []
    for prod in PRODUCTOS_MAESTROS:
        item = prod.copy()
        item['stock_actual'] = random.randint(10, 500)
        datos.append(item)
            
    df_inventario = pd.DataFrame(datos)
    df_inventario.to_csv(ruta_archivo, index=False, encoding='utf-8')
    logging.info(f"CSV: Generado catálogo real de {len(datos)} productos en '{ruta_archivo}'.")

def generar_perfiles_json(ruta_archivo: str = RUTA_PERFILES_JSON) -> None:
    """ Genera el archivo JSON leyendo directamente de la fuente de verdad unificada. """
    with open(ruta_archivo, 'w', encoding='utf-8') as archivo_json:
        json.dump(CLIENTES_MAESTROS, archivo_json, indent=4, ensure_ascii=False)
        
    logging.info(f"JSON: Generados {len(CLIENTES_MAESTROS)} perfiles realistas en '{ruta_archivo}'.")

def generar_catalogos_xml(ruta_archivo: str = RUTA_CATALOGOS_XML) -> None:
    """ Genera un archivo XML con los metadatos de las categorías de productos. """
    
    # 1. Creamos la etiqueta raíz del documento
    raiz = ET.Element("catalogos")
    
    # Datos simulados para enriquecer el XML según la categoría
    detalles_categoria = {
        'Tecnología': {'margen': '15%', 'responsable': 'Ana G.', 'prioridad': 'Alta', 'desc': 'Electrónica y gadgets de consumo.'},
        'Hogar': {'margen': '25%', 'responsable': 'Carlos M.', 'prioridad': 'Media', 'desc': 'Muebles, decoración y electrodomésticos.'},
        'Deportes': {'margen': '30%', 'responsable': 'Luis F.', 'prioridad': 'Media', 'desc': 'Ropa y equipo para actividades físicas.'},
        'Moda': {'margen': '40%', 'responsable': 'Sofía R.', 'prioridad': 'Alta', 'desc': 'Prendas de vestir y accesorios de temporada.'},
        'Libros': {'margen': '20%', 'responsable': 'Elena T.', 'prioridad': 'Baja', 'desc': 'Literatura, textos académicos y cómics.'}
    }
    
    # 2. Iteramos sobre las categorías de nuestra fuente de verdad
    for nombre_categoria in CATALOGO_PRODUCTOS.keys():
        # Obtenemos los detalles o valores por defecto si la categoría es nueva
        detalles = detalles_categoria.get(nombre_categoria, {'margen': '20%', 'responsable': 'Pendiente', 'prioridad': 'Media', 'desc': 'Categoría general.'})
        
        # Creamos el nodo hijo para la categoría
        nodo_categoria = ET.SubElement(raiz, "categoria", nombre=nombre_categoria)
        
        # Llenamos el nodo con sub-etiquetas
        ET.SubElement(nodo_categoria, "descripcion").text = detalles['desc']
        ET.SubElement(nodo_categoria, "margen_ganancia_esperado").text = detalles['margen']
        ET.SubElement(nodo_categoria, "responsable_area").text = detalles['responsable']
        ET.SubElement(nodo_categoria, "nivel_prioridad").text = detalles['prioridad']
        
    # 3. Formateamos y guardamos el archivo
    arbol = ET.ElementTree(raiz)
    # ET.indent le da el formato bonito con saltos de línea (requiere Python 3.9+)
    if hasattr(ET, 'indent'):
        ET.indent(arbol, space="\t", level=0)
        
    # Nos aseguramos de que la carpeta exista antes de guardar
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    
    arbol.write(ruta_archivo, encoding="utf-8", xml_declaration=True)
    logging.info(f"XML: Generado catálogo de categorías en '{ruta_archivo}'.")

def generar_ventas_sql(ruta_base_datos: str = RUTA_VENTAS_SQL, cantidad_registros: int = 5000) -> None:
    """ Crea transacciones históricas lógicas con métodos de pago y fechas secuenciales. """
    try:
        conexion = sqlite3.connect(ruta_base_datos)
        cursor = conexion.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER,
                id_producto INTEGER,
                monto REAL,
                metodo_pago TEXT,
                fecha_transaccion TEXT
            )
            ''')
        cursor.execute('DELETE FROM ventas') 
        
        datos_ventas = []
        fecha_base = datetime(2025, 1, 1)
        metodos = ['Tarjeta de Crédito', 'Tarjeta de Débito', 'Efectivo', 'MercadoPago', 'Transferencia']
        
        for _ in range(cantidad_registros):
            id_cliente = random.randint(100, 2000)
            
            # 1. Tomamos un producto de la fuente de verdad
            producto_vendido = random.choice(PRODUCTOS_MAESTROS)
            id_producto = producto_vendido['id_producto']
            precio_base = producto_vendido['precio_unitario']
            
            # 2. Simulamos la venta de forma lógica (1 a 3 unidades, con posible descuento)
            cantidad = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            descuento = random.choices([1.0, 0.9, 0.85], weights=[70, 20, 10])[0] 
            
            monto = round((precio_base * cantidad) * descuento, 2)
            
            # 3. Fechas aleatorias
            dias_sumar = random.randint(0, 365)
            fecha_venta = fecha_base + timedelta(days=dias_sumar)
            
            datos_ventas.append((
                id_cliente, 
                id_producto, 
                monto, 
                random.choice(metodos),
                fecha_venta.strftime("%Y-%m-%d")
            ))
            
        cursor.executemany('INSERT INTO ventas (id_cliente, id_producto, monto, metodo_pago, fecha_transaccion) VALUES (?, ?, ?, ?, ?)', datos_ventas)
        conexion.commit()
        logging.info(f"SQLite: Generadas {cantidad_registros} transacciones comerciales en '{ruta_base_datos}'.")
        
    except sqlite3.Error as error_sql:
        logging.error(f"Error al generar SQLite: {error_sql}")
    finally:
        if conexion:
            conexion.close()

def generar_metas_excel(ruta_archivo: str = RUTA_METAS_EXCEL) -> None:
    """ Genera un archivo Excel con los KPIs de negocio esperados por ciudad. """
    datos_metas = []
    categorias = list(CATALOGO_PRODUCTOS.keys())
    
    # Usamos nuestra fuente de verdad (CIUDADES) para no inventar regiones nuevas
    for ciudad in CIUDADES:
        meta_ventas = random.randint(500000, 2500000) # Meta en pesos MXN
        crecimiento = round(random.uniform(5.0, 25.0), 2) # Porcentaje esperado
        
        datos_metas.append({
            'ciudad': ciudad,
            'meta_ventas_mxn': meta_ventas,
            'crecimiento_esperado_pct': crecimiento,
            'categoria_impulso': random.choice(categorias)
        })
        
    df_metas = pd.DataFrame(datos_metas)
    
    import os
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    
    # Usamos openpyxl como motor para exportar a Excel
    df_metas.to_excel(ruta_archivo, index=False, engine='openpyxl')
    logging.info(f"Excel: Generadas metas anuales para {len(CIUDADES)} regiones en '{ruta_archivo}'.")

def generar_logs_txt(ruta_archivo: str = RUTA_LOGS_TXT, cantidad_lineas: int = 2000) -> None:
    """ Genera un archivo de texto simulando registros web vinculados a clientes y productos reales. """
    import os
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    
    endpoints_genericos = ['/inicio', '/carrito', '/checkout', '/api/pagos', '/login']
    codigos_estado = [200, 200, 200, 200, 201, 400, 404, 500] 
    
    fecha_base = datetime.now() - timedelta(days=30)
    
    with open(ruta_archivo, 'w', encoding='utf-8') as archivo_txt:
        for _ in range(cantidad_lineas):
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            fecha_base += timedelta(minutes=random.randint(1, 60))
            fecha_str = fecha_base.strftime("%Y-%m-%d %H:%M:%S")
            
            metodo = random.choices(['GET', 'POST', 'PUT'], weights=[70, 25, 5])[0]
            estado = random.choice(codigos_estado)
            tiempo_ms = random.randint(20, 1500) 
            
            # LÓGICA DE VINCULACIÓN
            # 60% de probabilidad de que el log sea una visita a un producto específico
            if random.random() > 0.4: 
                producto = random.choice(PRODUCTOS_MAESTROS)
                cliente = random.choice(CLIENTES_MAESTROS)
                endpoint = f"/catalogo/producto/{producto['id_producto']}?cliente={cliente['id_cliente']}"
            else:
                endpoint = random.choice(endpoints_genericos)
            
            linea_log = f"[{fecha_str}] {ip} {metodo} {endpoint} {estado} {tiempo_ms}ms\n"
            archivo_txt.write(linea_log)
            
    logging.info(f"TXT: Generados {cantidad_lineas} registros web vinculados en '{ruta_archivo}'.")

# =============================================================================
if __name__ == "__main__":
    logging.info("=== INICIANDO SIMULACIÓN DE DATOS RETAIL V2.0 ===")
    generar_inventario_csv() 
    generar_perfiles_json()
    generar_catalogos_xml()
    generar_ventas_sql()
    generar_metas_excel()
    generar_logs_txt()
    logging.info("=== SIMULACIÓN COMPLETADA ===")