# Makefile del TP Integrador de Investigacion Operativa
#
# Uso basico:
#     make            muestra esta ayuda
#     make todo       corre el proyecto completo, de punta a punta
#
# Cada etapa se puede correr sola, pero necesita que las anteriores ya hayan
# corrido (usan los CSV que dejan). Si falta algo, el script avisa cual es el
# make que hay que ejecutar antes.
#
# Si tu Python no se llama "python", pasalo por linea de comandos:
#     make todo PYTHON=py
#     make todo PYTHON=.venv/Scripts/python.exe

PYTHON ?= python
EJECUTAR = $(PYTHON) -m

.DEFAULT_GOAL := help


# ---------------------------------------------------------------- ayuda ------

help:
	@echo ""
	@echo "  TP Integrador - Investigacion Operativa"
	@echo "  ======================================"
	@echo ""
	@echo "  Todo junto"
	@echo "    make todo               corre el pipeline completo"
	@echo "    make limpiar-salidas    borra outputs/ y data/processed/"
	@echo ""
	@echo "  Por etapa"
	@echo "    make datos              limpia el dataset y arma la serie mensual"
	@echo "    make clasificacion      analisis ABC y XYZ"
	@echo "    make pronostico         los tres modelos y su comparacion"
	@echo "    make inventario         politicas A y B"
	@echo "    make almacen            capacidad minima requerida"
	@echo "    make sensibilidad       los dos analisis de sensibilidad"
	@echo ""
	@echo "  Scripts sueltos"
	@echo "    make datos-limpiar          make pronostico-holt-winters"
	@echo "    make datos-serie            make pronostico-prophet"
	@echo "    make clasificacion-abc      make pronostico-sarima"
	@echo "    make clasificacion-xyz      make pronostico-comparacion"
	@echo "    make inventario-riesgo      make sensibilidad-agotamiento"
	@echo "    make inventario-politicas   make sensibilidad-riesgo"
	@echo ""
	@echo "  Informe"
	@echo "    make informe            regenera docs/INFORME 2.0.docx desde el .md"
	@echo ""
	@echo "  Instalacion"
	@echo "    make instalar           instala las dependencias de requirements.txt"
	@echo ""


instalar:
	$(PYTHON) -m pip install -r requirements.txt


informe:
	$(PYTHON) herramientas/informe_a_docx.py


# --------------------------------------------------------------- etapas ------

# 1. Preparacion de datos
datos-limpiar:
	$(EJECUTAR) src.datos.limpiar

datos-serie:
	$(EJECUTAR) src.datos.serie_mensual

datos: datos-limpiar datos-serie


# 2. Clasificacion de componentes
clasificacion-abc:
	$(EJECUTAR) src.clasificacion.abc

clasificacion-xyz:
	$(EJECUTAR) src.clasificacion.xyz

clasificacion: clasificacion-abc clasificacion-xyz


# 3. Pronostico de demanda
pronostico-holt-winters:
	$(EJECUTAR) src.pronostico.holt_winters

pronostico-prophet:
	$(EJECUTAR) src.pronostico.prophet_modelo

pronostico-sarima:
	$(EJECUTAR) src.pronostico.sarima

pronostico-comparacion:
	$(EJECUTAR) src.pronostico.comparacion

pronostico: pronostico-holt-winters pronostico-prophet pronostico-sarima pronostico-comparacion


# 4. Modelos de inventario
inventario-riesgo:
	$(EJECUTAR) src.inventario.riesgo

inventario-politicas:
	$(EJECUTAR) src.inventario.politicas

inventario: inventario-riesgo inventario-politicas


# 5. Dimensionamiento del almacen
almacen:
	$(EJECUTAR) src.almacen.capacidad


# 6. Analisis de sensibilidad
sensibilidad-agotamiento:
	$(EJECUTAR) src.sensibilidad.costo_agotamiento

sensibilidad-riesgo:
	$(EJECUTAR) src.sensibilidad.riesgo_demanda

sensibilidad: sensibilidad-agotamiento sensibilidad-riesgo


# ----------------------------------------------------------- pipeline --------

todo: datos clasificacion pronostico inventario almacen sensibilidad
	@echo ""
	@echo "  Listo. Los resultados quedaron en outputs/"
	@echo ""


limpiar-salidas:
	$(PYTHON) -c "import shutil; shutil.rmtree('outputs', ignore_errors=True); shutil.rmtree('data/processed', ignore_errors=True); print('outputs/ y data/processed/ borrados')"


.PHONY: help instalar informe todo limpiar-salidas \
        datos datos-limpiar datos-serie \
        clasificacion clasificacion-abc clasificacion-xyz \
        pronostico pronostico-holt-winters pronostico-prophet pronostico-sarima pronostico-comparacion \
        inventario inventario-riesgo inventario-politicas \
        almacen \
        sensibilidad sensibilidad-agotamiento sensibilidad-riesgo
