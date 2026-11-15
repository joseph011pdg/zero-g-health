# BASAL · Autonomous health monitoring for astronauts

**NASA Space Apps Challenge 2026 · Create Health Monitoring Software for Astronauts on Space Missions**

> Educational and research prototype with **simulated data**. It is not a medical device, does not diagnose and is
> not clinically validated. It does not represent and is not endorsed by NASA.

**Live demo:** https://basal-pxyn.onrender.com · **Code:** https://github.com/joseph011pdg/basal ·
Spanish versions of the docs: `*_ES.md`.

## Summary

BASAL is an offline-first health monitoring prototype for long-duration missions such as a Mars transit, where
Earth is up to ~20 minutes away and links can drop entirely. Instead of comparing astronauts against population
thresholds, BASAL learns **each crew member's own baseline** for six indicators (resting heart rate, HRV/RMSSD,
sleep duration, radiation dose rate, PVT-B lapses and false starts, and self-reported mood) and flags when a person
stops behaving as they usually do, using a robust z-score (median/MAD) that excludes the current day and past alert
days from the baseline. Every alert explains **what changed, by how much, how it was detected, which follow-up is
suggested and which source supports it**, and Act alerts are routed to the crew Medical Officer.

A reproducible mission simulator injects known health events so the detector can be validated: tuned on one set of
seeds and evaluated on a separate set of 40 missions, the personal-baseline **Act** level detected **98.9%** of events
with **0.78** false-alarm episodes per 30 astronaut-days, versus **88.9%** and **1.87** for a fixed population
reference range — while the fixed threshold raised the alarm earlier on slow or large changes. The lab shows **when
personalization helps and when it does not**. Everything runs locally (FastAPI + SQLite + Vue 3 PWA) with no Internet.

## Problem

On a Mars mission the crew cannot rely on the medical team on Earth to catch gradual health changes in time. Population
thresholds ignore that each person has different usual values.

## Solution

Detect when an astronaut's body **stops behaving the way it usually does**, explain it in plain language and suggest a
conservative follow-up, all **on board and offline**. The advantage over fixed thresholds is a **hypothesis** that is
tested in the Validation lab, including the cases where it does not hold.

## How to use the demo

- **Home (Crew):** the headline answers "does anything need attention?". Below it: problem / solution / evidence,
  the main actions (Review alerts, Check-in, PVT test, Send report) and demo shortcuts:
  - **Guided demo** — 9 steps that perform real actions.
  - **Simulate blackout** — the link with Earth drops: detection and alerts keep working, reports stay queued.
  - **See fatigue (B) / See stress (C) / See solar event (D)** — jump to the day where each injected event shows.
- **Levels:** *Watch* = repeat the measurement; *Act* = notify the Medical Officer. Levels always show an icon and
  text, never color alone. An alert stays open until it is acknowledged, even if today's values are back to normal.
- **Roles:** *Astronaut* sees their status and what to do; *Medical Officer* also sees alert management
  (Acknowledge, Snooze 24 h, Escalate, Resolved, with who/when and an optional note).
- **Public demo:** every visitor gets their own day, blackout and alert acknowledgements (stored in the browser);
  nothing a visitor does changes what others see. "Reset demo" restores the starting point (day 40).

## Features (F1–F10 of the proposal)

| | Feature | Where |
|---|---|---|
| F1 | Fictional profiles (4 preloaded, illustrated portraits), create profile, records and baseline per person | Crew · Laboratory → Data |
| F2 | Validated ingestion: simulator, form, CSV (unit, range, day, duplicates, missing values); source of every value; rejection log | Laboratory → Data |
| F3 | 3-min PVT-B (and a clearly marked 60-s demo), monotonic clock, false starts, lapses, interruptions | Profile → "PVT test" |
| F4 | Check-in in < 1 min: mood, perceived sleep quality, notes; history | Profile → "Check-in" |
| F5 | Personal baseline: median, MAD, n, window, difference; calibration; alert days excluded | Profile ("Their usual" and "Why?") |
| F6 | Robust z, traffic light with persistence, mission-start baseline for slow drifts, trend, data quality, radiation rate vs. cumulative | Profile |
| F7 | Explainable alerts (sentence + actions; detail and source under "Why?"); alert management by priority: acknowledge or snooze 24 h per episode, log of who and when, escalation after 2 days | Profile · Crew → Alerts (Medical Officer role) |
| F8 | Charts: value over the personal usual-range band, optional population threshold, alert onset marked, data freshness and quality | Profile |
| F9 | Seeded simulator: scenarios A–G, play/pause/step/restart, configurable blackout, ground truth vs. detector | Laboratory → Simulator · Earth–Mars strip |
| F10 | Report per astronaut or crew, delayed-transmission queue that respects the blackout, JSON/CSV/PDF (print) | Reports |

## Architecture (5 layers, all local)

```
1 Acquisition   simulator.py · forms · CSV · PVT-B (Vue)               ─┐
2 Data          ingest.py (validation) → SQLite (db.py)                 │  backend/basal (Python, FastAPI)
3 Analysis      detector.py (baseline + robust z) · config.py           │  the science does not depend on HTTP
4 Decision      recommender.py + recomendaciones.json + evidence.json   │
   Services     services.py (joins layers) · main.py (routes, OpenAPI) ─┘
5 Presentation  frontend/ (Vue 3, Pinia, Vue Router, ECharts, PWA) served by FastAPI from one origin
```

Security: the server listens only on `127.0.0.1` locally; CORS only for the local dev server; no keys or external
services. The PWA caches the interface but **needs the local engine**: if it does not respond, the interface says so
and retries. Code identifiers (e.g. `amarillo`/`rojo` levels, `pendiente` states, JSON keys) are internal and kept
in Spanish; everything shown to the user is in English.

