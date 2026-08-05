# Heritage Motors S.A. — Informe Técnico-Ejecutivo

Modelos de pronóstico e inventario para el reaprovisionamiento de componentes
críticos y el dimensionamiento del nuevo almacén central.

---

## Resumen Ejecutivo

Heritage Motors S.A. está pasando por un momento de incertidumbre y amenaza en
base a su gestión de inventario. Sus dos líneas de producto, los Autos Clásicos
y los Autos Vintage, dependen de insumos caros que además tardan mucho en
llegar, y la demanda de esos vehículos no se comporta de manera regular. A eso
se le suma la necesidad de definir cuánto espacio tiene que tener el almacén que
la compañía quiere construir.

El estudio se realizó en cuatro tramos. Primero se limpiaron y organizaron los
datos de ventas. Después se identificó sobre qué insumos vale la pena poner el
esfuerzo. Luego se pronosticó la demanda del año que viene con tres modelos
distintos. Y por último se compararon dos políticas de reaprovisionamiento y se
tradujo la ganadora a metros cúbicos de galpón.

Lo que encontramos, en resumen:

| | |
|---|---|
| Demanda pronosticada | 917 vehículos para los próximos 12 meses |
| Modelo utilizado | Prophet (MAPE 14,70%) |
| Insumos críticos | 5 de 11, concentran el 69,69% del valor de uso anual |
| Política recomendada | **A — Faltantes admitidos (óptima por costos)** |
| Ahorro anual | USD 7.250 sobre el costo controlable de inventario |
| Nivel de servicio alcanzado | 99,68% de la demanda entregada a tiempo |
| Almacén propuesto | 428 m³, unos 86 m² con 5 metros de altura útil |
| Inversión en obra | USD 128.464 |

**Recomendamos a la organización inclinarse por la Política A**, que fija el
punto de reabastecimiento por criterio económico en lugar de imponerle al modelo
un nivel de servicio del 95%. Es más barata y, contra lo que uno esperaría a
primera vista, **da mejor servicio**: su probabilidad de quedarse sin stock
resulta de 0,0243, bastante por debajo del 0,05 que impone la otra política.

Lo más interesante que salió del análisis es que ese 95% de la Política B no
significa lo que parece. Es un objetivo *por cada ciclo de reposición*, y como
la compañía repone entre 35 y 42 veces al año por insumo, ese 5% de riesgo
repetido tantas veces termina dando alrededor de dos quiebres de stock anuales.
La política óptima por costos, al ponderar lo que realmente cuesta un faltante,
termina siendo más prudente que la restricción que se le quería imponer.

Para el almacén se propone construir 428 m³. La Política A necesita 18 m³ más
que la B, lo que representa USD 8.323 adicionales de obra por única vez, que se
recuperan en poco más de un año con la diferencia de costo operativo. La
restricción de capacidad no cambia la recomendación.

---

## 1. Análisis Preliminar

### 1.1. Limpieza y organización de los datos

En un primer paso, solo para aportar mayor contexto sobre el estudio realizado,
se comenzó con la limpieza y organización de los datos suministrados por la
organización. El histórico entregado tiene 2.823 líneas de pedido entre enero de
2003 y mayo de 2005.

Las actividades de esta índole fueron variadas, pero conviene detenerse en tres
decisiones que tomamos, porque cada una termina afectando los números finales.

**Primero, qué líneas de producto conservar.** Nos quedamos únicamente con los
pedidos de Autos Clásicos y Autos Vintage, que son las dos líneas del caso.
Quedan 1.574 líneas de pedido.

**Segundo, qué hacer con los pedidos que no fueron despachados.** La idea
original era quedarse solo con lo efectivamente enviado, pero al mirar la
distribución mes a mes apareció un problema. Abril de 2005 tiene 29 líneas y
solamente 12 aparecen como despachadas; mayo tiene 66 y solamente 29. Los
pedidos en proceso y en espera se amontonan al final de la serie por una razón
sencilla: son los más recientes, todavía no les dio tiempo de despacharse. No es
que la demanda haya caído.

Si hubiéramos filtrado por despachados nos habríamos fabricado un valle
artificial justo en los últimos meses, y el modelo de pronóstico lo habría
aprendido como si fuera un patrón real. Así que se decidió descartar únicamente
los pedidos **cancelados**: un pedido en proceso o en espera es demanda genuina,
el cliente igual pidió la unidad. Quedan **1.545 líneas**.

**Tercero, un error en el campo de precio.** El precio unitario del histórico
viene topeado en 100 en 781 de las 1.545 líneas, con lo cual no coincide con el
importe facturado dividido la cantidad. Lo recalculamos a partir del importe,
que es el campo que sí cierra.

**Y una aclaración sobre la unidad de medida.** El histórico registra cada línea
de pedido con una cantidad promedio de 35 unidades. Esa granularidad no
corresponde al negocio de Heritage Motors: un cliente que encarga una
restauración no pide 35 vehículos idénticos, pide uno con una configuración
determinada. Por eso tomamos la correspondencia **una línea de pedido = un
vehículo encargado**.

La decisión no cambia el patrón de demanda, que es lo que el histórico realmente
nos aporta. Lo verificamos: la correlación mensual entre contar líneas y contar
unidades es de **0,9968**, el pico de noviembre se conserva y el reparto entre
las dos líneas de producto prácticamente no se mueve (61,6% contra 61,9%).

La serie que queda tiene **29 meses y 1.545 vehículos**, 53,3 por mes en
promedio, repartidos en **61,55% Clásicos y 38,45% Vintage**.

### 1.2. Qué insumos priorizar

Para poder entender qué insumos debe priorizar la compañía, se procedió a
realizar un análisis sobre aquellos bienes que representan cerca del ochenta por
ciento de los costos. Se calculó el valor de uso anual de cada insumo, que es la
cantidad que se consume en un año multiplicada por su costo unitario.

| Insumo | Producto | Demanda anual | Costo unit. | Valor de uso | % individual | % acumulado |
|---|---|---:|---:|---:|---:|---:|
| Carrocería Artesanal de Época | Vintage | 246 | 15.000 | 3.690.000 | 16,80% | 16,80% |
| Motor de Alto Rendimiento V8 | Clásico | 394 | 9.000 | 3.546.000 | 16,15% | 32,95% |
| Motor de Cilindros en Línea Raro | Vintage | 246 | 12.000 | 2.952.000 | 13,44% | 46,39% |
| Carrocería Estándar (Fibra) | Clásico | 394 | 6.500 | 2.561.000 | 11,66% | 58,05% |
| Tapicería de Cuero Premium | Ambos | 639 | 4.000 | 2.556.000 | 11,64% | 69,69% |

