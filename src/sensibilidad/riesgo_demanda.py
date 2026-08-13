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

Vale aclarar de donde sale esa rigidez, porque es de la aproximacion q* = EOQ de
la ecuacion (13) y no del modelo (q, r) en general. En el sistema exacto de la
ecuacion (12) el lote lleva sumado el deficit del ciclo,

    q = (2*E(D)*(K + c_B*E(B_r)) / h)^(1/2)

y ahi sigma_X si entra, a traves de E(B_r). Resuelto asi, el modelo amortigua un
poco: pide lotes 3 a 5% mas grandes, y como menos ciclos al anio son menos
oportunidades de agotarse, el stock de seguridad sube 13,5 a 14,3% en vez del 15%
exacto. El margen de maniobra existe, pero es marginal, asi que la conclusion de
fondo se sostiene: la volatilidad se paga casi entera con capital parado. La
verificacion de la etapa 4b (verificacion_eoq.csv) va en la misma linea, con q
del exacto 17 a 37% por encima del EOQ pero TC a menos del 2% de diferencia.

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

ESCENARIO_BASE = "Base"
ESCENARIO_ENUNCIADO = f"+{AUMENTO_SIGMA:.0%}"
ESCENARIO_VALIDACION = "sigma de validacion"


def factor_validacion():
    """Cuanto mas grande es el error fuera de muestra que el del ajuste.

    El stock de seguridad se dimensiona con el desvio de los residuos del
    ajuste, que subestima el error real porque el modelo ya vio esos meses. El
    RMSE de la validacion de origen movil si es fuera de muestra y da bastante
    mas alto. Este escenario mide cuanto cambiaria todo si se usara ese, que es
    la unica incertidumbre del modelo que no cubre el +15% del enunciado.
    """
    ruta = rutas.exigir(rutas.PRONOSTICO / "resumen_pronostico.csv", "pronostico")
    resumen = pd.read_csv(ruta).iloc[0]
    return float(resumen["RMSE_Validacion"] / resumen["Sigma_Error_Mensual"])


def evaluar(parametros_riesgo, escenarios):
    """Resuelve ambas politicas en cada escenario de incertidumbre."""
    filas = []
    for nombre, factor in escenarios.items():
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
    """Totales por politica y escenario, con la variacion contra el base.

    Va en formato largo, con una columna Escenario, en vez de una columna por
    escenario: asi agregar un escenario mas no cambia la forma de la tabla.
    """
    agregado = detalle.groupby(["Politica", "Escenario"], sort=False).agg(
        Stock_Seguridad=("Stock_Seguridad", "sum"),
        Costo_Almacenamiento=("Costo_Almacenamiento", "sum"),
        Costo_Deficit=("Costo_Deficit", "sum"),
        TC=("TC", "sum"),
    ).reset_index()

    base = (agregado[agregado["Escenario"] == ESCENARIO_BASE]
            .set_index("Politica"))

    agregado["SS_Var_Pct"] = [
        100 * (fila.Stock_Seguridad / base.loc[fila.Politica, "Stock_Seguridad"] - 1)
        for fila in agregado.itertuples()
    ]
    agregado["TC_Var_Pct"] = [
        100 * (fila.TC / base.loc[fila.Politica, "TC"] - 1)
        for fila in agregado.itertuples()
    ]
    agregado["Delta_TC"] = [
        fila.TC - base.loc[fila.Politica, "TC"] for fila in agregado.itertuples()
    ]
    return agregado


