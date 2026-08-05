"""Modelos de inventario. Solo matematica, sin leer ni escribir archivos.

Todo este modulo sigue el capitulo 16 de Winston, "Modelos probabilisticos de
inventarios", y en particular las secciones 16.6 y 16.7. Se respeta su notacion
para que las formulas del informe se puedan seguir contra el libro.


NOTACION (Winston, seccion 16.6)
--------------------------------
  E(D)     demanda anual esperada
  K        costo de hacer un pedido
  h        costo de conservar una unidad en inventario un anio
  c_B      costo por unidad de deficit (caso de pedidos pendientes)
  L        plazo de entrega
  X        variable aleatoria: demanda durante el plazo de entrega
  E(X)     demanda media durante el plazo de entrega
  sigma_X  desvio de la demanda durante el plazo de entrega
  q        cantidad de pedido
  r        punto de reabastecimiento
  B_r      variable aleatoria: deficit durante un ciclo si el reorden es r
  E(B_r)   deficit esperado por ciclo

El stock de seguridad es r - E(X) (Winston, pag. 894, observacion 2).


EL SISTEMA (r, q)
-----------------
Se pide siempre la misma cantidad q y se dispara el pedido cuando el nivel de
existencias baja hasta r. El pedido tarda L en llegar. Lo que falte durante ese
plazo queda como pedido pendiente y cuesta c_B por unidad, que en este caso es
la compensacion del 5% al cliente por la demora.

Winston, ecuacion (11), pag. 892:

    TC(q, r) = h*(q/2 + r - E(X)) + c_B*E(B_r)*E(D)/q + K*E(D)/q
               \_______________/   \________________/   \_______/
                 almacenamiento          deficit          pedidos

El costo de compra queda deliberadamente afuera. No es una decision propia: es
como Winston define TC(q, r), "costo anual esperado (sin incluir costo de
compra)". Tiene sentido, porque se compra la misma cantidad al mismo precio
gobierne quien gobierne el inventario, asi que incluirlo solo diluiria la
comparacion entre politicas.


LAS DOS POLITICAS
-----------------
Las dos usan q* = EOQ y se diferencian unicamente en como fijan r:

  Politica A - pedidos pendientes (seccion 16.6, ecuacion 13)
      r sale de igualar el beneficio marginal de subir el reorden con su costo
      marginal:  P(X >= r*) = h*q* / (c_B*E(D))
      El nivel de servicio no se impone: queda determinado por los costos.

  Politica B - nivel de servicio (seccion 16.7)
      r sale de fijar la probabilidad de agotamiento en alfa = 0.05, o sea que
      el 95% de los ciclos terminen sin deficit.

Que las dos compartan q no es una simplificacion nuestra: Winston (pag. 893)
muestra que el q* que resuelve el sistema exacto de condiciones de primer orden
queda muy cerca del EOQ, y por eso lo aproxima asi. La funcion
resolver_exacto() de mas abajo verifica que en este caso sea cierto.
"""

import math

from scipy.stats import norm


# --- Piezas basicas -----------------------------------------------------------

def eoq(E_D, K, h):
    """EOQ de Wilson: q* = (2*K*E(D)/h)^(1/2).  Winston, ecuacion (13)."""
    if E_D <= 0 or h <= 0:
        return 0.0
    return math.sqrt(2.0 * K * E_D / h)


def perdida_normal(z):
    """Funcion de perdida normal estandar:  L(z) = phi(z) - z*(1 - Phi(z)).

    Devuelve el deficit esperado medido en desvios, cuando el punto de
    reabastecimiento esta z desvios por encima de E(X). El deficit esperado por
    ciclo es entonces E(B_r) = sigma_X * L(z).

    Winston resuelve sus ejemplos leyendo r de la normal y no necesita esta
    funcion de forma explicita, pero hace falta para evaluar el termino de
    deficit de la ecuacion (11). Es la formulacion estandar (Silver, Pyke y
    Peterson, cap. 7).
    """
    return float(norm.pdf(z) - z * (1.0 - norm.cdf(z)))


