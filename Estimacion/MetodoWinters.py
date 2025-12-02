import os
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# === 1. Ruta del archivo ===
ruta_csv = r"C:\Users\User\Documents\GitHub\RepoProyectoIO\ventaspormes.csv"

# === 2. Cargar dataset ===
df = pd.read_csv(ruta_csv)
df = df.iloc[:-5]  # Eliminar las últimas 5 filas
# === 3. Definir cuántos meses predecir ===
meses_a_predecir = 12

# === 4. Crear DataFrame de salida ===
df_resultado = pd.DataFrame({"Mes": list(range(1, len(df) + meses_a_predecir + 1))})

# === 5. Aplicar Holt-Winters a cada columna de ventas ===
for columna in df.columns[1:]:
    serie = df[columna]

    # Crear y ajustar el modelo (additivo = tendencia + estacionalidad moderada)
    modelo = ExponentialSmoothing(serie, trend='add', seasonal='add', seasonal_periods=12).fit()

    # Generar pronóstico
    predicciones = modelo.forecast(meses_a_predecir)

    # Combinar original + predicción
    serie_completa = pd.concat([serie, predicciones], ignore_index=True)
    df_resultado[columna + " Estimado"] = serie_completa

# === 6. Exportar a CSV ===
salida = os.path.join(os.getcwd(), "ventas_estimadas_cError.csv")
df_resultado.to_csv(salida, index=False)

# === 7. Calcular y mostrar el promedio total anual ===
promedios_anuales = df_resultado.iloc[:, 1:].sum() / 3  # Dividir por 3 para obtener el promedio anual

for tipo_auto, promedio in promedios_anuales.items():
    print(f"Promedio total anual para {tipo_auto}: {promedio:.2f}")

