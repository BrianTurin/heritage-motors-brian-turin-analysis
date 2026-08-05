"""Etapa 1b - Serie mensual de vehiculos vendidos.

Agrega las lineas de pedido limpias en una serie mensual con los vehiculos de
cada tipo. Esta serie es la entrada de los tres modelos de pronostico y de la
clasificacion XYZ.


POR QUE CANTIDADES Y NO FACTURACION
-----------------------------------
Los modelos de inventario piden cantidades de componentes, y cada vehiculo
consume una cantidad fija de cada componente segun la tabla del enunciado.
Pasar por la facturacion obligaria a suponer un precio por vehiculo que el
enunciado no da, y todo el trabajo quedaria colgado de ese supuesto.


POR QUE UNA LINEA DE PEDIDO EQUIVALE A UN VEHICULO
--------------------------------------------------
El dataset de origen es de maquetas de autos a escala: cada linea es un
producto distinto dentro del pedido de un cliente, y se compra a granel
(35 unidades por linea en promedio, mediana 34) porque son coleccionables que
un distribuidor revende.

El caso de Heritage Motors es otro negocio. Un cliente no encarga 35 restomods
identicos: encarga un vehiculo con una configuracion. La correspondencia
natural entre las dos operaciones es entonces

    una linea de pedido  ->  un vehiculo encargado

y no "una unidad del dataset -> un vehiculo", que daria 22.390 vehiculos
anuales para un fabricante-restaurador de nicho.

Lo importante es que la eleccion no altera el patron de demanda, que es lo que
el dataset realmente aporta:

  - correlacion mensual entre contar lineas y contar unidades: 0,997
  - el pico de noviembre se conserva (x3,64 en 2003 y x2,92 en 2004)
  - el reparto Clasico/Vintage practicamente no se mueve (61,6% contra 61,9%)

Se conserva igual la columna de unidades del dataset, para poder verificar
todo esto y para dejar la trazabilidad con la fuente.
"""

import pandas as pd

from src import parametros, rutas


def construir_serie(df):
    """Devuelve vehiculos por mes y por tipo, contando lineas de pedido."""
    df = df.copy()
    df["Periodo"] = df["ORDERDATE"].dt.to_period("M").dt.to_timestamp()

    # size cuenta filas, o sea lineas de pedido, o sea vehiculos
    tabla = df.pivot_table(
        index="Periodo",
        columns="PRODUCTLINE",
        values="QUANTITYORDERED",
        aggfunc="size",
        fill_value=0,
    )
    tabla = tabla.rename(
        columns={
            parametros.LINEA_CLASICO: "Unidades_Clasicos",
            parametros.LINEA_VINTAGE: "Unidades_Vintage",
        }
    )

    # Meses sin ventas registradas quedan explicitos en cero, no salteados
    rango = pd.date_range(tabla.index.min(), tabla.index.max(), freq="MS")
    tabla = tabla.reindex(rango, fill_value=0)
    tabla.index.name = "Periodo"

    tabla["Unidades_Total"] = tabla["Unidades_Clasicos"] + tabla["Unidades_Vintage"]

    # Columnas de referencia: no las usa ningun modelo, quedan para poder
    # contrastar la serie de vehiculos contra la fuente original.
    unidades = df.groupby("Periodo")["QUANTITYORDERED"].sum().reindex(rango, fill_value=0)
    tabla["Unidades_Dataset"] = unidades.values

    facturacion = df.groupby("Periodo")["SALES"].sum().reindex(rango, fill_value=0.0)
    tabla["Ventas_USD"] = facturacion.values

    return tabla.reset_index()


def main():
    rutas.titulo("ETAPA 1b - SERIE MENSUAL DE VEHICULOS")
    rutas.exigir(rutas.VENTAS_LIMPIAS, "limpiar")

    df = pd.read_csv(rutas.VENTAS_LIMPIAS, parse_dates=["ORDERDATE"])
    serie = construir_serie(df)

    rutas.preparar(rutas.DATOS_LIMPIOS)
    serie.to_csv(rutas.SERIE_MENSUAL, index=False, encoding="utf-8")

    total = serie["Unidades_Total"].sum()
    clasicos = serie["Unidades_Clasicos"].sum()
    vintage = serie["Unidades_Vintage"].sum()

    print(f"Meses en la serie : {len(serie)}")
    print(f"Periodo           : {serie['Periodo'].min():%Y-%m} a {serie['Periodo'].max():%Y-%m}")
    print(f"Vehiculos totales : {total:,}".replace(",", "."))
    print(f"  Clasicos        : {clasicos:,} ({clasicos / total:.2%})".replace(",", "."))
    print(f"  Vintage         : {vintage:,} ({vintage / total:.2%})".replace(",", "."))
    print(f"Promedio mensual  : {total / len(serie):,.1f} vehiculos".replace(",", "."))
    # Control de que contar lineas no deforma el patron de demanda
    correlacion = serie["Unidades_Total"].corr(serie["Unidades_Dataset"])
    unidades_dataset = f"{serie['Unidades_Dataset'].sum():,}".replace(",", ".")
    print(f"\nControl: correlacion con la serie de unidades del dataset = {correlacion:.4f}")
    print(f"         (unidades del dataset: {unidades_dataset})")

    print("\nVehiculos por mes:")
    for _, fila in serie.iterrows():
        print(
            f"  {fila['Periodo']:%Y-%m}  total {int(fila['Unidades_Total']):>5}"
            f"   clasicos {int(fila['Unidades_Clasicos']):>5}"
            f"   vintage {int(fila['Unidades_Vintage']):>5}"
        )

    print(f"\n  [csv] {rutas.SERIE_MENSUAL.relative_to(rutas.RAIZ)}")


if __name__ == "__main__":
    main()
