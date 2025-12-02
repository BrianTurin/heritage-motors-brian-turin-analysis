# ============================
# ANÁLISIS ABC DE INSUMOS POR VEHÍCULO
# ============================

import os
import pandas as pd

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

# Confirmar tipos de producto disponibles
print("Tipos de producto encontrados:", df['PRODUCTLINE'].unique())

# === 2. Definir el catálogo de insumos (según el TP Integrador) ===
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

# === 3. Calcular las cantidades y valores totales por componente ===
# Inicializamos un diccionario para acumular totales
totals = {c["component"]: {"total_quantity": 0, "unit_cost": c["unit_cost"]} for c in catalog}

# Recorremos cada fila del dataset
for _, row in df.iterrows():
    pl = row["PRODUCTLINE"]
    qty_orders = row["QUANTITYORDERED"]
    for c in catalog:
        if pl in c["applies_to"]:
            totals[c["component"]]["total_quantity"] += c["usage_per_vehicle"] * qty_orders

# Calculamos el valor total de cada componente
for comp, v in totals.items():
    v["total_value"] = v["total_quantity"] * v["unit_cost"]

# Convertimos los resultados a un DataFrame
res = pd.DataFrame([
    {
        "component": comp,
        "total_quantity": v["total_quantity"],
        "unit_cost": v["unit_cost"],
        "total_value": v["total_value"]
    }
    for comp, v in totals.items()
])

# === 4. Ordenar y calcular porcentajes acumulados ===
res = res.sort_values("total_value", ascending=False).reset_index(drop=True)
res["cum_value"] = res["total_value"].cumsum()
res["cum_value_pct"] = 100 * res["cum_value"] / res["total_value"].sum()
res["value_pct"] = 100 * res["total_value"] / res["total_value"].sum()

# === 5. Clasificación ABC ===
def classify(cum_pct):
    if cum_pct <= 80:
        return "A"
    elif cum_pct <= 95:
        return "B"
    else:
        return "C"

res["ABC_class"] = res["cum_value_pct"].apply(classify)

# === 6. Mostrar resultados finales ===
print("\n=== RESULTADOS DEL ANÁLISIS ABC ===\n")
print(res)

# === 7. (Opcional) Exportar a Excel o CSV ===
# res.to_excel("analisis_ABC.xlsx", index=False)
# res.to_csv("analisis_ABC.csv", index=False)

# === 8. Resumen adicional por componente ===
# Mostramos, debajo de la tabla principal, cada componente con su
# total_quantity, unit_cost y el producto unit_cost * total_quantity (total_value).
print("\n=== RESUMEN POR COMPONENTE (cantidad × precio unitario) ===\n")
summary = res[["component", "total_quantity", "unit_cost", "total_value"]]
print(summary.to_string(index=False))

# ============================
# Fin del análisis
# ============================
