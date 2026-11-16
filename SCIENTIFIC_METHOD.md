# Scientific method · BASAL

> Educational and research prototype. **Statistical** detection of deviations, not medical diagnosis.
> Every number in this document comes from `backend/basal/data/validation_results.json`, generated with
> `python -m basal.validation` (≈3 min). If the code changes, regenerate it. Spanish version: `SCIENTIFIC_METHOD_ES.md`.

## 1. Question

Under which conditions does comparing each astronaut with **their own baseline** improve change detection compared
with a **fixed population threshold**?

## 2. Indicators (`backend/basal/indicators.py`)

| Key | Indicator | Unit | Worse if it | Sensor (intended) | Clinical reference |
|---|---|---|---|---|---|
| `rhr` | Resting heart rate | bpm | ↑ | Wearable (ECG) | General convention: tachycardia > 100 bpm (not spaceflight-specific) |
| `hrv` | Heart rate variability (RMSSD) | ms | ↓ | Wearable (ECG), night | No accepted population threshold |
| `sleep` | Sleep duration | h | ↓ | Actigraphy | ≥ 7 h in adults (Watson et al., 2015) |
| `dose` | Dose **rate** | mGy/day | ↑ | Dosimeter | No NASA limits are used (see §6) |
| `pvt` | PVT-B lapses (lapses + false starts) | lapses | ↑ | Tablet | Lapse ≥ 355 ms (Basner et al., 2011) |
| `mood` | Mood (self-report) | /10 | ↓ | Tablet | Own scale, not validated |

Each indicator has a **physical plausibility range** (`limits`) used only to reject impossible values at ingestion,
and a **minimum spread** (`min_spread`) that acts as the practical resolution of the measurement.

## 3. Personal baseline and robust z-score (`backend/basal/detector.py`)

For astronaut *i*, indicator *k* and day *t*:

```
B_t = { x_s : t − W ≤ s < t, x_s valid, s was not in alert }         (W = 14 days)
m_t = median(B_t)
MAD_t = 1.4826 × median(|B_t − m_t|)
z_t = d_k × (x_t − m_t) / max(MAD_t, min_spread_k)                   (d_k = +1 if rising is bad, −1 if falling is bad)
```

Design choices and why:

| Choice | Reason |
|---|---|
| Median and MAD instead of mean and SD | One atypical day does not shift the reference. The 1.4826 factor makes MAD comparable to an SD under normal data. |
| Day *t* never enters B_t | The current value is never used to build its own reference (tested in `test_current_value_not_in_own_baseline`). |
| Alert days are excluded from B_t | Prevents a persistent deterioration from being absorbed into the baseline and "normalized". |
| If \|B_t\| < 7, extend up to 2W; if still short → **Calibrating** | Insufficient data is neither evaluated nor assumed healthy. |
| No measurement on day *t* → **No data** | Missing data is never read as normal. |
| Mission-start baseline: first 14 valid days | A slow drift stays under the day-to-day cutoff and the rolling window "absorbs" it; z_ini against the start of the mission is also computed and the larger one is used. |
| `min_spread` when MAD ≈ 0 | Avoids division by zero with discrete or very stable data (e.g., PVT lapses). |

**Traffic light** (parameters in `backend/basal/data/config.json`, loaded by `config.py`):

- Normal: z < 2.5 · **Watch**: 2.5 ≤ z < 4.5 · **Act**: z ≥ 4.5 **or** 3 consecutive valid days at Watch.
- The proposal started from 2 / 3; the first MVP used 2.5 / 3.5. Current values come from the **tuning** in §5.
- They are experimental prototype parameters, **not medical limits**.

**Other calculations**: 7-day trend with the Theil–Sen slope (median of pairwise slopes); quality = share of days with
data in the previous 14 (if < 70%, the alert says "reduced reliability"); stability index 0–100 =
100 × (1 − mean of min(max(z, 0), 5)/5) over the indicators evaluated that day.

## 4. From detection to alert (`recommender.py`, `recomendaciones.json`, `evidence.json`)

Combined rules (evaluated first): physiological stress (HR ↑ + HRV ↓), fatigue (sleep ↓ + PVT ↑), behavioral change
(mood ↓ + PVT ↑). If no combined rule applies, an individual rule per indicator and level. Each alert includes: what
changed, by how much (value, baseline, absolute and % difference, z, n, MAD), how it was detected (formula with
numbers and cutoffs), conservative **follow-up** actions, sources with **type and level of evidence**, data quality and
review status. Every Act alert adds: *"Notify the onboard Medical Officer and follow the authorized mission
protocols."* No medication is prescribed and no disease is diagnosed.

## 5. Validation (`backend/basal/validation.py`)

**Simulator** (`simulator.py`): 4 astronauts × 120 days; between-person differences (population SD) larger than each
person's day-to-day noise (with AR(1) autocorrelation = 0.3). Injected events: B progressive fatigue, C physiological
stress, D solar event (whole crew), E slow behavioral change; random intensity 0.5–1.5×.

**Methods**

- **A · Personal**: the detector above. Two levels are evaluated: *Watch* (Watch or Act) and *Act*.
- **B · Fixed population reference**: classic reference interval: 97.5th percentile (if rising is bad) or 2.5th (if
  falling is bad) of healthy days in the **tuning** population. The same for everyone.

**Definitions**

- *True event*: injected deviation with known start, end and affected indicators.
- *Detection* (event level): any alert on an affected indicator in [start, end + 2]. *Delay*: days from the start.
- *Healthy day*: day ≥ 14 outside [start − 1, end + 7] of every event. *False alarm* (day level): healthy day with an alert.
  *False episode*: run of alert days starting on a healthy day (reported per 30 astronaut-days).