Una aclaración sobre la demanda anual. Sale de anualizar el histórico —los 1.545
vehículos de 29 meses llevados a doce y repartidos entre las dos líneas de
producto—, y esa cuenta da un número fraccionario. Como los insumos son piezas
indivisibles (no se consumen 245,79 carrocerías), redondeamos la demanda a
unidades enteras y calculamos el valor de uso sobre esa cifra redondeada. Así la
tabla cierra si se rehace la multiplicación a mano. El redondeo mueve los
porcentajes menos de una décima de punto y no cambia ni el orden de los insumos
ni la clase de ninguno.

Todos estos insumos pertenecen a lo que técnicamente, referenciando al análisis
realizado, se conoce como **"Categoría A"**, y son los que representan la
grandísima mayoría de los costos, por lo cual les debemos prestar mayor
atención. Sobre estos cinco se van a aplicar los modelos de inventario.

El resto del catálogo queda así:

| Insumo | Producto | Valor de uso | % acumulado | Clase |
|---|---|---:|---:|:--:|
| Juego de Llantas Vintage Espec. | Vintage | 2.457.500 | 80,88% | B |
| Transmisión de 5 Velocidades | Ambos | 2.236.500 | 91,06% | B |
| Cubiertas de Alta Gama | Ambos | 639.250 | 93,97% | B |
| Llantas Regulares Cromados | Clásico | 629.600 | 96,84% | C |
| Sistema de Inyección Electrónica | Clásico | 472.800 | 98,99% | C |
| Set de Carburadores Dobles | Vintage | 221.400 | 100,00% | C |

Vale una aclaración sobre dónde cortamos. El insumo que cruza el 80% es el Juego
de Llantas Vintage, que llega al 80,88% acumulado. Podríamos haberlo metido en
la Categoría A y sumar once puntos porcentuales más, pero es el de menor costo
unitario del grupo y el que menos duele si falta una unidad. Preferimos quedarnos
con cinco insumos parejos en valor unitario alto, que es donde el esfuerzo de
modelado rinde.

### 1.3. La variabilidad de la demanda

Realizar un análisis del tipo ABC/XYZ contrastando qué productos son los más
importantes junto con su variabilidad en ventas pierde un poco el sentido en
nuestro caso, y ahora vamos a ver por qué. Igual dejamos la tabla, porque el
resultado tiene una consecuencia importante para lo que sigue.

| Perfil | Insumos | CV mensual | Clase |
|---|---|---:|:--:|
| Vintage | Carrocería Artesanal, Motor Raro, Carburadores, Llantas Vintage | 71,76% | Z |
| Ambos | Tapicería, Transmisión, Cubiertas | 73,94% | Z |
| Clásico | Motor V8, Carrocería Estándar, Inyección, Llantas Cromados | 77,67% | Z |

Como cada insumo se consume en proporción fija a los Clásicos, a los Vintage o a
los dos, solamente existen tres perfiles de variabilidad posibles. Y los tres
superan largamente el umbral del 25%. La totalidad de los insumos cuentan con
una desviación de demanda demasiado grande, entendiendo así que estamos
presenciando un caso altamente irregular e impredecible.

O sea que la matriz ABC/XYZ nos da todo AZ, BZ o CZ. Si todos los productos son
del tipo "Z", simplemente podemos decir que toda nuestra cartera es volátil
independientemente del producto, y el análisis XYZ no nos sirve para segmentar
nada que el ABC no haya segmentado ya.

Pero sí nos sirve para otra cosa, y es la conclusión importante de esta sección:
**con esta variabilidad la demanda no se puede tratar como si fuera constante**.
Eso descarta de entrada el modelo EOQ clásico del capítulo 15 de Winston y nos
obliga a trabajar con los modelos probabilísticos del capítulo 16. Volveremos
sobre esto más adelante.

### 1.4. El comportamiento estacional

Se estudió de cerca cómo es el comportamiento de las ventas en base al
calendario, y se encontró curiosamente un período estacional muy marcado.
Puntualmente alrededor del mes de noviembre de 2003 y de 2004.

El dato tomó mayor notoriedad cuando entendemos que las ventas respecto del mes
de octubre casi se duplican para noviembre, y vuelven a caer a valores más bajos
que el décimo mes para diciembre. Noviembre concentra casi el triple del
promedio mensual, y el patrón se repite prácticamente idéntico en los dos años
completos que tiene el histórico.

Esta información nos es útil por dos motivos. El primero es que un patrón que se
repite es un patrón que se puede pronosticar, así que juega a favor. El segundo
es que claramente estamos ante la necesidad de preparar el almacén para
absorber esa punta, cosa que retomaremos en la sección del galpón.

---

## 2. Pronóstico de la Demanda

Una vez en claro la demanda de los productos objetos de estudio, nos
encontramos disponibles para comenzar a hacer el interesante trabajo de
pronosticar la demanda para los tiempos venideros.

Los datos que se facilitaron fueron hasta el mes de mayo del 2005, y generamos
un pronóstico de 12 meses que podría tomarse desde junio de 2005 a mayo de 2006,
o si fuera contemporáneo, igual pero para el año actual.

### 2.1. Holt-Winters

Una primera predicción se alcanzó utilizando el modelo de Holt-Winters, que se
aplica a este tipo de problemas con estacionalidad. Se seleccionó el modelo
aditivo ya que la estacionalidad se visualiza de manera constante en magnitud en
los períodos en que se da: el pico de noviembre tiene una altura parecida en
2003 y en 2004, o sea que la estacionalidad suma una cantidad más o menos fija
en vez de multiplicar el nivel.

El modelo ajusta los parámetros alpha, beta y gamma de la siguiente manera:

| Parámetro | Valor | Significado |
|---|---:|---|
| α | 0 | No actualiza el nivel |
| β | 0 | No hay tendencia |
| γ | 0 | No actualiza la estacionalidad |

Los tres dan cero, y esto merece una explicación porque a primera vista parece
un error. No lo es: el optimizador nos está diciendo que no conviene actualizar
nada con las observaciones nuevas, porque el patrón se repite casi igual todos
los años. El modelo termina siendo un promedio estacional fijo, calculado en la
inicialización y sostenido para siempre. Es un ajuste degenerado, pero es
coherente con lo que muestran los datos y preferimos reportarlo antes que
disimularlo.

Se calcularon también las métricas de error, que dieron:

| Métrica | Valor |
|---|---:|
| MAE | 9,1 vehículos |
| RMSE | 11,1 vehículos |
| MAPE | 27,63% |

El valor del MAPE muy por encima del 20% nos indica que el pronóstico alcanzado
con Winters no es el más indicado, lo cual es un punto importante a considerar.
El total pronosticado fue de 906 vehículos para el año próximo.

### 2.2. Prophet

Como los resultados obtenidos no nos dejan una confianza suficiente, el equipo
decidió realizar la predicción en series temporales utilizando otros métodos.
Para determinar qué modelos se suelen usar en este tipo de casos, se comenzó con
la tarea de obtener información para solucionar este inconveniente (Predicciones
de Ventas con Series Temporales, Jared Onan Vilorio Luque, pág. 27).

