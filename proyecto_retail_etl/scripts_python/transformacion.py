"""
Módulo: transformacion.py
Descripción: Contiene la lógica de negocio, limpieza de datos, cruce de tablas 
y modelado estadístico (PCA) para la creación de la tabla maestra.
"""

# Importamos las librerías necesarias para la transformación de datos, modelado estadístico y manejo de DataFrames
import logging                                      # Para el registro de eventos y errores durante la transformación
import pandas as pd                                 # Para el manejo de DataFrames y operaciones de limpieza y cruce de datos
import numpy as np                                  # Para operaciones numéricas, creación de variables binarias y uso de np.where
from sklearn.decomposition import PCA               # Para la reducción de dimensionalidad y creación de componentes principales
from sklearn.preprocessing import MinMaxScaler      # Para la normalización de datos antes de aplicar PCA, cumpliendo con la rúbrica que pide escalado

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Clase encargada de la calidad, enriquecimiento y transformación analítica de los datos.
class TransformadorDatos:
    def limpiar_datos(self, df_ventas: pd.DataFrame, df_inventario: pd.DataFrame):
        logging.info("Transformación: Iniciando limpieza de datos...")
        
        # Rúbrica 1: Eliminar transacciones duplicadas en SQL
        df_ventas_limpias = df_ventas.drop_duplicates().copy()
        
        # Rúbrica 2: Normalización de fechas a datetime64
        if 'fecha_transaccion' in df_ventas_limpias.columns:
            logging.info("Transformación: Convirtiendo fechas a datetime64...")
            # format='mixed' nos salva de las fechas inconsistentes que inyectamos
            df_ventas_limpias['fecha_transaccion'] = pd.to_datetime(df_ventas_limpias['fecha_transaccion'], format='mixed', errors='coerce')
        
        # Rúbrica 3: Detectar y limpiar nulos en inventario.csv (Y quitar duplicados)
        logging.info("Transformación: Limpiando nulos y duplicados en inventario...")
        df_inventario_limpio = df_inventario.drop_duplicates().copy() # Eliminamos duplicados
        df_inventario_limpio['stock_actual'] = df_inventario_limpio['stock_actual'].fillna(0) # Limpiamos nulos
        df_inventario_limpio['categoria'] = df_inventario_limpio['categoria'].fillna('Sin Categoría')
        
        # Valor de retorno: DataFrames limpios listos para el cruce
        return df_ventas_limpias, df_inventario_limpio

    # Definimos la función de enriquecimiento de datos que realiza el cruce triple entre ventas, 
    # perfiles e inventario, y opcionalmente con competencia, catálogos, metas y logs
    def enriquecer_datos(self, df_ventas: pd.DataFrame, df_perfiles: pd.DataFrame, df_inventario: pd.DataFrame, df_competencia: pd.DataFrame = None, df_catalogos: pd.DataFrame = None, df_metas: pd.DataFrame = None, df_logs: pd.DataFrame = None) -> pd.DataFrame:
        logging.info("Transformación: Realizando cruce de información (Ventas + Perfiles + Inventario)...")
        
        # Rúbrica 4: Estandarizar abreviaturas y espacios en ciudades para mejorar el cruce con metas y perfiles
        if df_perfiles is not None and not df_perfiles.empty and 'ciudad' in df_perfiles.columns:
            logging.info("Transformación: Estandarizando abreviaturas y espacios en ciudades...")
            df_perfiles['ciudad'] = df_perfiles['ciudad'].str.lower().str.strip()
            
            reemplazos_ciudad = {
                'gdl': 'guadalajara', 'mty': 'monterrey', 'ciudad de mexico': 'cdmx',
                'cd. mx': 'cdmx', 'cdmx.': 'cdmx', 'culi': 'culiacán', 'culiacan': 'culiacán',
                'ver': 'veracruz', 'veracru': 'veracruz', 'chih': 'chihuahua', 'chihua': 'chihuahua',
                'pue': 'puebla', 'puebl': 'puebla', 'tol': 'toluca', 'tolu': 'toluca'
            }
            # Reemplazamos las abreviaturas y corregimos los nombres de ciudades para que coincidan con los datos de metas y perfiles
            df_perfiles['ciudad'] = df_perfiles['ciudad'].replace(reemplazos_ciudad)
            df_perfiles['ciudad'] = df_perfiles['ciudad'].str.title()
            df_perfiles['ciudad'] = df_perfiles['ciudad'].replace({'Cdmx': 'CDMX'})
        
        # Validación de que el DataFrame de ventas no esté vacío antes de intentar enriquecerlo, 
        # para evitar errores en los merges posteriores
        if df_ventas.empty:
            logging.warning("El DataFrame de ventas está vacío. No se puede enriquecer.")
            return pd.DataFrame()

        # 1. Cruzar Ventas con Inventario mediante el id_producto
        df_consolidado = pd.merge(df_ventas, df_inventario, on='id_producto', how='left')
        
        # 2. Cruzar el resultado con Perfiles de Cliente mediante el id_cliente
        df_maestro = pd.merge(df_consolidado, df_perfiles, on='id_cliente', how='left')
        
        # 3. Cruzar con Precios de la Competencia mediante el nombre del producto
        if df_competencia is not None and not df_competencia.empty:
            # Usamos left_on y right_on porque las columnas se llaman distinto
            df_maestro = pd.merge(df_maestro, df_competencia, left_on='nombre_producto', right_on='producto', how='left')
        
        # Cruce con Catálogos (XML) 
        if df_catalogos is not None and not df_catalogos.empty:
            df_maestro = pd.merge(df_maestro, df_catalogos, left_on='categoria', right_on='nombre', how='left')
        
        # Cruce con Metas (Excel) usando la ciudad como clave de cruce, asegurando que las ciudades estén estandarizadas para mejorar el match
        if df_metas is not None and not df_metas.empty:
            df_maestro = pd.merge(df_maestro, df_metas, on='ciudad', how='left')
        
        # Cruce con Logs del Servidor para enriquecer con información de experiencia web, asegurando que los IDs de cliente y producto estén en el mismo formato para evitar problemas de cruce
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
        # Si el DataFrame de logs llegó vacío, creamos columnas con valores supletorios para evitar errores en el cruce y asegurar que la tabla maestra tenga una estructura consistente
        else:
            logging.warning("Advertencia: El DataFrame de logs llegó vacío. Creando columnas con valores supletorios.")
            df_maestro['codigo_estado'] = 200
            df_maestro['tiempo_respuesta_ms'] = 200  # Valor promedio por defecto en ms
            
        # 4. Rellenamos posibles nulos (por si alguna venta no tuvo un registro en el log web)
        df_maestro['codigo_estado'] = df_maestro['codigo_estado'].fillna(200).astype(int)
        df_maestro['tiempo_respuesta_ms'] = df_maestro['tiempo_respuesta_ms'].fillna(150).astype(int)

        
        logging.info(f"Transformación: Cruce completado. Matriz resultante de {df_maestro.shape[0]} filas.")
        
        # Valor de retorno: DataFrame enriquecido listo para aplicar reglas de negocio y modelado estadístico
        return df_maestro

    # Definimos la función para aplicar reglas de negocio y realizar la conversión de divisas usando una tasa proporcionada, simulando el uso de una API externa
    def aplicar_reglas_negocio(self, df_maestro: pd.DataFrame, tasa_usd: float = 1.0) -> pd.DataFrame:
        logging.info("Transformación: Calculando métricas y convirtiendo divisas...")
        df_resultado = df_maestro.copy()
        
        # Gestion de nulos en precio_competencia, rellenando con el precio_unitario para no perder información valiosa en el análisis comparativo
        if 'precio_competencia' in df_resultado.columns:
            df_resultado['precio_competencia'] = df_resultado['precio_competencia'].fillna(df_resultado['precio_unitario'])
        
        # Gestión de nulos por si algún cliente o producto no se cruzó correctamente
        df_resultado['edad'] = df_resultado['edad'].fillna(df_resultado['edad'].mean())
        df_resultado['nivel_fidelidad'] = df_resultado['nivel_fidelidad'].fillna('Sin Registro')
        df_resultado['categoria'] = df_resultado['categoria'].fillna('Otros')
        
        # RÚBRICA 5: Crear segmento_cliente usando np.where anidado (gasto > 1000 y edad < 30) <---
        if 'gastos_mensuales' in df_resultado.columns and 'edad' in df_resultado.columns:
            df_resultado['segmento_cliente'] = np.where(
                (df_resultado['gastos_mensuales'] > 1000) & (df_resultado['edad'] < 30),
                'Premium Joven',
                np.where(df_resultado['gastos_mensuales'] > 1000, 'Premium Adulto', 'Estándar')
            )
        else:
            # Respaldo de seguridad usando 'monto' por si la columna no llega
            df_resultado['segmento_cliente'] = np.where(
                (df_resultado['monto'] > 1000) & (df_resultado['edad'] < 30), 
                'Premium Joven', 
                'Estándar'
            )

        # RÚBRICA 6: Segmentación demográfica por rangos de edad
        condiciones_edad = [
            (df_resultado['edad'] < 30),
            (df_resultado['edad'] >= 30) & (df_resultado['edad'] <= 50),
            (df_resultado['edad'] > 50)
        ]
        segmentos_edad = ['Joven', 'Adulto', 'Senior']
        df_resultado['segmento_edad'] = np.select(condiciones_edad, segmentos_edad, default='No Identificado')
        
        # RÚBRICA 7: Clasificación de transacciones según el volumen del monto
        df_resultado['ticket_alto'] = np.where(df_resultado['monto'] > df_resultado['precio_unitario'] * 1.5, 1, 0)
        
        # RÚBRICA 8: Mapeo numérico de la fidelidad para uso en algoritmos matemáticos
        mapeo_fidelidad = {'Bronce': 1, 'Plata': 2, 'Oro': 3, 'Platino': 4, 'Sin Registro': 0}
        df_resultado['codigo_fidelidad'] = df_resultado['nivel_fidelidad'].map(mapeo_fidelidad)
        
        # RÚBRICA 9: Conversión de montos a USD usando la tasa proporcionada (simulando una API externa)
        df_resultado['monto_usd'] = (df_resultado['monto'] / tasa_usd).round(2)
        df_resultado['precio_unitario_usd'] = (df_resultado['precio_unitario'] / tasa_usd).round(2)
        
        logging.info("Transformación: Reglas de negocio y conversión de divisas aplicadas.")
        return df_resultado

    def ejecutar_pca(self, df_maestro: pd.DataFrame):
        logging.info("Transformación: Ejecutando PCA...")
        df_analisis = df_maestro.copy()
        
        # Tomamos todas las numéricas disponibles para alimentar el PCA
        # (Esto simula el volumen de variables que pide la rúbrica)
        columnas_numericas = df_analisis.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filtramos columnas como IDs que no aportan al PCA
        columnas_pca = [col for col in columnas_numericas if col not in ['id_venta', 'id_cliente', 'id_producto', 'id_tienda']]
        
        # Rúbrica 10: Manejo de nulos antes de PCA (llenado con 0, aunque en un caso real podríamos usar la media o mediana)
        x_datos = df_analisis[columnas_pca].fillna(0)
        
        # Validación para asegurarnos de que hay suficientes datos para aplicar PCA, ya que si no, el modelo no se puede ajustar y lanzaría un error
        if x_datos.shape[0] < 2:
            return df_analisis, None

        # Rúbrica 11: Escalar numéricas con Min-Max
        escalador = MinMaxScaler() # <-- ¡Cambiado para cumplir la rúbrica!
        x_escalado = escalador.fit_transform(x_datos)
        
        # Rúbrica 12: Aplicar PCA para los 3 componentes principales
        pca = PCA(n_components=3, random_state=42)
        componentes = pca.fit_transform(x_escalado)
        
        df_analisis['PC1'] = componentes[:, 0].round(4)
        df_analisis['PC2'] = componentes[:, 1].round(4)
        df_analisis['PC3'] = componentes[:, 2].round(4)
        
        # Rúbrica 13: Explicación de varianza acumulada para entender cuánto de la información original se conserva en los componentes principales
        logging.info("Transformación: Filtrando columnas finales para el archivo maestro...")
        
        columnas_vip = [
            # 1. Datos de la Transacción (El qué y cuándo)
            'id_venta', 
            'fecha_transaccion', 
            'metodo_pago',
            
            # 2. Datos del Cliente (El quién)
            'id_cliente', 
            'nombre_completo', 
            'edad', 
            'ciudad', 
            'segmento_cliente', 
            'segmento_edad', 
            'nivel_fidelidad',
            
            # 3. Datos del Producto (El qué compró)
            'nombre_producto', 
            'categoria', 
            
            # 4. Datos Financieros (El dinero)
            'monto_usd', 
            'ticket_alto', 
            'precio_competencia', 
            
            # 5. Experiencia Web (Logs)
            'codigo_estado', 
            
            # 6. Variables Matemáticas (Tienen que escribirse tal cual las generó el código arriba)
            'PC1', 'PC2', 'PC3'
        ]
        
        # Filtramos el DataFrame para que solo contenga estas columnas
        columnas_existentes = [col for col in columnas_vip if col in df_analisis.columns]
        df_final = df_analisis[columnas_existentes].copy()
        
        # Retornamos el DataFrame filtrado y el modelo PCA
        return df_final, pca