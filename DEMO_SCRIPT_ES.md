# Guion de demostración (≈ 3 minutos)

**Preparación (antes de presentar)**
1. `.\scripts\start.ps1 -Reset` → se abre `http://127.0.0.1:8000` con la misión demo en el día 40 (demo pública: https://basal-pxyn.onrender.com,
   abrirla 5 minutos antes para que el servidor gratuito despierte).
2. Desactivar el wifi (para mostrar que funciona sin Internet). Pantalla completa del navegador (F11).
3. Tener abierta la pantalla Tripulación. El botón **Demo guiada** de la portada ejecuta cada paso de verdad.
   Los botones "Ver fatiga (B)", "Ver estrés (C)" y "Ver evento solar (D)" saltan al día de cada escenario.

> Los tiempos son orientativos. Si el tiempo oficial es menor, saltar los bloques marcados *(opcional)*.

---

**0:00 – 0:25 · Problema**
"En camino a Marte, un mensaje a la Tierra tarda hasta 20 minutos en llegar, y a veces no llega. Los astronautas
cambian de forma gradual —sueño, corazón, atención, ánimo— y cada persona es distinta. Un umbral igual para todos
puede no ver un cambio importante en alguien cuyo valor normal es bajo… o alarmar a quien siempre está alto."

**0:25 – 0:45 · Propuesta** — *Tripulación (paso 1 de la demo guiada)*
"BASAL compara a cada astronauta **consigo mismo**. Aprende su línea base de 14 días y avisa cuando deja de comportarse
como de costumbre. Aquí: cuatro tripulantes ficticios, seis indicadores, todo calculado en este portátil, sin red."

**0:45 – 1:30 · Demostración** — *Pasos 2 a 4 (Cmdte. Rivera)*
- Día 40: "Todo dentro de lo habitual. Cada indicador muestra su valor y 'su normal'; la gráfica compara su umbral personal con el poblacional."
- Día 54: "El simulador inyectó una fatiga progresiva desde el día 44. BASAL dispara **Actuar: fatiga**. La alerta dice en una frase qué pasa y qué hacer; en "¿Por qué?" responde: qué cambió (sueño 6 h frente a 6,8 h habituales y más lapsos en la PVT-B), cuánto (z = 3 y
  5,5), cómo se detectó (fórmula con sus números), qué hacer (posponer tareas críticas, descansar, repetir la prueba,
  avisar al oficial médico) y con qué fuente y nivel de evidencia."

**1:30 – 1:50 · Donde el umbral fijo no ve** — *Paso 5 (Ing. Lindqvist, día 72)*
"Su FC en reposo subió de 53 a 60 lpm y su variabilidad bajó. Para un umbral poblacional, 60 es normal. Para él no:
z = 4,7. BASAL lo marca; el umbral fijo, no."

**1:50 – 2:15 · Sin Tierra** — *Pasos 6 a 8*
- Día 97 (o el botón **Simular apagón** de la portada en cualquier día): "Apagón de comunicaciones. El sistema sigue
  monitoreando y mostrando alarmas; los reportes quedan en cola."
- Cambiar al rol **Oficial médico**: "Las alarmas se ordenan por prioridad. Reconozco el episodio de Lindqvist y queda registrado quién y cuándo; si una roja lleva dos días sin reconocer, se escala a la oficial médica. Una alerta sigue abierta aunque hoy los valores hayan vuelto a su normal. Las amarillas se agrupan para evitar la fatiga de alarmas."
- "Generamos el reporte para la Tierra: queda **en cola**. *(opcional: avanzar al día 105 y pulsar "Enviar cola" — envío simulado)*."

**2:15 – 2:45 · Ciencia** — *Paso 9 (Validation Lab)*
"¿Cómo sabemos que funciona? Ajustamos los cortes con 20 misiones simuladas y evaluamos con **otras 40**. El nivel
*actuar* detectó el 98,9 % de los eventos con 0,8 falsas alarmas cada 30 días; el umbral fijo, el 88,9 % con 1,9.
Pero somos honestos: en cambios lentos o grandes **el umbral fijo avisa antes**, y si las personas se parecen mucho
entre sí, la personalización no aporta. Esta gráfica muestra exactamente **en qué condiciones** gana cada método."

**2:45 – 3:00 · Impacto y cierre**
"Lo mismo sirve en la Antártida, en submarinos o en comunidades andinas y amazónicas sin médico. BASAL no
diagnostica: le dice a cada persona, en su idioma, qué cambió en *su* cuerpo y qué seguimiento hacer, cuando la Tierra
está demasiado lejos."

---

**Nota honesta sobre el día 32** (si alguien revisa el historial de Tanaka): la alarma "actuar" del día 32 no
corresponde a ningún evento inyectado; es un falso positivo real del detector. Por eso la demo arranca en el día 40,
fuera de la ventana de 7 días de la portada, y si preguntan se usa para explicar la tasa medida: 0,78 falsas alarmas
por 30 días-astronauta en el nivel "actuar".

**Si algo falla**: si la interfaz muestra "Motor local no disponible", volver a ejecutar `.\scripts\start.ps1`. Si los
datos se movieron, `.\scripts\start.ps1 -Reset` restablece exactamente el mismo escenario (semilla 7).
