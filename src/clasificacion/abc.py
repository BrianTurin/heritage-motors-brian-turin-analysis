"""Etapa 2a - Clasificacion ABC por valor de uso anual.

Valor de uso anual = demanda anual del componente x costo unitario.

La demanda anual de cada componente sale de las unidades historicas de cada
vehiculo, anualizadas (la serie cubre 29 meses, no un anio exacto) y
multiplicadas por el ratio de uso del enunciado.

Esa anualizacion da un numero fraccionario, pero los insumos son piezas
indivisibles: no se consumen 245,79 carrocerias. Se redondea la demanda a
unidades enteras y el valor de uso se calcula sobre la demanda redondeada, para
que la tabla del informe cierre al rehacer la multiplicacion a mano. El
redondeo mueve el valor de uso menos de una decima de punto porcentual y no
cambia ni el orden ni la clase de ningun componente.

Ojo: esta demanda historica es solo para rankear. Los modelos de inventario
(Etapa 4) corren sobre la demanda PRONOSTICADA de la Etapa 3, que es otra cifra.
De este archivo, las etapas siguientes solo leen la columna Clase_ABC.

Corte clasico de Pareto: A hasta el 80% acumulado, B hasta el 95%, C el resto.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import parametros, rutas


def clasificar(porcentaje_acumulado):
    if porcentaje_acumulado <= 80:
        return "A"
    if porcentaje_acumulado <= 95:
        return "B"
    return "C"


def calcular(serie):
    meses = len(serie)
    factor_anual = parametros.MESES_POR_ANIO / meses

    clasicos = serie["Unidades_Clasicos"].sum() * factor_anual
    vintage = serie["Unidades_Vintage"].sum() * factor_anual

    filas = []
    for _, comp in parametros.COMPONENTES.iterrows():
        # Piezas indivisibles: se redondea antes de valorizar (ver docstring).
        demanda = round(parametros.demanda_componente(clasicos, vintage, comp))
        filas.append(
            {
                "Componente": comp["Componente"],
                "Auto_Foco": comp["Auto_Foco"],
                "Demanda_Anual": demanda,
                "Costo_Unitario": comp["Costo_Unitario"],
                "Valor_Uso_Anual": demanda * comp["Costo_Unitario"],
            }
        )

    tabla = pd.DataFrame(filas).sort_values("Valor_Uso_Anual", ascending=False)
    total = tabla["Valor_Uso_Anual"].sum()
    tabla["Pct_Individual"] = 100 * tabla["Valor_Uso_Anual"] / total
    tabla["Pct_Acumulado"] = tabla["Pct_Individual"].cumsum()
    tabla["Clase_ABC"] = tabla["Pct_Acumulado"].apply(clasificar)
    return tabla.reset_index(drop=True)


def graficar(tabla, ruta):
    fig, ax = plt.subplots(figsize=(11, 6))
    colores = {"A": "#c0392b", "B": "#e67e22", "C": "#7f8c8d"}
    etiquetas = parametros.abreviar(tabla["Componente"])

    ax.bar(etiquetas, tabla["Valor_Uso_Anual"] / 1e6,
           color=[colores[c] for c in tabla["Clase_ABC"]])
    ax.set_ylabel("Valor de uso anual (millones USD)")
    ax.set_xticks(range(len(etiquetas)))
    ax.set_xticklabels(etiquetas, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)

    eje = ax.twinx()
    eje.plot(etiquetas, tabla["Pct_Acumulado"], color="black", marker="o", linewidth=1.5)
    eje.axhline(80, color="black", linestyle="--", linewidth=1)
    eje.set_ylabel("% acumulado")
    eje.set_ylim(0, 105)

    ax.set_title("Analisis ABC de componentes (valor de uso anual)")
    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)


def main():
    rutas.titulo("ETAPA 2a - CLASIFICACION ABC")
    rutas.exigir(rutas.SERIE_MENSUAL, "datos")

    serie = pd.read_csv(rutas.SERIE_MENSUAL, parse_dates=["Periodo"])
    tabla = calcular(serie)

    rutas.preparar(rutas.CLASIFICACION)

    columnas = ["Componente", "Auto_Foco", "Demanda_Anual", "Costo_Unitario",
                "Valor_Uso_Anual", "Pct_Individual", "Pct_Acumulado", "Clase_ABC"]
    print(tabla[columnas].to_string(index=False,
                                    formatters={"Demanda_Anual": "{:,.0f}".format,
                                                "Valor_Uso_Anual": "{:,.0f}".format,
                                                "Pct_Individual": "{:.2f}".format,
                                                "Pct_Acumulado": "{:.2f}".format}))

    clase_a = tabla[tabla["Clase_ABC"] == "A"]
    print(f"\nClase A: {len(clase_a)} componentes, "
          f"{clase_a['Pct_Individual'].sum():.2f}% del valor de uso anual")
    print("Sobre estos se aplican los modelos de inventario:")
    for nombre in clase_a["Componente"]:
        print(f"  - {nombre}")

    rutas.guardar_tabla(tabla[columnas], rutas.CLASIFICACION / "abc.csv")
    graficar(tabla, rutas.CLASIFICACION / "abc_pareto.png")


if __name__ == "__main__":
    main()
