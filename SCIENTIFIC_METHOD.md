# Método científico · BASAL

> Prototipo educativo y de investigación. Detección **estadística** de desviaciones, no diagnóstico médico.
> Todos los números de este documento salen de `backend/basal/data/validation_results.json`, generado con
> `python -m basal.validation` (≈3 min). Si cambia el código, vuelva a generarlo.

## 1. Pregunta

¿En qué condiciones comparar a cada astronauta con **su propia línea base** mejora la detección de cambios frente a
un **umbral poblacional fijo**?

## 2. Indicadores (`backend/basal/indicators.py`)

| Clave | Indicador | Unidad | Empeora si | Sensor (previsto) | Referencia clínica |
|---|---|---|---|---|---|
| `rhr` | FC en reposo | lpm | ↑ | Wearable (ECG) | Convención general: taquicardia > 100 lpm (no específica de vuelo) |
| `hrv` | Variabilidad de la FC (RMSSD) | ms | ↓ | Wearable (ECG) nocturno | No existe umbral poblacional aceptado |
| `sleep` | Duración del sueño | h | ↓ | Actigrafía | ≥ 7 h en adultos (Watson et al., 2015) |
| `dose` | **Tasa** de dosis | mGy/día | ↑ | Dosímetro | No se usan límites de NASA (ver §6) |
| `pvt` | Lapsos PVT-B (lapsos + anticipaciones) | lapsos | ↑ | Tableta | Lapso ≥ 355 ms (Basner et al., 2011) |
| `mood` | Ánimo (autorreporte) | /10 | ↓ | Tableta | Escala propia, no validada |

Cada indicador tiene un **rango de plausibilidad física** (`limits`) que solo sirve para rechazar datos imposibles en la
ingesta, y una **dispersión mínima** (`min_spread`) que actúa como resolución práctica de la medida.

## 3. Línea base individual y puntaje z robusto (`backend/basal/detector.py`)

Para el astronauta *i*, el indicador *k* y el día *t*:

```
B_t = { x_s : t − W ≤ s < t, x_s válido, s no estaba en alerta }       (W = 14 días)
m_t = mediana(B_t)
MAD_t = 1,4826 × mediana(|B_t − m_t|)
z_t = d_k × (x_t − m_t) / max(MAD_t, min_spread_k)                      (d_k = +1 si subir es malo, −1 si bajar es malo)
```

Decisiones y su motivo:

| Decisión | Motivo |
|---|---|
| Mediana y MAD en vez de media y DE | Un día atípico no altera la referencia. El factor 1,4826 hace el MAD comparable a una DE con datos normales. |
| El día *t* nunca entra en B_t | No usar el valor actual para calcular su propia referencia (probado en `test_current_value_not_in_own_baseline`). |
| Los días en alerta se excluyen de B_t | Evita que un deterioro persistente se incorpore a la línea base y se "normalice". |
| Si \|B_t\| < 7, se amplía hasta 2W; si no alcanza → **calibrando** | Datos insuficientes no se evalúan ni se dan por sanos. |
| Sin medición el día *t* → **sin dato** | La ausencia de datos nunca se interpreta como normalidad. |
| Línea base inicial: primeros 14 días válidos | Una deriva lenta pasa por debajo del corte día a día y la ventana móvil la "absorbe"; se calcula también z_ini contra el inicio de misión y se usa el mayor. |
| `min_spread` cuando MAD ≈ 0 | Evita divisiones entre cero con datos discretos o muy estables (p. ej., errores PVT). |

**Semáforo** (parámetros en `backend/basal/data/config.json`, cargados por `config.py`):

- Normal: z < 2,5 · **Vigilar**: 2,5 ≤ z < 4,5 · **Actuar**: z ≥ 4,5 **o** 3 días válidos seguidos en vigilar.
- La propuesta partía de 2 / 3; el MVP inicial usaba 2,5 / 3,5. Los valores actuales salen del **ajuste** del §5.
- Son parámetros experimentales del prototipo, **no límites médicos**.

**Otros cálculos**: tendencia de 7 días con pendiente de Theil–Sen (mediana de pendientes por pares); calidad =
proporción de días con dato en los 14 previos (si es < 70 %, la alerta indica "fiabilidad reducida"); índice de
estabilidad 0–100 = 100 × (1 − media de min(max(z, 0), 5)/5) sobre los indicadores evaluados ese día.

