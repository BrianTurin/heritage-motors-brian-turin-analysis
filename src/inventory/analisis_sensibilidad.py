# Análisis de Sensibilidad: Costo de Agotamiento y Riesgo (+15% incertidumbre)
# -----------------------------------------------------------------------------
# Este script usa los resultados existentes de EOQ estacional para:
# 1) Sensibilidad al Costo de Agotamiento (Política A): ±30%
# 2) Sensibilidad al Riesgo (+15% en incertidumbre): impacto en SS y CTE
#
# Entradas requeridas (preexistentes en el proyecto):
#   - outputs/forecast/prophet/prophet_forecast.csv
#   - outputs/inventory/eoq_estacional/eoq_estacional_pico_costo.csv
#   - outputs/inventory/eoq_estacional/eoq_estacional_normal_costo.csv
#   - outputs/inventory/eoq_estacional/eoq_estacional_pico_servicio.csv
#   - outputs/inventory/eoq_estacional/eoq_estacional_normal_servicio.csv
#
# Salidas:
#   - outputs/inventory/comparacion/sensibilidad_agotamiento_politica_a.csv
#   - outputs/inventory/comparacion/riesgo_+15.csv
#   - gráficos en outputs/inventory/comparacion/

import os
import math
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Parámetros coherentes con el proyecto
Z_ALPHA = 1.645              # 95% servicio
SEMANAS_POR_MES = 4.33
TASA_MANTENIMIENTO = 0.20    # anual

# Utilidades ------------------------------------------------------------------

def std_loss_L(k: float) -> float:
    """Función de pérdida estándar L(k) = φ(k) - k * (1-Φ(k))."""
    return norm.pdf(k) - k * (1.0 - norm.cdf(k))


def ensure_dirs(path: str):
    os.makedirs(path, exist_ok=True)


# Carga de datos ---------------------------------------------------------------

def cargar_componentes_basicos():
    """Replica la tabla de componentes definida en eoq_estacional.py."""
    return pd.DataFrame({
        'Componente': [
            'Carrocería Artesanal de Época',
            'Motor de Alto Rendimiento V8',
            'Motor de Cilindros de Línea Raro',
            'Carrocería Estándar (Fibra)',
            'Tapicería de Cuero Premium'
        ],
        'Auto_Foco': ['Vintage', 'Clásico', 'Vintage', 'Clásico', 'Ambos'],
        'Costo_Unitario': [15000, 9000, 12000, 6500, 4000],
        'Uso_por_Auto': [1, 1, 1, 1, 1],
        'Lead_Time_Semanas': [10, 6, 12, 4, 8]
    })


def cargar_pronostico(proj_root: str):
    path = os.path.join(proj_root, 'outputs', 'forecast', 'prophet', 'prophet_forecast.csv')
    df = pd.read_csv(path)
    df = df[pd.to_datetime(df['Periodo'], errors='coerce').notnull()].copy()
    df['Mes'] = pd.to_datetime(df['Periodo']).dt.month
    return df


# Cálculos por estación --------------------------------------------------------
MESES_PICO = [10, 11]
MESES_NORMAL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12]
FRACCION_PICO = len(MESES_PICO) / 12
FRACCION_NORMAL = len(MESES_NORMAL) / 12


def demanda_mensual_componente(df_forecast: pd.DataFrame, comp_row: pd.Series) -> pd.Series:
    if comp_row['Auto_Foco'] == 'Clásico':
        return df_forecast['Autos_Clasicos'] * comp_row['Uso_por_Auto']
    if comp_row['Auto_Foco'] == 'Vintage':
        return df_forecast['Autos_Vintage'] * comp_row['Uso_por_Auto']
    return (df_forecast['Autos_Clasicos'] + df_forecast['Autos_Vintage']) * comp_row['Uso_por_Auto']


def resumen_estacion(df_forecast: pd.DataFrame, dem_mensual: pd.Series, meses_est: list, lead_time_w: float):
    D_est = dem_mensual[df_forecast['Mes'].isin(meses_est)].sum()
    semanas_est = len(meses_est) * SEMANAS_POR_MES
    demanda_semanal = D_est / semanas_est if semanas_est > 0 else 0.0
    mu_L = demanda_semanal * lead_time_w
    # Calcular sigma mensual sólo con meses de la estación
    dem_est_mens = dem_mensual[df_forecast['Mes'].isin(meses_est)]
    sigma_mensual = float(dem_est_mens.std(ddof=0)) if len(dem_est_mens) > 1 else float('nan')
    L_meses = lead_time_w / SEMANAS_POR_MES
    sigma_L = sigma_mensual * math.sqrt(L_meses)
    return D_est, semanas_est, mu_L, sigma_mensual, sigma_L