def deficit_por_ciclo(sigma_X, z):
    """E(B_r): unidades que se espera no poder entregar en cada ciclo."""
    return sigma_X * perdida_normal(z)


def costo_total(E_D, K, h, c_B, q, z, sigma_X):
    """TC(q, r) segun Winston, ecuacion (11), pag. 892.

    El termino de almacenamiento usa r - E(X) = z*sigma_X, que es el stock de
    seguridad.
    """
    if q <= 0:
        return float("nan")
    stock_seguridad = z * sigma_X
    E_Br = deficit_por_ciclo(sigma_X, z)
    return (
        h * (q / 2.0 + stock_seguridad)      # almacenamiento
        + c_B * E_Br * E_D / q               # deficit
        + K * E_D / q                        # pedidos
    )


def indicadores(E_D, K, h, c_B, q, z, sigma_X, E_X):
    """Arma el diccionario de resultados comun a las dos politicas."""
    E_Br = deficit_por_ciclo(sigma_X, z)
    pedidos = E_D / q if q > 0 else float("nan")
    prob_agotamiento = float(1.0 - norm.cdf(z))

    return {
        "q": q,
        "r": E_X + z * sigma_X,
        "z": z,
        "Stock_Seguridad": z * sigma_X,          # r - E(X)
        "P_Agotamiento": prob_agotamiento,       # P(X >= r)
        "E_Br": E_Br,                            # deficit esperado por ciclo
        "Pedidos_Anio": pedidos,
        "Dias_Entre_Pedidos": 365.0 / pedidos if pedidos > 0 else float("nan"),
        "Deficit_Anual": pedidos * E_Br,

        # Medidas de nivel de servicio (Winston, seccion 16.7)
        # SLM1: fraccion esperada de la demanda que se cumple a tiempo.
        #   Del deficit anual (E(D)/q)*E(B_r) sobre la demanda E(D) queda
        #   directamente 1 - E(B_r)/q.
        "SLM1": 1.0 - E_Br / q if q > 0 else float("nan"),
        # SLM2: numero esperado de ciclos al anio con deficit.
        "SLM2": pedidos * prob_agotamiento,

        # Descomposicion de la ecuacion (11)
        "Costo_Almacenamiento": h * (q / 2.0 + z * sigma_X),
        "Costo_Deficit": c_B * E_Br * E_D / q if q > 0 else float("nan"),
        "Costo_Pedidos": K * E_D / q if q > 0 else float("nan"),
        "TC": costo_total(E_D, K, h, c_B, q, z, sigma_X),
    }


# --- Politica A: pedidos pendientes (Winston 16.6, ecuacion 13) ---------------

def politica_pedidos_pendientes(E_D, K, h, c_B, E_X, sigma_X):
    """(q, r) optimo por costos para el caso de pedidos pendientes.

    Winston, ecuacion (13), pag. 893:

        q*         = (2*K*E(D)/h)^(1/2)
        P(X >= r*) = h*q* / (c_B*E(D))

    La segunda ecuacion sale del analisis marginal: subir el reorden en delta
    cuesta h*delta de almacenamiento extra y ahorra delta*E(D)*c_B*P(X>=r)/q de
    deficit. El optimo iguala las dos cosas.

    Leido al reves, dice algo intuitivo: la probabilidad de agotamiento que
    conviene tolerar es tanto menor cuanto mas caro sea el deficit (c_B grande)
    y tanto mayor cuanto mas caro sea almacenar (h grande).

    Si h*q*/(c_B*E(D)) > 1 la ecuacion no tiene solucion, porque almacenar sale
    tan caro frente al deficit que al modelo le conviene no llevar stock de
    seguridad. Winston (pag. 894) indica fijar en ese caso el reorden en el
    nivel mas bajo aceptable; aca se toma z = 0, o sea reponer justo en la
    demanda media del plazo de entrega.
    """
    q = eoq(E_D, K, h)

    prob_agotamiento = h * q / (c_B * E_D) if c_B * E_D > 0 else 1.0
    if prob_agotamiento >= 1.0:
        z = 0.0
    else:
        z = float(norm.ppf(1.0 - prob_agotamiento))

    resultado = indicadores(E_D, K, h, c_B, q, z, sigma_X, E_X)
    resultado["Politica"] = "A - Pedidos pendientes"
    return resultado


