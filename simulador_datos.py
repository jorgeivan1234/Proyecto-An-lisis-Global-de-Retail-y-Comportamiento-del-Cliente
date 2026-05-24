"""
Módulo: simulador_datos.py
Descripción: Genera datos planos con lógica de negocio real
para simular un ecosistema de retail (SQL, JSON, CSV, XML, Excel).
"""

# Importación de librerías necesarias para la generación de datos y manejo de archivos
import sqlite3                               # Para la base de datos SQLite
import json                                  # Para manejar archivos JSON
import random                                # Para generar datos aleatorios
import pandas as pd                          # Para manejar DataFrames y generar CSV/Excel
import logging                               # Para la configuración de logs
import xml.etree.ElementTree as ET           # Para generar archivos XML
import os                                    # Para manejo de rutas y directorios
import numpy as np                           # Para manejo de datos numéricos y generación de nulos
from datetime import datetime, timedelta     # Para generar fechas aleatorias y manipularlas

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constantes de rutas para los archivos generados
RUTA_VENTAS_SQL = 'bodega_datos/1_brutos/ventas_historicas.sqlite'
RUTA_PERFILES_JSON = 'bodega_datos/1_brutos/perfiles_usuarios.json'
RUTA_INVENTARIO_CSV = 'bodega_datos/1_brutos/inventario.csv'
RUTA_CATALOGOS_XML = 'bodega_datos/1_brutos/catalogos.xml'
RUTA_METAS_EXCEL = 'bodega_datos/1_brutos/metas_anuales.xlsx'
RUTA_LOGS_TXT = 'bodega_datos/1_brutos/logs_servidor.txt'

# Definición de catálogos y datos maestros para la simulación
CATALOGO_PRODUCTOS = {
    'Tecnología': [('Laptop gamer', 16999.0), ('Jaifon X', 9800.0), ('Auriculares Bluetooth', 100.0), ('Monitor 27"', 5500.0), ('XBOX SERIES X', 12980.0), ('Cargador tipo C', 150.0), ('Smartwatch Deportivo', 1200.0), ('Teclado Mecánico', 750.0), ('Mouse Inalámbrico', 350.0), ('Audifonos para Computadora', 1180.0)],
    'Hogar': [('Sofá 3 Plazas', 6500.0), ('Cafetera Espresso', 2350.0), ('Lámpara de Pie', 450.0), ('Set de Sartenes', 4090.0), ('Colchón King Size', 10999.0), ('Comedor', 7890.0), ('Juego de Toallas', 250.0), ('Ganchos para ropa "paquete de 10 pzs"', 150.0)],
    'Moda': [('Chaqueta de Cuero', 1890.0), ('Zapatillas Running', 900.0), ('Reloj Clásico', 850.0), ('Pantalón Denim', 170.0), ('Vestido de Fiesta', 550.0), ('Bolso de Mano', 800.0), ('Gafas de Sol', 400.0), ('Cinturón de Piel', 100.0), ('Camisa Polo', 200.0), ('Set de Ropa Interior', 80.0)],
    'Deportes': [('Bicicleta de Montaña', 9500.0), ('Set de Mancuernas', 1500.0), ('Tienda de Campaña', 3450.0), ('Tapete de Yoga', 150.0), ('Balón de Fútbol Oficial', 300.0), ('Zapatillas de Baloncesto', 1200.0), ('Reloj GPS para Correr', 2200.0), ('Raqueta de Tenis', 800.0)]
}

# Para generar perfiles de clientes con ciudades sucias, vamos a crear variaciones de los nombres de las ciudades
# Estas variaciones simulan errores comunes de entrada de datos (mayúsculas, minúsculas, espacios extras, abreviaturas)
CIUDADES = ['CDMX', 'Guadalajara', 'Monterrey', 'Culiacán', 'Veracruz', 'Chihuahua', 'Puebla', 'Toluca']
NOMBRES = ['Ana', 'Carlos', 'María', 'Jorge', 'Lucía', 'Miguel', 'Sofía', 'Luis', 'Elena', 'Diego']
APELLIDOS = ['García', 'López', 'Martínez', 'Rodríguez', 'Pérez', 'Sánchez', 'Ramírez', 'Gómez']