def graficar(detalle, resumen, ruta):
    fig, ejes = plt.subplots(1, 3, figsize=(16, 5))

    # Los dos primeros paneles contrastan el base con el escenario que pide el
    # enunciado. El de sigma de validacion queda en la tabla: con tres barras
    # por politica el panel deja de leerse de un vistazo, y ademas responde otra
    # pregunta (que tan bien estimamos el error, no que tan volatil es el mercado).
    ss = resumen.pivot(index="Politica", columns="Escenario",
                       values="Stock_Seguridad")
    tc = resumen.pivot(index="Politica", columns="Escenario", values="TC")
    variacion = resumen.set_index(["Politica", "Escenario"])
    politicas = list(ss.index)
    posiciones = range(len(politicas))
    ancho = 0.35

    # Stock de seguridad total: base vs +15%
    izq = ejes[0]
    izq.bar([p - ancho / 2 for p in posiciones], ss[ESCENARIO_BASE], ancho,
            label="Base", color="#4c72b0")
    izq.bar([p + ancho / 2 for p in posiciones], ss[ESCENARIO_ENUNCIADO], ancho,
            label=f"+{AUMENTO_SIGMA:.0%} sigma_X", color="#c44e52")
    izq.set_xticks(list(posiciones))
    izq.set_xticklabels([f"Politica {p}" for p in politicas])
    izq.set_ylabel("Stock de seguridad total (unidades)")
    izq.set_title("La incertidumbre obliga a mas stock de seguridad")
    izq.grid(axis="y", alpha=0.3)
    # Aire arriba: sin esto la etiqueta de variacion de la barra mas alta queda
    # tapada por la leyenda.
    izq.set_ylim(0, ss[ESCENARIO_ENUNCIADO].max() * 1.2)
    for posicion, politica in zip(posiciones, politicas):
        pct = variacion.loc[(politica, ESCENARIO_ENUNCIADO), "SS_Var_Pct"]
        izq.text(posicion + ancho / 2, ss.loc[politica, ESCENARIO_ENUNCIADO],
                 f"{pct:+.1f}%", ha="center", va="bottom", fontsize=9)

    # TC(q, r) total: base vs +15%
    medio = ejes[1]
    medio.bar([p - ancho / 2 for p in posiciones], tc[ESCENARIO_BASE] / 1e3, ancho,
              label="Base", color="#4c72b0")
    medio.bar([p + ancho / 2 for p in posiciones], tc[ESCENARIO_ENUNCIADO] / 1e3,
              ancho, label=f"+{AUMENTO_SIGMA:.0%} sigma_X", color="#c44e52")
    medio.set_xticks(list(posiciones))
    medio.set_xticklabels([f"Politica {p}" for p in politicas])
    medio.set_ylabel("TC(q, r) total anual (miles USD)")
    medio.set_title("Impacto en el costo total")
    medio.grid(axis="y", alpha=0.3)
    medio.set_ylim(0, tc[ESCENARIO_ENUNCIADO].max() / 1e3 * 1.2)
    for posicion, politica in zip(posiciones, politicas):
        pct = variacion.loc[(politica, ESCENARIO_ENUNCIADO), "TC_Var_Pct"]
        medio.text(posicion + ancho / 2, tc.loc[politica, ESCENARIO_ENUNCIADO] / 1e3,
                   f"{pct:+.1f}%", ha="center", va="bottom", fontsize=9)

    # Stock de seguridad por componente
    der = ejes[2]
    pivote = detalle[detalle["Escenario"] == f"+{AUMENTO_SIGMA:.0%}"].pivot(
        index="Componente", columns="Politica", values="Stock_Seguridad"
    )
    pivote.index = parametros.abreviar(pivote.index)
    pivote.plot(kind="barh", ax=der, color=["#4c72b0", "#dd8452"])
    der.set_xlabel(f"Stock de seguridad con +{AUMENTO_SIGMA:.0%} sigma_X (unidades)")
    der.set_ylabel("")
    der.set_title(f"Stock de seguridad por componente con +{AUMENTO_SIGMA:.0%}")
    der.grid(axis="x", alpha=0.3)
    der.legend(title="Politica")

    # Los paneles 1 y 2 usan el mismo par de colores para lo mismo, asi que la
    # referencia va una sola vez a nivel de figura en vez de repetirse en cada uno.
    fig.legend(*izq.get_legend_handles_labels(), loc="lower center", ncol=2,
               bbox_to_anchor=(0.35, -0.02))
    fig.suptitle(f"Sensibilidad al riesgo: +{AUMENTO_SIGMA:.0%} de incertidumbre "
                 f"en la demanda", fontsize=13)
    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)


def main():
    rutas.titulo(f"ETAPA 6b - SENSIBILIDAD AL RIESGO (+{AUMENTO_SIGMA:.0%} DE INCERTIDUMBRE)")

    ruta = rutas.exigir(rutas.INVENTARIO / "parametros_riesgo.csv", "riesgo")
    # Se analiza la clase A, igual que la comparacion de politicas, para que el
    # TC base coincida con el que se reporta alli.
    parametros_riesgo = pd.read_csv(ruta).query("Clase_ABC == 'A'").reset_index(drop=True)

    factor = factor_validacion()
    escenarios = {
        ESCENARIO_BASE: 1.0,
        ESCENARIO_ENUNCIADO: 1 + AUMENTO_SIGMA,
        ESCENARIO_VALIDACION: factor,
    }
    print(f"Escenario adicional: sigma de validacion, factor {factor:.4f} "
          f"(+{100 * (factor - 1):.2f}% sobre el desvio del ajuste)\n")

    detalle = evaluar(parametros_riesgo, escenarios)
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

    print("\nResumen por politica y escenario:\n")
    print(resumen.to_string(index=False,
                            formatters={"Stock_Seguridad": "{:,.1f}".format,
                                        "Costo_Almacenamiento": "{:,.0f}".format,
                                        "Costo_Deficit": "{:,.0f}".format,
                                        "TC": "{:,.0f}".format,
                                        "SS_Var_Pct": "{:+.2f}".format,
                                        "TC_Var_Pct": "{:+.2f}".format,
                                        "Delta_TC": "{:+,.0f}".format}))

    def buscar(politica, escenario):
        seleccion = resumen[(resumen["Politica"] == politica)
                            & (resumen["Escenario"] == escenario)]
        return seleccion.iloc[0]

    fila_a = buscar("A", ESCENARIO_ENUNCIADO)
    fila_b = buscar("B", ESCENARIO_ENUNCIADO)

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

    val_a = buscar("A", ESCENARIO_VALIDACION)
    val_b = buscar("B", ESCENARIO_VALIDACION)
    print(f"\n  Escenario '{ESCENARIO_VALIDACION}' ({val_a['SS_Var_Pct']:+.1f}% de sigma):")
    print(f"    A  SS {val_a['Stock_Seguridad']:.1f}  TC "
          f"{val_a['TC']:,.0f} ({val_a['TC_Var_Pct']:+.2f}%)".replace(",", "."))
    print(f"    B  SS {val_b['Stock_Seguridad']:.1f}  TC "
          f"{val_b['TC']:,.0f} ({val_b['TC_Var_Pct']:+.2f}%)".replace(",", "."))
    ventaja = val_b["TC"] - val_a["TC"]
    print(f"    Aun con el desvio fuera de muestra, A sigue siendo mas barata por "
          f"USD {ventaja:,.0f}.".replace(",", "."))

    rutas.preparar(rutas.SENSIBILIDAD)
    rutas.guardar_tabla(detalle, rutas.SENSIBILIDAD / "riesgo_demanda_detalle.csv")
    rutas.guardar_tabla(resumen, rutas.SENSIBILIDAD / "riesgo_demanda_resumen.csv")
    graficar(detalle, resumen, rutas.SENSIBILIDAD / "riesgo_demanda.png")


if __name__ == "__main__":
    main()
