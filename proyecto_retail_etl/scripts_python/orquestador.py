"""
Módulo: orquestador.py
Descripción: Script principal que dirige el pipeline ETL. 
Incluye telemetría (medición de tiempos) y manejo global de excepciones.
"""

# Importación de librerías para manejo de tiempo, logging y procesamiento de datos
import logging                                      # Para el registro de eventos y errores
import time                                         # Para medir la duración de cada fase del pipeline
import pandas as pd                                 # Para manejo de DataFrames, aunque se espera que los datos ya estén procesados
from extraccion import ExtractorVentasSQL           # Para la extracción de datos de ventas desde SQL
from extraccion import ExtractorPerfilesMongo       # Para la extracción de perfiles de usuarios desde MongoDB
from extraccion import ExtractorPreciosCompetencia  # Para la extracción de precios de competencia desde HTML
from extraccion import ExtractorTiposCambioAPI      # Para la extracción de tipos de cambio desde una API
from extraccion import ExtractorLogs                # Para la extracción y procesamiento de logs del servidor
from transformacion import TransformadorDatos       # Para la transformación, limpieza y modelado de los datos
from visualizacion import VisualizadorDashboard     # Para la creación de visualizaciones analíticas basadas en los datos procesados

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constantes de rutas para las fuentes de datos y destino final
RUTA_SQL = 'bodega_datos/1_brutos/ventas_historicas.sqlite'
RUTA_CSV_INVENTARIO = 'bodega_datos/1_brutos/inventario.csv'
RUTA_JSON_PERFILES = 'bodega_datos/1_brutos/perfiles_usuarios.json'
RUTA_XML_CATALOGOS = 'bodega_datos/1_brutos/catalogos.xml'
RUTA_EXCEL_METAS = 'bodega_datos/1_brutos/metas_anuales.xlsx'
RUTA_PARQUET_FINAL = 'bodega_datos/2_procesados/datos_maestros_limpios.parquet'
RUTA_LOGS_TXT = 'bodega_datos/1_brutos/logs_servidor.txt'

