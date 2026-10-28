# Modelo matemático y correspondencia informática

## Objetivo acordado

Atender todos los pozos con igual valor, minimizando el tiempo de terminación del tratamiento completo. Cada perforación dura el mismo T. Otras fases pueden diferir por pozo. Los auxiliares tienen rutas independientes y propiedades individuales. Los ensayos de bombeo se incluyen como una fase adicional con duración configurable.

No se pretende optimizar extracción permanente de salmuera, producción química ni transporte de mineral.

## Conjuntos y parámetros

- P: pozos, con coordenada fija p_i.
- D: perforadoras; A_s: auxiliares del tipo de servicio s.
- E: siete fases ordenadas: preparación, perforación, acondicionamiento, montaje de ensayo, bombeo, recuperación, desmontaje.
- d_ie: duración de fase; d_i,perforación = T para todo i.
- o_u, a_u: ubicación y disponibilidad iniciales de cada unidad u.
- tau_u(x,y): tiempo de traslado por unidad. El concepto no exige simetría ni distancia euclidiana.
- R_a, K_a, Q_a: alcance, máximo de atenciones simultáneas y capacidad física de auxiliar a.
- g_s: demanda física de un servicio, editable (kW, m³/min, m³/h o unidades según servicio).
- sigma_u, delta_u: conexión y desconexión adicionales.
- Omega_a: región donde puede instalarse el auxiliar. En la demo es un rectángulo sintético.

En el cálculo actual se usa un conjunto J_ia de posiciones candidatas factibles para auxiliar a y pozo i. La cobertura usa distancia euclidiana local; el viaje puede ser recto u ortogonal. Ambas son hipótesis de DEMOSTRACIÓN, no datos de Novandino.

## Variables

- b_ie, f_ie: inicio y fin de fase.
- y_di binaria: asignación de perforadora d a pozo i.
- x_igaj binaria: servicio del grupo de fases consecutivas g del pozo i asignado a auxiliar a en j.
- v_u binaria: unidad u utilizada.
- o_kl binaria: precedencia entre dos reservas incompatibles k y l de la misma unidad.
- Cmax: terminación del tratamiento y liberación de todos los equipos.

El concepto de posición libre es q_ak en Omega_a. Esta versión sustituye esa búsqueda continua por la elección entre J_ia; no se confunde esa aproximación con el problema original.

## Duraciones, precedencias y asignación

    f_ie = b_ie + d_ie
    b_i,e+1 >= f_ie
    sum_d y_di = 1
    sum_(a,j) x_igaj = 1

La implementación añade igualdad entre fases consecutivas de construcción (0–2) y entre las del ensayo (3–6): son bloques no interrumpibles. Entre construcción y ensayo se permite espera. Un mismo servicio en fases consecutivas se agrupa y mantiene el mismo equipo/posición. Esta es una restricción adicional explícita de v0.1.

La perforadora ocupa [b_i0 - sigma_d, f_i2 + delta_d). El apoyo al grupo g ocupa [b_i,min(g) - sigma_a, f_i,max(g) + delta_a). La capacidad queda reservada durante conexión y desconexión. Montajes del proceso y tiempos adicionales son distintos; los adicionales de la perforadora y equipo de ensayo parten en cero para evitar doble conteo.

## Movimiento independiente

Si dos reservas k y l del mismo equipo se hacen en posiciones distintas:

    inicio_l >= fin_k + tau_u(q_k,q_l)
    O BIEN
    inicio_k >= fin_l + tau_u(q_l,q_k)

La disyunción se activa solo cuando ambas reservas están elegidas. La primera llegada también respeta:

    inicio_k >= a_u + tau_u(o_u,q_k)

Las reservas de un mismo auxiliar pueden coincidir si comparten posición y tienen capacidad suficiente. La perforadora, camión y equipo de ensayo tienen ocupación exclusiva. Con las métricas demo (que cumplen desigualdad triangular), estas restricciones por pares permiten reconstruir una ruta cronológica sin teletransportes. Una métrica general que no cumpla esa condición requiere reemplazar este esquema por arcos de sucesión inmediata; no basta cargar números arbitrarios.

`optimizer.extract` agrupa reservas consecutivas en la misma posición y genera eventos: no disponible, espera, viaje, conexión/desconexión, servicio, reserva durante recuperación, entrega y recarga. Los viajes se programan justo antes de la llegada requerida. Quedarse en una coordenada durante una espera no significa que el equipo siga ocupado.

## Cobertura y capacidades

    x_igaj = 1 => cobertura_a(j,p_i) = verdadero
    sum_k activa_ak(t) <= K_a
    sum_k g_k activa_ak(t) <= Q_a

Las restricciones `Cumulative` de CP-SAT se imponen por equipo y controlan la capacidad a lo largo de todo el intervalo, no únicamente en el comienzo. Un generador requiere ambas restricciones: cantidad simultánea y potencia total.

Un servicio se asigna entero a una unidad; v0.1 no divide la demanda entre varios generadores ni cambia de auxiliar a mitad de fase. Para bombeo de prueba la ubicación es el mismo pozo y la ocupación es exclusiva. El rango cero es válido.

