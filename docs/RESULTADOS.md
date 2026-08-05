# Resultados para el informe

Números finales del pipeline, ordenados por sección y cruzados contra la
rúbrica. Todos salen de `outputs/` y se regeneran con `make todo`.

Notación según Winston, *Investigación de Operaciones*, capítulo 16:

| Símbolo | Significado |
|---|---|
| E(D) | demanda anual esperada |
| K | costo de hacer un pedido |
| h | costo de conservar una unidad un año |
| c_B | costo por unidad de déficit |
| L | plazo de entrega |
| X | demanda durante el plazo de entrega |
| E(X), σ_X | media y desvío de X |
| q | cantidad de pedido |
| r | punto de reabastecimiento |
| E(B_r) | déficit esperado por ciclo |
| SLM₁, SLM₂ | medidas de nivel de servicio (sección 16.7) |

Stock de seguridad = r − E(X).

---

## 1. Preparación de datos

| Paso | Líneas |
|---|---:|
| Dataset original | 2.823 |
| Solo Classic Cars y Vintage Cars | 1.574 |
| Descartando pedidos cancelados | **1.545** |

- Período: enero 2003 a mayo 2005 (29 meses)
- **1.545 vehículos** (951 Clásicos / 594 Vintage), 53,3 por mes
- Reparto histórico: **61,55% Clásicos / 38,45% Vintage**

### Tres decisiones de limpieza que hay que contar

**1. El filtro por `Shipped` distorsiona la serie.** Abril 2005 tiene 29 líneas
Classic/Vintage y solo 12 están en estado `Shipped`; mayo tiene 66 y solo 29.
Los pedidos `In Process` y `On Hold` se concentran en los últimos meses
simplemente porque son los más recientes, no porque haya caído la demanda.
Filtrar por `Shipped` habría generado un valle artificial al final de la serie,
que el modelo aprende como si fuera estacionalidad. Se descarta únicamente
`Cancelled`.

**2. `PRICEEACH` está topeado en 100.** Ocurre en 781 de las 1.545 líneas, y en
esos casos `SALES ≠ QUANTITYORDERED × PRICEEACH`. El precio unitario se
reconstruye desde `SALES`, que es el campo consistente.

**3. Una línea de pedido equivale a un vehículo.** El dataset de origen es de
maquetas a escala: cada línea es un producto distinto dentro del pedido de un
cliente, comprado a granel (35 unidades por línea en promedio, mediana 34)
porque son coleccionables que un distribuidor revende. Un cliente de Heritage
Motors no encarga 35 restomods idénticos: encarga *un* vehículo con una
configuración.

La elección **no altera el patrón de demanda**, que es lo que el dataset
realmente aporta:

| Control | Valor |
|---|---:|
| Correlación mensual entre contar líneas y contar unidades | **0,9968** |
| Pico de noviembre 2003, en unidades / en líneas | ×3,64 / ×3,26 |
| Reparto Clásico-Vintage por líneas vs por unidades | 61,6% vs 61,9% |

---

## 2. Clasificación ABC y XYZ

*Rúbrica: 7 puntos.*

### ABC (valor de uso anual)

| Componente | Demanda anual | Costo unit. | Valor de uso | % | % acum. | Clase |
|---|---:|---:|---:|---:|---:|:--:|
| Carrocería Artesanal de Época | 246 | 15.000 | 3.690.000 | 16,80 | 16,80 | A |
| Motor de Alto Rendimiento V8 | 394 | 9.000 | 3.546.000 | 16,15 | 32,95 | A |
| Motor de Cilindros en Línea Raro | 246 | 12.000 | 2.952.000 | 13,44 | 46,39 | A |
| Carrocería Estándar (Fibra) | 394 | 6.500 | 2.561.000 | 11,66 | 58,05 | A |
| Tapicería de Cuero Premium | 639 | 4.000 | 2.556.000 | 11,64 | 69,69 | A |
| Juego de Llantas Vintage Espec. | 983 | 2.500 | 2.457.500 | 11,19 | 80,88 | B |
| Transmisión de 5 Velocidades | 639 | 3.500 | 2.236.500 | 10,18 | 91,06 | B |
| Cubiertas de Alta Gama | 2.557 | 250 | 639.250 | 2,91 | 93,97 | B |
| Llantas Regulares Cromados | 1.574 | 400 | 629.600 | 2,87 | 96,84 | C |
| Sistema de Inyección Electrónica | 394 | 1.200 | 472.800 | 2,15 | 98,99 | C |
| Set de Carburadores Dobles | 246 | 900 | 221.400 | 1,01 | 100,00 | C |

