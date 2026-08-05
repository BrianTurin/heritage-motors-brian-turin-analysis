"""Etapa 6b - Sensibilidad al riesgo (+15% de incertidumbre).

Que pasa si el mercado se vuelve mas volatil y el pronostico empieza a fallar
un 15% mas. Se aumenta sigma_X en un 15% y se vuelven a resolver las dos
politicas, para medir cual aguanta mejor.

El punto central es que el stock de seguridad es proporcional a sigma_X:

    stock de seguridad = r - E(X) = z * sigma_X

asi que un 15% mas de incertidumbre obliga a un 15% mas de stock de seguridad
solo para sostener la misma probabilidad de agotamiento. Esa es la parte del
costo que no se puede evitar.

Lo notable es que las dos politicas suben su stock de seguridad exactamente un
15%, y ninguna tiene margen para hacer otra cosa. El motivo es que ningun z
depende de sigma_X:

  - El de la Politica B esta clavado en 1,645 porque el alfa lo fija el
    enunciado.

  - El de la Politica A sale de P(X >= r*) = h*q*/(c_B*E(D)), donde sigma_X
    directamente no aparece.

Tampoco se mueve q, porque el EOQ tampoco depende de sigma_X. Toda la
incertidumbre extra se paga con stock inmovilizado, sin margen de maniobra: esa
es la demostracion concreta de que la volatilidad se traduce en capital parado.

Donde si se diferencian es en cuanto les cuesta. La Politica A parte de un stock
de seguridad mas alto, asi que el deficit adicional que genera la mayor
volatilidad es menor y su costo sube menos.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import parametros, rutas
from src.inventario import modelos

AUMENTO_SIGMA = 0.15


def evaluar(parametros_riesgo):
    """Resuelve ambas politicas con sigma base y con sigma aumentado."""
    filas = []
    for factor, nombre in ((1.0, "Base"), (1 + AUMENTO_SIGMA, f"+{AUMENTO_SIGMA:.0%}")):
        for _, fila in parametros_riesgo.iterrows():
            argumentos = dict(
                E_D=fila["Demanda_Anual"],
                K=parametros.COSTO_ORDENAR,
                h=fila["h_Anual"],
                c_B=fila["c_B_Deficit"],
                E_X=fila["E_X"],
                sigma_X=fila["sigma_X"] * factor,
            )
            resultados = {
                "A": modelos.politica_pedidos_pendientes(**argumentos),
                "B": modelos.politica_nivel_servicio(
                    **argumentos, nivel_servicio=parametros.NIVEL_SERVICIO
                ),
            }
            for politica, resultado in resultados.items():
                filas.append({
                    "Escenario": nombre,
                    "Politica": politica,
                    "Componente": fila["Componente"],
                    "sigma_X": fila["sigma_X"] * factor,
                    "q": resultado["q"],
                    "Stock_Seguridad": resultado["Stock_Seguridad"],
                    "P_Agotamiento": resultado["P_Agotamiento"],
                    "SLM1": resultado["SLM1"],
                    "Costo_Almacenamiento": resultado["Costo_Almacenamiento"],
                    "Costo_Deficit": resultado["Costo_Deficit"],
                    "TC": resultado["TC"],
                })
    return pd.DataFrame(filas)


def resumir(detalle):
    """Compara base contra escenario de mayor incertidumbre, por politica."""
    agregado = detalle.groupby(["Politica", "Escenario"], sort=False).agg(
        Stock_Seguridad=("Stock_Seguridad", "sum"),
        Costo_Almacenamiento=("Costo_Almacenamiento", "sum"),
        Costo_Deficit=("Costo_Deficit", "sum"),
        TC=("TC", "sum"),
    ).reset_index()

    filas = []
    for politica in ("A", "B"):
        sub = agregado[agregado["Politica"] == politica].set_index("Escenario")
        base = sub.loc["Base"]
        alto = sub.loc[f"+{AUMENTO_SIGMA:.0%}"]
        filas.append({
            "Politica": politica,
            "SS_Base": base["Stock_Seguridad"],
            "SS_Alto": alto["Stock_Seguridad"],
            "SS_Var_Pct": 100 * (alto["Stock_Seguridad"] / base["Stock_Seguridad"] - 1),
            "TC_Base": base["TC"],
            "TC_Alto": alto["TC"],
            "TC_Var_Pct": 100 * (alto["TC"] / base["TC"] - 1),
            "Delta_TC": alto["TC"] - base["TC"],
        })
    return pd.DataFrame(filas)


def graficar(detalle, resumen, ruta):
    fig, ejes = plt.subplots(1, 3, figsize=(16, 5))

    # Stock de seguridad total: base vs +15%
    izq = ejes[0]
    posiciones = range(len(resumen))
    ancho = 0.35
    izq.bar([p - ancho / 2 for p in posiciones], resumen["SS_Base"], ancho,
            label="Base", color="#4c72b0")
    izq.bar([p + ancho / 2 for p in posiciones], resumen["SS_Alto"], ancho,
            label=f"+{AUMENTO_SIGMA:.0%} sigma_X", color="#c44e52")
    izq.set_xticks(list(posiciones))
    izq.set_xticklabels([f"Politica {p}" for p in resumen["Politica"]])
    izq.set_ylabel("Stock de seguridad total (unidades)")
    izq.set_title("La incertidumbre obliga a mas stock de seguridad")
    izq.legend()
    izq.grid(axis="y", alpha=0.3)
    for posicion, fila in zip(posiciones, resumen.itertuples()):
        izq.text(posicion + ancho / 2, fila.SS_Alto, f"{fila.SS_Var_Pct:+.1f}%",
                 ha="center", va="bottom", fontsize=9)

    # TC(q, r) total: base vs +15%
    medio = ejes[1]
    medio.bar([p - ancho / 2 for p in posiciones], resumen["TC_Base"] / 1e3, ancho,
              label="Base", color="#4c72b0")
    medio.bar([p + ancho / 2 for p in posiciones], resumen["TC_Alto"] / 1e3, ancho,
              label=f"+{AUMENTO_SIGMA:.0%} sigma_X", color="#c44e52")
    medio.set_xticks(list(posiciones))
    medio.set_xticklabels([f"Politica {p}" for p in resumen["Politica"]])
    medio.set_ylabel("TC(q, r) total anual (miles USD)")
    medio.set_title("Impacto en el costo total")
    medio.legend()
    medio.grid(axis="y", alpha=0.3)
    for posicion, fila in zip(posiciones, resumen.itertuples()):
        medio.text(posicion + ancho / 2, fila.TC_Alto / 1e3,
                   f"{fila.TC_Var_Pct:+.1f}%", ha="center", va="bottom", fontsize=9)

    # Stock de seguridad por componente
    der = ejes[2]
    pivote = detalle[detalle["Escenario"] == f"+{AUMENTO_SIGMA:.0%}"].pivot(
        index="Componente", columns="Politica", values="Stock_Seguridad"
    )
    pivote.index = parametros.abreviar(pivote.index)
    pivote.plot(kind="barh", ax=der, color=["#4c72b0", "#dd8452"])
    der.set_xlabel("Stock de seguridad con +15% sigma_X (unidades)")
    der.set_ylabel("")
    der.set_title("Detalle por componente")
    der.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)


def main():
    rutas.titulo(f"ETAPA 6b - SENSIBILIDAD AL RIESGO (+{AUMENTO_SIGMA:.0%} DE INCERTIDUMBRE)")

    ruta = rutas.exigir(rutas.INVENTARIO / "parametros_riesgo.csv", "riesgo")
    # Se analiza la clase A, igual que la comparacion de politicas, para que el
    # TC base coincida con el que se reporta alli.
    parametros_riesgo = pd.read_csv(ruta).query("Clase_ABC == 'A'").reset_index(drop=True)

    detalle = evaluar(parametros_riesgo)
    resumen = resumir(detalle)

    print("Detalle por componente y politica:\n")
    print(detalle.to_string(index=False,
                            formatters={"sigma_X": "{:,.2f}".format,
                                        "q": "{:,.1f}".format,
                                        "Stock_Seguridad": "{:,.1f}".format,
                                        "P_Agotamiento": "{:.4f}".format,
                                        "SLM1": "{:.2%}".format,
                                        "Costo_Almacenamiento": "{:,.0f}".format,
                                        "Costo_Deficit": "{:,.0f}".format,
                                        "TC": "{:,.0f}".format}))

    print("\nResumen por politica:\n")
    print(resumen.to_string(index=False,
                            formatters={"SS_Base": "{:,.1f}".format,
                                        "SS_Alto": "{:,.1f}".format,
                                        "SS_Var_Pct": "{:+.2f}".format,
                                        "TC_Base": "{:,.0f}".format,
                                        "TC_Alto": "{:,.0f}".format,
                                        "TC_Var_Pct": "{:+.2f}".format,
                                        "Delta_TC": "{:+,.0f}".format}))

    fila_a = resumen[resumen["Politica"] == "A"].iloc[0]
    fila_b = resumen[resumen["Politica"] == "B"].iloc[0]

    print("\nLectura:")
    print(f"  Un {AUMENTO_SIGMA:.0%} mas de incertidumbre obliga a subir el stock de")
    print(f"  seguridad exactamente {AUMENTO_SIGMA:.0%} en las DOS politicas.")
    print("\n  El motivo es que ninguna de las dos puede reaccionar de otra forma:")
    print("  el stock de seguridad es z*sigma_X y ningun z depende de sigma_X.")
    print("  El de la Politica B esta fijado por el enunciado en 1,645; el de la")
    print("  Politica A sale de P(X >= r*) = h*q*/(c_B*E(D)), donde sigma_X no")
    print("  aparece. Tampoco se mueve q, porque el EOQ tampoco depende de sigma_X.")
    print("  Toda la incertidumbre extra se paga con stock, sin margen de maniobra.")

    delta_a = f"{fila_a['Delta_TC']:+,.0f}".replace(",", ".")
    delta_b = f"{fila_b['Delta_TC']:+,.0f}".replace(",", ".")
    print(f"\n  En costo, A se encarece {fila_a['TC_Var_Pct']:+.2f}% (USD {delta_a}) "
          f"y B {fila_b['TC_Var_Pct']:+.2f}% (USD {delta_b}).")
    print("  A absorbe mejor el golpe: parte de un stock de seguridad mas alto, asi")
    print("  que el deficit adicional que genera la mayor volatilidad es menor.")
    mas_robusta = "A" if fila_a["TC_Var_Pct"] < fila_b["TC_Var_Pct"] else "B"
    print(f"\n  La Politica {mas_robusta} es la mas robusta ante un mercado mas volatil.")

    rutas.preparar(rutas.SENSIBILIDAD)
    rutas.guardar_tabla(detalle, rutas.SENSIBILIDAD / "riesgo_demanda_detalle.csv")
    rutas.guardar_tabla(resumen, rutas.SENSIBILIDAD / "riesgo_demanda_resumen.csv")
    graficar(detalle, resumen, rutas.SENSIBILIDAD / "riesgo_demanda.png")


if __name__ == "__main__":
    main()
