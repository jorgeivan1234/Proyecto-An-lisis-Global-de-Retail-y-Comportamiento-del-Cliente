#

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class VisualizadorDashboard:
    """Clase encargada de generar los gráficos avanzados para el reporte final."""
    
    def __init__(self):
        # Configuramos el estilo visual de Seaborn para que luzca profesional
        sns.set_theme(style="whitegrid", palette="muted")

    def graficar_boxplots(self, df_master: pd.DataFrame):
        """Genera un Boxplot para detectar outliers en los montos de venta."""
        logging.info("Generando Boxplot de ventas...")
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='segmento_cliente', y='monto', data=df_master)
        plt.title('Distribución de Montos de Venta por Segmento de Cliente (Detección de Outliers)')
        plt.xlabel('Segmento')
        plt.ylabel('Monto ($)')
        plt.tight_layout()
        plt.savefig('boxplot_outliers.png') # Guardamos el gráfico como imagen
        plt.close()

    def graficar_pca_scatter(self, df_master: pd.DataFrame):
        """Visualiza los clusters generados por el PCA en un Scatter Plot 2D."""
        logging.info("Generando Scatter Plot de los Componentes Principales...")
        plt.figure(figsize=(10, 6))
        # Graficamos el Componente 1 vs Componente 2
        sns.scatterplot(
            x='PC1', y='PC2', 
            hue='segmento_cliente', # Coloreamos por el segmento de negocio
            data=df_master, 
            alpha=0.7
        )
        plt.title('Clusters de Comportamiento (PCA: PC1 vs PC2)')
        plt.xlabel('Componente Principal 1')
        plt.ylabel('Componente Principal 2')
        plt.legend(title='Segmento')
        plt.tight_layout()
        plt.savefig('scatter_pca.png')
        plt.close()

    def graficar_sankey(self):
        """
        Genera un diagrama de Sankey para mostrar el embudo de conversión.
        Nota: Para este ejemplo, simulamos los nodos basados en los logs del servidor.
        """
        logging.info("Generando Diagrama de Sankey interactivo/estático...")
        
        # Nodos: 0: Inicio Web, 1: Catálogo, 2: Carrito, 3: Compra Exitosa, 4: Abandono
        labels = ["Inicio Web", "Catálogo", "Carrito", "Compra Exitosa", "Abandono"]
        
        # Flujos: Origen (source) -> Destino (target) con un Valor (value)
        origenes =  [0, 0, 1, 1, 2, 2]
        destinos =  [1, 4, 2, 4, 3, 4]
        valores =   [2000, 500, 1200, 800, 900, 300] # Simulando cantidades de usuarios
        
        fig = go.Figure(data=[go.Sankey(
            node = dict(
              pad = 15, thickness = 20,
              line = dict(color = "black", width = 0.5),
              label = labels
            ),
            link = dict(
              source = origenes, target = destinos, value = valores
            ))])
        
        fig.update_layout(title_text="Flujo de Usuarios (Embudo de Conversión desde Logs)", font_size=12)
        # Lo guardamos como HTML estático
        fig.write_html("sankey_diagram.html")