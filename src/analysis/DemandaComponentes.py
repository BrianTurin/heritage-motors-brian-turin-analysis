# ============================
# ANÁLISIS demandas DE INSUMOS POR VEHÍCULO
# ============================

import os
import pandas as pd
import matplotlib.pyplot as plt

# === 1. Cargar el archivo CSV ===
# Intentamos varias rutas comunes: misma carpeta del script y la subcarpeta 'TPFinal IO'
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

# === 2. Asegurar que ORDERDATE sea fecha y agregar columna de mes ===
df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
df['MES'] = df['ORDERDATE'].dt.to_period('M').astype(str)

# === 3. Definir catálogo de insumos (según TP Integrador) ===
catalog = [
    {"component": "Motor de Alto Rendimiento V8", "applies_to": ["Classic Cars"], "usage_per_vehicle": 1, "unit_cost": 9000},
    {"component": "Motor de Cilindros en Línea Raro", "applies_to": ["Vintage Cars"], "usage_per_vehicle": 1, "unit_cost": 12000},
    {"component": "Carrocería Artesanal de Época", "applies_to": ["Vintage Cars"], "usage_per_vehicle": 1, "unit_cost": 15000},
    {"component": "Carrocería Estándar (Fibra)", "applies_to": ["Classic Cars"], "usage_per_vehicle": 1, "unit_cost": 6500},
    {"component": "Transmisión de 5 Velocidades", "applies_to": ["Classic Cars", "Vintage Cars"], "usage_per_vehicle": 1, "unit_cost": 3500},
    {"component": "Sistema de Inyección Electrónica", "applies_to": ["Classic Cars"], "usage_per_vehicle": 1, "unit_cost": 1200},
    {"component": "Set de Carburadores Dobles", "applies_to": ["Vintage Cars"], "usage_per_vehicle": 1, "unit_cost": 900},
    {"component": "Tapicería de Cuero Premium", "applies_to": ["Classic Cars", "Vintage Cars"], "usage_per_vehicle": 1, "unit_cost": 4000},
    {"component": "Juego de Llantas Vintage Espec.", "applies_to": ["Vintage Cars"], "usage_per_vehicle": 4, "unit_cost": 2500},
    {"component": "Llantas Regulares Cromados", "applies_to": ["Classic Cars"], "usage_per_vehicle": 4, "unit_cost": 400},
    {"component": "Cubiertas de Alta Gama (Neumáticos)", "applies_to": ["Classic Cars", "Vintage Cars"], "usage_per_vehicle": 4, "unit_cost": 250},
]

# Separar componentes por tipo de carro
vintage_components = [comp for comp in catalog if "Vintage Cars" in comp["applies_to"]]
classic_components = [comp for comp in catalog if "Classic Cars" in comp["applies_to"]]

# Calcular consumo mensual por componente
monthly_usage = []

for comp in catalog:
    subset = df[df['PRODUCTLINE'].isin(comp['applies_to'])]
    monthly = (
        subset.groupby('MES')['QUANTITYORDERED']
        .sum()
        .rename(comp['component'])
    )
    monthly_usage.append(monthly)

# Unir todos los componentes en un DataFrame
usage_df = pd.concat(monthly_usage, axis=1).fillna(0).astype(int)
usage_df.index.name = 'MES'

# Guardar resultados
output_path = os.path.join(base_dir, 'demanda_componentes_mensual.csv')
usage_df.to_csv(output_path)
print(f"✓ Demanda mensual de componentes exportada a: {output_path}")

# (Opcional) Graficar demanda de un componente
# usage_df['Motor de Alto Rendimiento V8'].plot(title='Demanda Mensual - Motor V8')
# plt.show()
