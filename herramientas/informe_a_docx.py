"""Convierte docs/INFORME 2.0.md a .docx replicando el formato del informe original.

Sirve para entregar el informe en el formato que pide la catedra sin tener que
mantener dos versiones del texto: la fuente es siempre el Markdown, y el .docx
se regenera cuando hace falta.

    python herramientas/informe_a_docx.py     (o: make informe)

Requiere python-docx:  pip install python-docx


SOBRE EL FORMATO
----------------
Los estilos de abajo no son una eleccion estetica: se leyeron del archivo
docs/INFORME IO.docx, que es el informe original, y se replican tal cual para
que las dos entregas se vean iguales. El original se escribio en Google Docs,
asi que sale de sus valores por defecto:

  - Arial 11 pt, interlineado 1,15, texto alineado a la izquierda.
  - Titulo 26 pt sin negrita; Encabezado 1 de 20 pt sin negrita; Encabezado 2
    de 16 pt en negrita; Encabezado 3 de 14 pt en negrita y gris 434343.
  - Tablas con borde negro simple de 1 pt en todos los lados y divisiones
    internas, sin relleno de fondo ni bandas de color. La fila de encabezado
    solo se distingue por la negrita.
  - El unico color del documento es el azul 1155CC de los hipervinculos.
"""

import pathlib
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = pathlib.Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "docs" / "INFORME 2.0.md"
DESTINO = ORIGEN.with_suffix(".docx")

# --- Valores leidos del informe original ---------------------------------------

FUENTE = "Arial"
CUERPO_PT = 11
INTERLINEADO = 1.15
GRIS_TITULO3 = RGBColor(0x43, 0x43, 0x43)
AZUL_ENLACE = RGBColor(0x11, 0x55, 0xCC)
MARGEN_CM = 2.5

# nivel -> (tamanio en pt, negrita, color, espacio antes, espacio despues)
TITULOS = {
    1: (26, False, None, 0, 6),
    2: (20, False, None, 20, 6),
    3: (16, True, None, 18, 6),
    4: (14, True, GRIS_TITULO3, 16, 4),
}


def preparar_documento():
    doc = Document()

    for seccion in doc.sections:
        seccion.left_margin = Cm(MARGEN_CM)
        seccion.right_margin = Cm(MARGEN_CM)
        seccion.top_margin = Cm(MARGEN_CM)
        seccion.bottom_margin = Cm(MARGEN_CM)

    normal = doc.styles["Normal"]
    normal.font.name = FUENTE
    normal.font.size = Pt(CUERPO_PT)
    # La fuente hay que fijarla tambien para los alfabetos no latinos, si no
    # Word la reemplaza por su propia predeterminada.
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
    normal.element.rPr.rFonts.set(qn("w:cs"), FUENTE)

    formato = normal.paragraph_format
    formato.line_spacing = INTERLINEADO
    formato.space_after = Pt(8)
    formato.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return doc


def agregar_titulo(doc, texto, nivel):
    """Titulos con el mismo aspecto que los del informe original.

    Se arma sobre un parrafo comun en vez de usar los estilos Heading de Word,
    porque esos vienen con el azul de la plantilla y habria que desarmarlos.
    """
    tamanio, negrita, color, antes, despues = TITULOS.get(nivel, TITULOS[4])
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(antes)
    p.paragraph_format.space_after = Pt(despues)
    p.paragraph_format.keep_with_next = True
    corrida = p.add_run(texto)
    corrida.font.name = FUENTE
    corrida.font.size = Pt(tamanio)
    corrida.bold = negrita
    if color is not None:
        corrida.font.color.rgb = color
    return p


def bordes_negros(tabla):
    """Borde negro simple de 1 pt en todo el contorno y las divisiones."""
    propiedades = tabla._tbl.tblPr
    bordes = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:val"), "single")
        elemento.set(qn("w:sz"), "8")        # octavos de punto: 8 = 1 pt
        elemento.set(qn("w:space"), "0")
        elemento.set(qn("w:color"), "000000")
        bordes.append(elemento)
    propiedades.append(bordes)