Así fue como decidimos que el modelo que probaremos será Prophet. Se podría usar
LSTM o SARIMA, pero encontramos información que indicaba su mayor complejidad y
bajo desempeño frente a un conjunto de datos acotado (Limitaciones del Modelo
LSTM en la Predicción de Demanda Eléctrica con Datos Simulados de Bajo Volumen,
C. Reyes y C. Inca).

Prophet es la librería para pronóstico univariado creada por Facebook (ahora
Meta) para series temporales con tendencia y estacionalidad. El modelo pronostica
en base a la siguiente ecuación (Forecasting at Scale, S. J. Taylor y B. Letham):

> y(t) = g(t) + s(t) + h(t) + ε(t)

donde g(t) es la tendencia, s(t) la estacionalidad, h(t) los feriados y ε(t) el
ruido. Se configuró con estacionalidad anual aditiva y se desactivaron la
semanal y la diaria, que no tienen ningún sentido en datos mensuales. Tampoco se
cargaron feriados, porque el histórico no identifica el país de cada pedido con
el detalle necesario.

Pasando a lo que nos interesa, las métricas en este caso fueron:

| Métrica | Valor |
|---|---:|
| MAE | 4,4 vehículos |
| RMSE | 6,4 vehículos |
| MAPE | 14,70% |

Si bien el MAPE continúa por encima del 10%, hubo una reducción de casi 13
puntos de error en Prophet frente a Winters, lo cual es una mejora considerable.

El pronóstico total fue de **917 vehículos** para los próximos 12 meses. Es
importante mencionar que Prophet trabaja sobre un intervalo de confianza, que en
nuestro caso se configuró al 95%: eso significa que hay un 95% de probabilidad
de que el valor real caiga dentro de ese rango.

Un punto que conviene señalar es que el pronóstico (917) queda por encima del
promedio anual del histórico (639). Prophet está extrapolando la tendencia
creciente de los últimos meses de la serie. Es una decisión del modelo y no un
error de cálculo, pero implica que estamos dimensionando para un escenario de
crecimiento, y eso hay que tenerlo presente.

### 2.3. SARIMA

Ahora, de manera rápida, pasaremos a demostrar que en este caso el análisis en
modelo SARIMA es una mala idea. Existen evidencias de que no conviene usarlo con
un número tan bajo de observaciones (Modelización de Series Temporales, modelos
clásicos y SARIMA, C. M. Chinlli, pág. 1), y nuestras 29 observaciones mensuales
son poco más de dos ciclos anuales completos.

Se aplicó igual el procedimiento habitual. El test de Dickey-Fuller aumentado
dio un p-valor de 0,0044, o sea que rechaza la raíz unitaria y diría que la serie
es estacionaria. Sin embargo, al probar cuatro especificaciones y comparar por
AIC, el criterio prefiere diferenciar una vez. La explicación es que con tan
pocos datos y un pico estacional que triplica el nivel del resto del año, el
test pierde potencia. Optamos por respetar el criterio de información y quedarnos
con un SARIMA(1,1,1)(1,0,1,12).

| Métrica | Valor |
|---|---:|
| MAE | 23,1 vehículos |
| RMSE | 34,9 vehículos |
| MAPE | 53,89% |

Como no se arrojan resultados útiles, se muestran solo los parámetros de error
para comprobar lo que decía la teoría.

### 2.4. Modelo vs. modelo

Ahora sí, la comparación que veníamos anunciando:

| Modelo | MAE | RMSE | MAPE | Desvío de residuos | Total 12 meses |
|---|---:|---:|---:|---:|---:|
| **Prophet** | 4,4 | 6,4 | **14,70%** | 6,5 | 917 |
| Holt-Winters aditivo | 9,1 | 11,1 | 27,63% | 11,3 | 906 |
| SARIMA(1,1,1)(1,0,1,12) | 23,1 | 34,9 | 53,89% | 35,5 | 819 |

**El modelo elegido es Prophet**, por un margen bastante amplio.

De esta etapa nos llevamos dos números a la etapa de inventario:

- La **demanda anual esperada: 917 vehículos**.
- La **desviación estándar del error de pronóstico: 6,5 vehículos por mes**, que
  equivale a 3,1 por semana.

Vale la pena detenerse en el segundo, porque la elección tiene consecuencias. No
es el desvío de la serie histórica ni el de los valores pronosticados: es el de
los **residuos del modelo**, o sea cuánto se equivoca el pronóstico mes a mes.

Es el que corresponde porque el stock de seguridad existe para cubrir aquello
que el pronóstico no logra anticipar. La estacionalidad de noviembre ya está
metida adentro del pronóstico, y por lo tanto ya está contemplada en la demanda
esperada durante el plazo de entrega. Si además la cubriéramos con stock de
seguridad la estaríamos pagando dos veces.

---

## 3. Modelos de Inventario

### 3.1. Por qué un modelo probabilístico

El documento de requerimientos plantea un enfoque EOQ (Economic Order Quantity,
o Cantidad Económica de Pedido), pero esto plantea varios supuestos que pueden
entrar en conflicto con el caso real que tenemos. El más importante es el
supuesto de **demanda constante**.

Ya vimos en la sección de variabilidad que la demanda de nuestros insumos tiene
coeficientes de variación de entre el 71% y el 77% mensual. No hay forma de
sostener que eso es constante. Según el criterio que expone Winston en el
capítulo 15, cuando la variabilidad de la demanda supera cierto umbral el EOQ
determinístico deja de ser la herramienta adecuada.

La salida no es forzar el EOQ clásico, sino pasar al **capítulo 16 de Winston,
"Modelos probabilísticos de inventarios"**, que es justamente el que trata el
caso de demanda incierta. Ahí está el sistema de revisión continua (r, q), que
es el que vamos a usar de acá en adelante.

El sistema funciona así: se pide siempre la misma cantidad *q*, y el pedido se
dispara cuando el nivel de existencias baja hasta el punto de reabastecimiento
*r*. El pedido tarda *L* semanas en llegar, y lo que falte durante esa espera
queda como pedido pendiente y le cuesta a la empresa la compensación del 5% al
cliente.

Usaremos la notación del libro para que se pueda seguir todo contra el texto:

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

El costo anual esperado es la ecuación (11) de Winston, página 892:

> **TC(q, r) = h · (q/2 + r − E(X)) + c_B · E(B_r) · E(D)/q + K · E(D)/q**

Los tres términos son, en orden: lo que cuesta almacenar, lo que cuesta el
déficit y lo que cuesta hacer los pedidos. El **stock de seguridad es r − E(X)**,
o sea lo que se lleva por encima de lo que se espera consumir mientras llega el
pedido.

Una aclaración que importa: Winston define TC(q, r) explícitamente como el
"costo anual esperado **sin incluir costo de compra**". No es una decisión
nuestra, es como está planteado el modelo, y tiene todo el sentido: se compra la
misma cantidad al mismo precio unitario sin importar qué política de inventario
se use, así que ese término aparecería idéntico a los dos lados de la
comparación. Lo vamos a reportar igual, pero aparte.

