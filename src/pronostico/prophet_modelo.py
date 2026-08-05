"""Etapa 3b - Pronostico con Prophet.

Prophet (Taylor y Letham, "Forecasting at Scale") descompone la serie en
tendencia, estacionalidad y ruido:  y(t) = g(t) + s(t) + h(t) + e(t).

Se usa estacionalidad anual aditiva y se desactivan la semanal y la diaria,
que no tienen sentido en datos mensuales. No se cargan feriados porque el
dataset no identifica el pais de cada pedido a nivel util.
"""

import logging
import warnings

import pandas as pd

from src import rutas
from src.pronostico import comun

MODELO = "prophet"


def main():
    rutas.titulo("ETAPA 3b - PRONOSTICO PROPHET")

    logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
    logging.getLogger("prophet").setLevel(logging.ERROR)
    warnings.simplefilter("ignore")
    from prophet import Prophet

    serie = comun.cargar_serie()
    print(f"Serie: {len(serie)} meses ({serie.index[0]:%Y-%m} a {serie.index[-1]:%Y-%m})")

    datos = pd.DataFrame({"ds": serie.index, "y": serie.values})

    modelo = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        interval_width=0.95,
        changepoint_prior_scale=0.05,
    )
    modelo.fit(datos)

    futuro = modelo.make_future_dataframe(periods=comun.HORIZONTE, freq="MS")
    salida = modelo.predict(futuro).set_index("ds")

    ajustado = salida.loc[serie.index, "yhat"]
    meses = comun.meses_futuros(serie)
    pronostico = salida.loc[meses, "yhat"].clip(lower=0)
    banda = (salida.loc[meses, "yhat_lower"].clip(lower=0),
             salida.loc[meses, "yhat_upper"])

    tendencia = salida["trend"]
    print("\nComponentes del modelo:")
    print(f"  puntos de cambio detectados : {len(modelo.changepoints)}")
    print(f"  tendencia: de {tendencia.iloc[0]:,.0f} a {tendencia.iloc[-1]:,.0f} unidades/mes"
          .replace(",", "."))
    amplitud = salida["yearly"].max() - salida["yearly"].min()
    print(f"  amplitud de la estacionalidad anual: {amplitud:,.0f} unidades".replace(",", "."))

    resumen = comun.metricas(serie.values, ajustado.values)
    resumen["Total_Pronosticado"] = float(pronostico.sum())
    comun.informar(resumen)
    print(f"\nTotal pronosticado 12 meses: {pronostico.sum():,.0f} unidades".replace(",", "."))
    print(f"  intervalo 95%: {banda[0].sum():,.0f} a {banda[1].sum():,.0f} unidades"
          .replace(",", "."))

    comun.exportar(MODELO, serie, ajustado.values, pronostico, resumen)
    comun.graficar(MODELO, "Prophet - unidades mensuales",
                   serie, ajustado.values, pronostico, banda=banda)

    # El intervalo se guarda aparte: solo Prophet lo reporta de forma directa
    pd.DataFrame(
        {
            "Periodo": meses,
            "Unidades_Pronosticadas": pronostico.values,
            "Limite_Inferior": banda[0].values,
            "Limite_Superior": banda[1].values,
        }
    ).to_csv(rutas.PRONOSTICO / "prophet_intervalo.csv", index=False)
    print("  [csv] outputs/pronostico/prophet_intervalo.csv")


if __name__ == "__main__":
    main()
