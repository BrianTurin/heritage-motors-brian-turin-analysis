"""Modelo de pronostico: SARIMA.

Se incluye SARIMA para contrastar, sabiendo de entrada que juega en desventaja:
la serie tiene 29 observaciones mensuales, o sea poco mas de dos ciclos anuales
completos, y la parte estacional con s=12 necesita bastante mas historia para
estimarse con precision.

El procedimiento es el habitual:
  1. Test de Dickey-Fuller aumentado para ver si hace falta diferenciar.
  2. Seleccion del orden por AIC entre un punado de candidatos razonables.
  3. Ajuste del modelo elegido y pronostico.

Sobre el punto 1: el ADF rechaza la raiz unitaria, pero igual se deja d=1 entre
los candidatos. Con 29 datos el test tiene poca potencia, y el pico de noviembre
-tres veces el nivel del resto del anio- pesa mucho en el estadistico. Que la
seleccion por AIC termine eligiendo d=1 muestra que el test se estaba quedando
corto. Es preferible dejar que el criterio de informacion decida y explicarlo,
antes que fijar el orden a mano.
"""

import warnings

import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.pronostico import comun

NOMBRE = "SARIMA"

# Candidatos a evaluar. Se mantienen pocos y simples a proposito: con 29 datos,
# agregar parametros solo sirve para sobreajustar.
#   (p, d, q)      parte no estacional
#   (P, D, Q, s)   parte estacional, s=12 por el ciclo anual
#
# D se deja siempre en 0: una diferenciacion estacional consumiria 12 de las 29
# observaciones, mas de un tercio de la muestra.
CANDIDATOS = [
    ((1, 0, 1), (1, 0, 1, 12)),
    ((1, 1, 1), (1, 0, 1, 12)),
    ((1, 1, 1), (1, 0, 0, 12)),
    ((1, 0, 0), (1, 0, 1, 12)),
]


def estacionariedad(serie):
    """Test de Dickey-Fuller aumentado. H0: la serie tiene raiz unitaria."""
    estadistico, p_valor, _, _, criticos, _ = adfuller(serie.dropna())
    return {
        "estadistico": float(estadistico),
        "p_valor": float(p_valor),
        "critico_5": float(criticos["5%"]),
        "estacionaria": bool(p_valor < 0.05),
    }


def _estimar(serie, orden, orden_estacional):
    """Ajusta un SARIMA y devuelve el resultado de statsmodels.

    enforce_stationarity y enforce_invertibility en False evitan que el
    optimizador se trabe contra los bordes de la region admisible, que es algo
    frecuente cuando hay pocos datos.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(
            serie,
            order=orden,
            seasonal_order=orden_estacional,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False)


def ajustar(serie, horizonte=comun.HORIZONTE):
    """Elige el orden por AIC, ajusta y pronostica. No imprime ni escribe.

    La seleccion de orden esta adentro de esta funcion y no afuera para que la
    validacion la repita en cada origen. Si el orden se eligiera una sola vez
    con la serie entera, ya habria mirado los meses que despues se usan como
    prueba y la validacion quedaria contaminada.
    """
    mejor = None
    for orden, orden_estacional in CANDIDATOS:
        modelo = _estimar(serie, orden, orden_estacional)
        if mejor is None or modelo.aic < mejor[0]:
            mejor = (modelo.aic, orden, orden_estacional, modelo)

    aic, orden, orden_estacional, modelo = mejor

    ajustado = modelo.fittedvalues.copy()
    # El primer valor ajustado no es utilizable cuando hay diferenciacion:
    # statsmodels arranca en cero y distorsiona el MAPE.
    ajustado.iloc[0] = serie.iloc[0]

    pronostico = pd.Series(
        modelo.get_forecast(steps=horizonte).predicted_mean.values,
        index=comun.meses_futuros(serie, horizonte),
    ).clip(lower=0)   # una demanda negativa no tiene sentido fisico

    return comun.Resultado(
        nombre=f"SARIMA{orden}x{orden_estacional}",
        ajustado=ajustado.values,
        pronostico=pronostico,
        detalle=f"elegido por AIC = {aic:.1f}",
    )