Los cinco de clase A concentran el **69,69%** del valor de uso.

La demanda anual está redondeada a unidades enteras (los insumos son piezas
indivisibles) y el valor de uso se calcula sobre esa cifra redondeada, así que la
multiplicación de la tabla cierra exacta. Sin redondear, la clase A daba 69,67%:
el redondeo mueve los porcentajes menos de una décima de punto y no cambia el
orden ni las clases.

Dato útil para el oral: **la clasificación ABC es invariante a la escala.**
Contando líneas de pedido o unidades del dataset se llega al mismo reparto y a
los mismos cinco componentes de clase A.

> **Nota:** el ítem que cruza el 80% es el Juego de Llantas Vintage (80,88%).
> Conviene escribir por qué se corta antes en vez de dejarlo implícito.

### XYZ (variabilidad)

Los once dan **clase Z**. Como todos se consumen en proporción fija a los
Clásicos, a los Vintage o a ambos, solo hay tres perfiles posibles:

| Perfil | CV mensual | Componentes |
|---|---:|---|
| Vintage | 71,76% | Carrocería Artesanal, Motor Raro, Carburadores, Llantas Vintage |
| Ambos | 73,94% | Tapicería, Transmisión, Cubiertas |
| Clásico | 77,67% | Motor V8, Carrocería Estándar, Inyección, Llantas Cromados |

Todo da AZ, BZ o CZ. El XYZ no agrega un criterio de corte por encima del ABC,
pero **sí justifica el paso siguiente**: con esa variabilidad la demanda no
puede tratarse como determinista, y por eso el trabajo va al capítulo 16 de
Winston (modelos probabilísticos) y no al 15 (determinísticos).

---

## 3. Pronóstico

*Rúbrica: 8 puntos.*

| Modelo | MAPE | σ residuos | Total 12 meses |
|---|---:|---:|---:|
| **Prophet** | **14,70%** | 6,5 | 917 |
| Holt-Winters aditivo | 27,63% | 11,3 | 906 |
| SARIMA(1,1,1)(1,0,1,12) | 53,89% | 35,5 | 819 |

Modelo seleccionado: **Prophet**.

**Lo que se lleva a la etapa de inventario:**

- E(D) total pronosticada: **917 vehículos/año**
- Desvío del error de pronóstico: **6,5 vehículos/mes** = **3,1 por semana**

Puntos a mencionar:

- **Holt-Winters estima α = β = γ = 0.** El optimizador dice que no conviene
  actualizar nada con las observaciones nuevas, porque el patrón se repite casi
  igual año a año. El modelo se reduce a un promedio estacional fijo.

- **El ADF rechaza la raíz unitaria (p = 0,0044) pero el AIC prefiere d = 1.**
  Con 29 observaciones y un pico estacional que triplica el nivel del resto del
  año, el test pierde potencia. El script prueba cuatro órdenes y se queda con
  el de menor AIC.

- **El desvío que importa es el del error, no el de la serie.** El stock de
  seguridad cubre lo que el pronóstico no anticipa. La estacionalidad de
  noviembre ya está dentro del pronóstico, y por lo tanto ya está contemplada
  en E(X).

- **El pronóstico (917) supera el promedio histórico (639).** Prophet extrapola
  la tendencia de crecimiento de los últimos meses.

---

## 4. Parámetros de riesgo

*Rúbrica: 10 puntos — cálculo preciso y justificado.*

### Costo por unidad de déficit (c_B)

El enunciado define la compensación como el 5% del precio del auto, pero no da
el precio. Lo que sí se puede calcular es el costo de materiales de cada
vehículo:

```
Clásico = 9.000 + 6.500 + 3.500 + 1.200 + 4.000 + 4×400   + 4×250 = 26.800
Vintage = 12.000 + 15.000 + 3.500 + 900  + 4.000 + 4×2.500 + 4×250 = 46.400
```

| Vehículo | Costo de materiales | c_B = 5% |
|---|---:|---:|
| Clásico | 26.800 | **1.340** |
| Vintage | 46.400 | **2.320** |
| Ambos (ponderado 61,55/38,45) | — | **1.717** |

**Justificación:** ningún fabricante vende por debajo del costo de materiales,
así que ese número es una **cota inferior** del precio de venta. El c_B
resultante es entonces conservador. La elección es deliberada — subestimar c_B
lleva a stocks de seguridad más chicos, que es el lado incómodo del error — y la
sensibilidad de ±30% cubre cuánto cambiaría la decisión si el precio real fuera
más alto.

