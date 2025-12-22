# EOQ ESTACIONAL - POLÍTICAS DE INVENTARIO
# ----------------------------------------
# Modelo EOQ adaptado para demanda estacional (CV < 0.20 por temporada).
# Basado en Winston, pág. 872-873.
# - Estación PICO: Oct-Nov (CV = 0.0919 < 0.20)
# - Estación NORMAL: Resto del año (CV = 0.0716 < 0.20)
# - Recomendado cuando el CV anual >= 0.20.
# Entradas: outputs/forecast/prophet_forecast.csv
# Salidas:  outputs/inventory/eoq_estacional_*.csv, eoq_estacional_*.png


import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# --- Manejo de argumentos para definir 'modo' ---
if len(sys.argv) > 2 and sys.argv[1] == '--modo':
    modo = sys.argv[2].lower()
    if modo not in ['costo', 'servicio']:
        print("Error: El modo debe ser 'costo' o 'servicio'.")
        sys.exit(1)
else:
    print("Uso: python eoq_estacional.py --modo [costo|servicio]")
    sys.exit(1)

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
    
    if modo == 'servicio':
        # --- EOQ anual único ---
        # Demanda mensual de cada componente (12 meses)
        mask_clasico = (row['Auto_Foco'] == 'Clásico')
        mask_vintage = (row['Auto_Foco'] == 'Vintage')
        mask_ambos = (row['Auto_Foco'] == 'Ambos')
        if mask_clasico:
            demanda_mensual = df_pronostico['Autos_Clasicos'] * row['Uso_por_Auto']
        elif mask_vintage:
            demanda_mensual = df_pronostico['Autos_Vintage'] * row['Uso_por_Auto']
        elif mask_ambos:
            demanda_mensual = (df_pronostico['Autos_Clasicos'] + df_pronostico['Autos_Vintage']) * row['Uso_por_Auto']
        else:
            demanda_mensual = pd.Series([0]*12)
        D_anual = demanda_mensual.sum()
        sigma_mensual = demanda_mensual.std(ddof=0)
        Q = calcular_eoq(D_anual, COSTO_ORDENAR, H)
        N = D_anual / Q if Q > 0 else 0
        # Para cada estación, calcular demanda y SS usando sigma_mensual de la estación
        for estacion, meses_estacion, fraccion, nombre_estacion in [
            ('PICO', MESES_PICO, FRACCION_PICO, 'PICO'),
            ('NORMAL', MESES_NORMAL, FRACCION_NORMAL, 'NORMAL')]:
            D_est = demanda_mensual[df_pronostico['Mes'].isin(meses_estacion)].sum()
            semanas_est = len(meses_estacion) * SEMANAS_POR_MES
            demanda_semanal_est = D_est / semanas_est if semanas_est > 0 else 0
            # Lead time en meses
            L_meses = L / SEMANAS_POR_MES
            # Calcular sigma_mensual solo con los meses de la estación
            demanda_mensual_est = demanda_mensual[df_pronostico['Mes'].isin(meses_estacion)]
            if len(demanda_mensual_est) < 2:
                print(f"[ADVERTENCIA] Solo hay {len(demanda_mensual_est)} mes(es) en la estación {nombre_estacion} para el componente {row['Componente']}. No se puede calcular sigma_mensual correctamente.")
                sigma_mensual_est = float('nan')
            else:
                sigma_mensual_est = demanda_mensual_est.std(ddof=0)
            # Stock de seguridad específico por estación
            sigma_L = sigma_mensual_est * np.sqrt(L_meses)
            SS = Z_ALPHA * sigma_L
            # ROP
            ROP = demanda_semanal_est * L + SS
            # Tiempo entre pedidos
            tiempo_entre_pedidos = semanas_est / N if N > 0 else np.nan
            # Costo total: el costo de mantener el SS debe ser anual (H), no fraccionado
            CTE = (D_est / Q) * COSTO_ORDENAR + (Q / 2) * H * fraccion + SS * H + 0  # +0 para mantener formato
            resultados = resultados_pico if estacion == 'PICO' else resultados_normal
            resultados.append({
                'Componente': row['Componente'],
                'Estacion': nombre_estacion,
                'Demanda_Estacion': D_est,
                'EOQ': Q,
                'Num_Pedidos': N,
                'Tiempo_Entre_Pedidos_Semanas': tiempo_entre_pedidos,
                'Tiempo_Entre_Pedidos_Dias': tiempo_entre_pedidos * 7 if not np.isnan(tiempo_entre_pedidos) else np.nan,
                'ROP': ROP,
                'CTE': CTE,
                'Costo_Unitario': C,
                'Stock_Seguridad': SS,
                'sigma_mensual': sigma_mensual_est
            })
    else:
        # --- ESTACIÓN PICO ---
        D_pico = calcular_demanda_componente_estacion(row, demanda_pico_clasicos, demanda_pico_vintage)
        Q_pico = calcular_eoq(D_pico, COSTO_ORDENAR, H)
        N_pico = D_pico / Q_pico if Q_pico > 0 else 0
        CTE_pico = calcular_costo_total(D_pico, Q_pico, COSTO_ORDENAR, H * FRACCION_PICO)
        semanas_pico = MESES_EN_PICO * SEMANAS_POR_MES
        demanda_semanal_pico = D_pico / semanas_pico if semanas_pico > 0 else 0
        ROP_pico = demanda_semanal_pico * L
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

