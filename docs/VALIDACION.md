# Validación del prototipo

Ejecutada el 28 de octubre de 2026 en Python 3.12.14, Node.js 24.19.0 y Chromium disponible en el entorno. Versiones de dependencias fijadas en `requirements-lock.txt` y `frontend/package-lock.json`.

## Resultados

- Backend: **13 pruebas aprobadas** (`python -m pytest -q`).
- Interpolación y estados React/TypeScript: **5 pruebas aprobadas** (`npm test`).
- Navegador real: **2 pruebas de extremo a extremo aprobadas** (`npm run test:e2e`).
- Compilación TypeScript y bundle Vite: **correcta** (`npm run build`).
- Capturas inspeccionadas: `preview-plan.png` y vista inicial; captura móvil adicional en `preview-mobile.png`.

Las pruebas de backend incluyen cobertura desde una posición distinta de los pozos, atención compartida, límites independientes de potencia y simultaneidad, tiempo T común, recuperación/desmontaje, capacidad de agua, recarga entre entregas, disponibilidades individuales, excepciones de duración, detección de teletransportes, trayectoria ortogonal, cancelación, API y validaciones de entrada.

El recorrido de navegador modifica cantidad y radio de un generador, resuelve, pausa, desplaza el slider a 110 h, cambia a cronograma por máquina, descarga CSV, abre las referencias y vuelve a calcular minimizando flota para un plazo. En móvil verifica ancho sin desbordamiento y rechazo visible de demanda de agua superior al tanque. No se observaron errores JavaScript durante el recorrido.

## Casos adicionales calculados

Datos sintéticos; 3 segundos de búsqueda en estos cuatro casos, semilla 17:

| Pozos | Modo | Plazo máximo | Estado | Finalización | Flota usada D/C/G/E/A |
|---|---|---:|---|---:|---|
| 8 | Menor duración | No aplica | OPTIMAL | 553,6 h | 2/2/2/2/1 |
| 6 | Menor flota | 500 h | FEASIBLE | 482,9 h | 1/1/2/2/1 |
| 6 | Menor flota | 1.000 h | OPTIMAL | 828,1 h | 1/1/1/1/1 |
| 6 | Menor flota | 100 h | INFEASIBLE | — | — |

D: perforadora; C: compresor; G: generador; E: equipo de ensayo; A: camión de agua. El circuito de agua/lodo no es requerido en estos casos.

`OPTIMAL` se refiere al modelo finito documentado. El caso de 500 h no prueba que esa sea la menor flota: la brecha del objetivo compuesto fue aproximadamente 0,567 %. Los resultados de búsquedas paralelas limitadas por tiempo pueden variar.

Se observó una advertencia de deprecación de Starlette sobre su uso de httpx en TestClient; las pruebas terminaron correctamente. No hubo validación industrial, datos geográficos reales ni pruebas de carga multiusuario.