# Mapeo de ciudades a IDs de tienda para asegurar consistencia en la generación de datos
MAPEO_TIENDAS = {
    'CDMX': 40001,
    'Guadalajara': 40002,
    'Monterrey': 40003,
    'Culiacán': 40004,
    'Veracruz': 40005,
    'Chihuahua': 40006,
    'Puebla': 40007,
    'Toluca': 40008
}

# Creación de datos maestros para productos y clientes, 
# que serán la base para generar los archivos simulados
PRODUCTOS_MAESTROS = []
_id_contador = 1 

# Generamos 22 variantes de los 36 productos base para alcanzar 792 productos únicos.
# Esto garantiza que el inventario cumpla la rúbrica de 500-1000 filas sin causar 
# multiplicaciones catastróficas al cruzar los datos más adelante.
for variante in range(1, 23): 
    for categoria, productos in CATALOGO_PRODUCTOS.items():
        for nombre, precio in productos:
            # Agregamos un sufijo a partir de la variante 2 para hacerlos únicos
            sufijo = f" Gen {variante}" if variante > 1 else ""
            # Variamos ligeramente el precio para darle realismo
            precio_variado = round(precio * random.uniform(0.85, 1.15), 2)
            
            # Creamos un producto maestro con un ID único, nombre con sufijo, categoría y precio variado, 
            # y lo agregamos a la lista de productos maestros
            PRODUCTOS_MAESTROS.append({
                'id_producto': _id_contador,
                'nombre_producto': f"{nombre}{sufijo}",
                'categoria': categoria,
                'precio_unitario': precio_variado
            })
            _id_contador += 1

CLIENTES_MAESTROS = []
categorias_nombres = list(CATALOGO_PRODUCTOS.keys())
niveles_fidelidad = ['Bronce', 'Plata', 'Oro', 'Platino'] 

# Generamos perfiles de clientes con lógica de negocio realista, 
# incluyendo variaciones sucias en las ciudades y asignación de tiendas seguras
for identificador in range(100, 2001):
    
    ciudad_real = random.choice(CIUDADES)
    variaciones_ciudad = [ciudad_real, ciudad_real.lower(), ciudad_real.upper(), f" {ciudad_real} "]
    
    if ciudad_real == 'CDMX': variaciones_ciudad.extend(['cdmx', 'Ciudad de Mexico', 'cd. mx', 'cdmx.'])
    if ciudad_real == 'Guadalajara': variaciones_ciudad.extend(['Gdl', ' gdl ','guadalajara'])
    if ciudad_real == 'Monterrey': variaciones_ciudad.extend(['Mty', 'mty','monterrey'])
    if ciudad_real == 'Culiacán': variaciones_ciudad.extend(['culiacan', 'Culiacan', 'culi'])
    if ciudad_real == 'Veracruz': variaciones_ciudad.extend(['veracruz', 'ver', 'veracru'])
    if ciudad_real == 'Chihuahua': variaciones_ciudad.extend(['chihuahua', 'chih', 'chihua'])
    if ciudad_real == 'Puebla': variaciones_ciudad.extend(['puebla', 'pue', 'puebl'])
    if ciudad_real == 'Toluca': variaciones_ciudad.extend(['toluca', 'tol', 'tolu'])

    ciudad_sucia = random.choice(variaciones_ciudad)    # Aquí se asigna la ciudad sucia al perfil del cliente
    id_tienda_segura = MAPEO_TIENDAS[ciudad_real]       # Asignamos la tienda segura basada en la ciudad real, no en la sucia
    
    # Lógica de negocio para generar ingresos y gastos mensuales,
    # coherentes con la edad y nivel de fidelidad del cliente
    perfil = {
        "id_cliente": identificador,
        "nombre_completo": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
        "edad": random.randint(18, 70),
        "ciudad": ciudad_sucia,
        "ciudad_real_oculta": ciudad_real,
        "id_tienda_segura": id_tienda_segura,
        "ingresos": round(random.uniform(10000, 80000), 2),
        "gastos_mensuales": round(random.uniform(2000, 40000), 2),
        "puntos_lealtad": random.randint(0, 5000),
        "nivel_fidelidad": random.choices(niveles_fidelidad, weights=[50, 30, 15, 5])[0], # Mayor probabilidad de ser Bronce o Plata, menos de Oro y muy pocos Platino
        "preferencia": random.choice(categorias_nombres)
    }
    CLIENTES_MAESTROS.append(perfil)

