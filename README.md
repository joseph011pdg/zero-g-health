# BASAL · Monitoreo de salud autónomo para astronautas

**NASA Space Apps Challenge 2026 · Create Health Monitoring Software for Astronauts on Space Missions**

> Prototipo educativo y de investigación con **datos sintéticos**. No es un dispositivo médico, no diagnostica y no
> está validado clínicamente. No representa ni tiene respaldo de NASA.

## English summary

BASAL is an offline-first health monitoring prototype for long-duration missions such as a Mars transit, where
Earth is up to ~20 minutes away and links can drop entirely. Instead of comparing astronauts against population
thresholds, BASAL learns **each crew member's own baseline** for six indicators (resting heart rate, HRV/RMSSD,
sleep duration, radiation dose rate, PVT-B vigilance errors and self-reported mood) and flags when a person stops
behaving as they usually do, using a robust z-score (median/MAD) that excludes the current day and past alert days
from the baseline. Every alert explains **what changed, by how much, how it was detected, which follow-up is
suggested and which source supports it**, and red alerts are routed to the crew medical officer. A reproducible
mission simulator injects known health events so the detector can be validated: tuned on one set of seeds and
evaluated on a separate set of 40 missions, the personal-baseline "act" level detected 98.9 % of events with 0.78
false-alarm episodes per 30 astronaut-days, versus 88.9 % and 1.87 for a fixed population reference range — while
the fixed threshold raised the alarm earlier on slow or large changes. The lab shows **when personalization helps
and when it does not**. Everything runs locally (FastAPI + SQLite + Vue 3 PWA) with no internet.

## Problema

En una misión a Marte la tripulación no puede depender del equipo médico en Tierra para detectar a tiempo cambios
graduales de salud. Los umbrales poblacionales ignoran que cada persona tiene valores habituales distintos.

## Solución

Detectar cuándo el cuerpo de un astronauta **deja de comportarse como habitualmente lo hace**, explicarlo en
lenguaje claro y sugerir un seguimiento conservador, todo **a bordo y sin conexión**. La ventaja sobre los umbrales
fijos es una **hipótesis** que se pone a prueba en el Validation Lab, incluidos los casos donde no se cumple.

## Funcionalidades (F1–F10 de la propuesta)

| | Función | Dónde |
|---|---|---|
| F1 | Perfiles ficticios (4 precargados, con retrato ilustrado), crear perfil, registros y línea base por persona | Tripulación · Laboratorio → Datos |
| F2 | Ingesta validada: simulador, formulario, CSV (unidad, rango, día, duplicados, ausentes); origen de cada dato; registro de rechazos | Laboratorio → Datos |
| F3 | PVT-B de 3 min (y demo abreviada de 60 s claramente marcada), reloj monotónico, anticipaciones, lapsos, interrupciones | Persona → botón "Prueba PVT" |
| F4 | Check-in < 1 min: ánimo, calidad de sueño percibida, notas; historial | Persona → botón "Check-in" |
| F5 | Línea base individual: mediana, MAD, n, ventana, diferencia; calibración; exclusión de días en alerta | Persona ("Su normal" y "¿Por qué?") |
| F6 | z robusto, semáforo con persistencia, línea base inicial para derivas, tendencia, calidad de datos, radiación tasa vs. acumulada | Persona |
| F7 | Alertas explicables (frase + acciones; detalle y fuente en "¿Por qué?"); gestión de alarmas por prioridad: reconocer o posponer 24 h por episodio, registro de quién y cuándo, aviso de escalado a los 2 días | Persona · Tripulación → Alarmas (rol Oficial médico) |
| F8 | Gráficos: valor sobre la banda de rango normal personal, umbral poblacional opcional, inicio de la alerta anotado, frescura y calidad del dato | Persona |
| F9 | Simulador con semillas: escenarios A–G, iniciar/pausar/avanzar/reiniciar, apagón configurable, verdad vs. detector | Laboratorio → Simulador · franja Tierra–Marte |
| F10 | Reporte por astronauta o tripulación, cola de envío diferido que respeta el apagón, JSON/CSV/PDF (imprimir) | Chip "Tierra" de la cabecera |

Selector de rol en la cabecera (**Astronauta** ve su estado y qué hacer; **Oficial médico** ve además las alarmas y los controles de revisión). Navegación: **Tripulación** (con una línea de respuesta: «2 de 4 tripulantes requieren acción») (inicio, con la franja Tierra–Marte y "Para revisar") y **Laboratorio** (simulador, validación, datos y ciencia). Cada astronauta se abre tocando su retrato; los reportes, desde el chip de la Tierra. Botón **Demo** en la cabecera (9 pasos con acciones reales). Diseño claro en blanco y azul; imágenes de la Tierra, Marte y la cúpula de la ISS de dominio público (NASA, vía Wikimedia Commons; créditos en `frontend/public/img/credits.json`) y retratos ilustrados propios.

## Arquitectura (5 capas, todo local)

```
1 Adquisición   simulator.py · formularios · CSV · PVT-B (Vue)      ─┐
2 Datos         ingest.py (validación) → SQLite (db.py)              │  backend/basal (Python, FastAPI)
3 Análisis      detector.py (línea base + z robusto) · config.py     │  la lógica científica no depende de HTTP
4 Decisión      recommender.py + recomendaciones.json + evidence.json│
   Servicios    services.py (une capas) · main.py (rutas, OpenAPI)  ─┘
5 Presentación  frontend/ (Vue 3, Pinia, Vue Router, ECharts, PWA) servido por FastAPI en un solo origen
```

