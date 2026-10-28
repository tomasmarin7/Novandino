# Litio Planner

Prototipo independiente de planificación de campañas de pozos: Python + OR-Tools CP-SAT + FastAPI y React/TypeScript. Interfaz negra, mapa sintético, reproducción temporal y fichas individuales. No está integrado con NavyBlue ni representa una aplicación oficial de Novandino.

## Ejecutar

### Clonar y ejecutar en macOS

Cuando el repositorio esté publicado en GitHub, clónalo en tu escritorio y ejecuta el lanzador desde la carpeta clonada:

```bash
cd "$HOME/Desktop"
git clone https://github.com/tomasmarin7/Novandino.git novandino
cd novandino
bash Iniciar.command
```

El lanzador requiere Python 3.11 o posterior (recomendado 3.12), instala las dependencias y abre el navegador. Incluye `frontend/dist`, por lo que no necesitas Node para usar la interfaz. Mantén la Terminal abierta y usa Ctrl+C para detener el servidor. Si cambias el repositorio a privado, necesitarás autenticarte en GitHub para clonarlo.

### Paquete descargable y desarrollo

**Paquete para macOS:** consulta `LEEME-MAC.txt`. `Instalar_en_Escritorio.command` copia el proyecto al escritorio sin sobrescribir una carpeta existente. `Iniciar.command` prepara las dependencias Python en un entorno local y abre la interfaz compilada en el navegador. Para usar ese paquete no hace falta Node. La descarga no cambia esta sesión remota a un proyecto local: abre la carpeta del escritorio en tu aplicación de desarrollo para continuar allí.

Requiere Python 3.11 o posterior y Node.js 22 o posterior. Desde esta carpeta:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
cd frontend
npm ci
npm run build
cd ..
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Abrir **http://127.0.0.1:8000**. FastAPI sirve también el frontend compilado. En Windows usar `.venv\Scripts\python.exe -m pip` y `.venv\Scripts\python.exe -m uvicorn` en lugar de los ejecutables Linux.

En este entorno las dependencias y `frontend/dist` ya están preparados: basta `bash run.sh` o el último comando. Si npm no puede escribir en su caché predeterminada, usar `npm ci --cache /tmp/litio-npm-cache`.

Para desarrollar, mantener FastAPI y ejecutar `npm run dev` en `frontend`: Vite sirve **http://127.0.0.1:5173** y envía `/api` a FastAPI. Estos enlaces son locales a la máquina que ejecuta el programa; no son una publicación web ni un enlace remoto compartido.

## Uso

1. En **Escenario**, ajustar semilla, número de pozos y dimensiones. Generar una distribución repetible.
2. En **Flota**, elegir cantidades y seleccionar unidades. El inspector permite editar ubicación inicial, disponibilidad, velocidad, alcance, capacidad simultánea y física, conexión y desconexión.
3. En **Proceso**, editar las siete duraciones, requisitos por fase, demandas físicas y agua. El tiempo de perforación T es único para todos los pozos.
4. Elegir **Terminar lo antes posible** o **Dimensionar la flota**. El segundo necesita un plazo y usa las cantidades de equipos como máximos. Minimiza número total de unidades con igual peso, no dinero.
5. **Calcular plan** ejecuta el backend. El progreso muestra incumbentes reales del solver. Se puede detener la búsqueda conservando un plan factible si ya existe.
6. Reproducir, pausar, cambiar velocidad o mover el slider. Seleccionar un equipo muestra su coordenada interpolada, destino y llegada. Seleccionar un pozo muestra fase, horas e inventario.
7. Exportar escenario/plan JSON o coordenadas y tiempos CSV. Importar un JSON permite repetir el caso; el escenario incorporado en un plan también se acepta. Modificar parámetros invalida el resultado anterior.

## Qué está implementado

