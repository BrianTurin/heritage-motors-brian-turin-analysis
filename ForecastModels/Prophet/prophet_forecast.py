# ============================
# MODELO DE PRONÓSTICO PROPHET
# Análisis de Tendencia y Estacionalidad
# ============================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

# === 1. CONFIGURACIÓN Y CARGA DE DATOS ===
print("="*60)
print("MODELO DE PRONÓSTICO PROPHET (Facebook/Meta)")
print("="*60)

# Buscar el archivo CSV en rutas comunes
filename = 'sales_data_sample_clean.csv'
script_dir = os.path.dirname(__file__) or os.getcwd()
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
candidate_paths = [
    os.path.join(project_root, 'TPFinal IO', filename),
    os.path.join(project_root, filename),
    os.path.join(script_dir, filename),
]

file_path = None
for p in candidate_paths:
    if os.path.exists(p):
        file_path = p
        break

if file_path is None:
    tried = '\n'.join(candidate_paths)
    raise SystemExit(f"Archivo no encontrado. Rutas probadas:\n{tried}")

print(f"\n✓ Cargando datos desde: {file_path}")
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

print(f"✓ Datos agregados por mes: {len(monthly_sales)} periodos")
print(f"  Rango temporal: {monthly_sales.index.min()} a {monthly_sales.index.max()}")
print(f"  Total ventas: ${monthly_sales.sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

# === 3. PREPARAR DATOS PARA PROPHET ===
# Prophet requiere un DataFrame con columnas 'ds' (fecha) y 'y' (valor)
print("\n--- Preparando datos para Prophet ---")

prophet_df = pd.DataFrame({
    'ds': monthly_sales.index,
    'y': monthly_sales.values
})

print(f"✓ DataFrame preparado: {len(prophet_df)} registros")
print(prophet_df.head())

# === 4. ANÁLISIS EXPLORATORIO ===
print("\n--- Estadísticas descriptivas mensuales ---")
print(prophet_df['y'].describe())

# === 5. MODELO PROPHET ===
print("\n--- Ajustando modelo Prophet ---")

try:
    # Configurar y ajustar el modelo Prophet
    # Prophet detecta automáticamente:
    # - Tendencia (lineal o logística)
    # - Estacionalidad anual, semanal y diaria
    # - Efectos de días festivos (opcional)
    
    model = Prophet(
        yearly_seasonality=True,      # Estacionalidad anual
        weekly_seasonality=False,     # No aplica para datos mensuales
        daily_seasonality=False,      # No aplica para datos mensuales
        seasonality_mode='additive',  # Modo aditivo (similar a Holt-Winters)
        interval_width=0.95,          # Intervalo de confianza del 95%
        changepoint_prior_scale=0.05  # Flexibilidad de cambios de tendencia
    )
    
    # Ajustar el modelo a los datos
    model.fit(prophet_df)
    
    print("✓ Modelo ajustado exitosamente")
    
    # Mostrar parámetros del modelo
    print(f"\n  Parámetros del modelo:")
    print(f"    Modo de estacionalidad:    {'Aditivo' if model.seasonality_mode == 'additive' else 'Multiplicativo'}")
    print(f"    Estacionalidad anual:      {'Sí' if model.yearly_seasonality else 'No'}")
    print(f"    Puntos de cambio detectados: {len(model.changepoints)}")
    print(f"    Intervalo de confianza:    95%")
    
    # === 6. PRONÓSTICO ===
    # Pronosticar los próximos 12 meses
    forecast_periods = 12
    print(f"\n--- Generando pronóstico para {forecast_periods} periodos futuros ---")
    
    # Crear dataframe futuro
    future = model.make_future_dataframe(periods=forecast_periods, freq='MS')
    
    # Generar pronóstico
    forecast = model.predict(future)
    
    # Separar valores históricos y pronóstico
    historical_forecast = forecast[forecast['ds'].isin(prophet_df['ds'])]
    future_forecast = forecast[~forecast['ds'].isin(prophet_df['ds'])]
    
    # Valores ajustados (fitted values)
    fitted_values = historical_forecast[['ds', 'yhat']].copy()
    fitted_values.set_index('ds', inplace=True)
    
    # === 7. MÉTRICAS DE ERROR ===
    print("\n--- Métricas de ajuste del modelo ---")
    
    # Calcular residuos
    residuals = prophet_df['y'].values - historical_forecast['yhat'].values
    
    mae = np.mean(np.abs(residuals))
    mse = np.mean(residuals**2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs(residuals / prophet_df['y'].values)) * 100
    
    print(f"  MAE  (Error Absoluto Medio):     ${mae:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  RMSE (Raíz Error Cuadrático):    ${rmse:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"  MAPE (Error Porcentual Medio):   {mape:.2f}%".replace('.', ','))
    
    # === 8. RESULTADOS DEL PRONÓSTICO ===
    print("\n--- Pronóstico mensual ---")
    print(f"\n{'Periodo':<15} {'Ventas Pronosticadas':>20} {'Límite Inferior':>18} {'Límite Superior':>18}")
    print("-" * 75)
    
    for _, row in future_forecast.iterrows():
        formatted_value = f"${row['yhat']:>15,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        formatted_lower = f"${row['yhat_lower']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        formatted_upper = f"${row['yhat_upper']:>12,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"{row['ds'].strftime('%Y-%m'):<15} {formatted_value} {formatted_lower} {formatted_upper}")
    
    formatted_total = f"${future_forecast['yhat'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    print(f"\n{'TOTAL PRONOSTICADO:'} {formatted_total}")
    
    # === 9. VISUALIZACIONES ===
    print("\n--- Generando gráficos ---")
    
    # Crear figura con diseño personalizado: 1 arriba, 1 en medio (ancho completo), 1 abajo
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.6)
    fig.suptitle('Análisis de Pronóstico Prophet (Facebook/Meta)', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Serie temporal histórica y pronóstico (fila superior)
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(prophet_df['ds'], prophet_df['y'], 
             label='Ventas Históricas', marker='o', linewidth=2, color='steelblue')
    ax1.plot(historical_forecast['ds'], historical_forecast['yhat'], 
             label='Valores Ajustados', linewidth=2, color='orange', alpha=0.7)
    ax1.plot(future_forecast['ds'], future_forecast['yhat'], 
             label='Pronóstico', marker='s', linewidth=2, 
             linestyle='--', color='red')
    # Intervalo de confianza
    ax1.fill_between(future_forecast['ds'], 
                     future_forecast['yhat_lower'], 
                     future_forecast['yhat_upper'],
                     color='red', alpha=0.2, label='Intervalo 95%')
    ax1.axvline(x=prophet_df['ds'].iloc[-1], color='gray', 
                linestyle=':', linewidth=1.5, label='Inicio Pronóstico')
    ax1.set_xlabel('Periodo', fontsize=11)
    ax1.set_ylabel('Ventas ($)', fontsize=11)
    ax1.set_title('Serie Temporal: Histórico vs Pronóstico', fontsize=13, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    # Configurar eje X con todos los meses
    all_dates = list(prophet_df['ds']) + list(future_forecast['ds'])
    ax1.set_xticks(all_dates)
    ax1.set_xticklabels([d.strftime('%y-%m') for d in all_dates], rotation=90, ha='center')
    
    # Gráfico 2: Componente Estacional (fila del medio - ancho completo)
    ax2 = fig.add_subplot(gs[1])
    if 'yearly' in forecast.columns:
        seasonal = forecast['yearly']
    else:
        # Si no hay columna yearly, calcular estacionalidad como diferencia
        seasonal = forecast['yhat'] - forecast['trend']
    ax2.plot(forecast['ds'], seasonal, 
             label='Estacionalidad', linewidth=2, color='purple')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Periodo', fontsize=11)
    ax2.set_ylabel('Componente Estacional ($)', fontsize=11)
    ax2.set_title('Componente de Estacionalidad', fontsize=13, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.1f}K'))
    ax2.set_xticks(forecast['ds'])
    ax2.set_xticklabels([d.strftime('%y-%m') for d in forecast['ds']], rotation=90, ha='center')
    
    # Gráfico 3: Residuos (fila inferior)
    ax3 = fig.add_subplot(gs[2])
    residuals_series = pd.Series(residuals, index=prophet_df['ds'])
    ax3.plot(residuals_series.index, residuals_series.values, 
             marker='o', linestyle='-', linewidth=1.5, 
             color='darkred', alpha=0.6)
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax3.fill_between(residuals_series.index, 0, residuals_series.values, 
                     alpha=0.2, color='red')
    ax3.set_xlabel('Periodo', fontsize=11)
    ax3.set_ylabel('Residuo ($)', fontsize=11)
    ax3.set_title('Residuos del Modelo (Errores)', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax3.set_xticks(residuals_series.index)
    ax3.set_xticklabels([d.strftime('%y-%m') for d in residuals_series.index], rotation=90, ha='center')
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = os.path.join(script_dir, 'prophet_forecast.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Gráfico guardado: {output_path}")
    
    plt.show()
    
    # === 10. GRÁFICOS ADICIONALES DE PROPHET ===
    # Prophet tiene funciones nativas para visualizar componentes
    print("\n--- Generando gráficos de componentes Prophet ---")
    
    fig_components = model.plot_components(forecast)
    components_path = os.path.join(script_dir, 'prophet_components.png')
    fig_components.savefig(components_path, dpi=150, bbox_inches='tight')
    print(f"✓ Componentes guardados: {components_path}")
    plt.close(fig_components)
    
    # === 11. EXPORTAR RESULTADOS ===
    print("\n--- Exportando resultados ---")
    
    # Crear DataFrame con resultados completos
    results_df = pd.DataFrame({
        'Periodo': prophet_df['ds'],
        'Ventas_Historicas': prophet_df['y'],
        'Valores_Ajustados': historical_forecast['yhat'].values,
        'Residuos': residuals
    })
    
    # DataFrame de pronósticos
    forecast_export_df = pd.DataFrame({
        'Periodo': future_forecast['ds'],
        'Pronostico': future_forecast['yhat'].values,
        'Limite_Inferior': future_forecast['yhat_lower'].values,
        'Limite_Superior': future_forecast['yhat_upper'].values
    })
    
    # Exportar a CSV
    results_path = os.path.join(script_dir, 'prophet_results.csv')
    results_df.to_csv(results_path, index=False)
    
    forecast_path = os.path.join(script_dir, 'prophet_forecast.csv')
    forecast_export_df.to_csv(forecast_path, index=False)
    
    print(f"✓ Resultados históricos: {results_path}")
    print(f"✓ Pronóstico: {forecast_path}")
    
    # === 12. RESUMEN FINAL ===
    print("\n" + "="*60)
    print("RESUMEN DEL ANÁLISIS")
    print("="*60)
    print(f"Periodos históricos analizados: {len(prophet_df)}")
    print(f"Periodos pronosticados:         {forecast_periods}")
    print(f"Precisión del modelo (MAPE):    {mape:.2f}%".replace('.', ','))
    print(f"Ventas históricas totales:      ${prophet_df['y'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f"Ventas pronosticadas (12 meses):${future_forecast['yhat'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Determinar tendencia
    trend_start = forecast['trend'].iloc[0]
    trend_end = forecast['trend'].iloc[-1]
    print(f"Tendencia general:              {'Creciente' if trend_end > trend_start else 'Decreciente'}")
    print("="*60)
    
except Exception as e:
    print(f"\n✗ Error al ajustar el modelo: {e}")
    print("\nPosibles soluciones:")
    print("  1. Instala prophet: pip install prophet")
    print("  2. Verifica que tengas suficientes datos")
    print("  3. Revisa que no haya valores faltantes en la serie temporal")
    import traceback
    traceback.print_exc()

# ============================
# Fin del análisis
# ============================
