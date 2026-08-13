"""Utilidades compartidas por los tres modelos de pronostico.

Los tres modelos (Holt-Winters, Prophet y SARIMA) se ajustan sobre la misma
serie (unidades totales por mes), se evaluan con las mismas metricas y devuelven
el mismo tipo de resultado, para que la comparacion sea justa.

Cada modulo de modelo expone una unica funcion `ajustar(serie, horizonte)` que
no lee ni escribe archivos y no imprime nada: solo calcula. Todo el manejo de
archivos y la salida por consola viven en `comparacion.py`. Esa separacion es la
que permite reutilizar los modelos dentro del bucle de validacion, donde hay que
ajustarlos decenas de veces en silencio.
"""

from collections import namedtuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import rutas

HORIZONTE = 12   # meses a pronosticar

# Minimo de meses para entrenar. Con estacionalidad anual hacen falta dos ciclos
# completos: con uno solo el modelo no puede separar el patron estacional de la
# tendencia.
MIN_ENTRENAMIENTO = 24

# Multiplicador de la banda de confianza (normal estandar, 95%).
Z_95 = 1.96


# Lo que devuelve cada modelo.
#   nombre       etiqueta para tablas y graficos
#   ajustado     valores ajustados sobre el historico, misma longitud que la serie
#   pronostico   los `horizonte` meses siguientes
#   detalle      nota corta con los parametros que estimo el modelo
Resultado = namedtuple("Resultado", "nombre ajustado pronostico detalle")


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


def meses_futuros(serie, horizonte=HORIZONTE):
    """Los `horizonte` meses que siguen al ultimo dato de la serie."""
    inicio = serie.index[-1] + pd.DateOffset(months=1)
    return pd.date_range(inicio, periods=horizonte, freq="MS")


def metricas(observado, estimado):
    """MAE, RMSE, MAPE y desvio de los residuos."""
    observado = np.asarray(observado, dtype=float)
    estimado = np.asarray(estimado, dtype=float)
    residuos = observado - estimado
    return {
        "MAE": float(np.mean(np.abs(residuos))),
        "RMSE": float(np.sqrt(np.mean(residuos ** 2))),
        "MAPE": float(np.mean(np.abs(residuos / observado)) * 100),
        "Desvio_Residuos": float(np.std(residuos, ddof=1)),
    }


def validar(ajustar, serie, minimo=MIN_ENTRENAMIENTO):
    """Validacion con origen movil, un paso adelante.

    Por que hace falta. El MAPE del ajuste mide cuanto se le parece el modelo a
    los datos con los que se entreno, y eso premia al que tiene mas parametros
    aunque prediga peor: un modelo con suficiente flexibilidad puede pasar por
    todos los puntos del historico y no acertar ni uno de los que vienen. Para
    saber cual pronostica mejor hay que pedirle que prediga datos que no vio.

    Como funciona. Se entrena con los primeros `minimo` meses y se predice el
    mes siguiente, que se compara contra el real. Despues se corre el origen un
    mes y se repite, hasta agotar la serie. Con 29 meses y un minimo de 24 salen
    cinco predicciones fuera de muestra por modelo.

    Son pocas, y conviene decirlo: la serie no da para mas. Tampoco se puede
    validar el horizonte de 12 meses que despues se pronostica, porque no hay 12
    meses de sobra para reservar. Es una limitacion del dato, no del metodo, y
    aun asi ordena a los modelos mucho mejor que el ajuste.

    Nota: el modelo se vuelve a estimar entero en cada origen, incluida la
    seleccion de orden de SARIMA. Si el orden se eligiera una sola vez con la
    serie completa, esa eleccion ya habria visto los datos de prueba.
    """
    errores, cuadrados = [], []
    for corte in range(minimo, len(serie)):
        entrenamiento = serie.iloc[:corte]
        real = serie.iloc[corte]
        prediccion = ajustar(entrenamiento, 1).pronostico.iloc[0]
        errores.append(abs(real - prediccion) / real * 100)
        cuadrados.append((real - prediccion) ** 2)

    return {
        "MAPE_Validacion": float(np.mean(errores)),
        "RMSE_Validacion": float(np.sqrt(np.mean(cuadrados))),
        "Origenes": len(errores),
    }


def banda(pronostico, desvio_residuos, z=Z_95):
    """Intervalo de confianza aproximado: pronostico +- z * sigma del error.

    Se usa la misma formula para los tres modelos por dos razones. La primera es
    que asi las bandas son comparables entre si; si cada modelo reportara la
    suya, las diferencias de ancho vendrian de como calcula el intervalo cada
    libreria y no del modelo. La segunda es que el intervalo de Prophet sale de
    mil simulaciones Monte Carlo sin semilla fija, con lo cual cambiaba en cada
    corrida y los numeros del informe dejaban de coincidir con los archivos.

    Limitacion conocida: la banda no se ensancha con el horizonte. Un pronostico
    a doce meses es mas incierto que uno a un mes, y esta aproximacion no lo
    refleja. A cambio es una cuenta que el lector puede rehacer a mano.
    """
    margen = z * desvio_residuos
    return (pronostico - margen).clip(lower=0), pronostico + margen


def graficar_modelo(ruta, titulo, serie, ajustado, pronostico, inferior, superior):
    """Ficha de un modelo: ajuste, pronostico con banda y residuos debajo.

    Los dos paneles comparten el eje X (`sharex`). Sin eso el panel de residuos
    solo cubre el historico mientras el de arriba llega hasta el final del
    pronostico, y al estar uno encima del otro se leen como si estuvieran
    alineados en el tiempo cuando no lo estan.
    """
    fig, (arriba, abajo) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    arriba.plot(serie.index, serie.values, marker="o", color="steelblue",
                label="Unidades reales")
    arriba.plot(serie.index, ajustado, color="darkorange", alpha=0.8,
                label="Ajuste del modelo")
    arriba.plot(pronostico.index, pronostico.values, marker="s", linestyle="--",
                color="firebrick", label=f"Pronostico {len(pronostico)} meses")
    arriba.fill_between(pronostico.index, inferior, superior,
                        color="firebrick", alpha=0.15, label="Intervalo 95%")
    arriba.axvline(serie.index[-1], color="gray", linestyle=":", linewidth=1.2)
    arriba.set_ylabel("Unidades / mes")
    arriba.set_title(titulo)
    arriba.legend(loc="upper left")
    arriba.grid(alpha=0.3)

    residuos = serie.values - np.asarray(ajustado, dtype=float)
    abajo.bar(serie.index, residuos, width=20, color="indianred", alpha=0.7)
    abajo.axhline(0, color="black", linewidth=1)
    abajo.axvline(serie.index[-1], color="gray", linestyle=":", linewidth=1.2)
    abajo.set_ylabel("Residuo")
    abajo.set_xlabel("Periodo")
    abajo.grid(alpha=0.3)

    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)
