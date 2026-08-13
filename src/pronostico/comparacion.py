"""Etapa 3 - Pronostico de demanda: ajuste, validacion, seleccion y desagregado.

Este es el unico script de la etapa. Ajusta los tres modelos, los valida fuera
de muestra, elige uno y baja el resultado a demanda por componente, que es lo
que consume la etapa de inventario.

Por que se elige con validacion y no con el MAPE del ajuste
-----------------------------------------------------------
El MAPE del ajuste mide cuanto se le parece el modelo a los datos con los que se
entreno. Eso premia al modelo con mas parametros, aunque prediga peor. Con esta
serie la diferencia no es teorica: Prophet ajusta con 14,7% de MAPE y es el peor
de los tres prediciendo, porque reparte 22 puntos de cambio de tendencia y 20
coeficientes de estacionalidad sobre 29 observaciones. Holt-Winters ajusta peor
y predice mejor, porque al quedarle los tres parametros de suavizado en cero no
tiene con que seguir el ruido: es el mas rigido de los tres. (Cero en los tres
pesos no significa pronostico plano; la inicializacion deja una tendencia lineal
fija mas una estacionalidad fija. La cuenta esta en holt_winters.py.)

La tabla de metricas reporta las dos cosas, ajuste y validacion, justamente para
que la diferencia quede a la vista. La seleccion usa la validacion. Lleva ademas
una fila de diagnostico, Prophet regulado, que no compite: ver correr_modelos().

Que se lleva la etapa siguiente
-------------------------------
  - la demanda promedio anual total (suma de los 12 meses pronosticados), y
  - el desvio estandar del error de pronostico a nivel de periodo.

El segundo punto merece una aclaracion. El desvio que interesa para dimensionar
el stock de seguridad es el del ERROR del pronostico, no el de la serie
historica ni el de los valores pronosticados. Mide cuanto se equivoca el modelo
mes a mes, que es exactamente la incertidumbre contra la que hay que cubrirse.
Se calcula sobre los residuos del ajuste (real - ajustado).

Sobre ese desvio queda una salvedad honesta: los residuos del ajuste subestiman
el error real, porque el modelo ya vio esos meses. El RMSE de la validacion, que
si es fuera de muestra, da mas alto. Se usa igual el del ajuste porque la
validacion tiene solo cinco puntos y un desvio estimado con cinco datos es muy
inestable; el de validacion queda reportado en la tabla de metricas para que el
lector pueda ver la brecha.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import parametros, rutas
from src.pronostico import comun, holt_winters, prophet_modelo, sarima

# Los tres modelos a comparar. La clave se usa como sufijo de columna en los
# CSV, asi que se mantiene corta y sin espacios.
MODELOS = {
    "HoltWinters": holt_winters,
    "Prophet": prophet_modelo,
    "SARIMA": sarima,
}

COLORES = {"HoltWinters": "tab:blue", "Prophet": "tab:green", "SARIMA": "tab:red"}


# ------------------------------------------------------- ajuste y validacion --

def _medir(clave, nombre_modelo, ajustar, serie, rol):
    """Ajusta, valida y arma la fila de metricas de un modelo."""
    resultado = ajustar(serie)
    fila = {"Modelo": clave, "Nombre": resultado.nombre, "Rol": rol}
    fila.update(comun.metricas(serie.values, resultado.ajustado))
    fila.update(comun.validar(ajustar, serie))
    fila["Total_Pronosticado"] = float(resultado.pronostico.sum())
    fila["Detalle"] = resultado.detalle
    return resultado, fila


def correr_modelos(serie):
    """Ajusta y valida los modelos. Devuelve resultados y tabla de metricas.

    La tabla lleva una columna Rol. Las filas "comparacion" son las tres
    candidatas entre las que se elige; la fila "diagnostico" es Prophet con la
    flexibilidad regulada y NO participa de la seleccion. Esta ahi porque sin
    ella la comparacion queda contra un rival mal configurado: los defaults de
    Prophet estan pensados para series largas, y sobre 29 observaciones el 47%
    de MAPE de validacion dice mas de esos defaults que del modelo. Ver
    prophet_modelo.regulado().
    """
    resultados, filas = {}, []

    for clave, modulo in MODELOS.items():
        print(f"  ajustando {clave} ...")
        resultado, fila = _medir(clave, clave, modulo.ajustar, serie, "comparacion")
        resultados[clave] = resultado
        filas.append(fila)

    print("  ajustando Prophet regulado (diagnostico) ...")
    _, fila = _medir("Prophet_regulado", "Prophet regulado",
                     prophet_modelo.regulado, serie, "diagnostico")
    filas.append(fila)

    columnas = ["Modelo", "Nombre", "Rol", "MAE", "RMSE", "MAPE",
                "Desvio_Residuos", "MAPE_Validacion", "RMSE_Validacion",
                "Origenes", "Total_Pronosticado", "Detalle"]
    # Ordenada por el criterio de seleccion, pero con las filas de comparacion
    # primero: asi la primera fila sigue siendo el modelo elegido.
    metricas = (pd.DataFrame(filas)[columnas]
                .sort_values(["Rol", "MAPE_Validacion"],
                             key=lambda c: c.map({"comparacion": 0, "diagnostico": 1})
                             if c.name == "Rol" else c)
                .reset_index(drop=True))
    return resultados, metricas


# --------------------------------------------------------------- desagregado --

def proporciones_historicas(serie):
    """Reparto Clasicos / Vintage segun las unidades realmente vendidas.

    El pronostico se hace sobre el total agregado, que es la serie con mejor
    senal. Para bajarlo a cada linea de vehiculo se usa la proporcion historica,
    tal como pide el enunciado ("las proporciones historicas de venta
    desagregada"). Se calcula sobre todo el historico y no sobre el ultimo mes
    para que no la mueva el ruido de un periodo puntual.
    """
    clasicos = serie["Unidades_Clasicos"].sum()
    vintage = serie["Unidades_Vintage"].sum()
    total = clasicos + vintage
    return clasicos / total, vintage / total


def demanda_por_componente(demanda_anual, desvio_mensual, p_clasico, p_vintage):
    """Traduce el pronostico agregado a demanda y riesgo de cada componente.

    Dos pasos:

    1. Del total a cada vehiculo, con la proporcion historica.
       El desvio del error se reparte con la misma proporcion: si el modelo se
       equivoca en N unidades de vehiculo, esas N se reparten entre las dos
       lineas igual que la demanda.

    2. De cada vehiculo a cada componente, con el ratio de uso del enunciado.
       Un componente que se monta 4 veces por auto (llantas, cubiertas)
       multiplica por 4 tanto la demanda como el desvio.

    El paso de mensual a semanal divide el desvio por la raiz de la cantidad de
    semanas del mes. Vale si los errores semanales son independientes entre si:
    la varianza de la suma es la suma de las varianzas, asi que el desvio
    mensual es raiz(4,33) veces el semanal.
    """
    filas = []
    for _, comp in parametros.COMPONENTES.iterrows():
        # Demanda anual del componente
        anual = parametros.demanda_componente(
            demanda_anual * p_clasico, demanda_anual * p_vintage, comp
        )
        # Desvio del error de pronostico, mismo camino de agregacion
        desvio_mes = parametros.demanda_componente(
            desvio_mensual * p_clasico, desvio_mensual * p_vintage, comp
        )
        desvio_semana = desvio_mes / parametros.SEMANAS_POR_MES ** 0.5

        filas.append(
            {
                "Componente": comp["Componente"],
                "Auto_Foco": comp["Auto_Foco"],
                "Demanda_Anual": anual,
                "Demanda_Semanal": anual / parametros.SEMANAS_POR_ANIO,
                "Sigma_Error_Mensual": desvio_mes,
                "Sigma_Error_Semanal": desvio_semana,
                "Lead_Time_Semanas": comp["Lead_Time_Semanas"],
                # Desvio de la demanda durante el plazo de entrega.
                # Winston, ecuacion (8): sigma_X = sigma_D * raiz(L)
                "sigma_X": desvio_semana * comp["Lead_Time_Semanas"] ** 0.5,
                "Costo_Unitario": comp["Costo_Unitario"],
                "Volumen_m3": comp["Volumen_m3"],
            }
        )
    return pd.DataFrame(filas)


# -------------------------------------------------------------------- tablas --

def tabla_ajuste(serie, resultados):
    """Un solo CSV con el ajuste de los tres modelos sobre el historico."""
    tabla = pd.DataFrame({"Periodo": serie.index, "Unidades_Reales": serie.values})
    for clave, resultado in resultados.items():
        ajustado = np.asarray(resultado.ajustado, dtype=float)
        tabla[f"Ajuste_{clave}"] = ajustado
        tabla[f"Residuo_{clave}"] = serie.values - ajustado
    return tabla


def tabla_pronostico(resultados, elegido, inferior, superior):
    """Un solo CSV con los 12 meses de los tres modelos y la banda del elegido."""
    tabla = pd.DataFrame({"Periodo": resultados[elegido].pronostico.index})
    for clave, resultado in resultados.items():
        tabla[f"Pronostico_{clave}"] = resultado.pronostico.values
    tabla["Limite_Inferior"] = inferior.values
    tabla["Limite_Superior"] = superior.values
    return tabla


# ------------------------------------------------------------------ graficos --

def graficar_comparacion(metricas, resultados, serie):
    """Los tres pronosticos superpuestos y el contraste ajuste / validacion."""
    fig, (izq, der) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel izquierdo: el historico y hacia donde va cada modelo
    izq.plot(serie.index, serie.values, color="black", marker="o",
             linewidth=1.5, label="Historico")
    for clave, resultado in resultados.items():
        izq.plot(resultado.pronostico.index, resultado.pronostico.values,
                 marker="s", linestyle="--", color=COLORES[clave], label=clave)
    izq.axvline(serie.index[-1], color="gray", linestyle=":")
    izq.set_ylabel("Unidades / mes")
    izq.set_title("Pronostico de los tres modelos")
    izq.legend()
    izq.grid(alpha=0.3)
    # Una marca cada tres meses; con una por mes las etiquetas se pisan entre si.
    # El xlim se fija al rango de los datos para que no aparezca una marca previa
    # al primer mes de la serie.
    ultimo = max(r.pronostico.index[-1] for r in resultados.values())
    izq.set_xlim(serie.index[0], ultimo)
    izq.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    izq.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    izq.tick_params(axis="x", rotation=45)

    # Panel derecho: el ajuste enfrentado a la validacion. Es el grafico que
    # justifica el criterio de seleccion, porque el orden se da vuelta.
    posicion = np.arange(len(metricas))
    ancho = 0.38
    der.bar(posicion - ancho / 2, metricas["MAPE"], ancho,
            color="lightsteelblue", edgecolor="gray", label="Ajuste (en muestra)")
    der.bar(posicion + ancho / 2, metricas["MAPE_Validacion"], ancho,
            color="firebrick", label="Validacion (fuera de muestra)")
    der.set_xticks(posicion)
    der.set_xticklabels(metricas["Modelo"])
    der.set_ylabel("MAPE (%)")
    der.set_title("Error de ajuste contra error de prediccion")
    # Espacio de sobra arriba para que la leyenda no tape la barra mas alta.
    der.set_ylim(0, metricas[["MAPE", "MAPE_Validacion"]].max().max() * 1.3)
    der.legend(loc="upper left")
    der.grid(axis="y", alpha=0.3)
    for x, ajuste, validacion in zip(posicion, metricas["MAPE"],
                                     metricas["MAPE_Validacion"]):
        der.text(x - ancho / 2, ajuste + 1, f"{ajuste:.1f}", ha="center", fontsize=9)
        der.text(x + ancho / 2, validacion + 1, f"{validacion:.1f}", ha="center",
                 fontsize=9)

    fig.tight_layout()
    rutas.guardar_figura(fig, rutas.PRONOSTICO / "modelos_comparacion.png")
    plt.close(fig)


# ---------------------------------------------------------------------- main --

def main():
    rutas.titulo("ETAPA 3 - PRONOSTICO DE DEMANDA")

    serie = comun.cargar_serie()
    print(f"Serie: {len(serie)} meses "
          f"({serie.index[0]:%Y-%m} a {serie.index[-1]:%Y-%m})")
    print(f"Ciclos estacionales completos disponibles: {len(serie) / 12:.1f}\n")

    adf = sarima.estacionariedad(serie)
    print("Test de Dickey-Fuller aumentado (previo a SARIMA):")
    print(f"  estadistico {adf['estadistico']:.4f} | p-valor {adf['p_valor']:.4f} "
          f"| critico 5% {adf['critico_5']:.4f}")
    print("  se rechaza la raiz unitaria: la serie es estacionaria al 5%\n"
          if adf["estacionaria"] else
          "  no se rechaza la raiz unitaria: conviene diferenciar (d=1)\n")

    resultados, metricas = correr_modelos(serie)

    print(f"\nComparacion de los tres modelos "
          f"(validacion: {int(metricas['Origenes'].iloc[0])} origenes, 1 paso adelante):\n")
    print(metricas[["Nombre", "MAE", "RMSE", "MAPE", "MAPE_Validacion",
                    "Desvio_Residuos", "Total_Pronosticado"]].to_string(
        index=False,
        formatters={"MAE": "{:,.1f}".format,
                    "RMSE": "{:,.1f}".format,
                    "MAPE": "{:.2f}".format,
                    "MAPE_Validacion": "{:.2f}".format,
                    "Desvio_Residuos": "{:,.1f}".format,
                    "Total_Pronosticado": "{:,.0f}".format}))

    for _, fila in metricas.iterrows():
        print(f"  {fila['Modelo']:<12} {fila['Detalle']}")

    # La seleccion mira solo las filas de comparacion: Prophet regulado esta en
    # la tabla como diagnostico y no compite.
    candidatos = metricas[metricas["Rol"] == "comparacion"].reset_index(drop=True)
    ganador = candidatos.iloc[0]
    elegido = ganador["Modelo"]
    print(f"\nModelo seleccionado: {ganador['Nombre']} "
          f"(MAPE de validacion {ganador['MAPE_Validacion']:.2f}%)")

    diagnostico = metricas[metricas["Rol"] == "diagnostico"]
    for _, fila in diagnostico.iterrows():
        print(f"  Diagnostico - {fila['Nombre']}: MAPE de validacion "
              f"{fila['MAPE_Validacion']:.2f}% contra {ganador['MAPE_Validacion']:.2f}% "
              f"del elegido. Los defaults de Prophet, no Prophet, son lo que"
              f" fallaba.")

    if ganador["MAPE"] != candidatos["MAPE"].min():
        mejor_ajuste = candidatos.loc[candidatos["MAPE"].idxmin()]
        print(f"  No es el de mejor ajuste: ese es {mejor_ajuste['Modelo']} "
              f"(MAPE {mejor_ajuste['MAPE']:.2f}%), que sin embargo predice peor "
              f"({mejor_ajuste['MAPE_Validacion']:.2f}%).")

    # Parametros que viajan a la etapa de inventario
    pronostico = resultados[elegido].pronostico
    demanda_anual = float(pronostico.sum())
    desvio_mensual = float(ganador["Desvio_Residuos"])
    desvio_semanal = desvio_mensual / parametros.SEMANAS_POR_MES ** 0.5

    serie_desagregada = pd.read_csv(rutas.SERIE_MENSUAL, parse_dates=["Periodo"])
    p_clasico, p_vintage = proporciones_historicas(serie_desagregada)

    print("\nParametros que se llevan a los modelos de inventario:")
    print(f"  Demanda anual total pronosticada  {demanda_anual:,.0f} unidades"
          .replace(",", "."))
    print(f"  Desvio del error de pronostico    {desvio_mensual:,.1f} unidades/mes"
          .replace(",", "."))
    print(f"  equivalente semanal               {desvio_semanal:,.1f} unidades/semana"
          .replace(",", "."))
    print(f"  Proporcion historica Clasicos     {p_clasico:.2%}")
    print(f"  Proporcion historica Vintage      {p_vintage:.2%}")

    componentes = demanda_por_componente(
        demanda_anual, desvio_mensual, p_clasico, p_vintage
    )
    print("\nDemanda y riesgo por componente:")
    print(componentes[["Componente", "Demanda_Anual", "Sigma_Error_Semanal",
                       "Lead_Time_Semanas", "sigma_X"]].to_string(
        index=False,
        formatters={"Demanda_Anual": "{:,.0f}".format,
                    "Sigma_Error_Semanal": "{:,.2f}".format,
                    "sigma_X": "{:,.2f}".format}))

    # --- Salidas ---
    print()
    rutas.preparar(rutas.PRONOSTICO)
    inferior, superior = comun.banda(pronostico, desvio_mensual)

    rutas.guardar_tabla(metricas, rutas.PRONOSTICO / "modelos_metricas.csv")
    rutas.guardar_tabla(tabla_ajuste(serie, resultados),
                        rutas.PRONOSTICO / "modelos_ajuste.csv")
    rutas.guardar_tabla(tabla_pronostico(resultados, elegido, inferior, superior),
                        rutas.PRONOSTICO / "modelos_pronostico.csv")
    rutas.guardar_tabla(componentes, rutas.PRONOSTICO / "demanda_componentes.csv")
    rutas.guardar_tabla(pd.DataFrame([{
        "Modelo": elegido,
        "Nombre": ganador["Nombre"],
        "MAPE_Validacion": ganador["MAPE_Validacion"],
        "Demanda_Anual_Total": demanda_anual,
        "Sigma_Error_Mensual": desvio_mensual,
        "Sigma_Error_Semanal": desvio_semanal,
        # El desvio fuera de muestra viaja junto al del ajuste porque la etapa 6b
        # lo necesita para el escenario de sensibilidad al riesgo: el del ajuste
        # subestima el error real y conviene medir cuanto cambia todo con el otro.
        "RMSE_Validacion": float(ganador["RMSE_Validacion"]),
        "Proporcion_Clasicos": p_clasico,
        "Proporcion_Vintage": p_vintage,
    }]), rutas.PRONOSTICO / "resumen_pronostico.csv")

    graficar_comparacion(metricas, resultados, serie)
    comun.graficar_modelo(
        rutas.PRONOSTICO / "pronostico_elegido.png",
        f"{ganador['Nombre']} - modelo seleccionado",
        serie, resultados[elegido].ajustado, pronostico, inferior, superior,
    )


if __name__ == "__main__":
    main()
