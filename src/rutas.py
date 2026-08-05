"""Rutas del proyecto y utilidades de entrada/salida.

Centraliza donde se leen y escriben los archivos para que ningun script tenga
que construir rutas relativas a mano.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

DATOS_CRUDOS = RAIZ / "data" / "raw"
DATOS_LIMPIOS = RAIZ / "data" / "processed"
SALIDAS = RAIZ / "outputs"

VENTAS_CRUDAS = DATOS_CRUDOS / "sales_data_sample.csv"
VENTAS_LIMPIAS = DATOS_LIMPIOS / "ventas_limpias.csv"
SERIE_MENSUAL = DATOS_LIMPIOS / "serie_mensual.csv"

CLASIFICACION = SALIDAS / "clasificacion"
PRONOSTICO = SALIDAS / "pronostico"
INVENTARIO = SALIDAS / "inventario"
ALMACEN = SALIDAS / "almacen"
SENSIBILIDAD = SALIDAS / "sensibilidad"


def preparar(*carpetas):
    """Crea las carpetas de salida si no existen."""
    for carpeta in carpetas:
        carpeta.mkdir(parents=True, exist_ok=True)


def exigir(ruta, comando_sugerido):
    """Corta con un mensaje claro si falta un archivo intermedio."""
    if not Path(ruta).exists():
        raise SystemExit(
            f"Falta el archivo {ruta}.\nGeneralo con:  make {comando_sugerido}"
        )
    return Path(ruta)


def guardar_tabla(df, ruta, decimales=4):
    """Escribe un CSV redondeando las columnas numericas."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.round(decimales).to_csv(ruta, index=False, encoding="utf-8")
    print(f"  [csv] {ruta.relative_to(RAIZ)}")


def guardar_figura(fig, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    print(f"  [png] {ruta.relative_to(RAIZ)}")


def titulo(texto):
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


def usar_utf8():
    """La consola de Windows no siempre viene en UTF-8 y rompe los acentos."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


usar_utf8()
