"""Datos del enunciado y constantes del modelo.

Todo lo que sale del documento del TP vive aca. Ningun otro modulo define
costos, lead times ni volumenes por su cuenta: se importan de este archivo.
"""

import pandas as pd

# --- Parametros de gestion (enunciado, seccion "Contexto del Caso") ---

COSTO_ORDENAR = 300.0          # K: costo fijo por orden de compra (USD)
TASA_MANTENIMIENTO = 0.20      # c1 anual como fraccion del costo unitario
DESCUENTO_POR_DEMORA = 0.05    # compensacion al cliente si no hay stock

# --- Nivel de servicio de la Politica B ---

ALPHA = 0.05                   # el enunciado fija alfa = 0.05
NIVEL_SERVICIO = 1 - ALPHA     # 0.95

# --- Conversiones de tiempo ---

SEMANAS_POR_ANIO = 52.0
MESES_POR_ANIO = 12.0
SEMANAS_POR_MES = SEMANAS_POR_ANIO / MESES_POR_ANIO   # 4.333...

# --- Lineas de producto del dataset que representan a cada vehiculo ---

LINEA_CLASICO = "Classic Cars"
LINEA_VINTAGE = "Vintage Cars"

# --- Catalogo de componentes criticos (tabla del enunciado) ---

COMPONENTES = pd.DataFrame(
    [
        # componente,                             auto,       costo,  uso, vol,  lead time
        ("Motor de Alto Rendimiento V8",          "Clásico",   9000,   1,   0.80,  6),
        ("Motor de Cilindros en Línea Raro",      "Vintage",  12000,   1,   0.90, 12),
        ("Carrocería Artesanal de Época",         "Vintage",  15000,   1,   4.00, 10),
        ("Carrocería Estándar (Fibra)",           "Clásico",   6500,   1,   3.50,  4),
        ("Transmisión de 5 Velocidades",          "Ambos",     3500,   1,   0.40,  4),
        ("Sistema de Inyección Electrónica",      "Clásico",   1200,   1,   0.10,  3),
        ("Set de Carburadores Dobles",            "Vintage",    900,   1,   0.10,  5),
        ("Tapicería de Cuero Premium",            "Ambos",     4000,   1,   0.50,  8),
        ("Juego de Llantas Vintage Espec.",       "Vintage",   2500,   4,   0.15,  5),
        ("Llantas Regulares Cromados",            "Clásico",    400,   4,   0.10,  2),
        ("Cubiertas de Alta Gama (Neumáticos)",   "Ambos",      250,   4,   0.10,  2),
    ],
    columns=[
        "Componente",
        "Auto_Foco",
        "Costo_Unitario",
        "Uso_por_Auto",
        "Volumen_m3",
        "Lead_Time_Semanas",
    ],
)


# Nombres abreviados para los ejes de los graficos. Los nombres completos no
# entran y truncarlos a lo bruto corta las palabras por la mitad.
NOMBRE_CORTO = {
    "Motor de Alto Rendimiento V8": "Motor V8",
    "Motor de Cilindros en Línea Raro": "Motor Raro",
    "Carrocería Artesanal de Época": "Carr. Artesanal",
    "Carrocería Estándar (Fibra)": "Carr. Estándar",
    "Transmisión de 5 Velocidades": "Transmisión",
    "Sistema de Inyección Electrónica": "Inyección",
    "Set de Carburadores Dobles": "Carburadores",
    "Tapicería de Cuero Premium": "Tapicería",
    "Juego de Llantas Vintage Espec.": "Llantas Vintage",
    "Llantas Regulares Cromados": "Llantas Cromadas",
    "Cubiertas de Alta Gama (Neumáticos)": "Cubiertas",
}


def abreviar(nombres):
    """Traduce nombres de componente a su version corta para graficar."""
    return [NOMBRE_CORTO.get(n, n) for n in nombres]


def costo_materiales_por_vehiculo():
    """Costo de los componentes que lleva cada tipo de vehiculo.

    Se usa como cota inferior del precio de venta para justificar el costo de
    agotamiento (ver src/inventario/riesgo.py): el precio al cliente no puede
    ser menor que el costo de los materiales que lo componen.
    """
    costos = {}
    for auto in ("Clásico", "Vintage"):
        aplica = COMPONENTES["Auto_Foco"].isin([auto, "Ambos"])
        sub = COMPONENTES[aplica]
        costos[auto] = float((sub["Costo_Unitario"] * sub["Uso_por_Auto"]).sum())
    return costos


def demanda_componente(unidades_clasico, unidades_vintage, fila):
    """Demanda de un componente dadas las unidades vendidas de cada vehiculo."""
    if fila["Auto_Foco"] == "Clásico":
        vehiculos = unidades_clasico
    elif fila["Auto_Foco"] == "Vintage":
        vehiculos = unidades_vintage
    else:
        vehiculos = unidades_clasico + unidades_vintage
    return vehiculos * fila["Uso_por_Auto"]
