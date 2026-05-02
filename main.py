# main.py - Orquestador del Pipeline de Datos para Análisis Global de Retail y Comportamiento del Cliente
# Este script coordina la ejecución de las fases de extracción, transformación, visualización y exportación de datos.
# Importamos las clases y funciones necesarias de los módulos extract, transform y visualize
import logging
from extract import VentasSQLExtractor, PerfilesMongoExtractor # Importamos tus extractores
from transform import DataTransformer # Importamos tu transformador
from visualize import VisualizadorDashboard # Importamos el visualizador
import pandas as pd

# Configuración del logging para mostrar mensajes informativos con timestamps y niveles de log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Función principal que ejecuta todo el pipeline de datos, desde la extracción hasta la exportación final
def ejecutar_pipeline():
    logging.info("=== INICIANDO PIPELINE DE DATOS ===")
    
    # Cada fase del pipeline se ejecuta secuencialmente, con logs informativos para seguir el progreso y detectar posibles errores
    # FASE 1: EXTRACCIÓN (Mockup con datos de prueba) - Aquí se simula la extracción de datos desde una base de datos SQL y un sistema NoSQL, generando DataFrames temporales para continuar con el proceso
    logging.info("--- Fase 1: Extracción ---")
    
    # Asumiendo que ejecutaste mock_data.py y tienes tu base de datos SQLite
    extractor_sql = VentasSQLExtractor(db_path='ventas_historicas.sqlite')
    df_ventas = extractor_sql.extraer_incremental(ultimo_id=0, limite=5000)
    
    # Simulamos el DataFrame de inventario leyéndolo directamente (ya lo generaste)
    df_inventario = pd.read_csv('inventario.csv')
    
    # Simulamos los perfiles (si MongoDB falla, usamos el DF temporal generado abajo)
    df_perfiles = pd.DataFrame({
        'id_cliente': range(100, 2000),
        'edad': [20 + (i % 40) for i in range(1900)],
        'preferencia': ['Tecnología' if i % 2 == 0 else 'Hogar' for i in range(1900)]
    })

    # FASE 2: TRANSFORMACIÓN Y PCA - Aquí se limpian los datos, se enriquecen con información adicional, se aplican reglas de negocio y finalmente se ejecuta el PCA para reducir la dimensionalidad y preparar los datos para la visualización
    logging.info("--- Fase 2: Transformación y Calidad ---")
    transformer = DataTransformer()
    
    ventas_limpias, inventario_limpio = transformer.limpiar_datos(df_ventas, df_inventario)
    df_master = transformer.enriquecer_datos(ventas_limpias, df_perfiles)
    df_master = transformer.aplicar_reglas_negocio(df_master)
    
    df_master_final, pca_model = transformer.ejecutar_pca(df_master)

    # FASE 3: VISUALIZACIÓN - En esta fase se generan gráficos avanzados para el reporte final, incluyendo boxplots para detectar outliers, scatter plots para visualizar clusters y diagramas de sankey para mostrar el embudo de conversión. Se utilizan librerías como Matplotlib, Seaborn y Plotly para crear visualizaciones estáticas e interactivas.
    logging.info("--- Fase 3: Visualización ---")
    visualizador = VisualizadorDashboard()
    visualizador.graficar_boxplots(df_master_final)
    visualizador.graficar_pca_scatter(df_master_final)
    visualizador.graficar_sankey()

    # FASE 4: EXPORTACIÓN PARA BI - Finalmente, se exporta el DataFrame limpio y enriquecido a un formato Parquet, que es eficiente para su uso en herramientas de Business Intelligence como Power BI o Tableau. Se asegura de que el archivo esté listo para ser consumido por estas plataformas para análisis adicionales y creación de dashboards.
    logging.info("--- Fase 4: Exportación ---")
    ruta_salida = 'data_master_clean.parquet'
    
    # Exportamos el archivo limpio a Parquet (Requiere pyarrow)
    df_master_final.to_parquet(ruta_salida, index=False)
    
    logging.info(f"Pipeline ejecutado exitosamente. Archivo final guardado en: {ruta_salida}")
    logging.info("=== FIN DEL PIPELINE ===")

if __name__ == "__main__":
    ejecutar_pipeline()