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
        .reset_index(name='qty')
        .assign(
            component=comp['component'],
            usage=lambda x: x['qty'] * comp['usage_per_vehicle']
        )
    )
    monthly_usage.append(monthly)

monthly_df = pd.concat(monthly_usage, ignore_index=True)

# Crear figuras
plt.figure(figsize=(15, 10))

# Gráfica para Vintage Cars
plt.subplot(2, 1, 1)
for comp in vintage_components:
    data = monthly_df[monthly_df['component'] == comp['component']]
    plt.plot(data['MES'], data['usage'], marker='o', label=comp['component'])

plt.title('Demanda Mensual - Componentes Vintage Cars')
plt.xlabel('Mes')
plt.ylabel('Unidades')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.xticks(rotation=45)

# Gráfica para Classic Cars
plt.subplot(2, 1, 2)
for comp in classic_components:
    data = monthly_df[monthly_df['component'] == comp['component']]
    plt.plot(data['MES'], data['usage'], marker='o', label=comp['component'])

plt.title('Demanda Mensual - Componentes Classic Cars')
plt.xlabel('Mes')
plt.ylabel('Unidades')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()
