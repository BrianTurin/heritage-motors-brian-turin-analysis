# TP Integrador de Investigación Operativa — Heritage Motors S.A.

Modelos de pronóstico de demanda y políticas probabilísticas de inventario para
definir el reaprovisionamiento de componentes críticos y dimensionar un nuevo
almacén central.

UTN FRCU — Ingeniería en Sistemas de Información.

---

## Qué hace el proyecto

El trabajo recorre seis etapas encadenadas. Cada una deja sus resultados en
`outputs/` y la siguiente los toma de ahí.

| Etapa | Qué resuelve |
|---|---|
| 1. Datos | Limpia el dataset de ventas y arma la serie mensual de vehículos |
| 2. Clasificación | ABC por valor de uso anual y XYZ por variabilidad |
| 3. Pronóstico | Holt-Winters, Prophet y SARIMA; se elige por error fuera de muestra |
| 4. Inventario | Política A (pedidos pendientes) y Política B (nivel de servicio 95%) |
| 5. Almacén | Capacidad mínima requerida por cada política |
| 6. Sensibilidad | Costo de agotamiento ±30% y riesgo de demanda +15% |

---

## Cómo correrlo

Requiere Python 3.10 o superior.

```bash
make instalar     # instala las dependencias
make todo         # corre el pipeline completo
```

`make` sin argumentos muestra la lista de comandos disponibles.

Si tu intérprete no se llama `python`, se pasa por parámetro:

```bash
make todo PYTHON=py
make todo PYTHON=.venv/Scripts/python.exe
```

Cada etapa se puede correr sola (`make pronostico`, `make inventario`, ...), y
casi todas también script por separado (`make clasificacion-abc`). Si falta un
archivo intermedio, el script avisa qué `make` hay que ejecutar antes.

Las salidas tienen nombre fijo, así que cada corrida pisa a la anterior y
`outputs/` siempre refleja la última ejecución. Dos corridas seguidas dan
archivos idénticos byte a byte: no hay nada aleatorio sin semilla en el pipeline.

Sin `make` instalado, los scripts se invocan como módulos desde la raíz:

```bash
python -m src.datos.limpiar
python -m src.inventario.politicas
```

---

## Estructura

```
├── data/
│   ├── raw/                    dataset original, no se modifica
│   └── processed/              datos limpios (los genera la etapa 1)
│
├── src/
│   ├── parametros.py           datos del enunciado: costos, volúmenes, lead times
│   ├── rutas.py                rutas del proyecto y utilidades de entrada/salida
│   │
│   ├── datos/                  1. limpieza y serie mensual
│   ├── clasificacion/          2. ABC y XYZ
│   ├── pronostico/             3. los tres modelos, su validación y comparación
│   │   ├── comun.py              serie, métricas, validación y gráficos
│   │   ├── holt_winters.py       un modelo por archivo, solo cálculo
│   │   ├── prophet_modelo.py
│   │   ├── sarima.py
│   │   └── comparacion.py        corre los tres, elige y escribe las salidas
│   ├── inventario/             4. modelos de inventario y aplicación
│   │   ├── modelos.py            matemática pura, sin lectura ni escritura
│   │   ├── riesgo.py             c_B y sigma_X de cada componente
│   │   └── politicas.py          aplica A y B, y las compara
│   ├── almacen/                5. capacidad mínima
│   └── sensibilidad/           6. los dos análisis de sensibilidad
│
├── outputs/                    resultados (CSV y PNG), se regeneran con make todo
│   ├── clasificacion/            abc_xyz.csv, abc_pareto.png
│   ├── pronostico/               modelos_metricas.csv, modelos_ajuste.csv,
│   │                             modelos_pronostico.csv, demanda_componentes.csv,
│   │                             resumen_pronostico.csv y los dos gráficos
│   ├── inventario/               parametros_riesgo.csv, politicas.csv, verificacion_eoq.csv
│   ├── almacen/                  capacidad por componente y dimensionamiento del galpón
│   └── sensibilidad/             c_B ±30% y σ +15%, cada uno con detalle y resumen
│
├── docs/
│   ├── ... - TP Integrador Investigación Operativa (2).pdf   el enunciado
│   └── ... - Trabajo Integrador IO v1.0.pdf                  el informe que se entrega
│
├── Makefile                    los comandos del pipeline
└── requirements.txt            dependencias
```

