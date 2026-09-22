"""Modelo de pronostico: Prophet.

Prophet (Taylor y Letham, "Forecasting at Scale") descompone la serie en
tendencia, estacionalidad y ruido:  y(t) = g(t) + s(t) + h(t) + e(t).

Se usa estacionalidad anual aditiva y se desactivan la semanal y la diaria, que
no tienen sentido en datos mensuales. No se cargan feriados porque el dataset no
identifica el pais de cada pedido a nivel util.

Una advertencia sobre este modelo con esta serie. Prophet viene preparado para
series largas y por defecto es muy flexible: sobre nuestras 29 observaciones
reparte 22 puntos de cambio de tendencia y describe la estacionalidad anual con
10 armonicos de Fourier, o sea 20 coeficientes. Eso da mas parametros que datos,
y el resultado es un ajuste casi perfecto que no se traduce en buenas
predicciones. Por eso el ajuste dentro de la muestra no alcanza para elegir
modelo y `comparacion.py` decide con la validacion fuera de muestra.

El conteo se puede leer directo de los vectores que deja el ajuste en
`modelo.params`, y de ahi salen los numeros del informe:

    delta      (1, 22)   un coeficiente por punto de cambio de tendencia
    beta       (1, 20)   10 armonicos anuales, seno y coseno de cada uno
    k, m       (1, 1)    pendiente y ordenada al origen de la tendencia base
    sigma_obs  (1, 1)    desvio del ruido
                         --------
                            45 parametros para 29 observaciones

Un matiz por si lo repreguntan: no son parametros libres al estilo de una
regresion. Prophet estima por MAP y encoge `delta` con un prior Laplace de
escala `changepoint_prior_scale`, con lo cual los grados de libertad efectivos
son menos de 45. La frase "mas de 40 parametros" es correcta como conteo
nominal, pero el argumento que no depende de como se cuenten los parametros es
el experimento de `regulado()`: bajando esa flexibilidad, el MAPE de validacion
cae de 47,39% a 31,89%.

Se deja la configuracion por defecto a proposito, para que la comparacion
muestre el problema en vez de taparlo.
"""

import logging
import warnings

import pandas as pd

from src.pronostico import comun

NOMBRE = "Prophet"


def _cargar_prophet():
    """Importa Prophet en silencio.

    Los dos loggers se apagan con `disabled` y no con `setLevel`. La razon es
    que cmdstanpy fija el nivel de su propio logger en INFO la primera vez que
    lo usa, con lo cual pisa cualquier nivel puesto de antemano y las lineas
    "Chain [1] start processing" se cuelan igual en medio de la salida. El flag
    `disabled` no lo toca nadie.

    De Prophet ademas hay que silenciar el aviso de que falta plotly, que se
    emite como error aunque sea inofensivo: el proyecto no usa sus graficos
    interactivos. Ese aviso sale de "prophet.plot" y hay que nombrarlo aparte,
    porque `disabled` no se hereda del logger padre.
    """
    for nombre in ("prophet", "prophet.plot", "cmdstanpy"):
        logging.getLogger(nombre).disabled = True
    warnings.simplefilter("ignore")
    from prophet import Prophet
    return Prophet


def ajustar(serie, horizonte=comun.HORIZONTE, changepoint_prior_scale=0.05,
            n_changepoints=25, nombre=NOMBRE):
    """Ajusta el modelo y pronostica `horizonte` meses. No imprime ni escribe.

    Los valores por defecto son los de Prophet. `regulado()` los baja.
    """
    Prophet = _cargar_prophet()

    # `yearly_seasonality=True` deja el orden de Fourier por defecto de Prophet,
    # que es 10: de ahi los 20 coeficientes (seno y coseno por armonico) del
    # vector `beta`. Se puede confirmar con
    # `modelo.seasonalities["yearly"]["fourier_order"]`.
    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        changepoint_prior_scale=changepoint_prior_scale,
        n_changepoints=n_changepoints,
    )
    modelo.fit(pd.DataFrame({"ds": serie.index, "y": serie.values}))

    futuro = modelo.make_future_dataframe(periods=horizonte, freq="MS")
    salida = modelo.predict(futuro).set_index("ds")

    meses = comun.meses_futuros(serie, horizonte)
    pronostico = salida.loc[meses, "yhat"].clip(lower=0)

    tendencia = salida["trend"]

    # `len(modelo.changepoints)` son los puntos de cambio que Prophet coloco de
    # verdad, que no son los 25 que pide el argumento `n_changepoints`. Prophet
    # solo ubica quiebres en el primer 80% de la historia (`changepoint_range`)
    # y ademas recorta la cantidad si no entran: 29 * 0,8 da 23 fechas
    # candidatas y descarta la primera, porque ahi ya esta la pendiente base
    # `k`. Quedan 22, uno por mes entre febrero 2003 y noviembre 2004. Ese 22 es
    # el que sale impreso en la columna Detalle de modelos_metricas.csv, y el
    # que cita el informe.
    detalle = (f"{len(modelo.changepoints)} puntos de cambio, "
               f"tendencia de {tendencia.iloc[0]:.0f} a {tendencia.iloc[-1]:.0f}")

    return comun.Resultado(
        nombre=nombre,
        ajustado=salida.loc[serie.index, "yhat"].values,
        pronostico=pronostico,
        detalle=detalle,
    )


def regulado(serie, horizonte=comun.HORIZONTE):
    """Prophet con la flexibilidad bajada a lo que admiten 29 observaciones.

    Se incluye como diagnostico, no como candidato. El punto es acotar que
    conclusion permite sacar la comparacion: con los defaults Prophet valida en
    47,39% y parece muy inferior a Holt-Winters, pero bajando el prior de los
    puntos de cambio de 0,05 a 0,01 y su cantidad de 25 a 5 valida en 31,89%,
    practicamente empatado con el ganador (32,20%).

    O sea que lo que falla no es Prophet sino sus valores por defecto sobre una
    serie corta. La eleccion de Holt-Winters se sostiene igual, pero por otros
    motivos: es mas simple de auditar y con 29 observaciones tiene menos que
    ajustar. Prophet regulado sigue ajustando con 14,7% de MAPE y un desvio de
    residuos de 6,5 contra los 16,7 de Holt-Winters, y esa diferencia es
    flexibilidad del modelo, no menor incertidumbre: fuera de muestra el RMSE
    es parecido (16,2 contra 19,0).
    """
    return ajustar(serie, horizonte, changepoint_prior_scale=0.01,
                   n_changepoints=5, nombre="Prophet regulado")