### Demanda durante el plazo de entrega

Winston, ecuación (8), pág. 891: `E(X) = L·E(D)` y `σ_X = σ_D·√L`.

Tres pasos: σ mensual del error → σ semanal (dividir por √4,33) → σ_X
(multiplicar por √L).

| Componente | E(D) | h | c_B | c_B/h | L (sem) | E(X) | σ_X |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 565 | 1.800 | 1.340 | 0,74 | 6 | 65,2 | 4,70 |
| Motor de Cilindros en Línea Raro | 353 | 2.400 | 2.320 | 0,97 | 12 | 81,4 | 4,15 |
| Carrocería Artesanal de Época | 353 | 3.000 | 2.320 | 0,77 | 10 | 67,8 | 3,79 |
| Carrocería Estándar (Fibra) | 565 | 1.300 | 1.340 | 1,03 | 4 | 43,4 | 3,84 |
| Tapicería de Cuero Premium | 917 | 800 | 1.717 | 2,15 | 8 | 141,1 | 8,82 |

La relación **c_B/h** es la que gobierna el punto de reabastecimiento.

---

## 5. Política A — Pedidos pendientes (Winston 16.6)

*Rúbrica: 15 puntos.*

Winston, ecuación (13), pág. 893:

```
q*         = (2·K·E(D)/h)^½
P(X ≥ r*)  = h·q* / (c_B·E(D))
```

La segunda sale del análisis marginal: subir el reorden en Δ cuesta h·Δ de
almacenamiento extra y ahorra Δ·E(D)·c_B·P(X ≥ r)/q de déficit; el óptimo iguala
las dos cosas.

| Componente | q | r | SS | z | P(X≥r) | E(B_r) | Pedidos/año | SLM₁ | SLM₂ | TC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Motor V8 | 13,72 | 73,83 | 8,67 | 1,843 | 0,0326 | 0,060 | 41,2 | 99,56% | 1,34 | 43.620 |
| Motor Raro | 9,39 | 89,36 | 7,97 | 1,918 | 0,0275 | 0,044 | 37,6 | 99,53% | 1,03 | 45.481 |
| Carrocería Artesanal | 8,40 | 74,92 | 7,09 | 1,869 | 0,0308 | 0,045 | 42,0 | 99,46% | 1,29 | 50.889 |
| Carrocería Estándar | 16,14 | 50,79 | 7,36 | 1,915 | 0,0277 | 0,041 | 35,0 | 99,75% | 0,97 | 32.462 |
| Tapicería | 26,23 | 160,69 | 19,56 | 2,217 | 0,0133 | 0,041 | 35,0 | 99,84% | 0,47 | 39.101 |

**TC total Política A: USD 211.553/año**

### Verificación de la aproximación q* = EOQ

Winston aproxima q* por el EOQ y cita a Brown (1967) en la nota al pie de la
pág. 893: la aproximación es aceptable **salvo que EOQ ≤ σ_X**. Se verificó
contra la solución exacta del sistema de condiciones de primer orden (su
ecuación 12), resuelto por iteración:

| Componente | σ_X | q (EOQ) | q exacto | Δq | TC (EOQ) | TC exacto | ΔTC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor V8 | 4,70 | 13,72 | 15,73 | +14,6% | 43.620 | 43.393 | −0,52% |
| Motor Raro | 4,15 | 9,39 | 11,16 | +18,8% | 45.481 | 45.151 | −0,73% |
| Carrocería Artesanal | 3,79 | 8,40 | 10,05 | +19,6% | 50.889 | 50.492 | −0,78% |
| Carrocería Estándar | 3,84 | 16,14 | 17,70 | +9,7% | 32.462 | 32.373 | −0,27% |
| Tapicería | 8,82 | 26,23 | 29,55 | +12,6% | 39.101 | 38.954 | −0,38% |

Los cinco cumplen EOQ > σ_X y la solución exacta mejora el costo **a lo sumo un
0,78%**. La aproximación de Winston es válida en este caso. Vale la pena poner
esta tabla en el informe: muestra que la simplificación no se dio por sentada.

---

## 6. Política B — Nivel de servicio (Winston 16.7)

*Rúbrica: 12 puntos.*

q* sale del mismo EOQ. r sale de imponer `P(X ≥ r) = α = 0,05`, o sea
z = Φ⁻¹(0,95) = **1,6449**.

