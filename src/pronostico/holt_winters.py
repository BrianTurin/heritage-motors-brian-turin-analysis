"""Modelo de pronostico: Holt-Winters aditivo (suavizado exponencial triple).

Se elige el modo aditivo porque la amplitud del pico de noviembre se mantiene
parecida entre 2003 (180 unidades) y 2004 (170): la estacionalidad suma una
cantidad casi constante en vez de multiplicar el nivel.

Los valores iniciales (nivel, tendencia y los doce indices estacionales) se
fijan con la heuristica estandar de Hyndman: descomposicion por media movil
sobre los dos primeros ciclos y regresion lineal sobre la serie
desestacionalizada. Con esos valores fijos, statsmodels estima alfa, beta y
gamma por maxima verosimilitud.

Se usa esa heuristica y no `initialization_method="estimated"` porque con
"estimated" los valores iniciales entran en la misma optimizacion que los
pesos, y con 29 observaciones el optimizador termina explicando toda la serie
con la inicializacion y deja alfa, beta y gamma exactamente en cero. Ese
resultado es un artefacto de dejar demasiados parametros libres: un modelo que
no actualiza la estacionalidad con las observaciones nuevas no es lo que se
espera de Holt-Winters. Con la heuristica los tres pesos quedan positivos y la
validacion fuera de muestra da practicamente lo mismo.
"""

import warnings

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.pronostico import comun

NOMBRE = "Holt-Winters aditivo"


def ajustar(serie, horizonte=comun.HORIZONTE):
    """Ajusta el modelo y pronostica `horizonte` meses. No imprime ni escribe."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo = ExponentialSmoothing(
            serie,
            trend="add",
            seasonal="add",
            seasonal_periods=12,
            initialization_method="heuristic",
        ).fit()

    # Los tres parametros de suavizado son pesos entre 0 y 1: cuanto mas altos,
    # mas rapido se adapta cada componente a la ultima observacion.
    alfa = modelo.params["smoothing_level"]        # nivel
    beta = modelo.params["smoothing_trend"]        # tendencia
    gamma = modelo.params["smoothing_seasonal"]    # estacionalidad

    pronostico = pd.Series(
        modelo.forecast(horizonte).values,
        index=comun.meses_futuros(serie, horizonte),
    ).clip(lower=0)   # una demanda negativa no tiene sentido fisico

    return comun.Resultado(
        nombre=NOMBRE,
        ajustado=modelo.fittedvalues.values,
        pronostico=pronostico,
        detalle=f"alfa={alfa:.4f} beta={beta:.4f} gamma={gamma:.4f}",
    )