## 4. De la detección a la alerta (`recommender.py`, `recomendaciones.json`, `evidence.json`)

Reglas combinadas (se evalúan primero): estrés fisiológico (FC ↑ + VFC ↓), fatiga (sueño ↓ + PVT ↑), cambio
conductual (ánimo ↓ + PVT ↑). Si no aplica una combinada, regla individual por indicador y nivel. Cada alerta incluye:
qué cambió, cuánto (valor, línea base, diferencia absoluta y %, z, n, MAD), cómo se detectó (fórmula con números y
cortes), acciones de **seguimiento** conservadoras, fuentes con **tipo y nivel de evidencia**, calidad de datos y
estado de revisión. Toda alerta roja añade: *"Notificar al oficial médico de a bordo y seguir los protocolos
autorizados de la misión."* No se prescriben fármacos ni se diagnostican enfermedades.

## 5. Validación (`backend/basal/validation.py`)

**Simulador** (`simulator.py`): 4 astronautas × 120 días; diferencias entre personas (DE poblacional) mayores que
el ruido diario de cada persona (con autocorrelación AR(1) = 0,3). Eventos inyectados: B fatiga progresiva, C estrés
fisiológico, D evento solar (toda la tripulación), E cambio conductual lento; intensidad aleatoria 0,5–1,5×.

**Métodos**

- **A · Individual**: el detector anterior. Se evalúan dos niveles: *vigilar* (amarillo o rojo) y *actuar* (rojo).
- **B · Referencia poblacional fija**: intervalo de referencia clásico — percentil 97,5 (si subir es malo) o 2,5 (si
  bajar es malo) de los días sanos de la población **de ajuste**. Igual para todos.

**Definiciones**

- *Evento verdadero*: desviación inyectada con inicio, fin e indicadores afectados conocidos.
- *Detección* (nivel evento): alguna alerta en un indicador afectado en [inicio, fin + 2]. *Retraso*: días desde el inicio.
- *Día sano*: día ≥ 14 fuera de [inicio − 1, fin + 7] de todo evento. *Falsa alarma* (nivel día): día sano con alerta.
  *Episodio falso*: racha de días con alerta que empieza en un día sano (se informa por 30 días-astronauta).
- *Anticipación*: retraso(B) − retraso(A) en los eventos que ambos detectan.

**Protocolo**: ajuste con semillas 1000–1019 (20 misiones); evaluación con semillas **distintas** 2000–2039
(40 misiones, 160 astronautas, 279 eventos, 12 176 días sanos). Criterio de ajuste (decisión de ingeniería): entre
las combinaciones con ≤ 1 episodio falso "actuar" por 30 días-astronauta, la de mayor sensibilidad "actuar"
(desempate: menor retraso). Rejilla: amarillo ∈ {2; 2,5; 3}, rojo ∈ {3; 3,5; 4; 4,5}.

### Resultados (conjunto de evaluación)

| Método | Sensibilidad | Retraso medio (mediana) | Falsas alarmas / 30 días-astronauta | % días sanos con alerta |
|---|---|---|---|---|
| A · vigilar | 100 % | 1,53 d (0) | 5,04 | 26,8 % |
| A · actuar | 98,9 % | 4,34 d (1) | 0,78 | 3,5 % |
| B · fijo | 88,9 % | 3,16 d (0) | 1,87 | 13,4 % |

Por escenario (sensibilidad / retraso medio, A·actuar vs B):

| Escenario | A · actuar | B · fijo | Lectura |
|---|---|---|---|
| B fatiga progresiva | 98,3 % / 5,6 d | 100 % / 4,3 d | **B igual o mejor**: el sueño corto cruza pronto el umbral fijo. |
| C estrés fisiológico | 100 % / 1,1 d | 49,1 % / 1,2 d | **A mucho mejor**: +8 lpm no cruza un umbral fijo si la FC basal es baja. |
| D evento solar | 100 % / 0 d | 100 % / 0 d | Empate: el cambio es enorme. |
| E cambio conductual | 96,3 % / 15,8 d | 94,4 % / 9,9 d | **B avisa antes**; A necesita evidencia acumulada. |

