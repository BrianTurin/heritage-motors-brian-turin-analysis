"""Etapa 3c - Pronostico con SARIMA.

Se incluye SARIMA para contrastar, sabiendo de entrada que juega en desventaja:
la serie tiene 29 observaciones mensuales, o sea poco mas de dos ciclos anuales
completos, y la parte estacional con s=12 necesita bastante mas historia para
estimarse con precision.

El procedimiento es el habitual:
  1. Test de Dickey-Fuller aumentado para ver si hace falta diferenciar.
  2. Seleccion del orden por AIC entre un puñado de candidatos razonables.
  3. Ajuste del modelo elegido y pronostico a 12 meses.

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

from src import rutas
from src.pronostico import comun

MODELO = "sarima"

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


def test_estacionariedad(serie):
    """Dickey-Fuller aumentado. H0: la serie tiene raiz unitaria."""
    estadistico, p_valor, _, _, criticos, _ = adfuller(serie.dropna())
    print("\nTest de Dickey-Fuller aumentado:")
    print(f"  estadistico  {estadistico:.4f}")
    print(f"  p-valor      {p_valor:.4f}")
    print(f"  critico 5%   {criticos['5%']:.4f}")
    if p_valor < 0.05:
        print("  se rechaza la raiz unitaria: la serie es estacionaria al 5%")
    else:
        print("  no se rechaza la raiz unitaria: conviene diferenciar (d=1)")
    return p_valor < 0.05


def ajustar(serie, orden, orden_estacional):
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


def seleccionar(serie):
    """Prueba los candidatos y se queda con el de menor AIC."""
    print("\nSeleccion de orden por AIC:")
    print(f"  {'orden':<12} {'estacional':<16} {'AIC':>8} {'MAPE':>8}")

    evaluados = []
    for orden, orden_estacional in CANDIDATOS:
        ajuste = ajustar(serie, orden, orden_estacional)
        ajustado = ajuste.fittedvalues.copy()
        # El primer valor ajustado no es utilizable cuando hay diferenciacion:
        # statsmodels arranca en cero y distorsiona el MAPE.
        ajustado.iloc[0] = serie.iloc[0]
        resumen = comun.metricas(serie.values, ajustado.values)
        evaluados.append((ajuste.aic, orden, orden_estacional, ajuste, ajustado, resumen))
        print(f"  {str(orden):<12} {str(orden_estacional):<16} "
              f"{ajuste.aic:>8.1f} {resumen['MAPE']:>7.2f}%")

    mejor = min(evaluados, key=lambda fila: fila[0])
    print(f"\n  elegido: SARIMA{mejor[1]}x{mejor[2]} (AIC {mejor[0]:.1f})")
    return mejor


def main():
    rutas.titulo("ETAPA 3c - PRONOSTICO SARIMA")
    serie = comun.cargar_serie()
    print(f"Serie: {len(serie)} meses ({serie.index[0]:%Y-%m} a {serie.index[-1]:%Y-%m})")
    print(f"Ciclos estacionales completos disponibles: {len(serie) / 12:.1f}")

    estacionaria = test_estacionariedad(serie)
    _, orden, orden_estacional, ajuste, ajustado, resumen = seleccionar(serie)

    if estacionaria and orden[1] == 1:
        print("\n  Nota: el ADF daba estacionaria pero el AIC prefiere d=1. Con 29")
        print("  observaciones y un pico estacional muy marcado, el test pierde")
        print("  potencia; se respeta el criterio de informacion.")

    futuro = comun.meses_futuros(serie)
    pronostico = pd.Series(
        ajuste.get_forecast(steps=comun.HORIZONTE).predicted_mean.values, index=futuro
    ).clip(lower=0)   # una demanda negativa no tiene sentido fisico

    resumen["Total_Pronosticado"] = float(pronostico.sum())
    resumen["AIC"] = float(ajuste.aic)
    resumen["Orden"] = f"SARIMA{orden}x{orden_estacional}"

    comun.informar(resumen)
    print(f"\nTotal pronosticado 12 meses: {pronostico.sum():,.0f} unidades".replace(",", "."))

    comun.exportar(MODELO, serie, ajustado.values, pronostico, resumen)
    comun.graficar(MODELO, f"SARIMA{orden}x{orden_estacional} - unidades mensuales",
                   serie, ajustado.values, pronostico)


if __name__ == "__main__":
    main()
