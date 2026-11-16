# Judges' questions · short answers

Spanish version: `JUDGES_QA_ES.md`. All figures come from `backend/basal/data/validation_results.json`
(40 evaluation missions, simulated data).

**What is innovative about it?**
The combination: a robust personal baseline for six physiological and behavioral indicators, alerts that explain what
changed, by how much, how it was detected, what to do and with which evidence, 100% local operation with a delayed
queue to Earth, and a reproducible quantitative validation that shows **when** personalization helps and when it does
not. We do not claim to be "the first system": AnomalyDetect (Bogu, 2020; used in Mishra et al., 2020) already uses
personal baselines with wearables; our contribution is applying it to a mission without Earth, explainably and
validated against a comparator.

**Why a personal baseline?**
Because differences between people are usually larger than the changes that matter within one person (in the 520-day
Mars-500 isolation study the response differed widely between crew members; Basner et al., 2014). In the demo, a rise
of 7 bpm (from 53 to 60) is relevant for Eng. Lindqvist (z = 4.7), even though 60 bpm is "normal" for the population.

**Why not just population thresholds?**
In our evaluation the fixed threshold detected only 49% of physiological-stress episodes (vs. 100%) and gave more
false alarms (1.87 vs. 0.78 per 30 astronaut-days). But we do not discard it: it alerts earlier on large or slow
changes. An operational version could combine both.

**How did you verify the alerts?**
With a simulator that injects known events (the "ground truth"). We tuned the cutoffs with seeds 1000–1019 and
evaluated with different seeds 2000–2039. We measured event-level sensitivity, delay, false alarms per day and per
episode, by scenario, by indicator and by heterogeneity. Everything is reproducible with `python -m basal.validation`
and from the Validation lab. There are also 32 automated tests.

**Which data are from NASA?**
No individual NASA measurement is in the MVP. We use NASA and research publications to set orders of magnitude (dose
rate, Patel et al., 2020) and definitions (PVT-B). The system accepts real data via CSV with a documented schema;
integrating OSDR/Inspiration4 is the next step and depends on which individual variables are actually downloadable.

**Which data are simulated?**
Every demo measurement, the (fictional) astronauts, the health events, the blackout and the transmission to Earth.
Each measurement stores its source (`sintetico` = synthetic, `manual`, `csv`, `pvt`, `real`) and the interface shows it.

**Why offline?**
Up to ~20 minutes each way and blackouts during solar conjunction: a system that depends on Earth arrives too late.
BASAL runs on a laptop: FastAPI + SQLite + PWA interface from one local origin, no CDN and no keys.

**What happens when data are missing?**
Normal is never assumed: the indicator shows "No data" or "Calibrating"; the baseline uses only valid observations
(and widens the window if needed); each alert shows the % of data in the last 14 days and warns of "reduced
reliability" below 70%. Impossible records are rejected and logged with their reason.

**How do you avoid wrong medical recommendations?**
They are conservative **follow-up** guidance (repeat the measurement, rest, log symptoms), with no medication and no
diagnoses; each one cites its source and level of evidence; Act alerts go to the Medical Officer and the mission
protocols; the Medical Officer acknowledges, snoozes, escalates or resolves each alert. The rules need professional
review before any real use.

**How do you avoid alarm fatigue?**
Alerts have two priorities with their own shape and text (*Act* = notify the Medical Officer; *Watch* = repeat the
measurement). On the home page Watch notices are sorted by z and the rest are grouped under "N more notices"; alerts
are acknowledged per episode (not every day) and can be snoozed 24 h; if an Act alert stays unacknowledged for 2 days,
the interface asks to escalate it. Who acknowledged what and when is logged, with an optional note. It is a design
inspired by clinical alarm management, not a certified implementation of those standards.

**Does it use artificial intelligence?**
Not in the sense of a trained model. It is robust statistics and deterministic rules: explainable, reproducible and
testable. There were no real labeled data to train a model without it just learning the simulator's assumptions. A
local voice assistant is a future improvement.

**How would it integrate with real sensors?**
The ingestion layer already validates units, ranges and duplicates and records the source. A wearable or dosimeter
only has to deliver `astro_id, day, indicator, value, unit` (CSV or `POST /api/measurements`). For raw ECG signals a
HR/HRV extraction step would be added (e.g., RapidHRV; Kirk et al., 2022).

**What would be needed for operational use?**
Real flight or analog data for validation, medical review of rules and cutoffs, certified sensors, authentication and
encryption, auditing, a way for the Medical Officer to accept a new baseline (not built; listed as a limitation),
integration with mission procedures and regulatory approval.

**What are its limitations?**
Validated only with synthetic data; the Watch level gives ~5 false notices per 30 days per astronaut; the Act level
alerts later than the fixed threshold on slow changes; browser PVT-B without latency correction; mood is a single
question; recommendations not reviewed by physicians.

**Impact on Earth?**
Staff in Antarctic bases, submarines and offshore platforms; rural communities without a doctor (Andes, Amazon);
anywhere help is far away and what matters is knowing when a person **stopped being their usual self**.

## Weaknesses we point out first

**"The Watch level gives many notices."**
Yes: 26.8% of healthy days and 5.04 false notices per 30 astronaut-days. Watch means "repeat the measurement", not
"act". The Act level has 0.78 false alarms per 30 astronaut-days and 3.5% of healthy days.

**"The personal method alerts later."**
At Act, the mean delay is 4.34 days vs. 3.16 for the fixed threshold; when both detect, the fixed one alerts 1.44 days
earlier on average. In exchange, A detects 31 events that B misses (B only 3 that A misses) with less than half the
false alarms. The Watch level does alert earlier than the fixed threshold (1.49 days on average).

**"You lose on PVT."**
Yes: 75.9% sensitivity at Act vs. 93.8% for the fixed threshold. That is why the system combines six indicators and
persistence instead of relying on one.

**"Mood is weak."**
50% sensitivity at Act. It is a single question, not a validated test; it is used as support, never alone.

**"What about Tanaka's day-32 alert?"**
It is a false positive: Spec. Kenji Tanaka (A4) gets an Act alert for PVT lapses on day 32 (z = 4.5) with no injected
event (his first event, a behavioral change, starts on day 52). We do not hide it: it is an example of the measured
false-alarm rate (0.78 per 30 astronaut-days) and of why "Snooze" and "Acknowledge" exist. The demo starts on day 40,
so it is outside the 7-day window of the home page, but it is visible in his history and in the Simulator.

**"Radiation: 102% of what?"**
Of what the simulated scenario expects to date (nominal rate × days elapsed), in mGy (absorbed dose), not mSv
(equivalent dose) and not against NASA limits. The cumulative dose is reported and raises no alert; the alert watches
the daily rate against each person's usual values.

**"Why 'lapses' and not 'errors'?"**
We follow Basner et al. (2011): lapse = response ≥ 355 ms; the indicator adds lapses and false starts of the PVT-B.
