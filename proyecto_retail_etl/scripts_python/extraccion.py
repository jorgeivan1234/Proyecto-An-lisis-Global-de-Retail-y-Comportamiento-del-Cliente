"""
Módulo: extraccion.py
Descripción: Contiene las clases encargadas de conectarse a diversas fuentes de datos 
(SQL, NoSQL, APIs, Archivos) para extraer la información cruda y convertirla en DataFrames.
Ajustado para la versión 2.0 de los datos (nuevas métricas y dimensiones).
"""

import sqlite3
import logging
import requests
import re
import random
import pandas as pd
from pymongo import MongoClient
from typing import Optional
from bs4 import BeautifulSoup


# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ExtractorVentasSQL:
    """ 
    Clase responsable de conectarse a la base de datos SQLite y extraer las transacciones. 
    """
    
    def __init__(self, ruta_base_datos: str):
        self.ruta_base_datos = ruta_base_datos

    def extraer_incremental(self, ultimo_id: int = 0, limite: int = 5000) -> pd.DataFrame:
        """
        Extrae registros de ventas nuevos basándose en el último ID procesado.
        
        Args:
            ultimo_id (int): El ID de venta desde donde se empezará a leer.
            limite (int): Cantidad máxima de registros a extraer.
            
        Returns:
            pd.DataFrame: Tabla con los datos de ventas extraídos.
        """
        logging.info(f"Conectando a SQLite en: '{self.ruta_base_datos}'...")
        conexion = None
        try:
            conexion = sqlite3.connect(self.ruta_base_datos)
            
            # ¡ACTUALIZACIÓN V2.0! Añadimos id_producto y metodo_pago a la consulta SQL
            consulta = f"""
                SELECT id_venta, id_cliente, id_producto, monto, metodo_pago, fecha_transaccion 
                FROM ventas 
                WHERE id_venta > {ultimo_id} 
                LIMIT {limite}
            """
            df_ventas = pd.read_sql_query(consulta, conexion)
            logging.info(f"Éxito: Extraídos {len(df_ventas)} registros de ventas de SQLite.")
            return df_ventas
            
        except sqlite3.Error as error_sql:
            logging.error(f"Fallo al extraer de SQLite: {error_sql}")
            return pd.DataFrame() # Devolvemos un DataFrame vacío para no romper el pipeline
            
        finally:
            if conexion:
                conexion.close()


class ExtractorPerfilesMongo:
    """ 
    Clase para extraer perfiles de clientes desde MongoDB, con un sistema 
    de respaldo (fallback) que lee desde un archivo JSON si la base de datos falla.
    """
    
    def __init__(self, uri: str, nombre_bd: str, nombre_coleccion: str, ruta_respaldo_json: str):
        self.uri = uri
        self.nombre_bd = nombre_bd
        self.nombre_coleccion = nombre_coleccion
        self.ruta_respaldo_json = ruta_respaldo_json # ¡Mejora! Ahora la ruta se inyecta desde afuera

    def extraer_perfiles(self) -> Optional[pd.DataFrame]:
        """
        Intenta leer de MongoDB. Si no hay conexión, lee el archivo JSON local.
        
        Returns:
            pd.DataFrame: Tabla con los perfiles, o None si ambos métodos fallan.
        """
        try:
            logging.info("Intentando conexión a MongoDB para perfiles de cliente...")
            cliente_mongo = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            base_datos = cliente_mongo[self.nombre_bd]
            coleccion = base_datos[self.nombre_coleccion]
            
            # Buscamos todos los documentos excluyendo el ID interno de Mongo
            datos_crudos = list(coleccion.find({}, {"_id": 0}))
            df_perfiles = pd.DataFrame(datos_crudos)
            
            logging.info(f"Éxito: Extraídos {len(df_perfiles)} perfiles desde MongoDB.")
            cliente_mongo.close()
            return df_perfiles
            
        except Exception as error_mongo:
            logging.warning(f"MongoDB no disponible ({error_mongo}). Activando Plan B (Respaldo JSON)...")
            
            try:
                # Utilizamos la ruta inyectada en lugar de hardcodearla aquí
                df_respaldo = pd.read_json(self.ruta_respaldo_json)
                logging.info(f"Éxito (Plan B): Extraídos {len(df_respaldo)} perfiles desde '{self.ruta_respaldo_json}'.")
                return df_respaldo
                
            except Exception as error_json:
                logging.error(f"Fallo crítico: El plan B también falló. Error: {error_json}")
                return None

