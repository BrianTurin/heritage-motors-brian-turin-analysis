# Proyecto Final - Investigación Operativa

**Universidad Tecnológica Nacional - Facultad Regional Concepción del Uruguay**  
**Ingeniería en Sistemas de Información - 4to Año**  
**Materia:** Investigación Operativa

## 👥 Equipo de Desarrollo

- **Matias Bochatay**
- **Brian Turin**
- **Juan Brun**

---

## 📋 Descripción del Proyecto

Este proyecto implementa un sistema completo de **gestión de inventarios y pronóstico de demanda** para una empresa automotriz especializada en la fabricación de vehículos clásicos y vintage. El sistema analiza datos históricos de ventas y componentes para optimizar la planificación de recursos mediante técnicas de Investigación Operativa.

### 📄 Documentación Completa

La definición del TP Integrador está disponible en:
- **[TP Integrador Investigación Operativa.docx](./TP%20Integrador%20Investigaci%C3%B3n%20Operativa.docx)**

Este documento contiene:
- Marco teórico y fundamentos de Investigación Operativa
- Metodología de análisis ABC-XYZ aplicada
- Desarrollo matemático del modelo Holt-Winters
- Análisis de resultados y conclusiones
- Recomendaciones para la gestión de inventarios

### 🎯 Objetivos

1. **Análisis de Inventario ABC-XYZ**: Clasificación de componentes según valor económico y variabilidad de demanda
2. **Pronóstico de Ventas**: Predicción de demanda futura usando modelos de suavización exponencial (Holt-Winters)
3. **Análisis de Demanda de Componentes**: Cálculo de necesidades de insumos basado en pronósticos de producción
4. **Visualización de Datos**: Generación de gráficos y reportes para toma de decisiones

---

## 🗂️ Estructura del Proyecto