- Asignación de todos los pozos, rutas individuales, precedencias y objetivo de plazo total.
- Ocupación de perforadoras durante construcción, liberación antes de los ensayos.
- Auxiliares compartidos desde una posición, con límites K y Q separados.
- Generadores con demanda física en kW; compresores y circulación con unidades explícitas.
- Ensayo: montaje, bombeo, recuperación (equipo reservado por defecto) y desmontaje.
- Agua: camiones independientes, entrega previa a tanque fijo por pozo, recarga en base entre entregas y consumo durante perforación.
- Ubicaciones auxiliares fuera de los pozos generadas desde geometría, sin cuadrícula.
- Coordenadas, trayectorias y estados de cada equipo a lo largo del tiempo.
- Dimensionamiento acotado de flota, estado de resolución y brecha del objetivo.
- Verificador independiente ejecutado antes de entregar cualquier plan.

## Límites explícitos de esta primera versión

Los pozos, tiempos y flotas son **datos sintéticos de demostración**, no valores operativos validados por Novandino. Elegir distancia recta u ortogonal no afirma nada sobre la topografía de su faena. No se han cargado GIS, caminos, pendientes, prohibiciones, mangueras reales ni métricas asimétricas.

El modelo conceptual admite posiciones continuas. El algoritmo implementado utiliza **un conjunto finito de posiciones candidatas**, seleccionadas geométricamente sin grilla (pozos, centroide, puntos medios, intersecciones de círculos y ubicación inicial). Un resultado `OPTIMAL` certifica solo ese conjunto y la discretización temporal de **0,1 h**. No certifica el óptimo del espacio continuo ni del terreno real. Aumentar candidatos amplía la búsqueda, pero no prueba convergencia continua.

Construcción y ensayo son dos bloques sin pausas internas; puede haber espera entre ellos. Cada servicio consecutivo mantiene el mismo auxiliar y posición, reservando capacidad incluso durante conexión/desconexión. No hay relevo dentro de un bloque. El equipo de ensayo permanece reservado durante recuperación por defecto. Las demandas se redondean hacia arriba y capacidades hacia abajo a centésimas.

El tanque se considera instalado en cada pozo. Solo hay una entrega de agua antes de perforar; consumo superior a tanque o camión se rechaza. No se modelan entregas parciales ni recargas durante perforación. El camión empieza cargado en base. No hay retorno final obligatorio de unidades. El plan termina cuando se completa el tratamiento y se liberan todos los recursos, incluida su desconexión final.

Máximo de la demo: 16 pozos, 40 equipos, 6 candidatos por servicio/unidad y 60 segundos de solver. Construcción/verificación se suman a ese tiempo. No se promete encontrar solución en todos los casos grandes. El API local no tiene autenticación y conserva un número limitado de cálculos en memoria; no exponerlo como servicio público.

## Cálculo sin interfaz

```bash
.venv/bin/python -m backend.cli --input examples/demo-6.json --output /tmp/plan.json
.venv/bin/python -m backend.cli --demo 8 --seed 17 --output /tmp/otro-plan.json
```

En JSON se pueden definir excepciones de duración por pozo mediante `durations` (excepto `drill`) y consumo individual mediante `water_demand`. El mapa puede editar las coordenadas de cada pozo. La API documentada está en `/docs`.

## Verificación

```bash
.venv/bin/python -m pytest -q
cd frontend
npm test
npm run build
npm run test:e2e
```

La prueba de navegador usa Chromium disponible en `/usr/bin/chromium` o la variable `CHROMIUM_PATH`; si no existe, configurar un navegador de Playwright. Playwright inicia el servidor local si hace falta. No se necesita descargar un navegador en este entorno.

## Archivos principales

- `docs/MODELO.md`: formulación, objetivo, restricciones y correspondencia con código.
- `docs/REFERENCIAS.md`: papers y evidencia operativa, con límites de adaptación.
- `backend/schema.py`: contrato de datos y ejemplo reproducible.
- `backend/geometry.py`: candidatos, métricas y recorridos de demostración.
- `backend/optimizer.py`: modelo CP-SAT, búsqueda y exportación de trayectorias.
- `backend/verify.py`: verificación física independiente.
- `backend/app.py`: API asíncrona, cancelación y servidor de frontend.
- `frontend/src/App.tsx`, `Map.tsx`, `simulation.ts`: interfaz, dibujo y reproducción.

Siguiente extensión matemática: métricas reales por tipo de unidad, posiciones continuas/refinamiento adaptativo y recargas con inventario dinámico. Los módulos están separados para reemplazar esas aproximaciones sin rehacer la interfaz.
