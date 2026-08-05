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
| 3. Pronóstico | Holt-Winters, Prophet y SARIMA; se elige el de menor MAPE |
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
también cada script por separado (`make pronostico-sarima`). Si falta un archivo
intermedio, el script avisa qué `make` hay que ejecutar antes.

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
│   ├── pronostico/             3. los tres modelos y su comparación
│   ├── inventario/             4. modelos de inventario y aplicación
│   │   ├── modelos.py            matemática pura, sin lectura ni escritura
│   │   ├── riesgo.py             c_B y sigma_X de cada componente
│   │   └── politicas.py          aplica A y B, y las compara
│   ├── almacen/                5. capacidad mínima
│   └── sensibilidad/           6. los dos análisis de sensibilidad
│
├── outputs/                    resultados (CSV y PNG), se regeneran con make todo
└── docs/                       enunciado, informe y resultados
```

Dos decisiones de organización que conviene explicar:

- **Un solo lugar para los datos del enunciado.** Costos unitarios, ratios de
  uso, volúmenes y lead times viven únicamente en `src/parametros.py`. Ningún
  script los redefine por su cuenta.

- **La matemática separada de la aplicación.** `src/inventario/modelos.py` tiene
  las fórmulas y nada más: no lee archivos ni imprime. Eso permite verificar los
  modelos con valores conocidos, independientemente del pipeline.

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

**El stock de seguridad se dimensiona con el error del pronóstico**, no con la
variabilidad de la serie histórica. Lo que hay que cubrir es lo que el modelo no
logra anticipar; la estacionalidad ya está dentro del pronóstico.

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
