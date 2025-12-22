"""
Cálculo de la Capacidad Mínima de Almacén requerida para soportar el pronóstico de demanda.
- Utiliza los volúmenes de cada componente y los resultados del pronóstico/EOQ estacional.
- Considera el máximo inventario esperado por componente y estación.
"""

import os
import pandas as pd

# Rutas
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
output_dir = os.path.join(project_root, 'outputs', 'warehouse')
os.makedirs(output_dir, exist_ok=True)

# Cargar tabla de valores clave (resultado EOQ estacional)
tabla_path = os.path.join(project_root, 'outputs', 'inventory', 'eoq_estacional', 'tabla_valores_clave.csv')
tabla = pd.read_csv(tabla_path)

# Definir volúmenes por componente (m³/unidad) según la definición del problema
volumenes = {
    'Motor de Alto Rendimiento V8': 0.8,
    'Motor de Cilindros de Línea Raro': 0.9,
    'Carrocería Artesanal de Época': 4.0,
    'Carrocería Estándar (Fibra)': 3.5,
    'Tapicería de Cuero Premium': 0.5
    # Agregar más componentes aquí si se amplía el análisis
}

# Calcular el inventario máximo esperado por componente y estación
# Inventario máximo ≈ ROP + EOQ (o ROP + Q/2 + SS, según política)
resultados = []
for idx, row in tabla.iterrows():
    comp = row['Componente']
    if comp not in volumenes:
        continue  # Saltar componentes sin volumen definido
    volumen = volumenes[comp]
    # Inventario máximo considerando nivel de servicio: ROP + EOQ + Stock de Seguridad
    ss = row['Stock_Seguridad'] if 'Stock_Seguridad' in row and not pd.isna(row['Stock_Seguridad']) else 0
    inventario_max = row['ROP'] + row['EOQ'] + ss
    capacidad_requerida = inventario_max * volumen
    resultados.append({
        'Componente': comp,
        'Estacion': row['Estacion'],
        'Inventario_Maximo': inventario_max,
        'Volumen_por_Unidad_m3': volumen,
        'Capacidad_Requerida_m3': capacidad_requerida
    })


# Crear DataFrame y redondear
capacidad_df = pd.DataFrame(resultados)
capacidad_df = capacidad_df.round(4)

# Calcular totales por estación
totales_estacion = capacidad_df.groupby('Estacion').agg({
    'Inventario_Maximo': 'sum',
    'Capacidad_Requerida_m3': 'sum'
}).reset_index()

# Determinar estación con mayor necesidad
idx_max = totales_estacion['Capacidad_Requerida_m3'].idxmax()
estacion_max = totales_estacion.loc[idx_max, 'Estacion']
inv_max = totales_estacion.loc[idx_max, 'Inventario_Maximo']
cap_max = totales_estacion.loc[idx_max, 'Capacidad_Requerida_m3']

# Agregar fila de total de la estación más demandante
total_row = {
    'Componente': 'TOTAL',
    'Estacion': f'{estacion_max} (mayor necesidad, suma de máximos por componente)',
    'Inventario_Maximo': inv_max,
    'Volumen_por_Unidad_m3': '—',
    'Capacidad_Requerida_m3': cap_max
}
capacidad_df = pd.concat([capacidad_df, pd.DataFrame([total_row])], ignore_index=True)

# Guardar resultados principales
csv_path = os.path.join(output_dir, 'capacidad_minima_almacen.csv')
capacidad_df.to_csv(csv_path, index=False)

# Guardar totales por estación y resumen en el mismo CSV (agregando como nuevas filas)
with open(csv_path, 'a', encoding='utf-8') as f:
    f.write('\n')
    f.write('Totales por estación,,Inventario_Maximo,Capacidad_Requerida_m3\n')
    for _, row in totales_estacion.iterrows():
        f.write(f"{row['Estacion']},,{row['Inventario_Maximo']},{row['Capacidad_Requerida_m3']}\n")
    f.write(f"\nEstación con mayor necesidad:,{estacion_max},Inventario_Maximo:,{inv_max},Capacidad_Requerida_m3:,{cap_max}\n")

print("[OK] Capacidad mínima de almacén calculada y exportada a:", csv_path)
print(capacidad_df)
print("\nTotales por estación:")
print(totales_estacion)
print(f"\nLa estación con mayor necesidad de almacén es: {estacion_max}")