Seguridad: el servidor escucha solo en `127.0.0.1`; CORS solo para el servidor de desarrollo local; sin claves ni
servicios externos. La PWA cachea la interfaz, pero **necesita el motor local**: si no responde, la interfaz lo dice y
reintenta.

## Requisitos e instalación (Windows 10/11)

1. Instalar **Python 3.11+** (probado con 3.14; marcar "Add python.exe to PATH") y **Node.js LTS** (probado con 24).
2. Abrir la carpeta del proyecto en Visual Studio Code → *Terminal → New Terminal* (PowerShell).
3. Instalar (única vez, necesita Internet):
   ```powershell
   .\scripts\setup.ps1
   ```
   Si PowerShell bloquea scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (o
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`).
4. Iniciar (sin Internet):
   ```powershell
   .\scripts\start.ps1
   ```
   Abre `http://127.0.0.1:8000`. API documentada en `http://127.0.0.1:8000/docs`.
5. Detener: `Ctrl+C` en la terminal. Volver a iniciar: `.\scripts\start.ps1`.
   Reiniciar la misión de demostración: `.\scripts\start.ps1 -Reset` o botón "Reiniciar misión demo" en el Simulador.

Desarrollo con recarga en caliente: `cd backend; .venv\Scripts\python -m uvicorn basal.main:app --reload --host 127.0.0.1`
y en otra terminal `cd frontend; npm run dev` (http://localhost:5173, proxy `/api`).

## Demo pública en línea (Render)

**URL: https://basal-pxyn.onrender.com** · código: https://github.com/joseph011pdg/basal


El repositorio incluye `render.yaml` (runtime Python, plan gratuito) y la interfaz ya compilada en `frontend/dist`.
1. Subir el repositorio a GitHub.
2. En Render: **New → Blueprint** → elegir el repositorio → **Apply**. Render instala `backend/requirements.txt` y
   arranca `uvicorn` en `0.0.0.0:$PORT` con `BASAL_PUBLIC=1`.
3. Antes de cada push con cambios en la interfaz: `cd frontend; npm run build` (Render no compila el frontend).

Con `BASAL_PUBLIC=1` el estado es compartido entre visitantes, así que se bloquean los cambios de escenario, el
apagón y la creación de perfiles (403), el reinicio siempre vuelve a la demo canónica (semilla 7, día 38) y los
experimentos de validación se limitan a 10 misiones. En el plan gratuito el servicio se duerme sin visitas (primera
carga lenta) y la base SQLite se regenera en cada reinicio. La versión de referencia sigue siendo la local, sin Internet.

## Pruebas

```powershell
.\scripts\test.ps1
```
30 pruebas pytest (mediana, MAD, z, MAD = 0, ausentes, imposibles, calibración, cambios bruscos y graduales,
persistencia, no absorción, separación de perfiles, CSV, reproducibilidad, métricas, reportes, cola diferida,
radiación, persistencia SQLite, API) + compilación de la interfaz. Regenerar la validación científica:
`cd backend; .venv\Scripts\python -m basal.validation`.

## Datos

- **Sintéticos**: todas las mediciones de la demo, los 4 astronautas ficticios, los eventos, el apagón y la
  transmisión. Generados con semilla fija (`simulator.py`), reproducibles.
- **De la literatura**: orden de magnitud de la tasa de dosis (Patel et al., 2020), definiciones PVT-B (Basner et al.,
  2011), recomendación de sueño (Watson et al., 2015).
- **Datos NASA**: el MVP **no** incluye mediciones individuales de NASA OSDR/Inspiration4 ni de Mars-520. Se pueden
  cargar datos reales con el esquema CSV `astro_id,day,indicator,value,unit[,source]` (ver `GET /api/ingest/schema`).

## Limitaciones

Validación solo con datos sintéticos; recomendaciones ilustrativas que requieren revisión médica; PVT-B en navegador
sin corrección de latencia; ánimo con una sola pregunta no validada; no hay "aceptar nueva línea base"; envío a la
Tierra simulado. Detalle en [SCIENTIFIC_METHOD.md](SCIENTIFIC_METHOD.md).

## Documentación

[SCIENTIFIC_METHOD.md](SCIENTIFIC_METHOD.md) · [DEMO_SCRIPT.md](DEMO_SCRIPT.md) · [JUDGES_QA.md](JUDGES_QA.md) ·
[PROGRESS.md](PROGRESS.md) · propuesta original en `docs/propuesta.pdf`.

## Referencias principales

- Basner, M., et al. (2014). Psychological and behavioral changes during confinement in a 520-day simulated interplanetary mission to Mars. *PLoS ONE, 9*(3), e93298.
- Basner, M., Mollicone, D., & Dinges, D. F. (2011). Validity and sensitivity of a brief psychomotor vigilance test (PVT-B) to total and partial sleep deprivation. *Acta Astronautica, 69*(11–12), 949–959.
- Mishra, T., et al. (2020). Pre-symptomatic detection of COVID-19 from smartwatch data. *Nature Biomedical Engineering, 4*(12), 1208–1220.
- Patel, Z. S., et al. (2020). Red risks for a journey to the red planet. *npj Microgravity, 6*, 33.
- Garrett-Bakelman, F. E., et al. (2019). The NASA Twins Study. *Science, 364*(6436), eaau8650.
- Crucian, B. E., et al. (2018). Immune system dysregulation during spaceflight. *Frontiers in Immunology, 9*, 1437.
- Watson, N. F., et al. (2015). Recommended amount of sleep for a healthy adult. *Sleep, 38*(6), 843–844.
- Lista completa con nivel de evidencia: `backend/basal/evidence.json` y pantalla "Reportes y ciencia → Ciencia".