## Agua: caso simplificado explícito

Cada pozo cuenta con un tanque fijo inicialmente vacío, capacidad V_i, y demanda total W_i consumida uniformemente durante la perforación. Se hace una entrega completa antes de b_i,perforación:

    fin_entrega_i <= b_i,perforación
    W_i <= V_i
    W_i <= capacidad_camión_asignado

El inventario sube a W_i al finalizar la entrega y baja linealmente a cero durante T. Por construcción 0 <= inventario_i(t) <= V_i. No se implementa un flujo instantáneo continuo durante la descarga: se contabiliza al terminarla.

Entre entregas del mismo camión:

    inicio_entrega_j >= fin_entrega_i
                        + tau_camión(p_i,base)
                        + tiempo_recarga
                        + tau_camión(base,p_j)

El camión parte cargado de la base y su capacidad se repone para cada visita. Sin retorno obligatorio después de la última entrega. Si W_i supera tanque o camión, el dato se rechaza; no se inventan entregas parciales ni se simula cobertura radial de agua.

## Objetivos y flota

Modo plazo:

    min Cmax
    Cmax >= f_i,última para todo i
    Cmax >= fin_k para toda reserva elegida

Se desempata por menor número de unidades utilizadas. En ticks enteros:

    min (U + 1) * Cmax_ticks + sum_u v_u

U es el total de unidades disponibles: ningún ahorro secundario compensa un tick adicional de campaña.

Modo dimensionamiento: dado plazo L y máximos de flota, minimizar sum_u v_u sujeto a Cmax <= L. Desempate por menor plazo:

    min (H + 1) * sum_u v_u + Cmax_ticks

H es el horizonte calculado. Cada unidad pesa uno, sin asumir costos monetarios. El resultado no permite afirmar que la mezcla es económicamente óptima, ni que se consideraron equipos por encima de los máximos ingresados. Sin plazo/presupuesto, pedir «la mejor cantidad» minimizando tiempo es un problema diferente que favorece flotas crecientes.

## Algoritmo implementado

1. Validar escenario, unidades, capacidades y demandas.
2. Generar candidatos sin cuadrícula a partir de pozos, ubicación inicial, centroide, puntos medios e intersecciones de círculos de alcance entre pares de pozos.
3. Retener el pozo y hasta el límite configurable de candidatos con mayor cobertura y menor distancia inicial. La selección es por auxiliar; se conservan sus propiedades heterogéneas.
4. Construir intervalos opcionales, asignaciones, restricciones de capacidad y precedencias de viaje.
5. Dar una solución serial conservadora como pista; puede violar el plazo de dimensionamiento, por lo que es solo una pista y el solver debe repararla.
6. Ejecutar CP-SAT con cuatro trabajadores y límite de tiempo. Las mejoras publicadas en UI son soluciones factibles reales del solver.
7. Extraer trayectorias y validar sin usar las variables internas del solver.

No se ha implementado la doble generación de columnas de Deng/Jacquillat ni el ALNS de otros autores. Es una formulación propia CP-SAT inspirada en sus estructuras de coordinación.

## Certificados, redondeo y reproducibilidad

El tiempo se representa en décimas de hora. Duraciones, conexiones y traslados se redondean hacia arriba; el plazo hacia abajo. Demandas físicas se redondean hacia arriba y capacidad hacia abajo a centésimas. Por ello se conserva factibilidad conservadora, pudiendo perder eficiencia respecto del continuo.

`OPTIMAL`: óptimo demostrado del objetivo para estos candidatos, discretizaciones y restricciones. `FEASIBLE`: plan válido sin demostración completa. `INFEASIBLE`: imposibilidad en este modelo restringido, no necesariamente en todos los puntos del espacio continuo. `UNKNOWN`: no se halló una solución en el tiempo disponible; no significa imposibilidad.

La brecha se calcula como (objetivo - cota) / max(1, |objetivo|) para el objetivo compuesto. No se presenta como porcentaje garantizado de mejora del makespan solamente. `Cmax` incluye desconexiones finales; `construction_end` es el fin de las fases de construcción. Los campos `completion` por pozo corresponden a su última fase, no a la desconexión adicional global.

La semilla reproduce pozos y parámetros del solver; cuatro trabajadores pueden producir distintos planes equivalentes o incumbentes entre ejecuciones. Para experimentos que necesitan reproducibilidad bit a bit usar un solo trabajador y registrar versión, máquina y límite determinista.

## Para adaptar a operación real

Mantener el contrato de fases, equipos y trayectorias; reemplazar `geometry.py` por cálculo de rutas sobre GIS, restricciones de circulación y cobertura de mangueras/cables. Para posiciones continuas, incorporar optimización geométrica/refinamiento y medir pérdida de la aproximación. Añadir inventario con entregas múltiples, cuadrillas/turnos, fallas, zonas prohibidas y restricciones entre ensayos cuando existan datos validados. Ninguna de esas condiciones se presume resuelta por la demo.