# Lectura de salidas EOQ -------------------------------------------------------

def cargar_eoq_outputs(proj_root: str):
    base = os.path.join(proj_root, 'outputs', 'inventory', 'eoq_estacional')
    pico_costo = pd.read_csv(os.path.join(base, 'eoq_estacional_pico_costo.csv'))
    normal_costo = pd.read_csv(os.path.join(base, 'eoq_estacional_normal_costo.csv'))
    pico_serv = pd.read_csv(os.path.join(base, 'eoq_estacional_pico_servicio.csv'))
    normal_serv = pd.read_csv(os.path.join(base, 'eoq_estacional_normal_servicio.csv'))
    return pico_costo, normal_costo, pico_serv, normal_serv


# Sensibilidades ---------------------------------------------------------------

def sensibilidad_agotamiento_politica_a(proj_root: str, rate_agotamiento: float, variacion: float):
    """Evalúa el efecto del costo de agotamiento en la CTE de la Política A.
    
    Según Hadley-Whitin:
    CTE = (K·D)/q + c1·(q/2 + SR - E[x]) + (c2·D/q)·S
    donde S = sigma_L · L(k) es el faltante esperado por ciclo.
    
    rate_agotamiento: fracción del costo unitario (ej. 0.5 => 50% del CU)
    variacion: ± variación a analizar (ej. 0.30)
    """
    df_forecast = cargar_pronostico(proj_root)
    componentes = cargar_componentes_basicos()
    pico_costo, normal_costo, _, _ = cargar_eoq_outputs(proj_root)

    resultados = []

    for _, row in componentes.iterrows():
        dem_mens = demanda_mensual_componente(df_forecast, row)
        for est_nombre, meses, df_est, fracc in (
            ('PICO', MESES_PICO, pico_costo, FRACCION_PICO),
            ('NORMAL', MESES_NORMAL, normal_costo, FRACCION_NORMAL),
        ):
            # Métricas de demanda y volatilidad
            D_est, semanas_est, mu_L, sigma_mens, sigma_L = resumen_estacion(
                df_forecast, dem_mens, meses, row['Lead_Time_Semanas']
            )
            # Fila EOQ de política A
            fila = df_est[df_est['Componente'] == row['Componente']]
            if fila.empty:
                continue
            Q = float(fila['EOQ'].values[0])
            N = float(fila['Num_Pedidos'].values[0]) if 'Num_Pedidos' in fila.columns else (D_est / Q if Q > 0 else 0)
            CTE_base = float(fila['CTE'].values[0])
            # ROP en Política A (sin SS en el script base)
            ROP = float(fila['ROP'].values[0]) if 'ROP' in fila.columns else mu_L
            # k según ROP
            k = (ROP - mu_L) / sigma_L if sigma_L and sigma_L > 0 else 0.0
            # Costo unitario de agotamiento
            c_agot_base = rate_agotamiento * row['Costo_Unitario']
            c_agot_low = (1 - variacion) * c_agot_base
            c_agot_high = (1 + variacion) * c_agot_base
            # Faltante esperado por ciclo: S = sigma_L · L(k)
            S = (sigma_L * std_loss_L(k)) if (sigma_L and sigma_L > 0) else 0.0
            # Faltante anual según Hadley-Whitin: (D/q) · S
            faltante_anual = (D_est / Q) * S if Q > 0 else 0.0
            # Costos de agotamiento anuales por escenario
            # Costo de agotamiento anual = c2 · (D/q) · S
            costo_agot_base = c_agot_base * faltante_anual
            costo_agot_low = c_agot_low * faltante_anual
            costo_agot_high = c_agot_high * faltante_anual
            CTE_con_agot_base = CTE_base + costo_agot_base
            CTE_con_agot_low = CTE_base + costo_agot_low
            CTE_con_agot_high = CTE_base + costo_agot_high
            resultados.append({
                'Componente': row['Componente'],
                'Estacion': est_nombre,
                'Costo_Unitario': row['Costo_Unitario'],
                'CTE_Base_A': CTE_base,
                'ROP_A': ROP,
                'mu_L': mu_L,
                'sigma_mensual': sigma_mens,
                'sigma_L': sigma_L,
                'k': k,
                'EOQ': Q,
                'Num_Pedidos': N,
                'S_esperado_ciclo': S,
                'Faltante_Anual': faltante_anual,
                'c_agot_base': c_agot_base,
                'CTE_A_conAgot_base': CTE_con_agot_base,
                'CTE_A_conAgot_low(-30%)': CTE_con_agot_low,
                'CTE_A_conAgot_high(+30%)': CTE_con_agot_high,
            })

    df_result = pd.DataFrame(resultados)
    df_result['CTE_A_delta_low'] = df_result['CTE_A_conAgot_low(-30%)'] - df_result['CTE_Base_A']
    df_result['CTE_A_delta_high'] = df_result['CTE_A_conAgot_high(+30%)'] - df_result['CTE_Base_A']

    out_dir = os.path.join(proj_root, 'outputs', 'inventory', 'comparacion')
    ensure_dirs(out_dir)
    path_csv = os.path.join(out_dir, 'sensibilidad_agotamiento_politica_a.csv')
    df_result.to_csv(path_csv, index=False)

    # Gráfico de totales por escenario
    tot_base = df_result['CTE_Base_A'].sum()
    tot_low = df_result['CTE_A_conAgot_low(-30%)'].sum()
    tot_mid = df_result['CTE_A_conAgot_base'].sum()
    tot_high = df_result['CTE_A_conAgot_high(+30%)'].sum()

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ['A (base)', 'A (-30% CA)', 'A (CA base)', 'A (+30% CA)']
    valores = [tot_base, tot_low, tot_mid, tot_high]
    colores = ['#6baed6', '#74c476', '#fd8d3c', '#e34a33']
    ax.bar(labels, valores, color=colores)
    ax.set_title('Sensibilidad Costo de Agotamiento - Política A')
    ax.set_ylabel('CTE total anual ($)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    for i, v in enumerate(valores):
        ax.text(i, v * 1.01, f"${v:,.0f}".replace(',', '.'), ha='center', fontsize=9)
    plt.tight_layout()
    fig_path = os.path.join(out_dir, 'sensibilidad_agotamiento_politica_a.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    return path_csv, fig_path


def sensibilidad_riesgo_plus_15(proj_root: str):
    """Evalúa el impacto de +15% incertidumbre en SS y CTE de ambas políticas.
    
    Política A (costos): incrementa el faltante esperado S = sigma_L · L(k)
                          con sigma_L nuevo = 1.15 · sigma_L original
    Política B (servicio): incrementa SS = z · sigma_L, afectando CTE por H·SS
    """
    df_forecast = cargar_pronostico(proj_root)
    componentes = cargar_componentes_basicos()
    pico_costo, normal_costo, pico_serv, normal_serv = cargar_eoq_outputs(proj_root)

    registros = []

    for _, row in componentes.iterrows():
        dem_mens = demanda_mensual_componente(df_forecast, row)
        for est_nombre, meses, df_a, df_b, fracc in (
            ('PICO', MESES_PICO, pico_costo, pico_serv, FRACCION_PICO),
            ('NORMAL', MESES_NORMAL, normal_costo, normal_serv, FRACCION_NORMAL),
        ):
            D_est, semanas_est, mu_L, sigma_mens, sigma_L = resumen_estacion(
                df_forecast, dem_mens, meses, row['Lead_Time_Semanas']
            )
            # Política A (costos): SS = 0, pero el riesgo incrementa el faltante esperado
            fila_a = df_a[df_a['Componente'] == row['Componente']]
            if fila_a.empty:
                continue
            Q_a = float(fila_a['EOQ'].values[0])
            N_a = float(fila_a['Num_Pedidos'].values[0]) if 'Num_Pedidos' in fila_a.columns else (D_est / Q_a if Q_a > 0 else 0)
            CTE_a = float(fila_a['CTE'].values[0])
            ROP_a = float(fila_a['ROP'].values[0]) if 'ROP' in fila_a.columns else mu_L
            k_a = (ROP_a - mu_L) / sigma_L if sigma_L and sigma_L > 0 else 0.0
            # Faltante base: S = sigma_L · L(k)
            S_base = (sigma_L * std_loss_L(k_a)) if (sigma_L and sigma_L > 0) else 0.0
            # Faltante con +15% sigma: S_up = 1.15·sigma_L · L(k) (k no cambia pues ROP se mantiene)
            S_up15 = (1.15 * sigma_L * std_loss_L(k_a)) if (sigma_L and sigma_L > 0) else 0.0
            # Política B (servicio): SS = z * sigma_L, CTE incluye SS*H
            fila_b = df_b[df_b['Componente'] == row['Componente']]
            if fila_b.empty:
                continue
            Q_b = float(fila_b['EOQ'].values[0])
            D_b_est = float(fila_b['Demanda_Estacion'].values[0])
            N_b = D_b_est / Q_b if Q_b > 0 else 0
            SS_b = float(fila_b['Stock_Seguridad'].values[0]) if 'Stock_Seguridad' in fila_b.columns else Z_ALPHA * sigma_L
            CTE_b = float(fila_b['CTE'].values[0])
            SS_b_up = 1.15 * SS_b
            # Incremento de costo por mayor SS (H anual)
            H_anual = row['Costo_Unitario'] * TASA_MANTENIMIENTO
            delta_cost_b = (SS_b_up - SS_b) * H_anual
            CTE_b_up = CTE_b + delta_cost_b
            registros.append({
                'Componente': row['Componente'],
                'Estacion': est_nombre,
                'CTE_A_base': CTE_a,
                'ROP_A': ROP_a,
                'k_A': k_a,
                'SS_A_base': 0.0,
                'S_esperado_ciclo_A_base': S_base,
                'S_esperado_ciclo_A_up15': S_up15,
                'CTE_B_base': CTE_b,
                'SS_B_base': SS_b,
                'SS_B_up15': SS_b_up,
                'Delta_SS_B': SS_b_up - SS_b,
                'Delta_CTE_B': delta_cost_b,
                'CTE_B_up15': CTE_b_up
            })

    df_riesgo = pd.DataFrame(registros)
    out_dir = os.path.join(proj_root, 'outputs', 'inventory', 'comparacion')
    ensure_dirs(out_dir)
    path_csv = os.path.join(out_dir, 'riesgo_+15.csv')
    df_riesgo.to_csv(path_csv, index=False)

    # Gráfico: incremento total de CTE Política B vs base
    tot_b_base = df_riesgo['CTE_B_base'].sum()
    tot_b_up = df_riesgo['CTE_B_up15'].sum()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(['B base', 'B +15% σ'], [tot_b_base, tot_b_up], color=['#6baed6', '#e34a33'])
    ax.set_title('Sensibilidad al Riesgo (+15% σ) - Política B')
    ax.set_ylabel('CTE total anual ($)')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    for i, v in enumerate([tot_b_base, tot_b_up]):
        ax.text(i, v * 1.01, f"${v:,.0f}".replace(',', '.'), ha='center', fontsize=9)
    plt.tight_layout()
    fig_path = os.path.join(out_dir, 'riesgo_+15_politica_b.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    return path_csv, fig_path


# CLI -------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Análisis de sensibilidad final del proyecto')
    parser.add_argument('--rate-agotamiento', type=float, default=0.50,
                        help='Fracción del costo unitario para el costo de agotamiento (default 0.50)')
    parser.add_argument('--variacion', type=float, default=0.30,
                        help='Variación ± para sensibilidad de agotamiento (default 0.30)')
    args = parser.parse_args()

    script_dir = os.path.dirname(__file__) or os.getcwd()
    proj_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

    print('\n=== Sensibilidad: Costo de Agotamiento (Politica A) ===')
    path1, fig1 = sensibilidad_agotamiento_politica_a(proj_root, args.rate_agotamiento, args.variacion)
    print(f'[OK] Resultados CSV: {path1}')
    print(f'[OK] Grafico: {fig1}')

    print('\n=== Sensibilidad: Riesgo (+15% sigma) en SS y CTE ===')
    path2, fig2 = sensibilidad_riesgo_plus_15(proj_root)
    print(f'[OK] Resultados CSV: {path2}')
    print(f'[OK] Grafico: {fig2}')


if __name__ == '__main__':
    main()
