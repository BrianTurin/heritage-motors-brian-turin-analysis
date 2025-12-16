# ============================
# MODELO DE PRONÓSTICO WINTERS (HOLT-WINTERS)
# Análisis de Tendencia y Estacionalidad
# ============================
"""
winters_forecast.py
===================
Modelo Holt-Winters (Suavización Exponencial Triple).
MAPE ~31.54% - Buena precisión para tendencia y estacionalidad.

Entrada: data/sales_data_sample_clean.csv
Salida:  outputs/forecast/winters_*.csv, outputs/forecast/winters_*.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')

# === 1. CONFIGURACIÓN Y CARGA DE DATOS ===
print("="*60)
print("MODELO DE PRONÓSTICO WINTERS (HOLT-WINTERS)")
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

# Convertir índice Period a Timestamp para compatibilidad con statsmodels
monthly_sales.index = monthly_sales.index.to_timestamp()

print(f"[OK] Datos agregados por mes: {len(monthly_sales)} periodos")
print(f"  Rango temporal: {monthly_sales.index.min()} a {monthly_sales.index.max()}")
print(f"  Total ventas: ${monthly_sales.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 3. ANÁLISIS EXPLORATORIO ===
print("\n--- Estadísticas descriptivas mensuales ---")
print(monthly_sales.describe())

# === 4. MODELO HOLT-WINTERS ===
print("\n--- Ajustando modelo Holt-Winters ---")

# Configuración del modelo
# - trend='add': tendencia aditiva (cambios constantes)
# - seasonal='add': estacionalidad aditiva (cambios estacionales constantes)
# - seasonal_periods=12: ciclo anual (12 meses)

# Si tienes menos de 2 años de datos, ajustar seasonal_periods
n_periods = len(monthly_sales)
if n_periods < 24:
    seasonal_periods = 4  # Ciclo trimestral
    print(f"  ⚠ Datos insuficientes para ciclo anual. Usando ciclo trimestral (4 periodos)")
else:
    seasonal_periods = 12
    print(f"  [OK] Usando ciclo estacional de {seasonal_periods} meses")

try:
    # Ajustar modelo
    model = ExponentialSmoothing(
        monthly_sales,
        trend='add',           # Tendencia aditiva
        seasonal='add',        # Estacionalidad aditiva
        seasonal_periods=seasonal_periods,
        initialization_method='estimated'
    )
    
    # Ajustar el modelo a los datos
    # Usar optimized=True para encontrar los mejores parámetros automáticamente
    # Esto sirve para encontrar alpha, beta, gamma óptimos
    fitted_model = model.fit(optimized=True)
    
    print("[OK] Modelo ajustado exitosamente")
    print(f"\n  Parámetros optimizados:")
    print(f"    α (alpha - nivel):        {fitted_model.params['smoothing_level']:.4f}")
    print(f"    β (beta - tendencia):     {fitted_model.params['smoothing_trend']:.4f}")
    print(f"    γ (gamma - estacionalidad): {fitted_model.params['smoothing_seasonal']:.4f}")
    
    # === 5. PRONÓSTICO ===
    # Pronosticar los próximos 12 meses
    forecast_periods = 12
    print(f"\n--- Generando pronóstico para {forecast_periods} periodos futuros ---")
    
    forecast = fitted_model.forecast(steps=forecast_periods)
    fitted_values = fitted_model.fittedvalues
    
    # === 6. MÉTRICAS DE ERROR ===
    print("\n--- Métricas de ajuste del modelo ---")
    
    # Calcular errores solo donde hay valores ajustados
    valid_idx = fitted_values.index.intersection(monthly_sales.index)
    residuals = monthly_sales.loc[valid_idx] - fitted_values.loc[valid_idx]
    
    mae = np.mean(np.abs(residuals))
    mse = np.mean(residuals**2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs(residuals / monthly_sales.loc[valid_idx])) * 100
    
    print(f"  MAE  (Error Absoluto Medio):     ${mae:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  RMSE (Raíz Error Cuadrático):    ${rmse:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  MAPE (Error Porcentual Medio):   {mape:.2f}%".replace('.', ','))
    
    # === 7. RESULTADOS DEL PRONÓSTICO ===
    print("\n--- Pronóstico mensual ---")
    print(f"\n{'Periodo':<15} {'Ventas Pronosticadas':>20}")
    print("-" * 40)
    for date, value in forecast.items():
        formatted_value = f"${value:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"{date.strftime('%Y-%m'):<15} {formatted_value}")
    
    formatted_total = f"${forecast.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    print(f"\n{'TOTAL PRONOSTICADO:'} {formatted_total}")
    
    # === 8. VISUALIZACIONES ===
    print("\n--- Generando gráficos ---")
    
    # Crear figura con diseño personalizado: 1 arriba, 2 en medio, 1 abajo
    fig = plt.figure(figsize=(14, 14))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], hspace=0.4, wspace=0.3)
    fig.suptitle('Análisis de Pronóstico Winters (Holt-Winters)', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Serie temporal histórica y pronóstico (ocupa toda la fila superior)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(monthly_sales.index, monthly_sales.values, 
             label='Ventas Históricas', marker='o', linewidth=2, color='steelblue')
    ax1.plot(fitted_values.index, fitted_values.values, 
             label='Valores Ajustados', linewidth=2, color='orange', alpha=0.7)
    ax1.plot(forecast.index, forecast.values, 
             label='Pronóstico', marker='s', linewidth=2, 
             linestyle='--', color='red')
    ax1.axvline(x=monthly_sales.index[-1], color='gray', 
                linestyle=':', linewidth=1.5, label='Inicio Pronóstico')
    ax1.set_xlabel('Periodo', fontsize=11)
    ax1.set_ylabel('Ventas ($)', fontsize=11)
    ax1.set_title('Serie Temporal: Histórico vs Pronóstico', fontsize=13, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    # Configurar eje X con todos los meses
    all_dates = monthly_sales.index.union(forecast.index)
    ax1.set_xticks(all_dates)
    ax1.set_xticklabels([d.strftime('%y-%m') for d in all_dates], rotation=90, ha='center')
    
    # Extraer componentes del modelo
    trend = fitted_model.trend
    seasonal = fitted_model.season
    
    # Gráfico 2: Tendencia (lado izquierdo de la fila del medio)
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(trend.index, trend.values, 
             label='Tendencia', linewidth=2.5, color='green')
    ax2.set_xlabel('Periodo', fontsize=11)
    ax2.set_ylabel('Tendencia ($)', fontsize=11)
    ax2.set_title('Componente de Tendencia', fontsize=13, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.1f}K'))
    ax2.set_xticks(trend.index)
    ax2.set_xticklabels([d.strftime('%y-%m') for d in trend.index], rotation=90, ha='center')
    
    # Gráfico 3: Componente Estacional (lado derecho de la fila del medio)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(seasonal.index, seasonal.values, 
             label='Estacionalidad', linewidth=2, color='purple')
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax3.set_xlabel('Periodo', fontsize=11)
    ax3.set_ylabel('Componente Estacional ($)', fontsize=11)
    ax3.set_title('Componente de Estacionalidad', fontsize=13, fontweight='bold')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.1f}K'))
    ax3.set_xticks(seasonal.index)
    ax3.set_xticklabels([d.strftime('%y-%m') for d in seasonal.index], rotation=90, ha='center')
    
    # Gráfico 4: Residuos (fila inferior completa)
    ax4 = fig.add_subplot(gs[2, :])
    ax4.plot(residuals.index, residuals.values, 
             marker='o', linestyle='-', linewidth=1.5, 
             color='darkred', alpha=0.6)
    ax4.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax4.fill_between(residuals.index, 0, residuals.values, 
                     alpha=0.2, color='red')
    ax4.set_xlabel('Periodo', fontsize=11)
    ax4.set_ylabel('Residuo ($)', fontsize=11)
    ax4.set_title('Residuos del Modelo (Errores)', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax4.set_xticks(residuals.index)
    ax4.set_xticklabels([d.strftime('%y-%m') for d in residuals.index], rotation=90, ha='center')
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = os.path.join(output_dir, 'winters_forecast.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Gráfico guardado: {output_path}")
    
    plt.show()
    
    # === 9. EXPORTAR RESULTADOS ===
    print("\n--- Exportando resultados ---")
    
    # Crear DataFrame con resultados completos
    results_df = pd.DataFrame({
        'Periodo': monthly_sales.index,
        'Ventas_Historicas': monthly_sales.values,
        'Valores_Ajustados': fitted_values.values,
        'Residuos': residuals.values
    })
    
    # Agregar pronósticos
    forecast_df = pd.DataFrame({
        'Periodo': forecast.index,
        'Pronostico': forecast.values
    })
    
    # Exportar a CSV
    results_path = os.path.join(output_dir, 'winters_results.csv')
    results_df.to_csv(results_path, index=False)
    
    forecast_path = os.path.join(output_dir, 'winters_forecast.csv')
    forecast_df.to_csv(forecast_path, index=False)
    
    print(f"[OK] Resultados históricos: {results_path}")
    print(f"[OK] Pronóstico: {forecast_path}")
    
    # === 10. RESUMEN FINAL ===
    print("\n" + "="*60)
    print("RESUMEN DEL ANÁLISIS")
    print("="*60)
    print(f"Periodos históricos analizados: {len(monthly_sales)}")
    print(f"Periodos pronosticados:         {forecast_periods}")
    print(f"Precisión del modelo (MAPE):    {mape:.2f}%".replace('.', ','))
    print(f"Ventas históricas totales:      ${monthly_sales.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"Ventas pronosticadas (12 meses):${forecast.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"Tendencia general:              {'Creciente' if trend.iloc[-1] > trend.iloc[0] else 'Decreciente'}")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] Error al ajustar el modelo: {e}")
    print("\nPosibles soluciones:")
    print("  1. Verifica que tengas suficientes datos (mínimo 2 ciclos estacionales)")
    print("  2. Instala statsmodels: pip install statsmodels")
    print("  3. Revisa que no haya valores faltantes en la serie temporal")

# ============================
# Fin del análisis
# ============================
