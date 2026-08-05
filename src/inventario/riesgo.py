"""Etapa 4a - Parametros de riesgo de cada componente.

Junta, para cada uno de los once componentes, los cuatro numeros que necesitan los
modelos de inventario:

  E(D)     demanda anual esperada, del pronostico
  h        costo de conservar una unidad un anio = 20% del costo unitario
  c_B      costo por unidad de deficit
  E(X)     demanda media durante el plazo de entrega
  sigma_X  desvio de la demanda durante el plazo de entrega

Se usa la notacion del capitulo 16 de Winston.

Los dos primeros salen directo del enunciado y de la etapa anterior. Los dos
ultimos son los que el enunciado pide "calcular y justificar", asi que van
explicados en detalle.


COSTO POR UNIDAD DE DEFICIT (c_B)
---------------------------------
El enunciado define la compensacion como "un descuento del 5% sobre el precio
del auto al cliente por la demora". Falta el dato del precio de venta: la tabla
de componentes da costos, no precios.

Lo que si se puede calcular con los datos del enunciado es el costo de los
materiales de cada vehiculo, sumando los componentes que lleva por su ratio de
uso:

    Clasico  = 9.000 + 6.500 + 3.500 + 1.200 + 4.000 + 4x400 + 4x250 = 26.800
    Vintage  = 12.000 + 15.000 + 3.500 + 900 + 4.000 + 4x2.500 + 4x250 = 46.400

Como ningun fabricante vende por debajo del costo de materiales, ese numero es
una cota inferior del precio. Usarlo hace que el c_B resultante tambien sea
cota inferior: el costo real de quedarse sin stock es al menos este, y
probablemente mas alto. La eleccion es deliberadamente conservadora, porque
subestimar c_B lleva a stocks de seguridad mas chicos, que es el lado
"incomodo" del error. El analisis de sensibilidad de +-30% cubre justamente
cuanto cambia la decision si el precio real fuera mas alto.

Para los componentes que se montan en los dos vehiculos, c_B se pondera por la
proporcion historica de ventas de cada linea.


DESVIO DURANTE EL PLAZO DE ENTREGA (sigma_X)
--------------------------------------------
Winston, ecuacion (8), pag. 891:  E(X) = L*E(D)  y  sigma_X = sigma_D*raiz(L),
donde D es la demanda por unidad de tiempo y L el plazo de entrega medido en
esas mismas unidades. Se arma en tres pasos:

  1. sigma del error de pronostico mensual (residuos del modelo ganador),
  2. dividido por raiz(4,33) para pasarlo a semanal,
  3. multiplicado por raiz(L) para acumularlo sobre las L semanas del plazo.

El paso 3 supone que los errores de semanas distintas son independientes, que
es el supuesto explicito de Winston al deducir (8).

Vale la pena remarcar que se usa el desvio del ERROR de pronostico y no el de
la demanda historica: el stock de seguridad cubre lo que el pronostico no logra
anticipar, no la estacionalidad, que ya esta dentro del pronostico y por lo
tanto ya esta contemplada en E(X).
"""

import pandas as pd

from src import parametros, rutas


def costo_deficit_por_vehiculo():
    """c_B para cada tipo de vehiculo: 5% del costo de materiales."""
    materiales = parametros.costo_materiales_por_vehiculo()
    return {
        auto: parametros.DESCUENTO_POR_DEMORA * costo
        for auto, costo in materiales.items()
    }


def costo_deficit_por_componente(auto_foco, c_B_vehiculo, p_clasico, p_vintage):
    """c_B del componente segun en que vehiculo se monta.

    Si va en los dos, el faltante frena indistintamente la produccion de un
    Clasico o de un Vintage, asi que se pondera por la mezcla de ventas.
    """
    if auto_foco == "Clásico":
        return c_B_vehiculo["Clásico"]
    if auto_foco == "Vintage":
        return c_B_vehiculo["Vintage"]
    return p_clasico * c_B_vehiculo["Clásico"] + p_vintage * c_B_vehiculo["Vintage"]


