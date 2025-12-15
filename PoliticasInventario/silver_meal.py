# ============================
# HEURÍSTICA SILVER-MEAL
# Para demanda variable/estacional
# ============================
# Referencia: Winston - Investigación de Operaciones
# Capítulo 18: Modelos determinísticos de inventario
# Alternativa a EOQ cuando CV ≥ 0.20
# ============================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("HEURÍSTICA SILVER-MEAL")
print("Para demanda variable/estacional (CV ≥ 0.20)")
print("Referencia: Winston - Inv. Operaciones, Cap. 18")
print("="*70)

# === 1. PARÁMETROS ===
COSTO_ORDENAR = 300  # $ por orden de compra (K en Winston)
TASA_MANTENIMIENTO = 0.20  # 20% del costo unitario anual
MESES_POR_AÑO = 12

print(f"\n--- Parámetros ---")
print(f"  Costo de ordenar (K):      ${COSTO_ORDENAR:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  Tasa de mantenimiento:     {TASA_MANTENIMIENTO*100:.0f}% anual")

# === 2. CARGAR PRONÓSTICO PROPHET ===
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..'))

prophet_forecast_path = os.path.join(project_root, 'ForecastModels', 'Prophet', 'prophet_forecast.csv')

if not os.path.exists(prophet_forecast_path):
    raise SystemExit(f"Error: No se encontró {prophet_forecast_path}")

df_pronostico = pd.read_csv(prophet_forecast_path)

# Demandas mensuales pronosticadas (en $)
demandas_monetarias = df_pronostico['Pronostico'].values
periodos = df_pronostico['Periodo'].values
n_periodos = len(demandas_monetarias)

# Convertir a UNIDADES de autos vendidos
# (Silver-Meal trabaja con unidades, no con valores monetarios)
PRECIO_PROMEDIO_AUTO = 3500  # $/auto promedio

demandas = demandas_monetarias / PRECIO_PROMEDIO_AUTO  # Unidades de autos

