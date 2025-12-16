<div align="center">

# 🚗 Proyecto de Investigación Operativa
## Análisis de Ventas y Gestión de Inventario - Vehículos Clásicos y Vintage

[![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)](https://python.org)
[![UTN](https://img.shields.io/badge/UTN-FRCU-green?style=for-the-badge)](https://www.frcu.utn.edu.ar/)
[![Status](https://img.shields.io/badge/Status-Completado-success?style=for-the-badge)]()
[![Prophet](https://img.shields.io/badge/Prophet-MAPE%2013.39%25-orange?style=for-the-badge)]()

![Cars](https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif)

*Trabajo Práctico Final - Ingeniería en Sistemas de Información*

</div>

---

## 📑 Tabla de Contenidos

1. [📋 Descripción del Proyecto](#-descripción-del-proyecto)
2. [🗂️ Estructura del Proyecto](#️-estructura-del-proyecto)
3. [🚀 Instalación y Configuración](#-instalación-y-configuración)
4. [▶️ Guía de Ejecución](#️-guía-de-ejecución)
5. [📊 Módulo 1: Análisis de Datos](#-módulo-1-análisis-de-datos)
6. [📈 Módulo 2: Modelos de Pronóstico](#-módulo-2-modelos-de-pronóstico)
7. [📦 Módulo 3: Políticas de Inventario](#-módulo-3-políticas-de-inventario)
8. [📉 Resultados Principales](#-resultados-principales)
9. [🛠️ Tecnologías Utilizadas](#️-tecnologías-utilizadas)
10. [📚 Referencias Bibliográficas](#-referencias-bibliográficas)

---

## 📋 Descripción del Proyecto

Este proyecto implementa un **sistema completo de gestión de inventario** para una empresa ficticia de vehículos clásicos y vintage, aplicando técnicas de Investigación Operativa:

### Objetivos
- ✅ **Análisis ABC/XYZ** de componentes por valor e importancia
- ✅ **Pronóstico de demanda** con 3 modelos comparados
- ✅ **Políticas de inventario EOQ** con validación estadística
- ✅ **EOQ Estacional** adaptado para demanda variable


### Dataset
- **Fuente**: Ventas históricas (29 meses)
- **Productos**: Classic Cars + Vintage Cars
- **Registros originales**: 2,823 pedidos
- **Registros filtrados**: 1,471 (solo Shipped + Classic/Vintage)

---

## 🗂️ Estructura del Proyecto

```
RepoProyectoIO/
│
├── 📂 data/                          # Datos de entrada/salida
│   ├── sales_data_sample_raw.csv     # Dataset ORIGINAL (sin filtrar)
│   ├── sales_data_sample_clean.csv   # Dataset limpio (filtrado)
│   └── ventaspormes.csv              # Serie temporal agregada
│
├── 📂 src/                           # Código fuente
│   ├── 📂 preprocessing/             # Preprocesamiento
│   │   ├── 01_limpiar_dataset.py     # Filtrar datos válidos
│   │   └── 02_generar_ventas_mensuales.py
│   │
│   ├── 📂 analysis/                  # Análisis de clasificación
│   │   ├── ABC_analysis.py           # Análisis Pareto (80-20)
│   │   └── XYZ_analisis.py           # Análisis por variabilidad
│   │
│   ├── 📂 forecast/                  # Modelos de pronóstico
│   │   ├── winters_forecast.py       # Holt-Winters (MAPE 31.54%)
│   │   ├── prophet_forecast.py       # Prophet (MAPE 13.39%) ⭐
│   │   └── sarima_forecast.py        # SARIMA (MAPE 41.48%)
│   │
│   └── 📂 inventory/                 # Políticas de inventario
│       ├── eoq_politicas.py          # EOQ Clásico + validación CV
│       ├── eoq_estacional.py         # EOQ por temporadas ⭐
│       ├── analisis_cv_periodos.py   # Análisis de CV por períodos

│
├── 📂 outputs/                       # Resultados generados
│   ├── 📂 forecast/
│   │   ├── 📂 prophet/               # Outputs Prophet (csv, png)
│   │   ├── 📂 winters/               # Outputs Holt-Winters (csv, png)
│   │   └── 📂 sarima/                # Outputs SARIMA (csv, png)
│   ├── 📂 inventory/
│   │   ├── 📂 eoq_clasico/           # Resultados EOQ clásico
│   │   ├── 📂 eoq_estacional/        # Resultados EOQ estacional
│   │   ├── 📂 cv/                    # Análisis de coeficiente de variación
│   │   └── 📂 comparacion/           # Comparaciones y gráficos
│   └── 📂 analysis/
│       ├── 📂 abc_xyz/               # Resultados ABC/XYZ
│       └── 📂 componentes/           # Resultados demanda componentes
│
├── 📂 docs/                          # Documentación del TP
│   ├── TP Integrador IO.pdf
│   └── TP Integrador IO.docx
│
├── 📂 .venv/                         # Entorno virtual Python
├── README.md                         # Este archivo
└── requirements.txt                  # Dependencias (crear si no existe)
```

---

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.10+ (recomendado 3.13)
- pip (gestor de paquetes)

### Paso 1: Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd RepoProyectoIO
```

### Paso 2: Crear Entorno Virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
# Instalar dependencias principales
pip install pandas numpy matplotlib statsmodels scipy

# Instalar Prophet (puede requerir C++ Build Tools en Windows)
pip install prophet
```

> **Nota:** Si tienes problemas instalando Prophet en Windows, instala primero:
> - `pip install --upgrade pip setuptools wheel`
> - Instala [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
> - Luego ejecuta `pip install prophet`


**Dependencias principales:**
| Paquete | Versión | Uso |
|---------|---------|-----|
| pandas | ≥2.0 | Manipulación de datos |
| numpy | ≥1.24 | Operaciones numéricas |
| matplotlib | ≥3.7 | Visualización |
| statsmodels | ≥0.14 | Holt-Winters, SARIMA |
| prophet | ≥1.1 | Modelo Prophet |
| scipy | ≥1.10 | Estadísticas |

---

## ▶️ Guía de Ejecución

> **IMPORTANTE:** Antes de ejecutar los scripts, asegúrate de que todas las dependencias estén instaladas correctamente y que Prophet funcione ejecutando:
> ```bash
> python -c "from prophet import Prophet; print('Prophet instalado correctamente')"
> ```

### 🔴 IMPORTANTE: Orden de Ejecución

Los scripts deben ejecutarse en este orden específico:

```
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: Preprocesamiento                                   │
│  ├── 01_limpiar_dataset.py                                  │
│  └── 02_generar_ventas_mensuales.py                        │
├─────────────────────────────────────────────────────────────┤
│  PASO 2: Análisis (opcional)                                │
│  ├── ABC_analysis.py                                        │
│  └── XYZ_analisis.py                                        │
├─────────────────────────────────────────────────────────────┤
│  PASO 3: Pronósticos                                        │
│  ├── prophet_forecast.py   ← Ejecutar PRIMERO (requerido)  │
│  ├── winters_forecast.py                                    │
│  └── sarima_forecast.py                                     │
├─────────────────────────────────────────────────────────────┤
│  PASO 4: Políticas de Inventario                            │
│  ├── eoq_politicas.py      ← Requiere prophet_forecast     │
│  ├── eoq_estacional.py     ← RECOMENDADO                   │
│  └── silver_meal.py                                         │

└─────────────────────────────────────────────────────────────┘
```

### Ejecución Paso a Paso

```bash
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Preprocesamiento (ejecutar desde la raíz del proyecto)
python src/preprocessing/01_limpiar_dataset.py
python src/preprocessing/02_generar_ventas_mensuales.py

# 3. Análisis ABC/XYZ (opcional)
python src/analysis/ABC_analysis.py
python src/analysis/XYZ_analisis.py

# 4. Modelos de Pronóstico
python src/forecast/prophet_forecast.py    # ⭐ Ejecutar PRIMERO
python src/forecast/winters_forecast.py
python src/forecast/sarima_forecast.py

# 5. Políticas de Inventario
python src/inventory/eoq_politicas.py      # EOQ clásico (valida CV)
python src/inventory/eoq_estacional.py     # ⭐ EOQ estacional (RECOMENDADO)

```

### Script de Ejecución Completa (Windows PowerShell)
```powershell
# Guardar como run_all.ps1 y ejecutar con: .\run_all.ps1
.venv\Scripts\activate
python src/preprocessing/01_limpiar_dataset.py
python src/preprocessing/02_generar_ventas_mensuales.py
python src/forecast/prophet_forecast.py
python src/inventory/eoq_estacional.py
Write-Host "Ejecución completada!" -ForegroundColor Green
```

---

## 📊 Módulo 1: Análisis de Datos

### Análisis ABC (Pareto)
Clasifica componentes según su **valor monetario total**:

| Clase | % del Valor | Componentes |
|-------|-------------|-------------|
| **A** | 0-80% | Carrocería Artesanal, Motor V8, Motor Raro |
| **B** | 80-95% | Llantas Vintage, Carrocería Estándar |
| **C** | 95-100% | Inyección, Carburadores, Tapicería |

### Análisis XYZ (Variabilidad)
Clasifica componentes según **estabilidad de demanda** (CV):

| Clase | CV | Descripción |
|-------|-----|-------------|
| **X** | < 10% | Demanda estable, fácil de pronosticar |
| **Y** | 10-25% | Demanda variable, pronóstico moderado |
| **Z** | > 25% | Demanda errática, difícil de pronosticar |

---

## 📈 Módulo 2: Modelos de Pronóstico

Se implementaron **3 modelos** de pronóstico y se compararon por precisión (MAPE):

### Comparación de Modelos

| Modelo | MAPE | Ventajas | Desventajas |
|--------|------|----------|-------------|
| **Prophet** ⭐ | 13.39% | Mejor precisión, maneja estacionalidad automáticamente | Requiere más dependencias |
| **Holt-Winters** | 31.54% | Parámetros interpretables (α, β, γ) | Menos flexible |
| **SARIMA** | 41.48% | Intervalos de confianza robustos | Requiere más datos |

### 🏆 Modelo Recomendado: Prophet

```
Parámetros Prophet:
├── Tendencia: Lineal con changepoints
├── Estacionalidad: Anual (modo aditivo)
├── Intervalo de confianza: 95%
└── MAPE: 13.39%
```

**Pronóstico 12 meses (ejemplo):**
| Mes | Pronóstico | Límite Inferior | Límite Superior |
|-----|------------|-----------------|-----------------|
| Jun-2025 | $73,473 | $35,297 | $110,273 |
| Oct-2025 | $652,911 | $618,254 | $687,963 |
| Nov-2025 | $680,457 | $644,287 | $719,211 |

---

## 📦 Módulo 3: Políticas de Inventario

### Validación del CV (Coeficiente de Variabilidad)

> **Referencia**: Winston - *Investigación de Operaciones*, pág. 872-873  
> Método de Peterson y Silver (1998)

El modelo EOQ clásico es válido **solo si CV < 0.20**. En nuestro caso:

| Métrica | Valor | ¿Válido para EOQ? |
|---------|-------|-------------------|
| CV Anual | 0.4446 | ❌ No (≥ 0.20) |
| CV Temporada PICO (Oct-Nov) | 0.0919 | ✅ Sí (< 0.20) |
| CV Temporada NORMAL (resto) | 0.0716 | ✅ Sí (< 0.20) |

### Solución: EOQ Estacional

Al dividir el año en **2 estaciones** con CV < 0.20, el modelo EOQ se vuelve válido:

```
Estaciones definidas:
├── PICO: Octubre - Noviembre
│   └── CV = 0.0919 ✓
└── NORMAL: Enero-Septiembre, Diciembre
    └── CV = 0.0716 ✓
```

### Comparación de Políticas

| Política | Descripción | Costo Total Anual |
|----------|-------------|-------------------|
| **EOQ Clásico - Política A** | Optimización por costos | $164,059 |
| **EOQ Clásico - Política B** | Nivel servicio 95% | $263,001 |
| **EOQ Estacional - Política A** ⭐ | Por temporadas | $159,161 |
| **EOQ Estacional - Política B** | Por temporadas + servicio | $206,709 |

### 💰 Ahorro con EOQ Estacional

```
Política A:
  EOQ Clásico:    $164,059
  EOQ Estacional: $159,161
  Ahorro:         $4,898 (-2.99%)

Política B:
  EOQ Clásico:    $263,001
  EOQ Estacional: $206,709
  Ahorro:         $56,292 (-21.40%)
```


---

## 📉 Resultados Principales

### Resumen Ejecutivo

| Área | Métrica | Resultado |
|------|---------|-----------|
| **Pronóstico** | Mejor modelo | Prophet (MAPE 13.39%) |
| **Pronóstico** | Ventas anuales | ~$2.26M |
| **Inventario** | Política recomendada | EOQ Estacional |
| **Inventario** | Ahorro anual | $4,898 - $56,292 |
| **Inventario** | CV validado | < 0.20 por temporada |

### Patrón Estacional Detectado

```
Demanda mensual ($):
       J    F    M    A    M    J    J    A    S    O    N    D
     ─────────────────────────────────────────────────────────
      🔵   🔵   🔵   🔵   🔵   🔵   🟢   🟢   🟢   🔴   🔴   🟢
     Bajo                        Normal            PICO
     ~$90K                       ~$150K            ~$670K
```

---

## 🛠️ Tecnologías Utilizadas

### Técnicas de Investigación Operativa

1. **Análisis ABC**: Principio de Pareto (80-20)
2. **Análisis XYZ**: Coeficiente de variación estadístico
3. **EOQ (Economic Order Quantity)**: Modelo de Wilson
4. **Validación CV**: Método Peterson-Silver (Winston)

6. **Series Temporales**: Holt-Winters, Prophet, SARIMA

### Stack Tecnológico

| Herramienta | Versión | Uso |
|-------------|---------|-----|
| Python | 3.13 | Lenguaje principal |
| Pandas | 2.x | Manipulación de datos |
| NumPy | 1.x | Operaciones numéricas |
| Matplotlib | 3.x | Visualizaciones |
| Statsmodels | 0.14 | Holt-Winters, SARIMA |
| Prophet | 1.1 | Pronóstico avanzado |
| SciPy | 1.x | Estadísticas, Z-scores |

---

## 📚 Referencias Bibliográficas

1. **Winston, W.L.** - *Investigación de Operaciones: Aplicaciones y Algoritmos*
   - Capítulo 15: Modelos de inventario determinísticos
   - Páginas 872-873: Método CV de Peterson y Silver

2. **Peterson, R. & Silver, E.A.** (1998) - *Decision Systems for Inventory Management and Production Planning*

3. **Taylor, S.J. & Letham, B.** (2018) - *Forecasting at Scale* (Prophet)

4. **Hyndman, R.J. & Athanasopoulos, G.** - *Forecasting: Principles and Practice*

---

## 🤝 Contribuciones

Este proyecto fue desarrollado como Trabajo Práctico Final para **Investigación Operativa**.

### Equipo
- **Institución**: UTN - Facultad Regional Concepción del Uruguay
- **Carrera**: Ingeniería en Sistemas de Información
- **Año**: 2025

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
