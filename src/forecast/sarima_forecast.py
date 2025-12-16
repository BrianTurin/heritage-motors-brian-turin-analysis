# ============================
# MODELO DE PRONÓSTICO SARIMA
# Seasonal Autoregressive Integrated Moving Average
# ============================
"""
sarima_forecast.py
==================
Modelo SARIMA para pronóstico de series temporales estacionales.
MAPE ~41.48% - Intervalos de confianza amplios con pocos datos.

Entrada: data/sales_data_sample_clean.csv
Salida:  outputs/forecast/sarima_*.csv, outputs/forecast/sarima_*.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, acf, pacf
import warnings
warnings.filterwarnings('ignore')

# === 1. CONFIGURACIÓN Y CARGA DE DATOS ===
print("="*60)
print("MODELO DE PRONÓSTICO SARIMA")
print("(Seasonal Autoregressive Integrated Moving Average)")
print("="*60)

# Configurar rutas
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
data_dir = os.path.join(project_root, 'data')
output_dir = os.path.join(project_root, 'outputs', 'forecast')

os.makedirs(output_dir, exist_ok=True)

filename = 'sales_data_sample_clean.csv'
file_path = os.path.join(data_dir, filename)

if not os.path.exists(file_path):
    raise SystemExit(f"Archivo no encontrado: {file_path}\n\nAsegurate de tener el dataset en data/")

print(f"\n[CARGA] Cargando datos desde: {file_path}")
df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)

# === 2. PREPARACIÓN DE DATOS TEMPORALES ===
print("\n--- Preparando serie temporal ---")

# Convertir ORDERDATE a formato datetime
df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], format='%m/%d/%Y %H:%M', errors='coerce')

# Crear columna de periodo (Año-Mes) para agregación
df['PERIOD'] = df['ORDERDATE'].dt.to_period('M')

# Agregar ventas por mes
monthly_sales = df.groupby('PERIOD')['SALES'].sum().sort_index()

# Convertir índice Period a Timestamp para compatibilidad
monthly_sales.index = monthly_sales.index.to_timestamp()

# Asegurar frecuencia mensual
monthly_sales = monthly_sales.asfreq('MS')

print(f"[OK] Datos agregados por mes: {len(monthly_sales)} periodos")
print(f"  Rango temporal: {monthly_sales.index.min()} a {monthly_sales.index.max()}")
print(f"  Total ventas: ${monthly_sales.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 3. ANÁLISIS DE ESTACIONARIEDAD ===
print("\n--- Analisis de estacionariedad (Test ADF) ---")

def adf_test(series, name='Serie'):
    """Realiza el test de Dickey-Fuller aumentado"""
    result = adfuller(series.dropna(), autolag='AIC')
    print(f"  {name}:")
    print(f"    Estadistico ADF: {result[0]:.4f}")
    print(f"    p-valor:         {result[1]:.4f}")
    print(f"    Valores criticos:")
    for key, value in result[4].items():
        print(f"      {key}: {value:.4f}")
    
    if result[1] <= 0.05:
        print(f"    Conclusion: Serie ESTACIONARIA (p <= 0.05)")
        return True
    else:
        print(f"    Conclusion: Serie NO ESTACIONARIA (p > 0.05)")
        return False

is_stationary = adf_test(monthly_sales, "Ventas mensuales")

# === 4. ANÁLISIS EXPLORATORIO ===
print("\n--- Estadisticas descriptivas mensuales ---")
print(monthly_sales.describe())

# === 5. MODELO SARIMA ===
print("\n--- Ajustando modelo SARIMA ---")

try:
    # SARIMA(p,d,q)(P,D,Q,s)
    # p: orden autorregresivo (AR)
    # d: orden de diferenciación
    # q: orden de media móvil (MA)
    # P: orden autorregresivo estacional
    # D: orden de diferenciación estacional
    # Q: orden de media móvil estacional
    # s: período estacional (12 para datos mensuales)
    
    # Para series cortas (29 meses), usar diferenciación estacional D=0
    # para no perder demasiados datos
    order = (1, 1, 1)           # (p, d, q) - componentes no estacionales
    seasonal_order = (1, 0, 1, 12)  # (P, D, Q, s) - componentes estacionales (D=0)
    
    print(f"  Configuracion SARIMA{order}x{seasonal_order}")
    print(f"    Componentes no estacionales (p,d,q): {order}")
    print(f"      p (AR):  {order[0]} - Terminos autorregresivos")
    print(f"      d (I):   {order[1]} - Orden de diferenciacion")
    print(f"      q (MA):  {order[2]} - Terminos de media movil")
    print(f"    Componentes estacionales (P,D,Q,s): {seasonal_order}")
    print(f"      P (SAR): {seasonal_order[0]} - Terminos AR estacionales")
    print(f"      D (SI):  {seasonal_order[1]} - Diferenciacion estacional")
    print(f"      Q (SMA): {seasonal_order[2]} - Terminos MA estacionales")
    print(f"      s:       {seasonal_order[3]} - Periodo estacional (meses)")
    
    # Ajustar modelo SARIMA
    model = SARIMAX(
        monthly_sales,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    
    fitted_model = model.fit(disp=False)
    
    print("\n[OK] Modelo ajustado exitosamente")
    
    # === PARÁMETROS DEL MODELO ===
    print("\n--- Parametros estimados del modelo SARIMA ---")
    print("    Modelo: SARIMA(p,d,q)(P,D,Q)s")
    print("    y_t = c + phi*y_(t-1) + theta*e_(t-1) + Phi*y_(t-s) + Theta*e_(t-s) + e_t")
    
    params = fitted_model.params
    print(f"\n  [COMPONENTES NO ESTACIONALES]")
    if 'ar.L1' in params.index:
        print(f"    phi_1 (AR1):     {params['ar.L1']:.6f}")
    if 'ma.L1' in params.index:
        print(f"    theta_1 (MA1):   {params['ma.L1']:.6f}")
    
    print(f"\n  [COMPONENTES ESTACIONALES]")
    if 'ar.S.L12' in params.index:
        print(f"    Phi_1 (SAR12):   {params['ar.S.L12']:.6f}")
    if 'ma.S.L12' in params.index:
        print(f"    Theta_1 (SMA12): {params['ma.S.L12']:.6f}")
    
    print(f"\n  [VARIANZA DEL ERROR]")
    if 'sigma2' in params.index:
        sigma2 = params['sigma2']
        print(f"    sigma^2:         {sigma2:.2f}")
        print(f"    sigma:           {np.sqrt(sigma2):.2f}")
    
    # Criterios de información
    print(f"\n  [CRITERIOS DE INFORMACION]")
    print(f"    AIC:  {fitted_model.aic:.2f}")
    print(f"    BIC:  {fitted_model.bic:.2f}")
    print(f"    HQIC: {fitted_model.hqic:.2f}")
    
    # === 6. PRONÓSTICO ===
    forecast_periods = 12
    print(f"\n--- Generando pronostico para {forecast_periods} periodos futuros ---")
    
    # Generar pronóstico con intervalos de confianza
    forecast_result = fitted_model.get_forecast(steps=forecast_periods)
    forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=0.05)  # 95% de confianza
    
    # Valores ajustados (fitted values)
    fitted_values = fitted_model.fittedvalues
    
    # === 7. MÉTRICAS DE ERROR ===
    print("\n--- Metricas de ajuste del modelo ---")
    
    # Calcular residuos (excluir primeros valores por diferenciación)
    valid_idx = fitted_values.index.intersection(monthly_sales.index)
    # Excluir primer valor por diferenciación d=1
    start_idx = 1
    valid_idx = valid_idx[start_idx:]
    
    residuals = monthly_sales.loc[valid_idx] - fitted_values.loc[valid_idx]
    
    mae = np.mean(np.abs(residuals))
    mse = np.mean(residuals**2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs(residuals / monthly_sales.loc[valid_idx])) * 100
    
    print(f"  MAE  (Error Absoluto Medio):     ${mae:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  RMSE (Raiz Error Cuadratico):    ${rmse:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  MAPE (Error Porcentual Medio):   {mape:.2f}%".replace('.', ','))
    
    # === 8. RESULTADOS DEL PRONÓSTICO ===
    print("\n--- Pronostico mensual ---")
    print(f"\n{'Periodo':<15} {'Ventas Pronosticadas':>20} {'Limite Inferior':>18} {'Limite Superior':>18}")
    print("-" * 75)
    
    for i, (date, value) in enumerate(forecast.items()):
        lower = conf_int.iloc[i, 0]
        upper = conf_int.iloc[i, 1]
        formatted_value = f"${value:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        formatted_lower = f"${lower:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        formatted_upper = f"${upper:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"{date.strftime('%Y-%m'):<15} {formatted_value} {formatted_lower} {formatted_upper}")
    
    formatted_total = f"${forecast.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    print(f"\n{'TOTAL PRONOSTICADO:'} {formatted_total}")
    
    # === 9. VISUALIZACIONES ===
    print("\n--- Generando graficos ---")
    
    # Crear figura con diseño personalizado
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.6)
    fig.suptitle('Analisis de Pronostico SARIMA', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Serie temporal histórica y pronóstico
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(monthly_sales.index, monthly_sales.values, 
             label='Ventas Historicas', marker='o', linewidth=2, color='steelblue')
    ax1.plot(fitted_values.index, fitted_values.values, 
             label='Valores Ajustados', linewidth=2, color='orange', alpha=0.7)
    ax1.plot(forecast.index, forecast.values, 
             label='Pronostico', marker='s', linewidth=2, 
             linestyle='--', color='red')
    # Intervalo de confianza
    ax1.fill_between(forecast.index, 
                     conf_int.iloc[:, 0], 
                     conf_int.iloc[:, 1],
                     color='red', alpha=0.2, label='Intervalo 95%')
    ax1.axvline(x=monthly_sales.index[-1], color='gray', 
                linestyle=':', linewidth=1.5, label='Inicio Pronostico')
    ax1.set_xlabel('Periodo', fontsize=11)
    ax1.set_ylabel('Ventas ($)', fontsize=11)
    ax1.set_title('Serie Temporal: Historico vs Pronostico', fontsize=13, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    # Configurar eje X con todos los meses
    all_dates = list(monthly_sales.index) + list(forecast.index)
    ax1.set_xticks(all_dates)
    ax1.set_xticklabels([d.strftime('%y-%m') for d in all_dates], rotation=90, ha='center')
    
    # Gráfico 2: Componentes ACF/PACF de residuos
    ax2 = fig.add_subplot(gs[1])
    resid = fitted_model.resid[start_idx:]
    ax2.plot(resid.index, resid.values, 
             label='Residuos', linewidth=1.5, color='purple', alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax2.fill_between(resid.index, 0, resid.values, alpha=0.3, color='purple')
    ax2.set_xlabel('Periodo', fontsize=11)
    ax2.set_ylabel('Residuo ($)', fontsize=11)
    ax2.set_title('Residuos del Modelo SARIMA', fontsize=13, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax2.set_xticks(resid.index)
    ax2.set_xticklabels([d.strftime('%y-%m') for d in resid.index], rotation=90, ha='center')
    
    # Gráfico 3: Diagnóstico - Distribución de residuos
    ax3 = fig.add_subplot(gs[2])
    # Histograma de residuos
    ax3.hist(resid.values, bins=15, density=True, alpha=0.7, color='teal', edgecolor='black')
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Media = 0')
    ax3.axvline(x=resid.mean(), color='orange', linestyle='-', linewidth=2, 
                label=f'Media real = ${resid.mean():,.0f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    ax3.set_xlabel('Residuo ($)', fontsize=11)
    ax3.set_ylabel('Densidad', fontsize=11)
    ax3.set_title('Distribucion de Residuos', fontsize=13, fontweight='bold')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = os.path.join(output_dir, 'sarima_forecast.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Grafico guardado: {output_path}")
    
    plt.close(fig)
    
    # === 10. GRÁFICO DE DIAGNÓSTICO ADICIONAL ===
    print("\n--- Generando grafico de diagnostico ---")
    
    fig_diag = plt.figure(figsize=(12, 8))
    fig_diag.suptitle('Diagnostico del Modelo SARIMA', fontsize=14, fontweight='bold')
    
    # ACF de residuos
    ax_acf = fig_diag.add_subplot(2, 2, 1)
    n_lags = min(10, len(resid.dropna()) // 2 - 1)  # Ajustar lags para datos cortos
    acf_vals = acf(resid.dropna(), nlags=n_lags)
    ax_acf.bar(range(len(acf_vals)), acf_vals, color='steelblue', alpha=0.7)
    ax_acf.axhline(y=0, color='black', linewidth=1)
    ax_acf.axhline(y=1.96/np.sqrt(len(resid)), color='red', linestyle='--', alpha=0.7)
    ax_acf.axhline(y=-1.96/np.sqrt(len(resid)), color='red', linestyle='--', alpha=0.7)
    ax_acf.set_title('ACF de Residuos', fontsize=11)
    ax_acf.set_xlabel('Lag')
    ax_acf.set_ylabel('Autocorrelacion')
    
    # PACF de residuos
    ax_pacf = fig_diag.add_subplot(2, 2, 2)
    pacf_vals = pacf(resid.dropna(), nlags=n_lags)
    ax_pacf.bar(range(len(pacf_vals)), pacf_vals, color='teal', alpha=0.7)
    ax_pacf.axhline(y=0, color='black', linewidth=1)
    ax_pacf.axhline(y=1.96/np.sqrt(len(resid)), color='red', linestyle='--', alpha=0.7)
    ax_pacf.axhline(y=-1.96/np.sqrt(len(resid)), color='red', linestyle='--', alpha=0.7)
    ax_pacf.set_title('PACF de Residuos', fontsize=11)
    ax_pacf.set_xlabel('Lag')
    ax_pacf.set_ylabel('Autocorrelacion Parcial')
    
    # Q-Q Plot
    ax_qq = fig_diag.add_subplot(2, 2, 3)
    from scipy import stats
    stats.probplot(resid.dropna(), dist="norm", plot=ax_qq)
    ax_qq.set_title('Q-Q Plot de Residuos', fontsize=11)
    ax_qq.grid(True, alpha=0.3)
    
    # Serie de residuos estandarizados
    ax_std = fig_diag.add_subplot(2, 2, 4)
    std_resid = resid / resid.std()
    ax_std.plot(std_resid.index, std_resid.values, marker='o', linestyle='-', 
                color='darkgreen', alpha=0.6, markersize=4)
    ax_std.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax_std.axhline(y=2, color='red', linestyle='--', alpha=0.7)
    ax_std.axhline(y=-2, color='red', linestyle='--', alpha=0.7)
    ax_std.set_title('Residuos Estandarizados', fontsize=11)
    ax_std.set_xlabel('Periodo')
    ax_std.set_ylabel('Residuo Estandarizado')
    ax_std.set_xticks(std_resid.index)
    ax_std.set_xticklabels([d.strftime('%y-%m') for d in std_resid.index], rotation=90, ha='center')
    ax_std.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    diag_path = os.path.join(output_dir, 'sarima_diagnostics.png')
    fig_diag.savefig(diag_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Diagnostico guardado: {diag_path}")
    plt.close(fig_diag)
    
    # === 11. EXPORTAR RESULTADOS ===
    print("\n--- Exportando resultados ---")
    
    # Crear DataFrame con resultados completos
    results_df = pd.DataFrame({
        'Periodo': monthly_sales.index,
        'Ventas_Historicas': monthly_sales.values,
        'Valores_Ajustados': fitted_values.values,
        'Residuos': (monthly_sales - fitted_values).values
    })
    
    # DataFrame de pronósticos
    forecast_export_df = pd.DataFrame({
        'Periodo': forecast.index,
        'Pronostico': forecast.values,
        'Limite_Inferior': conf_int.iloc[:, 0].values,
        'Limite_Superior': conf_int.iloc[:, 1].values
    })
    
    # Exportar a CSV
    results_path = os.path.join(output_dir, 'sarima_results.csv')
    results_df.to_csv(results_path, index=False)
    
    forecast_path = os.path.join(output_dir, 'sarima_forecast.csv')
    forecast_export_df.to_csv(forecast_path, index=False)
    
    print(f"[OK] Resultados historicos: {results_path}")
    print(f"[OK] Pronostico: {forecast_path}")
    
    # === 12. RESUMEN FINAL ===
    print("\n" + "="*60)
    print("RESUMEN DEL ANALISIS")
    print("="*60)
    print(f"Modelo:                         SARIMA{order}x{seasonal_order}")
    print(f"Periodos historicos analizados: {len(monthly_sales)}")
    print(f"Periodos pronosticados:         {forecast_periods}")
    print(f"Precision del modelo (MAPE):    {mape:.2f}%".replace('.', ','))
    print(f"AIC:                            {fitted_model.aic:.2f}")
    print(f"BIC:                            {fitted_model.bic:.2f}")
    print(f"Ventas historicas totales:      ${monthly_sales.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"Ventas pronosticadas (12 meses):${forecast.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] Error al ajustar el modelo: {e}")
    print("\nPosibles soluciones:")
    print("  1. Verifica que tengas suficientes datos (minimo 2 ciclos estacionales)")
    print("  2. Intenta con diferentes ordenes (p,d,q) y (P,D,Q,s)")
    print("  3. Revisa que no haya valores faltantes en la serie temporal")
    import traceback
    traceback.print_exc()