# --- Politica B: nivel de servicio (Winston 16.7) -----------------------------

def politica_nivel_servicio(E_D, K, h, c_B, E_X, sigma_X, nivel_servicio):
    """(q, r) con la probabilidad de agotamiento fijada por enunciado.

    q* sale del EOQ, igual que en la Politica A. r sale de imponer
    P(X >= r) = alfa = 0.05, o sea z = Phi^-1(0.95) = 1.645, de modo que el 95%
    de los ciclos terminen sin deficit.

    El costo de deficit se calcula igual que en la Politica A, con el mismo c_B,
    aunque esta politica no lo haya usado para decidir. Es imprescindible para
    que la comparacion sea justa: las dos se miden con la misma TC(q, r) de la
    ecuacion (11), y lo unico que cambia es como eligieron r.
    """
    q = eoq(E_D, K, h)
    z = float(norm.ppf(nivel_servicio))

    resultado = indicadores(E_D, K, h, c_B, q, z, sigma_X, E_X)
    resultado["Politica"] = f"B - Nivel de servicio {nivel_servicio:.0%}"
    return resultado


# --- Verificacion: solucion exacta del sistema (12) ---------------------------

def resolver_exacto(E_D, K, h, c_B, E_X, sigma_X, tolerancia=1e-8, max_iter=200):
    """Resuelve q y r simultaneamente, sin aproximar q por el EOQ.

    Winston aproxima q* = EOQ porque el q que resuelve el sistema exacto de
    condiciones de primer orden (su ecuacion 12) queda cerca. Esta funcion
    resuelve ese sistema para comprobar que la aproximacion sea buena en este
    caso concreto, en vez de darlo por sentado.

    Derivando TC(q, r) respecto de cada variable e igualando a cero:

        dTC/dq = 0  ->  q = (2*E(D)*(K + c_B*E(B_r)) / h)^(1/2)
        dTC/dr = 0  ->  P(X >= r) = h*q / (c_B*E(D))

    Cada incognita aparece dentro de la otra, asi que no hay despeje cerrado.
    Se itera desde el EOQ: se calcula el r que corresponde, con ese r se
    recalcula q, y se repite hasta que q deja de moverse. Converge rapido
    porque cada paso corrige menos que el anterior.

    El unico cambio respecto de la ecuacion (13) es que el costo de ordenar
    lleva sumado c_B*E(B_r): cada ciclo arrastra su propio deficit, asi que
    conviene hacer ciclos algo mas largos que el EOQ puro.

    La nota al pie de Winston en la pag. 893 cita a Brown (1967): la
    aproximacion por EOQ es aceptable salvo que EOQ <= sigma_X. Por eso la
    funcion tambien devuelve esa comparacion.
    """
    q = eoq(E_D, K, h)
    z = 0.0
    iteraciones = 0

    for iteraciones in range(1, max_iter + 1):
        prob_agotamiento = q * h / (c_B * E_D) if c_B * E_D > 0 else 1.0
        z_nuevo = 0.0 if prob_agotamiento >= 1.0 else float(norm.ppf(1.0 - prob_agotamiento))

        E_Br = deficit_por_ciclo(sigma_X, z_nuevo)
        q_nuevo = math.sqrt(2.0 * E_D * (K + c_B * E_Br) / h)

        convergio = abs(q_nuevo - q) < tolerancia and abs(z_nuevo - z) < tolerancia
        q, z = q_nuevo, z_nuevo
        if convergio:
            break

    resultado = indicadores(E_D, K, h, c_B, q, z, sigma_X, E_X)
    resultado["Politica"] = "A - Solucion exacta (verificacion)"
    resultado["Iteraciones"] = iteraciones
    resultado["EOQ_mayor_que_sigma_X"] = eoq(E_D, K, h) > sigma_X
    return resultado
