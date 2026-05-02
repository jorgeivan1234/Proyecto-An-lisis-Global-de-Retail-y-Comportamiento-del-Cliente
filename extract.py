# extract.py - Módulo de extracción de datos para el proyecto de análisis global de retail y comportamiento del cliente
# Este módulo define varias clases de extractores para obtener datos desde diferentes fuentes, incluyendo bases de datos SQL, bases de datos NoSQL (MongoDB), APIs REST y mediante Web Scraping.
# Cada clase está diseñada para manejar la conexión, consulta y extracción de datos de su fuente específica, con manejo de errores y logging para facilitar la depuración y el seguimiento del proceso de extracción.
import sqlite3
import requests
import pandas as pd
import logging
from bs4 import BeautifulSoup
from pymongo import MongoClient
from typing import Optional

# Configuración básica de loggingpara el registro de eventos en la consola.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VentasSQLExtractor:
    """ Clase encargada de la extracción de ventas históricas desde una base de datos SQL. """
    def __init__(self, db_path: str):
        self.db_path = db_path

    # Método privado para establecer la conexión a la base de datos SQL, con manejo de errores.
    def _get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error al conectar a la base de datos SQL: {e}")
            raise

    def extraer_incremental(self, ultimo_id: int = 0, limite: int = 500) -> Optional[pd.DataFrame]:
        """ Realiza una extracción incremental de la tabla ventas_historicas limitando por lotes."""
        query = """
            SELECT id_transaccion, id_cliente, monto, fecha, id_tienda 
            FROM ventas_historicas 
            WHERE id_transaccion > ? 
            ORDER BY id_transaccion ASC 
            LIMIT ?
                """
        # Intentamos ejecutar la consulta SQL con los parámetros proporcionados, manejando cualquier error que pueda ocurrir durante la conexión o la consulta.
        try:
            with self._get_connection() as conn:
                logging.info(f"Ejecutando extracción incremental: ID mayor a {ultimo_id}, Límite: {limite}")
                df_ventas = pd.read_sql_query(query, conn, params=(ultimo_id, limite))
                logging.info(f"Se extrajeron {len(df_ventas)} registros exitosamente de SQL.")
                return df_ventas
        # Si ocurre cualquier error durante la extracción, se captura y se registra el error, devolviendo None para indicar que la extracción falló.
        except Exception as e:
            logging.error(f"Error durante la extracción incremental: {e}")
            return None

class PerfilesMongoExtractor:
    """ Extrae los perfiles de usuario desde una base de datos NoSQL (MongoDB). """
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name

    # Método para extraer los perfiles de usuario desde MongoDB, con manejo de errores y un plan B para leer desde un archivo local si la conexión falla.
    def extraer_perfiles(self) -> Optional[pd.DataFrame]:
        try:
            logging.info("Conectando a MongoDB para extraer perfiles...")
            cliente = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            db = cliente[self.db_name]
            coleccion = db[self.collection_name]
            
            # Omisión del id interno de Mongo para evitar conflictos con Pandas.
            datos = list(coleccion.find({}, {"_id": 0}))
            df_perfiles = pd.DataFrame(datos)
            
            # Log de resumen de la extracción, indicando cuántos perfiles se extrajeron exitosamente.
            logging.info(f"Se extrajeron {len(df_perfiles)} perfiles de MongoDB.")
            cliente.close()
            return df_perfiles
        
        # Si ocurre cualquier error durante la conexión o extracción de MongoDB, se captura el error, se registra y se intenta leer desde un archivo local como plan B, manejando también cualquier error que pueda ocurrir en ese proceso.
        except Exception as e:
            logging.error(f"Error al extraer datos de MongoDB: {e}")
            logging.warning("Intentando leer el archivo local perfiles_usuarios.json como plan B...")
            # Si el plan B también falla, se captura el error y se devuelve None para indicar que la extracción de perfiles no fue exitosa.
            try:
                return pd.read_json('perfiles_usuarios.json', lines=True)
            except Exception as ex:
                logging.error(f"Fallo el plan B: {ex}")
                return None

class APIExchangeExtractor:
    """ Consume una API REST pública para obtener tipos de cambio actuales. """
    def __init__(self, url: str):
        self.url = url

    # Método para consumir la API REST y obtener los tipos de cambio, con manejo de errores para problemas de conexión o respuestas no exitosas.
    def obtener_tipos_de_cambio(self) -> Optional[pd.DataFrame]:
        try:
            logging.info(f"Consumiendo API REST desde: {self.url}")
            response = requests.get(self.url, timeout=10)
            response.raise_for_status() 
            
            datos_json = response.json()
            # Uso de la estructura de Frankfurter API: ("rates": ("USD": 1.05, ...)).
            tasas = datos_json.get('rates', {})
            
            df_tasas = pd.DataFrame(list(tasas.items()), columns=['Moneda', 'Tasa_Conversion'])
            logging.info(f"Se extrajeron {len(df_tasas)} tasas de cambio exitosamente.")
            return df_tasas
        
        # Si ocurre cualquier error durante la conexión o el consumo de la API, se captura el error y se registra, devolviendo None para indicar que la extracción de tipos de cambio no fue exitosa.
        except requests.exceptions.RequestException as e:
            logging.error(f"Error de conexión con la API REST: {e}")
            return None

class CompetenciaScraper:
    """ Extrae información de precios de la competencia mediante Web Scraping buscando tablas HTML."""
    def __init__(self, url: str):
        self.url = url

    # Método para realizar Web Scraping y extraer datos de precios desde una tabla HTML, con manejo de errores para problemas de conexión o si no se encuentra la tabla esperada.
    def extraer_precios_html(self) -> Optional[pd.DataFrame]:
        try:
            logging.info(f"Iniciando Web Scraping en: {self.url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tabla = soup.find('table') 
            
            # Si se encuentra la tabla, se convierte a DataFrame usando Pandas, y se registra el número de registros extraídos.
            # Si no se encuentra la tabla, se registra una advertencia y se devuelve None.
            if tabla:
                df_scraper = pd.read_html(str(tabla))[0]
                logging.info(f"Scraping completado. Se extrajeron {len(df_scraper)} registros con éxito.")
                return df_scraper
            else:
                logging.warning("No se encontró ninguna tabla HTML en la página.")
                return None
        
        # Si ocurre cualquier error durante el proceso de Web Scraping, se captura el error y se registra, devolviendo None para indicar que la extracción de precios no fue exitosa.        
        except Exception as e:
            logging.error(f"Error durante el Web Scraping: {e}")
            return None