# Definición de función para generar el archivo de inventario en CSV.
def generar_inventario_csv(ruta_archivo: str = RUTA_INVENTARIO_CSV) -> None:
    datos = []
    for prod in PRODUCTOS_MAESTROS:
        item = prod.copy()
        item['stock_actual'] = random.randint(10, 500)
        datos.append(item)
            
    df_inventario = pd.DataFrame(datos) # Aquí tendremos 792 filas base
    
    # Lógica para inyectar suciedad en el inventario, incluyendo duplicados y nulos, 
    # y desordenar las filas para que la suciedad esté esparcida aleatoriamente
    cantidad_base = len(df_inventario)
    
    # 1. Inyectamos 5% de Duplicados (Rúbrica)
    cantidad_5_pct = int(cantidad_base * 0.05)
    filas_duplicadas = df_inventario.sample(n=cantidad_5_pct, replace=True, random_state=42)
    df_inventario = pd.concat([df_inventario, filas_duplicadas], ignore_index=True)
    
    # 2. Inyectamos 10% de Nulos (Rúbrica)
    total_filas = len(df_inventario) # Filas base + duplicados
    cantidad_10_pct = int(total_filas * 0.10)
    
    # Distribuimos los nulos principalmente en la columna numérica 'stock_actual'
    indices_nulos_stock = random.sample(range(total_filas), cantidad_10_pct)
    df_inventario.loc[indices_nulos_stock, 'stock_actual'] = np.nan
    
    # También metemos algunos nulos en 'categoria' para que haya limpieza de texto
    indices_nulos_cat = random.sample(range(total_filas), int(cantidad_10_pct * 0.3)) 
    df_inventario.loc[indices_nulos_cat, 'categoria'] = np.nan
    
    # Desordenamos el DataFrame para que la "suciedad" esté esparcida aleatoriamente
    df_inventario = df_inventario.sample(frac=1, random_state=random.randint(1, 100)).reset_index(drop=True)

    # Guardamos el archivo CSV
    df_inventario.to_csv(ruta_archivo, index=False, encoding='utf-8')
    logging.info(f"CSV: Generado inventario de {total_filas} filas (con {cantidad_5_pct} duplicados y {cantidad_10_pct} nulos) en '{ruta_archivo}'.")

# Definición de función para generar el archivo de logs con lógica de negocio realista, 
# incluyendo endpoints vinculados a productos y clientes
def generar_perfiles_json(ruta_archivo: str = RUTA_PERFILES_JSON) -> None:
    with open(ruta_archivo, 'w', encoding='utf-8') as archivo_json:
        json.dump(CLIENTES_MAESTROS, archivo_json, indent=4, ensure_ascii=False)
    logging.info(f"JSON: Generados {len(CLIENTES_MAESTROS)} perfiles realistas en '{ruta_archivo}'.")

# Definición de función para generar el archivo XML de catálogos con detalles adicionales, como descripción de la categoría, 
# margen de ganancia esperado, responsable del área y nivel de prioridad para la gestión de esa categoría
def generar_catalogos_xml(ruta_archivo: str = RUTA_CATALOGOS_XML) -> None:
    raiz = ET.Element("catalogos")
    
    # Detalles adicionales para cada categoría, con lógica de negocio realista basada en la naturaleza de los productos
    detalles_categoria = {
        'Tecnología': {'margen': '15%', 'responsable': 'Ana G.', 'prioridad': 'Alta', 'desc': 'Electrónica y gadgets de consumo.'},
        'Hogar': {'margen': '25%', 'responsable': 'Carlos M.', 'prioridad': 'Media', 'desc': 'Muebles, decoración y electrodomésticos.'},
        'Deportes': {'margen': '30%', 'responsable': 'Luis F.', 'prioridad': 'Media', 'desc': 'Ropa y equipo para actividades físicas.'},
        'Moda': {'margen': '40%', 'responsable': 'Sofía R.', 'prioridad': 'Alta', 'desc': 'Prendas de vestir y accesorios de temporada.'},
        'Libros': {'margen': '20%', 'responsable': 'Elena T.', 'prioridad': 'Baja', 'desc': 'Literatura, textos académicos y cómics.'}
    }
    
    # Creamos un nodo XML para cada categoría, incluyendo los detalles adicionales
    for nombre_categoria in CATALOGO_PRODUCTOS.keys():
        detalles = detalles_categoria.get(nombre_categoria, {'margen': '20%', 'responsable': 'Pendiente', 'prioridad': 'Media', 'desc': 'Categoría general.'})
        nodo_categoria = ET.SubElement(raiz, "categoria", nombre=nombre_categoria)
        ET.SubElement(nodo_categoria, "descripcion").text = detalles['desc']
        ET.SubElement(nodo_categoria, "margen_ganancia_esperado").text = detalles['margen']
        ET.SubElement(nodo_categoria, "responsable_area").text = detalles['responsable']
        ET.SubElement(nodo_categoria, "nivel_prioridad").text = detalles['prioridad']
    
    # Guardamos el árbol XML en un archivo, asegurándonos de crear las carpetas necesarias y de que el XML esté bien formateado
    arbol = ET.ElementTree(raiz)
    if hasattr(ET, 'indent'):
        ET.indent(arbol, space="\t", level=0)
        
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    arbol.write(ruta_archivo, encoding="utf-8", xml_declaration=True)
    logging.info(f"XML: Generado catálogo de categorías en '{ruta_archivo}'.")

