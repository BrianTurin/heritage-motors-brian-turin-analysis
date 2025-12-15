# ============================
# POLÍTICAS DE INVENTARIO - EOQ ESTACIONAL
# Cantidad Económica de Pedido por Temporadas
# ============================
# Basado en análisis de CV (Winston, pág. 872-873)
# Estación PICO: Oct-Nov (CV = 0.0919 < 0.20) ✓
# Estación NORMAL: Resto del año (CV = 0.0716 < 0.20) ✓
# ============================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# === 1. CONFIGURACIÓN Y PARÁMETROS ===
print("="*70)
print("POLÍTICAS DE INVENTARIO - EOQ ESTACIONAL")
print("(Modelo ajustado por temporadas según CV)")
print("="*70)

# Parámetros de costos del TP
COSTO_ORDENAR = 300  # $ por orden de compra
TASA_MANTENIMIENTO = 0.20  # 20% del costo unitario anual
ALPHA = 0.05  # Nivel de significancia (95% nivel de servicio)
Z_ALPHA = stats.norm.ppf(1 - ALPHA)  # 1.645

print(f"\n--- Parámetros de Costos ---")
print(f"  Costo de ordenar (S):      ${COSTO_ORDENAR:,.2f} por orden".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  Tasa de mantenimiento:     {TASA_MANTENIMIENTO*100:.0f}% anual del costo unitario")
print(f"  Nivel de servicio (1-α):   {(1-ALPHA)*100:.0f}%")
print(f"  Z-score (α=0.05):          {Z_ALPHA:.4f}")

# === 2. CATÁLOGO DE COMPONENTES ===
componentes = pd.DataFrame({
    'Componente': [
        'Motor de Alto Rendimiento V8',
        'Motor de Cilindros en Línea Raro',
        'Carrocería Artesanal de Época',
        'Carrocería Estándar (Fibra)',
        'Transmisión de 5 Velocidades',
        'Sistema de Inyección Electrónica',
        'Set de Carburadores Dobles',
        'Tapicería de Cuero Premium',
        'Juego de Llantas Vintage Espec.',
        'Llantas Regulares Cromados',
        'Cubiertas de Alta Gama (Neumáticos)'
    ],
    'Auto_Foco': [
        'Clásico', 'Vintage', 'Vintage', 'Clásico', 'Ambos',
        'Clásico', 'Vintage', 'Ambos', 'Vintage', 'Clásico', 'Ambos'
    ],
    'Costo_Unitario': [
        9000, 12000, 15000, 6500, 3500, 
        1200, 900, 4000, 2500, 400, 250
    ],
    'Uso_por_Auto': [
        1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4
    ],
    'Volumen_m3': [
        0.8, 0.9, 4.0, 3.5, 0.4, 0.1, 0.1, 0.5, 0.15, 0.1, 0.1
    ],
    'Lead_Time_Semanas': [
        6, 12, 10, 4, 4, 3, 5, 8, 5, 2, 2
    ]
})

# === 3. CARGAR Y SEGMENTAR PRONÓSTICO PROPHET ===
print("\n--- Cargando y segmentando pronóstico Prophet ---")

script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..'))

prophet_results_path = os.path.join(project_root, 'ForecastModels', 'Prophet', 'prophet_results.csv')
prophet_forecast_path = os.path.join(project_root, 'ForecastModels', 'Prophet', 'prophet_forecast.csv')

if not os.path.exists(prophet_results_path):
    raise SystemExit(f"Error: No se encontró {prophet_results_path}")

df_historico = pd.read_csv(prophet_results_path)
df_pronostico = pd.read_csv(prophet_forecast_path)

# Función para calcular CV
def calcular_cv(datos):
    datos = np.array(datos)
    d_prom = np.mean(datos)
    var_est = np.mean(datos**2) - d_prom**2
    return var_est / (d_prom**2) if d_prom > 0 else float('inf')

# Extraer mes de cada período
df_pronostico['Mes'] = pd.to_datetime(df_pronostico['Periodo']).dt.month

# Definir estaciones según análisis de CV
# PICO: Octubre (10) y Noviembre (11) - demanda alta
# NORMAL: Resto del año
MESES_PICO = [10, 11]
MESES_NORMAL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12]

