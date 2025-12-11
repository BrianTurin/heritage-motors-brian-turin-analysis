# Proyecto Final - Investigación Operativa

<div align="center">

![Operations Research](https://media.giphy.com/media/3o7btPCcdNniyf0ArS/giphy.gif)

*"Optimizando decisiones, un algoritmo a la vez"* 🎯

[![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.3-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Status](https://img.shields.io/badge/Status-En%20Proceso-yellow?style=for-the-badge)]()
[![UTN](https://img.shields.io/badge/UTN-FRCU-red?style=for-the-badge)]()

</div>

---

**Universidad Tecnológica Nacional - Facultad Regional Concepción del Uruguay**  
**Ingeniería en Sistemas de Información - 4to Año**  
**Materia:** Investigación Operativa

<div align="center">

| 📊 Pronósticos | 📈 Análisis | 🎓 Investigación |
|:---:|:---:|:---:|
| ![Forecast](https://media.giphy.com/media/l46Cy1rHbQ92uuLXa/giphy.gif) | ![Analysis](https://media.giphy.com/media/3oKIPEqDGUULpEU0aQ/giphy.gif) | ![Study](https://media.giphy.com/media/IPbS5R4fSUl5S/giphy.gif) |
| *Holt-Winters, Prophet, SARIMA* | *ABC-XYZ Classification* | *Café + Código = TP* |

</div>

---

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
│   ├── Holt-Winters/
│   │   ├── winters_forecast.py          # Modelo Holt-Winters completo
│   │   ├── winters_forecast.png         # Gráficos del análisis
│   │   ├── winters_results.csv          # Resultados históricos
│   │   └── winters_forecast.csv         # Pronósticos futuros (12 meses)
│   │
│   ├── Prophet/
│   │   ├── prophet_forecast.py          # Modelo Prophet (Facebook/Meta)
│   │   ├── prophet_forecast.png         # Gráficos del análisis
│   │   ├── prophet_components.png       # Componentes nativos de Prophet
│   │   ├── prophet_results.csv          # Resultados históricos
│   │   ├── prophet_forecast.csv         # Pronósticos con intervalos de confianza
│   │   └── requirements_prophet.txt     # Dependencias específicas de Prophet
│   │
│   └── SARIMA/
│       ├── sarima_forecast.py           # Modelo SARIMA completo
│       ├── sarima_forecast.png          # Gráficos del análisis
│       ├── sarima_diagnostics.png       # Diagnóstico del modelo (ACF, PACF, Q-Q)
│       ├── sarima_results.csv           # Resultados históricos
│       └── sarima_forecast.csv          # Pronósticos con intervalos de confianza
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
- Git (para clonar el repositorio)

### Instalación Rápida

```powershell
# 1. Clonar el repositorio
git clone https://github.com/JuanBrun/RepoProyectoIO.git
cd RepoProyectoIO

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements_winters.txt
pip install prophet
```

### Instalación Manual de Dependencias

```powershell
pip install pandas>=2.0.0 numpy>=1.24.0 matplotlib>=3.7.0 statsmodels>=0.14.0 prophet>=1.1.0
```

### Dependencias Principales

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| **pandas** | ≥2.0.0 | Manipulación y análisis de datos |
| **numpy** | ≥1.24.0 | Cálculos numéricos |
| **matplotlib** | ≥3.7.0 | Visualización de datos |
| **statsmodels** | ≥0.14.0 | Modelos estadísticos (Holt-Winters, SARIMA) |
| **prophet** | ≥1.1.0 | Modelo de pronóstico de Facebook/Meta |

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

#### Modelo Prophet (Facebook/Meta)

**`ForecastModels/Prophet/prophet_forecast.py`**

Prophet es un modelo de pronóstico desarrollado por Facebook/Meta, diseñado para series temporales con patrones estacionales fuertes y datos históricos de varios años.

**Características del modelo:**
- **Detección automática** de tendencia y estacionalidad
- **Manejo robusto** de datos faltantes y outliers
- **Intervalos de confianza** del 95% para cada pronóstico
- **Puntos de cambio**: Detecta automáticamente cambios en la tendencia

**Configuración utilizada:**
- **Estacionalidad anual**: Activada
- **Modo**: Aditivo
- **Intervalo de confianza**: 95%

**Métricas de Evaluación:**
- MAE (Error Absoluto Medio)
- RMSE (Raíz del Error Cuadrático Medio)
- MAPE (Error Porcentual Absoluto Medio)

**Salidas generadas:**
- `prophet_forecast.png`: 3 gráficos de análisis
  1. Serie temporal histórica vs pronóstico con intervalos de confianza
  2. Componente estacional
  3. Residuos del modelo
- `prophet_components.png`: Componentes nativos de Prophet (tendencia + estacionalidad)
- `prophet_results.csv`: Valores históricos, ajustados y residuos
- `prophet_forecast.csv`: Pronósticos con límites inferior y superior (12 periodos)

```bash
python ForecastModels\Prophet\prophet_forecast.py
```

**Interpretación de Resultados:**

El modelo Prophet identificó:
- **Puntos de cambio**: 22 cambios detectados en la tendencia
- **Tendencia**: Creciente
- **Estacionalidad**: Patrón anual claro con pico en noviembre (~$600K)
- **Precisión (MAPE)**: ~13% (mejor ajuste que Holt-Winters)

#### Modelo SARIMA (Seasonal ARIMA)

**`ForecastModels/SARIMA/sarima_forecast.py`**

SARIMA (Seasonal Autoregressive Integrated Moving Average) es un modelo estadístico clásico para series temporales que combina componentes autorregresivos, de media móvil y diferenciación, tanto regulares como estacionales.

**Modelo matemático:**
$$y_t = c + \phi_1 y_{t-1} + \theta_1 \varepsilon_{t-1} + \Phi_1 y_{t-12} + \Theta_1 \varepsilon_{t-12} + \varepsilon_t$$

**Configuración utilizada: SARIMA(1,1,1)(1,0,1)₁₂**

**Componentes no estacionales (p,d,q):**
- **p = 1**: 1 término autorregresivo (AR)
- **d = 1**: 1 diferenciación para estacionariedad
- **q = 1**: 1 término de media móvil (MA)

**Componentes estacionales (P,D,Q,s):**
- **P = 1**: 1 término AR estacional
- **D = 0**: Sin diferenciación estacional (para preservar datos en serie corta)
- **Q = 1**: 1 término MA estacional
- **s = 12**: Período estacional de 12 meses

**Parámetros estimados:**
- **φ₁ (AR1)**: Coeficiente autorregresivo no estacional
- **θ₁ (MA1)**: Coeficiente de media móvil no estacional
- **Φ₁ (SAR12)**: Coeficiente autorregresivo estacional
- **Θ₁ (SMA12)**: Coeficiente de media móvil estacional
- **σ²**: Varianza del error

**Métricas de Evaluación:**
- MAE (Error Absoluto Medio)
- RMSE (Raíz del Error Cuadrático Medio)
- MAPE (Error Porcentual Absoluto Medio)
- AIC/BIC (Criterios de información)

**Salidas generadas:**
- `sarima_forecast.png`: 3 gráficos de análisis
  1. Serie temporal histórica vs pronóstico con intervalos de confianza
  2. Residuos del modelo
  3. Distribución de residuos
- `sarima_diagnostics.png`: Diagnóstico del modelo
  1. ACF de residuos
  2. PACF de residuos
  3. Q-Q Plot
  4. Residuos estandarizados
- `sarima_results.csv`: Valores históricos, ajustados y residuos
- `sarima_forecast.csv`: Pronósticos con intervalos de confianza (12 periodos)

```bash
python ForecastModels\SARIMA\sarima_forecast.py
```

**Interpretación de Resultados:**

El modelo SARIMA identificó:
- **Test ADF**: Serie estacionaria (p-valor = 0.0009)
- **Componente AR estacional (Φ₁)**: ~0.56 (correlación positiva con mismo mes del año anterior)
- **Estacionalidad**: Capturada mediante componentes SAR y SMA
- **Precisión (MAPE)**: ~41% (menor precisión debido a la serie corta de 29 meses)

**Nota**: SARIMA requiere idealmente 3-5 ciclos estacionales completos (36-60 meses) para estimaciones óptimas. Con solo 29 meses disponibles, el modelo tiene limitaciones pero sigue siendo útil para comparación metodológica.

#### Comparación de Modelos

| Métrica | Holt-Winters | Prophet | SARIMA |
|---------|--------------|---------|--------|
| **MAPE** | 31,54% | **13,39%** ✅ | 41,48% |
| **MAE** | $36.298 | **$12.567** ✅ | $76.395 |
| **RMSE** | $55.808 | **$18.373** ✅ | $134.129 |
| **Total Pronóstico (12 meses)** | $2.776.620 | $2.417.382 | $2.421.953 |
| **Intervalos de Confianza** | No | Sí (95%) | Sí (95%) |
| **Criterios de Información** | No | No | Sí (AIC/BIC) |
| **Datos mínimos recomendados** | 24 meses | 12 meses | 36-60 meses |

**Conclusión**: Prophet muestra la mejor precisión en este dataset debido a su capacidad de detectar múltiples puntos de cambio en la tendencia y su robustez con series temporales cortas. Holt-Winters ofrece un balance entre simplicidad e interpretabilidad. SARIMA, aunque menos preciso con pocos datos, proporciona diagnósticos estadísticos rigurosos y es preferido cuando se dispone de series más largas.

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

4. Pronóstico de Ventas (elegir uno o varios)
   ├─> python ForecastModels/Holt-Winters/winters_forecast.py
   ├─> python ForecastModels/Prophet/prophet_forecast.py
   └─> python ForecastModels/SARIMA/sarima_forecast.py

5. Cálculo de Demanda de Componentes
   └─> python DemandaComponentes.py
```

---

## 🚶 Guía Paso a Paso de Ejecución

Esta sección detalla cómo ejecutar cada componente del proyecto en orden.

### Paso 0: Configuración Inicial (Solo la primera vez)

```powershell
# 1. Clonar el repositorio (si no lo tienes)
git clone https://github.com/JuanBrun/RepoProyectoIO.git
cd RepoProyectoIO

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 4. Instalar todas las dependencias
pip install pandas numpy matplotlib statsmodels prophet
```

### Paso 1: Preparación y Limpieza de Datos

**Objetivo**: Limpiar el dataset original y filtrar solo los datos relevantes.

```powershell
# Ejecutar script de limpieza
python "TPFinal IO/dataset IO.py"
```

**Resultado**: Genera `sales_data_sample_clean.csv` con solo:
- Órdenes con STATUS = 'Shipped'
- Productos: Classic Cars y Vintage Cars

### Paso 2: Generar Serie Temporal de Ventas

**Objetivo**: Agregar las ventas por mes para análisis temporal.

```powershell
python VentasPorMes.py
```

**Resultado**: 
- Genera `ventaspormes.csv`
- Muestra en consola las ventas por mes de cada tipo de vehículo

### Paso 3: Análisis ABC de Inventario

**Objetivo**: Clasificar componentes por valor económico (Principio de Pareto).

```powershell
python Analisis/ABC_analysis.py
```

**Resultado**: Muestra en consola:
- Tabla de componentes ordenados por valor total
- Clasificación ABC (A: 80%, B: 15%, C: 5%)
- Porcentaje acumulado de cada componente

### Paso 4: Análisis XYZ de Variabilidad

**Objetivo**: Clasificar componentes por variabilidad de demanda.

```powershell
python Analisis/XYZ_analisis.py
```

**Resultado**: Muestra en consola:
- Coeficiente de variación (CV) de cada componente
- Clasificación XYZ (X: ≤10%, Y: 10-25%, Z: >25%)
- Promedio mensual y desviación estándar

### Paso 5: Pronóstico con Holt-Winters

**Objetivo**: Predecir ventas futuras usando suavización exponencial triple.

```powershell
python ForecastModels/Holt-Winters/winters_forecast.py
```

**Resultado**:
- `winters_forecast.png` - Gráficos de análisis (4 paneles)
- `winters_forecast.csv` - Pronósticos para 12 meses
- `winters_results.csv` - Valores históricos y ajustados
- Métricas en consola: MAE, RMSE, MAPE

### Paso 6: Pronóstico con Prophet

**Objetivo**: Predecir ventas futuras con el modelo de Facebook/Meta.

```powershell
python ForecastModels/Prophet/prophet_forecast.py
```

**Resultado**:
- `prophet_forecast.png` - Gráficos de análisis (3 paneles)
- `prophet_components.png` - Descomposición de componentes
- `prophet_forecast.csv` - Pronósticos con intervalos de confianza
- `prophet_results.csv` - Valores históricos y ajustados
- Métricas en consola: MAE, RMSE, MAPE

### Paso 7: Pronóstico con SARIMA

**Objetivo**: Predecir ventas futuras con el modelo estadístico SARIMA.

```powershell
python ForecastModels/SARIMA/sarima_forecast.py
```

**Resultado**:
- `sarima_forecast.png` - Gráficos de análisis (3 paneles)
- `sarima_diagnostics.png` - Diagnóstico del modelo (ACF, PACF, Q-Q Plot)
- `sarima_forecast.csv` - Pronósticos con intervalos de confianza
- `sarima_results.csv` - Valores históricos y ajustados
- Métricas en consola: MAE, RMSE, MAPE, AIC, BIC

### Paso 8: Análisis de Demanda de Componentes

**Objetivo**: Visualizar la demanda mensual de cada componente.

```powershell
python DemandaComponentes.py
```

**Resultado**:
- Gráfico interactivo con demanda de componentes Vintage Cars
- Gráfico interactivo con demanda de componentes Classic Cars

### Ejecución Completa (Todos los pasos)

Para ejecutar todo el análisis de una vez:

```powershell
# Activar entorno virtual
.venv\Scripts\Activate.ps1

# Ejecutar en orden
python "TPFinal IO/dataset IO.py"
python VentasPorMes.py
python Analisis/ABC_analysis.py
python Analisis/XYZ_analisis.py
python ForecastModels/Holt-Winters/winters_forecast.py
python ForecastModels/Prophet/prophet_forecast.py
python ForecastModels/SARIMA/sarima_forecast.py
python DemandaComponentes.py
```

### Resumen de Archivos Generados

| Paso | Script | Archivos Generados |
|------|--------|-------------------|
| 1 | `dataset IO.py` | `sales_data_sample_clean.csv` |
| 2 | `VentasPorMes.py` | `ventaspormes.csv` |
| 3 | `ABC_analysis.py` | (salida en consola) |
| 4 | `XYZ_analisis.py` | (salida en consola) |
| 5 | `winters_forecast.py` | `winters_forecast.png`, `winters_forecast.csv`, `winters_results.csv` |
| 6 | `prophet_forecast.py` | `prophet_forecast.png`, `prophet_components.png`, `prophet_forecast.csv`, `prophet_results.csv` |
| 7 | `sarima_forecast.py` | `sarima_forecast.png`, `sarima_diagnostics.png`, `sarima_forecast.csv`, `sarima_results.csv` |
| 8 | `DemandaComponentes.py` | (gráficos interactivos) |

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
4. **Prophet**: Modelo aditivo generalizado de Facebook/Meta
5. **SARIMA**: Modelo autorregresivo integrado de media móvil estacional
6. **Series Temporales**: Descomposición en tendencia, estacionalidad y ruido

### Herramientas
- **Python 3.13**: Lenguaje de programación
- **Pandas**: Manipulación de datos tabulares
- **NumPy**: Operaciones numéricas eficientes
- **Matplotlib**: Generación de gráficos profesionales
- **Statsmodels**: Modelos estadísticos avanzados (Holt-Winters, SARIMA)
- **Prophet**: Modelo de pronóstico de Facebook/Meta
- **SciPy**: Análisis estadístico (Q-Q plots, tests)

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

**`winters_forecast.csv`**: Pronósticos mensuales (Holt-Winters)
```csv
Periodo,Pronostico
2005-06-01,87761.58
2005-07-01,178767.12
...
```

**`prophet_forecast.csv`**: Pronósticos con intervalos de confianza (Prophet)
```csv
Periodo,Pronostico,Limite_Inferior,Limite_Superior
2005-06-01,73473.11,35297.13,110273.02
2005-07-01,167937.13,132631.61,202040.02
...
```

**`sarima_forecast.csv`**: Pronósticos con intervalos de confianza (SARIMA)
```csv
Periodo,Pronostico,Limite_Inferior,Limite_Superior
2005-06-01,102517.48,-202830.74,407865.70
2005-07-01,196861.66,-109700.28,503423.59
...
```

---

## 🤝 Contribuciones

Este proyecto fue desarrollado como trabajo final para la materia Investigación Operativa. 

### Responsabilidades del Equipo
- **Análisis de datos y limpieza**: Dataset IO, exploración inicial
- **Modelos de clasificación**: Implementación ABC-XYZ
- **Modelos de pronóstico**: Holt-Winters, Prophet, SARIMA, validación estadística
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

**Fecha de última actualización**: Diciembre 2025

---

<div align="center">

## 🎓 ¡Gracias por visitar nuestro proyecto!

*"Al finalizar todo este trabajo..."*

| 🧠 Lo que aprendimos | 🧉 Mate consumido | 🐛 Bugs encontrados |
|:---:|:---:|:---:|
| Mucho | Demasiado | No queremos hablar de eso |

![ThankYou](https://media.giphy.com/media/3oz8xIsloV7zOmt81G/giphy.gif)

**¿Te gustó el proyecto? ¡Dale una ⭐ al repositorio!**

[![Made with Love](https://img.shields.io/badge/Made%20with-❤️%20y%20mate-red?style=for-the-badge)]()

---

*UTN FRCU - Ingeniería en Sistemas - 2025*

*"La optimización es el arte de hacer lo mejor posible con lo que se tiene... incluyendo las horas de sueño"* 😴

</div>