### 3.2. Los insumos y sus parámetros

Entonces comenzamos definiendo los insumos como variables de decisión junto a su
costo:

| Variable | Insumo | Costo unitario | Uso por auto | Volumen (m³) | Lead time (sem.) | Vehículo |
|---|---|---:|---:|---:|---:|---|
| x₁ | Carrocería Artesanal de Época | USD 15.000 | 1 | 4,0 | 10 | Vintage |
| x₂ | Motor de Alto Rendimiento V8 | USD 9.000 | 1 | 0,8 | 6 | Clásico |
| x₃ | Motor de Cilindros en Línea Raro | USD 12.000 | 1 | 0,9 | 12 | Vintage |
| x₄ | Carrocería Estándar (Fibra) | USD 6.500 | 1 | 3,5 | 4 | Clásico |
| x₅ | Tapicería de Cuero Premium | USD 4.000 | 1 | 0,5 | 8 | Ambos |

También sumamos el resto de parámetros de interés:

| Parámetro | Valor |
|---|---|
| Costo de la orden (K) | USD 300 |
| Costo de almacenamiento (h) | 20% del costo del insumo, anual |
| Costo de agotamiento (c_B) | 5% de descuento en el precio del auto |

### 3.3. El costo de agotamiento

Acá nos topamos con un problema. El enunciado dice que la compensación es un
descuento del 5% sobre el precio del auto, pero no nos da ese precio: la tabla
de insumos informa costos, no precios de venta. Y sin ese número no podemos
poner el modelo a funcionar.

Lo que sí podemos calcular con los datos que tenemos es el **costo de los
materiales de cada vehículo**, sumando todos los insumos que lleva multiplicados
por su ratio de uso:

```
Clásico = 9.000 + 6.500 + 3.500 + 1.200 + 4.000 + 4×400   + 4×250 = USD 26.800
Vintage = 12.000 + 15.000 + 3.500 + 900  + 4.000 + 4×2.500 + 4×250 = USD 46.400
```

El razonamiento que hicimos es el siguiente: ninguna empresa vende un auto por
debajo de lo que le costaron los materiales para fabricarlo. Entonces ese número
es, como mínimo, el piso del precio de venta. Si calculamos el 5% sobre ese piso,
el costo de agotamiento que obtenemos también es un piso.

| Vehículo | Costo de materiales | c_B = 5% |
|---|---:|---:|
| Clásico | 26.800 | **USD 1.340** |
| Vintage | 46.400 | **USD 2.320** |
| Insumos de ambos (ponderado 61,55 / 38,45) | — | **USD 1.717** |

Elegimos quedarnos cortos a propósito. Subestimar el costo de agotamiento lleva
a stocks de seguridad más chicos, que es el lado incómodo del error, así que si
nos equivocamos preferimos que sea del lado que después se nota. De todos modos
en la sección de sensibilidad vamos a ver exactamente cuánto cambiaría la
decisión si el precio real fuera bastante más alto.

Para los insumos que se montan en los dos vehículos, el costo de agotamiento se
pondera por la proporción histórica de ventas de cada línea, porque un faltante
frena indistintamente la producción de un Clásico o de un Vintage.

### 3.4. La demanda durante el plazo de entrega

El otro parámetro que necesitamos es cuánta demanda hay que cubrir mientras
esperamos el pedido, y con cuánta incertidumbre. Winston lo resuelve en la
ecuación (8), página 891: **E(X) = L · E(D)** y **σ_X = σ_D · √L**.

El desvío se arma en tres pasos, partiendo del error de pronóstico que sacamos
en la etapa anterior: se toma el desvío mensual, se divide por la raíz de 4,33
para llevarlo a base semanal, y se multiplica por la raíz del lead time para
acumularlo sobre todas las semanas de espera. El último paso supone que los
errores de semanas distintas son independientes entre sí, que es exactamente el
supuesto bajo el cual Winston deduce esa ecuación.

Nos queda esta tabla, que es la entrada de todo lo que viene:

| Insumo | E(D) | h | c_B | c_B/h | L (sem.) | E(X) | σ_X |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 565 | 1.800 | 1.340 | 0,74 | 6 | 65,2 | 4,70 |
| Motor de Cilindros en Línea Raro | 353 | 2.400 | 2.320 | 0,97 | 12 | 81,4 | 4,15 |
| Carrocería Artesanal de Época | 353 | 3.000 | 2.320 | 0,77 | 10 | 67,8 | 3,79 |
| Carrocería Estándar (Fibra) | 565 | 1.300 | 1.340 | 1,03 | 4 | 43,4 | 3,84 |
| Tapicería de Cuero Premium | 917 | 800 | 1.717 | 2,15 | 8 | 141,1 | 8,82 |

La columna que conviene mirar es **c_B/h**: cuánto cuesta que falte una unidad
comparado con cuánto cuesta tenerla parada un año. Esa relación es la que va a
gobernar todo el resultado.

---

## 4. Política A — EOQ con Faltantes Admitidos

Esta es la política óptima por costos. No le imponemos ningún nivel de servicio:
dejamos que el modelo elija *q* y *r* minimizando el costo total. Corresponde al
caso de **pedidos pendientes** de la sección 16.6 de Winston.

El libro aproxima la cantidad de pedido por el EOQ y obtiene el punto de
reabastecimiento por análisis marginal. Ecuación (13), página 893:

> **q\* = (2 · K · E(D) / h)^½**
>
> **P(X ≥ r\*) = h · q\* / (c_B · E(D))**

La segunda ecuación tiene una lectura bastante intuitiva. Si subimos el punto de
reabastecimiento en una unidad, pagamos un poco más de almacenamiento pero nos
ahorramos algo de déficit. El óptimo es el punto donde las dos cosas se igualan.
Leída al revés, dice que la probabilidad de quedarse sin stock que conviene
tolerar es más chica cuanto más caro sea el faltante, y más grande cuanto más
caro sea almacenar.

### Ejemplo de cálculo

Se mostrará un ejemplo para el Motor de Alto Rendimiento V8. El resto de los
valores se dejará directamente adjunto como tabla.

```
q*  = (2 × 300 × 565 / 1.800)^½ = 13,72 unidades

P(X ≥ r*) = (1.800 × 13,72) / (1.340 × 565) = 0,0326

z   = Φ⁻¹(1 − 0,0326) = 1,843

r*  = E(X) + z · σ_X = 65,2 + 1,843 × 4,70 = 73,83 unidades

Stock de seguridad = r* − E(X) = 8,67 unidades
```

O sea que pedimos de a 14 motores, y disparamos el pedido cuando quedan 74 en
stock. De esos 74, unos 65 se van a consumir mientras el pedido viaja y los
otros 9 son el colchón por si la demanda viene más fuerte de lo esperado.