class ExtractorLogs:
    """ Lee el archivo de texto plano y usa RegEx para extraer IDs, estados y tiempos. """
    
    def procesar_logs(self, ruta_archivo: str) -> pd.DataFrame:
        logging.info("Scraping: Procesando logs del servidor web...")
        
        # Nuestro nuevo patrón detector que atrapa 4 datos
        patron = r"producto/(\d+)\?cliente=(\d+) (\d+) (\d+)ms"
        datos_encontrados = []
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                for linea in archivo:
                    coincidencia = re.search(patron, linea)
                    
                    if coincidencia:
                        # Ahora atrapamos los 4 grupos de números
                        datos_encontrados.append({
                            'id_producto': int(coincidencia.group(1)),
                            'id_cliente': int(coincidencia.group(2)),
                            'codigo_estado': int(coincidencia.group(3)),
                            'tiempo_respuesta_ms': int(coincidencia.group(4))
                        })
            
            df_logs = pd.DataFrame(datos_encontrados)
            logging.info(f"Éxito: Se extrajeron {len(df_logs)} registros útiles de los logs.")
            return df_logs
            
        except FileNotFoundError:
            logging.error(f"Error: No se encontró el archivo {ruta_archivo}")
            return pd.DataFrame()
            
class ExtractorTiposCambioAPI:
    """ 
    Clase responsable de conectarse a una API REST pública 
    para extraer los tipos de cambio actualizados. 
    """
    def __init__(self, url_base: str = "https://open.er-api.com/v6/latest/MXN"):
        # Usamos una API gratuita que no requiere clave de acceso
        self.url_base = url_base

    def extraer_tipos_cambio(self) -> pd.DataFrame:
        """ Ejecuta la petición GET y convierte el JSON resultante en un DataFrame. """
        try:
            logging.info(f"API: Solicitando tipos de cambio a {self.url_base}...")
            
            # Hacemos la petición a la web
            respuesta = requests.get(self.url_base)
            
            # Validamos que el servidor nos responda con un "200 OK"
            respuesta.raise_for_status()
            
            # Convertimos la respuesta de texto a un diccionario de Python
            datos_json = respuesta.json()
            tasas = datos_json.get('rates', {})
            
            # Transformamos el diccionario en una tabla (DataFrame)
            df_tasas = pd.DataFrame(list(tasas.items()), columns=['moneda', 'tasa_cambio_vs_mxn'])
            
            logging.info(f"Éxito: Extraídas {len(df_tasas)} divisas desde la API.")
            return df_tasas
            
        except requests.exceptions.RequestException as error_api:
            logging.error(f"Error al conectar con la API de divisas: {error_api}")
            return pd.DataFrame() # Retornamos un DataFrame vacío si falla

class ExtractorPreciosCompetencia:
    """ Simula la extracción de precios dinámicos de la competencia basados en el inventario real. """
    
    def extraer_precios_html(self, df_inventario: pd.DataFrame) -> pd.DataFrame:
        logging.info("Scraping: Simulando extracción dinámica de precios de la competencia...")
        
        # Validamos que el inventario no esté vacío
        if df_inventario is None or df_inventario.empty:
            return pd.DataFrame()

        datos = []
        # Iteramos sobre cada producto de nuestro inventario real
        for indice, fila in df_inventario.iterrows():
            producto = fila['nombre_producto']
            precio_nuestro = fila['precio_unitario']
            
            # Simulamos un precio de la competencia: +/- 5% de nuestro precio
            variacion = random.uniform(-0.05, 0.05)
            precio_competencia = round(precio_nuestro * (1 + variacion), 2)
            
            datos.append({'producto': producto, 'precio_competencia': precio_competencia})
            
        df_competencia = pd.DataFrame(datos)
        logging.info(f"Éxito: Generados {len(df_competencia)} precios de la competencia.")
        return df_competencia