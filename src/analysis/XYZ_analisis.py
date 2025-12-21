# ANÁLISIS XYZ DE COMPONENTES
# ---------------------------
# Análisis XYZ de componentes según variabilidad de demanda.
# Entradas: data/sales_data_sample_clean.csv
# Salidas:  outputs/analysis/analisis_XYZ.csv (opcional)

import os
import pandas as pd

# === 1. Cargar el archivo CSV ===
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
data_dir = os.path.join(project_root, 'data')
output_dir = os.path.join(project_root, 'outputs', 'analysis')

os.makedirs(output_dir, exist_ok=True)

filename = 'sales_data_sample_clean.csv'
file_path = os.path.join(data_dir, filename)

if not os.path.exists(file_path):
    raise SystemExit(f"Archivo no encontrado: {file_path}\n\nAsegurate de tener el dataset en data/")

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

# === 4. Calcular consumo mensual por componente ===
# Inicializar dataframe de resultados mensuales
monthly_usage = []

for comp in catalog:
    subset = df[df['PRODUCTLINE'].isin(comp['applies_to'])]
    monthly = (
        subset.groupby('MES')['QUANTITYORDERED']
        .sum()
        .reset_index(name='qty')
        .assign(component=comp['component'],
                usage=lambda x: x['qty'] * comp['usage_per_vehicle'])
    )
    monthly_usage.append(monthly)

monthly_df = pd.concat(monthly_usage, ignore_index=True)

# === 5. Calcular coeficiente de variación por componente ===
summary = (
    monthly_df.groupby('component')['usage']
    .agg(['mean', 'std'])
    .reset_index()
)
summary['coef_var'] = (summary['std'] / summary['mean']) * 100

# === 6. Clasificar según CV ===
def xyz_class(cv):
    if cv <= 10:
        return 'X'
    elif cv <= 25:
        return 'Y'
    else:
        return 'Z'

summary['XYZ'] = summary['coef_var'].apply(xyz_class)

# === 7. Formatear resultados finales ===
summary['coef_var'] = summary['coef_var'].map(lambda x: f"{x:.2f}%")
summary = summary.rename(columns={'mean': 'Promedio mensual', 'std': 'Desvío estándar', 'coef_var': 'Coef. de variación'})

# === 8. Mostrar resultados ===
print("\n=== RESULTADOS DEL ANÁLISIS XYZ ===\n")
print(summary.to_string(index=False))

# ============================
# Fin del análisis
# ============================
