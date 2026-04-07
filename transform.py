# fase de transformación: limpieza, enriquecimiento y analisis avanzado (PCA).

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
import logging

# Configuración de logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataTransformer:
    
    """ Clase central para la limpieza, enriquecimiento y análisis avanzado de datos.
    Aplica transformaciones de Pandas, reglas de negocio y algoritmos de Machine Learning (PCA). """

    def limpiar_datos(self, df_ventas: pd.DataFrame, df_inventario: pd.DataFrame) -> tuple:
        
        """ Limpia duplicados y nulos, y normaliza strings y fechas. """
        
        logging.info("Iniciando fase de limpieza de datos...")
        
        # Limpieza de SQL (Ventas): Eliminando duplicados basados en id_transaccion.
        ventas_limpias = df_ventas.drop_duplicates(subset=['id_transaccion']).copy()
        
        # Normalización de fechas a datetime64.
        ventas_limpias['fecha'] = pd.to_datetime(ventas_limpias['fecha'], errors='coerce')
        
        # 2. Limpieza de CSV (Inventario): Detectar y tratar nulos.
        inventario_limpio = df_inventario.drop_duplicates().copy()
        # Rellenamos el stock nulo con 0 y el precio_unitario con la mediana.
        inventario_limpio['stock'] = inventario_limpio['stock'].fillna(0)
        inventario_limpio['precio_unitario'] = inventario_limpio['precio_unitario'].fillna(
            inventario_limpio['precio_unitario'].median()
        )
        
        # Normalización de texto sucio (ej: "México", "mex", "mx").
        if 'categoria' in inventario_limpio.columns:
            inventario_limpio['categoria'] = (
                inventario_limpio['categoria']
                .str.lower()
                .str.strip()
                .replace({'mex': 'méxico', 'mx': 'méxico'})
            )
            
        logging.info("Limpieza completada. Fechas convertidas a datetime64.")
        return ventas_limpias, inventario_limpio

    def enriquecer_datos(self, df_ventas: pd.DataFrame, df_perfiles: pd.DataFrame) -> pd.DataFrame:
        
        """ Realiza un Left Join entre las ventas y los perfiles de usuario. """
        
        logging.info("Realizando Left Join entre Ventas y Perfiles...")
        # nos aseguramos de que la llave de cruce tenga el mismo nombre en ambos DataFrames.
        if 'id_cliente' in df_perfiles.columns:
            df_master = pd.merge(df_ventas, df_perfiles, on='id_cliente', how='left')
        else:
            df_master = pd.merge(df_ventas, df_perfiles, left_on='id_cliente', right_on='Customer_ID', how='left')
            
        logging.info(f"Join completado. El DataFrame maestro tiene {len(df_master)} registros.")
        return df_master

    def aplicar_reglas_negocio(self, df_master: pd.DataFrame) -> pd.DataFrame:
        
        """ Crea la columna segmento_cliente utilizando np.where. """
        
        logging.info("Aplicando reglas de negocio complejas con np.where...")
        
        # Si la edad no existe (nula por el left join), le ponemos un valor por defecto temporal.
        df_master['edad_temp'] = df_master.get('edad', 35).fillna(35) 
        
        # Regla: Si gasto > 1000 y edad < 30 -> "Premium Joven", sino "Regular".
        condicion_premium = (df_master['monto'] > 1000) & (df_master['edad_temp'] < 30)
        
        df_master['segmento_cliente'] = np.where(condicion_premium, "Premium Joven", "Regular")
        # Limpieza final: eliminamos la columna temporal de edad.
        df_master.drop(columns=['edad_temp'], inplace=True) 
        
        logging.info("Segmentación de clientes aplicada exitosamente.")
        return df_master

    def ejecutar_pca(self, df_master: pd.DataFrame) -> tuple:
        
        """ Aplica Análisis de Componentes Principales (PCA) sobre las features numéricas. """
        
        logging.info("Iniciando Análisis Avanzado (PCA)...")
        
        # Seleccionar variables numéricas (simulamos que hay 20 columnas numéricas de comportamiento).
        # En la práctica, tomamos todas las columnas que sean float o int.
        cols_numericas = df_master.select_dtypes(include=[np.number]).columns.tolist()
        
        # Quitamos IDs y Fechas de las variables para el PCA.
        cols_ignoradas = ['id_transaccion', 'id_cliente', 'id_tienda', 'Customer_ID']
        features = [c for c in cols_numericas if c not in cols_ignoradas]
        # El PCA no soporta nulos, así que los rellenamos con 0 o mediana según corresponda.
        df_features = df_master[features].fillna(0) 
        
        # 2. Normalización Min-Max (Requisito clave para no sesgar el modelo).
        scaler = MinMaxScaler()
        datos_escalados = scaler.fit_transform(df_features)
        # se redujeron a 3 features para facilitar la visualizacion y la interpretación.
        # Si tienes menos de 3 features numéricas en las pruebas, el PCA tomará el máximo posible.
        n_components = min(3, len(features)) 
        pca = PCA(n_components=n_components)
        componentes = pca.fit_transform(datos_escalados)
        
        # Calculamos cuánta varianza explican estos 3 componentes.
        varianza_explicada = pca.explained_variance_ratio_
        varianza_total = sum(varianza_explicada) * 100
        
        logging.info(f"PCA completado. Se redujeron {len(features)} dimensiones a {n_components}.")
        logging.info(f"Varianza explicada por componente: {varianza_explicada}")
        logging.info(f"Los componentes capturan el {varianza_total:.2f}% de la varianza total.")
        
        # Añadimos los componentes al DataFrame Maestro para graficarlos luego.
        for i in range(n_components):
            df_master[f'PC{i+1}'] = componentes[:, i]
            
        return df_master, pca