| Componente | q | r | SS | Pedidos/año | E(B_r) | SLM₁ | SLM₂ | TC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Motor V8 | 13,72 | 72,89 | 7,74 | 41,2 | 0,098 | 99,28% | 2,06 | 44.042 |
| Motor Raro | 9,39 | 88,23 | 6,83 | 37,6 | 0,087 | 99,08% | 1,88 | 46.503 |
| Carrocería Artesanal | 8,40 | 74,06 | 6,24 | 42,0 | 0,079 | 99,06% | 2,10 | 51.633 |
| Carrocería Estándar | 16,14 | 49,75 | 6,32 | 35,0 | 0,080 | 99,50% | 1,75 | 32.960 |
| Tapicería | 26,23 | 155,65 | 14,51 | 35,0 | 0,184 | 99,30% | 1,75 | 43.665 |

**TC total Política B: USD 218.802/año**

---

## 7. Comparación A vs B

*Rúbrica: 7 puntos.*

**Las dos políticas piden el mismo q.** Lo único que cambia es r. Eso hace que
la comparación aísle exactamente la decisión que las distingue.

| Concepto (ecuación 11) | Política A | Política B |
|---|---:|---:|
| Costo de pedidos | 57.199 | 57.199 |
| Costo de almacenamiento | 138.414 | 126.068 |
| Costo de déficit | 15.939 | 35.535 |
| **TC(q, r)** | **211.553** | **218.802** |
| Costo de compra (fuera de TC) | 21.944.702 | 21.944.702 |
| Costo total | 22.156.254 | 22.163.504 |

**La Política A ahorra USD 7.250 al año**, un 3,3% de TC(q, r).

> **Por qué el costo de compra va aparte.** No es una decisión nuestra: Winston
> define TC(q, r) como el "costo anual esperado (sin incluir costo de compra)"
> (pág. 891). Tiene sentido: se compra la misma cantidad al mismo precio
> gobierne quien gobierne el inventario. Sobre el costo total esa misma
> diferencia sería del **0,03%**, así que incluirla haría invisible cualquier
> diferencia de gestión.

**El argumento central:** la Política B parece la conservadora porque impone un
95%, pero ese 95% es *por ciclo*. Con 35 a 42 reposiciones al año, un 5% de
riesgo por ciclo da SLM₂ de 1,75 a 2,10 quiebres anuales. La Política A tolera
una probabilidad de agotamiento menor (0,013 a 0,033), lleva entre 13% y 35%
más de stock de seguridad, y baja SLM₂ a 0,47-1,34.

Nótese que A gasta **más** en almacenamiento (138.414 vs 126.068) y **menos** en
déficit (15.939 vs 35.535). No ahorra en todo: reasigna el gasto hacia donde
rinde. Esa es exactamente la transacción de la figura 4 de Winston (pág. 894).

**Recomendación: Política A.** Es más barata y da mejor servicio.

Referencia sobre el catálogo completo (11 componentes): TC de **USD 323.148**
para A y **USD 360.327** para B.

---

## 8. Nivel de servicio resultante

*Rúbrica: 8 puntos.*

Winston define dos medidas (sección 16.7, pág. 898):

- **SLM₁**: fracción esperada de toda la demanda que se cumple a tiempo
- **SLM₂**: número esperado de ciclos al año durante los cuales se presenta déficit

La Política A no fija el nivel de servicio: lo determina la relación c_B/h a
través de `P(X ≥ r*) = h·q*/(c_B·E(D))`.

| Componente | c_B/h | P(X ≥ r) | z | SLM₁ | SLM₂ |
|---|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 0,74 | 0,0326 | 1,843 | 99,56% | 1,34 |
| Motor de Cilindros en Línea Raro | 0,97 | 0,0275 | 1,918 | 99,53% | 1,03 |
| Carrocería Artesanal de Época | 0,77 | 0,0308 | 1,869 | 99,46% | 1,29 |
| Carrocería Estándar (Fibra) | 1,03 | 0,0277 | 1,915 | 99,75% | 0,97 |
| Tapicería de Cuero Premium | 2,15 | 0,0133 | 2,217 | 99,84% | 0,47 |

**Ponderado por demanda: SLM₁ = 99,68%, P(X ≥ r) = 0,0243.**

Resultado a destacar: la probabilidad de agotamiento del óptimo económico
(0,0243) queda **por debajo del α = 0,05** que el enunciado le impone a la
Política B. Con estos costos, cubrirse conviene por sí solo. Y se ve la lógica
componente a componente: el de mayor c_B/h (Tapicería, 2,15) es el que llega al
z más alto (2,217).