def construir():
    """Tabla de parametros de riesgo de todo el catalogo."""
    ruta_demanda = rutas.exigir(
        rutas.PRONOSTICO / "demanda_componentes.csv", "pronostico"
    )
    ruta_resumen = rutas.exigir(
        rutas.PRONOSTICO / "resumen_pronostico.csv", "pronostico"
    )
    ruta_abc = rutas.exigir(rutas.CLASIFICACION / "abc.csv", "clasificacion")

    demanda = pd.read_csv(ruta_demanda)
    resumen = pd.read_csv(ruta_resumen).iloc[0]
    abc = pd.read_csv(ruta_abc)

    # Se calculan los parametros de los once componentes, no solo de los de
    # clase A. Los modelos de inventario se aplican y se comparan sobre la
    # clase A, que es donde el enunciado pide enfocar, pero el almacen tiene
    # que guardar todo el catalogo: para dimensionarlo hacen falta los once.
    # La columna Clase_ABC permite filtrar despues segun para que se use.
    tabla = demanda.merge(abc[["Componente", "Clase_ABC"]], on="Componente")

    c_B_vehiculo = costo_deficit_por_vehiculo()
    p_clasico = float(resumen["Proporcion_Clasicos"])
    p_vintage = float(resumen["Proporcion_Vintage"])

    tabla["h_Anual"] = tabla["Costo_Unitario"] * parametros.TASA_MANTENIMIENTO
    tabla["c_B_Deficit"] = tabla["Auto_Foco"].apply(
        lambda auto: costo_deficit_por_componente(
            auto, c_B_vehiculo, p_clasico, p_vintage
        )
    )
    # E(X): demanda media durante el plazo de entrega. Es el centro alrededor
    # del cual se fija el punto de reabastecimiento.
    tabla["E_X"] = tabla["Demanda_Semanal"] * tabla["Lead_Time_Semanas"]

    columnas = [
        "Componente", "Auto_Foco", "Clase_ABC", "Demanda_Anual", "Costo_Unitario",
        "h_Anual", "c_B_Deficit", "Lead_Time_Semanas", "E_X", "sigma_X",
        "Volumen_m3",
    ]
    return tabla[columnas].reset_index(drop=True), c_B_vehiculo, (p_clasico, p_vintage)


def main():
    rutas.titulo("ETAPA 4a - PARAMETROS DE RIESGO POR COMPONENTE")

    tabla, c_B_vehiculo, (p_clasico, p_vintage) = construir()
    materiales = parametros.costo_materiales_por_vehiculo()

    print("Costo por unidad de deficit (c_B), del 5% de compensacion al cliente:\n")
    print(f"  {'vehiculo':<10} {'costo materiales':>18} {'c_B = 5%':>12}")
    for auto in ("Clásico", "Vintage"):
        print(f"  {auto:<10} {materiales[auto]:>18,.0f} {c_B_vehiculo[auto]:>12,.0f}"
              .replace(",", "."))
    mezcla = p_clasico * c_B_vehiculo["Clásico"] + p_vintage * c_B_vehiculo["Vintage"]
    print(f"  {'Ambos':<10} {'ponderado':>18} {mezcla:>12,.0f}".replace(",", "."))
    print(f"\n  ponderacion: {p_clasico:.2%} Clasicos / {p_vintage:.2%} Vintage")
    print("  el costo de materiales es cota inferior del precio de venta, asi que")
    print("  el c_B obtenido es conservador (el real no puede ser menor)")

    print("\nParametros por componente:\n")
    print(tabla.to_string(index=False,
                          formatters={"Demanda_Anual": "{:,.0f}".format,
                                      "Costo_Unitario": "{:,.0f}".format,
                                      "h_Anual": "{:,.0f}".format,
                                      "c_B_Deficit": "{:,.0f}".format,
                                      "E_X": "{:,.1f}".format,
                                      "sigma_X": "{:,.2f}".format}))

    print("\nLectura rapida: h es lo que cuesta conservar una unidad un anio y c_B")
    print("lo que cuesta que falte una unidad. Su relacion gobierna el punto de")
    print("reabastecimiento por la ecuacion (13) de Winston:")
    for _, fila in tabla.iterrows():
        ratio = fila["c_B_Deficit"] / fila["h_Anual"]
        print(f"  {fila['Componente']:<36} c_B/h = {ratio:>5.2f}")

    rutas.preparar(rutas.INVENTARIO)
    rutas.guardar_tabla(tabla, rutas.INVENTARIO / "parametros_riesgo.csv")


if __name__ == "__main__":
    main()
