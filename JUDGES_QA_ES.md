# Preguntas del jurado · respuestas breves

**¿Qué tiene de innovador?**
La combinación: línea base individual robusta para seis indicadores fisiológicos y conductuales, alertas que explican
qué cambió, cuánto, cómo se detectó, qué hacer y con qué evidencia, funcionamiento 100 % local con cola diferida a la
Tierra, y una validación cuantitativa reproducible que muestra **cuándo** la personalización ayuda y cuándo no. No
afirmamos ser "el primer sistema": AnomalyDetect (Mishra et al., 2020) ya usa líneas base personales con wearables; lo
nuestro es aplicarlo a una misión sin Tierra, de forma explicable y validada contra un comparador.

**¿Por qué una línea base individual?**
Porque las diferencias entre personas suelen ser mayores que los cambios que importan dentro de una persona (en
Mars-520 la respuesta a 520 días de aislamiento fue muy distinta entre tripulantes; Basner et al., 2014). En la demo, un
aumento de 7 lpm (de 53 a 60) es relevante para el Ing. Lindqvist (z = 4,7), aunque 60 lpm sea "normal" para la población.

**¿Por qué no solo umbrales poblacionales?**
En nuestra evaluación, el umbral fijo detectó solo el 49 % de los episodios de estrés fisiológico (frente al 100 %) y
dio más falsas alarmas (1,87 frente a 0,78 por 30 días). Pero no lo descartamos: avisa antes en cambios grandes o
lentos. Una versión operacional podría combinar ambos.

**¿Cómo verificaron las alertas?**
Con un simulador que inyecta eventos conocidos (la "verdad"). Ajustamos los cortes con las semillas 1000–1019 y
evaluamos con 2000–2039, distintas. Medimos sensibilidad por evento, retraso, falsas alarmas por día y por episodio,
por escenario, por indicador y por heterogeneidad. Todo se reproduce con `python -m basal.validation` y desde el
Validation Lab. Además hay 30 pruebas automáticas.

**¿Qué datos son de NASA?**
Ninguna medición individual de NASA está en el MVP. Usamos publicaciones de NASA y de investigación para fijar
órdenes de magnitud (tasa de dosis, Patel et al., 2020) y definiciones (PVT-B). El sistema acepta datos reales por CSV
con esquema documentado; integrar OSDR/Inspiration4 es el siguiente paso y depende de qué variables individuales sean
realmente descargables.

**¿Qué datos son simulados?**
Todas las mediciones de la demostración, los astronautas (ficticios), los eventos de salud, el apagón y el envío a la
Tierra. Cada medición guarda su origen (`sintetico`, `manual`, `csv`, `pvt`, `real`) y la interfaz lo muestra.

**¿Por qué offline?**
Hasta ~20 minutos por sentido y apagones durante la conjunción solar: un sistema que dependa de la Tierra llega tarde.
BASAL corre en un portátil: FastAPI + SQLite + interfaz PWA en un solo origen local, sin CDN ni claves.

**¿Qué pasa cuando faltan datos?**
Nunca se asume normalidad: el indicador aparece "sin dato" o "calibrando"; la línea base usa solo observaciones válidas
(y amplía la ventana si hace falta); cada alerta muestra el % de datos de los últimos 14 días y advierte "fiabilidad
reducida" por debajo del 70 %. Los registros imposibles se rechazan y quedan registrados con su motivo.

**¿Cómo evitan recomendaciones médicas incorrectas?**
Son orientaciones de **seguimiento** conservadoras (repetir la medición, descansar, registrar síntomas), sin fármacos
ni diagnósticos; cada una cita su fuente y nivel de evidencia; las rojas remiten al oficial médico y a los protocolos
de la misión; el oficial médico revisa, escala o descarta cada alerta. Las reglas requieren revisión profesional antes
de cualquier uso real.

