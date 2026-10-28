# Referencias y decisiones de adaptación

## Papers matemáticos

1. Adam Deng y Alexandre Jacquillat (2023). **Coordinating mobile network coverage and vehicle routing: a double column generation approach**. [arXiv:2312.08341](https://arxiv.org/abs/2312.08341), [texto completo](https://arxiv.org/html/2312.08341v1).
   - Aporta coordinación muchos-a-muchos entre vehículos que ejecutan trabajos y unidades móviles de cobertura.
   - La sección 3.1 considera ubicaciones candidatas para emisores y discretización temporal.
   - Aquí se usan varios servicios heterogéneos, capacidades físicas y siete fases. No se importa su objetivo ni se reproduce su algoritmo.
2. David Wittwer y Felix Tamke (2024). **The vehicle routing problem with synchronization constraints and support vehicle-dependent service times**. [arXiv:2403.03355](https://arxiv.org/abs/2403.03355).
   - Aporta formulaciones de vehículos principales y de apoyo y decisiones sobre asignaciones.
   - En nuestro modelo T es fijo y no se reduce por añadir auxiliares; la dependencia de productividad del paper no se adopta.
3. Michael Drexl (2012). **Synchronization in Vehicle Routing—A Survey of VRPs with Multiple Synchronization Constraints**. Transportation Science 46(3), 297–316. [DOI 10.1287/trsc.1110.0400](https://doi.org/10.1287/trsc.1110.0400).
   - Marco para coordinación espacial, temporal y de recursos.
4. Minh Hoàng Hà y colaboradores (2019). **A new constraint programming model and a linear programming-based adaptive large neighborhood search for the vehicle routing problem with synchronization constraints**. [arXiv:1910.13513](https://arxiv.org/abs/1910.13513).
   - Referencia para escalar con búsqueda de vecindarios; ALNS no está implementado en v0.1.

## Evidencia operativa

- [Novandino: operación actual](https://novandino.com/operacion/operacion-actual/): salmuera extraída mediante pozos, concentración en piscinas y procesamiento posterior en Planta Química Litio Carmen.
- [Informe técnico SQM, 5 de abril de 2024](https://www.sec.gov/Archives/edgar/data/909037/000110465924044246/tm2410667d1_ex96-1.htm), §7.3 y §13.4: ensayos hidráulicos, equipos y construcción de pozos. Antecedente histórico; no es inventario de la flota actual de Novandino.
- [Portal de empleos Novandino, operador de bombeo](https://www.trabajaen.novandino.com/5404-Operador-a-bombeo): descripción pública de montaje, desmontaje, traslados y apoyo en ensayos. La búsqueda pública devolvió el contenido; la apertura directa falló en la sesión de investigación. No se usa para inferir cantidades ni duraciones.

La duración inicial de bombeo (96 h) es un valor demostrativo compatible con el antecedente de cuatro días o más del informe de 2024; no es un estándar certificado ni una duración universal. Preparación 2 h, perforación 48 h, acondicionamiento 4 h, montaje 2 h, recuperación 24 h y desmontaje 2 h son **supuestos sintéticos**, no mediciones industriales. Alcances, velocidades, consumos y capacidades también son sintéticos.

El catálogo configurable (compresor, circulación, generador, camión/tanque y equipo de ensayo) no representa una flota aprobada ni prueba que un servicio pueda compartirse en cualquier configuración real. El método de perforación y los procedimientos de campo determinan cuáles corresponden.

## Documentación de implementación

- [OR-Tools: Job Shop](https://developers.google.com/optimization/scheduling/job_shop): intervalos, precedencias y makespan.
- [OR-Tools: CP-SAT](https://developers.google.com/optimization/cp/cp_solver): variables enteras y estados del solver.
- [FastAPI: tareas en segundo plano](https://fastapi.tiangolo.com/tutorial/background-tasks/): límites del enfoque local; la demo usa una cola de ejecución en un único proceso y CP-SAT nativo.

Fecha de elaboración: 28 de octubre de 2026. La documentación distingue evidencia consultada, supuestos del ejemplo y decisiones de implementación.