# Función principal que ejecuta el pipeline completo
def ejecutar_pipeline() -> None:
    tiempo_inicio = time.time()
    logging.info("====== INICIANDO PIPELINE DE DATOS =======")

    try:
        # -------------------------------------------------------------------------
        # FASE 1: EXTRACCIÓN
        # -------------------------------------------------------------------------
        logging.info("------ Fase 1: Extracción ------")
        
        # Extracción de datos desde diversas fuentes utilizando las clases del módulo de extraccion.py
        extractor_ventas = ExtractorVentasSQL(ruta_base_datos=RUTA_SQL)
        datos_ventas = extractor_ventas.extraer_incremental(ultimo_id=0, limite=10000)
        datos_inventario = pd.read_csv(RUTA_CSV_INVENTARIO)
        datos_catalogos = pd.read_xml(RUTA_XML_CATALOGOS)
        datos_metas = pd.read_excel(RUTA_EXCEL_METAS)
        
        # Creación de una instancia del extractor de perfiles desde MongoDB
        extractor_perfiles = ExtractorPerfilesMongo(
            uri="mongodb://localhost:27017", 
            nombre_bd="retail", 
            nombre_coleccion="perfiles", 
            ruta_respaldo_json=RUTA_JSON_PERFILES
        )
        # Extraemos los perfiles de usuarios desde MongoDB y los convertimos en un DataFrame
        datos_perfiles = extractor_perfiles.extraer_perfiles()

        # Extraemos y procesamos los logs del servidor para obtener insights sobre el comportamiento de los usuarios y posibles incidencias
        extractor_logs = ExtractorLogs()
        df_logs = extractor_logs.procesar_logs(RUTA_LOGS_TXT)
        
        # Extraemos los precios de la competencia desde HTML y los convertimos en un DataFrame para su posterior análisis y comparación
        extractor_html = ExtractorPreciosCompetencia()
        df_competencia = extractor_html.extraer_precios_html(datos_inventario)

        # Extraemos los tipos de cambio desde una API externa para convertir los montos de venta a una moneda común (USD) y facilitar el análisis comparativo
        extractor_api = ExtractorTiposCambioAPI()
        df_divisas = extractor_api.extraer_tipos_cambio()
        
        # Buscamos la fila del Peso Mexicano ('MXN') en la tabla de 65 divisas
        tasa_usd = 1.0 
        if not df_divisas.empty:
            fila_mxn = df_divisas[df_divisas['moneda'] == 'MXN']
            if not fila_mxn.empty:
                tasa_usd = fila_mxn['tasa_cambio_vs_usd'].values[0]
                    
        # -------------------------------------------------------------------------
        # FASE 2: TRANSFORMACIÓN Y MODELADO
        # -------------------------------------------------------------------------
        logging.info("------ Fase 2: Transformación y Calidad ------")
        
        # Creamos una instancia del transformador de datos para realizar las operaciones de limpieza, enriquecimiento y modelado
        transformador = TransformadorDatos()
        
        # Limpiamos los datos de ventas e inventario utilizando las funciones del transformador, asegurando que los datos estén en un formato adecuado para el análisis y modelado posterior
        ventas_limpias, inventario_limpio = transformador.limpiar_datos(datos_ventas, datos_inventario)
        
        # Pasamos df_competencia al cruce de datos
        df_maestro = transformador.enriquecer_datos(ventas_limpias, datos_perfiles, inventario_limpio, df_competencia, datos_catalogos, datos_metas, df_logs)
        
        # Pasamos la tasa_usd a las reglas de negocio
        df_maestro = transformador.aplicar_reglas_negocio(df_maestro, tasa_usd)
        
        # Aplicamos PCA para reducir la dimensionalidad de los datos y facilitar la visualización y el análisis de patrones en los datos procesados
        df_maestro_final, modelo_pca = transformador.ejecutar_pca(df_maestro)
        
        # -------------------------------------------------------------------------
        # FASE 3: VISUALIZACIÓN
        # -------------------------------------------------------------------------
        logging.info("------ Fase 3: Visualización ------")
        
        # Creamos una instancia del visualizador de dashboard para generar las visualizaciones analíticas basadas en los datos procesados, 
        # utilizando las funciones del módulo de visualizacion.py
        visualizador = VisualizadorDashboard()
        
        # Generamos un boxplot para detectar outliers en los montos de venta, un scatter plot 3D basado en PCA para visualizar clusters de clientes, 
        # y un diagrama de Sankey para mostrar el flujo desde los logs hasta los segmentos finales, con un diseño explicativo y orientado al storytelling.
        visualizador.graficar_boxplots(df_maestro_final)
        visualizador.graficar_pca_scatter(df_maestro_final)
        visualizador.graficar_sankey(df_maestro_final)
        
        # -------------------------------------------------------------------------
        # FASE 4: EXPORTACIÓN PARA BI
        # -------------------------------------------------------------------------
        logging.info("------ Fase 4: Exportación ------")
        df_maestro_final.to_parquet(RUTA_PARQUET_FINAL, index=False)
        logging.info(f"Archivo maestro guardado en: {RUTA_PARQUET_FINAL}")
        
        tiempo_fin = time.time()
        duracion = round(tiempo_fin - tiempo_inicio, 2)
        logging.info(f"====== PIPELINE COMPLETADO EXITOSAMENTE EN {duracion} SEGUNDOS ======")
        
    # Manejo global de excepciones para capturar cualquier error crítico que ocurra durante la ejecución del pipeline
    except Exception as error_critico:
        logging.error(f"ha ocurrido un error crítico: {error_critico}")
        logging.info("El pipeline se detuvo por seguridad. Revisa el log de errores.")

# Punto de entrada del script para ejecutar el pipeline completo
if __name__ == "__main__":
    ejecutar_pipeline()