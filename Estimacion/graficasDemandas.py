import matplotlib.pyplot as plt
import pandas as pd

ruta_csv = r"C:\Users\User\Documents\GitHub\RepoProyectoIO\Estimacion\ventas_estimadas.csv"
dfSE = pd.read_csv(ruta_csv)

ruta_csv = r"C:\Users\User\Documents\GitHub\RepoProyectoIO\Estimacion\ventas_estimadas_cError.csv"
dsCE = pd.read_csv(ruta_csv)

# Filtrar para mostrar solo desde el mes 24 (inclusive)
dfSE = dfSE[dfSE['Mes'] >= 24].reset_index(drop=True)
dsCE = dsCE[dsCE['Mes'] >= 24].reset_index(drop=True)

# Calcular desviación estándar del error para los meses 25-29
meses_eval = [25, 26, 27, 28, 29]
mask = dfSE['Mes'].isin(meses_eval)

std_classic = (dfSE['Classic Cars Estimado'] - dsCE['Classic Cars Estimado'])[mask].std()
std_vintage = (dfSE['Vintage Cars Estimado'] - dsCE['Vintage Cars Estimado'])[mask].std()

print(f"Desviación estándar del error Classic Cars (meses 25-29): {std_classic:.4f}")
print(f"Desviación estándar del error Vintage Cars (meses 25-29): {std_vintage:.4f}")

# Crear una figura con dos subplots: izquierda = Classic, derecha = Vintage
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

# Classic Cars (izquierda)
axes[0].plot(dfSE['Mes'], dfSE['Classic Cars Estimado'],
             label='Classic - sin cError', color='C0', marker='o')
axes[0].plot(dsCE['Mes'], dsCE['Classic Cars Estimado'],
             label='Classic - cError', color='C0', linestyle='--', marker='x')
axes[0].set_title('Classic Cars (desde mes 24)')
axes[0].set_xlabel('Mes')
axes[0].set_ylabel('Ventas estimadas')
axes[0].legend()
axes[0].grid(alpha=0.3)
# Anotar desviación estándar en la gráfica Classic
axes[0].text(0.05, 0.95, f"Std error (25-29): {std_classic:.2f}",
             transform=axes[0].transAxes, va='top', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# Vintage Cars (derecha)
axes[1].plot(dfSE['Mes'], dfSE['Vintage Cars Estimado'],
             label='Vintage - sin cError', color='C1', marker='o')
axes[1].plot(dsCE['Mes'], dsCE['Vintage Cars Estimado'],
             label='Vintage - cError', color='C1', linestyle='--', marker='x')
axes[1].set_title('Vintage Cars (desde mes 24)')
axes[1].set_xlabel('Mes')
axes[1].legend()
axes[1].grid(alpha=0.3)
# Anotar desviación estándar en la gráfica Vintage
axes[1].text(0.05, 0.95, f"Std error (25-29): {std_vintage:.2f}",
             transform=axes[1].transAxes, va='top', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

plt.suptitle('Comparación de estimaciones por tipo de auto (meses >= 24)')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.show()