def texto_con_formato(parrafo, texto, tamanio=None):
    """Interpreta **negrita**, *cursiva*, `codigo` y enlaces de Markdown."""
    for parte in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`|https?://\S+)", texto):
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**"):
            corrida = parrafo.add_run(parte[2:-2])
            corrida.bold = True
        elif parte.startswith("*") and parte.endswith("*"):
            corrida = parrafo.add_run(parte[1:-1])
            corrida.italic = True
        elif parte.startswith("`") and parte.endswith("`"):
            corrida = parrafo.add_run(parte[1:-1])
            corrida.font.name = "Consolas"
        elif parte.startswith("http"):
            corrida = parrafo.add_run(parte)
            corrida.font.color.rgb = AZUL_ENLACE
            corrida.underline = True
        else:
            corrida = parrafo.add_run(parte)
        if corrida.font.name is None:
            corrida.font.name = FUENTE
        corrida.font.size = Pt(tamanio or CUERPO_PT)


def celdas(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def convertir():
    doc = preparar_documento()
    lineas = ORIGEN.read_text(encoding="utf-8").split("\n")
    i = 0
    buffer_parrafo = []

    def volcar_parrafo():
        nonlocal buffer_parrafo
        if buffer_parrafo:
            texto = " ".join(buffer_parrafo).strip()
            if texto:
                texto_con_formato(doc.add_paragraph(), texto)
            buffer_parrafo = []

    while i < len(lineas):
        linea = lineas[i]

        # Separador horizontal: no se dibuja, solo cierra el parrafo
        if linea.strip() == "---":
            volcar_parrafo()
            i += 1
            continue

        # Titulos
        if linea.startswith("#"):
            volcar_parrafo()
            nivel = len(linea) - len(linea.lstrip("#"))
            agregar_titulo(doc, linea.lstrip("#").strip(), nivel)
            i += 1
            continue

        # Bloque de codigo o de formulas
        if linea.startswith("```"):
            volcar_parrafo()
            i += 1
            cuerpo = []
            while i < len(lineas) and not lineas[i].startswith("```"):
                cuerpo.append(lineas[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            p.paragraph_format.line_spacing = 1.0
            corrida = p.add_run("\n".join(cuerpo))
            corrida.font.name = "Consolas"
            corrida.font.size = Pt(9.5)
            continue

        # Tabla: se detecta por la fila de guiones debajo del encabezado
        if linea.strip().startswith("|") and i + 1 < len(lineas) and \
                re.match(r"^\|[\s:\-\|]+\|$", lineas[i + 1].strip()):
            volcar_parrafo()
            encabezado = celdas(linea)
            i += 2
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(celdas(lineas[i]))
                i += 1

            tabla = doc.add_table(rows=1, cols=len(encabezado))
            bordes_negros(tabla)

            for celda, titulo in zip(tabla.rows[0].cells, encabezado):
                celda.text = ""
                p = celda.paragraphs[0]
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.0
                corrida = p.add_run(titulo)
                corrida.bold = True
                corrida.font.name = FUENTE
                corrida.font.size = Pt(10)

            for fila in filas:
                celdas_fila = tabla.add_row().cells
                for celda, valor in zip(celdas_fila, fila):
                    celda.text = ""
                    p = celda.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.0
                    texto_con_formato(p, valor, tamanio=10)
            doc.add_paragraph()
            continue

        # Cita destacada: en el original no hay recuadros de color, asi que se
        # resuelve con sangria y cursiva
        if linea.startswith(">"):
            volcar_parrafo()
            cuerpo = []
            while i < len(lineas) and lineas[i].startswith(">"):
                cuerpo.append(lineas[i].lstrip(">").strip())
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            texto_con_formato(p, " ".join(cuerpo))
            for corrida in p.runs:
                corrida.italic = True
            continue

        # Vinieta
        if re.match(r"^\s*[-*] ", linea):
            volcar_parrafo()
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = INTERLINEADO
            texto_con_formato(p, re.sub(r"^\s*[-*] ", "", linea))
            i += 1
            continue

        # Linea en blanco: cierra el parrafo en curso
        if not linea.strip():
            volcar_parrafo()
            i += 1
            continue

        buffer_parrafo.append(linea.strip())
        i += 1

    volcar_parrafo()
    doc.save(DESTINO)
    return doc


if __name__ == "__main__":
    documento = convertir()
    print(f"generado: {DESTINO.relative_to(RAIZ)}")
    print(f"  parrafos: {len(documento.paragraphs)}   tablas: {len(documento.tables)}")
    print(f"  formato: {FUENTE} {CUERPO_PT} pt, interlineado {INTERLINEADO}, "
          f"tablas con borde negro simple")
