# ============================
# POLÍTICAS DE INVENTARIO - EOQ
# Cantidad Económica de Pedido
# ============================
# Política A: Óptima por Costos
# Política B: Basada en Nivel de Servicio (α = 0.05)
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
print("POLÍTICAS DE INVENTARIO - MODELO EOQ")
print("(Cantidad Económica de Pedido)")
print("="*70)

# Parámetros de costos del TP
COSTO_ORDENAR = 300  # $ por orden de compra
TASA_MANTENIMIENTO = 0.20  # 20% del costo unitario anual
ALPHA = 0.05  # Nivel de significancia (95% nivel de servicio)

# Z-score para nivel de servicio 95%
Z_ALPHA = stats.norm.ppf(1 - ALPHA)  # 1.645

print(f"\n--- Parámetros de Costos ---")
print(f"  Costo de ordenar (S):      ${COSTO_ORDENAR:,.2f} por orden".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  Tasa de mantenimiento:     {TASA_MANTENIMIENTO*100:.0f}% anual del costo unitario")
print(f"  Nivel de servicio (1-α):   {(1-ALPHA)*100:.0f}%")
print(f"  Z-score (α=0.05):          {Z_ALPHA:.4f}")

# === 2. CATÁLOGO DE COMPONENTES ===
# Datos del PDF del TP
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

print(f"\n--- Catálogo de Componentes ---")
print(componentes[['Componente', 'Auto_Foco', 'Costo_Unitario', 'Lead_Time_Semanas']].to_string(index=False))

# === 3. CARGAR PRONÓSTICO PROPHET ===
print("\n--- Cargando pronóstico Prophet ---")

script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..'))

# Cargar resultados históricos de Prophet
prophet_results_path = os.path.join(project_root, 'ForecastModels', 'Prophet', 'prophet_results.csv')
prophet_forecast_path = os.path.join(project_root, 'ForecastModels', 'Prophet', 'prophet_forecast.csv')

if not os.path.exists(prophet_results_path):
    raise SystemExit(f"Error: No se encontró {prophet_results_path}\nEjecuta primero: python ForecastModels/Prophet/prophet_forecast.py")

df_historico = pd.read_csv(prophet_results_path)
df_pronostico = pd.read_csv(prophet_forecast_path)

# Calcular métricas de demanda
demanda_mensual_promedio = df_historico['Ventas_Historicas'].mean()
demanda_anual = df_historico['Ventas_Historicas'].sum() / (len(df_historico) / 12)  # Anualizada
demanda_pronostico_anual = df_pronostico['Pronostico'].sum()

# Desviación estándar del error de pronóstico (para stock de seguridad)
desv_error_mensual = df_historico['Residuos'].std()

# Convertir a semanal (asumiendo 4.33 semanas por mes)
SEMANAS_POR_MES = 4.33
SEMANAS_POR_AÑO = 52

demanda_semanal_promedio = demanda_mensual_promedio / SEMANAS_POR_MES
desv_error_semanal = desv_error_mensual / np.sqrt(SEMANAS_POR_MES)

print(f"\n  Datos del pronóstico Prophet:")
print(f"    Periodos históricos:           {len(df_historico)} meses")
print(f"    Demanda mensual promedio:      ${demanda_mensual_promedio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Demanda anual estimada:        ${demanda_anual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Pronóstico próximos 12 meses:  ${demanda_pronostico_anual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Desv. estándar error mensual:  ${desv_error_mensual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Desv. estándar error semanal:  ${desv_error_semanal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === VALIDACIÓN: Coeficiente de Variabilidad (CV) ===
# Referencia: Winston - Investigación de Operaciones, pág. 872-873
# Método de Peterson y Silver (1998)
print("\n" + "="*70)
print("VALIDACIÓN: COEFICIENTE DE VARIABILIDAD (CV)")
print("Referencia: Winston - Inv. Operaciones, Cap. 15, pág. 872-873")
print("Método: Peterson y Silver (1998)")
print("="*70)

# Usar el pronóstico de 12 meses para calcular CV (demanda futura proyectada)
demandas_pronostico = df_pronostico['Pronostico'].values
n_periodos = len(demandas_pronostico)

# 1. Demanda promedio: d̄ = (1/n) * Σ d_i
d_promedio = np.mean(demandas_pronostico)

# 2. Varianza estimada: Var.Est.D = (1/n) * Σ d_i² - d̄²
var_est_d = np.mean(demandas_pronostico**2) - d_promedio**2

# 3. Coeficiente de Variabilidad: CV = Var.Est.D / d̄²
CV = var_est_d / (d_promedio**2)

print(f"\n  Cálculo del CV (usando pronóstico de {n_periodos} meses):")
print(f"    Demandas mensuales pronosticadas:")
for i, d in enumerate(demandas_pronostico):
    mes = df_pronostico['Periodo'].iloc[i][:7]
    print(f"      {mes}: ${d:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n    d̄ (demanda promedio):         ${d_promedio:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    Var.Est.D (varianza):          {var_est_d:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"    CV = Var.Est.D / d̄²:           {CV:>15.4f}")

print(f"\n  --- Regla de Decisión (Winston, pág. 872) ---")
if CV < 0.20:
    print(f"    CV = {CV:.4f} < 0.20")
    print(f"    RESULTADO: Es RAZONABLE usar modelo EOQ clásico")
    print(f"    La demanda es suficientemente estable.")
    EOQ_VALIDO = True
else:
    print(f"    CV = {CV:.4f} ≥ 0.20")
    print(f"    RESULTADO: La demanda es MUY IRREGULAR para EOQ clásico")
    print(f"    Winston recomienda: Silver-Meal o Wagner-Whitin (Cap. 18)")
    EOQ_VALIDO = False

# También calcular CV con datos históricos para comparar
demandas_historico = df_historico['Ventas_Historicas'].values
d_prom_hist = np.mean(demandas_historico)
var_est_hist = np.mean(demandas_historico**2) - d_prom_hist**2
CV_historico = var_est_hist / (d_prom_hist**2)

print(f"\n  --- Verificación con datos históricos ({len(demandas_historico)} meses) ---")
print(f"    CV histórico = {CV_historico:.4f}")
if CV_historico < 0.20:
    print(f"    Histórico también indica demanda estable")
else:
    print(f"    Histórico también indica alta variabilidad")

# === 4. PROPORCIONES DE VENTA POR TIPO DE AUTO ===
# Basado en análisis histórico del dataset
# Asumimos proporciones aproximadas del dataset original
PROPORCION_CLASSIC = 0.65  # 65% Classic Cars
PROPORCION_VINTAGE = 0.35  # 35% Vintage Cars

print(f"\n--- Proporciones de venta ---")
print(f"    Classic Cars:  {PROPORCION_CLASSIC*100:.0f}%")
print(f"    Vintage Cars:  {PROPORCION_VINTAGE*100:.0f}%")

# === 5. CÁLCULO DE DEMANDA POR COMPONENTE ===
print("\n--- Calculando demanda anual por componente ---")

# Precio promedio por auto (estimado del dataset ~$3,500 por unidad vendida en promedio)
PRECIO_PROMEDIO_AUTO = 3500

# Unidades vendidas estimadas anualmente
unidades_anuales_total = demanda_pronostico_anual / PRECIO_PROMEDIO_AUTO
unidades_classic = unidades_anuales_total * PROPORCION_CLASSIC
unidades_vintage = unidades_anuales_total * PROPORCION_VINTAGE

print(f"    Unidades totales estimadas (anual):  {unidades_anuales_total:,.0f}".replace(',', '.'))
print(f"    Unidades Classic Cars:               {unidades_classic:,.0f}".replace(',', '.'))
print(f"    Unidades Vintage Cars:               {unidades_vintage:,.0f}".replace(',', '.'))

# Calcular demanda anual de cada componente
def calcular_demanda_componente(row):
    """Calcula la demanda anual de un componente según su tipo de auto"""
    if row['Auto_Foco'] == 'Clásico':
        return unidades_classic * row['Uso_por_Auto']
    elif row['Auto_Foco'] == 'Vintage':
        return unidades_vintage * row['Uso_por_Auto']
    else:  # Ambos
        return unidades_anuales_total * row['Uso_por_Auto']

componentes['Demanda_Anual'] = componentes.apply(calcular_demanda_componente, axis=1)

# Calcular desviación estándar de demanda durante lead time
# σ_LT = σ_semanal * √L
def calcular_desv_lead_time(row):
    """Calcula la desviación estándar de la demanda durante el lead time"""
    # Desviación proporcional a la demanda del componente
    proporcion_demanda = row['Demanda_Anual'] / unidades_anuales_total
    desv_demanda_semanal = (desv_error_semanal / PRECIO_PROMEDIO_AUTO) * proporcion_demanda * row['Uso_por_Auto']
    return desv_demanda_semanal * np.sqrt(row['Lead_Time_Semanas'])

componentes['Desv_Lead_Time'] = componentes.apply(calcular_desv_lead_time, axis=1)

# === 6. MODELO EOQ - POLÍTICA A (ÓPTIMA POR COSTOS) ===
print("\n" + "="*70)
print("POLÍTICA A: ÓPTIMA POR COSTOS (EOQ Clásico)")
print("="*70)

def calcular_eoq(D, S, H):
    """
    Calcula la Cantidad Económica de Pedido (EOQ)
    D: Demanda anual
    S: Costo de ordenar
    H: Costo de mantener por unidad por año
    
    EOQ = √(2DS/H)
    """
    return np.sqrt((2 * D * S) / H)

def calcular_costo_total_politica_a(D, Q, S, H):
    """
    Calcula el Costo Total Esperado (CTE) para Política A
    CTE = (D/Q)*S + (Q/2)*H
    """
    costo_ordenar = (D / Q) * S
    costo_mantener = (Q / 2) * H
    return costo_ordenar + costo_mantener

# Calcular EOQ y costos para cada componente
resultados_politica_a = []

for idx, row in componentes.iterrows():
    D = row['Demanda_Anual']  # Demanda anual
    C = row['Costo_Unitario']  # Costo unitario
    H = C * TASA_MANTENIMIENTO  # Costo de mantener
    L = row['Lead_Time_Semanas']  # Lead time en semanas
    
    # EOQ
    Q_optimo = calcular_eoq(D, COSTO_ORDENAR, H)
    
    # Número de pedidos por año
    N = D / Q_optimo
    
    # Tiempo entre pedidos (semanas)
    T = SEMANAS_POR_AÑO / N
    
    # Punto de reorden (ROP) = Demanda durante lead time
    demanda_semanal = D / SEMANAS_POR_AÑO
    ROP = demanda_semanal * L
    
    # Inventario promedio
    inv_promedio = Q_optimo / 2
    
    # Inventario máximo
    inv_maximo = Q_optimo
    
    # Costo total esperado
    CTE = calcular_costo_total_politica_a(D, Q_optimo, COSTO_ORDENAR, H)
    
    resultados_politica_a.append({
        'Componente': row['Componente'],
        'Demanda_Anual': D,
        'Costo_Unitario': C,
        'Costo_Mantener': H,
        'EOQ': Q_optimo,
        'Num_Pedidos': N,
        'Tiempo_Entre_Pedidos': T,
        'ROP': ROP,
        'Inv_Promedio': inv_promedio,
        'Inv_Maximo': inv_maximo,
        'CTE': CTE
    })

df_politica_a = pd.DataFrame(resultados_politica_a)

print("\n--- Resultados Política A ---")
print(f"\n{'Componente':<35} {'D (anual)':<12} {'EOQ':<10} {'N pedidos':<10} {'ROP':<10} {'CTE ($)':<15}")
print("-" * 102)

for idx, row in df_politica_a.iterrows():
    print(f"{row['Componente']:<35} {row['Demanda_Anual']:>10,.0f} {row['EOQ']:>10,.1f} {row['Num_Pedidos']:>10,.1f} {row['ROP']:>10,.1f} {row['CTE']:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_total_a = df_politica_a['CTE'].sum()
print(f"\n{'COSTO TOTAL ESPERADO (CTE) POLÍTICA A:':<50} ${cte_total_a:>20,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 7. MODELO EOQ - POLÍTICA B (NIVEL DE SERVICIO 95%) ===
print("\n" + "="*70)
print("POLÍTICA B: BASADA EN NIVEL DE SERVICIO (α = 0.05, Servicio = 95%)")
print("="*70)

def calcular_stock_seguridad(z, sigma_lt):
    """
    Calcula el Stock de Seguridad
    SS = z * σ_LT
    z: Z-score para el nivel de servicio
    σ_LT: Desviación estándar de demanda durante lead time
    """
    return z * sigma_lt

# Calcular EOQ con stock de seguridad para cada componente
resultados_politica_b = []

for idx, row in componentes.iterrows():
    D = row['Demanda_Anual']  # Demanda anual
    C = row['Costo_Unitario']  # Costo unitario
    H = C * TASA_MANTENIMIENTO  # Costo de mantener
    L = row['Lead_Time_Semanas']  # Lead time en semanas
    sigma_lt = row['Desv_Lead_Time']  # Desviación estándar durante lead time
    
    # EOQ (mismo que política A)
    Q_optimo = calcular_eoq(D, COSTO_ORDENAR, H)
    
    # Stock de seguridad
    SS = calcular_stock_seguridad(Z_ALPHA, sigma_lt)
    
    # Número de pedidos por año
    N = D / Q_optimo
    
    # Punto de reorden (ROP) = Demanda durante lead time + Stock de seguridad
    demanda_semanal = D / SEMANAS_POR_AÑO
    demanda_lt = demanda_semanal * L
    ROP = demanda_lt + SS
    
    # Inventario promedio (incluye SS)
    inv_promedio = (Q_optimo / 2) + SS
    
    # Inventario máximo
    inv_maximo = Q_optimo + SS
    
    # Costo total esperado (incluye costo de mantener SS)
    costo_ordenar = (D / Q_optimo) * COSTO_ORDENAR
    costo_mantener = ((Q_optimo / 2) + SS) * H
    CTE = costo_ordenar + costo_mantener
    
    resultados_politica_b.append({
        'Componente': row['Componente'],
        'Demanda_Anual': D,
        'Costo_Unitario': C,
        'Costo_Mantener': H,
        'EOQ': Q_optimo,
        'Stock_Seguridad': SS,
        'Num_Pedidos': N,
        'ROP': ROP,
        'Inv_Promedio': inv_promedio,
        'Inv_Maximo': inv_maximo,
        'CTE': CTE
    })

df_politica_b = pd.DataFrame(resultados_politica_b)

print(f"\n  Z-score para α=0.05: {Z_ALPHA:.4f}")
print("\n--- Resultados Política B ---")
print(f"\n{'Componente':<35} {'EOQ':<10} {'SS':<10} {'ROP':<10} {'Inv Max':<10} {'CTE ($)':<15}")
print("-" * 100)

for idx, row in df_politica_b.iterrows():
    print(f"{row['Componente']:<35} {row['EOQ']:>10,.1f} {row['Stock_Seguridad']:>10,.1f} {row['ROP']:>10,.1f} {row['Inv_Maximo']:>10,.1f} {row['CTE']:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

cte_total_b = df_politica_b['CTE'].sum()
print(f"\n{'COSTO TOTAL ESPERADO (CTE) POLÍTICA B:':<50} ${cte_total_b:>20,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 8. COMPARACIÓN DE POLÍTICAS ===
print("\n" + "="*70)
print("COMPARACIÓN DE POLÍTICAS A vs B")
print("="*70)

diferencia_cte = cte_total_b - cte_total_a
porcentaje_incremento = (diferencia_cte / cte_total_a) * 100

print(f"\n  {'Métrica':<40} {'Política A':<20} {'Política B':<20}")
print("-" * 80)
print(f"  {'CTE Total':<40} ${cte_total_a:>18,.2f} ${cte_total_b:>18,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'Diferencia de costo':<40} {'':<20} ${diferencia_cte:>18,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'Incremento porcentual':<40} {'':<20} {porcentaje_incremento:>17,.2f}%".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'Nivel de servicio':<40} {'Variable':<20} {'95%':<20}")
print(f"  {'Riesgo de agotamiento':<40} {'Mayor':<20} {'Controlado (5%)':<20}")

# Comparación detallada por componente
print("\n--- Comparación detallada por componente ---")
print(f"\n{'Componente':<35} {'CTE Pol.A':<15} {'CTE Pol.B':<15} {'SS (Pol.B)':<12} {'Δ Costo':<12}")
print("-" * 89)

for i in range(len(df_politica_a)):
    comp = df_politica_a.iloc[i]['Componente']
    cte_a = df_politica_a.iloc[i]['CTE']
    cte_b = df_politica_b.iloc[i]['CTE']
    ss = df_politica_b.iloc[i]['Stock_Seguridad']
    delta = cte_b - cte_a
    print(f"{comp:<35} ${cte_a:>13,.2f} ${cte_b:>13,.2f} {ss:>12,.1f} ${delta:>10,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 9. ANÁLISIS DE CAPACIDAD DE ALMACÉN ===
print("\n" + "="*70)
print("ANÁLISIS DE CAPACIDAD DE ALMACÉN")
print("="*70)

# Calcular volumen requerido para cada política
df_politica_a['Volumen_Max'] = df_politica_a['Inv_Maximo'] * componentes['Volumen_m3'].values
df_politica_b['Volumen_Max'] = df_politica_b['Inv_Maximo'] * componentes['Volumen_m3'].values

volumen_total_a = df_politica_a['Volumen_Max'].sum()
volumen_total_b = df_politica_b['Volumen_Max'].sum()

print(f"\n  {'Capacidad de almacén requerida':<40}")
print("-" * 60)
print(f"  {'Política A (sin stock seguridad):':<40} {volumen_total_a:>15,.2f} m³".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'Política B (con stock seguridad):':<40} {volumen_total_b:>15,.2f} m³".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'Diferencia:':<40} {volumen_total_b - volumen_total_a:>15,.2f} m³".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Detalle por componente
print("\n--- Volumen por componente ---")
print(f"\n{'Componente':<35} {'Vol/unidad':<12} {'Inv Max A':<12} {'Vol A (m³)':<12} {'Inv Max B':<12} {'Vol B (m³)':<12}")
print("-" * 95)

for i in range(len(componentes)):
    comp = componentes.iloc[i]['Componente']
    vol_unit = componentes.iloc[i]['Volumen_m3']
    inv_max_a = df_politica_a.iloc[i]['Inv_Maximo']
    inv_max_b = df_politica_b.iloc[i]['Inv_Maximo']
    vol_a = df_politica_a.iloc[i]['Volumen_Max']
    vol_b = df_politica_b.iloc[i]['Volumen_Max']
    print(f"{comp:<35} {vol_unit:>12,.2f} {inv_max_a:>12,.1f} {vol_a:>12,.2f} {inv_max_b:>12,.1f} {vol_b:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 10. VISUALIZACIONES ===
print("\n--- Generando gráficos ---")

fig = plt.figure(figsize=(16, 12))
fig.suptitle('Análisis de Políticas de Inventario EOQ', fontsize=16, fontweight='bold')

# Gráfico 1: Comparación CTE por componente
ax1 = fig.add_subplot(2, 2, 1)
x = np.arange(len(df_politica_a))
width = 0.35
bars1 = ax1.bar(x - width/2, df_politica_a['CTE'], width, label='Política A', color='steelblue')
bars2 = ax1.bar(x + width/2, df_politica_b['CTE'], width, label='Política B', color='coral')
ax1.set_ylabel('CTE ($)')
ax1.set_title('Costo Total Esperado por Componente')
ax1.set_xticks(x)
ax1.set_xticklabels([c[:15] + '...' if len(c) > 15 else c for c in df_politica_a['Componente']], rotation=45, ha='right')
ax1.legend()
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax1.grid(True, alpha=0.3)

# Gráfico 2: Stock de Seguridad (Política B)
ax2 = fig.add_subplot(2, 2, 2)
colors = ['coral' if ss > 0 else 'gray' for ss in df_politica_b['Stock_Seguridad']]
bars = ax2.barh(df_politica_b['Componente'], df_politica_b['Stock_Seguridad'], color=colors)
ax2.set_xlabel('Unidades')
ax2.set_title('Stock de Seguridad (Política B)')
ax2.grid(True, alpha=0.3, axis='x')
for i, (bar, ss) in enumerate(zip(bars, df_politica_b['Stock_Seguridad'])):
    ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
             f'{ss:.1f}', va='center', fontsize=8)

# Gráfico 3: Inventario Máximo comparativo
ax3 = fig.add_subplot(2, 2, 3)
bars1 = ax3.bar(x - width/2, df_politica_a['Inv_Maximo'], width, label='Política A', color='steelblue')
bars2 = ax3.bar(x + width/2, df_politica_b['Inv_Maximo'], width, label='Política B', color='coral')
ax3.set_ylabel('Unidades')
ax3.set_title('Inventario Máximo por Componente')
ax3.set_xticks(x)
ax3.set_xticklabels([c[:15] + '...' if len(c) > 15 else c for c in df_politica_a['Componente']], rotation=45, ha='right')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Gráfico 4: Comparación de Costos Totales
ax4 = fig.add_subplot(2, 2, 4)
categorias = ['Política A\n(Óptima Costos)', 'Política B\n(Servicio 95%)']
valores = [cte_total_a, cte_total_b]
colores = ['steelblue', 'coral']
bars = ax4.bar(categorias, valores, color=colores, edgecolor='black', linewidth=1.5)
ax4.set_ylabel('CTE Total ($)')
ax4.set_title('Costo Total Esperado - Comparación')
ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
for bar, val in zip(bars, valores):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500, 
             f'${val:,.0f}'.replace(',', '.'), ha='center', fontsize=10, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

# Guardar gráfico
output_path = os.path.join(script_dir, 'eoq_comparacion.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ Gráfico guardado: {output_path}")
plt.close()

# === 11. EXPORTAR RESULTADOS ===
print("\n--- Exportando resultados ---")

# Guardar resultados de Política A
politica_a_path = os.path.join(script_dir, 'politica_a_resultados.csv')
df_politica_a.to_csv(politica_a_path, index=False)
print(f"✓ Política A: {politica_a_path}")

# Guardar resultados de Política B
politica_b_path = os.path.join(script_dir, 'politica_b_resultados.csv')
df_politica_b.to_csv(politica_b_path, index=False)
print(f"✓ Política B: {politica_b_path}")

# Guardar comparación
comparacion = pd.DataFrame({
    'Metrica': ['CTE Total ($)', 'Capacidad Almacén (m³)', 'Nivel de Servicio', 'Riesgo Agotamiento'],
    'Politica_A': [cte_total_a, volumen_total_a, 'Variable', 'Mayor'],
    'Politica_B': [cte_total_b, volumen_total_b, '95%', '5%']
})
comparacion_path = os.path.join(script_dir, 'comparacion_politicas.csv')
comparacion.to_csv(comparacion_path, index=False)
print(f"✓ Comparación: {comparacion_path}")

# === 12. RESUMEN FINAL ===
print("\n" + "="*70)
print("RESUMEN EJECUTIVO")
print("="*70)

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    POLÍTICAS DE INVENTARIO EOQ                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  POLÍTICA A (Óptima por Costos)                                       ║
║    • CTE Total:              ${cte_total_a:>15,.2f}                   ║
║    • Capacidad Almacén:      {volumen_total_a:>15,.2f} m³                   ║
║    • Nivel de Servicio:      Variable (sin stock seguridad)           ║
║    • Riesgo:                 Mayor exposición a agotamientos          ║
╠══════════════════════════════════════════════════════════════════════╣
║  POLÍTICA B (Nivel de Servicio 95%)                                   ║
║    • CTE Total:              ${cte_total_b:>15,.2f}                   ║
║    • Capacidad Almacén:      {volumen_total_b:>15,.2f} m³                   ║
║    • Nivel de Servicio:      95% garantizado                          ║
║    • Riesgo:                 Controlado (5% prob. agotamiento)        ║
╠══════════════════════════════════════════════════════════════════════╣
║  DIFERENCIA                                                           ║
║    • Incremento CTE:         ${diferencia_cte:>15,.2f} ({porcentaje_incremento:>5.2f}%)      ║
║    • Espacio adicional:      {volumen_total_b - volumen_total_a:>15,.2f} m³                   ║
╚══════════════════════════════════════════════════════════════════════╝
""".replace(',', 'X').replace('.', ',').replace('X', '.'))

print("="*70)
print("Fin del análisis de Políticas de Inventario")
print("="*70)
