"""Etapa 3d - Comparacion de modelos y seleccion del pronostico.

Junta las metricas de los tres modelos, elige el de menor MAPE y deja guardado
el pronostico ganador en un unico archivo, que es el que consumen todas las
etapas siguientes. De esta forma el resto del proyecto no depende de que modelo
gano: si manana Holt-Winters mejorara a Prophet, cambia este archivo y nada mas.

Ademas se calculan las dos cosas que el enunciado pide llevarse de esta etapa:

  - la demanda promedio anual total (suma de los 12 meses pronosticados), y
  - el desvio estandar del error de pronostico a nivel de periodo.

El segundo punto merece una aclaracion. El desvio que interesa para dimensionar
el stock de seguridad es el del ERROR del pronostico, no el de la serie
historica ni el de los valores pronosticados. Mide cuanto se equivoca el modelo
mes a mes, que es exactamente la incertidumbre contra la que hay que cubrirse.
Se calcula sobre los residuos del ajuste (real - ajustado).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import parametros, rutas
from src.pronostico import comun

MODELOS = ["holt_winters", "prophet", "sarima"]

NOMBRES = {
    "holt_winters": "Holt-Winters aditivo",
    "prophet": "Prophet",
    "sarima": "SARIMA",
}


def cargar_metricas():
    """Lee los CSV de metricas que dejo cada modelo."""
    filas = []
    for modelo in MODELOS:
        ruta = rutas.PRONOSTICO / f"{modelo}_metricas.csv"
        rutas.exigir(ruta, "pronostico")
        fila = pd.read_csv(ruta).iloc[0].to_dict()
        fila["Nombre"] = NOMBRES[modelo]
        filas.append(fila)
    columnas = ["Modelo", "Nombre", "MAE", "RMSE", "MAPE",
                "Desvio_Residuos", "Total_Pronosticado"]
    return pd.DataFrame(filas)[columnas].sort_values("MAPE").reset_index(drop=True)


def proporciones_historicas(serie):
    """Reparto Clasicos / Vintage segun las unidades realmente vendidas.

    El pronostico se hace sobre el total agregado, que es la serie con mejor
    senal. Para bajarlo a cada linea de vehiculo se usa la proporcion historica,
    tal como pide el enunciado ("las proporciones historicas de venta
    desagregada"). Se calcula sobre todo el historico y no sobre el ultimo mes
    para que no la mueva el ruido de un periodo puntual.
    """
    clasicos = serie["Unidades_Clasicos"].sum()
    vintage = serie["Unidades_Vintage"].sum()
    total = clasicos + vintage
    return clasicos / total, vintage / total


def demanda_por_componente(demanda_anual, desvio_mensual, p_clasico, p_vintage):
    """Traduce el pronostico agregado a demanda y riesgo de cada componente.

    Dos pasos:

    1. Del total a cada vehiculo, con la proporcion historica.
       El desvio del error se reparte con la misma proporcion: si el modelo se
       equivoca en N unidades de vehiculo, esas N se reparten entre las dos
       lineas igual que la demanda.

    2. De cada vehiculo a cada componente, con el ratio de uso del enunciado.
       Un componente que se monta 4 veces por auto (llantas, cubiertas)
       multiplica por 4 tanto la demanda como el desvio.

    El paso de mensual a semanal divide el desvio por la raiz de la cantidad de
    semanas del mes. Vale si los errores semanales son independientes entre si:
    la varianza de la suma es la suma de las varianzas, asi que el desvio
    mensual es raiz(4,33) veces el semanal.
    """
    filas = []
    for _, comp in parametros.COMPONENTES.iterrows():
        # Demanda anual del componente
        anual = parametros.demanda_componente(
            demanda_anual * p_clasico, demanda_anual * p_vintage, comp
        )
        # Desvio del error de pronostico, mismo camino de agregacion
        desvio_mes = parametros.demanda_componente(
            desvio_mensual * p_clasico, desvio_mensual * p_vintage, comp
        )
        desvio_semana = desvio_mes / parametros.SEMANAS_POR_MES ** 0.5

        filas.append(
            {
                "Componente": comp["Componente"],
                "Auto_Foco": comp["Auto_Foco"],
                "Demanda_Anual": anual,
                "Demanda_Semanal": anual / parametros.SEMANAS_POR_ANIO,
                "Sigma_Error_Mensual": desvio_mes,
                "Sigma_Error_Semanal": desvio_semana,
                "Lead_Time_Semanas": comp["Lead_Time_Semanas"],
                # Desvio de la demanda durante el plazo de entrega.
                # Winston, ecuacion (8): sigma_X = sigma_D * raiz(L)
                "sigma_X": desvio_semana * comp["Lead_Time_Semanas"] ** 0.5,
                "Costo_Unitario": comp["Costo_Unitario"],
                "Volumen_m3": comp["Volumen_m3"],
            }
        )
    return pd.DataFrame(filas)


def graficar(metricas, pronosticos, serie):
    fig, (izq, der) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel izquierdo: los tres pronosticos superpuestos sobre el historico
    izq.plot(serie.index, serie.values, color="black", marker="o",
             linewidth=1.5, label="Historico")
    colores = {"holt_winters": "tab:blue", "prophet": "tab:green", "sarima": "tab:red"}
    for modelo, datos in pronosticos.items():
        izq.plot(datos["Periodo"], datos["Unidades_Pronosticadas"],
                 marker="s", linestyle="--", color=colores[modelo],
                 label=NOMBRES[modelo])
    izq.axvline(serie.index[-1], color="gray", linestyle=":")
    izq.set_ylabel("Unidades / mes")
    izq.set_title("Pronostico de los tres modelos")
    izq.legend()
    izq.grid(alpha=0.3)

    # Panel derecho: MAPE de cada uno, con el umbral habitual del 10%
    orden = metricas.sort_values("MAPE")
    barras = der.bar(orden["Nombre"], orden["MAPE"],
                     color=[colores[m] for m in orden["Modelo"]])
    der.axhline(10, color="black", linestyle="--", linewidth=1,
                label="Referencia 10%")
    der.set_ylabel("MAPE (%)")
    der.set_title("Error porcentual medio del ajuste")
    der.legend()
    der.grid(axis="y", alpha=0.3)
    for barra, valor in zip(barras, orden["MAPE"]):
        der.text(barra.get_x() + barra.get_width() / 2, valor + 0.8,
                 f"{valor:.2f}%", ha="center")

    fig.tight_layout()
    rutas.guardar_figura(fig, rutas.PRONOSTICO / "comparacion_modelos.png")
    plt.close(fig)


def main():
    rutas.titulo("ETAPA 3d - COMPARACION DE MODELOS Y DEMANDA POR COMPONENTE")

    metricas = cargar_metricas()
    print("Comparacion de los tres modelos (ajuste dentro de la muestra):\n")
    print(metricas.to_string(index=False,
                             formatters={"MAE": "{:,.1f}".format,
                                         "RMSE": "{:,.1f}".format,
                                         "MAPE": "{:.2f}".format,
                                         "Desvio_Residuos": "{:,.1f}".format,
                                         "Total_Pronosticado": "{:,.0f}".format}))

    ganador = metricas.iloc[0]
    modelo = ganador["Modelo"]
    print(f"\nModelo seleccionado: {ganador['Nombre']} (MAPE {ganador['MAPE']:.2f}%)")

    # Pronostico y desvio del error del modelo ganador
    pronostico = pd.read_csv(rutas.PRONOSTICO / f"{modelo}_pronostico.csv",
                             parse_dates=["Periodo"])
    demanda_anual = float(pronostico["Unidades_Pronosticadas"].sum())
    desvio_mensual = float(ganador["Desvio_Residuos"])

    serie = pd.read_csv(rutas.SERIE_MENSUAL, parse_dates=["Periodo"])
    p_clasico, p_vintage = proporciones_historicas(serie)

    print("\nParametros que se llevan a los modelos de inventario:")
    print(f"  Demanda anual total pronosticada  {demanda_anual:,.0f} unidades".replace(",", "."))
    print(f"  Desvio del error de pronostico    {desvio_mensual:,.1f} unidades/mes".replace(",", "."))
    print(f"  equivalente semanal               "
          f"{desvio_mensual / parametros.SEMANAS_POR_MES ** 0.5:,.1f} unidades/semana".replace(",", "."))
    print(f"  Proporcion historica Clasicos     {p_clasico:.2%}")
    print(f"  Proporcion historica Vintage      {p_vintage:.2%}")

    componentes = demanda_por_componente(
        demanda_anual, desvio_mensual, p_clasico, p_vintage
    )

    print("\nDemanda y riesgo por componente:")
    print(componentes[["Componente", "Demanda_Anual", "Sigma_Error_Semanal",
                       "Lead_Time_Semanas", "sigma_X"]].to_string(
        index=False,
        formatters={"Demanda_Anual": "{:,.0f}".format,
                    "Sigma_Error_Semanal": "{:,.2f}".format,
                    "sigma_X": "{:,.2f}".format}))

    rutas.preparar(rutas.PRONOSTICO)
    rutas.guardar_tabla(metricas, rutas.PRONOSTICO / "comparacion_modelos.csv")
    rutas.guardar_tabla(componentes, rutas.PRONOSTICO / "demanda_componentes.csv")

    # El pronostico elegido queda copiado con nombre fijo, para que las etapas
    # siguientes no tengan que saber cual gano.
    pronostico.to_csv(rutas.PRONOSTICO / "pronostico_seleccionado.csv", index=False)
    pd.DataFrame([{
        "Modelo": modelo,
        "Nombre": ganador["Nombre"],
        "MAPE": ganador["MAPE"],
        "Demanda_Anual_Total": demanda_anual,
        "Sigma_Error_Mensual": desvio_mensual,
        "Sigma_Error_Semanal": desvio_mensual / parametros.SEMANAS_POR_MES ** 0.5,
        "Proporcion_Clasicos": p_clasico,
        "Proporcion_Vintage": p_vintage,
    }]).to_csv(rutas.PRONOSTICO / "resumen_pronostico.csv", index=False)
    print("  [csv] outputs/pronostico/pronostico_seleccionado.csv")
    print("  [csv] outputs/pronostico/resumen_pronostico.csv")

    pronosticos = {
        m: pd.read_csv(rutas.PRONOSTICO / f"{m}_pronostico.csv", parse_dates=["Periodo"])
        for m in MODELOS
    }
    graficar(metricas, pronosticos, comun.cargar_serie())


if __name__ == "__main__":
    main()
