import os
import pandas as pd

# === Cargar CSV (intenta rutas comunes) ===
filename = 'sales_data_sample_clean.csv'
base_dir = os.path.dirname(__file__) or os.getcwd()
candidate_paths = [
    os.path.join(base_dir, filename),
    os.path.join(base_dir, 'TPFinal IO', filename),
    os.path.join(base_dir, 'TPFinal_IO', filename),
]

file_path = None
for p in candidate_paths:
    if os.path.exists(p):
        file_path = p
        break

if file_path is None:
    tried = '\n'.join(candidate_paths)
    raise SystemExit(f"Archivo no encontrado. Rutas probadas:\n{tried}\n\nColoca '{filename}' en una de esas rutas o ejecuta el script desde la carpeta que lo contenga.")

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
output_path = os.path.join(base_dir, 'ventaspormes.csv')
result.to_csv(output_path, index=False)

# Salida mínima
print(f"CSV generado: {output_path}")
print(result.head(10))