```
RepoProyectoIO/
│
├── TP Integrador Investigación Operativa.docx
│                                        # Informe técnico completo del proyecto
│
├── TPFinal IO/                          # Datos y procesamiento inicial
│   ├── sales_data_sample_clean.csv     # Dataset limpio (solo Shipped, Classic/Vintage Cars)
│   ├── dataset IO.py                    # Script de limpieza de datos
│   └── notebook.ipynb                   # Análisis exploratorio
│
├── Analisis/                            # Análisis de clasificación de inventario
│   ├── ABC_analysis.py                  # Clasificación ABC por valor económico
│   └── XYZ_analisis.py                  # Clasificación XYZ por variabilidad
│
├── ForecastModels/                      # Modelos de pronóstico
│   └── Holt-Winters/
│       ├── winters_forecast.py          # Modelo Holt-Winters completo
│       ├── winters_forecast.png         # Gráficos del análisis
│       ├── winters_results.csv          # Resultados históricos
│       └── winters_forecast.csv         # Pronósticos futuros (12 meses)
│
├── Estimacion/                          # Scripts de estimación auxiliares
│   ├── MetodoWinters.py                 # Implementación alternativa Winters
│   ├── graficasDemandas.py             # Visualizaciones de demanda
│   └── ventas_estimadas.csv            # Resultados de estimaciones
│
├── DemandaComponentes.py                # Análisis de demanda de insumos
├── VentasPorMes.py                      # Agregación mensual de ventas
├── ventaspormes.csv                     # Serie temporal mensual
├── requirements_winters.txt             # Dependencias del proyecto
└── README.md                            # Este archivo
```

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements_winters.txt
```

### Dependencias Principales

- **pandas** (≥2.0.0): Manipulación y análisis de datos
- **numpy** (≥1.24.0): Cálculos numéricos
- **matplotlib** (≥3.7.0): Visualización de datos
- **statsmodels** (≥0.14.0): Modelos estadísticos y series temporales

---

## 📊 Módulos del Sistema

### 1. Preparación de Datos

**`TPFinal IO/dataset IO.py`**
- Limpia el dataset original
- Filtra registros por STATUS = 'Shipped'
- Mantiene solo productos: Classic Cars y Vintage Cars
- Genera: `sales_data_sample_clean.csv`

**`VentasPorMes.py`**
- Agrega ventas por mes y tipo de producto
- Crea serie temporal de 29 periodos
- Genera: `ventaspormes.csv`

```bash
python VentasPorMes.py
```

### 2. Análisis ABC-XYZ

#### Análisis ABC (Valor Económico)

**`Analisis/ABC_analysis.py`**

Clasifica componentes según su valor total en inventario:
- **Clase A**: 80% del valor acumulado (componentes críticos)
- **Clase B**: 15% del valor (componentes importantes)
- **Clase C**: 5% del valor (componentes de bajo impacto)

**Catálogo de Componentes:**
- Motor de Alto Rendimiento V8
- Motor de Cilindros en Línea Raro
- Carrocería Artesanal de Época
- Transmisión de 5 Velocidades
- Tapicería de Cuero Premium
- Llantas y Neumáticos especializados
- *(11 componentes en total)*

```bash
python Analisis/ABC_analysis.py
```

#### Análisis XYZ (Variabilidad de Demanda)

**`Analisis/XYZ_analisis.py`**

Clasifica componentes según coeficiente de variación (CV):
- **Clase X**: CV ≤ 10% (demanda muy predecible)
- **Clase Y**: 10% < CV ≤ 25% (demanda moderadamente variable)
- **Clase Z**: CV > 25% (demanda altamente variable)

```bash
python Analisis/XYZ_analisis.py
```

### 3. Pronóstico de Demanda

#### Modelo Holt-Winters (Triple Suavización Exponencial)

**`ForecastModels/Holt-Winters/winters_forecast.py`**

**Características del modelo:**
- **Componentes**: Nivel + Tendencia + Estacionalidad
- **Tipo**: Aditivo (cambios constantes)
- **Periodicidad**: 12 meses (ciclo anual)
- **Horizonte**: 12 meses futuros
- **Optimización**: Parámetros α, β, γ optimizados automáticamente

**Parámetros del modelo:**
- **α (alpha)**: Suavización del nivel
- **β (beta)**: Suavización de la tendencia
- **γ (gamma)**: Suavización de la estacionalidad

**Métricas de Evaluación:**
- MAE (Error Absoluto Medio)
- RMSE (Raíz del Error Cuadrático Medio)
- MAPE (Error Porcentual Absoluto Medio)

**Salidas generadas:**
- `winters_forecast.png`: 4 gráficos de análisis
  1. Serie temporal histórica vs pronóstico
  2. Componente de tendencia
  3. Componente estacional
  4. Residuos del modelo
- `winters_results.csv`: Valores históricos, ajustados y residuos
- `winters_forecast.csv`: Pronósticos mensuales (12 periodos)

```bash
python ForecastModels\Holt-Winters\winters_forecast.py
```

**Interpretación de Resultados:**

El modelo identificó en los datos analizados:
- **Nivel base**: ~$150K mensuales
- **Tendencia**: Constante (sin crecimiento acelerado)
- **Estacionalidad**: Fuerte patrón cíclico (picos en noviembre: ~$670K)
- **Precisión (MAPE)**: ~31% (aceptable para serie corta de 29 meses)

### 4. Análisis de Demanda de Componentes

**`DemandaComponentes.py`**

Calcula las necesidades de insumos basándose en:
- Ventas históricas por tipo de vehículo
- Catálogo de componentes y su aplicabilidad
- Uso por vehículo de cada componente

**Visualizaciones:**
- Gráfico de demanda mensual para componentes Vintage Cars
- Gráfico de demanda mensual para componentes Classic Cars

```bash
python DemandaComponentes.py
```

---

## 📈 Flujo de Trabajo Recomendado

```
1. Limpieza de Datos
   └─> python TPFinal IO/dataset IO.py

2. Generación de Serie Temporal
   └─> python VentasPorMes.py

3. Análisis de Inventario (paralelo)
   ├─> python Analisis/ABC_analysis.py
   └─> python Analisis/XYZ_analisis.py

