"""Etapa 4b - Aplicacion y comparacion de las dos politicas de inventario.

Sigue el capitulo 16 de Winston. Sobre cada componente se resuelven:

  Politica A: pedidos pendientes, seccion 16.6, ecuacion (13).
              q* = EOQ y r* de P(X >= r*) = h*q*/(c_B*E(D)).
              El nivel de servicio no se impone, sale de los costos.

  Politica B: nivel de servicio, seccion 16.7.
              q* = EOQ y r de P(X >= r) = alfa = 0.05.

Las dos usan el mismo q y se miden con la misma TC(q, r) de la ecuacion (11).
Eso hace que la comparacion aisle exactamente lo unico que las distingue: como
cada una fija el punto de reabastecimiento.

El costo de compra no entra en TC(q, r). No es una decision nuestra: Winston lo
define asi, "costo anual esperado (sin incluir costo de compra)". Igual se
reporta aparte, porque el enunciado pide el costo total.

Las politicas se resuelven para los once componentes -el almacen tiene que
guardarlos a todos- pero la comparacion se reporta sobre los cinco de clase A,
que son sobre los que el enunciado pide aplicar los modelos avanzados.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from src import parametros, rutas
from src.inventario import modelos

COLUMNAS = [
    "Componente", "q", "r", "Stock_Seguridad", "z", "P_Agotamiento",
    "E_Br", "Pedidos_Anio", "Deficit_Anual", "SLM1", "SLM2",
    "Costo_Pedidos", "Costo_Almacenamiento", "Costo_Deficit", "TC",
]

# Orden de columnas del CSV. Primero las que identifican la fila y despues los
# resultados, que es como se lee una tabla: antes de mirar un q hay que saber de
# que componente y de que politica es.
COLUMNAS_SALIDA = [
    "Politica", "Componente", "Clase_ABC",
    "Demanda_Anual", "Costo_Unitario", "Volumen_m3",
    "q", "r", "z", "Stock_Seguridad", "E_Br", "P_Agotamiento", "SLM1", "SLM2",
    "Pedidos_Anio", "Deficit_Anual",
    "Costo_Pedidos", "Costo_Almacenamiento", "Costo_Deficit", "TC",
    "Costo_Compra",
]

FORMATOS = {
    "q": "{:,.1f}".format,
    "r": "{:,.1f}".format,
    "Stock_Seguridad": "{:,.1f}".format,
    "z": "{:.3f}".format,
    "P_Agotamiento": "{:.4f}".format,
    "E_Br": "{:.3f}".format,
    "Pedidos_Anio": "{:.1f}".format,
    "Deficit_Anual": "{:,.2f}".format,
    "SLM1": "{:.2%}".format,
    "SLM2": "{:.2f}".format,
    "Costo_Pedidos": "{:,.0f}".format,
    "Costo_Almacenamiento": "{:,.0f}".format,
    "Costo_Deficit": "{:,.0f}".format,
    "TC": "{:,.0f}".format,
}


def aplicar(catalogo):
    """Resuelve las dos politicas sobre cada componente del catalogo."""
    filas_a, filas_b = [], []

    for _, fila in catalogo.iterrows():
        argumentos = dict(
            E_D=fila["Demanda_Anual"],
            K=parametros.COSTO_ORDENAR,
            h=fila["h_Anual"],
            c_B=fila["c_B_Deficit"],
            E_X=fila["E_X"],
            sigma_X=fila["sigma_X"],
        )

        resultado_a = modelos.politica_pedidos_pendientes(**argumentos)
        resultado_b = modelos.politica_nivel_servicio(
            **argumentos, nivel_servicio=parametros.NIVEL_SERVICIO
        )

        for resultado, destino in ((resultado_a, filas_a), (resultado_b, filas_b)):
            resultado["Componente"] = fila["Componente"]
            resultado["Clase_ABC"] = fila["Clase_ABC"]
            resultado["Costo_Unitario"] = fila["Costo_Unitario"]
            resultado["Demanda_Anual"] = fila["Demanda_Anual"]
            resultado["Volumen_m3"] = fila["Volumen_m3"]
            # Costo de compra: fuera de TC(q, r), se reporta aparte
            resultado["Costo_Compra"] = fila["Costo_Unitario"] * fila["Demanda_Anual"]
            destino.append(resultado)

    return pd.DataFrame(filas_a), pd.DataFrame(filas_b)


def verificar_aproximacion_eoq(catalogo):
    """Comprueba que aproximar q* por el EOQ sea razonable en este caso.

    Winston aproxima q* = EOQ y cita a Brown (1967): la aproximacion es
    aceptable salvo que EOQ <= sigma_X. Aca se verifican las dos cosas, la
    condicion de Brown y la diferencia real contra la solucion exacta del
    sistema de condiciones de primer orden.
    """
    filas = []
    for _, fila in catalogo.iterrows():
        argumentos = dict(
            E_D=fila["Demanda_Anual"],
            K=parametros.COSTO_ORDENAR,
            h=fila["h_Anual"],
            c_B=fila["c_B_Deficit"],
            E_X=fila["E_X"],
            sigma_X=fila["sigma_X"],
        )
        winston = modelos.politica_pedidos_pendientes(**argumentos)
        exacto = modelos.resolver_exacto(**argumentos)
        filas.append({
            "Componente": fila["Componente"],
            "sigma_X": fila["sigma_X"],
            "q_EOQ": winston["q"],
            "q_exacto": exacto["q"],
            "Dif_q_Pct": 100 * (exacto["q"] / winston["q"] - 1),
            "TC_EOQ": winston["TC"],
            "TC_exacto": exacto["TC"],
            "Dif_TC_Pct": 100 * (exacto["TC"] / winston["TC"] - 1),
            "Cumple_Brown": winston["q"] > fila["sigma_X"],
            "Iteraciones": exacto["Iteraciones"],
        })
    return pd.DataFrame(filas)


def miles(valor, decimales=0):
    """Formatea con punto como separador de miles, sin tocar el resto del texto."""
    return f"{valor:,.{decimales}f}".replace(",", ".")


def mostrar(nombre, tabla):
    print(f"\n{nombre}\n")
    print(tabla[COLUMNAS].to_string(index=False, formatters=FORMATOS))
    print(f"\n  TC total: USD {miles(tabla['TC'].sum())}")


def comparar(tabla_a, tabla_b):
    """Tabla componente a componente con la diferencia entre politicas."""
    izquierda = tabla_a.set_index("Componente")
    derecha = tabla_b.set_index("Componente")

    comparacion = pd.DataFrame({
        "q": izquierda["q"],                      # igual en las dos politicas
        "r_A": izquierda["r"],
        "r_B": derecha["r"],
        "SS_A": izquierda["Stock_Seguridad"],
        "SS_B": derecha["Stock_Seguridad"],
        "P_Agot_A": izquierda["P_Agotamiento"],
        "P_Agot_B": derecha["P_Agotamiento"],
        "SLM1_A": izquierda["SLM1"],
        "SLM1_B": derecha["SLM1"],
        "TC_A": izquierda["TC"],
        "TC_B": derecha["TC"],
    })
    comparacion["Diferencia"] = comparacion["TC_B"] - comparacion["TC_A"]
    comparacion["Diferencia_Pct"] = 100 * comparacion["Diferencia"] / comparacion["TC_A"]
    return comparacion.reset_index()


def graficar(comparacion, tabla_a, tabla_b):
    fig, ejes = plt.subplots(1, 3, figsize=(16, 5))
    etiquetas = parametros.abreviar(comparacion["Componente"])
    posiciones = range(len(etiquetas))
    ancho = 0.38

    # Panel 1: descomposicion de TC(q, r) segun la ecuacion (11)
    izq = ejes[0]
    conceptos = ["Costo_Pedidos", "Costo_Almacenamiento", "Costo_Deficit"]
    nombres = ["Pedidos", "Almacenamiento", "Deficit"]
    colores = ["#4c72b0", "#dd8452", "#c44e52"]
    base_a = base_b = 0
    for concepto, nombre, color in zip(conceptos, nombres, colores):
        valor_a, valor_b = tabla_a[concepto].sum(), tabla_b[concepto].sum()
        izq.bar("Politica A", valor_a, bottom=base_a, color=color, label=nombre)
        izq.bar("Politica B", valor_b, bottom=base_b, color=color)
        base_a += valor_a
        base_b += valor_b
    # En miles: en USD crudos el eje muestra numeros de seis cifras que no
    # aportan precision y desalinean el panel con los otros dos.
    izq.yaxis.set_major_formatter(
        FuncFormatter(lambda valor, _: f"{valor / 1e3:,.0f}".replace(",", "."))
    )
    izq.set_ylabel("TC(q, r) anual (miles USD)")
    izq.set_title("Descomposicion del costo")
    # Aire arriba para que la leyenda no se apoye sobre la barra mas alta.
    izq.set_ylim(0, max(base_a, base_b) * 1.35)
    izq.legend(loc="upper left")
    izq.grid(axis="y", alpha=0.3)

    # Panel 2: stock de seguridad, que es lo unico que distingue a las politicas
    medio = ejes[1]
    medio.bar([p - ancho / 2 for p in posiciones], comparacion["SS_A"], ancho,
              label="Politica A", color="#4c72b0")
    medio.bar([p + ancho / 2 for p in posiciones], comparacion["SS_B"], ancho,
              label="Politica B", color="#dd8452")
    medio.set_ylabel("Stock de seguridad r - E(X) (unidades)")
    medio.set_title("Stock de seguridad por componente")
    medio.set_xticks(list(posiciones))
    medio.set_xticklabels(etiquetas, rotation=45, ha="right")
    medio.grid(axis="y", alpha=0.3)

    # Panel 3: probabilidad de agotamiento durante el plazo de entrega
    der = ejes[2]
    der.bar([p - ancho / 2 for p in posiciones], 100 * comparacion["P_Agot_A"], ancho,
            label="Politica A (resultante)", color="#4c72b0")
    der.bar([p + ancho / 2 for p in posiciones], 100 * comparacion["P_Agot_B"], ancho,
            label="Politica B (impuesta)", color="#dd8452")
    der.axhline(5, color="black", linestyle="--", linewidth=1,
                label=f"alfa = {parametros.ALPHA:.0%}")
    der.set_ylabel("P(X >= r)  (%)")
    der.set_title("Probabilidad de agotamiento en el plazo de entrega")
    der.set_xticks(list(posiciones))
    der.set_xticklabels(etiquetas, rotation=45, ha="right")
    # Las barras de la Politica B quedan justo sobre la linea de alfa, asi que
    # la leyenda de este panel se apoyaba encima de los datos. Solo se deja aca
    # la referencia de alfa; el color de cada politica ya lo explica el panel
    # del medio, que usa exactamente los mismos dos colores.
    der.set_ylim(0, 6.5)
    # Se selecciona por etiqueta y no por posicion: matplotlib devuelve primero
    # las lineas y despues las barras, asi que quedarse con el ultimo elemento
    # tomaba una barra en lugar de la linea de alfa.
    manejadores, nombres = der.get_legend_handles_labels()
    solo_alfa = [m for m, n in zip(manejadores, nombres) if n.startswith("alfa")]
    der.legend(handles=solo_alfa, fontsize=8, loc="upper left")
    der.grid(axis="y", alpha=0.3)

    # Una sola leyenda de politicas para toda la figura, abajo. Antes cada panel
    # repetia la suya diciendo lo mismo y con tamanos distintos.
    fig.legend(*medio.get_legend_handles_labels(), loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Politica A (pedidos pendientes) contra Politica B "
                 "(nivel de servicio 95%)", fontsize=13)
    fig.tight_layout()
    rutas.guardar_figura(fig, rutas.INVENTARIO / "comparacion_politicas.png")
    plt.close(fig)


def main():
    rutas.titulo("ETAPA 4b - POLITICAS DE INVENTARIO A Y B (Winston, cap. 16)")

    ruta = rutas.exigir(rutas.INVENTARIO / "parametros_riesgo.csv", "riesgo")
    catalogo = pd.read_csv(ruta)

    todos_a, todos_b = aplicar(catalogo)
    clase_a = catalogo[catalogo["Clase_ABC"] == "A"]
    tabla_a = todos_a[todos_a["Clase_ABC"] == "A"].reset_index(drop=True)
    tabla_b = todos_b[todos_b["Clase_ABC"] == "A"].reset_index(drop=True)

    print(f"Politicas resueltas para los {len(todos_a)} componentes del catalogo.")
    print(f"La comparacion se reporta sobre los {len(tabla_a)} de clase A.")
    print(f"\nPolitica B: z = {tabla_b['z'].iloc[0]:.4f} para alfa = {parametros.ALPHA}")

    # --- Verificacion de la aproximacion q* = EOQ ---
    rutas.titulo("VERIFICACION: LA APROXIMACION q* = EOQ")
    print("Winston aproxima q* por el EOQ y cita a Brown (1967): la aproximacion")
    print("es aceptable salvo que EOQ <= sigma_X. Se comprueba contra la solucion")
    print("exacta del sistema de condiciones de primer orden.\n")
    verificacion = verificar_aproximacion_eoq(clase_a)
    print(verificacion.to_string(index=False,
                                 formatters={"sigma_X": "{:.2f}".format,
                                             "q_EOQ": "{:.2f}".format,
                                             "q_exacto": "{:.2f}".format,
                                             "Dif_q_Pct": "{:+.2f}".format,
                                             "TC_EOQ": "{:,.0f}".format,
                                             "TC_exacto": "{:,.0f}".format,
                                             "Dif_TC_Pct": "{:+.3f}".format}))
    if verificacion["Cumple_Brown"].all():
        peor = verificacion["Dif_TC_Pct"].abs().max()
        print(f"\n  Los cinco componentes cumplen EOQ > sigma_X, y la solucion exacta")
        print(f"  mejora el costo a lo sumo un {peor:.3f}%. La aproximacion es valida.")

    mostrar("POLITICA A - Pedidos pendientes (optima por costos)", tabla_a)
    mostrar("POLITICA B - Nivel de servicio 95%", tabla_b)

    comparacion = comparar(tabla_a, tabla_b)

    rutas.titulo("COMPARACION A vs B")
    print("Las dos politicas piden el mismo q (el EOQ). Lo unico que cambia es r.\n")
    print(comparacion.to_string(
        index=False,
        formatters={"q": "{:,.1f}".format,
                    "r_A": "{:,.1f}".format, "r_B": "{:,.1f}".format,
                    "SS_A": "{:,.1f}".format, "SS_B": "{:,.1f}".format,
                    "P_Agot_A": "{:.4f}".format, "P_Agot_B": "{:.4f}".format,
                    "SLM1_A": "{:.2%}".format, "SLM1_B": "{:.2%}".format,
                    "TC_A": "{:,.0f}".format, "TC_B": "{:,.0f}".format,
                    "Diferencia": "{:+,.0f}".format,
                    "Diferencia_Pct": "{:+.2f}".format}))

    total_a, total_b = tabla_a["TC"].sum(), tabla_b["TC"].sum()
    compra = tabla_a["Costo_Compra"].sum()

    print("\nTotales anuales:\n")
    print(f"  {'':<32} {'Politica A':>16} {'Politica B':>16}")
    for concepto, etiqueta in (("Costo_Pedidos", "Pedidos"),
                               ("Costo_Almacenamiento", "Almacenamiento"),
                               ("Costo_Deficit", "Deficit")):
        print(f"  {etiqueta:<32} {miles(tabla_a[concepto].sum()):>16} "
              f"{miles(tabla_b[concepto].sum()):>16}")
    print(f"  {'-' * 66}")
    print(f"  {'TC(q, r)':<32} {miles(total_a):>16} {miles(total_b):>16}")
    print(f"  {'Costo de compra (fuera de TC)':<32} {miles(compra):>16} "
          f"{miles(compra):>16}")
    print(f"  {'Costo total':<32} {miles(total_a + compra):>16} "
          f"{miles(total_b + compra):>16}")

    diferencia = total_b - total_a
    print(f"\n  La Politica A ahorra USD {miles(diferencia)} al anio sobre TC(q, r),")
    print(f"  un {100 * diferencia / total_b:.1f}% menos que la Politica B.")
    print(f"  Sobre el costo total, con la compra incluida, esa misma diferencia")
    print(f"  seria del {100 * diferencia / (total_b + compra):.2f}%: por eso Winston")
    print(f"  define TC(q, r) sin el costo de compra.")

    # --- Nivel de servicio resultante (Winston 16.7) ---
    rutas.titulo("NIVEL DE SERVICIO RESULTANTE DE LA POLITICA OPTIMA POR COSTOS")
    print("La Politica A no fija el nivel de servicio: lo determina la relacion")
    print("entre c_B y h a traves de P(X >= r*) = h*q*/(c_B*E(D)).\n")

    ratios = clase_a.set_index("Componente")
    ratios = ratios["c_B_Deficit"] / ratios["h_Anual"]

    print(f"  {'Componente':<36} {'c_B/h':>6} {'P(X>=r)':>9} {'z':>7} "
          f"{'SLM1':>9} {'SLM2':>7}")
    for _, fila in tabla_a.iterrows():
        print(f"  {fila['Componente']:<36} {ratios[fila['Componente']]:>6.2f} "
              f"{fila['P_Agotamiento']:>9.4f} {fila['z']:>7.3f} "
              f"{fila['SLM1']:>8.2%} {fila['SLM2']:>7.2f}")

    print("\n  SLM1 = fraccion de la demanda que se cumple a tiempo")
    print("  SLM2 = ciclos por anio en los que se presenta deficit")

    slm1_medio = modelos.promedio_ponderado(tabla_a["SLM1"],
                                            tabla_a["Demanda_Anual"])
    p_media = modelos.promedio_ponderado(tabla_a["P_Agotamiento"],
                                         tabla_a["Demanda_Anual"])
    print(f"\n  Ponderado por demanda: SLM1 = {slm1_medio:.2%}, "
          f"P(X >= r) = {p_media:.4f}")
    if p_media < parametros.ALPHA:
        print(f"  La probabilidad de agotamiento queda por debajo del alfa = "
              f"{parametros.ALPHA} exigido")
        print(f"  a la Politica B: el optimo economico ya es mas conservador que la")
        print(f"  restriccion de servicio del enunciado.")

    rutas.preparar(rutas.INVENTARIO)

    # Las dos politicas van a un solo archivo. Tienen exactamente las mismas
    # columnas y ya traen una que dice a cual pertenece cada fila, asi que
    # separarlas obligaba a mantener dos tablas de esquema identico y a volver a
    # cruzarlas para compararlas. Filtrar por la columna Politica es mas simple.
    politicas = pd.concat([todos_a, todos_b], ignore_index=True)
    rutas.guardar_tabla(politicas[COLUMNAS_SALIDA],
                        rutas.INVENTARIO / "politicas.csv")
    rutas.guardar_tabla(verificacion, rutas.INVENTARIO / "verificacion_eoq.csv")

    # La comparacion A contra B no se guarda: sale entera de filtrar la tabla
    # anterior por politica y restar. Se usa solo para el grafico y para la
    # lectura por consola.
    graficar(comparacion, tabla_a, tabla_b)


if __name__ == "__main__":
    main()