El número de pedidos al año es E(D)/q = 565 / 13,72 = 41,2 pedidos, o sea
aproximadamente uno cada nueve días.

### Resultados

| Insumo | q | r | Stock seg. | z | P(X≥r) | Pedidos/año | TC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 13,72 | 73,83 | 8,67 | 1,843 | 0,0326 | 41,2 | 43.620 |
| Motor de Cilindros en Línea Raro | 9,39 | 89,36 | 7,97 | 1,918 | 0,0275 | 37,6 | 45.481 |
| Carrocería Artesanal de Época | 8,40 | 74,92 | 7,09 | 1,869 | 0,0308 | 42,0 | 50.889 |
| Carrocería Estándar (Fibra) | 16,14 | 50,79 | 7,36 | 1,915 | 0,0277 | 35,0 | 32.462 |
| Tapicería de Cuero Premium | 26,23 | 160,69 | 19,56 | 2,217 | 0,0133 | 35,0 | 39.101 |
| **TOTAL** | | | **50,65** | | | | **USD 211.553** |

### ¿Está bien aproximar q por el EOQ?

Winston aproxima la cantidad óptima por el EOQ en lugar de resolver el sistema
completo, y en una nota al pie de la página 893 cita a Brown (1967): la
aproximación es aceptable **salvo que el EOQ sea menor o igual a σ_X**.

Como la advertencia está explícita en el libro, nos pareció que correspondía
verificarla en vez de darla por buena. Resolvimos entonces el sistema exacto por
iteración: se arranca del EOQ, se calcula el *r* que corresponde, con ese *r* se
recalcula *q* incorporando el déficit esperado, y se repite hasta que deja de
moverse. Converge entre 10 y 12 vueltas según el insumo.

| Insumo | σ_X | q (EOQ) | q exacto | Dif. | TC (EOQ) | TC exacto | Dif. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor V8 | 4,70 | 13,72 | 15,73 | +14,6% | 43.620 | 43.393 | −0,52% |
| Motor Raro | 4,15 | 9,39 | 11,16 | +18,8% | 45.481 | 45.151 | −0,73% |
| Carrocería Artesanal | 3,79 | 8,40 | 10,05 | +19,6% | 50.889 | 50.492 | −0,78% |
| Carrocería Estándar | 3,84 | 16,14 | 17,70 | +9,7% | 32.462 | 32.373 | −0,27% |
| Tapicería | 8,82 | 26,23 | 29,55 | +12,6% | 39.101 | 38.954 | −0,38% |

Los cinco insumos cumplen holgadamente la condición de Brown, y aunque la
cantidad de pedido cambia entre un 10% y un 20%, el costo total apenas mejora
**un 0,78% en el peor caso**. La aproximación de Winston es perfectamente válida
acá, así que nos quedamos con ella.

---

## 5. Política B — EOQ Basado en Nivel de Servicio (α = 0,05)

Ahora colocamos los resultados de aplicar una política de stock basada en un
nivel de servicio donde el 95% de los ciclos de reposición no poseen quiebres de
stock. Corresponde a la sección 16.7 de Winston.

La cantidad de pedido es la misma, el EOQ. Lo único que cambia es cómo se fija
el punto de reabastecimiento: en lugar de derivarlo de los costos, le imponemos
al modelo que la probabilidad de quedarse sin stock durante el plazo de entrega
sea del 5%.

```
z = Φ⁻¹(0,95) = 1,6449
r = E(X) + 1,6449 · σ_X
```

| Insumo | q | r | Stock seg. | Pedidos/año | TC |
|---|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 13,72 | 72,89 | 7,74 | 41,2 | 44.042 |
| Motor de Cilindros en Línea Raro | 9,39 | 88,23 | 6,83 | 37,6 | 46.503 |
| Carrocería Artesanal de Época | 8,40 | 74,06 | 6,24 | 42,0 | 51.633 |
| Carrocería Estándar (Fibra) | 16,14 | 49,75 | 6,32 | 35,0 | 32.960 |
| Tapicería de Cuero Premium | 26,23 | 155,65 | 14,51 | 35,0 | 43.665 |
| **TOTAL** | | | **41,64** | | **USD 218.802** |

El costo de déficit se calcula con el mismo c_B que en la Política A, aunque
esta política no lo haya usado para decidir nada. Esto es fundamental para que
la comparación signifique algo: si a cada política la midiéramos con su propia
fórmula, ganaría la que tenga la fórmula más piadosa y no la que administre
mejor el inventario.

---

## 6. Nivel de Servicio Resultante

Una pregunta que vale la pena hacerse es: si la Política A no fija ningún nivel
de servicio, ¿cuál termina alcanzando?

Winston define dos medidas para responder esto (sección 16.7, página 898):

- **SLM₁**: la fracción esperada de toda la demanda que se cumple a tiempo.
- **SLM₂**: el número esperado de ciclos al año durante los cuales se presenta
  un déficit.

| Insumo | c_B/h | P(X ≥ r) | z | SLM₁ | SLM₂ |
|---|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 0,74 | 0,0326 | 1,843 | 99,56% | 1,34 |
| Motor de Cilindros en Línea Raro | 0,97 | 0,0275 | 1,918 | 99,53% | 1,03 |
| Carrocería Artesanal de Época | 0,77 | 0,0308 | 1,869 | 99,46% | 1,29 |
| Carrocería Estándar (Fibra) | 1,03 | 0,0277 | 1,915 | 99,75% | 0,97 |
| Tapicería de Cuero Premium | 2,15 | 0,0133 | 2,217 | 99,84% | 0,47 |

**Ponderando por demanda, la Política A alcanza un SLM₁ del 99,68% y una
probabilidad de agotamiento de 0,0243.**

Y acá está el resultado más interesante de todo el trabajo: **el óptimo
económico termina siendo más conservador que el 95% que le imponíamos a la
Política B**. Con estos costos, cubrirse conviene por sí solo; no hace falta
obligar al modelo a hacerlo.

La lógica se sigue insumo por insumo mirando la columna c_B/h. La Tapicería de
Cuero Premium, que es la que tiene la relación más alta (2,15), es la que
termina con el z más grande (2,217). Es el insumo donde un faltante duele más en
relación a lo que cuesta guardarlo, así que el modelo decide cubrirse más.

---

## 7. Comparación de las Dos Políticas

Como las dos políticas piden el mismo *q*, la comparación aísla exactamente lo
único que las diferencia: dónde ponen el punto de reabastecimiento.

| Concepto | Política A | Política B | Diferencia |
|---|---:|---:|---:|
| Costo de pedidos | 57.199 | 57.199 | 0 |
| Costo de almacenamiento | 138.414 | 126.068 | +12.346 |
| Costo de déficit | 15.939 | 35.535 | −19.596 |
| **TC(q, r)** | **211.553** | **218.802** | **−7.250** |
| Costo de compra (fuera de TC) | 21.944.702 | 21.944.702 | 0 |
| Costo total | 22.156.254 | 22.163.504 | −7.250 |

