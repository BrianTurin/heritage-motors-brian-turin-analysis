# ============================
# ANÁLISIS DE CV POR PERÍODOS
# Para determinar ventanas donde EOQ es válido
# ============================
# Referencia: Winston - Inv. Operaciones, pág. 872-873
# ============================
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("="*70)
print("ANÁLISIS DE COEFICIENTE DE VARIABILIDAD (CV) POR PERÍODOS")
print("Objetivo: Encontrar períodos donde CV < 0.20 para usar EOQ")
print("="*70)

# Cargar datos
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..'))
prophet_forecast_path = os.path.join(project_root, 'outputs', 'forecast', 'prophet', 'prophet_forecast.csv')

df = pd.read_csv(prophet_forecast_path)
demandas = df['Pronostico'].values
meses = [p[:7] for p in df['Periodo']]
n = len(demandas)

print(f"\n--- Demandas Mensuales Pronosticadas ---")
for i, (m, d) in enumerate(zip(meses, demandas)):
    print(f"  {i+1:2}. {m}: ${d:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# Función para calcular CV
def calcular_cv(datos):
    """Calcula el Coeficiente de Variabilidad según Winston"""
    datos = np.array(datos)
    d_prom = np.mean(datos)
    var_est = np.mean(datos**2) - d_prom**2
    return var_est / (d_prom**2) if d_prom > 0 else float('inf')

# CV Total
cv_total = calcular_cv(demandas)
print(f"\n  CV Total (12 meses): {cv_total:.4f}")
print(f"  Estado: {'OK EOQ valido' if cv_total < 0.20 else 'CV alto, EOQ no recomendado'}")

# === ANÁLISIS POR TRIMESTRES ===
print("\n" + "="*70)
print("ANÁLISIS POR TRIMESTRES")
print("="*70)

trimestres = [
    ('Q3-2005', 'Jun-Jul-Ago', [0, 1, 2]),
    ('Q4-2005', 'Sep-Oct-Nov', [3, 4, 5]),
    ('Q1-2006', 'Dic-Ene-Feb', [6, 7, 8]),
    ('Q2-2006', 'Mar-Abr-May', [9, 10, 11])
]

print(f"\n{'Trimestre':<12} {'Meses':<15} {'Demanda Prom':<15} {'CV':<10} {'Estado':<20}")
print("-" * 72)

for nombre, desc, indices in trimestres:
    datos = demandas[indices]
    cv = calcular_cv(datos)
    prom = np.mean(datos)
    estado = '✓ EOQ válido' if cv < 0.20 else '✗ CV alto'
    print(f"{nombre:<12} {desc:<15} ${prom:>12,.0f} {cv:>9.4f} {estado:<20}".replace(',', '.'))

# === ANÁLISIS POR TEMPORADAS ===
print("\n" + "="*70)
print("ANÁLISIS POR TEMPORADAS (Alta vs Baja)")
print("="*70)

# Identificar temporada alta (meses con demanda > promedio)
promedio = np.mean(demandas)
print(f"\n  Demanda promedio mensual: ${promedio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

temporada_alta_idx = [i for i, d in enumerate(demandas) if d > promedio * 1.2]
temporada_baja_idx = [i for i in range(n) if i not in temporada_alta_idx]

print(f"\n  Temporada Alta (demanda > 120% promedio):")
print(f"    Meses: {[meses[i] for i in temporada_alta_idx]}")
if len(temporada_alta_idx) > 1:
    cv_alta = calcular_cv(demandas[temporada_alta_idx])
    print(f"    CV: {cv_alta:.4f} {'✓ EOQ válido' if cv_alta < 0.20 else '✗ CV alto'}")

print(f"\n  Temporada Baja (resto):")
print(f"    Meses: {[meses[i] for i in temporada_baja_idx]}")
if len(temporada_baja_idx) > 1:
    cv_baja = calcular_cv(demandas[temporada_baja_idx])
    print(f"    CV: {cv_baja:.4f} {'✓ EOQ válido' if cv_baja < 0.20 else '✗ CV alto'}")

# === BÚSQUEDA DE VENTANAS CON CV < 0.20 ===
print("\n" + "="*70)
print("BÚSQUEDA DE VENTANAS CONSECUTIVAS CON CV < 0.20")
print("="*70)

ventanas_validas = []

for window_size in range(2, n+1):
    print(f"\n--- Ventanas de {window_size} meses ---")
    encontradas = 0
    for start in range(n - window_size + 1):
        end = start + window_size
        datos_ventana = demandas[start:end]
        cv = calcular_cv(datos_ventana)
        
        if cv < 0.20:
            encontradas += 1
            meses_str = f"{meses[start]} a {meses[end-1]}"
            prom = np.mean(datos_ventana)
            ventanas_validas.append({
                'inicio': start,
                'fin': end,
                'meses': meses_str,
                'cv': cv,
                'demanda_prom': prom,
                'demanda_total': np.sum(datos_ventana),
                'n_meses': window_size
            })
            print(f"  ✓ {meses_str}: CV = {cv:.4f}, Demanda prom = ${prom:,.0f}".replace(',', '.'))
    
    if encontradas == 0:
        print(f"  No se encontraron ventanas con CV < 0.20")

# === RESUMEN DE VENTANAS VÁLIDAS ===
print("\n" + "="*70)
print("RESUMEN: VENTANAS VÁLIDAS PARA EOQ")
print("="*70)

if ventanas_validas:
    df_ventanas = pd.DataFrame(ventanas_validas)
    df_ventanas = df_ventanas.sort_values('cv')
    
    print(f"\n{'Período':<25} {'Meses':<8} {'CV':<10} {'Demanda Total':<18} {'Demanda Prom':<15}")
    print("-" * 80)
    
    for _, row in df_ventanas.iterrows():
        print(f"{row['meses']:<25} {row['n_meses']:<8} {row['cv']:<10.4f} ${row['demanda_total']:>15,.0f} ${row['demanda_prom']:>12,.0f}".replace(',', '.'))
    
    # Mejor opción
    mejor = df_ventanas.iloc[0]
    print(f"\n  ★ MEJOR VENTANA: {mejor['meses']} con CV = {mejor['cv']:.4f}")
else:
    print("\n  ⚠️ No se encontraron ventanas con CV < 0.20")


# === ESTRATEGIA RECOMENDADA ===
print("\n" + "="*70)
print("ESTRATEGIA RECOMENDADA (según Winston)")
print("="*70)

# Analizar si podemos dividir el año en 2 estaciones
# Temporada pico: Oct-Nov (alta variabilidad entre ellos pero período corto)
# Resto del año

# Opción 1: Excluir noviembre del análisis general
sin_nov_idx = [i for i in range(n) if i != 5]  # Excluir índice 5 (noviembre)
cv_sin_nov = calcular_cv(demandas[sin_nov_idx])

print(f"\n  Opción 1: Excluir noviembre (outlier estacional)")
print(f"    CV sin noviembre: {cv_sin_nov:.4f}")
print(f"    Estado: {'✓ EOQ válido' if cv_sin_nov < 0.20 else '✗ Aún con CV alto'}")

# Opción 2: Dividir en 2 políticas
print(f"\n  Opción 2: Política dual (2 estaciones)")
print(f"    - Estación PICO (Oct-Nov): Planificación especial, pedidos ajustados")
print(f"    - Estación NORMAL (resto): EOQ estándar si CV < 0.20")

# CV de meses normales (excluyendo Oct y Nov)
normal_idx = [i for i in range(n) if i not in [4, 5]]  # Sin Oct ni Nov
cv_normal = calcular_cv(demandas[normal_idx])
print(f"    CV estación normal: {cv_normal:.4f} {'✓' if cv_normal < 0.20 else '✗'}")

# === VISUALIZACIÓN ===
print("\n--- Generando gráfico ---")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Análisis de CV por Períodos - Validación para EOQ', fontsize=14, fontweight='bold')

# Gráfico 1: Serie temporal con umbral
ax1 = axes[0, 0]
ax1.bar(range(n), demandas, color='steelblue', alpha=0.7)
ax1.axhline(y=promedio, color='red', linestyle='--', label=f'Promedio: ${promedio/1000:.0f}K')
ax1.axhline(y=promedio*1.2, color='orange', linestyle=':', label='120% Promedio')
ax1.set_xticks(range(n))
ax1.set_xticklabels([m[-2:] for m in meses], rotation=45)
ax1.set_ylabel('Demanda ($)')
ax1.set_title('Demanda Mensual Pronosticada')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfico 2: CV por trimestre
ax2 = axes[0, 1]
trimestre_nombres = ['Q3-2005', 'Q4-2005', 'Q1-2006', 'Q2-2006']
cvs_trim = [calcular_cv(demandas[t[2]]) for t in trimestres]
colors = ['green' if cv < 0.20 else 'red' for cv in cvs_trim]
bars = ax2.bar(trimestre_nombres, cvs_trim, color=colors, alpha=0.7)
ax2.axhline(y=0.20, color='black', linestyle='--', linewidth=2, label='Umbral CV = 0.20')
ax2.set_ylabel('Coeficiente de Variabilidad')
ax2.set_title('CV por Trimestre')
ax2.legend()
for bar, cv in zip(bars, cvs_trim):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
             f'{cv:.3f}', ha='center', fontsize=10)
ax2.grid(True, alpha=0.3)

# Gráfico 3: CV acumulativo
ax3 = axes[1, 0]
cvs_acum = []
for i in range(2, n+1):
    cvs_acum.append(calcular_cv(demandas[:i]))
ax3.plot(range(2, n+1), cvs_acum, 'o-', color='steelblue', linewidth=2, markersize=8)
ax3.axhline(y=0.20, color='red', linestyle='--', linewidth=2, label='Umbral CV = 0.20')
ax3.set_xlabel('Número de meses incluidos')
ax3.set_ylabel('CV Acumulativo')
ax3.set_title('Evolución del CV al agregar meses')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_xticks(range(2, n+1))

# Gráfico 4: Mapa de calor de CV por ventanas
ax4 = axes[1, 1]
# Crear matriz de CV para diferentes ventanas
max_window = 6
cv_matrix = np.full((max_window-1, n), np.nan)
for w in range(2, max_window+1):
    for start in range(n - w + 1):
        cv_matrix[w-2, start] = calcular_cv(demandas[start:start+w])

im = ax4.imshow(cv_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=0.5)
ax4.set_yticks(range(max_window-1))
ax4.set_yticklabels([f'{w} meses' for w in range(2, max_window+1)])
ax4.set_xticks(range(n))
ax4.set_xticklabels([m[-2:] for m in meses], rotation=45)
ax4.set_xlabel('Mes de inicio')
ax4.set_title('Mapa de CV por ventana (verde=bajo, rojo=alto)')
plt.colorbar(im, ax=ax4, label='CV')

# Marcar celdas con CV < 0.20
for w in range(2, max_window+1):
    for start in range(n - w + 1):
        cv_val = cv_matrix[w-2, start]
        if not np.isnan(cv_val) and cv_val < 0.20:
            ax4.add_patch(plt.Rectangle((start-0.5, w-2-0.5), 1, 1, 
                                        fill=False, edgecolor='black', linewidth=2))

plt.tight_layout()

output_path = os.path.join(script_dir, 'analisis_cv_periodos.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ Gráfico guardado: {output_path}")
plt.close()

# === CONCLUSIÓN ===
print("\n" + "="*70)
print("CONCLUSIÓN")
print("="*70)

print(f"""
  El análisis revela que:
  
  1. CV Total = {cv_total:.4f} (≥ 0.20) → EOQ clásico NO es óptimo para todo el año
  
  2. La alta variabilidad se debe principalmente a:
     - Noviembre: ${demandas[5]:,.0f} (pico estacional)
     - Abril: ${demandas[10]:,.0f} (valle)
  
  3. Estrategia recomendada según Winston:
     
     Si no hay ventanas con CV < 0.20 para el horizonte completo:

     → O dividir en estaciones y aplicar EOQ por estación
     
  4. Para este caso específico:
     - CV sin Nov = {cv_sin_nov:.4f}
     - Se recomienda tratar noviembre como período especial
       con planificación separada
""".replace(',', 'X').replace('.', ',').replace('X', '.'))