---

## 9. Capacidad mínima de almacén

*Rúbrica: 10 puntos.*

En el sistema (r, q) el inventario máximo es **q + (r − E(X))**: el lote que
acaba de llegar más el stock de seguridad. Sale de la misma cuenta que hace
Winston en la pág. 892 al deducir la ecuación (11) — el nivel al principio del
ciclo es r − E(X) + q.

No se suma r entero: la demanda del plazo de entrega que r cubre se consume
mientras el pedido viaja, y además r ya lleva el stock de seguridad adentro.

Se toman los **once** componentes: los modelos se aplican sobre la clase A
porque ahí está el valor, pero el depósito guarda todo el catálogo.

| Componente | Vol. unit. | Imax A | m³ A | Imax B | m³ B |
|---|---:|---:|---:|---:|---:|
| Motor V8 | 0,80 | 22,4 | 17,9 | 21,5 | 17,2 |
| Motor Raro | 0,90 | 17,4 | 15,6 | 16,2 | 14,6 |
| Carrocería Artesanal | 4,00 | 15,5 | 62,0 | 14,6 | 58,6 |
| Carrocería Estándar | 3,50 | 23,5 | 82,2 | 22,5 | 78,6 |
| Transmisión | 0,40 | 42,0 | 16,8 | 38,3 | 15,3 |
| Inyección | 0,10 | 45,1 | 4,5 | 43,0 | 4,3 |
| Carburadores | 0,10 | 40,8 | 4,1 | 38,7 | 3,9 |
| Tapicería | 0,50 | 45,8 | 22,9 | 40,7 | 20,4 |
| Llantas Vintage | 0,15 | 67,9 | 10,2 | 58,8 | 8,8 |
| Llantas Cromadas | 0,10 | 159,5 | 16,0 | 148,0 | 14,8 |
| Cubiertas | 0,10 | 261,6 | 26,2 | 238,9 | 23,9 |
| **Total neto** | | | **278,3** | | **260,3** |

Del volumen neto al galpón, con el rango de utilización de NetSuite (45-85%) y
altura útil de 5 m:

| Política | Escenario | Utilización | Volumen almacén | Superficie | Costo obra |
|---|---|---:|---:|---:|---:|
| A | Conservador | 65% | 428 m³ | 86 m² | USD 128.464 |
| A | Óptimo | 75% | 371 m³ | 74 m² | USD 111.336 |
| B | Conservador | 65% | 400 m³ | 80 m² | USD 120.141 |
| B | Óptimo | 75% | 347 m³ | 69 m² | USD 104.123 |

### Análisis de factibilidad

La política más barata **no** es la que menos espacio necesita. La A pide
**18 m³ más** (6,9%) porque lleva más stock de seguridad: **USD 8.323** más de
obra en el escenario conservador.

Ese sobrecosto es de una sola vez y la diferencia operativa se repite todos los
años: **USD 8.323 contra USD 7.250 anuales**. La inversión adicional se recupera
en poco más de un año. **La restricción de capacidad no cambia la
recomendación.**

**Propuesta:** construir para la Política A en escenario conservador —
**428 m³, unos 86 m² con 5 m de altura útil**. Aceptar el 65% de utilización en
vez del 75% deja margen para el pico de octubre-noviembre, que en el histórico
casi triplica la demanda mensual promedio.

> **Qué no incluye.** El cálculo cubre el inventario de componentes, que es lo
> que pide el enunciado. Un depósito real necesita además espacio para material
> en proceso, vehículos terminados y devoluciones, y cualquier lote mínimo de
> compra de un proveedor obligaría a pedir más de lo que dice el modelo.
> Conviene leerlo como un piso para el sector de componentes, no como el tamaño
> del edificio.

---

## 10. Sensibilidad al costo de déficit (c_B ±30%)

*Rúbrica: 10 puntos.*

c_B no se toca solo en la fórmula del costo: se **vuelve a resolver la ecuación
(13)** con el nuevo valor.

| Escenario | q prom. | SS total | Déficit anual | TC total | Δ TC | P(X≥r) media | SLM₁ media |
|---|---:|---:|---:|---:|---:|---:|---:|
| c_B −30% | 14,78 | 46,71 | 13,36 | 205.724 | −2,76% | 0,0377 | 99,44% |
| c_B base | 14,78 | 50,65 | 8,89 | 211.553 | — | 0,0264 | 99,63% |
| c_B +30% | 14,78 | 53,40 | 6,61 | 215.663 | +1,94% | 0,0203 | 99,72% |

