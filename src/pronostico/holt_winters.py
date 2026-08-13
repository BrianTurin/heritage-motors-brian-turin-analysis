"""Modelo de pronostico: Holt-Winters aditivo (suavizado exponencial triple).

Se elige el modo aditivo porque la amplitud del pico de noviembre se mantiene
parecida entre 2003 (180 unidades) y 2004 (170): la estacionalidad suma una
cantidad casi constante en vez de multiplicar el nivel.

statsmodels estima alfa, beta y gamma por maxima verosimilitud. Con esta serie
los tres dan practicamente cero, y eso no es un error del ajuste: el optimizador
esta diciendo que no conviene actualizar nada con las observaciones nuevas
porque el patron anual se repite casi igual.

Cuidado con la lectura facil de ese resultado. Beta = 0 no significa que no haya
tendencia, sino que la tendencia no se *actualiza*: queda clavada en el valor de
la inicializacion. El modelo no es "un promedio estacional fijo" sino una
tendencia lineal fija mas una estacionalidad fija. La cuenta esta abajo, en el
comentario de los parametros iniciales.

Vale la pena remarcarlo porque explica por que este modelo termina ganando la
validacion. Al no tener nada que ajustar mes a mes es el mas rigido de los tres,
y con 29 observaciones la rigidez es una ventaja: no hay informacion suficiente
para estimar mas cosas sin empezar a seguir el ruido.
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
            initialization_method="estimated",
        ).fit()

    # Los tres parametros de suavizado son pesos entre 0 y 1: cuanto mas altos,
    # mas rapido se adapta cada componente a la ultima observacion.
    alfa = modelo.params["smoothing_level"]        # nivel
    beta = modelo.params["smoothing_trend"]        # tendencia
    gamma = modelo.params["smoothing_seasonal"]    # estacionalidad

    # De donde sale la pendiente de 0,95 vehiculos/mes que cita el informe.
    #
    # Con initialization_method="estimated" statsmodels no usa una heuristica
    # fija para arrancar: mete el nivel inicial, la pendiente inicial y los doce
    # indices estacionales en la misma optimizacion por maxima verosimilitud que
    # alfa, beta y gamma. Son parametros ajustados, no supuestos, y quedan en
    # `modelo.params` junto a los de suavizado:
    #
    #     modelo.params["initial_level"]     42,4494 vehiculos
    #     modelo.params["initial_trend"]      0,9475 vehiculos/mes   <- el 0,95
    #     modelo.params["initial_seasons"]   los doce indices
    #
    # Se puede verificar aparte: la pendiente de una regresion lineal sobre la
    # serie desestacionalizada (restandole esos doce indices) da 0,948. Sobre la
    # serie cruda da 1,285, porque el pico de noviembre 2004 la inclina.
    #
    # Como beta = 0 la pendiente nunca se actualiza y como alfa = 0 el nivel
    # tampoco, asi que el nivel del mes t queda en l0 + t * b y el pronostico
    # del mes h posterior al final de la muestra (T = 29) vale
    # l0 + (T + h) * b + estacional. Sumando los doce meses del horizonte:
    #
    #     tendencia acumulada = 0,9475 * sum(29 + h para h en 1..12) = 403,6
    #     total = 12 * 42,4494 + 403,6 - 6,78 (estacionalidad neta) = 906,26
    #
    # Ojo con esos 404: son la tendencia acumulada desde el inicio de la serie,
    # no la que se genera durante el horizonte. Eso ultimo seria 0,9475 * 78 =
    # 73,9, y quien intente reproducir el 404 con los doce meses solos no lo va
    # a encontrar.

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
