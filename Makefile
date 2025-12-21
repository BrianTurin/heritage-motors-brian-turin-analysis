# Makefile para facilitar la ejecución de scripts del proyecto

PYTHON = C:/RepoProyectoIO/.venv/Scripts/python.exe
SRC = src

# --- Preprocesamiento ---
preprocesar-limpiar:
	$(PYTHON) $(SRC)/preprocessing/01_limpiar_dataset.py

preprocesar-ventas-mensuales:
	$(PYTHON) $(SRC)/preprocessing/02_generar_ventas_mensuales.py

# --- Pronóstico ---
pronostico-prophet:
	$(PYTHON) $(SRC)/forecast/prophet_forecast.py

pronostico-sarima:
	$(PYTHON) $(SRC)/forecast/sarima_forecast.py

pronostico-winters:
	$(PYTHON) $(SRC)/forecast/winters_forecast.py

# --- Análisis ---
analisis-abc:
	$(PYTHON) $(SRC)/analysis/ABC_analysis.py

analisis-xyz:
	$(PYTHON) $(SRC)/analysis/XYZ_analisis.py

analisis-componentes:
	$(PYTHON) $(SRC)/analysis/DemandaComponentes.py

# --- Inventario ---
inventario-eoq-estacional-costo:
	$(PYTHON) $(SRC)/inventory/eoq_estacional.py --modo costo

inventario-eoq-estacional-servicio:
	$(PYTHON) $(SRC)/inventory/eoq_estacional.py --modo servicio

inventario-cv-periodos:
	$(PYTHON) $(SRC)/inventory/analisis_cv_periodos.py

# --- Atajos útiles ---
preprocesar: preprocesar-limpiar preprocesar-ventas-mensuales

pronostico: pronostico-profeta pronostico-sarima pronostico-winters

analisis: analisis-abc analisis-xyz analisis-componentes

inventario: inventario-eoq-estacional-costo inventario-eoq-estacional-servicio inventario-cv-periodos

todo: preprocesar pronostico analisis inventario

.PHONY: preprocesar preprocesar-limpiar preprocesar-ventas-mensuales pronostico pronostico-profeta pronostico-sarima pronostico-winters analisis analisis-abc analisis-xyz analisis-componentes inventario inventario-eoq-estacional-costo inventario-eoq-estacional-servicio inventario-cv-periodos todo