**¿Cómo evitan la fatiga de alarmas?**
Las alarmas tienen dos prioridades con forma y texto propios, las amarillas se agrupan en una sola fila, se reconocen por
episodio (no cada día) y se pueden posponer 24 h; si una roja lleva 2 días sin reconocer, la interfaz pide escalarla.
Queda registro de quién reconoció qué y cuándo. Es un diseño inspirado en la gestión de alarmas clínicas, no una
implementación certificada de esas normas.

**¿Usa inteligencia artificial?**
No en el sentido de un modelo entrenado. Es estadística robusta y reglas deterministas: explicables, reproducibles y
validables. No había datos reales etiquetados para entrenar un modelo sin que aprendiera solo los supuestos del
simulador. Un asistente local por voz queda como mejora futura.

**¿Cómo se integraría con sensores reales?**
La capa de ingesta ya valida unidades, rangos y duplicados y registra el origen. Un wearable o dosímetro solo tiene
que entregar `astro_id, día, indicador, valor, unidad` (CSV o `POST /api/measurements`). Para señales crudas de ECG se
añadiría un paso de extracción de FC/VFC (p. ej., RapidHRV; Kirk et al., 2022).

**¿Qué faltaría para un uso operacional?**
Datos reales de vuelo o análogos para validar, revisión médica de reglas y cortes, sensores certificados, autenticación
y cifrado, auditoría, mecanismo para que el oficial médico acepte una nueva línea base, integración con los
procedimientos de la misión y aprobación regulatoria.

**¿Qué limitaciones tiene?**
Validado solo con datos sintéticos; el nivel "vigilar" da ~5 avisos falsos por 30 días por astronauta; el nivel
"actuar" avisa más tarde que el umbral fijo en cambios lentos; PVT-B en navegador sin corrección de latencia; ánimo
con una sola pregunta; recomendaciones no revisadas por médicos.

**¿Impacto en la Tierra?**
Personal en bases antárticas, submarinos y plataformas; comunidades rurales sin médico (Andes, Amazonía); cualquier
lugar donde la ayuda está lejos y lo importante es saber cuándo una persona **dejó de estar como siempre**.

## Debilidades que mostramos nosotros primero
Cifras de `backend/basal/data/validation_results.json` (40 misiones de evaluación, datos simulados).

**"El nivel vigilar da muchos avisos."**
Sí: 26,8 % de los días sanos y 5,04 avisos falsos por 30 días-astronauta. Vigilar significa "repita la medición", no
"actúe". El nivel actuar tiene 0,78 falsas alarmas por 30 días-astronauta y 3,5 % de los días sanos.

**"El método personal avisa más tarde."**
En actuar, el retraso medio es 4,34 días frente a 3,16 del umbral fijo; cuando ambos detectan, el fijo avisa en
promedio 1,44 días antes. A cambio, A detecta 31 eventos que B no ve (B solo 3 que A no ve) con menos de la mitad de
falsas alarmas. El nivel vigilar sí avisa antes que el fijo (1,49 días de media).

**"En PVT pierden."**
Sí: 75,9 % de sensibilidad en actuar frente a 93,8 % del umbral fijo. Por eso el sistema combina seis indicadores y
persistencia en vez de depender de uno.

**"El ánimo es débil."**
50 % de sensibilidad en actuar. Es una sola pregunta, no un test validado; se usa como apoyo, nunca solo.

**"¿La alarma del día 32 de Tanaka?"**
Es un falso positivo: no hay evento inyectado ese día. No lo escondemos; es un ejemplo de la tasa de falsas alarmas
medida y de por qué existen "Posponer" y "Reconocer".

**"¿Radiación: 102 % de qué?"**
De lo esperado a hoy en el escenario simulado (tasa nominal × días transcurridos), en mGy (dosis absorbida), no en
mSv (dosis equivalente) ni frente a límites de NASA. El acumulado se informa y no genera alarma; la alarma vigila la
tasa diaria frente a la normal de cada persona.

**"¿Por qué 'lapsos' y no 'errores'?"**
Seguimos a Basner et al. (2011): lapso = respuesta ≥ 355 ms; el indicador suma lapsos y anticipaciones (falsos
arranques) de la PVT-B.

