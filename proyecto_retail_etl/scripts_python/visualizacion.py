"""
Módulo: visualizacion.py
Descripción: Se encarga de la generación de gráficos estadísticos y paneles 
interactivos basados en los datos procesados por el pipeline ETL.
"""

import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Intentamos importar Plotly de forma segura (Excelente práctica de tu código original)
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_DISPONIBLE = True
except ImportError:
    PLOTLY_DISPONIBLE = False

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VisualizadorDashboard:
    """ 
    Clase responsable de diseñar y exportar las visualizaciones analíticas del proyecto.
    """

    def __init__(self, ruta_salida: str = 'bodega_datos/3_visualizaciones'):
        self.ruta_salida = ruta_salida
        # Recuperamos la creación automática de tu directorio de salida
        os.makedirs(self.ruta_salida, exist_ok=True)
        
        # Configuración estética global
        sns.set_theme(style="whitegrid")
        plt.rcParams.update({
            'font.size': 11,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'figure.titlesize': 16
        })

    def graficar_boxplots(self, df: pd.DataFrame) -> None:
        """ 1. Boxplots: Detecta outliers en los montos de venta. """
        if df.empty or 'monto' not in df.columns:
            logging.warning("Visualización: Datos insuficientes para el Boxplot.")
            return

        logging.info("Visualización: Generando Boxplot de montos...")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Mantenemos el gráfico limpio para buscar anomalías financieras
        sns.boxplot(x=df['monto'], color='#3498db', ax=ax)
        
        ax.set_title('Detección de Valores Atípicos (Outliers) en Montos de Venta', pad=15)
        ax.set_xlabel('Monto de Venta (USD)')
        
        # Guardamos en la ruta correcta
        ruta_guardado = os.path.join(self.ruta_salida, 'boxplot_outliers.png')
        plt.tight_layout()
        plt.savefig(ruta_guardado, dpi=300)
        plt.close()
        logging.info(f"Visualización: Boxplot guardado en '{ruta_guardado}'.")

    def graficar_pca_scatter(self, df: pd.DataFrame) -> None:
        """ 2. Scatter Plot 3D: Visualización de clusters usando PC1, PC2 y PC3. """
        # Validamos que existan tus 3 componentes exactos
        if not all(col in df.columns for col in ['PC1', 'PC2', 'PC3']):
            logging.error("Visualización: Faltan las columnas PC1, PC2 o PC3")
            return

        logging.info("Visualización: Generando Scatter Plot 3D del PCA...")
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        segmentos = df['segmento_cliente'].dropna().unique()
        colores = sns.color_palette("viridis", len(segmentos))
        
        for segmento, color in zip(segmentos, colores):
            df_subset = df[df['segmento_cliente'] == segmento]
            ax.scatter(
                df_subset['PC1'], 
                df_subset['PC2'], 
                df_subset['PC3'], 
                color=color, 
                label=segmento,
                s=60, alpha=0.8
            )
            
        ax.set_title('Clusters de Comportamiento (Análisis PCA 3D)', pad=15)
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        
        ax.legend(title='Segmentos de Negocio', bbox_to_anchor=(1.1, 1), loc='upper left')
        
        # Guardamos en la ruta correcta
        ruta_guardado = os.path.join(self.ruta_salida, 'scatter_clusters_pca_3d.png')
        plt.tight_layout()
        plt.savefig(ruta_guardado, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Visualización: Gráfico PCA 3D guardado en '{ruta_guardado}'.")

    def graficar_sankey(self, df: pd.DataFrame = None) -> None:
        """ 3. Sankey Diagram: Flujo web (logs) hasta el segmento final de compra. """
        if not PLOTLY_DISPONIBLE:
            logging.warning("Visualización: Plotly no está instalado. Omitiendo diagrama Sankey.")
            return
            
        if df is None or df.empty:
            logging.warning("Visualización: No se encontraron datos para procesar el diagrama Sankey.")
            return

        logging.info("Visualización: Generando Diagrama de Sankey (Flujo de conversión)...")
        
        # Filtramos para usar la data de los logs web vs el segmento de cliente
        df_limpio = df.dropna(subset=['codigo_estado', 'segmento_cliente'])
        if df_limpio.empty:
             logging.warning("Visualización: Faltan datos de logs o segmentos para el Sankey.")
             return
             
        flujos = df_limpio.groupby(['codigo_estado', 'segmento_cliente']).size().reset_index(name='cantidad')
        
        flujos['codigo_estado'] = 'HTTP ' + flujos['codigo_estado'].astype(int).astype(str)
        flujos['segmento_cliente'] = flujos['segmento_cliente'].astype(str)
        
        nodos_origen = flujos['codigo_estado'].unique().tolist()
        nodos_destino = flujos['segmento_cliente'].unique().tolist()
        todos_los_nodos = nodos_origen + nodos_destino
        
        mapeo_nodos = {nodo: idx for idx, nodo in enumerate(todos_los_nodos)}
        
        fuente = flujos['codigo_estado'].map(mapeo_nodos).tolist()
        destino = flujos['segmento_cliente'].map(mapeo_nodos).tolist()
        valores = flujos['cantidad'].tolist()
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20, thickness=15,
                line=dict(color="gray", width=0.5),
                label=todos_los_nodos,
                color="#2ecc71"
            ),
            link=dict(
                source=fuente, target=destino, value=valores, color="rgba(46, 204, 113, 0.4)"
            )
        )])
        
        fig.update_layout(title_text="Flujo de Conversión: Desde Servidor Web hasta Segmentación", font_size=12)
        
        # Guardamos en la ruta correcta en formato HTML interactivo
        ruta_guardado = os.path.join(self.ruta_salida, 'sankey_flujo_web.html')
        pio.write_html(fig, file=ruta_guardado, auto_open=False)
        logging.info(f"Visualización: Diagrama Sankey guardado en '{ruta_guardado}'.")
        