# Definición de función para generar el archivo de ventas en SQLite con lógica de negocio realista,
# incluyendo la asignación de tiendas basada en la ciudad del cliente y formatos de fecha inconsistentes
def generar_ventas_sql(ruta_base_datos: str = RUTA_VENTAS_SQL, cantidad_registros: int = 5000) -> None:
    try:
        
        # Conectamos a SQLite y preparamos la tabla de ventas, asegurándonos de incluir el campo id_tienda
        conexion = sqlite3.connect(ruta_base_datos)
        cursor = conexion.cursor()
        
        # Creación de la tabla de ventas con el nuevo campo id_tienda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id_tienda INTEGER,
                id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                id_producto INTEGER,
                id_cliente INTEGER,
                monto REAL,
                metodo_pago TEXT,
                fecha_transaccion TEXT
            )
            ''')
        cursor.execute('DELETE FROM ventas') 
        
        # Generamos transacciones comerciales, asignando la tienda basada en la ciudad del cliente y formatos de fecha inconsistentes
        datos_ventas = []
        fecha_base = datetime(2025, 1, 1)
        metodos = ['Tarjeta de Crédito', 'Tarjeta de Débito', 'Efectivo', 'MercadoPago', 'Transferencia']
        
        for _ in range(cantidad_registros):
            # 1. Escogemos un cliente real de nuestro maestro de clientes
            cliente_comprador = random.choice(CLIENTES_MAESTROS)
            id_cliente = cliente_comprador['id_cliente']
            
            # 2. Asignamos la tienda basada en la ciudad real del cliente, no en la sucia, 
            # para mantener la lógica de negocio coherente
            ciudad_para_mapeo = cliente_comprador['ciudad_real_oculta']
            id_tienda_simulada = MAPEO_TIENDAS[ciudad_para_mapeo]
            
            # 3. Escogemos un producto real de nuestro maestro de productos para generar una venta coherente
            producto_vendido = random.choice(PRODUCTOS_MAESTROS)
            id_producto = producto_vendido['id_producto']
            precio_base = producto_vendido['precio_unitario']
            
            # Lógica para generar montos de venta cpherentes, aplicando descuentos aleatorios y cantidades variables, 
            # además de formatos de fecha inconsistentes
            cantidad = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            descuento = random.choices([1.0, 0.9, 0.85], weights=[70, 20, 10])[0] 
            monto = round((precio_base * cantidad) * descuento, 2)
            dias_sumar = random.randint(0, 365)
            fecha_venta = fecha_base + timedelta(days=dias_sumar)
            formatos_posibles = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"]
            fecha_sucia = fecha_venta.strftime(random.choice(formatos_posibles))
            
            datos_ventas.append((
                id_cliente, 
                id_producto, 
                monto, 
                random.choice(metodos),
                fecha_sucia,
                id_tienda_simulada
            ))
        
        # Insertamos los datos generados en la tabla de ventas, 
        # asegurándonos de que el orden de los campos coincida con la definición de la tabla
        cursor.executemany('INSERT INTO ventas (id_cliente, id_producto, monto, metodo_pago, fecha_transaccion, id_tienda) VALUES (?, ?, ?, ?, ?, ?)', datos_ventas)
        conexion.commit()
        logging.info(f"SQLite: Generadas {cantidad_registros} transacciones comerciales en '{ruta_base_datos}'.")
        
    except sqlite3.Error as error_sql:
        logging.error(f"Error al generar SQLite: {error_sql}")
    finally:
        if conexion:
            conexion.close()

# Definición de función para generar el archivo de metas anuales en Excel,
# incluyendo metas de ventas coherentes con el tamaño de la ciudad y crecimiento esperado basado en tendencias
def generar_metas_excel(ruta_archivo: str = RUTA_METAS_EXCEL) -> None:
    datos_metas = []
    categorias = list(CATALOGO_PRODUCTOS.keys())
    
    for ciudad in CIUDADES:
        meta_ventas = random.randint(500000, 2500000)       # Metas de ventas anuales entre 500k y 2.5M MXN, coherentes con el tamaño de la ciudad
        crecimiento = round(random.uniform(5.0, 25.0), 2)   # Crecimiento esperado entre 5% y 25%, basado en tendencias de mercado y potencial de cada ciudad
        
        datos_metas.append({
            'ciudad': ciudad,
            'meta_ventas_mxn': meta_ventas,
            'crecimiento_esperado_pct': crecimiento,
            'categoria_impulso': random.choice(categorias)
        })
        
    df_metas = pd.DataFrame(datos_metas)
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    df_metas.to_excel(ruta_archivo, index=False, engine='openpyxl')
    logging.info(f"Excel: Generadas metas anuales para {len(CIUDADES)} regiones en '{ruta_archivo}'.")

# Definición de función para generar el archivo de logs con lógica de negocio,
# incluyendo endpoints vinculados a productos y clientes, códigos de estado variados y tiempos de respuesta real
def generar_logs_txt(ruta_archivo: str = RUTA_LOGS_TXT, cantidad_lineas: int = 2000) -> None:
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    endpoints_genericos = ['/inicio', '/carrito', '/checkout', '/api/pagos', '/login']
    codigos_estado = [200, 200, 200, 200, 201, 400, 404, 500] 
    
    fecha_base = datetime.now() - timedelta(days=30)
    
    # Generamos líneas de log con IPs aleatorias, fechas con formatos inconsistentes, métodos HTTP variados, 
    # endpoints vinculados a productos y clientes, códigos de estado y tiempos de respuesta variados
    with open(ruta_archivo, 'w', encoding='utf-8') as archivo_txt:
        for _ in range(cantidad_lineas):
            ip = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            fecha_base += timedelta(minutes=random.randint(1, 60))
            fecha_str = fecha_base.strftime("%Y-%m-%d %H:%M:%S")
            
            metodo = random.choices(['GET', 'POST', 'PUT'], weights=[70, 25, 5])[0]
            estado = random.choice(codigos_estado)
            tiempo_ms = random.randint(20, 1500) 
            
            if random.random() > 0.4: 
                producto = random.choice(PRODUCTOS_MAESTROS)
                cliente = random.choice(CLIENTES_MAESTROS)
                endpoint = f"/catalogo/producto/{producto['id_producto']}?cliente={cliente['id_cliente']}"
            else:
                endpoint = random.choice(endpoints_genericos)
            
            linea_log = f"[{fecha_str}] {ip} {metodo} {endpoint} {estado} {tiempo_ms}ms\n"
            archivo_txt.write(linea_log)
            
    logging.info(f"TXT: Generados {cantidad_lineas} registros web vinculados en '{ruta_archivo}'.")

# Punto de entrada para ejecutar la generación de datos, asegurándonos de que las carpetas necesarias existan antes de generar los archivos, 
# para evitar errores de escritura
if __name__ == "__main__":
    logging.info("====== INICIANDO SIMULACIÓN DE DATOS RETAIL ======")
    
    # Antes de generar los archivos, nos aseguramos de que las carpetas necesarias existan para evitar errores de escritura
    carpetas_necesarias = [
        'bodega_datos/1_brutos',
        'bodega_datos/2_procesados',
        'bodega_datos/3_visualizaciones'
    ]
    
    # Nos aseguramos de que todas las carpetas necesarias existan antes de generar los archivos, para evitar errores de escritura
    for carpeta in carpetas_necesarias:
        os.makedirs(carpeta, exist_ok=True)
    # Generamos cada uno de los archivos con la lógica de negocio y sucia incorporada
    generar_inventario_csv() 
    generar_perfiles_json()
    generar_catalogos_xml()
    generar_ventas_sql()
    generar_metas_excel()
    generar_logs_txt()
    logging.info("====== SIMULACIÓN DE DATOS COMPLETADA ======")