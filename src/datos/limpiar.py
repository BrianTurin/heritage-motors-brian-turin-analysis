"""Etapa 1a - Limpieza del dataset de ventas.

Parte de data/raw/sales_data_sample.csv (dataset publico "classicmodels",
2.823 lineas de pedido) y deja en data/processed/ventas_limpias.csv solo las
lineas que representan demanda real de los dos vehiculos del caso.

Decisiones de limpieza (cada una se justifica en el informe):

1. Nos quedamos con PRODUCTLINE en {Classic Cars, Vintage Cars}. El resto de
   las lineas (aviones, barcos, motos, trenes, camiones) no corresponden al
   negocio de Heritage Motors.

2. Descartamos unicamente STATUS == 'Cancelled'. Un pedido cancelado no llego
   a ser demanda satisfecha ni pendiente. Los estados 'Shipped', 'Resolved',
   'In Process', 'On Hold' y 'Disputed' si son demanda: el cliente pidio la
   unidad. Filtrar solo por 'Shipped' recorta los ultimos meses de la serie
   (abril 2005 pasaria de 29 a 12 lineas) e introduce un valle artificial.

3. PRICEEACH viene topeado en 100 en 797 de las 1.574 lineas del caso, asi que
   no coincide con SALES / QUANTITYORDERED. Recalculamos el precio unitario a
   partir de SALES, que es el campo consistente.

4. Descartamos filas sin fecha valida o con cantidad no positiva.
"""

import pandas as pd

from src import rutas

ESTADOS_DESCARTADOS = ["Cancelled"]
LINEAS_DEL_CASO = ["Classic Cars", "Vintage Cars"]

COLUMNAS_UTILES = [
    "ORDERNUMBER",
    "ORDERLINENUMBER",
    "ORDERDATE",
    "STATUS",
    "PRODUCTLINE",
    "PRODUCTCODE",
    "QUANTITYORDERED",
    "PRICEEACH",
    "SALES",
    "MSRP",
]


def main():
    rutas.titulo("ETAPA 1a - LIMPIEZA DEL DATASET")
    rutas.exigir(rutas.VENTAS_CRUDAS, "datos")

    df = pd.read_csv(rutas.VENTAS_CRUDAS, encoding="latin-1", low_memory=False)
    df = df[COLUMNAS_UTILES].copy()
    print(f"Lineas en el dataset original: {len(df)}")

    # 1. Solo las dos lineas de producto del caso
    df = df[df["PRODUCTLINE"].isin(LINEAS_DEL_CASO)]
    print(f"  tras filtrar Classic/Vintage Cars: {len(df)}")

    # 2. Fuera los pedidos cancelados
    cancelados = df["STATUS"].isin(ESTADOS_DESCARTADOS).sum()
    df = df[~df["STATUS"].isin(ESTADOS_DESCARTADOS)]
    print(f"  tras descartar {cancelados} pedidos cancelados: {len(df)}")

    # 3. Fechas y cantidades validas
    df["ORDERDATE"] = pd.to_datetime(
        df["ORDERDATE"], format="%m/%d/%Y %H:%M", errors="coerce"
    )
    antes = len(df)
    df = df[df["ORDERDATE"].notna() & (df["QUANTITYORDERED"] > 0)]
    if antes != len(df):
        print(f"  tras descartar fechas o cantidades invalidas: {len(df)}")

    # 4. Precio unitario reconstruido desde SALES
    topeados = int((df["PRICEEACH"] == 100).sum())
    df["PRECIO_UNITARIO"] = df["SALES"] / df["QUANTITYORDERED"]
    print(f"  lineas con PRICEEACH topeado en 100: {topeados} (precio recalculado)")

    df = df.sort_values(["ORDERDATE", "ORDERNUMBER", "ORDERLINENUMBER"])

    rutas.preparar(rutas.DATOS_LIMPIOS)
    df.to_csv(rutas.VENTAS_LIMPIAS, index=False, encoding="utf-8")

    print("\nResumen del dataset limpio")
    print(f"  lineas de pedido : {len(df)}")
    print(f"  periodo          : {df['ORDERDATE'].min():%Y-%m} a {df['ORDERDATE'].max():%Y-%m}")
    print(f"  unidades totales : {int(df['QUANTITYORDERED'].sum()):,}".replace(",", "."))
    print("\n  por linea de producto:")
    for linea, grupo in df.groupby("PRODUCTLINE"):
        unidades = int(grupo["QUANTITYORDERED"].sum())
        print(f"    {linea:<15} {len(grupo):>5} lineas   {unidades:>7,} unidades".replace(",", "."))
    print("\n  por estado conservado:")
    for estado, cuenta in df["STATUS"].value_counts().items():
        print(f"    {estado:<12} {cuenta:>5}")

    print(f"\n  [csv] {rutas.VENTAS_LIMPIAS.relative_to(rutas.RAIZ)}")


if __name__ == "__main__":
    main()