# Exportar resultados únicos por modo
df_pico = pd.DataFrame(resultados_pico)
df_normal = pd.DataFrame(resultados_normal)
df_pico.to_csv(os.path.join(output_dir, f'eoq_estacional_pico_{modo}.csv'), index=False)
df_normal.to_csv(os.path.join(output_dir, f'eoq_estacional_normal_{modo}.csv'), index=False)

# Exportar resumen por modo
df_resumen = df_pico[['Componente','CTE','CT_Optimo']].copy()
df_resumen = df_resumen.rename(columns={'CTE':'CTE_PICO','CT_Optimo':'CT_Optimo_PICO'})
df_resumen = df_resumen.merge(
    df_normal[['Componente','CTE','CT_Optimo']].rename(columns={'CTE':'CTE_NORMAL','CT_Optimo':'CT_Optimo_NORMAL'}),
    on='Componente', how='outer')
df_resumen['CTE_TOTAL'] = df_resumen['CTE_PICO'].fillna(0) + df_resumen['CTE_NORMAL'].fillna(0)
df_resumen['CT_Optimo_TOTAL'] = df_resumen['CT_Optimo_PICO'].fillna(0) + df_resumen['CT_Optimo_NORMAL'].fillna(0)
total_row = {col: '' for col in df_resumen.columns}
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    total_row[col] = df_resumen[col].sum()
total_row['Componente'] = 'TOTAL'
df_resumen = pd.concat([df_resumen, pd.DataFrame([total_row])], ignore_index=True)
for col in ['CTE_PICO','CT_Optimo_PICO','CTE_NORMAL','CT_Optimo_NORMAL','CTE_TOTAL','CT_Optimo_TOTAL']:
    df_resumen[col] = pd.to_numeric(df_resumen[col], errors='coerce').round(4)
df_resumen.to_csv(os.path.join(output_dir, f'eoq_estacional_resumen_{modo}.csv'), index=False)

# Calcular totales para gráficos
cte_pico_total = df_pico['CTE'].sum()
cte_normal_total = df_normal['CTE'].sum()
cte_anual_estacional = cte_pico_total + cte_normal_total


# === 11. TABLA DE VALORES CLAVE POR COMPONENTE Y ESTACIÓN ===
import tabulate
print("\n" + "="*70)
print("TABLA DE VALORES CLAVE POR COMPONENTE Y ESTACIÓN")
print("="*70)

tabla = []
columnas = [
    "Componente", "Estacion", "Demanda_Estacion", "EOQ", "Num_Pedidos", "Lead_Time_Semanas",
    "ROP", "Stock_Seguridad", "sigma_mensual", "fraccion", "CTE", "CT_Optimo"
]


# Usar el sigma_mensual y fraccion almacenados en cada resultado por estación
for df in [df_pico, df_normal]:
    for idx, row in df.iterrows():
        comp = row['Componente']
        lead_time = componentes[componentes['Componente'] == comp]['Lead_Time_Semanas'].values[0]
        ss = row['Stock_Seguridad'] if 'Stock_Seguridad' in row else 0
        fraccion = row['fraccion'] if 'fraccion' in row else (FRACCION_PICO if row['Estacion'] == 'PICO' else FRACCION_NORMAL)
        sigma_mensual = row['sigma_mensual'] if 'sigma_mensual' in row else np.nan
        tabla.append([
            comp,
            row['Estacion'],
            row['Demanda_Estacion'],
            row['EOQ'],
            row['Num_Pedidos'],
            lead_time,
            row['ROP'],
            ss,
            sigma_mensual,
            fraccion,
            row['CTE'],
            row['CT_Optimo']
        ])

try:
    from tabulate import tabulate as tabulate_func
except ImportError:
    def tabulate_func(data, headers, floatfmt):
        # Fallback simple si no está tabulate
        header_line = " | ".join(headers)
        lines = [header_line, "-"*len(header_line)]
        for row in data:
            lines.append(" | ".join([f"{x:.2f}" if isinstance(x, float) else str(x) for x in row]))
        return "\n".join(lines)


# Exportar la tabla de valores clave a un CSV
tabla_df = pd.DataFrame(tabla, columns=columnas)
# Redondear todas las columnas numéricas a 4 decimales
for col in tabla_df.columns:
    if pd.api.types.is_numeric_dtype(tabla_df[col]):
        tabla_df[col] = tabla_df[col].round(4)
tabla_csv_path = os.path.join(output_dir, 'tabla_valores_clave.csv')
tabla_df.to_csv(tabla_csv_path, index=False)
print(f"\n[OK] Tabla de valores clave exportada a: {tabla_csv_path}\n")
print(tabulate_func(tabla, columnas, floatfmt=".4f"))

print(f"\nResultados EOQ estacional ({modo}) exportados a: {output_dir}\n")
print(df_pico.head())
print(df_normal.head())
print(df_resumen.head())

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
