"""
02_generar_ventas_mensuales.py
==============================
Genera la serie temporal de ventas mensuales por tipo de producto.

Entrada: data/sales_data_sample_clean.csv
Salida:  data/ventaspormes.csv
"""
import os
import pandas as pd

# === Configuración de rutas ===
SCRIPT_DIR = os.path.dirname(__file__) or os.getcwd()
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

filename = 'sales_data_sample_clean.csv'
file_path = os.path.join(DATA_DIR, filename)

if not os.path.exists(file_path):
    raise SystemExit(f"Archivo no encontrado: {file_path}\n\nAsegurate de ejecutar primero 01_limpiar_dataset.py")

df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)

# === Preparar columnas de fecha ===
df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
df = df.dropna(subset=['ORDERDATE'])

# Definir rango fijo de 29 meses empezando desde el mes mínimo del dataset
start_period = df['ORDERDATE'].min().to_period('M')
periods = pd.period_range(start_period, periods=29, freq='M').astype(str)

# Contar ventas por mes y por tipo de producto
df['Year_Month'] = df['ORDERDATE'].dt.to_period('M').astype(str)
counts = (
    df.groupby(['Year_Month', 'PRODUCTLINE'])['ORDERNUMBER']
      .count()
      .unstack(fill_value=0)
)

# Asegurar columnas para ambos tipos
for col in ['Classic Cars', 'Vintage Cars']:
    if col not in counts.columns:
        counts[col] = 0

# Reindexar usando los 29 meses definidos, rellenar con ceros si faltan
counts = counts.reindex(periods).fillna(0).astype(int)

# Resultado final: columna Mes (1..29) + ventas por tipo
result = counts.reset_index().rename(columns={'index': 'Periodo'})
result.insert(0, 'Mes', range(1, len(result) + 1))
result = result[['Mes', 'Classic Cars', 'Vintage Cars']]

# Guardar CSV
output_path = os.path.join(DATA_DIR, 'ventaspormes.csv')
result.to_csv(output_path, index=False)

# Salida mínima
print(f"CSV generado: {output_path}")
print(result.head(10))