Dos decisiones de organización que conviene explicar:

- **Un solo lugar para los datos del enunciado.** Costos unitarios, ratios de
  uso, volúmenes y lead times viven únicamente en `src/parametros.py`. Ningún
  script los redefine por su cuenta.

- **La matemática separada de la aplicación.** `src/inventario/modelos.py` tiene
  las fórmulas y nada más: no lee archivos ni imprime. Eso permite verificar los
  modelos con valores conocidos, independientemente del pipeline.

  Los tres modelos de pronóstico siguen la misma idea: cada uno expone una sola
  función `ajustar(serie, horizonte)` que solo calcula, y `comparacion.py` se
  ocupa de los archivos y de la consola. Sin esa separación no se podría validar,
  porque la validación necesita reajustar cada modelo cinco veces en silencio.

---

## Decisiones metodológicas

**Se pronostican cantidades, no facturación.** Los modelos de inventario
necesitan cantidades de componentes, y cada vehículo consume una cantidad fija de
cada uno según la tabla del enunciado. Pasar por la facturación obligaría a
suponer un precio por vehículo que el enunciado no da.

**Una línea de pedido equivale a un vehículo.** El dataset de origen es de
maquetas a escala, que se venden a granel (35 unidades por línea en promedio). Un
cliente de Heritage Motors encarga *un* vehículo con una configuración, no 35
idénticos, así que la correspondencia natural es una línea por vehículo. La
elección no altera el patrón de demanda: la correlación mensual con la serie de
unidades es 0,997 y el pico de noviembre se conserva.

**Se descarta solo el estado `Cancelled`.** Los pedidos en proceso, en espera o
en disputa son demanda real: el cliente pidió la unidad. Filtrar únicamente por
`Shipped` recorta los últimos meses de la serie e introduce un valle artificial
en abril de 2005.

**`PRICEEACH` se recalcula.** Viene topeado en 100 en 781 de las 1.545 líneas
del caso, así que no coincide con `SALES / QUANTITYORDERED`. El precio unitario
se reconstruye desde `SALES`, que es el campo consistente.

**El modelo de pronóstico se elige por error fuera de muestra, no por ajuste.**
El MAPE del ajuste mide cuánto se parece el modelo a los datos con los que se
entrenó, y eso premia al que tiene más parámetros aunque prediga peor. Con esta
serie la diferencia es grande: Prophet es el que mejor ajusta (MAPE 14,70%) y el
que peor predice (47,39%), porque reparte 22 puntos de cambio de tendencia y 20
coeficientes de estacionalidad sobre 29 observaciones. La selección usa una
validación con origen móvil: se entrena con los primeros 24 meses, se predice el
mes siguiente y se corre el origen, cinco veces. Gana Holt-Winters con 32,20%,
porque con pesos de suavizado chicos (α = 0,035, β = 0,035, γ = 0,241) no tiene
con qué seguir el ruido: es el más rígido de los tres y con 29 observaciones la
rigidez es una ventaja.

**Holt-Winters se inicializa con la heurística estándar, no por optimización.**
Con `initialization_method="estimated"` statsmodels mete el nivel, la tendencia
y los doce índices iniciales en la misma optimización que α, β y γ, y con 29
observaciones el optimizador explica toda la serie con la inicialización y deja
los tres pesos exactamente en cero: un Holt-Winters que no actualiza nada. Con
la heurística de Hyndman (descomposición sobre los dos primeros ciclos y
regresión sobre la serie desestacionalizada) los valores iniciales quedan
fijos, los tres pesos salen positivos y la validación da prácticamente lo
mismo. El modelo pronostica 886 vehículos contra un promedio histórico
anualizado de 639.

**Prophet perdió por sus valores por defecto, no por ser Prophet.** Los defaults
están calibrados para series largas, y sobre 29 observaciones el 47% de
validación dice más de esos defaults que del modelo. Bajando el prior de los
puntos de cambio de 0,05 a 0,01 y su cantidad de 25 a 5, Prophet valida en
31,89%: empate técnico con el ganador. Esa corrida queda en la tabla de métricas
como fila `Prophet_regulado` con `Rol = diagnostico`, y no compite en la
selección. La elección de Holt-Winters se sostiene igual, por parsimonia y
auditabilidad: con 29 observaciones, un modelo con tres pesos es más fácil de
defender que uno con 45 parámetros regulados a mano.