# Segmentar pronósticos
mask_pico = df_pronostico['Mes'].isin(MESES_PICO)
mask_normal = df_pronostico['Mes'].isin(MESES_NORMAL)

demanda_pico = df_pronostico[mask_pico]['Pronostico'].values
demanda_normal = df_pronostico[mask_normal]['Pronostico'].values

# Calcular CV por estación
cv_pico = calcular_cv(demanda_pico)
cv_normal = calcular_cv(demanda_normal)

print("\n" + "="*70)
print("VALIDACIÓN DE CV POR ESTACIÓN (Winston, pág. 872)")
print("="*70)

print(f"\n  ESTACIÓN PICO (Oct-Nov):")
print(f"    Meses: {MESES_PICO}")
print(f"    Demandas: {[f'${d:,.0f}'.replace(',', '.') for d in demanda_pico]}")
print(f"    CV = {cv_pico:.4f} {'✓ EOQ válido' if cv_pico < 0.20 else '✗ CV alto'}")

print(f"\n  ESTACIÓN NORMAL (resto):")
print(f"    Meses: {MESES_NORMAL}")
print(f"    CV = {cv_normal:.4f} {'✓ EOQ válido' if cv_normal < 0.20 else '✗ CV alto'}")

# Verificar que ambas estaciones tienen CV < 0.20
if cv_pico >= 0.20 or cv_normal >= 0.20:
    print("\n  ⚠️ ADVERTENCIA: Alguna estación tiene CV ≥ 0.20")
    print("     Considerar métodos alternativos (Silver-Meal)")
else:
    print("\n  ✓ Ambas estaciones tienen CV < 0.20")
    print("    EOQ es válido para cada estación según Winston")

# === 4. CALCULAR DEMANDA ANUALIZADA POR ESTACIÓN ===
print("\n" + "="*70)
print("CÁLCULO DE DEMANDA POR ESTACIÓN")
print("="*70)

# Duración de cada estación (en meses y fracción del año)
MESES_EN_PICO = len(MESES_PICO)  # 2 meses
MESES_EN_NORMAL = len(MESES_NORMAL)  # 10 meses

FRACCION_PICO = MESES_EN_PICO / 12  # 2/12 = 0.167
FRACCION_NORMAL = MESES_EN_NORMAL / 12  # 10/12 = 0.833

# Demanda total por estación (del pronóstico de 12 meses)
demanda_total_pico = demanda_pico.sum()
demanda_total_normal = demanda_normal.sum()
demanda_total_anual = demanda_total_pico + demanda_total_normal

# Demanda mensual promedio por estación
demanda_mensual_pico = np.mean(demanda_pico)
demanda_mensual_normal = np.mean(demanda_normal)

