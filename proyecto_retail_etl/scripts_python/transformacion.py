"""
Módulo: transformacion.py
Descripción: Contiene la lógica de negocio, limpieza de datos, cruce de tablas 
y modelado estadístico (PCA) para la creación de la tabla maestra.
"""

import logging
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Tuple

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TransformadorDatos:
    """ 
    Clase encargada de la calidad, enriquecimiento y transformación analítica de los datos. 
    """

    def limpiar_datos(self, df_ventas: pd.DataFrame, df_inventario: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Realiza la limpieza inicial de los datos eliminando duplicados y gestionando nulos.
        """
        logging.info("Transformación: Iniciando limpieza de datos...")
        
        # Limpieza en ventas
        df_ventas_limpias = df_ventas.drop_duplicates().copy()
        df_ventas_limpias['monto'] = df_ventas_limpias['monto'].fillna(0)
        
        # Limpieza en inventario
        df_inventario_limpio = df_inventario.drop_duplicates().copy()
        df_inventario_limpio['stock_actual'] = df_inventario_limpio['stock_actual'].fillna(0)
        
        logging.info("Transformación: Limpieza inicial completada con éxito.")
        return df_ventas_limpias, df_inventario_limpio

    def enriquecer_datos(self, df_ventas: pd.DataFrame, df_perfiles: pd.DataFrame, df_inventario: pd.DataFrame, df_competencia: pd.DataFrame = None, df_catalogos: pd.DataFrame = None, df_metas: pd.DataFrame = None, df_logs: pd.DataFrame = None) -> pd.DataFrame:
        """
        Realiza un cruce triple (Merge) para consolidar las ventas con los 
        perfiles de los clientes y el catálogo de productos.
        """
        logging.info("Transformación: Realizando cruce de información (Ventas + Perfiles + Inventario)...")
        
        if df_ventas.empty:
            logging.warning("El DataFrame de ventas está vacío. No se puede enriquecer.")
            return pd.DataFrame()

        # 1. Cruzar Ventas con Inventario mediante el id_producto
        df_consolidado = pd.merge(df_ventas, df_inventario, on='id_producto', how='left')
        
        # 2. Cruzar el resultado con Perfiles de Cliente mediante el id_cliente
        df_maestro = pd.merge(df_consolidado, df_perfiles, on='id_cliente', how='left')
        
        # 3. NUEVO: Cruzar con Precios de la Competencia mediante el nombre del producto
        if df_competencia is not None and not df_competencia.empty:
            # Usamos left_on y right_on porque las columnas se llaman distinto
            df_maestro = pd.merge(df_maestro, df_competencia, left_on='nombre_producto', right_on='producto', how='left')
        
        # Cruce con Catálogos (XML) 
        if df_catalogos is not None and not df_catalogos.empty:
            df_maestro = pd.merge(df_maestro, df_catalogos, left_on='categoria', right_on='nombre', how='left')
        
        if df_metas is not None and not df_metas.empty:
            df_maestro = pd.merge(df_maestro, df_metas, on='ciudad', how='left')
        
        if df_logs is not None and not df_logs.empty:
            logging.info("Transformación: Homologando y acoplando logs del servidor...")
            
            # 1. Forzamos a que los IDs sean enteros en ambas tablas para evitar conflictos de tipo de datos
            df_logs['id_producto'] = pd.to_numeric(df_logs['id_producto'], errors='coerce').fillna(0).astype(int)
            df_logs['id_cliente'] = pd.to_numeric(df_logs['id_cliente'], errors='coerce').fillna(0).astype(int)
            
            df_maestro['id_producto'] = pd.to_numeric(df_maestro['id_producto'], errors='coerce').fillna(0).astype(int)
            df_maestro['id_cliente'] = pd.to_numeric(df_maestro['id_cliente'], errors='coerce').fillna(0).astype(int)
            
            # 2. Agrupamos los logs por cliente y producto para consolidar las visitas múltiples
            df_logs_agrupados = df_logs.groupby(['id_producto', 'id_cliente']).agg({
                'codigo_estado': 'last',              # Nos quedamos con el último estado HTTP reportado
                'tiempo_respuesta_ms': 'mean'         # Calculamos el tiempo promedio de respuesta web
            }).reset_index()
            
            # 3. Realizamos el cruce seguro
            df_maestro = pd.merge(df_maestro, df_logs_agrupados, on=['id_producto', 'id_cliente'], how='left')
        else:
            logging.warning("Advertencia: El DataFrame de logs llegó vacío. Creando columnas con valores supletorios.")
            df_maestro['codigo_estado'] = 200
            df_maestro['tiempo_respuesta_ms'] = 200  # Valor promedio por defecto en ms
            
        # 4. Rellenamos posibles nulos (por si alguna venta no tuvo un registro en el log web)
        df_maestro['codigo_estado'] = df_maestro['codigo_estado'].fillna(200).astype(int)
        df_maestro['tiempo_respuesta_ms'] = df_maestro['tiempo_respuesta_ms'].fillna(150).astype(int)

        df_maestro['segmento_cliente'] = np.where(
            (df_maestro['monto'] > 1000) & (df_maestro['edad'] < 30), 
            'Premium Joven', 
            'Estándar'
        )
        
        logging.info(f"Transformación: Cruce completado. Matriz resultante de {df_maestro.shape[0]} filas.")
        return df_maestro

    def aplicar_reglas_negocio(self, df_maestro: pd.DataFrame, tasa_usd: float = 1.0) -> pd.DataFrame:
        """
        Aplica lógica de negocio y usa la API externa para conversión de divisas.
        """
        logging.info("Transformación: Calculando métricas y convirtiendo divisas...")
        df_resultado = df_maestro.copy()
        
        # Gestión de nulos por si algún cliente o producto no se cruzó correctamente
        df_resultado['edad'] = df_resultado['edad'].fillna(df_resultado['edad'].mean())
        df_resultado['nivel_fidelidad'] = df_resultado['nivel_fidelidad'].fillna('Sin Registro')
        df_resultado['categoria'] = df_resultado['categoria'].fillna('Otros')
        
        # Regla 1: Segmentación demográfica por rangos de edad
        condiciones_edad = [
            (df_resultado['edad'] < 30),
            (df_resultado['edad'] >= 30) & (df_resultado['edad'] <= 50),
            (df_resultado['edad'] > 50)
        ]
        segmentos_edad = ['Joven', 'Adulto', 'Senior']
        df_resultado['segmento_edad'] = np.select(condiciones_edad, segmentos_edad, default='No Identificado')
        
        # Regla 2: Clasificación de transacciones según el volumen del monto
        df_resultado['ticket_alto'] = np.where(df_resultado['monto'] > df_resultado['precio_unitario'] * 1.5, 1, 0)
        
        # Regla 3: Mapeo numérico de la fidelidad para uso en algoritmos matemáticos
        mapeo_fidelidad = {'Bronce': 1, 'Plata': 2, 'Oro': 3, 'Platino': 4, 'Sin Registro': 0}
        df_resultado['codigo_fidelidad'] = df_resultado['nivel_fidelidad'].map(mapeo_fidelidad)
        
        # Regla 4: Conversión de montos a USD usando la tasa proporcionada (simulando una API externa)
        df_resultado['monto_usd'] = (df_resultado['monto'] * tasa_usd).round(2)
        df_resultado['precio_unitario_usd'] = (df_resultado['precio_unitario'] * tasa_usd).round(2)
        
        logging.info("Transformación: Reglas de negocio y conversión de divisas aplicadas.")
        return df_resultado

    def ejecutar_pca(self, df_maestro: pd.DataFrame) -> Tuple[pd.DataFrame, PCA]:
        """
        Prepara las variables numéricas, las estandariza y ejecuta el algoritmo 
        de Análisis de Componentes Principales (PCA) para reducción de dimensionalidad.
        """
        logging.info("Transformación: Preparando variables numéricas para el algoritmo PCA...")
        df_analisis = df_maestro.copy()
        
        # Seleccionamos las columnas numéricas clave que tienen sentido correlacionar
        columnas_numericas = ['monto', 'precio_unitario', 'stock_actual', 'edad', 'codigo_fidelidad', 'ticket_alto']
        
        # Extraemos la matriz de características y eliminamos cualquier nulo remanente
        x_datos = df_analisis[columnas_numericas].dropna()
        
        if x_datos.shape[0] < 2:
            logging.warning("Datos insuficientes para ejecutar PCA. Se omitirá el paso estadístico.")
            df_analisis['PC1'] = 0.0
            df_analisis['PC2'] = 0.0
            return df_analisis, None

        # Estandarizamos los datos (Media = 0, Varianza = 1) para que ninguna variable domine por su escala
        escalador = StandardScaler()
        x_escalado = escalador.fit_transform(x_datos)
        
        # Inicializamos y entrenamos PCA para obtener los 3 componentes principales más importantes
        pca = PCA(n_components=3, random_state=42)
        componentes = pca.fit_transform(x_escalado)
        
        # Asignamos los componentes de vuelta al DataFrame original sincronizando los índices
        df_analisis.loc[x_datos.index, 'PC1'] = componentes[:, 0]
        df_analisis.loc[x_datos.index, 'PC2'] = componentes[:, 1]
        df_analisis.loc[x_datos.index, 'PC3'] = componentes[:, 2]
        
        #Limitamos los decimales para facilitar la interpretación y visualización
        df_analisis['PC1'] = df_analisis['PC1'].round(4)
        df_analisis['PC2'] = df_analisis['PC2'].round(4)
        df_analisis['PC3'] = df_analisis['PC3'].round(4)
        
        varianza_explicada = round(np.sum(pca.explained_variance_ratio_) * 100, 2)
        logging.info(f"Transformación: PCA completado con éxito. Varianza explicada: {varianza_explicada}%")
        
        return df_analisis, pca