"""Utilidades compartidas por los tres modelos de pronostico.

Los tres modelos (Holt-Winters, Prophet y SARIMA) se ajustan sobre la misma
serie (unidades totales por mes), se evaluan con las mismas metricas y
exportan con el mismo formato, para que la comparacion sea justa.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import rutas

HORIZONTE = 12  # meses a pronosticar


def cargar_serie():
    """Serie mensual de unidades totales, indexada por fecha.

    Se le fija la frecuencia 'MS' (inicio de mes) porque statsmodels la necesita
    para saber donde caen los periodos futuros; sin eso avisa por consola y la
    infiere sola en cada llamada.
    """
    rutas.exigir(rutas.SERIE_MENSUAL, "datos")
    serie = pd.read_csv(rutas.SERIE_MENSUAL, parse_dates=["Periodo"])
    serie = serie.set_index("Periodo")["Unidades_Total"].astype(float)
    serie.index.freq = "MS"
    return serie


def meses_futuros(serie):
    inicio = serie.index[-1] + pd.DateOffset(months=1)
    return pd.date_range(inicio, periods=HORIZONTE, freq="MS")


def metricas(observado, ajustado):
    """MAE, RMSE y MAPE del ajuste dentro de la muestra."""
    observado = np.asarray(observado, dtype=float)
    ajustado = np.asarray(ajustado, dtype=float)
    residuos = observado - ajustado
    return {
        "MAE": float(np.mean(np.abs(residuos))),
        "RMSE": float(np.sqrt(np.mean(residuos ** 2))),
        "MAPE": float(np.mean(np.abs(residuos / observado)) * 100),
        "Desvio_Residuos": float(np.std(residuos, ddof=1)),
    }


def exportar(modelo, serie, ajustado, pronostico, resumen):
    """Guarda pronostico y metricas de un modelo con nombres homogeneos."""
    rutas.preparar(rutas.PRONOSTICO)

    pd.DataFrame(
        {"Periodo": pronostico.index, "Unidades_Pronosticadas": pronostico.values}
    ).to_csv(rutas.PRONOSTICO / f"{modelo}_pronostico.csv", index=False)

    pd.DataFrame(
        {
            "Periodo": serie.index,
            "Unidades_Reales": serie.values,
            "Unidades_Ajustadas": np.asarray(ajustado, dtype=float),
            "Residuo": serie.values - np.asarray(ajustado, dtype=float),
        }
    ).to_csv(rutas.PRONOSTICO / f"{modelo}_ajuste.csv", index=False)

    fila = {"Modelo": modelo}
    fila.update(resumen)
    pd.DataFrame([fila]).to_csv(
        rutas.PRONOSTICO / f"{modelo}_metricas.csv", index=False
    )

    print(f"  [csv] outputs/pronostico/{modelo}_pronostico.csv")
    print(f"  [csv] outputs/pronostico/{modelo}_ajuste.csv")
    print(f"  [csv] outputs/pronostico/{modelo}_metricas.csv")


def graficar(modelo, titulo, serie, ajustado, pronostico, banda=None):
    fig, (arriba, abajo) = plt.subplots(
        2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [2, 1]}
    )

    arriba.plot(serie.index, serie.values, marker="o", label="Unidades reales",
                color="steelblue")
    arriba.plot(serie.index, ajustado, label="Ajuste del modelo",
                color="darkorange", alpha=0.8)
    arriba.plot(pronostico.index, pronostico.values, marker="s", linestyle="--",
                label="Pronostico 12 meses", color="firebrick")
    if banda is not None:
        arriba.fill_between(pronostico.index, banda[0], banda[1],
                            color="firebrick", alpha=0.15, label="Intervalo 95%")
    arriba.axvline(serie.index[-1], color="gray", linestyle=":", linewidth=1.2)
    arriba.set_ylabel("Unidades / mes")
    arriba.set_title(titulo)
    arriba.legend(loc="upper left")
    arriba.grid(alpha=0.3)

    residuos = serie.values - np.asarray(ajustado, dtype=float)
    abajo.bar(serie.index, residuos, width=20, color="indianred", alpha=0.7)
    abajo.axhline(0, color="black", linewidth=1)
    abajo.set_ylabel("Residuo")
    abajo.set_xlabel("Periodo")
    abajo.grid(alpha=0.3)

    fig.tight_layout()
    rutas.guardar_figura(fig, rutas.PRONOSTICO / f"{modelo}_pronostico.png")
    plt.close(fig)


def informar(resumen):
    print("\nMetricas de ajuste:")
    print(f"  MAE                 {resumen['MAE']:,.1f} unidades".replace(",", "."))
    print(f"  RMSE                {resumen['RMSE']:,.1f} unidades".replace(",", "."))
    print(f"  MAPE                {resumen['MAPE']:.2f}%")
    print(f"  Desvio de residuos  {resumen['Desvio_Residuos']:,.1f} unidades/mes".replace(",", "."))
