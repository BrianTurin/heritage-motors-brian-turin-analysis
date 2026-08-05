"""Etapa 3a - Pronostico con Holt-Winters (suavizado exponencial triple).

Se elige el modo aditivo porque la amplitud del pico de noviembre se mantiene
parecida entre 2003 (6.009 unidades) y 2004 (5.974): la estacionalidad suma una
cantidad casi constante en vez de multiplicar el nivel.

statsmodels estima alfa, beta y gamma por maxima verosimilitud.
"""

import warnings

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src import rutas
from src.pronostico import comun

MODELO = "holt_winters"


def main():
    rutas.titulo("ETAPA 3a - PRONOSTICO HOLT-WINTERS")
    serie = comun.cargar_serie()
    print(f"Serie: {len(serie)} meses ({serie.index[0]:%Y-%m} a {serie.index[-1]:%Y-%m})")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ajuste = ExponentialSmoothing(
            serie,
            trend="add",
            seasonal="add",
            seasonal_periods=12,
            initialization_method="estimated",
        ).fit()

    # Los tres parametros de suavizado son pesos entre 0 y 1: cuanto mas altos,
    # mas rapido se adapta cada componente a la ultima observacion.
    alfa = ajuste.params["smoothing_level"]        # nivel
    beta = ajuste.params["smoothing_trend"]        # tendencia
    gamma = ajuste.params["smoothing_seasonal"]    # estacionalidad

    print("\nParametros estimados por maxima verosimilitud:")
    print(f"  alfa  (nivel)        {alfa:.4f}")
    print(f"  beta  (tendencia)    {beta:.4f}")
    print(f"  gamma (estacional)   {gamma:.4f}")

    # Con esta serie los tres dan practicamente cero. No es un error del
    # ajuste: el optimizador esta diciendo que no conviene actualizar nada con
    # las observaciones nuevas, porque el patron se repite casi igual todos los
    # anios (noviembre 2003 = 6.009 unidades, noviembre 2004 = 5.974). El modelo
    # queda entonces como un promedio estacional fijo, estimado en la
    # inicializacion. Es un ajuste degenerado pero coherente con los datos, y
    # conviene reportarlo antes que disimularlo.
    if max(alfa, beta, gamma) < 0.01:
        print("\n  Los tres parametros quedan en cero. El modelo se reduce a un")
        print("  promedio estacional fijo: no actualiza nivel ni tendencia con las")
        print("  observaciones nuevas porque el patron anual se repite casi igual.")
    elif alfa < 0.01:
        print("\n  alfa practicamente nulo: el nivel queda fijo en su valor inicial")
        print("  y el modelo explica la serie casi solo con el patron estacional.")

    futuro = comun.meses_futuros(serie)
    pronostico = pd.Series(ajuste.forecast(comun.HORIZONTE).values, index=futuro)
    pronostico = pronostico.clip(lower=0)

    resumen = comun.metricas(serie.values, ajuste.fittedvalues.values)
    resumen["Total_Pronosticado"] = float(pronostico.sum())
    comun.informar(resumen)
    print(f"\nTotal pronosticado 12 meses: {pronostico.sum():,.0f} unidades".replace(",", "."))

    comun.exportar(MODELO, serie, ajuste.fittedvalues.values, pronostico, resumen)
    comun.graficar(MODELO, "Holt-Winters aditivo - unidades mensuales",
                   serie, ajuste.fittedvalues.values, pronostico)


if __name__ == "__main__":
    main()
