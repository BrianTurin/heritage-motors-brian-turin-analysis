# ============================
# POLÍTICAS DE INVENTARIO - EOQ ESTACIONAL
# Cantidad Económica de Pedido por Temporadas
# ============================
"""
eoq_estacional.py
=================
Modelo EOQ adaptado para demanda estacional (CV < 0.20 por temporada).
Basado en Winston, pág. 872-873.

Estación PICO: Oct-Nov (CV = 0.0919 < 0.20) (EOQ válido)
Estación NORMAL: Resto del año (CV = 0.0716 < 0.20) (EOQ válido)

Este es el modelo RECOMENDADO cuando el CV anual >= 0.20.

Entrada: outputs/forecast/prophet_results.csv, prophet_forecast.csv
Salida:  outputs/inventory/eoq_estacional_*.csv, eoq_estacional_*.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Parámetro de tasa de mantenimiento anual (20% del costo unitario)
TASA_MANTENIMIENTO = 0.20
# Costo de ordenar por pedido
COSTO_ORDENAR = 300
# Z-score para nivel de servicio 95%
Z_ALPHA = 1.645

# Definir rutas necesarias antes de usarlas
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
output_dir = os.path.join(project_root, 'outputs', 'inventory', 'eoq_estacional')
os.makedirs(output_dir, exist_ok=True)
forecast_dir = os.path.join(project_root, 'outputs', 'forecast')
componentes = pd.DataFrame({
    'Componente': [
        'Carrocería Artesanal de Época',
        'Motor de Alto Rendimiento V8',
        'Motor de Cilindros de Línea Raro',
        'Carrocería Estándar (Fibra)',
        'Tapicería de Cuero Premium'
    ],
    'Auto_Foco': [
        'Vintage',
        'Clásico',
        'Vintage',
        'Clásico',
        'Ambos'
    ],
    'Costo_Unitario': [
        15000,
        9000,
        12000,
        6500,
        4000
    ],
    'Uso_por_Auto': [
        1, 1, 1, 1, 1
    ],
    'Volumen_m3': [
        4.0,
        0.8,
        0.9,
        3.5,
        0.5
    ],
    'Lead_Time_Semanas': [
        10,
        6,
        12,
        4,
        8
    ]
})

# === 3. CARGAR Y SEGMENTAR PRONÓSTICO PROPHET ===
print("\n--- Cargando y segmentando pronóstico Prophet ---")


# Usar exactamente los valores de Autos_Clasicos de prophet_forecast.csv
prophet_forecast_path = os.path.join(forecast_dir, 'prophet', 'prophet_forecast.csv')
df_pronostico = pd.read_csv(prophet_forecast_path)
df_pronostico = df_pronostico[pd.to_datetime(df_pronostico['Periodo'], errors='coerce').notnull()].copy()
df_pronostico['Mes'] = pd.to_datetime(df_pronostico['Periodo']).dt.month

# Definir meses de cada estación
MESES_PICO = [10, 11]
MESES_NORMAL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12]


# Demanda exacta de Autos_Clasicos y Autos_Vintage por estación
demanda_pico_clasicos = df_pronostico[df_pronostico['Mes'].isin(MESES_PICO)]['Autos_Clasicos'].sum()
demanda_normal_clasicos = df_pronostico[df_pronostico['Mes'].isin(MESES_NORMAL)]['Autos_Clasicos'].sum()
demanda_pico_vintage = df_pronostico[df_pronostico['Mes'].isin(MESES_PICO)]['Autos_Vintage'].sum()
demanda_normal_vintage = df_pronostico[df_pronostico['Mes'].isin(MESES_NORMAL)]['Autos_Vintage'].sum()

demanda_total_pico = demanda_pico_clasicos + demanda_pico_vintage
demanda_total_normal = demanda_normal_clasicos + demanda_normal_vintage

print("\nResultados EOQ estacional usando demanda EXACTA de cada temporada:")
# Mostrar el EOQ para 'Motor de Alto Rendimiento V8' como ejemplo
try:
    eoq_pico = None
    eoq_normal = None
    if 'df_pico' in locals() and not df_pico.empty:
        eoq_pico = df_pico[df_pico['Componente'] == 'Motor de Alto Rendimiento V8']['EOQ'].values[0]
    if 'df_normal' in locals() and not df_normal.empty:
        eoq_normal = df_normal[df_normal['Componente'] == 'Motor de Alto Rendimiento V8']['EOQ'].values[0]
    print(f"\nTemporada pico (meses {MESES_PICO}):\n  Demanda total: {demanda_pico}\n  EOQ Motor V8: {eoq_pico:.2f}" if eoq_pico is not None else "EOQ Motor V8 no disponible para pico")
    print(f"\nTemporada normal (meses {MESES_NORMAL}):\n  Demanda total: {demanda_normal}\n  EOQ Motor V8: {eoq_normal:.2f}" if eoq_normal is not None else "EOQ Motor V8 no disponible para normal")
except Exception as e:
    print(f"Error mostrando EOQ Motor V8: {e}")

# === 4. CALCULAR DEMANDA ANUALIZADA POR ESTACIÓN ===
print("\n" + "="*70)
print("CÁLCULO DE DEMANDA POR ESTACIÓN")
print("="*70)

# Duración de cada estación (en meses y fracción del año)
MESES_EN_PICO = len(MESES_PICO)  # 2 meses
MESES_EN_NORMAL = len(MESES_NORMAL)  # 10 meses

FRACCION_PICO = MESES_EN_PICO / 12  # 2/12 = 0.167
FRACCION_NORMAL = MESES_EN_NORMAL / 12  # 10/12 = 0.833


# Demanda total por estación (ya son escalares)
demanda_total_anual = demanda_total_pico + demanda_total_normal

# Demanda mensual promedio por estación
demanda_mensual_pico = demanda_total_pico / MESES_EN_PICO if MESES_EN_PICO > 0 else 0
demanda_mensual_normal = demanda_total_normal / MESES_EN_NORMAL if MESES_EN_NORMAL > 0 else 0

print(f"\n  ESTACIÓN PICO ({MESES_EN_PICO} meses = {FRACCION_PICO*100:.1f}% del año):")
print(f"    Demanda total:          ${demanda_total_pico:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Demanda mensual prom:   ${demanda_mensual_pico:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n  ESTACIÓN NORMAL ({MESES_EN_NORMAL} meses = {FRACCION_NORMAL*100:.1f}% del año):")
print(f"    Demanda total:          ${demanda_total_normal:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Demanda mensual prom:   ${demanda_mensual_normal:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n  TOTAL ANUAL:              ${demanda_total_anual:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))



print(f"\n  Unidades estimadas PICO:    {demanda_total_pico:>10,.0f} (Clásicos: {demanda_pico_clasicos:.0f}, Vintage: {demanda_pico_vintage:.0f})")
print(f"  Unidades estimadas NORMAL:  {demanda_total_normal:>10,.0f} (Clásicos: {demanda_normal_clasicos:.0f}, Vintage: {demanda_normal_vintage:.0f})")

# === 6. FUNCIONES EOQ ===
def calcular_eoq(D, S, H):
    # EOQ = sqrt(2DS/H)
    return np.sqrt((2 * D * S) / H)

def calcular_costo_total(D, Q, S, H, SS=0):
    """CTE = (D/Q)*S + (Q/2 + SS)*H"""
    costo_ordenar = (D / Q) * S
    costo_mantener = ((Q / 2) + SS) * H
    return costo_ordenar + costo_mantener

# === 7. CALCULAR EOQ POR ESTACIÓN ===
print("\n" + "="*70)
print("EOQ POR ESTACIÓN - POLÍTICA A (Óptima por Costos)")
print("="*70)

SEMANAS_POR_MES = 4.33

def calcular_demanda_componente_estacion(row, demanda_clasicos, demanda_vintage):
    """Calcula demanda de componente para una estación según tipo de auto"""
    if row['Auto_Foco'] == 'Clásico':
        return demanda_clasicos * row['Uso_por_Auto']
    elif row['Auto_Foco'] == 'Vintage':
        return demanda_vintage * row['Uso_por_Auto']
    elif row['Auto_Foco'] == 'Ambos':
        # Para componentes 'Ambos', la demanda es la suma de Autos_Clasicos y Autos_Vintage multiplicada por Uso_por_Auto
        return (demanda_clasicos + demanda_vintage) * row['Uso_por_Auto']
    else:
        # Si hay un valor inesperado, lanzar advertencia y devolver 0
        print(f"[ADVERTENCIA] Auto_Foco inesperado: {row['Auto_Foco']} para componente {row['Componente']}")
        return 0

# Calcular demanda por componente para cada estación
resultados_pico = []
resultados_normal = []

for idx, row in componentes.iterrows():
    C = row['Costo_Unitario']
    H = C * TASA_MANTENIMIENTO  # Anual
    L = row['Lead_Time_Semanas']
    
    # --- ESTACIÓN PICO ---
    D_pico = calcular_demanda_componente_estacion(row, demanda_pico_clasicos, demanda_pico_vintage)
    # EOQ con demanda real de la estación (NO anualizada)
    Q_pico = calcular_eoq(D_pico, COSTO_ORDENAR, H)
    # Número de pedidos durante la estación pico
    N_pico = D_pico / Q_pico if Q_pico > 0 else 0
    # Costo durante estación pico (proporcional)
    CTE_pico = calcular_costo_total(D_pico, Q_pico, COSTO_ORDENAR, H * FRACCION_PICO)
    # Demanda semanal y ROP
    semanas_pico = MESES_EN_PICO * SEMANAS_POR_MES
    demanda_semanal_pico = D_pico / semanas_pico if semanas_pico > 0 else 0
    ROP_pico = demanda_semanal_pico * L
    # Tiempo entre pedidos en semanas
    tiempo_entre_pedidos_pico = semanas_pico / N_pico if N_pico > 0 else np.nan
    resultados_pico.append({
        'Componente': row['Componente'],
        'Estacion': 'PICO',
        'Demanda_Estacion': D_pico,
        'EOQ': Q_pico,
        'Num_Pedidos': N_pico,
        'Tiempo_Entre_Pedidos_Semanas': tiempo_entre_pedidos_pico,
        'Tiempo_Entre_Pedidos_Dias': tiempo_entre_pedidos_pico * 7 if not np.isnan(tiempo_entre_pedidos_pico) else np.nan,
        'ROP': ROP_pico,
        'CTE': CTE_pico,
        'Costo_Unitario': C
    })
    # --- ESTACIÓN NORMAL ---
    D_normal = calcular_demanda_componente_estacion(row, demanda_normal_clasicos, demanda_normal_vintage)
    # EOQ con demanda real de la estación (NO anualizada)
    Q_normal = calcular_eoq(D_normal, COSTO_ORDENAR, H)
    N_normal = D_normal / Q_normal if Q_normal > 0 else 0
    CTE_normal = calcular_costo_total(D_normal, Q_normal, COSTO_ORDENAR, H * FRACCION_NORMAL)
    semanas_normal = MESES_EN_NORMAL * SEMANAS_POR_MES
    demanda_semanal_normal = D_normal / semanas_normal if semanas_normal > 0 else 0
    ROP_normal = demanda_semanal_normal * L
    tiempo_entre_pedidos_normal = semanas_normal / N_normal if N_normal > 0 else np.nan
    resultados_normal.append({
        'Componente': row['Componente'],
        'Estacion': 'NORMAL',
        'Demanda_Estacion': D_normal,
        'EOQ': Q_normal,
        'Num_Pedidos': N_normal,
        'Tiempo_Entre_Pedidos_Semanas': tiempo_entre_pedidos_normal,
        'Tiempo_Entre_Pedidos_Dias': tiempo_entre_pedidos_normal * 7 if not np.isnan(tiempo_entre_pedidos_normal) else np.nan,
        'ROP': ROP_normal,
        'CTE': CTE_normal,
        'Costo_Unitario': C
    })


# === NUEVA SECCIÓN: CÁLCULO DE COSTO TOTAL ÓPTIMO POR COSTOS (FÓRMULA COMPLETA) ===
print("\n" + "="*70)
print("COSTO TOTAL ÓPTIMO POR COSTOS (FÓRMULA COMPLETA)")
print("="*70)

def calcular_ct_optimo(K, D, Q, h, c):
    # TC(Q) = (K*D)/Q + (h*Q)/2 + c*D
    # K: costo de ordenar por pedido
    # D: demanda de la estación
    # Q: cantidad de pedido (EOQ)
    # h: costo de mantener una unidad durante la estación (c * tasa_mant * fraccion_estacion)
    # c: costo unitario de compra
    return (K * D) / Q + (h * Q) / 2 + c * D if Q > 0 else np.nan

# Agregar columna CT_Optimo a los resultados de cada estación
for res in resultados_pico:
    # h para estación pico: c * tasa_mant * fracción_pico
    h_pico = res['Costo_Unitario'] * TASA_MANTENIMIENTO * FRACCION_PICO
    res['CT_Optimo'] = calcular_ct_optimo(COSTO_ORDENAR, res['Demanda_Estacion'], res['EOQ'], h_pico, res['Costo_Unitario'])
for res in resultados_normal:
    # h para estación normal: c * tasa_mant * fracción_normal
    h_normal = res['Costo_Unitario'] * TASA_MANTENIMIENTO * FRACCION_NORMAL
    res['CT_Optimo'] = calcular_ct_optimo(COSTO_ORDENAR, res['Demanda_Estacion'], res['EOQ'], h_normal, res['Costo_Unitario'])
"""
EJEMPLO DE CÁLCULO PASO A PASO PARA MOTOR DE ALTO RENDIMIENTO V8, ESTACIÓN PICO:

Datos:
K = 300
D = 172
Q = 7.6 (aprox, calculado por EOQ)
c = 9000
Tasa de mantenimiento = 0.20
Fracción estación pico = 2/12 = 0.1667
h = 9000 * 0.20 * 0.1667 = 300

CT(Q) = (K*D)/Q + (h*Q)/2 + c*D
    = (300*172)/7.6 + (300*7.6)/2 + 9000*172
    = 6,789.47 + 1,140 + 1,548,000 = 1,555,929.47
"""

df_pico = pd.DataFrame(resultados_pico)
df_normal = pd.DataFrame(resultados_normal)

print("\n--- ESTACIÓN PICO (Oct-Nov, 2 meses) ---")
print(f"{'Componente':<35} {'EOQ':<10} {'CT_Óptimo($)':<15}")
print("-" * 60)
for idx, row in df_pico.iterrows():
    print(f"{row['Componente']:<35} {row['EOQ']:>10.1f} {row['CT_Optimo']:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print("\n--- ESTACIÓN NORMAL (resto, 10 meses) ---")
print(f"{'Componente':<35} {'EOQ':<10} {'CT_Óptimo($)':<15}")
print("-" * 60)
for idx, row in df_normal.iterrows():
    print(f"{row['Componente']:<35} {row['EOQ']:>10.1f} {row['CT_Optimo']:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Mostrar resultados PICO
print(f"\n--- ESTACIÓN PICO (Oct-Nov, {MESES_EN_PICO} meses) ---")
print(f"  Demanda anualizada para cálculo EOQ (ajustada por duración)")

print(f"\n{'Componente':<35} {'D estac.':<12} {'EOQ':<10} {'N ped.':<8} {'CTE ($)':<12}")
print("-" * 70)
for idx, row in df_pico.iterrows():
    print(f"{row['Componente']:<35} {row['Demanda_Estacion']:>10,.1f} {row['EOQ']:>10,.1f} {row['Num_Pedidos']:>7,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_pico_total = df_pico['CTE'].sum()
print(f"\n{'CTE TOTAL ESTACIÓN PICO:':<55} ${cte_pico_total:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Mostrar resultados NORMAL
print(f"\n--- ESTACIÓN NORMAL (resto, {MESES_EN_NORMAL} meses) ---")

print(f"\n{'Componente':<35} {'D estac.':<12} {'EOQ':<10} {'N ped.':<8} {'CTE ($)':<12}")
print("-" * 70)
for idx, row in df_normal.iterrows():
    print(f"{row['Componente']:<35} {row['Demanda_Estacion']:>10,.1f} {row['EOQ']:>10,.1f} {row['Num_Pedidos']:>7,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_normal_total = df_normal['CTE'].sum()
print(f"\n{'CTE TOTAL ESTACIÓN NORMAL:':<55} ${cte_normal_total:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_anual_estacional = cte_pico_total + cte_normal_total
print(f"\n{'CTE TOTAL ANUAL (PICO + NORMAL):':<55} ${cte_anual_estacional:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 8. COMPARACIÓN CON EOQ SIN ESTACIONALIDAD ===

# === 9. POLÍTICA B - CON STOCK DE SEGURIDAD ===

print("\n" + "="*70)
print("EOQ ESTACIONAL - POLÍTICA B (Nivel de Servicio 95%)")
print("="*70)

# Usar los mismos componentes y estructura que EOQ A
print("\nComponentes considerados (idénticos a EOQ A):")
for comp in componentes['Componente']:
    print(f"- {comp}")


# Exportar los mismos resultados que EOQ A para la política B, con columna de aviso
df_pico_b = df_pico.copy()
df_normal_b = df_normal.copy()
df_pico_b['Aviso'] = 'Sin stock de seguridad (SS) por falta de datos'
df_normal_b['Aviso'] = 'Sin stock de seguridad (SS) por falta de datos'
df_pico_b.to_csv(os.path.join(output_dir, 'eoq_estacional_pico_b.csv'), index=False)
df_normal_b.to_csv(os.path.join(output_dir, 'eoq_estacional_normal_b.csv'), index=False)
print("\n[AVISO] Se omite el cálculo de stock de seguridad (Política B) por falta de datos de error de pronóstico.\nSe exportan los mismos productos y columnas que EOQ A en eoq_estacional_pico_b.csv y eoq_estacional_normal_b.csv.")


# === 10. RESUMEN COMPARATIVO ===
print("\n" + "="*70)
print("RESUMEN EOQ ESTACIONAL (CV validado por Winston)")
print(f"  ESTACIÓN PICO (Oct-Nov, 2 meses):")
print(f"    Política A (sin SS):  ${cte_pico_total:>12,.2f}")
print(f"  ESTACIÓN NORMAL (resto, 10 meses):")
print(f"    Política A (sin SS):  ${cte_normal_total:>12,.2f}")
print(f"  TOTALES ANUALES:")
print(f"    Política A Estacional:  ${cte_anual_estacional:>12,.2f}")

# === 11. EXPORTAR RESULTADOS ===
print("\n--- Exportando resultados ---")

# Guardar resultados por estación

# Redondear a 4 decimales todos los valores numéricos antes de exportar

df_pico_rounded = df_pico.copy()
df_normal_rounded = df_normal.copy()
for col in df_pico_rounded.select_dtypes(include=['float', 'int']).columns:
    df_pico_rounded[col] = df_pico_rounded[col].round(4)
for col in df_normal_rounded.select_dtypes(include=['float', 'int']).columns:
    df_normal_rounded[col] = df_normal_rounded[col].round(4)
df_pico_rounded.to_csv(os.path.join(output_dir, 'eoq_estacional_pico_a.csv'), index=False)
df_normal_rounded.to_csv(os.path.join(output_dir, 'eoq_estacional_normal_a.csv'), index=False)

# Crear CSV resumen para política A
df_resumen_a = df_pico_rounded[['Componente','CTE','CT_Optimo']].copy()
df_resumen_a = df_resumen_a.rename(columns={'CTE':'CTE_PICO','CT_Optimo':'CT_Optimo_PICO'})
df_resumen_a = df_resumen_a.merge(
    df_normal_rounded[['Componente','CTE','CT_Optimo']].rename(columns={'CTE':'CTE_NORMAL','CT_Optimo':'CT_Optimo_NORMAL'}),
    on='Componente', how='outer')
df_resumen_a['CTE_TOTAL'] = df_resumen_a['CTE_PICO'].fillna(0) + df_resumen_a['CTE_NORMAL'].fillna(0)
df_resumen_a['CT_Optimo_TOTAL'] = df_resumen_a['CT_Optimo_PICO'].fillna(0) + df_resumen_a['CT_Optimo_NORMAL'].fillna(0)
total_row_a = {col: '' for col in df_resumen_a.columns}
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    total_row_a[col] = df_resumen_a[col].sum()
total_row_a['Componente'] = 'TOTAL'
df_resumen_a = pd.concat([df_resumen_a, pd.DataFrame([total_row_a])], ignore_index=True)
# Redondear columnas numéricas a 4 decimales
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    df_resumen_a[col] = pd.to_numeric(df_resumen_a[col], errors='coerce').round(4)
df_resumen_a.to_csv(os.path.join(output_dir, 'eoq_estacional_resumen_a.csv'), index=False)

# Crear CSV resumen para política B (idéntico a A en este caso)
df_pico_b = df_pico_rounded.copy()
df_normal_b = df_normal_rounded.copy()
df_pico_b['Aviso'] = 'Sin stock de seguridad (SS) por falta de datos'
df_normal_b['Aviso'] = 'Sin stock de seguridad (SS) por falta de datos'
df_pico_b.to_csv(os.path.join(output_dir, 'eoq_estacional_pico_b.csv'), index=False)
df_normal_b.to_csv(os.path.join(output_dir, 'eoq_estacional_normal_b.csv'), index=False)
df_resumen_b = df_pico_b[['Componente','CTE','CT_Optimo']].copy()
df_resumen_b = df_resumen_b.rename(columns={'CTE':'CTE_PICO','CT_Optimo':'CT_Optimo_PICO'})
df_resumen_b = df_resumen_b.merge(
    df_normal_b[['Componente','CTE','CT_Optimo']].rename(columns={'CTE':'CTE_NORMAL','CT_Optimo':'CT_Optimo_NORMAL'}),
    on='Componente', how='outer')
df_resumen_b['CTE_TOTAL'] = df_resumen_b['CTE_PICO'].fillna(0) + df_resumen_b['CTE_NORMAL'].fillna(0)
df_resumen_b['CT_Optimo_TOTAL'] = df_resumen_b['CT_Optimo_PICO'].fillna(0) + df_resumen_b['CT_Optimo_NORMAL'].fillna(0)
df_resumen_b.to_csv(os.path.join(output_dir, 'eoq_estacional_resumen_b.csv'), index=False)
total_row_b = {col: '' for col in df_resumen_b.columns}
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    total_row_b[col] = df_resumen_b[col].sum()
total_row_b['Componente'] = 'TOTAL'
df_resumen_b = pd.concat([df_resumen_b, pd.DataFrame([total_row_b])], ignore_index=True)
# Redondear columnas numéricas a 4 decimales
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    df_resumen_b[col] = pd.to_numeric(df_resumen_b[col], errors='coerce').round(4)
df_resumen_b.to_csv(os.path.join(output_dir, 'eoq_estacional_resumen_b.csv'), index=False)

print(f"[OK] Exportados en {output_dir}: eoq_estacional_pico_a.csv, eoq_estacional_normal_a.csv")

# === 12. VISUALIZACIÓN ===
print("\n--- Generando gráficos ---")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('EOQ Estacional - Análisis por Temporadas\n(CV validado según Winston)', 
             fontsize=14, fontweight='bold')

# Gráfico 1: Demanda por estación
ax1 = axes[0, 0]
x = np.arange(len(componentes))
width = 0.35
bars1 = ax1.bar(x - width/2, df_pico['Demanda_Estacion'], width, label='PICO (Oct-Nov)', color='coral')
bars2 = ax1.bar(x + width/2, df_normal['Demanda_Estacion'], width, label='NORMAL (resto)', color='steelblue')
ax1.set_ylabel('Demanda (unidades)')
ax1.set_title('Demanda por Componente y Estación')
ax1.set_xticks(x)
ax1.set_xticklabels([c[:12]+'...' if len(c)>12 else c for c in componentes['Componente']], rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico 2: EOQ por estación
ax2 = axes[0, 1]
bars1 = ax2.bar(x - width/2, df_pico['EOQ'], width, label='EOQ PICO', color='coral')
bars2 = ax2.bar(x + width/2, df_normal['EOQ'], width, label='EOQ NORMAL', color='steelblue')
ax2.set_ylabel('Cantidad de pedido (EOQ)')
ax2.set_title('EOQ Óptimo por Estación')
ax2.set_xticks(x)
ax2.set_xticklabels([c[:12]+'...' if len(c)>12 else c for c in componentes['Componente']], rotation=45, ha='right')
ax2.legend()
ax2.grid(True, alpha=0.3)


# Gráfico 3: CTE Política A por estación
ax3 = axes[1, 0]
categorias = ['PICO\nPol.A', 'NORMAL\nPol.A']
valores_a = [cte_pico_total, cte_normal_total]
colores = ['coral', 'steelblue']
bars = ax3.bar(categorias, valores_a, color=colores)
ax3.set_ylabel('CTE ($)')
ax3.set_title('Costo Total por Estación (Política A)')
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
for bar, val in zip(bars, valores_a):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, 
             f'${val/1000:.1f}K', ha='center', fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# Gráfico 4: Resumen total Política A
ax4 = axes[1, 1]
labels = ['EOQ Estacional\nPolítica A']
valores_total_a = [cte_anual_estacional]
colores_total = ['forestgreen']
bars = ax4.bar(labels, valores_total_a, color=colores_total)
ax4.set_ylabel('CTE Total Anual ($)')
ax4.set_title('Comparación de Modelos')
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
for bar, val in zip(bars, valores_total_a):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500, 
             f'${val:,.0f}'.replace(',', '.'), ha='center', fontsize=10, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
output_path = os.path.join(output_dir, 'eoq_estacional_comparacion.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"[OK] Gráfico guardado: {output_path}")
plt.close()

print("\n" + "="*70)
print("Fin del análisis EOQ Estacional")
print("="*70)