- *Lead time*: delay(B) − delay(A) on events detected by both.

**Protocol**: tuning with seeds 1000–1019 (20 missions); evaluation with **different** seeds 2000–2039 (40 missions,
160 astronauts, 279 events, 12,176 healthy days). Tuning criterion (engineering decision): among combinations with
≤ 1 false "Act" episode per 30 astronaut-days, the one with the highest "Act" sensitivity (tie-break: lower delay).
Grid: Watch ∈ {2, 2.5, 3}, Act ∈ {3, 3.5, 4, 4.5}.

### Results (evaluation set)

| Method | Sensitivity | Mean delay (median) | False alarms / 30 astronaut-days | % healthy days with an alert |
|---|---|---|---|---|
| A · Watch | 100% | 1.53 d (0) | 5.04 | 26.8% |
| A · Act | 98.9% | 4.34 d (1) | 0.78 | 3.5% |
| B · fixed | 88.9% | 3.16 d (0) | 1.87 | 13.4% |

By scenario (sensitivity / mean delay, A·Act vs B):

| Scenario | A · Act | B · fixed | Reading |
|---|---|---|---|
| B progressive fatigue | 98.3% / 5.6 d | 100% / 4.3 d | **B equal or better**: short sleep crosses the fixed threshold early. |
| C physiological stress | 100% / 1.1 d | 49.1% / 1.2 d | **A much better**: +8 bpm does not cross a fixed threshold if resting HR is low. |
| D solar event | 100% / 0 d | 100% / 0 d | Tie: the change is huge. |
| E behavioral change | 96.3% / 15.8 d | 94.4% / 9.9 d | **B alerts earlier**; A needs accumulated evidence. |

**Lead time** (events detected by both): *Watch* alerts before B on average (+1.5 days; 74 earlier, 164 same day,
10 later); *Act* alerts **after** B on average (−1.4 days; 33 earlier, 142 same day, 70 later), but detects 31 events
that B misses (B detects 3 that *Act* misses).

**Key condition: heterogeneity between people** (between-person SD × factor; B re-estimated for each population with
tuning seeds; 20 evaluation missions per condition, so the 1× row differs slightly from the 40-mission main table):

| Heterogeneity | A · Act (sens. / FA) | B · fixed (sens. / FA) |
|---|---|---|
| 0.25× | 99.3% / 0.74 | 100% / 2.16 |
| 0.5× | 96.6% / 0.76 | 97.3% / 2.23 |
| 1× | 98.7% / 0.65 | 87.2% / 2.08 |
| 2× | 96.6% / 0.66 | 78.5% / 1.71 |

**Answer to the question (on synthetic data)**: the personal baseline keeps sensitivity with fewer false alarms when
people differ a lot from each other and the changes are small relative to those differences (scenario C). When the
population is homogeneous or the change is large or slow, the fixed threshold is just as sensitive and often **alerts
earlier**. Personalization is not a universal advantage.

**Ablation** (A · Act): without excluding alert days 97.8% / 0.63 FA; without mission-start baseline 82.1% / 0.42 FA;
rolling window only 77.1% / 0.25 FA. The mission-start baseline provides almost all the detection of slow drifts, at
the cost of more notices.

### Example of a real false alarm in the demo

In the demo mission, Spec. Kenji Tanaka (A4) has an **Act** alert on day 32 (PVT lapses, z ≈ 4.5) with **no injected
event** (his first event, a behavioral change, starts on day 52). It is a genuine false positive of the detector, of
the kind counted in the 0.78 false alarms per 30 astronaut-days. The public demo starts on day 40, so it is outside
the 7-day window of the home page, but it is visible in his history and in the Simulator's ground-truth table.

## 6. Radiation

The robust z is not applied to the **cumulative** dose (it always grows). The **daily rate** (mGy/day) is watched with
the personal baseline and, separately, the measured cumulative dose is shown against **what the simulated scenario
expects to date** (0.40 mGy/day × days elapsed, an order of magnitude consistent with 300–450 mGy over ~3 years;
Patel et al., 2020). Units are absorbed dose (mGy), not equivalent dose (mSv). It is not a NASA exposure limit; days
without a reading are reported, not filled in.

## 7. PVT-B

Stimulus with a random 2–5 s interval; response with the space bar or a tap; lapse = RT ≥ 355 ms; false start =
response before the stimulus or < 100 ms; no response within 3 s = lapse. `performance.now()` clock from the first
frame that draws the stimulus. Switching windows is logged as an interruption and the test becomes invalid (it does
not enter the baseline). The 60-s version is a **short demo** that is not equivalent to the 3-min protocol; its lapses
are scaled to 3 min and stored flagged as `pvt_abreviada`. *To verify*: the 2–5 s interval against the original PVT-B
paper.

## 8. Limitations

1. **Synthetic** data only: results depend on the simulator's assumptions. No validation with flight data and no
   clinical validation.
2. The *Watch* level gives ~5 false notices per 30 days per astronaut (6 indicators): it means repeat the measurement,
   not act.
3. Comparator B is estimated on the same simulated population; real clinical thresholds would be even less sensitive.
4. Window (14 d) and minimum number of observations (7) fixed by design, not tuned.
5. The mission-start baseline cannot tell a legitimate adaptation from a deterioration; there is no way yet for the
   Medical Officer to "accept a new baseline".
6. Recommendation rules written by the team from the literature; they need professional medical review.
7. Individual NASA OSDR/Inspiration4 or Mars-500 data are not integrated yet (the CSV schema allows it).

## 9. Why not machine learning?

There are no real labeled data to train or validate a model; a model trained only on the simulator would learn the
simulator's assumptions. The robust method is deterministic, explainable in one line and reproducible. BASAL is
**not** a "trained AI model": it is rules and robust statistics.