print(f"\n--- Demanda Pronosticada (12 meses) ---")
print(f"  {'Mes':<12} {'Ventas ($)':<18} {'Unidades (autos)':<18}")
print("-" * 50)
for i, (p, d_mon, d_uni) in enumerate(zip(periodos, demandas_monetarias, demandas)):
    print(f"  {p[:7]:<12} ${d_mon:>14,.2f} {d_uni:>16,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n  Total anual: {sum(demandas):,.0f} unidades (autos)".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Costo de mantener mensual por UNIDAD (h = H/12)
# Para un auto completo, usamos costo promedio de componentes
COSTO_UNITARIO_PROMEDIO = 5000  # $ por conjunto de componentes/auto
h_mensual = (COSTO_UNITARIO_PROMEDIO * TASA_MANTENIMIENTO) / MESES_POR_AÑO

print(f"\n  Costo de mantener mensual por unidad (h): ${h_mensual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 3. ALGORITMO SILVER-MEAL ===
# Winston, Cap. 18: "Minimizar el costo promedio por período"
#
# Para cada período t, calculamos el costo promedio por período de ordenar
# en t para cubrir demandas de t hasta t+j periodos.
#
# C(t, t+j) = [K + h*(d_{t+1} + 2*d_{t+2} + ... + j*d_{t+j})] / (j+1)
#
# Ordenamos cuando C(t, t+j+1) > C(t, t+j)

print("\n" + "="*70)
print("ALGORITMO SILVER-MEAL")
print("="*70)

def silver_meal(demandas, K, h):
    """
    Implementa la heurística Silver-Meal.
    
    Parámetros:
    - demandas: array de demandas por período
    - K: costo fijo de ordenar
    - h: costo de mantener por unidad por período
    
    Retorna:
    - plan: lista de tuplas (periodo_orden, cantidad, periodos_cubiertos)
    - costo_total: costo total del plan
    """
    n = len(demandas)
    plan = []
    costo_total = 0
    t = 0  # Período actual
    
    print(f"\n  Iteraciones del algoritmo:")
    print("-" * 80)
    
    while t < n:
        print(f"\n  → Período {t+1} ({periodos[t][:7]}):")
        
        # Calcular costo promedio por período para diferentes horizontes
        mejor_j = 0
        mejor_costo_promedio = float('inf')
        
        for j in range(n - t):
            # Costo de mantener inventario
            costo_mantener = 0
            for k in range(1, j + 1):
                if t + k < n:
                    costo_mantener += k * h * demandas[t + k]
            
            # Costo total para cubrir períodos t hasta t+j
            costo_total_j = K + costo_mantener
            
            # Costo promedio por período
            costo_promedio = costo_total_j / (j + 1)
            
            print(f"    j={j}: Cubrir {j+1} período(s), Costo total=${costo_total_j:,.2f}, "
                  f"Costo promedio=${costo_promedio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            # Regla Silver-Meal: parar cuando el costo promedio empieza a aumentar
            if costo_promedio < mejor_costo_promedio:
                mejor_costo_promedio = costo_promedio
                mejor_j = j
            else:
                # El costo promedio aumentó, usar el anterior
                break
        
        # Cantidad a ordenar: suma de demandas desde t hasta t+mejor_j
        cantidad = sum(demandas[t:t + mejor_j + 1])
        periodos_cubiertos = list(range(t + 1, t + mejor_j + 2))
        
        # Calcular costo real de esta orden
        costo_orden = K
        for k in range(1, mejor_j + 1):
            if t + k < n:
                costo_orden += k * h * demandas[t + k]
        
        plan.append({
            'Periodo_Orden': t + 1,
            'Mes_Orden': periodos[t][:7],
            'Cantidad': cantidad,
            'Periodos_Cubiertos': periodos_cubiertos,
            'Meses_Cubiertos': mejor_j + 1,
            'Costo_Orden': costo_orden
        })
        
        costo_total += costo_orden
        
        print(f"    ✓ DECISIÓN: Ordenar {cantidad:,.1f} unidades en período {t+1} para cubrir {mejor_j+1} período(s)".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Avanzar al siguiente período no cubierto
        t = t + mejor_j + 1
    
    return plan, costo_total


# Ejecutar Silver-Meal
plan_silver_meal, costo_total_sm = silver_meal(demandas, COSTO_ORDENAR, h_mensual)

# === 4. RESULTADOS SILVER-MEAL ===
print("\n" + "="*70)
print("RESULTADOS SILVER-MEAL")
print("="*70)

df_plan = pd.DataFrame(plan_silver_meal)

print(f"\n--- Plan de Pedidos ---")
print(f"\n{'#':<5} {'Mes Orden':<12} {'Cantidad (uni)':<18} {'Meses Cubiertos':<18} {'Costo Orden ($)':<18}")
print("-" * 75)

for idx, row in df_plan.iterrows():
    print(f"{idx+1:<5} {row['Mes_Orden']:<12} {row['Cantidad']:>16,.1f} {row['Meses_Cubiertos']:>16} {row['Costo_Orden']:>16,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f"\n{'COSTO TOTAL SILVER-MEAL:':<40} ${costo_total_sm:>20,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"{'Número de pedidos:':<40} {len(plan_silver_meal):>20}")
print(f"{'Demanda total del año:':<40} {sum(demandas):>20,.0f} unidades".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 5. COMPARACIÓN CON EOQ ===
print("\n" + "="*70)
print("COMPARACIÓN: SILVER-MEAL vs EOQ")
print("="*70)

# Calcular EOQ para comparar (en unidades)
D_anual = sum(demandas)  # Unidades anuales
H_anual = COSTO_UNITARIO_PROMEDIO * TASA_MANTENIMIENTO  # Costo mantener anual por unidad

# EOQ clásico
EOQ = np.sqrt((2 * D_anual * COSTO_ORDENAR) / H_anual)
N_pedidos_eoq = D_anual / EOQ
Costo_total_eoq = (D_anual / EOQ) * COSTO_ORDENAR + (EOQ / 2) * H_anual

print(f"\n  {'Método':<25} {'Costo Total ($)':<20} {'Nº Pedidos':<15} {'Q promedio':<15}")
print("-" * 75)
print(f"  {'Silver-Meal':<25} {costo_total_sm:>18,.2f} {len(plan_silver_meal):>13} {sum(demandas)/len(plan_silver_meal):>13,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f"  {'EOQ Clásico':<25} {Costo_total_eoq:>18,.2f} {N_pedidos_eoq:>13,.1f} {EOQ:>13,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

ahorro = Costo_total_eoq - costo_total_sm
ahorro_pct = (ahorro / Costo_total_eoq) * 100

if ahorro > 0:
    print(f"\n  ✅ Silver-Meal AHORRA ${ahorro:,.2f} ({ahorro_pct:.1f}%) vs EOQ".replace(',', 'X').replace('.', ',').replace('X', '.'))
else:
    print(f"\n  ℹ️  EOQ es más económico por ${-ahorro:,.2f} ({-ahorro_pct:.1f}%)".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 6. VISUALIZACIÓN ===
print("\n--- Generando gráficos ---")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Heurística Silver-Meal vs EOQ\n(Winston - Inv. Operaciones, Cap. 18)', fontsize=14, fontweight='bold')

# Gráfico 1: Demanda mensual con puntos de pedido
ax1 = axes[0, 0]
meses = [p[:7] for p in periodos]
ax1.bar(meses, demandas, color='steelblue', alpha=0.7, label='Demanda (unidades)')

# Marcar puntos de pedido Silver-Meal
for orden in plan_silver_meal:
    idx = orden['Periodo_Orden'] - 1
    ax1.axvline(x=idx, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.annotate(f"Orden\n{orden['Cantidad']:.0f} uni", 
                 xy=(idx, demandas[idx]), 
                 xytext=(idx, demandas[idx] + 15),
                 fontsize=8, ha='center', color='red')

ax1.set_xlabel('Mes')
ax1.set_ylabel('Demanda (unidades)')
ax1.set_title('Demanda Mensual y Puntos de Pedido (Silver-Meal)')
ax1.tick_params(axis='x', rotation=45)
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico 2: Comparación de costos
ax2 = axes[0, 1]
metodos = ['Silver-Meal', 'EOQ Clásico']
costos = [costo_total_sm, Costo_total_eoq]
colores = ['forestgreen', 'steelblue']
bars = ax2.bar(metodos, costos, color=colores, edgecolor='black')
ax2.set_ylabel('Costo Total ($)')
ax2.set_title('Comparación de Costos Totales')
for bar, costo in zip(bars, costos):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100, 
             f'${costo:,.0f}'.replace(',', '.'), ha='center', fontsize=10, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

# Gráfico 3: Cantidad por pedido Silver-Meal
ax3 = axes[1, 0]
ordenes = [f"Orden {i+1}\n({o['Mes_Orden']})" for i, o in enumerate(plan_silver_meal)]
cantidades = [o['Cantidad'] for o in plan_silver_meal]
ax3.bar(ordenes, cantidades, color='forestgreen', edgecolor='black')
ax3.set_ylabel('Cantidad (unidades)')
ax3.set_title('Cantidad por Pedido (Silver-Meal)')
for i, (o, c) in enumerate(zip(ordenes, cantidades)):
    ax3.text(i, c + 5, f'{c:.0f}', ha='center', fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# Gráfico 4: Cobertura de cada pedido
ax4 = axes[1, 1]
# Crear un gráfico de Gantt simple
for i, orden in enumerate(plan_silver_meal):
    inicio = orden['Periodo_Orden'] - 1
    duracion = orden['Meses_Cubiertos']
    ax4.barh(i, duracion, left=inicio, height=0.5, color='forestgreen', edgecolor='black')
    ax4.text(inicio + duracion/2, i, f"{duracion} mes(es)", ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax4.set_yticks(range(len(plan_silver_meal)))
ax4.set_yticklabels([f"Orden {i+1}" for i in range(len(plan_silver_meal))])
ax4.set_xlabel('Mes')
ax4.set_xticks(range(12))
ax4.set_xticklabels([m[-2:] for m in meses])
ax4.set_title('Cobertura de cada Pedido')
ax4.grid(True, alpha=0.3, axis='x')

plt.tight_layout()

output_path = os.path.join(script_dir, 'silver_meal_resultado.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ Gráfico guardado: {output_path}")
plt.close()

# === 7. EXPORTAR RESULTADOS ===
print("\n--- Exportando resultados ---")

# Plan de pedidos
plan_path = os.path.join(script_dir, 'silver_meal_plan.csv')
df_plan.to_csv(plan_path, index=False)
print(f"✓ Plan Silver-Meal: {plan_path}")

# Comparación
comparacion = pd.DataFrame({
    'Metodo': ['Silver-Meal', 'EOQ Clásico'],
    'Costo_Total': [costo_total_sm, Costo_total_eoq],
    'Num_Pedidos': [len(plan_silver_meal), N_pedidos_eoq],
    'Demanda_Total': [sum(demandas), sum(demandas)]
})
comp_path = os.path.join(script_dir, 'silver_meal_vs_eoq.csv')
comparacion.to_csv(comp_path, index=False)
print(f"✓ Comparación: {comp_path}")

# === 8. RESUMEN ===
print("\n" + "="*70)
print("RESUMEN - HEURÍSTICA SILVER-MEAL")
print("="*70)

print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║              SILVER-MEAL vs EOQ (Winston, Cap. 18)                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  Contexto:                                                            ║
║    • CV = 0.44 ≥ 0.20 → Demanda irregular/estacional                  ║
║    • Winston recomienda Silver-Meal para este caso                    ║
╠══════════════════════════════════════════════════════════════════════╣
║  SILVER-MEAL:                                                         ║
║    • Costo Total:       ${costo_total_sm:>15,.2f}                          ║
║    • Número de pedidos: {len(plan_silver_meal):>15}                               ║
║    • Adapta pedidos a la estacionalidad                               ║
╠══════════════════════════════════════════════════════════════════════╣
║  EOQ CLÁSICO:                                                         ║
║    • Costo Total:       ${Costo_total_eoq:>15,.2f}                          ║
║    • Número de pedidos: {N_pedidos_eoq:>15,.1f}                               ║
║    • Asume demanda constante (NO aplica aquí)                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  CONCLUSIÓN:                                                          ║
║    Silver-Meal {"AHORRA" if ahorro > 0 else "cuesta más"}: ${abs(ahorro):>15,.2f} ({abs(ahorro_pct):>5.1f}%)                    ║
╚══════════════════════════════════════════════════════════════════════╝
""".replace(',', 'X').replace('.', ',').replace('X', '.'))

print("\n" + "="*70)
print("Fin del análisis Silver-Meal")
print("="*70)
