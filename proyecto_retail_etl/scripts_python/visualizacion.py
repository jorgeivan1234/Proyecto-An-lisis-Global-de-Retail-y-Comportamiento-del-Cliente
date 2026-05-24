"""
Módulo: visualizacion.py
Descripción: Se encarga de la generación de gráficos estadísticos y paneles 
interactivos basados en los datos procesados por el pipeline ETL.
"""

# Importación de librerías para visualización y manejo de datos
import os                           # Para manejo de rutas y creación de directorios
import logging                      # Para el registro de eventos y errores
import pandas as pd                 # Para manejo de DataFrames, aunque se espera que los datos ya estén procesados
import matplotlib.pyplot as plt     # Para gráficos estáticos
import seaborn as sns               # Para gráficos estadísticos con estilo

# Intentamos importar Plotly para gráficos interactivos
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_DISPONIBLE = True
except ImportError:
    PLOTLY_DISPONIBLE = False

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Creamos la clase VisualizadorDashboard con métodos para cada tipo de gráfico que queremos generar
class VisualizadorDashboard:

    # Constructor que asegura la creación del directorio de salida y establece configuraciones estéticas globales
    def __init__(self, ruta_salida: str = 'bodega_datos/3_visualizaciones'):
        self.ruta_salida = ruta_salida
        # Recuperamos la creación automática de tu directorio de salida
        os.makedirs(self.ruta_salida, exist_ok=True)
        
        # Configuraciones estéticas globales para los gráficos
        sns.set_theme(style="whitegrid")
        plt.rcParams.update({
            'font.size': 11,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'figure.titlesize': 16
        })

    # Método para graficar boxplots
    def graficar_boxplots(self, df: pd.DataFrame) -> None:
        """ 1. Boxplots: Detecta outliers en los montos de venta con diseño explicativo. """
        if df.empty or 'monto_usd' not in df.columns:
            logging.warning("Visualización: Datos insuficientes para el Boxplot.")
            return

        # Diseño avanzado del boxplot con colores personalizados, líneas de referencia y anotaciones explicativas
        logging.info("Visualización: Generando Boxplot de montos con diseño avanzado...")
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # 1. Definición de colores
        color_caja = '#2ecc71'       # Verde amigable para la normalidad
        color_outlier = '#e74c3c'    # Rojo para llamar la atención sobre lo atípico
        
        # 2. Creación del gráfico con estilos específicos
        sns.boxplot(
            x=df['monto_usd'], 
            color=color_caja, 
            ax=ax,
            width=0.4,
            flierprops=dict(markerfacecolor=color_outlier, marker='o', markersize=8, alpha=0.6, markeredgecolor='none')
        )
        
        # 3. Cálculos estadísticos para las líneas de referencia
        mediana = df['monto_usd'].median()
        q1 = df['monto_usd'].quantile(0.25)
        q3 = df['monto_usd'].quantile(0.75)
        iqr = q3 - q1
        limite_sup = q3 + 1.5 * iqr
        
        # 4. Líneas y etiquetas de referencia visual
        # Línea de la Mediana
        ax.axvline(mediana, color='#2c3e50', linestyle='--', alpha=0.7)
        ax.text(mediana, -0.3, f'Mediana\n(USD ${mediana:,.2f})', horizontalalignment='center', color='#2c3e50', fontsize=10, weight='bold')
        
        # Línea del Límite de Outliers
        ax.axvline(limite_sup, color=color_outlier, linestyle=':', alpha=0.7)
        ax.text(limite_sup, -0.3, 'Límite de Outliers\n(Ventas Atípicas)', horizontalalignment='center', color=color_outlier, fontsize=10, weight='bold')
        
        # 5. Caja de texto explicativa anclada en la esquina superior izquierda
        texto_explicativo = (
            "¿CÓMO LEER ESTE GRÁFICO?\n"
            "• Caja Verde: Contiene el 50% central de todas las ventas (del Cuartil 1 al 3).\n"
            "• Línea Central punteada: Es la Mediana, el valor justo a la mitad de tus ventas.\n"
            "• Puntos Rojos (Outliers): Son ventas excepcionalmente altas que escapan\n"
            "  del comportamiento habitual. ¡Revisar posibles fraudes o ventas mayoristas!"
        )
        props_caja = dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', alpha=0.9, edgecolor='#bdc3c7')
        ax.text(0.02, 0.95, texto_explicativo, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props_caja, color='#2c3e50')

        # 6. Estética final: Títulos y limpieza de bordes
        ax.set_title('Distribución y Detección de Valores Atípicos en Montos de Venta', pad=20, fontsize=16, weight='bold')
        ax.set_xlabel('Monto de Venta (USD)', fontsize=12, labelpad=10)
        ax.set_yticks([]) # Ocultamos el eje Y porque en un boxplot horizontal no aporta información
        sns.despine(left=True) # Quitamos el borde izquierdo para un look más limpio

        # Guardado
        ruta_guardado = os.path.join(self.ruta_salida, 'boxplot_outliers.png')
        plt.tight_layout()
        plt.savefig(ruta_guardado, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Visualización: Boxplot mejorado guardado en '{ruta_guardado}'.")
        
    # Método para graficar un scatter plot 3D basado en PCA
    def graficar_pca_scatter(self, df: pd.DataFrame) -> None:
        
        # Verificación de columnas necesarias para el PCA 3D
        if not all(col in df.columns for col in ['PC1', 'PC2', 'PC3']):
            logging.error("Visualización: Faltan las columnas PC1, PC2 o PC3")
            return
        
        # Verificación de la columna de segmento para el color
        if 'segmento_cliente' not in df.columns:
            logging.error("Visualización: Falta la columna 'segmento_cliente' para agrupar.")
            return

        logging.info("Visualización: Generando Scatter Plot 3D del PCA...")
        
        # Configuración de la figura y el eje 3D
        fig = plt.figure(figsize=(15, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.view_init(elev=20, azim=135) 
        
        # Paleta de colores altamente contrastante con los nombres originales del ETL
        mapa_colores = {
            'Premium Joven': '#e74c3c',       # Rojo (Llamativo, destaca la juventud)
            'Premium Adulto': '#2980b9',      # Azul (Serio, destaca la madurez)
            'Estándar': '#2ecc71',            # Verde (Listo por si cambian los datos a futuro)
            'No Identificado': '#95a5a6'      # Gris
        }
        
        # Agrupamos por segmento y graficamos cada grupo con su color asignado
        segmentos_presentes = df['segmento_cliente'].dropna().unique()
        for segmento in segmentos_presentes:
            df_subset = df[df['segmento_cliente'] == segmento]
            color_segmento = mapa_colores.get(segmento, '#34495e') 
            
            ax.scatter(
                df_subset['PC1'], 
                df_subset['PC2'], 
                df_subset['PC3'], 
                color=color_segmento, 
                label=segmento,
                s=70,           
                alpha=0.8,      
                edgecolors='white', 
                linewidth=0.5
            )

        # Guía de Dirección (Esquina superior derecha)
        texto_guia = (
            "GUÍA DE DIRECCIÓN (Tendencias):\n"
            "→ Derecha (PC1 ↑): Mayor Ingreso y Gasto\n"
            "↑ Arriba (PC2 ↑): Mayor Edad / Antigüedad\n"
            "-> Profundidad (PC3 ↑): Mayor Fidelidad"
        )
        props_guia = dict(boxstyle='round,pad=0.5', facecolor='#ffffff', alpha=0.9, edgecolor='#bdc3c7')
        ax.text2D(0.98, 0.95, texto_guia, transform=ax.transAxes, fontsize=10, 
                  verticalalignment='top', horizontalalignment='right', bbox=props_guia, color='#34495e')

        # Caja explicativa del PCA (Esquina superior izquierda)
        texto_pca = (
            "¿CÓMO ENTENDER ESTE MAPA MATEMÁTICO?\n"
            "El PCA condensa múltiples variables (ingresos, gasto, edad, lealtad)\n"
            "en solo 3 ejes principales. ¡Es el ADN de tus clientes en 3D!\n\n"
            "• Cercanía: Clientes con perfiles y comportamientos muy parecidos.\n"
            "• Distancia: Clientes con hábitos de compra totalmente diferentes."
        )
        props_caja = dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', alpha=0.9, edgecolor='#bdc3c7')
        ax.text2D(-0.05, 1.02, texto_pca, transform=ax.transAxes, fontsize=10, 
                  verticalalignment='top', bbox=props_caja, color='#2c3e50')

        # Caja de leyenda (Esquina inferior derecha)
        ax.set_title('ADN del Cliente: Mapa Matemático de Clusters de Comportamiento (PCA 3D)', pad=45, fontsize=16, weight='bold')
        ax.set_xlabel('Volumen Financiero (PC1)', labelpad=10)
        ax.set_ylabel('Demografía/Edad (PC2)', labelpad=10)
        ax.set_zlabel('Fidelidad (PC3)', labelpad=10)
        ax.grid(True, linestyle='--', alpha=0.5)

        ax.legend(title='Segmentos de Negocio', bbox_to_anchor=(1.05, 0.0), loc='lower right', fontsize=10, title_fontsize=11)
        
        # Guardado del gráfico con alta resolución y diseño ajustado
        ruta_guardado = os.path.join(self.ruta_salida, 'scatter_clusters_pca_3d.png')
        plt.savefig(ruta_guardado, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Visualización: Gráfico PCA 3D final guardado en '{ruta_guardado}'.")
    
    # Método para graficar un diagrama de Sankey basado en los logs y segmentos finales
    def graficar_sankey(self, df: pd.DataFrame = None) -> None:
        
        # Verificación de disponibilidad de Plotly para gráficos interactivos
        if not PLOTLY_DISPONIBLE:
            logging.warning("Visualización: Plotly no está instalado. Omitiendo diagrama Sankey.")
            return
        
        # Verificación de columnas necesarias para el Sankey
        if df is None or df.empty:
            logging.warning("Visualización: No se encontraron datos para procesar el diagrama Sankey.")
            return

        logging.info("Visualización: Generando Diagrama de Sankey interactivo...")
        
        # Filtramos nulos
        df_limpio = df.dropna(subset=['codigo_estado', 'segmento_cliente']).copy()
        if df_limpio.empty:
             logging.warning("Visualización: Faltan datos de logs o segmentos para el Sankey.")
             return
             
        # Preparación de datos para el Sankey: Mapeamos códigos HTTP a categorías legibles y segmentamos por cliente
        mapeo_http = {
            200: 'HTTP 200 (Éxito)',
            404: 'HTTP 404 (No Encontrado)',
            500: 'HTTP 500 (Error Servidor)'
        }
        # Aplicamos el mapeo; si hay un código raro, lo deja como 'HTTP XXX'
        df_limpio['origen'] = df_limpio['codigo_estado'].astype(int).map(mapeo_http).fillna('HTTP ' + df_limpio['codigo_estado'].astype(int).astype(str))
        df_limpio['destino'] = df_limpio['segmento_cliente'].astype(str)
        
        # Calculamos el tamaño de los flujos
        flujos = df_limpio.groupby(['origen', 'destino']).size().reset_index(name='cantidad')
        
        # Definimos los nodos (cajas)
        nodos_origen = flujos['origen'].unique().tolist()
        nodos_destino = flujos['destino'].unique().tolist()
        todos_los_nodos = nodos_origen + nodos_destino
        
        # Mapeamos los nodos a índices para Plotly
        mapeo_nodos = {nodo: idx for idx, nodo in enumerate(todos_los_nodos)}
        
        # Preparamos las listas de fuente, destino y valores para el diagrama Sankey
        fuente = flujos['origen'].map(mapeo_nodos).tolist()
        destino = flujos['destino'].map(mapeo_nodos).tolist()
        valores = flujos['cantidad'].tolist()
        
        # Consistencia de colores
        paleta_segmentos = {
            'Premium Joven': '#e74c3c',       # Rojo
            'Premium Adulto': '#2980b9',      # Azul
            'Estándar': '#2ecc71'             # Verde
        }
        
        # Asignamos color a las cajas (Nodos)
        colores_nodos = []
        for nodo in todos_los_nodos:
            if nodo in paleta_segmentos:
                colores_nodos.append(paleta_segmentos[nodo])
            elif '200' in nodo:
                colores_nodos.append('#27ae60') # Verde oscuro para éxito web
            elif '404' in nodo or '500' in nodo:
                colores_nodos.append('#c0392b') # Rojo oscuro para errores web
            else:
                colores_nodos.append('#95a5a6') # Gris por defecto
                
        # Asignamos color a los flujos (Enlaces) basándonos en el color del destino
        colores_enlaces = []
        for dest in flujos['destino']:
            hex_color = paleta_segmentos.get(dest, '#bdc3c7')
            # Convertimos el color HEX a RGBA para darle transparencia en Plotly
            h = hex_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            colores_enlaces.append(f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.4)')
        
        # Creación del gráfico en Plotly
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=25, thickness=20,
                line=dict(color="white", width=0.5),
                label=todos_los_nodos,
                color=colores_nodos,
                hovertemplate='%{label}: %{value} usuarios<extra></extra>'
            ),
            link=dict(
                source=fuente, target=destino, value=valores, 
                color=colores_enlaces,
                hovertemplate='De %{source.label} hacia %{target.label}<br>Volumen: %{value} usuarios<extra></extra>'
            )
        )])
        
        # Textos Explicativos (Storytelling con anotaciones web)
        texto_explicativo = (
            "<b>¿CÓMO LEER ESTE DIAGRAMA?</b><br>"
            "• <b>Grosor de las líneas:</b> Representa el volumen (cantidad) de usuarios interactuando.<br>"
            "• <b>Lado Izquierdo (Origen):</b> Indica la experiencia técnica del usuario en la web.<br>"
            "• <b>Lado Derecho (Destino):</b> Muestra la conversión final por segmento de negocio.<br>"
            "<i>(Tip: Pon el cursor del mouse sobre las líneas para ver los detalles exactos).</i>"
        )
        
        # Configuración del diseño del gráfico con un título claro, márgenes adecuados y una caja de texto explicativa anclada en la parte inferior para guiar al usuario en la interpretación del diagrama
        fig.update_layout(
            title_text="<b>Embudo de Conversión: Desde Servidor Web hasta Segmentación</b>",
            title_font_size=20,
            font_size=13,
            margin=dict(t=80, b=120, l=40, r=40), # Más margen inferior para el texto
            annotations=[
                dict(
                    x=0.5, y=-0.25, # Posicionado en la parte inferior, centrado
                    xref='paper', yref='paper',
                    text=texto_explicativo,
                    showarrow=False,
                    align='center',
                    bgcolor='#f8f9fa',
                    bordercolor='#bdc3c7',
                    borderwidth=1,
                    borderpad=10,
                    font=dict(size=12, color='#2c3e50')
                )
            ]
        )
        
        # Guardado del HTML
        ruta_guardado = os.path.join(self.ruta_salida, 'sankey_flujo_web.html')
        pio.write_html(fig, file=ruta_guardado, auto_open=False)
        logging.info(f"Visualización: Diagrama Sankey interactivo guardado en '{ruta_guardado}'.")