**Los modelos de inventario trabajan en base anual.** E(D) es la suma de los
doce meses pronosticados, la tasa de demanda es E(D)/52 por semana y el punto de
reabastecimiento es el mismo todo el año. Como en ese esquema la estacionalidad
no está en E(X), el desvío que alimenta el stock de seguridad es el **desvío de
los doce meses pronosticados** (42,65 por mes, 20,49 por semana), que es donde
vive el pico de noviembre, y no el de los residuos del ajuste, que solo mide el
ruido alrededor del pronóstico. El stock de seguridad se va acumulando con la
tasa anual a lo largo del año y queda disponible para la estación de mayor
consumo. El desvío de residuos de cada modelo queda en
`outputs/pronostico/modelos_metricas.csv` como medida de ajuste.

**Con este desvío el EOQ queda por debajo de σ_X en los cinco insumos de clase
A**, que es el caso en que Brown (1967) advierte que aproximar q* por el EOQ
deja de estar garantizado. Se mantiene igual q* = EOQ porque es lo que pide el
enunciado, y `outputs/inventario/verificacion_eoq.csv` reporta cuánto mejoraría
el costo la solución exacta del sistema (entre 4% y 10%).

**Un archivo de salida por pregunta.** Las tablas que se contenían unas a otras
se unificaron: la etapa 2 deja una sola clasificación con las columnas del ABC y
del XYZ, y la etapa 4 deja las dos políticas en una tabla con una columna
`Politica` en lugar de dos archivos de esquema idéntico. Nada que se pueda
obtener filtrando o restando otra tabla se guarda aparte.

**El costo de compra queda fuera de la comparación entre políticas.** No es una
decisión propia: Winston define TC(q, r) como el "costo anual esperado sin
incluir costo de compra". Es idéntico en las dos políticas —misma demanda, mismo
precio— y representa el 99% del gasto total, con lo cual incluirlo haría
invisible cualquier diferencia de gestión: sobre el total, A y B difieren en un
0,03%. Se reporta aparte.

**Se sigue la notación de Winston, capítulo 16.** `E(D)` demanda anual, `K` costo
de pedido, `h` costo de conservación, `c_B` costo por unidad de déficit, `q`
cantidad de pedido, `r` punto de reabastecimiento, `E(X)` y `sigma_X` para la
demanda durante el plazo de entrega, `E(B_r)` déficit esperado por ciclo, y
`SLM1`/`SLM2` para las dos medidas de nivel de servicio de la sección 16.7.

---

## Dependencias

| Paquete | Uso |
|---|---|
| pandas, numpy | manipulación de datos |
| scipy | distribución normal y función de pérdida |
| matplotlib | gráficos |
| statsmodels | Holt-Winters y SARIMA |
| prophet | modelo Prophet |

---

## Bibliografía

- Winston, W. L. *Investigación de Operaciones: Aplicaciones y Algoritmos*,
  4.ª ed. Thomson. Base teórica de todo el módulo de inventario:
  - Sección 16.6, "La EOQ con demanda incierta: modelos (r, q) y (s, S)",
    págs. 890-897. Ecuación (8) para la demanda en el plazo de entrega,
    ecuación (11) para TC(q, r) y ecuación (13) para el caso de pedidos
    pendientes.
  - Sección 16.7, "Método del nivel de servicio", pág. 898. Definición de
    SLM1 y SLM2.
- Hadley, G. y Whitin, T. M. *Analysis of Inventory Systems*. Prentice-Hall, 1963.
- Brown, R. G. *Decision Rules for Inventory Management*, 1967. Citado por
  Winston (pág. 893) para la validez de aproximar q* por el EOQ.
- Silver, E. A., Pyke, D. F. y Peterson, R. *Inventory Management and Production
  Planning and Scheduling*, 3.ª ed. Cap. 7, función de pérdida normal.
- Taylor, S. J. y Letham, B. *Forecasting at Scale*, 2018.
  https://peerj.com/preprints/3190/
- Superintendencia de Riesgos del Trabajo. *Manual de Buenas Prácticas —
  Industria Automotriz*.
- Jenkins, A. *Warehouse Space Utilization: How to Calculate and Optimize*,
  NetSuite.