## Requirements and installation (Windows 10/11)

1. Install **Python 3.11+** (tested with 3.14; tick "Add python.exe to PATH") and **Node.js LTS** (tested with 24).
2. Open the project folder in Visual Studio Code → *Terminal → New Terminal* (PowerShell).
3. Install (once, needs Internet):
   ```powershell
   .\scripts\setup.ps1
   ```
   If PowerShell blocks scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (or
   `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`).
4. Start (no Internet needed):
   ```powershell
   .\scripts\start.ps1
   ```
   Opens `http://127.0.0.1:8000`. API docs at `http://127.0.0.1:8000/docs`.
5. Stop: `Ctrl+C` in the terminal. Restart: `.\scripts\start.ps1`.
   Restart the demo mission: `.\scripts\start.ps1 -Reset` or "Restart demo mission" in the Simulator.

Hot-reload development: `cd backend; .venv\Scripts\python -m uvicorn basal.main:app --reload --host 127.0.0.1`
and in another terminal `cd frontend; npm run dev` (http://localhost:5173, `/api` proxy).

## Public online demo (Render)

The repository includes `render.yaml` (Python runtime, free plan) and the compiled interface in `frontend/dist`.
1. Push the repository to GitHub.
2. In Render: **New → Blueprint** → choose the repository → **Apply**. Render installs `backend/requirements.txt` and
   starts `uvicorn` on `0.0.0.0:$PORT` with `BASAL_PUBLIC=1`.
3. Before every push that changes the interface: `cd frontend; npm run build` (Render does not build the frontend).

With `BASAL_PUBLIC=1` the database is shared, but **each visitor has their own session**: the day and the simulated
blackout travel in the `X-Basal-Dia` / `X-Basal-Apagon` headers, alert acknowledgements are stored in the browser
("Reset demo" button) and check-ins, PVT tests and reports are computed without being saved (the report is shown as a
preview). Scenario changes, the blackout window and profile creation are blocked (403), a restart always returns to
the canonical demo (seed 7, day 40) and validation experiments are limited to 10 missions. A GitHub Actions workflow
(`.github/workflows/keepalive.yml`) pings the site every ~10 min so it does not fall asleep; while it wakes up, the
interface shows "Waking up the server…". The service worker updates itself immediately (`autoUpdate`, `skipWaiting`,
`clientsClaim`) so visitors do not see an old cached version. The reference version is still the local one, with no
Internet.

## Tests

```powershell
.\scripts\test.ps1
```
32 pytest tests (median, MAD, z, MAD = 0, missing values, impossible values, calibration, sudden and gradual changes,
persistence, no absorption, profile separation, CSV, reproducibility, metrics, reports, delayed queue, radiation,
SQLite persistence, API, per-session headers) + interface build. Regenerate the scientific validation:
`cd backend; .venv\Scripts\python -m basal.validation`.

## Data

- **Simulated:** every demo measurement, the 4 fictional astronauts, the events, the blackout and the transmission.
  Generated with a fixed seed (`simulator.py`), reproducible.
- **From the literature:** order of magnitude of the dose rate (Patel et al., 2020), PVT-B definitions (Basner et
  al., 2011), sleep recommendation (Watson et al., 2015).
- **NASA data:** the MVP does **not** include individual measurements from NASA OSDR/Inspiration4 or Mars-500. Real
  data can be loaded with the CSV schema `astro_id,day,indicator,value,unit[,source]` (see `GET /api/ingest/schema`).

## Limitations

Validated only with simulated data; illustrative recommendations that need medical review; browser PVT-B without
latency correction; mood is a single, non-validated question; no way yet to "accept a new baseline"; simulated
transmission to Earth. Details in [SCIENTIFIC_METHOD.md](SCIENTIFIC_METHOD.md).

## Documentation

[SCIENTIFIC_METHOD.md](SCIENTIFIC_METHOD.md) · [DEMO_SCRIPT.md](DEMO_SCRIPT.md) · [JUDGES_QA.md](JUDGES_QA.md) ·
[PROGRESS.md](PROGRESS.md) (team log, Spanish) · Spanish versions: [README_ES.md](README_ES.md),
[SCIENTIFIC_METHOD_ES.md](SCIENTIFIC_METHOD_ES.md), [DEMO_SCRIPT_ES.md](DEMO_SCRIPT_ES.md), [JUDGES_QA_ES.md](JUDGES_QA_ES.md) ·
original proposal in `docs/propuesta.pdf`.

## Main references

- Basner, M., et al. (2014). Psychological and behavioral changes during confinement in a 520-day simulated interplanetary mission to Mars. *PLoS ONE, 9*(3), e93298.
- Basner, M., Mollicone, D., & Dinges, D. F. (2011). Validity and sensitivity of a brief psychomotor vigilance test (PVT-B) to total and partial sleep deprivation. *Acta Astronautica, 69*(11–12), 949–959.
- Mishra, T., et al. (2020). Pre-symptomatic detection of COVID-19 from smartwatch data. *Nature Biomedical Engineering, 4*(12), 1208–1220.
- Patel, Z. S., et al. (2020). Red risks for a journey to the red planet. *npj Microgravity, 6*, 33.
- Garrett-Bakelman, F. E., et al. (2019). The NASA Twins Study. *Science, 364*(6436), eaau8650.
- Crucian, B. E., et al. (2018). Immune system dysregulation during spaceflight. *Frontiers in Immunology, 9*, 1437.
- Watson, N. F., et al. (2015). Recommended amount of sleep for a healthy adult. *Sleep, 38*(6), 843–844.
- Full list with evidence level: `backend/basal/evidence.json` and the Laboratory → Science screen.
