"""
Módulo: orquestador.py
Descripción: Script principal que dirige el pipeline ETL V2.0. 
Incluye telemetría (medición de tiempos) y manejo global de excepciones.
"""

import logging
import time
import pandas as pd
from extraccion import ExtractorVentasSQL 
from extraccion import ExtractorPerfilesMongo
from extraccion import ExtractorPreciosCompetencia
from extraccion import ExtractorTiposCambioAPI
from extraccion import ExtractorLogs
from transformacion import TransformadorDatos
from visualizacion import VisualizadorDashboard

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CONSTANTES DE RUTAS
RUTA_SQL = 'bodega_datos/1_brutos/ventas_historicas.sqlite'
RUTA_CSV_INVENTARIO = 'bodega_datos/1_brutos/inventario.csv'
RUTA_JSON_PERFILES = 'bodega_datos/1_brutos/perfiles_usuarios.json'
RUTA_XML_CATALOGOS = 'bodega_datos/1_brutos/catalogos.xml'
RUTA_EXCEL_METAS = 'bodega_datos/1_brutos/metas_anuales.xlsx'
RUTA_PARQUET_FINAL = 'bodega_datos/2_procesados/datos_maestros_limpios.parquet'
RUTA_LOGS_TXT = 'bodega_datos/1_brutos/logs_servidor.txt'

def ejecutar_pipeline() -> None:
    """ Ejecuta las fases del pipeline con monitoreo de tiempo y errores. """
    tiempo_inicio = time.time()
    logging.info("=== INICIANDO PIPELINE DE DATOS V2.0 ===")

    try:
        # -------------------------------------------------------------------------
        # FASE 1: EXTRACCIÓN
        # -------------------------------------------------------------------------
        logging.info("--- Fase 1: Extracción ---")
        
        extractor_ventas = ExtractorVentasSQL(ruta_base_datos=RUTA_SQL)
        datos_ventas = extractor_ventas.extraer_incremental(ultimo_id=0, limite=10000)
        
        datos_inventario = pd.read_csv(RUTA_CSV_INVENTARIO)
        datos_catalogos = pd.read_xml(RUTA_XML_CATALOGOS)
        datos_metas = pd.read_excel(RUTA_EXCEL_METAS)
        
        extractor_perfiles = ExtractorPerfilesMongo(
            uri="mongodb://localhost:27017", 
            nombre_bd="retail", 
            nombre_coleccion="perfiles", 
            ruta_respaldo_json=RUTA_JSON_PERFILES
        )
        datos_perfiles = extractor_perfiles.extraer_perfiles()

        extractor_logs = ExtractorLogs()
        df_logs = extractor_logs.procesar_logs(RUTA_LOGS_TXT)
        
        extractor_html = ExtractorPreciosCompetencia()
        df_competencia = extractor_html.extraer_precios_html(datos_inventario)

        extractor_api = ExtractorTiposCambioAPI()
        df_divisas = extractor_api.extraer_tipos_cambio()
        
        # Lógica para aislar el valor numérico del Dólar (USD)
        tasa_usd = 1.0 
        if not df_divisas.empty:
            # Filtramos la tabla para encontrar la fila del USD y extraemos su valor
            fila_usd = df_divisas[df_divisas['moneda'] == 'USD']
            if not fila_usd.empty:
                tasa_usd = fila_usd['tasa_cambio_vs_mxn'].values[0]
        # -------------------------------------------------------------------------
        # FASE 2: TRANSFORMACIÓN Y MODELADO
        # -------------------------------------------------------------------------
        logging.info("--- Fase 2: Transformación y Calidad ---")
        transformador = TransformadorDatos()
        
        ventas_limpias, inventario_limpio = transformador.limpiar_datos(datos_ventas, datos_inventario)
        
        # Pasamos df_competencia al cruce de datos
        df_maestro = transformador.enriquecer_datos(ventas_limpias, datos_perfiles, inventario_limpio, df_competencia, datos_catalogos, datos_metas, df_logs)
        
        # Pasamos la tasa_usd a las reglas de negocio
        df_maestro = transformador.aplicar_reglas_negocio(df_maestro, tasa_usd)
        
        df_maestro_final, modelo_pca = transformador.ejecutar_pca(df_maestro)

        # -------------------------------------------------------------------------
        # FASE 3: VISUALIZACIÓN
        # -------------------------------------------------------------------------
        logging.info("--- Fase 3: Visualización ---")
        visualizador = VisualizadorDashboard()
        
        visualizador.graficar_boxplots(df_maestro_final)
        visualizador.graficar_pca_scatter(df_maestro_final)
        visualizador.graficar_sankey(df_maestro_final)

        # -------------------------------------------------------------------------
        # FASE 4: EXPORTACIÓN PARA BI
        # -------------------------------------------------------------------------
        logging.info("--- Fase 4: Exportación ---")
        df_maestro_final.to_parquet(RUTA_PARQUET_FINAL, index=False)
        logging.info(f"Archivo maestro guardado en: {RUTA_PARQUET_FINAL}")
        
        tiempo_fin = time.time()
        duracion = round(tiempo_fin - tiempo_inicio, 2)
        logging.info(f"=== PIPELINE COMPLETADO EXITOSAMENTE EN {duracion} SEGUNDOS ===")

    except Exception as error_critico:
        logging.error(f"ERROR CRÍTICO EN EL PIPELINE: {error_critico}")
        logging.info("El pipeline se detuvo por seguridad. Revisa el log de errores.")

if __name__ == "__main__":
    ejecutar_pipeline()