print(f"\n  ESTACIÓN PICO ({MESES_EN_PICO} meses = {FRACCION_PICO*100:.1f}% del año):")
print(f"    Demanda total:          ${demanda_total_pico:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Demanda mensual prom:   ${demanda_mensual_pico:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n  ESTACIÓN NORMAL ({MESES_EN_NORMAL} meses = {FRACCION_NORMAL*100:.1f}% del año):")
print(f"    Demanda total:          ${demanda_total_normal:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Demanda mensual prom:   ${demanda_mensual_normal:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n  TOTAL ANUAL:              ${demanda_total_anual:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 5. PROPORCIONES Y UNIDADES ===
PROPORCION_CLASSIC = 0.65
PROPORCION_VINTAGE = 0.35
PRECIO_PROMEDIO_AUTO = 3500

# Unidades por estación
unidades_pico_total = demanda_total_pico / PRECIO_PROMEDIO_AUTO
unidades_normal_total = demanda_total_normal / PRECIO_PROMEDIO_AUTO

unidades_pico_classic = unidades_pico_total * PROPORCION_CLASSIC
unidades_pico_vintage = unidades_pico_total * PROPORCION_VINTAGE
unidades_normal_classic = unidades_normal_total * PROPORCION_CLASSIC
unidades_normal_vintage = unidades_normal_total * PROPORCION_VINTAGE

print(f"\n  Unidades estimadas PICO:    {unidades_pico_total:>10,.0f} ({unidades_pico_classic:,.0f} Classic, {unidades_pico_vintage:,.0f} Vintage)".replace(',', '.'))
print(f"  Unidades estimadas NORMAL:  {unidades_normal_total:>10,.0f} ({unidades_normal_classic:,.0f} Classic, {unidades_normal_vintage:,.0f} Vintage)".replace(',', '.'))

# === 6. FUNCIONES EOQ ===
def calcular_eoq(D, S, H):
    """EOQ = √(2DS/H)"""
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

def calcular_demanda_componente_estacion(row, unidades_total, unidades_classic, unidades_vintage):
    """Calcula demanda de componente para una estación"""
    if row['Auto_Foco'] == 'Clásico':
        return unidades_classic * row['Uso_por_Auto']
    elif row['Auto_Foco'] == 'Vintage':
        return unidades_vintage * row['Uso_por_Auto']
    else:  # Ambos
        return unidades_total * row['Uso_por_Auto']

# Calcular demanda por componente para cada estación
resultados_pico = []
resultados_normal = []

for idx, row in componentes.iterrows():
    C = row['Costo_Unitario']
    H = C * TASA_MANTENIMIENTO  # Anual
    L = row['Lead_Time_Semanas']
    
    # --- ESTACIÓN PICO ---
    D_pico = calcular_demanda_componente_estacion(
        row, unidades_pico_total, unidades_pico_classic, unidades_pico_vintage
    )
    
    # Anualizar la demanda de la estación pico para calcular EOQ
    # (D_pico es la demanda de 2 meses, anualizamos para usar fórmula EOQ)
    D_pico_anualizado = D_pico * (12 / MESES_EN_PICO)
    
    # EOQ con demanda anualizada
    Q_pico = calcular_eoq(D_pico_anualizado, COSTO_ORDENAR, H)
    
    # Número de pedidos durante la estación pico
    N_pico = D_pico / Q_pico if Q_pico > 0 else 0
    
    # Costo durante estación pico (proporcional)
    # Usamos D_pico (real) no anualizado para el costo
    CTE_pico = calcular_costo_total(D_pico, Q_pico, COSTO_ORDENAR, H * FRACCION_PICO)
    
    # Demanda semanal y ROP
    semanas_pico = MESES_EN_PICO * SEMANAS_POR_MES
    demanda_semanal_pico = D_pico / semanas_pico if semanas_pico > 0 else 0
    ROP_pico = demanda_semanal_pico * L
    
    resultados_pico.append({
        'Componente': row['Componente'],
        'Estacion': 'PICO',
        'Demanda_Estacion': D_pico,
        'Demanda_Anualizada': D_pico_anualizado,
        'EOQ': Q_pico,
        'Num_Pedidos': N_pico,
        'ROP': ROP_pico,
        'CTE': CTE_pico,
        'Costo_Unitario': C
    })
    
    # --- ESTACIÓN NORMAL ---
    D_normal = calcular_demanda_componente_estacion(
        row, unidades_normal_total, unidades_normal_classic, unidades_normal_vintage
    )
    
    # Anualizar
    D_normal_anualizado = D_normal * (12 / MESES_EN_NORMAL)
    
    Q_normal = calcular_eoq(D_normal_anualizado, COSTO_ORDENAR, H)
    N_normal = D_normal / Q_normal if Q_normal > 0 else 0
    CTE_normal = calcular_costo_total(D_normal, Q_normal, COSTO_ORDENAR, H * FRACCION_NORMAL)
    
    semanas_normal = MESES_EN_NORMAL * SEMANAS_POR_MES
    demanda_semanal_normal = D_normal / semanas_normal if semanas_normal > 0 else 0
    ROP_normal = demanda_semanal_normal * L
    
    resultados_normal.append({
        'Componente': row['Componente'],
        'Estacion': 'NORMAL',
        'Demanda_Estacion': D_normal,
        'Demanda_Anualizada': D_normal_anualizado,
        'EOQ': Q_normal,
        'Num_Pedidos': N_normal,
        'ROP': ROP_normal,
        'CTE': CTE_normal,
        'Costo_Unitario': C
    })

df_pico = pd.DataFrame(resultados_pico)
df_normal = pd.DataFrame(resultados_normal)

# Mostrar resultados PICO
print(f"\n--- ESTACIÓN PICO (Oct-Nov, {MESES_EN_PICO} meses) ---")
print(f"  Demanda anualizada para cálculo EOQ (ajustada por duración)")
print(f"\n{'Componente':<35} {'D estac.':<12} {'D anual.':<12} {'EOQ':<10} {'N ped.':<8} {'CTE ($)':<12}")
print("-" * 89)

for idx, row in df_pico.iterrows():
    print(f"{row['Componente']:<35} {row['Demanda_Estacion']:>10,.1f} {row['Demanda_Anualizada']:>10,.1f} {row['EOQ']:>10,.1f} {row['Num_Pedidos']:>7,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_pico_total = df_pico['CTE'].sum()
print(f"\n{'CTE TOTAL ESTACIÓN PICO:':<55} ${cte_pico_total:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Mostrar resultados NORMAL
print(f"\n--- ESTACIÓN NORMAL (resto, {MESES_EN_NORMAL} meses) ---")
print(f"\n{'Componente':<35} {'D estac.':<12} {'D anual.':<12} {'EOQ':<10} {'N ped.':<8} {'CTE ($)':<12}")
print("-" * 89)

for idx, row in df_normal.iterrows():
    print(f"{row['Componente']:<35} {row['Demanda_Estacion']:>10,.1f} {row['Demanda_Anualizada']:>10,.1f} {row['EOQ']:>10,.1f} {row['Num_Pedidos']:>7,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_normal_total = df_normal['CTE'].sum()
print(f"\n{'CTE TOTAL ESTACIÓN NORMAL:':<55} ${cte_normal_total:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_anual_estacional = cte_pico_total + cte_normal_total
print(f"\n{'CTE TOTAL ANUAL (PICO + NORMAL):':<55} ${cte_anual_estacional:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 8. COMPARACIÓN CON EOQ SIN ESTACIONALIDAD ===
print("\n" + "="*70)
print("COMPARACIÓN: EOQ ESTACIONAL vs EOQ CLÁSICO")
print("="*70)

# Cargar resultados del EOQ clásico si existen
politica_a_path = os.path.join(script_dir, 'politica_a_resultados.csv')
if os.path.exists(politica_a_path):
    df_clasico = pd.read_csv(politica_a_path)
    cte_clasico_total = df_clasico['CTE'].sum()
    
    diferencia = cte_anual_estacional - cte_clasico_total
    porcentaje = (diferencia / cte_clasico_total) * 100
    
    print(f"\n  {'Modelo':<35} {'CTE Total ($)':<20}")
    print("-" * 55)
    print(f"  {'EOQ Clásico (demanda constante)':<35} ${cte_clasico_total:>18,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  {'EOQ Estacional (PICO + NORMAL)':<35} ${cte_anual_estacional:>18,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  {'Diferencia':<35} ${diferencia:>18,.2f} ({porcentaje:>+.2f}%)".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    print(f"\n  Nota: El EOQ estacional ajusta las cantidades de pedido según")
    print(f"        la demanda real de cada temporada, cumpliendo con CV < 0.20")
else:
    print("\n  ⚠️ No se encontró archivo de EOQ clásico para comparar")
    print(f"     CTE Estacional calculado: ${cte_anual_estacional:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 9. POLÍTICA B - CON STOCK DE SEGURIDAD ===
print("\n" + "="*70)
print("EOQ ESTACIONAL - POLÍTICA B (Nivel de Servicio 95%)")
print("="*70)

# Desviación estándar del error de pronóstico
desv_error_mensual = df_historico['Residuos'].std()

resultados_pico_b = []
resultados_normal_b = []

for idx, row in componentes.iterrows():
    C = row['Costo_Unitario']
    H = C * TASA_MANTENIMIENTO
    L = row['Lead_Time_Semanas']
    
    # Desviación proporcional a la demanda del componente
    # (simplificación: usamos la misma desv. para ambas estaciones ajustada)
    
    # --- ESTACIÓN PICO ---
    D_pico = calcular_demanda_componente_estacion(
        row, unidades_pico_total, unidades_pico_classic, unidades_pico_vintage
    )
    D_pico_anualizado = D_pico * (12 / MESES_EN_PICO)
    Q_pico = calcular_eoq(D_pico_anualizado, COSTO_ORDENAR, H)
    
    # Stock de seguridad basado en desviación durante lead time
    semanas_pico = MESES_EN_PICO * SEMANAS_POR_MES
    demanda_semanal_pico = D_pico / semanas_pico if semanas_pico > 0 else 0
    
    # Proporción de demanda del componente
    proporcion = D_pico / unidades_pico_total if unidades_pico_total > 0 else 0
    desv_semanal = (desv_error_mensual / PRECIO_PROMEDIO_AUTO / SEMANAS_POR_MES) * proporcion * row['Uso_por_Auto']
    sigma_lt_pico = desv_semanal * np.sqrt(L)
    SS_pico = Z_ALPHA * sigma_lt_pico
    
    ROP_pico = demanda_semanal_pico * L + SS_pico
    N_pico = D_pico / Q_pico if Q_pico > 0 else 0
    CTE_pico = calcular_costo_total(D_pico, Q_pico, COSTO_ORDENAR, H * FRACCION_PICO, SS_pico)
    
    resultados_pico_b.append({
        'Componente': row['Componente'],
        'Estacion': 'PICO',
        'Demanda_Estacion': D_pico,
        'EOQ': Q_pico,
        'Stock_Seguridad': SS_pico,
        'ROP': ROP_pico,
        'CTE': CTE_pico
    })
    
    # --- ESTACIÓN NORMAL ---
    D_normal = calcular_demanda_componente_estacion(
        row, unidades_normal_total, unidades_normal_classic, unidades_normal_vintage
    )
    D_normal_anualizado = D_normal * (12 / MESES_EN_NORMAL)
    Q_normal = calcular_eoq(D_normal_anualizado, COSTO_ORDENAR, H)
    
    semanas_normal = MESES_EN_NORMAL * SEMANAS_POR_MES
    demanda_semanal_normal = D_normal / semanas_normal if semanas_normal > 0 else 0
    
    proporcion_n = D_normal / unidades_normal_total if unidades_normal_total > 0 else 0
    desv_semanal_n = (desv_error_mensual / PRECIO_PROMEDIO_AUTO / SEMANAS_POR_MES) * proporcion_n * row['Uso_por_Auto']
    sigma_lt_normal = desv_semanal_n * np.sqrt(L)
    SS_normal = Z_ALPHA * sigma_lt_normal
    
    ROP_normal = demanda_semanal_normal * L + SS_normal
    N_normal = D_normal / Q_normal if Q_normal > 0 else 0
    CTE_normal = calcular_costo_total(D_normal, Q_normal, COSTO_ORDENAR, H * FRACCION_NORMAL, SS_normal)
    
    resultados_normal_b.append({
        'Componente': row['Componente'],
        'Estacion': 'NORMAL',
        'Demanda_Estacion': D_normal,
        'EOQ': Q_normal,
        'Stock_Seguridad': SS_normal,
        'ROP': ROP_normal,
        'CTE': CTE_normal
    })

df_pico_b = pd.DataFrame(resultados_pico_b)
df_normal_b = pd.DataFrame(resultados_normal_b)

# Mostrar resultados Política B
print(f"\n--- POLÍTICA B: ESTACIÓN PICO con Stock de Seguridad ---")
print(f"\n{'Componente':<35} {'EOQ':<10} {'SS':<10} {'ROP':<10} {'CTE ($)':<12}")
print("-" * 77)

for idx, row in df_pico_b.iterrows():
    print(f"{row['Componente']:<35} {row['EOQ']:>10,.1f} {row['Stock_Seguridad']:>10,.1f} {row['ROP']:>10,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_pico_b = df_pico_b['CTE'].sum()
print(f"\n{'CTE PICO (Política B):':<55} ${cte_pico_b:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n--- POLÍTICA B: ESTACIÓN NORMAL con Stock de Seguridad ---")
print(f"\n{'Componente':<35} {'EOQ':<10} {'SS':<10} {'ROP':<10} {'CTE ($)':<12}")
print("-" * 77)

for idx, row in df_normal_b.iterrows():
    print(f"{row['Componente']:<35} {row['EOQ']:>10,.1f} {row['Stock_Seguridad']:>10,.1f} {row['ROP']:>10,.1f} {row['CTE']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_normal_b = df_normal_b['CTE'].sum()
print(f"\n{'CTE NORMAL (Política B):':<55} ${cte_normal_b:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_anual_b = cte_pico_b + cte_normal_b
print(f"\n{'CTE TOTAL ANUAL - POLÍTICA B:':<55} ${cte_anual_b:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 10. RESUMEN COMPARATIVO ===
print("\n" + "="*70)
print("RESUMEN COMPARATIVO - TODAS LAS POLÍTICAS")
print("="*70)

print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║              EOQ ESTACIONAL (CV validado por Winston)                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ESTACIÓN PICO (Oct-Nov, 2 meses)                                      ║
║    CV = {cv_pico:.4f} < 0.20 ✓                                               ║
║    Política A (sin SS):  ${cte_pico_total:>12,.2f}                            ║
║    Política B (con SS):  ${cte_pico_b:>12,.2f}                            ║
║                                                                        ║
║  ESTACIÓN NORMAL (resto, 10 meses)                                     ║
║    CV = {cv_normal:.4f} < 0.20 ✓                                               ║
║    Política A (sin SS):  ${cte_normal_total:>12,.2f}                            ║
║    Política B (con SS):  ${cte_normal_b:>12,.2f}                            ║
║                                                                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║  TOTALES ANUALES                                                       ║
║    Política A Estacional:  ${cte_anual_estacional:>12,.2f}                            ║
║    Política B Estacional:  ${cte_anual_b:>12,.2f}                            ║
╚═══════════════════════════════════════════════════════════════════════╝
""".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 11. EXPORTAR RESULTADOS ===
print("\n--- Exportando resultados ---")

# Guardar resultados por estación
df_pico.to_csv(os.path.join(script_dir, 'eoq_estacional_pico_a.csv'), index=False)
df_normal.to_csv(os.path.join(script_dir, 'eoq_estacional_normal_a.csv'), index=False)
df_pico_b.to_csv(os.path.join(script_dir, 'eoq_estacional_pico_b.csv'), index=False)
df_normal_b.to_csv(os.path.join(script_dir, 'eoq_estacional_normal_b.csv'), index=False)

print(f"✓ Exportados: eoq_estacional_pico_a.csv, eoq_estacional_normal_a.csv")
print(f"✓ Exportados: eoq_estacional_pico_b.csv, eoq_estacional_normal_b.csv")

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

# Gráfico 3: Comparación CTE Política A vs B
ax3 = axes[1, 0]
categorias = ['PICO\nPol.A', 'PICO\nPol.B', 'NORMAL\nPol.A', 'NORMAL\nPol.B']
valores = [cte_pico_total, cte_pico_b, cte_normal_total, cte_normal_b]
colores = ['coral', 'lightcoral', 'steelblue', 'lightsteelblue']
bars = ax3.bar(categorias, valores, color=colores)
ax3.set_ylabel('CTE ($)')
ax3.set_title('Costo Total por Estación y Política')
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
for bar, val in zip(bars, valores):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, 
             f'${val/1000:.1f}K', ha='center', fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# Gráfico 4: Resumen total
ax4 = axes[1, 1]
labels = ['EOQ Estacional\nPolítica A', 'EOQ Estacional\nPolítica B']
valores_total = [cte_anual_estacional, cte_anual_b]

# Si existe EOQ clásico, agregarlo
if os.path.exists(politica_a_path):
    labels.insert(0, 'EOQ Clásico\n(sin estaciones)')
    valores_total.insert(0, cte_clasico_total)
    colores_total = ['gray', 'forestgreen', 'darkgreen']
else:
    colores_total = ['forestgreen', 'darkgreen']

bars = ax4.bar(labels, valores_total, color=colores_total)
ax4.set_ylabel('CTE Total Anual ($)')
ax4.set_title('Comparación de Modelos')
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
for bar, val in zip(bars, valores_total):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500, 
             f'${val:,.0f}'.replace(',', '.'), ha='center', fontsize=10, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
output_path = os.path.join(script_dir, 'eoq_estacional_comparacion.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ Gráfico guardado: {output_path}")
plt.close()

print("\n" + "="*70)
print("Fin del análisis EOQ Estacional")
print("="*70)
