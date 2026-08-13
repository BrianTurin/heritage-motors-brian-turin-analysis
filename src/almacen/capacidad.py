"""Etapa 5 - Capacidad minima de almacen.

Traduce cada politica de inventario a metros cubicos y evalua si el almacen que
hay que construir es factible para una y para otra.


CUANTO STOCK HAY QUE GUARDAR
----------------------------
En el sistema (r, q) el stock fisico en el deposito sube hasta su maximo justo
cuando llega un pedido, y en ese instante vale:

    inventario maximo = q + (r - E(X))

o sea el lote que acaba de entrar mas el stock de seguridad que quedaba. Sale
de la misma cuenta que hace Winston en la pag. 892 al deducir la ecuacion (11):
el nivel de inventario al principio del ciclo es r - E(X) + q.

No hay que sumarle r entero. r es el nivel que dispara la orden, y la demanda
del plazo de entrega que r cubre se consume mientras el pedido viaja, no se
almacena. Sumar r ademas contaria el stock de seguridad dos veces, porque r ya
lo lleva adentro: r = E(X) + stock de seguridad.

El total se calcula sumando el maximo de cada componente. Es conservador: en la
practica los picos de los distintos componentes no caen todos el mismo dia,
porque cada uno tiene su propio lead time y su propio ciclo. Como para
dimensionar un galpon conviene errar por exceso, se deja asi y se aclara.

Se toman los once componentes del catalogo, no solo los cinco de clase A: los
modelos de inventario se aplican sobre la clase A porque ahi esta el valor,
pero el deposito tiene que guardar todo lo que entra.


QUE NO ESTA INCLUIDO
--------------------
El calculo cubre el inventario de componentes, que es lo que pide el enunciado.
Un deposito real necesita ademas espacio para material en proceso, vehiculos
terminados a la espera de entrega y devoluciones. Tambien queda afuera cualquier
lote minimo de compra que imponga un proveedor, que obligaria a pedir mas de lo
que dice el modelo. Todo eso se suma al numero que sale de aca, asi que la cifra
hay que leerla como un piso para el sector de componentes y no como el tamanio
total del edificio.


DEL VOLUMEN NETO AL GALPON
--------------------------
Los metros cubicos de mercaderia no son los metros cubicos del edificio: hacen
falta pasillos de circulacion, zonas de carga y descarga, areas de maniobra y
espacios libres por seguridad. El Manual de Buenas Practicas de la
Superintendencia de Riesgos del Trabajo para la industria automotriz enumera
esos requisitos.

Para cuantificarlos se usa el rango de utilizacion que reporta NetSuite
(Warehouse Space Utilization, Abby Jenkins): las empresas suelen aprovechar
entre el 45% y el 85% del espacio total. Se plantean dos escenarios dentro de
ese rango, uno conservador y uno exigente.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from src import parametros, rutas

# Escenarios de aprovechamiento del espacio (referencia NetSuite: 45% a 85%)
ESCENARIOS = {
    "Conservador": 0.65,
    "Optimo": 0.75,
}

# Costo de referencia de construccion por metro cuadrado cubierto
COSTO_M2 = 1500.0

# Altura util supuesta para pasar de volumen a superficie. Cinco metros es una
# altura estandar de galpon industrial con estanteria; subir mas obliga a
# equipos de elevacion mas caros y complica la operacion.
ALTURA_UTIL_M = 5.0


def capacidad_por_politica(tabla, etiqueta):
    """Inventario maximo y volumen requerido de cada componente."""
    resultado = pd.DataFrame({
        "Componente": tabla["Componente"],
        "Politica": etiqueta,
        "q": tabla["q"],
        "Stock_Seguridad": tabla["Stock_Seguridad"],
        "Inventario_Maximo": tabla["q"] + tabla["Stock_Seguridad"],
        "Volumen_Unitario_m3": tabla["Volumen_m3"],
    })
    resultado["Capacidad_Requerida_m3"] = (
        resultado["Inventario_Maximo"] * resultado["Volumen_Unitario_m3"]
    )
    return resultado


def dimensionar(volumen_neto):
    """Convierte volumen neto en superficie y costo, para cada escenario.

    Cada paso redondea antes de alimentar al siguiente, para que la cadena
    volumen -> superficie -> costo se pueda rehacer a mano con las mismas cifras
    que muestra el informe. Con los valores exactos el costo sale de 107,3011 m2
    x 1.500 = 160.952, y un lector que multiplica los 107 m2 de la tabla obtiene
    160.500: la tabla dejaba de cerrar consigo misma. Nadie construye 107,3 m2,
    asi que se redondea y se valoriza sobre el redondeo.
    """
    neto = round(volumen_neto, 1)
    filas = []
    for nombre, utilizacion in ESCENARIOS.items():
        volumen_total = round(neto / utilizacion)
        superficie = round(volumen_total / ALTURA_UTIL_M)
        filas.append({
            "Escenario": nombre,
            "Utilizacion": utilizacion,
            "Volumen_Neto_m3": neto,
            "Volumen_Almacen_m3": volumen_total,
            "Superficie_m2": superficie,
            "Costo_Construccion_USD": superficie * COSTO_M2,
        })
    return pd.DataFrame(filas)


# Nombre corto de cada politica para los ejes. Los nombres completos ocupan mas
# de veinte caracteres y, puestos uno al lado del otro, se superponen hasta
# volverse ilegibles.
POLITICA_CORTA = {
    "A - Pedidos pendientes": "A",
    "B - Nivel de servicio 95%": "B",
}


def graficar(detalle, ruta):
    fig, (izq, der) = plt.subplots(1, 2, figsize=(14, 5))

    # Volumen requerido por componente, comparando politicas. Se ordena de mayor
    # a menor: la pregunta que contesta el panel es que componentes se comen el
    # almacen, y ordenado alfabeticamente esa respuesta hay que buscarla.
    pivote = detalle.pivot(index="Componente", columns="Politica",
                           values="Capacidad_Requerida_m3")
    pivote = pivote.loc[pivote.max(axis=1).sort_values().index]
    pivote.index = parametros.abreviar(pivote.index)
    pivote.plot(kind="barh", ax=izq, color=["#4c72b0", "#dd8452"])
    izq.set_xlabel("Volumen requerido (m³)")
    izq.set_ylabel("")
    izq.set_title("Espacio por componente")
    izq.grid(axis="x", alpha=0.3)
    izq.legend(title="Politica")

    # Total por politica: el volumen neto de las piezas y lo que hay que
    # construir con cada nivel de aprovechamiento del galpon.
    totales = detalle.groupby("Politica")["Capacidad_Requerida_m3"].sum()
    etiquetas, valores, colores = [], [], []
    for politica, neto in totales.items():
        corta = POLITICA_CORTA.get(politica, politica)
        es_a = corta == "A"
        etiquetas.append(f"{corta}\nneto")
        valores.append(neto)
        colores.append("#4c72b0" if es_a else "#dd8452")
        for nombre, utilizacion in ESCENARIOS.items():
            etiquetas.append(f"{corta}\n{nombre}")
            valores.append(neto / utilizacion)
            colores.append("#a3bcd8" if es_a else "#f0c3a0")

    barras = der.bar(etiquetas, valores, color=colores)
    der.set_ylabel("Volumen de almacen (m³)")
    der.set_title("Capacidad requerida segun politica y aprovechamiento")
    der.grid(axis="y", alpha=0.3)
    # Aire arriba para que la leyenda no tape ni las barras ni sus numeros.
    der.set_ylim(0, max(valores) * 1.3)
    for barra, valor in zip(barras, valores):
        der.text(barra.get_x() + barra.get_width() / 2, valor,
                 f"{valor:,.0f}".replace(",", "."), ha="center", va="bottom",
                 fontsize=8)

    # El tono claro y el oscuro distinguen el volumen neto de lo que hay que
    # construir, y eso solo estaba dicho en las etiquetas del eje.
    der.legend(handles=[
        Patch(facecolor="#7f7f7f", label="Volumen neto de las piezas"),
        Patch(facecolor="#cccccc", label="Galpon a construir (segun aprovechamiento)"),
    ], loc="upper left", fontsize=8)

    fig.suptitle("Dimensionamiento del almacen central", fontsize=13)
    fig.tight_layout()
    rutas.guardar_figura(fig, ruta)
    plt.close(fig)


def main():
    rutas.titulo("ETAPA 5 - CAPACIDAD MINIMA DE ALMACEN")

    ruta = rutas.exigir(rutas.INVENTARIO / "politicas.csv", "politicas")
    politicas = pd.read_csv(ruta)

    # Las dos politicas vienen en la misma tabla, distinguidas por la columna
    # Politica. Se procesa cada una por separado porque el inventario maximo, y
    # por lo tanto el lugar que hace falta en el almacen, es distinto en cada una.
    detalle = pd.concat(
        [capacidad_por_politica(grupo, nombre)
         for nombre, grupo in politicas.groupby("Politica", sort=True)],
        ignore_index=True,
    )

    print("Inventario maximo q + (r - E(X)) y volumen requerido:\n")
    print(detalle.to_string(index=False,
                            formatters={"q": "{:,.1f}".format,
                                        "Stock_Seguridad": "{:,.0f}".format,
                                        "Inventario_Maximo": "{:,.0f}".format,
                                        "Volumen_Unitario_m3": "{:.2f}".format,
                                        "Capacidad_Requerida_m3": "{:,.1f}".format}))

    totales = detalle.groupby("Politica")["Capacidad_Requerida_m3"].sum()
    print("\nVolumen neto de mercaderia por politica:")
    for politica, valor in totales.items():
        print(f"  {politica:<28} {valor:>10,.0f} m3".replace(",", "."))

    dimensiones = []
    for politica, neto in totales.items():
        tabla = dimensionar(neto)
        tabla.insert(0, "Politica", politica)
        dimensiones.append(tabla)
    dimensiones = pd.concat(dimensiones, ignore_index=True)

    print("\nDimensionamiento del galpon (altura util "
          f"{ALTURA_UTIL_M:.0f} m, USD {COSTO_M2:,.0f}/m2):\n".replace(",", "."))
    print(dimensiones.to_string(index=False,
                                formatters={"Utilizacion": "{:.0%}".format,
                                            "Volumen_Neto_m3": "{:,.0f}".format,
                                            "Volumen_Almacen_m3": "{:,.0f}".format,
                                            "Superficie_m2": "{:,.0f}".format,
                                            "Costo_Construccion_USD": "{:,.0f}".format}))

    # Analisis de factibilidad: la politica mas barata no es la que menos
    # espacio necesita. Este es el compromiso que hay que poner sobre la mesa.
    rutas.titulo("FACTIBILIDAD DE CADA POLITICA FRENTE A LA RESTRICCION")
    politica_barata = "A - Pedidos pendientes"
    politica_compacta = totales.idxmin()
    diferencia = totales.max() - totales.min()
    porcentaje = 100 * diferencia / totales.min()

    print(f"La politica de menor costo es la {politica_barata}.")
    print(f"La que menos espacio necesita es la {politica_compacta}.")
    print(f"\nDiferencia de volumen neto: {diferencia:,.0f} m3 "
          f"({porcentaje:.0f}% mas)".replace(",", "."))

    costos = dimensiones[dimensiones["Escenario"] == "Conservador"].set_index("Politica")
    delta_obra = (costos.loc[politica_barata, "Costo_Construccion_USD"]
                  - costos["Costo_Construccion_USD"].min())
    print(f"Sobrecosto de obra del escenario conservador: USD {delta_obra:,.0f}"
          .replace(",", "."))
    print("\nLa Politica A pide mas galpon porque pide lotes mas grandes y mas")
    print("stock de seguridad. Ese sobrecosto es de una sola vez, mientras que la")
    print("diferencia de costo operativo se repite todos los anios: conviene")
    print("compararlos sobre el mismo horizonte antes de decidir.")

    rutas.preparar(rutas.ALMACEN)
    rutas.guardar_tabla(detalle, rutas.ALMACEN / "capacidad_detalle.csv")
    rutas.guardar_tabla(dimensiones, rutas.ALMACEN / "capacidad_dimensionamiento.csv")
    graficar(detalle, rutas.ALMACEN / "capacidad_almacen.png")


if __name__ == "__main__":
    main()