4. Pronóstico de Ventas
   └─> python ForecastModels/Holt-Winters/winters_forecast.py

5. Cálculo de Demanda de Componentes
   └─> python DemandaComponentes.py
```

---

## 📊 Resultados Clave

### Datos del Dataset
- **Periodo analizado**: 2003-01 a 2005-05 (29 meses)
- **Productos**: Classic Cars y Vintage Cars
- **Total ventas históricas**: ~$5.4M
- **Ventas pronosticadas (12 meses)**: ~$2.8M

### Componentes Más Relevantes (ABC)
Los análisis identificaron que componentes como:
- Carrocería Artesanal de Época
- Motores especializados (V8 y Cilindros en Línea)
- Tapicería Premium

Representan la mayor inversión en inventario (Clase A).

### Patrón Estacional Detectado
- **Meses de alta demanda**: Octubre-Noviembre (picos de ~$670K)
- **Meses de baja demanda**: Enero-Junio (~$90K-$180K)
- **Promedio mensual**: $188K

---

## 🛠️ Tecnologías y Metodologías

### Técnicas de Investigación Operativa Aplicadas

1. **Análisis ABC**: Principio de Pareto (80-20)
2. **Análisis XYZ**: Coeficiente de variación estadístico
3. **Suavización Exponencial**: Modelo Holt-Winters triple
4. **Series Temporales**: Descomposición en tendencia, estacionalidad y ruido

### Herramientas
- **Python 3.13**: Lenguaje de programación
- **Pandas**: Manipulación de datos tabulares
- **NumPy**: Operaciones numéricas eficientes
- **Matplotlib**: Generación de gráficos profesionales
- **Statsmodels**: Modelos estadísticos avanzados

---

## 📝 Formato de Datos

### Dataset Principal (`sales_data_sample_clean.csv`)

```csv
ORDERNUMBER,QUANTITYORDERED,PRICEEACH,ORDERLINENUMBER,SALES,ORDERDATE,STATUS,QTR_ID,MONTH_ID,YEAR_ID,PRODUCTLINE,MSRP,PRODUCTCODE,CUSTOMERNAME,PHONE,ADDRESSLINE1,ADDRESSLINE2,CITY,STATE,POSTALCODE,COUNTRY,TERRITORY,CONTACTLASTNAME,CONTACTFIRSTNAME,DEALSIZE
```

**Campos clave:**
- `ORDERDATE`: Fecha de la orden (formato: MM/DD/YYYY HH:MM)
- `QUANTITYORDERED`: Cantidad de vehículos pedidos
- `SALES`: Monto total de la venta
- `PRODUCTLINE`: Tipo de producto (Classic Cars / Vintage Cars)
- `STATUS`: Estado del pedido (filtrado a 'Shipped' únicamente)

### Archivos de Salida

**`ventaspormes.csv`**: Serie temporal agregada
```csv
Mes,Classic Cars,Vintage Cars
1,10,16
2,3,8
...
```

**`winters_forecast.csv`**: Pronósticos mensuales
```csv
Periodo,Pronostico
2005-06-01,87761.58
2005-07-01,178767.12
...
```

---

## 🤝 Contribuciones

Este proyecto fue desarrollado como trabajo final para la materia Investigación Operativa. 

### Responsabilidades del Equipo
- **Análisis de datos y limpieza**: Dataset IO, exploración inicial
- **Modelos de clasificación**: Implementación ABC-XYZ
- **Modelos de pronóstico**: Holt-Winters, validación estadística
- **Visualización y reportes**: Gráficos, documentación, presentación

---

## 📄 Licencia

Este proyecto es de uso académico para la Universidad Tecnológica Nacional - FRCU.

---

## 📧 Contacto

Para consultas sobre el proyecto:
- **Institución**: UTN - Facultad Regional Concepción del Uruguay
- **Carrera**: Ingeniería en Sistemas de Información
- **Año**: 2025

---

**Fecha de última actualización**: Diciembre 2025, martes 2