**Lectura:** un error de ±30% en c_B mueve TC(q, r) solo entre −2,76% y +1,94%.

**El lote q no se mueve**, porque el EOQ no depende de c_B: todo el ajuste pasa
por r. Eso se lee directo en la ecuación (13) y es un buen punto para el oral.

Aun con c_B un 30% por debajo, la probabilidad de agotamiento (0,0377) sigue por
debajo del α = 0,05 exigido a la Política B. **La recomendación no cambia.**

---

## 11. Sensibilidad al riesgo (+15% de incertidumbre)

*Rúbrica: 8 puntos — demostrar cómo la incertidumbre obliga a aumentar el SS.*

| Política | SS base | SS +15% | Δ SS | TC base | TC +15% | Δ TC |
|---|---:|---:|---:|---:|---:|---:|
| A | 50,65 | 58,24 | **+15,00%** | 211.553 | 226.126 | +6,89% |
| B | 41,64 | 47,89 | **+15,00%** | 218.802 | 234.463 | +7,16% |

**Lectura:** el stock de seguridad es z·σ_X, así que un 15% más de
incertidumbre obliga a exactamente un 15% más de stock **en las dos políticas**.

Ninguna puede reaccionar de otra forma, y el motivo es interesante: ningún z
depende de σ_X. El de B está fijado por el enunciado en 1,645; el de A sale de
`P(X ≥ r*) = h·q*/(c_B·E(D))`, donde σ_X no aparece. Tampoco se mueve q, porque
el EOQ tampoco depende de σ_X. **Toda la incertidumbre extra se paga con stock,
sin margen de maniobra.** Ese es el resultado que pide la rúbrica.

En costo A sube 6,89% (USD 14.573) y B 7,16% (USD 15.661). A absorbe mejor el
golpe porque parte de un stock más alto, así que el déficit adicional que genera
la mayor volatilidad es menor. **A es la más robusta.**

---

## Cobertura de la rúbrica

| Criterio | Puntos | Dónde |
|---|---:|---|
| Pronóstico (series de tiempo) | 8 | Sección 3 |
| Clasificación ABC y XYZ | 7 | Sección 2 |
| Parámetros de riesgo | 10 | Sección 4 |
| Política A (Hadley/Whitin) | 15 | Sección 5 |
| Política B (NS = 95%) | 12 | Sección 6 |
| Nivel de servicio resultante | 8 | Sección 8 |
| Restricción de capacidad | 10 | Sección 9 |
| Sensibilidad a costos | 10 | Sección 10 |
| Sensibilidad a riesgo | 8 | Sección 11 |
| Recomendación de política | 7 | Sección 7 |
| Recomendación de almacén | 5 | Sección 9 |

---

## Puntos a cuidar en la defensa oral

**1. Por qué una línea de pedido es un vehículo.** Es el supuesto que fija la
escala de todo el trabajo: *el dataset es de maquetas que se venden a granel (34
por línea); un cliente de Heritage Motors encarga un vehículo, no 34 idénticos.*
El respaldo: la correlación con la serie de unidades es 0,9968, o sea que el
patrón de demanda no cambia, solo la unidad.

Si insisten, el argumento fuerte es que **la recomendación no depende de la
escala**: se verificó reescalando la demanda por factores de 1 a 100 y la
Política A resulta más barata en todos los casos, con probabilidad de
agotamiento siempre por debajo del α exigido. Lo que sí cambia es el margen, así
que conviene no exagerar el tamaño del ahorro.

**2. Por qué el costo de compra va aparte.** Winston lo define así. Ver
sección 7.

**3. Por qué σ es el del error y no el de la serie.** El stock de seguridad
cubre lo que el pronóstico no anticipa. La estacionalidad de noviembre ya está
dentro del pronóstico y por lo tanto ya está en E(X); volver a cubrirla con
stock sería pagarla dos veces.

**4. Por qué el almacén da chico.** 86 m² para 917 vehículos al año sorprende.
El modelo repone seguido (35 a 42 pedidos por año) y con reposición frecuente
hay poco stock en estante. El número cubre componentes, no material en proceso
ni vehículos terminados.

**5. Por qué se usa la aproximación q* = EOQ.** Porque es lo que hace Winston, y
porque se verificó: los cinco componentes cumplen la condición de Brown
(EOQ > σ_X) y la solución exacta mejora el costo a lo sumo 0,78%. Ver sección 5.