Insumo por insumo:

| Insumo | Stock seg. A | Stock seg. B | SLM₁ A | SLM₁ B | TC A | TC B | Dif. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Motor V8 | 8,67 | 7,74 | 99,56% | 99,28% | 43.620 | 44.042 | +1,0% |
| Motor Raro | 7,97 | 6,83 | 99,53% | 99,08% | 45.481 | 46.503 | +2,2% |
| Carrocería Artesanal | 7,09 | 6,24 | 99,46% | 99,06% | 50.889 | 51.633 | +1,5% |
| Carrocería Estándar | 7,36 | 6,32 | 99,75% | 99,50% | 32.462 | 32.960 | +1,5% |
| Tapicería | 19,56 | 14,51 | 99,84% | 99,30% | 39.101 | 43.665 | +11,7% |

**La Política A ahorra USD 7.250 al año**, un 3,3% del costo controlable de
inventario.

Hay dos observaciones que conviene hacer sobre este resultado.

**La primera es que la Política A no ahorra en todo: reasigna.** Gasta USD 12.346
más en almacenamiento y USD 19.596 menos en déficit. Es exactamente la
transacción entre costo de almacenamiento y costo de déficit que Winston
ilustra en la figura 4 de la página 894: al llevar más stock de seguridad se
paga más por conservarlo, pero se evita proporcionalmente más en compensaciones
a los clientes.

**La segunda es que el 95% de la Política B protege menos de lo que aparenta.**
Es un objetivo por cada ciclo de reposición. Con 35 a 42 reposiciones al año, un
5% de riesgo por ciclo se traduce en un SLM₂ de entre 1,75 y 2,10 quiebres de
stock anuales. La Política A, al tolerar una probabilidad de entre 0,013 y 0,033,
baja ese número al rango de 0,47 a 1,34.

Un último comentario sobre por qué el costo de compra va aparte. Si lo
incluyéramos, la diferencia entre las dos políticas sería del 0,03% sobre el
total, y cualquier diferencia de gestión quedaría completamente tapada por un
término que es idéntico en ambos casos. Por eso Winston lo excluye de TC(q, r),
y por eso lo reportamos aparte.

Para tener la referencia completa: si en lugar de los cinco insumos de Categoría
A tomáramos los once del catálogo, el costo controlable sería de USD 323.148
para la Política A y USD 360.327 para la B.

---

## 8. Capacidad Mínima de Almacén

En pos de la necesidad operacional de la empresa de entender qué necesidad de
espacio en almacén tendrá que satisfacer, se propone lo siguiente.

### 8.1. El espacio teórico necesario

Primero hay que definir cuánto stock hay que guardar realmente. En un sistema
(r, q) el inventario físico llega a su máximo justo en el momento en que entra
un pedido, y en ese instante vale:

> **Inventario máximo = q + (r − E(X))**

O sea, el lote que acaba de llegar más el stock de seguridad que todavía quedaba.
Sale de la misma cuenta que hace Winston en la página 892 al construir la
ecuación (11).

Es importante no sumarle el punto de reabastecimiento completo. La demanda del
plazo de entrega que *r* cubre se va consumiendo mientras el pedido está en
camino, así que nunca está toda junta en el estante. Y además *r* ya lleva el
stock de seguridad adentro, con lo cual sumarlo otra vez sería contarlo dos
veces.

Acá tomamos los **once insumos del catálogo** y no solo los cinco de Categoría
A. La razón es sencilla: los modelos de inventario se aplican sobre la Categoría
A porque ahí está concentrado el valor, pero el depósito tiene que guardar todo
lo que entra.

| Insumo | Volumen unit. | Inv. máx. A | m³ A | Inv. máx. B | m³ B |
|---|---:|---:|---:|---:|---:|
| Motor de Alto Rendimiento V8 | 0,80 | 22,4 | 17,9 | 21,5 | 17,2 |
| Motor de Cilindros en Línea Raro | 0,90 | 17,4 | 15,6 | 16,2 | 14,6 |
| Carrocería Artesanal de Época | 4,00 | 15,5 | 62,0 | 14,6 | 58,6 |
| Carrocería Estándar (Fibra) | 3,50 | 23,5 | 82,2 | 22,5 | 78,6 |
| Transmisión de 5 Velocidades | 0,40 | 42,0 | 16,8 | 38,3 | 15,3 |
| Sistema de Inyección Electrónica | 0,10 | 45,1 | 4,5 | 43,0 | 4,3 |
| Set de Carburadores Dobles | 0,10 | 40,8 | 4,1 | 38,7 | 3,9 |
| Tapicería de Cuero Premium | 0,50 | 45,8 | 22,9 | 40,7 | 20,4 |
| Juego de Llantas Vintage Espec. | 0,15 | 67,9 | 10,2 | 58,8 | 8,8 |
| Llantas Regulares Cromados | 0,10 | 159,5 | 16,0 | 148,0 | 14,8 |
| Cubiertas de Alta Gama | 0,10 | 261,6 | 26,2 | 238,9 | 23,9 |
| **TOTAL** | | | **278,3 m³** | | **260,3 m³** |

El total suma el máximo de cada insumo por separado. Es un criterio conservador,
porque en la práctica los picos no van a caer todos el mismo día: cada insumo
tiene su propio plazo de entrega y su propio ciclo. Pero para dimensionar un
galpón conviene errar por exceso.

La **Capacidad Mínima Teórica** para la Política A es entonces de **279 m³**.

### 8.2. Del espacio teórico al galpón real

Sin embargo, esto no es cierto de manera física. En un almacén no todos los
productos entran directamente uno perfectamente al lado del otro, ya que se
necesitan espacios operacionales.

Para calcular esto se hizo uso del Manual de Buenas Prácticas emitido desde el
gobierno de la nación, exactamente la Superintendencia de Riesgos del Trabajo.
En el mismo se establecen muchas características que debe cumplir un almacén de
una industria como la que estamos tratando. Entre dichas características se
encuentran los espacios requeridos:

- Pasillos de circulación
- Zonas de carga y descarga
- Áreas de maniobra
- Espacios libres por seguridad
- Limitaciones de altura útil

Como el fin de nuestro análisis no es recomendar prácticas de trabajo dentro del
almacén, ni se sabe correctamente por parte del equipo con qué tipos de
maquinaria se cuenta o se contará, entregaremos dos planteos posibles sobre la
Capacidad Mínima Requerida.

Según un reporte de NetSuite (Warehouse Space Utilization: How to Calculate and
Optimize, Abby Jenkins), las empresas suelen utilizar entre el 45% y el 85% del
espacio total de almacén. Tomamos dos escenarios dentro de ese rango, con una
altura útil de 5 metros, que es lo estándar para un galpón industrial con
estantería.

**Capacidad Mínima de Almacén Conservadora.** Suponiendo una utilización del 65%
del espacio:

```
CMAC = 279 m³ / 0,65 ≈ 428 m³
```

Esto permite una distribución recomendada de 15 m de largo, 6 m de ancho y 5 m
de alto (450 m³, superficie de 90 m²).

**Capacidad Mínima de Almacén Óptima.** Si la empresa se compromete a manejar de
la mejor manera posible sus productos, quizás ese 35% de desperdicio pueda
minimizarse a un 25%:

```
CMAO = 279 m³ / 0,75 ≈ 371 m³
```

Lo cual se podría alcanzar con un almacén de 13 m de largo, 6 m de ancho y 5 m
de alto (390 m³, superficie de 78 m²).

Resulta fácil realizar un recálculo de lo anterior si la organización encuentra
otra forma que considere más apropiada para construir su almacén. Lo que nunca
se podrá hacer es trabajar por debajo de la Capacidad Mínima Teórica de 279 m³.

### 8.3. Costos de construcción

Se facilita de manera breve un cálculo rápido a modo de ayuda del costo de
construcción de cada una de las opciones suministradas. El costo exacto de cada
caso, si estos fueran a llevarse a cabo, debería precisarse en detalle. No se
realiza ahora mismo ya que escapa del alcance inicial, que trata solo sobre el
dimensionamiento. Se toma un valor de referencia de USD 1.500 por m².

| Política | Escenario | Utilización | Volumen | Superficie | Costo de obra |
|---|---|---:|---:|---:|---:|
| A | Conservador | 65% | 428 m³ | 86 m² | **USD 128.464** |
| A | Óptimo | 75% | 371 m³ | 74 m² | USD 111.336 |
| B | Conservador | 65% | 400 m³ | 80 m² | USD 120.141 |
| B | Óptimo | 75% | 347 m³ | 69 m² | USD 104.123 |

### 8.4. ¿Alguna política es inviable por el espacio?

Acá aparece algo que no esperábamos: la política más barata **no** es la que
menos espacio necesita.

La Política A pide 18 m³ más que la B, un 6,9%, porque lleva más stock de
seguridad. En el escenario conservador eso significa **USD 8.323 adicionales de
obra**.

Pero hay que comparar sobre el mismo horizonte. Ese sobrecosto de obra se paga
**una sola vez**, mientras que la diferencia de costo operativo —los USD 7.250
que ya vimos— se repite **todos los años**. La inversión adicional se recupera
en poco más de un año y a partir de ahí es ahorro neto.

**Las dos políticas son factibles y la restricción de capacidad no cambia la
recomendación.**

Una última aclaración sobre el alcance. Este número cubre el inventario de
insumos, que es lo que pide el estudio. Un depósito en operación real necesita
además lugar para material en proceso, para vehículos terminados esperando
entrega y para devoluciones. Y si algún proveedor impone un lote mínimo de
compra, habría que recibir más de lo que dice el modelo. Así que conviene leer
la cifra como un piso para el sector de insumos, no como el tamaño total del
edificio.

---

## 9. Análisis de Sensibilidad

### 9.1. Sensibilidad al Costo de Agotamiento (±30%)

El costo de agotamiento es el parámetro más discutible de todo el modelo, porque
lo tuvimos que derivar de un precio de venta que el enunciado no nos da. Así que
corresponde ver qué pasaría si ese número estuviera mal.

Un punto importante del procedimiento: no alcanza con recalcular el costo
dejando la política fija. Lo que hicimos fue **volver a resolver la ecuación
(13) con cada valor de c_B**, porque si el costo de agotamiento sube, el modelo
elige un punto de reabastecimiento más alto, y ese reajuste es justamente lo que
interesa medir.

| Escenario | q prom. | Stock seg. | Déficit anual | TC total | Δ TC | P(X≥r) | SLM₁ |
|---|---:|---:|---:|---:|---:|---:|---:|
| c_B − 30% | 14,78 | 46,71 | 13,36 | 205.724 | −2,76% | 0,0377 | 99,44% |
| c_B base | 14,78 | 50,65 | 8,89 | 211.553 | — | 0,0264 | 99,63% |
| c_B + 30% | 14,78 | 53,40 | 6,61 | 215.663 | +1,94% | 0,0203 | 99,72% |

Las conclusiones son tres.

Una variación de ±30% en el costo de agotamiento mueve el costo total apenas
entre −2,76% y +1,94%. El modelo absorbe buena parte del error reajustando la
política, así que el resultado es bastante robusto frente a la incertidumbre de
este parámetro.

**La cantidad de pedido no se mueve en absoluto.** Esto se lee directo en la
ecuación (13): el EOQ no depende de c_B. Todo el ajuste pasa por el punto de
reabastecimiento, que hace subir el stock de seguridad de 46,71 a 53,40 unidades.

Y lo más importante: aun en el escenario más desfavorable, con el costo de
agotamiento un 30% por debajo de lo que estimamos, la probabilidad de quedarse
sin stock (0,0377) sigue estando **por debajo del 0,05 exigido a la Política B**.
La recomendación no cambia.

### 9.2. Sensibilidad al Riesgo (+15% de incertidumbre)

Luego se evaluó qué pasa con la existencia de una mayor incertidumbre en la
demanda, en este caso del 15%. Es decir, qué pasa si el mercado se vuelve más
volátil y el pronóstico empieza a fallar más de lo que falla hoy.

| Política | Stock seg. base | Stock seg. +15% | Δ SS | TC base | TC +15% | Δ TC |
|---|---:|---:|---:|---:|---:|---:|
| A | 50,65 | 58,24 | **+15,00%** | 211.553 | 226.126 | +6,89% |
| B | 41,64 | 47,89 | **+15,00%** | 218.802 | 234.463 | +7,16% |

Como el stock de seguridad es z · σ_X, un 15% más de incertidumbre obliga a un
15% más de stock de seguridad **en las dos políticas**, solamente para sostener
el mismo nivel de protección que se tenía antes.

Lo llamativo es que **ninguna de las dos tiene margen para reaccionar de otra
manera**, y el motivo es que ningún z depende de σ_X. El de la Política B está
clavado en 1,645 porque se lo fija el enunciado; el de la Política A sale de
P(X ≥ r*) = h·q*/(c_B·E(D)), expresión donde σ_X directamente no aparece. Y
tampoco se mueve la cantidad de pedido, porque el EOQ tampoco depende de σ_X.

O sea que toda la incertidumbre adicional se paga con stock inmovilizado, sin
posibilidad de compensarla por otro lado. Esta es la demostración concreta de
que la volatilidad del mercado se traduce directa y proporcionalmente en capital
parado en el depósito.

En plata, la Política A se encarece un 6,89% (USD 14.573) y la B un 7,16%
(USD 15.661). La Política A aguanta un poco mejor, porque parte de un stock de
seguridad más alto y entonces el déficit adicional que genera la volatilidad es
menor.

---