**Anticipación** (eventos detectados por ambos): *vigilar* avisa antes que B en promedio (+1,5 días; 74 antes, 164
mismo día, 10 después); *actuar* avisa **después** que B en promedio (−1,4 días; 33 antes, 142 mismo día, 70 después),
pero detecta 31 eventos que B no detecta (B detecta 3 que *actuar* no).

**Condición clave: heterogeneidad entre personas** (DE entre personas × factor; B re-estimado para cada población
con semillas de ajuste; 20 misiones de evaluación por condición, por eso la fila 1× difiere ligeramente de la tabla
principal de 40 misiones):

| Heterogeneidad | A · actuar (sens. / FA) | B · fijo (sens. / FA) |
|---|---|---|
| 0,25× | 99,3 % / 0,74 | 100 % / 2,16 |
| 0,5× | 96,6 % / 0,76 | 97,3 % / 2,23 |
| 1× | 98,7 % / 0,65 | 87,2 % / 2,08 |
| 2× | 96,6 % / 0,66 | 78,5 % / 1,71 |

**Respuesta a la pregunta (en datos sintéticos)**: la línea base individual mantiene la sensibilidad con menos falsas
alarmas cuando las personas difieren mucho entre sí y los cambios son pequeños respecto a esas diferencias
(escenario C). Cuando la población es homogénea o el cambio es grande o lento, el umbral fijo es igual de sensible y a
menudo **avisa antes**. La personalización no es una ventaja universal.

**Ablación** (A · actuar): sin excluir días en alerta 97,8 % / 0,63 FA; sin línea base inicial 82,1 % / 0,42 FA;
solo ventana móvil 77,1 % / 0,25 FA. La línea base inicial aporta casi toda la detección de derivas lentas, a costa
de más avisos.

## 6. Radiación

No se aplica el z robusto a la dosis **acumulada** (crece siempre). Se vigila la **tasa diaria** (mGy/día) con la línea
base individual y, por separado, se muestra la dosis acumulada medida frente a un **presupuesto del escenario
simulado** (0,40 mGy/día × días transcurridos, orden de magnitud coherente con 300–450 mGy en ~3 años; Patel et al.,
2020). No es un límite de exposición de NASA; los días sin lectura se informan, no se rellenan.

## 7. PVT-B

Estímulo con intervalo aleatorio de 2–5 s; respuesta con barra espaciadora o toque; lapso = RT ≥ 355 ms; anticipación =
respuesta antes del estímulo o < 100 ms; sin respuesta en 3 s = lapso. Reloj `performance.now()` desde el primer cuadro
que dibuja el estímulo. Cambiar de ventana se registra como interrupción y la prueba queda inválida (no entra en la
línea base). La versión de 60 s es una **demostración abreviada** que no equivale al protocolo de 3 min; sus errores se
escalan a 3 min y se guardan marcados como `pvt_abreviada`. *Pendiente de verificar*: el intervalo 2–5 s frente al
artículo original de PVT-B.

## 8. Limitaciones

1. Solo datos **sintéticos**: los resultados dependen de los supuestos del simulador. No hay validación con datos de
   vuelo ni validación clínica.
2. El nivel *vigilar* da ~5 avisos falsos por 30 días por astronauta (6 indicadores): sirve para repetir la medición,
   no para actuar.
3. Comparador B estimado en la misma población simulada; umbrales clínicos reales serían todavía menos sensibles.
4. Ventana (14 d) y mínimo de observaciones (7) fijados por diseño, no ajustados.
5. La línea base inicial no distingue una adaptación legítima de un deterioro; falta que el oficial médico pueda
   "aceptar una nueva línea base".
6. Reglas de recomendación escritas por el equipo a partir de la literatura; requieren revisión médica profesional.
7. No se integran todavía datos individuales de NASA OSDR/Inspiration4 ni de Mars-520 (el esquema CSV lo permite).

## 9. ¿Por qué no machine learning?

No hay datos etiquetados reales para entrenar ni validar un modelo; un modelo entrenado solo con el simulador
aprendería los supuestos del simulador. El método robusto es determinista, explicable en una línea y reproducible.
BASAL **no** es un "modelo de IA entrenado": son reglas y estadística robusta.
