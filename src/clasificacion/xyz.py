"""Etapa 2b - Clasificacion XYZ por variabilidad de la demanda.

CV = desvio estandar / media de la demanda mensual del componente.
Corte habitual: X hasta 10%, Y hasta 25%, Z por encima.

Como todos los componentes se consumen en proporcion fija a las unidades de
Clasicos, de Vintage o de ambos, solo hay tres perfiles de variabilidad
posibles. La tabla lo deja a la vista.

Al final se cruza con el ABC para armar la matriz que pide el enunciado. Ese
cruce es la unica salida de toda la etapa 2: outputs/clasificacion/abc_xyz.csv
lleva las columnas de las dos clasificaciones, asi que no hace falta guardar
ademas una tabla de ABC y otra de XYZ por separado.
"""

import pandas as pd

from src import parametros, rutas
from src.clasificacion import abc

# Columnas del unico archivo que deja la etapa: primero que componente es,
# despues el ABC (valor de uso) y por ultimo el XYZ (variabilidad).
COLUMNAS_SALIDA = [
    "Componente", "Auto_Foco",
    "Demanda_Anual", "Costo_Unitario", "Valor_Uso_Anual",
    "Pct_Individual", "Pct_Acumulado", "Clase_ABC",
    "Demanda_Mensual_Media", "Desvio_Mensual", "CV_Pct", "Clase_XYZ",
    "Clase",
]


def clasificar(cv_porcentual):
    if cv_porcentual <= 10:
        return "X"
    if cv_porcentual <= 25:
        return "Y"
    return "Z"


def calcular(serie):
    filas = []
    for _, comp in parametros.COMPONENTES.iterrows():
        demanda_mensual = parametros.demanda_componente(
            serie["Unidades_Clasicos"], serie["Unidades_Vintage"], comp
        )
        media = demanda_mensual.mean()
        desvio = demanda_mensual.std(ddof=1)
        cv = 100 * desvio / media if media else float("nan")
        filas.append(
            {
                "Componente": comp["Componente"],
                "Auto_Foco": comp["Auto_Foco"],
                "Demanda_Mensual_Media": media,
                "Desvio_Mensual": desvio,
                "CV_Pct": cv,
                "Clase_XYZ": clasificar(cv),
            }
        )
    return pd.DataFrame(filas).sort_values("CV_Pct").reset_index(drop=True)


def main():
    rutas.titulo("ETAPA 2b - CLASIFICACION XYZ")
    rutas.exigir(rutas.SERIE_MENSUAL, "datos")

    serie = pd.read_csv(rutas.SERIE_MENSUAL, parse_dates=["Periodo"])
    tabla = calcular(serie)

    print(tabla.to_string(index=False,
                          formatters={"Demanda_Mensual_Media": "{:,.0f}".format,
                                      "Desvio_Mensual": "{:,.0f}".format,
                                      "CV_Pct": "{:.2f}".format}))

    reparto = tabla["Clase_XYZ"].value_counts()
    print("\nReparto por clase:")
    for clase in ("X", "Y", "Z"):
        print(f"  {clase}: {reparto.get(clase, 0)} componentes")

    # Cruce ABC x XYZ.
    #
    # El ABC se recalcula en memoria en vez de leerse de un CSV intermedio. Es
    # la misma cuenta a partir de la misma serie, y asi la etapa deja un unico
    # archivo con las dos clasificaciones en lugar de tres que se contienen unos
    # a otros.
    tabla_abc = abc.calcular(serie)
    cruce = tabla_abc.merge(
        tabla[["Componente", "Demanda_Mensual_Media", "Desvio_Mensual",
               "CV_Pct", "Clase_XYZ"]],
        on="Componente",
    )
    cruce["Clase"] = cruce["Clase_ABC"] + cruce["Clase_XYZ"]
    cruce = cruce.sort_values(["Clase_ABC", "CV_Pct"]).reset_index(drop=True)

    print("\nMatriz ABC / XYZ:")
    print(cruce[["Componente", "Clase_ABC", "CV_Pct", "Clase_XYZ", "Clase"]]
          .to_string(index=False, formatters={"CV_Pct": "{:.2f}".format}))

    if (tabla["Clase_XYZ"] == "Z").all():
        print(
            "\nTodos los componentes caen en Z: la variabilidad mensual supera el 25%\n"
            "en los tres perfiles. La clasificacion XYZ no aporta un criterio de corte\n"
            "adicional al ABC, pero confirma que la demanda no puede tratarse como\n"
            "determinista y justifica usar modelos probabilisticos de inventario."
        )

    rutas.preparar(rutas.CLASIFICACION)
    rutas.guardar_tabla(cruce[COLUMNAS_SALIDA],
                        rutas.CLASIFICACION / "abc_xyz.csv")


if __name__ == "__main__":
    main()