## 10. Recomendación Final

Una vez obtenida toda la información anterior, **recomendamos a la organización
inclinarse por la Política A**, la de faltantes admitidos, que fija el punto de
reabastecimiento por criterio económico en lugar de imponerle un nivel de
servicio.

Los motivos son cuatro.

**Es más barata.** USD 211.553 al año contra USD 218.802 de la Política B, o sea
un ahorro de USD 7.250 anuales sobre el costo controlable de inventario.

**Da mejor servicio.** Su probabilidad de quedarse sin stock resulta de 0,0243
frente al 0,05 que impone la Política B, y entrega el 99,68% de la demanda a
tiempo. La cantidad de quiebres de stock anuales baja del rango 1,75-2,10 al
rango 0,47-1,34. El óptimo económico termina siendo más prudente que la
restricción de servicio que le queríamos imponer, que es un resultado que a
nosotros mismos nos sorprendió.

**Es más robusta.** Frente a un error del 30% en el costo de agotamiento su
costo se mueve menos del 2%, y frente a un 15% más de volatilidad se encarece
menos que la Política B.

**Es factible.** Necesita 18 m³ más de almacén, una diferencia que se amortiza
en poco más de un año.

Sobre la implementación, hay un punto que conviene mencionar. El modelo indica
entre 35 y 42 reposiciones anuales por insumo, aproximadamente una por semana.
Con estos volúmenes, y con un costo de conservación que es alto comparado con lo
que cuesta emitir un pedido, el óptimo económico es reponer seguido. En la
práctica esto no significa emitir cuarenta órdenes de compra sueltas por año,
sino cerrar un acuerdo de entregas programadas con cada proveedor.

**Para el almacén se propone construir 428 m³**, unos 86 m² con 5 metros de
altura útil, con una inversión estimada de **USD 128.464**.

Elegimos el escenario conservador de utilización (65%) y no el de 75% por dos
razones. La primera es que deja margen operativo para el pico de octubre y
noviembre, que como vimos casi triplica la demanda mensual promedio. La segunda
es que absorbe el crecimiento que el propio pronóstico está anticipando.

La altura útil de 5 metros también es una decisión. Una altura mayor reduciría
la superficie necesaria, pero obligaría a equipos de elevación más caros y
complicaría la operación del día a día sin un beneficio claro a esta escala. El
largo y el ancho pueden ajustarse a comodidad de la empresa siempre que se
respete el volumen mínimo.

### Limitaciones del estudio

Nos parece honesto dejar registradas tres cosas que quedaron fuera del alcance o
apoyadas en supuestos.

**El precio de venta de los vehículos es un supuesto.** El costo de agotamiento
lo derivamos del costo de materiales como piso. El análisis de sensibilidad
muestra que la recomendación se sostiene igual, pero tener el precio real
permitiría afinar los puntos de reabastecimiento.

**El pronóstico proyecta crecimiento.** Prophet anticipa 917 vehículos contra un
promedio histórico de 639. Si ese crecimiento no se materializa, los lotes y los
stocks de seguridad quedarían sobredimensionados. Convendría revisar el
pronóstico cada tres meses.

**Los plazos de entrega se tomaron como fijos.** El enunciado los da así.
Winston señala en la página 895 que un plazo de entrega variable puede más que
duplicar el stock de seguridad necesario. Si en la práctica los proveedores
tienen variabilidad de entrega, el modelo debería extenderse con la ecuación (8')
del texto, que incorpora la varianza del plazo.

---

## Bibliografía

**Winston, W. L.** *Investigación de Operaciones: Aplicaciones y Algoritmos*,
4.ª edición. Thomson.
- Capítulo 15: modelos determinísticos de inventario.
- Capítulo 16, sección 16.6: "La EOQ con demanda incierta: modelos (r, q) y
  (s, S)", págs. 890-897. Ecuación (8) para la demanda durante el plazo de
  entrega, ecuación (11) para el costo anual esperado y ecuación (13) para el
  caso de pedidos pendientes.
- Capítulo 16, sección 16.7: "La EOQ con demanda incierta: método del nivel de
  servicio para determinar el nivel de existencias de seguridad", pág. 898.
  Definiciones de SLM₁ y SLM₂.

**Hadley, G. y Whitin, T. M.** *Analysis of Inventory Systems*. Prentice-Hall,
1963.

**Brown, R. G.** *Decision Rules for Inventory Management*, 1967. Citado por
Winston en la pág. 893 para la validez de aproximar la cantidad óptima de pedido
por el EOQ.

**Silver, E. A., Pyke, D. F. y Peterson, R.** *Inventory Management and
Production Planning and Scheduling*, 3.ª edición. Wiley. Capítulo 7, función de
pérdida normal.

**Taylor, S. J. y Letham, B.** *Forecasting at Scale* (paper original de
Prophet). https://peerj.com/preprints/3190/

**Vilorio Luque, J. O.** *Predicciones de Ventas con Series Temporales*, pág. 27.
https://www.uhu.es/mecofin/docencia/tfm/20222023/

**Reyes, C. e Inca, C.** *Limitaciones del Modelo LSTM en la Predicción de
Demanda Eléctrica con Datos Simulados de Bajo Volumen*.
https://magazineasce.com/index.php/1/article/view/131

**Miranda Chinlli, C. M.** *Modelización de Series Temporales: modelos clásicos
y SARIMA* (bajo número de observaciones en SARIMA).
https://masteres.ugr.es/estadistica-aplicada/sites/master/moea/public/inline-files/TFM_MIRANDA_CHINLLI_CARLOS.pdf

**Superintendencia de Riesgos del Trabajo.** *Manual de Buenas Prácticas —
Industria Automotriz*, 2025/2026.
https://www.argentina.gob.ar/sites/default/files/mbp_industria-automotriz_0_corregido.pdf

**Jenkins, A.** *Warehouse Space Utilization: How to Calculate and Optimize*.
NetSuite.
https://www.netsuite.com/portal/resource/articles/inventory-management/space-utilization-warehouse.shtml

**Repositorio del trabajo:** https://github.com/JuanBrun/RepoProyectoIO

---

## Anexo — Reproducibilidad

Todos los cálculos de este informe se generan con el código del repositorio
mediante un único comando:

```
make todo
```

Las etapas también pueden ejecutarse por separado (`make pronostico`,
`make inventario`, `make almacen`, `make sensibilidad`). Los resultados quedan
en la carpeta `outputs/` como archivos CSV y gráficos.

| Sección del informe | Dónde están los resultados |
|---|---|
| 1.1 Limpieza de datos | `data/processed/` |
| 1.2 y 1.3 ABC y XYZ | `outputs/clasificacion/` |
| 2 Pronóstico | `outputs/pronostico/` |
| 3 a 7 Modelos de inventario | `outputs/inventario/` |
| 8 Almacén | `outputs/almacen/` |
| 9 Sensibilidad | `outputs/sensibilidad/` |
