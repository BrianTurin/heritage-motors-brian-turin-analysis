"""Etapa 6a - Sensibilidad al costo por unidad de deficit (c_B +-30%).

c_B es el parametro mas discutible del modelo: se derivo del 5% de compensacion
al cliente sobre un precio que el enunciado no da, usando el costo de materiales
como cota inferior. Corresponde entonces ver cuanto cambia la respuesta si ese
numero estuviera mal.

Lo importante es que c_B NO se toca solo en la formula del costo: se vuelve a
resolver la ecuacion (13) de Winston con el nuevo valor. Como

    P(X >= r*) = h*q* / (c_B*E(D))

un c_B mas alto baja la probabilidad de agotamiento tolerada y sube el punto de
reabastecimiento. Ese reajuste es justamente lo que hay que mostrar. Recalcular
unicamente el costo, dejando la politica fija, mediria otra cosa: cuanto se
encarece una politica que ya dejo de ser la optima.

Notar que q* = EOQ no depende de c_B, asi que el lote no se mueve: todo el
ajuste pasa por r.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import parametros, rutas
from src.inventario import modelos

VARIACION = 0.30

ESCENARIOS = {
    "c_B -30%": 1 - VARIACION,
    "c_B base": 1.0,
    "c_B +30%": 1 + VARIACION,
}


def evaluar(parametros_riesgo):
    """Resuelve la Politica A en cada escenario de c_B."""
    filas = []
    for nombre, factor in ESCENARIOS.items():
        for _, fila in parametros_riesgo.iterrows():
            c_B = fila["c_B_Deficit"] * factor
            resultado = modelos.politica_pedidos_pendientes(
                E_D=fila["Demanda_Anual"],
                K=parametros.COSTO_ORDENAR,
                h=fila["h_Anual"],
                c_B=c_B,
                E_X=fila["E_X"],
                sigma_X=fila["sigma_X"],
            )
            filas.append({
                "Escenario": nombre,
                "Factor": factor,
                "Componente": fila["Componente"],
                "Demanda_Anual": fila["Demanda_Anual"],
                "c_B": c_B,
                "q": resultado["q"],
                "Stock_Seguridad": resultado["Stock_Seguridad"],
                "r": resultado["r"],
                "P_Agotamiento": resultado["P_Agotamiento"],
                "SLM1": resultado["SLM1"],
                "Deficit_Anual": resultado["Deficit_Anual"],
                "TC": resultado["TC"],
            })
    return pd.DataFrame(filas)


def resumir(detalle):
    """Totales por escenario y variacion respecto del caso base.

    P(X >= r) y SLM1 se ponderan por demanda anual, no por promedio simple. Es
    la misma ponderacion que usa la etapa 4b para reportar el nivel de servicio
    de la Politica A, y tiene que serlo: con promedio simple el escenario base
    daba 0,0266 y 99,35% mientras la otra seccion informaba 0,0244 y 99,43%
    para exactamente la misma politica. Un promedio simple ademas le da el mismo
    peso a un componente que se pide 35 veces al anio que a uno que se pide una,
    que no es lo que significa "nivel de servicio de la politica".
    """
    def ponderar(grupo, columna):
        return modelos.promedio_ponderado(grupo[columna], grupo["Demanda_Anual"])

    filas = []
    for escenario, grupo in detalle.groupby("Escenario", sort=False):
        filas.append({
            "Escenario": escenario,
            "q_Promedio": grupo["q"].mean(),
            "Stock_Seguridad_Total": grupo["Stock_Seguridad"].sum(),
            "Deficit_Anual_Total": grupo["Deficit_Anual"].sum(),
            "TC_Total": grupo["TC"].sum(),
            "P_Agotamiento_Ponderada": ponderar(grupo, "P_Agotamiento"),
            "SLM1_Ponderado": ponderar(grupo, "SLM1"),
        })
    resumen = pd.DataFrame(filas)

    base = resumen.loc[resumen["Escenario"] == "c_B base", "TC_Total"].iloc[0]
    resumen["Variacion_TC_Pct"] = 100 * (resumen["TC_Total"] - base) / base
    return resumen


def graficar(detalle, resumen, ruta):
    fig, ejes = plt.subplots(1, 3, figsize=(16, 5))
    colores = {"c_B -30%": "#55a868", "c_B base": "#4c72b0", "c_B +30%": "#c44e52"}

    # TC(q, r) total por escenario
    izq = ejes[0]
    barras = izq.bar(resumen["Escenario"], resumen["TC_Total"] / 1e3,
                     color=[colores[e] for e in resumen["Escenario"]])
    izq.set_ylabel("TC(q, r) total anual (miles USD)")
    izq.set_title("Costo total esperado")
    izq.grid(axis="y", alpha=0.3)
    # Las etiquetas de cada barra son de dos lineas; sin aire arriba la del
    # escenario mas caro se sale del recuadro.
    izq.set_ylim(0, resumen["TC_Total"].max() / 1e3 * 1.2)
    for barra, valor, pct in zip(barras, resumen["TC_Total"],
                                 resumen["Variacion_TC_Pct"]):
        izq.text(barra.get_x() + barra.get_width() / 2, valor / 1e3,
                 f"{valor / 1e3:.0f}k\n({pct:+.1f}%)", ha="center", va="bottom",
                 fontsize=9)

    # Stock de seguridad por componente y escenario
    medio = ejes[1]
    pivote = detalle.pivot(index="Componente", columns="Escenario",
                           values="Stock_Seguridad")
    pivote = pivote[list(ESCENARIOS)]
    pivote.index = parametros.abreviar(pivote.index)
    pivote.plot(kind="bar", ax=medio, color=[colores[e] for e in ESCENARIOS])
    medio.set_ylabel("Stock de seguridad (unidades)")
    medio.set_xlabel("")
    medio.set_title("Reaccion del stock de seguridad")
    medio.set_xticklabels(medio.get_xticklabels(), rotation=45, ha="right")
    medio.grid(axis="y", alpha=0.3)
    # El panel 1 ya identifica los tres escenarios por color en su eje X, y el
    # panel 3 vuelve a usar los mismos: alcanza con una referencia para toda la
    # figura, que va abajo del todo.
    manejadores, nombres = medio.get_legend_handles_labels()
    medio.get_legend().remove()

    # Nivel de servicio resultante
    der = ejes[2]
    pivote_ns = detalle.pivot(index="Componente", columns="Escenario",
                              values="P_Agotamiento") * 100
    pivote_ns = pivote_ns[list(ESCENARIOS)]
    pivote_ns.index = parametros.abreviar(pivote_ns.index)
    pivote_ns.plot(kind="bar", ax=der, color=[colores[e] for e in ESCENARIOS])
    der.axhline(5, color="black", linestyle="--", linewidth=1,
                label=f"alfa = {parametros.ALPHA:.0%}")
    der.set_ylabel("P(X >= r)  (%)")
    der.set_xlabel("")
    der.set_title("Probabilidad de agotamiento resultante")
    der.set_xticklabels(der.get_xticklabels(), rotation=45, ha="right")
    der.grid(axis="y", alpha=0.3)
    # Se conserva solo la referencia de alfa, que es la unica que este panel
    # agrega; los escenarios ya estan en la leyenda de la figura. Se busca por
    # etiqueta y no por posicion, porque matplotlib devuelve primero las lineas
    # y despues las barras.
    manejadores_der, nombres_der = der.get_legend_handles_labels()
    solo_alfa = [m for m, n in zip(manejadores_der, nombres_der)
                 if n.startswith("alfa")]
    der.legend(handles=solo_alfa, loc="upper left")

    fig.legend(manejadores, nombres, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, -0.03))
    fig.suptitle("Sensibilidad al costo de agotamiento: c_B mas y menos 30%",
                 fontsize=13)
    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)


def main():
    rutas.titulo("ETAPA 6a - SENSIBILIDAD AL COSTO DE DEFICIT c_B (+-30%)")

    ruta = rutas.exigir(rutas.INVENTARIO / "parametros_riesgo.csv", "riesgo")
    # Se analiza la clase A, igual que la comparacion de politicas, para que el
    # TC base coincida con el que se reporta alli.
    parametros_riesgo = pd.read_csv(ruta).query("Clase_ABC == 'A'").reset_index(drop=True)

    detalle = evaluar(parametros_riesgo)
    resumen = resumir(detalle)

    print("Efecto por componente:\n")
    print(detalle.to_string(index=False,
                            formatters={"Factor": "{:.2f}".format,
                                        "c_B": "{:,.0f}".format,
                                        "q": "{:,.1f}".format,
                                        "Stock_Seguridad": "{:,.1f}".format,
                                        "r": "{:,.1f}".format,
                                        "P_Agotamiento": "{:.4f}".format,
                                        "SLM1": "{:.2%}".format,
                                        "Deficit_Anual": "{:,.2f}".format,
                                        "TC": "{:,.0f}".format}))

    print("\nTotales por escenario:\n")
    print(resumen.to_string(index=False,
                            formatters={"q_Promedio": "{:,.1f}".format,
                                        "Stock_Seguridad_Total": "{:,.1f}".format,
                                        "Deficit_Anual_Total": "{:,.2f}".format,
                                        "TC_Total": "{:,.0f}".format,
                                        "P_Agotamiento_Ponderada": "{:.4f}".format,
                                        "SLM1_Ponderado": "{:.2%}".format,
                                        "Variacion_TC_Pct": "{:+.2f}".format}))

    bajo = resumen[resumen["Escenario"] == "c_B -30%"].iloc[0]
    alto = resumen[resumen["Escenario"] == "c_B +30%"].iloc[0]

    print("\nLectura:")
    print(f"  Una variacion de +-30% en c_B mueve TC(q, r) entre "
          f"{bajo['Variacion_TC_Pct']:+.2f}% y {alto['Variacion_TC_Pct']:+.2f}%.")
    print(f"  El lote q no se mueve, porque el EOQ no depende de c_B. Todo el")
    print(f"  ajuste pasa por el punto de reabastecimiento: el stock de seguridad")
    print(f"  sube de {bajo['Stock_Seguridad_Total']:.1f} a "
          f"{alto['Stock_Seguridad_Total']:.1f} unidades y la probabilidad de")
    print(f"  agotamiento baja de {bajo['P_Agotamiento_Ponderada']:.4f} a "
          f"{alto['P_Agotamiento_Ponderada']:.4f}.")
    print("\n  TC(q, r) se mueve mucho menos que el parametro que lo origina: el")
    print("  modelo absorbe el error reajustando r. Aun con c_B un 30% por debajo,")
    print(f"  la probabilidad de agotamiento ({bajo['P_Agotamiento_Ponderada']:.4f}) sigue")
    print(f"  por debajo del alfa = {parametros.ALPHA} exigido a la Politica B, asi que")
    print("  la recomendacion no cambia por un error de esta magnitud en c_B.")

    rutas.preparar(rutas.SENSIBILIDAD)
    rutas.guardar_tabla(detalle, rutas.SENSIBILIDAD / "costo_agotamiento_detalle.csv")
    rutas.guardar_tabla(resumen, rutas.SENSIBILIDAD / "costo_agotamiento_resumen.csv")
    graficar(detalle, resumen, rutas.SENSIBILIDAD / "costo_agotamiento.png")


if __name__ == "__main__":
    main()
