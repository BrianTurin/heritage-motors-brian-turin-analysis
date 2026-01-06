#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisis de Sensibilidad v2: Costo de Agotamiento y Riesgo (+15% incertidumbre)

JUSTIFICACION DEL c2 (con todos los insumos: 11 componentes):
- Segun enunciado: descuento del 5% sobre PRECIO DEL AUTO
- Clasico: $17,100  -> c2 = 5% = $855
- Vintage: $30,400  -> c2 = 5% = $1,520
- Ambos:   $7,750   -> c2 = 5% = $387

Estos c2 se usan en el modelo Hadley-Whitin (Politica A) y en la sensibilidad.
"""

import os
import math
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Parametros coherentes con el proyecto
Z_ALPHA = 1.645              # 95% servicio
SEMANAS_POR_MES = 4.33
TASA_MANTENIMIENTO = 0.20    # anual

# Utilidades ------------------------------------------------------------------

def std_loss_L(k: float) -> float:
    """Funcion de perdida estandar L(k) = phi(k) - k * (1-Phi(k))."""
    return norm.pdf(k) - k * (1.0 - norm.cdf(k))


def ensure_dirs(path: str):
    os.makedirs(path, exist_ok=True)


# Carga de datos ---------------------------------------------------------------

def cargar_componentes_basicos():
    """Replica la tabla de componentes definida en eoq_estacional.py."""
    return pd.DataFrame({
        'Componente': [
            'Carroceria Artesanal de Epoca',
            'Motor de Alto Rendimiento V8',
            'Motor de Cilindros de Linea Raro',
            'Carroceria Estandar (Fibra)',
            'Tapiceria de Cuero Premium'
        ],
        'Auto_Foco': ['Vintage', 'Clasico', 'Vintage', 'Clasico', 'Ambos'],
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


# Calculos por estacion --------------------------------------------------------
MESES_PICO = [10, 11]
MESES_NORMAL = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12]
FRACCION_PICO = len(MESES_PICO) / 12
FRACCION_NORMAL = len(MESES_NORMAL) / 12


def demanda_mensual_componente(df_forecast: pd.DataFrame, comp_row: pd.Series) -> pd.Series:
    if comp_row['Auto_Foco'] == 'Clasico':
        return df_forecast['Autos_Clasicos'] * comp_row['Uso_por_Auto']
    if comp_row['Auto_Foco'] == 'Vintage':
        return df_forecast['Autos_Vintage'] * comp_row['Uso_por_Auto']
    return (df_forecast['Autos_Clasicos'] + df_forecast['Autos_Vintage']) * comp_row['Uso_por_Auto']


def resumen_estacion(df_forecast: pd.DataFrame, dem_mensual: pd.Series, meses_est: list, lead_time_w: float):
    D_est = dem_mensual[df_forecast['Mes'].isin(meses_est)].sum()
    semanas_est = len(meses_est) * SEMANAS_POR_MES
    demanda_semanal = D_est / semanas_est if semanas_est > 0 else 0.0
    mu_L = demanda_semanal * lead_time_w
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


def std_loss_L(k):
    """Función de pérdida estándar L(k) = phi(k) - k*(1-Phi(k))"""
    return norm.pdf(k) - k * (1 - norm.cdf(k))


def obtener_descuentos_agotamiento():
    """Retorna diccionario de c2 por tipo de auto basado en 5% de descuento.

    Valores recalculados con TODOS los insumos de las tablas (11 componentes):
      - Clasico: $17,100 * 5% = $855
      - Vintage: $30,400 * 5% = $1,520
      - Ambos  :  $7,750 * 5% = $387
    """
    return {
        'Clasico': 855,
        'Vintage': 1520,
        'Ambos': 387
    }


def obtener_tipo_auto_componente(componente):
    """Retorna el tipo de auto ('Clasico', 'Vintage', 'Ambos') segun el componente.

    Se usa coincidencia por substring en minúsculas para ser robustos a acentos/encoding.
    """
    name = str(componente).lower()
    if 'rendimiento v8' in name:
        return 'Clasico'
    if 'cilindros' in name and 'linea' in name:
        return 'Vintage'
    if 'artesanal' in name or 'epoca' in name:
        return 'Vintage'
    if 'fibra' in name or 'estandar' in name:
        return 'Clasico'
    if 'inyeccion electronica' in name:
        return 'Clasico'
    if 'carburadores dobles' in name:
        return 'Vintage'
    if 'llantas vintage' in name:
        return 'Vintage'
    if 'llantas regulares' in name or 'cromados' in name:
        return 'Clasico'
    if 'transmision' in name or 'velocidades' in name:
        return 'Ambos'
    if 'cubiertas' in name or 'neumatic' in name:
        return 'Ambos'
    if 'tapiceria' in name or 'cuero' in name:
        return 'Ambos'
    return 'Ambos'


def sensibilidad_agotamiento_politica_a(proj_root: str, descuentos_agotamiento: dict, variacion: float):
    """Evalua el efecto del costo de agotamiento en la CTE de la Politica A.
    
    Implementa modelo Hadley-Whitin estocastico con c2 basado en descuentos reales.
    
    CTE = (K*D)/q + c1*(q/2 + SR - E[x]) + (c2*D/q)*S
    donde S = sigma_L * L(k) es el faltante esperado por ciclo.
    """
    df_forecast = cargar_pronostico(proj_root)
    pico_costo, normal_costo, _, _ = cargar_eoq_outputs(proj_root)

    resultados = []

    for estacion, df_eoq in [('PICO', pico_costo), ('NORMAL', normal_costo)]:
        for idx, row in df_eoq.iterrows():
            componente = row['Componente']
            auto_foco = obtener_tipo_auto_componente(componente)
            costo_unitario = row['Costo_Unitario']
            
            # Obtener c2 segun tipo de auto
            c_agot_base = descuentos_agotamiento[auto_foco]
            c_agot_low = (1 - variacion) * c_agot_base
            c_agot_high = (1 + variacion) * c_agot_base

            # Demanda en la estacion
            D_est = float(row['Demanda_Estacion'])
            # Para anualizar: si es PICO, multiplica por 12/2, si es NORMAL por 12/10
            D_anual = D_est * 12 / (2 if estacion == 'PICO' else 10)
            
            Q = float(row['EOQ'])
            K = 300.0  # Costo de orden (fijo)
            c_mant = 0.20 * costo_unitario  # c1 = 20% del CU
            
            # CTE sin agotamiento (Politica A base)
            CTE_base_A = (K * D_anual) / Q + c_mant * (Q / 2)

            # Parametros de demanda durante lead time (usamos ROP del CSV)
            ROP = float(row['ROP']) if 'ROP' in row.index else 0
            
            # Estimamos sigma_L basado en la variabilidad de la demanda
            # sigma_L es la desviacion de la demanda durante el lead time
            # Usamos una aproximacion: sigma_L ~ demanda_estacion * 0.15 (coef de variacion del 15%)
            sigma_L = D_est * 0.15
            mu_L = D_est / 2  # Aproximacion de demanda media durante lead time
            
            k = (ROP - mu_L) / sigma_L if sigma_L and sigma_L > 0 else 0.0

            # Faltante esperado por ciclo: S = sigma_L * L(k)
            S = (sigma_L * std_loss_L(k)) if (sigma_L and sigma_L > 0) else 0.0
            
            # Faltante anual segun Hadley-Whitin: (D/q) * S
            faltante_anual = (D_est / Q) * S if Q > 0 else 0.0

            # Costos de agotamiento anuales por escenario
            costo_agot_base = c_agot_base * faltante_anual
            costo_agot_low = c_agot_low * faltante_anual
            costo_agot_high = c_agot_high * faltante_anual
            
            CTE_con_agot_base = CTE_base_A + costo_agot_base
            CTE_con_agot_low = CTE_base_A + costo_agot_low
            CTE_con_agot_high = CTE_base_A + costo_agot_high

            resultados.append({
                'Componente': componente,
                'Estacion': estacion,
                'Auto_Foco': auto_foco,
                'CTE_Base_A': CTE_base_A,
                'c2_Base': c_agot_base,
                'c2_Low': c_agot_low,
                'c2_High': c_agot_high,
                'Faltante_Anual': faltante_anual,
                'CTE_A_conAgot_base': CTE_con_agot_base,
                'CTE_A_conAgot_low': CTE_con_agot_low,
                'CTE_A_conAgot_high': CTE_con_agot_high,
                'Costo_Agot_Base': costo_agot_base,
                'Costo_Agot_Low': costo_agot_low,
                'Costo_Agot_High': costo_agot_high,
                'sigma_L': sigma_L,
                'k': k
            })

    df_resultado = pd.DataFrame(resultados)
    
    # Guardar CSV
    outputs_dir = os.path.join(proj_root, 'outputs', 'inventory', 'comparacion')
    os.makedirs(outputs_dir, exist_ok=True)
    
    csv_path = os.path.join(outputs_dir, 'sensibilidad_agotamiento_politica_a_v2.csv')
    df_resultado.to_csv(csv_path, index=False)
    
    # Crear visualizacion
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Sensibilidad Costo de Agotamiento - Politica A (c2 justificado por descuento 5pct)', fontsize=14)
    
    # Grafico 1: CTE total por componente
    ax = axes[0, 0]
    df_pivot = df_resultado.pivot_table(values='CTE_A_conAgot_base', index='Componente', aggfunc='sum')
    df_pivot.plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title('CTE Total por Componente (c2 Base)')
    ax.set_ylabel('CTE (USD)')
    ax.set_xlabel('')
    ax.grid(True, alpha=0.3)
    
    # Grafico 2: Variacion de CTE con +-30pct c2
    ax = axes[0, 1]
    df_pivot_low = df_resultado.pivot_table(values='CTE_A_conAgot_low', index='Componente', aggfunc='sum')
    df_pivot_base = df_resultado.pivot_table(values='CTE_A_conAgot_base', index='Componente', aggfunc='sum')
    df_pivot_high = df_resultado.pivot_table(values='CTE_A_conAgot_high', index='Componente', aggfunc='sum')
    
    x = np.arange(len(df_pivot_base))
    width = 0.25
    ax.bar(x - width, df_pivot_low.values.flatten(), width, label='c2 -30pct', alpha=0.8)
    ax.bar(x, df_pivot_base.values.flatten(), width, label='c2 Base', alpha=0.8)
    ax.bar(x + width, df_pivot_high.values.flatten(), width, label='c2 +30pct', alpha=0.8)
    ax.set_ylabel('CTE (USD)')
    ax.set_title('Impacto de +-30pct en c2')
    ax.set_xticks(x)
    ax.set_xticklabels(df_pivot_base.index, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Grafico 3: Costo anual de faltantes por estacion
    ax = axes[1, 0]
    df_pico = df_resultado[df_resultado['Estacion'] == 'PICO'].groupby('Componente')['Costo_Agot_Base'].sum()
    df_normal = df_resultado[df_resultado['Estacion'] == 'NORMAL'].groupby('Componente')['Costo_Agot_Base'].sum()
    
    x = np.arange(len(df_pico))
    width = 0.35
    ax.bar(x - width/2, df_pico.values, width, label='PICO', alpha=0.8)
    ax.bar(x + width/2, df_normal.values, width, label='NORMAL', alpha=0.8)
    ax.set_ylabel('Costo de Faltantes (USD)')
    ax.set_title('Costo Anual de Faltantes por Estacion')
    ax.set_xticks(x)
    ax.set_xticklabels(df_pico.index, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Grafico 4: Resumen de deltas
    ax = axes[1, 1]
    df_resultado['Delta_Low'] = df_resultado['CTE_A_conAgot_low'] - df_resultado['CTE_A_conAgot_base']
    df_resultado['Delta_High'] = df_resultado['CTE_A_conAgot_high'] - df_resultado['CTE_A_conAgot_base']
    
    df_delta = df_resultado.groupby('Componente')[['Delta_Low', 'Delta_High']].sum()
    
    x = np.arange(len(df_delta))
    width = 0.35
    ax.bar(x - width/2, df_delta['Delta_Low'].values, width, label='Delta c2 -30pct', alpha=0.8, color='red')
    ax.bar(x + width/2, df_delta['Delta_High'].values, width, label='Delta c2 +30pct', alpha=0.8, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_ylabel('Cambio en CTE (USD)')
    ax.set_title('Impacto Simetrico en CTE (+-30pct c2)')
    ax.set_xticks(x)
    ax.set_xticklabels(df_delta.index, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    png_path = os.path.join(outputs_dir, 'sensibilidad_agotamiento_politica_a_v2.png')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Grafico de resumen (totales A base vs A con c2 ±30%)
    tot_base = df_resultado['CTE_Base_A'].sum()
    tot_low = df_resultado['CTE_A_conAgot_low'].sum()
    tot_mid = df_resultado['CTE_A_conAgot_base'].sum()
    tot_high = df_resultado['CTE_A_conAgot_high'].sum()

    labels = ['A (base)', 'A (-30% CA)', 'A (CA base)', 'A (+30% CA)']
    values = [tot_base, tot_low, tot_mid, tot_high]
    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728']

    plt.figure(figsize=(12, 6))
    bars = plt.bar(labels, values, color=colors, alpha=0.85)
    plt.title('Sensibilidad Costo de Agotamiento - Totales Politica A (c2 5% precio auto)')
    plt.ylabel('CTE total anual (USD)')
    plt.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, values):
        plt.text(bar.get_x() + bar.get_width() / 2, val, f"${val:,.0f}", ha='center', va='bottom')

    plt.tight_layout()
    png_path_tot = os.path.join(outputs_dir, 'sensibilidad_agotamiento_totales_v2.png')
    plt.savefig(png_path_tot, dpi=300, bbox_inches='tight')
    # Sobrescribimos el nombre clasico para evitar confusiones
    png_path_legacy = os.path.join(outputs_dir, 'sensibilidad_agotamiento_politica_a.png')
    plt.savefig(png_path_legacy, dpi=300, bbox_inches='tight')
    plt.close()
    
    return csv_path, png_path


def sensibilidad_riesgo_plus_15(proj_root: str, descuentos_agotamiento: dict):
    """Evalua el efecto de +15% de incertidumbre en ambas politicas."""
    pico_costo, normal_costo, pico_servicio, normal_servicio = cargar_eoq_outputs(proj_root)

    resultados = []

    for estacion, df_costo, df_servicio in [
        ('PICO', pico_costo, pico_servicio),
        ('NORMAL', normal_costo, normal_servicio)
    ]:
        for idx_c, row_costo in df_costo.iterrows():
            componente = row_costo['Componente']
            costo_unitario = row_costo['Costo_Unitario']
            auto_foco = obtener_tipo_auto_componente(componente)
            c_agot_base = descuentos_agotamiento[auto_foco]
            
            # Buscar correspondiente en servicio
            row_servicio = df_servicio[df_servicio['Componente'] == componente]
            if row_servicio.empty:
                continue
            row_servicio = row_servicio.iloc[0]

            D_est = float(row_costo['Demanda_Estacion'])
            # Anualizar
            D_anual = D_est * 12 / (2 if estacion == 'PICO' else 10)
            
            Q_A = float(row_costo['EOQ'])
            Q_B = float(row_servicio['EOQ'])
            K = 300.0
            c_mant = 0.20 * costo_unitario
            
            # Politica A base
            CTE_A_base = (K * D_anual) / Q_A + c_mant * (Q_A / 2)
            
            ROP = float(row_costo['ROP']) if 'ROP' in row_costo.index else 0
            sigma_L = D_est * 0.15  # Coef variacion
            mu_L = D_est / 2
            k = (ROP - mu_L) / sigma_L if sigma_L and sigma_L > 0 else 0.0
            
            S = (sigma_L * std_loss_L(k)) if (sigma_L and sigma_L > 0) else 0.0
            faltante_anual = (D_anual / Q_A) * S if Q_A > 0 else 0.0
            costo_agot_A = c_agot_base * faltante_anual
            CTE_A_conAgot = CTE_A_base + costo_agot_A
            
            # Politica A con +15% incertidumbre
            sigma_L_up15 = sigma_L * 1.15
            S_up15 = (sigma_L_up15 * std_loss_L(k)) if sigma_L_up15 > 0 else 0.0
            faltante_anual_up15 = (D_anual / Q_A) * S_up15 if Q_A > 0 else 0.0
            costo_agot_A_up15 = c_agot_base * faltante_anual_up15
            CTE_A_up15 = CTE_A_base + costo_agot_A_up15
            
            # Politica B (servicios)
            SS_B = float(row_servicio['SS']) if 'SS' in row_servicio.index else 0
            H = c_mant
            
            CTE_B_base = (K * D_anual) / Q_B + H * (Q_B / 2 + SS_B)
            
            # Politica B con +15% SS
            SS_B_up15 = SS_B * 1.15
            CTE_B_up15 = (K * D_anual) / Q_B + H * (Q_B / 2 + SS_B_up15)

            resultados.append({
                'Componente': componente,
                'Estacion': estacion,
                'Auto_Foco': auto_foco,
                'CTE_A_conAgot_base': CTE_A_conAgot,
                'CTE_A_conAgot_up15': CTE_A_up15,
                'Delta_CTE_A': CTE_A_up15 - CTE_A_conAgot,
                'CTE_B_base': CTE_B_base,
                'CTE_B_up15': CTE_B_up15,
                'Delta_CTE_B': CTE_B_up15 - CTE_B_base
            })

    df_resultado = pd.DataFrame(resultados)
    
    outputs_dir = os.path.join(proj_root, 'outputs', 'inventory', 'comparacion')
    csv_path = os.path.join(outputs_dir, 'riesgo_mas_15_v2.csv')
    df_resultado.to_csv(csv_path, index=False)
    
    return csv_path


def main():
    parser = __import__('argparse').ArgumentParser(description='Analisis de sensibilidad v2')
    args = parser.parse_args()

    script_dir = os.path.dirname(__file__) or os.getcwd()
    proj_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

    print('\n=== Sensibilidad: Costo de Agotamiento (Politica A - v2) ===')
    descuentos = obtener_descuentos_agotamiento()
    print('Descuentos c2 por tipo de auto:')
    for tipo, valor in descuentos.items():
        print('  %s: $%d' % (tipo, valor))
    
    csv1, png1 = sensibilidad_agotamiento_politica_a(proj_root, descuentos, 0.30)
    print('\nArchivos generados:')
    print('  CSV: %s' % csv1)
    print('  PNG: %s' % png1)

    print('\n=== Sensibilidad: Riesgo +15%% (Politicas A y B) ===')
    csv2 = sensibilidad_riesgo_plus_15(proj_root, descuentos)
    print('  CSV: %s' % csv2)


if __name__ == '__main__':
    main()
