# Demo script (≈ 3 minutes)

Spanish version: `DEMO_SCRIPT_ES.md`.

**Preparation (before presenting)**
1. `.\scripts\start.ps1 -Reset` → opens `http://127.0.0.1:8000` with the demo mission on day 40 (public demo:
   https://basal-pxyn.onrender.com; open it 5 minutes before so the free server wakes up).
2. Turn off Wi-Fi (to show that the local version works without Internet). Full-screen browser (F11).
3. Keep the Crew screen open. The **Guided demo** button on the home page performs each step for real.
   The "See fatigue (B)", "See stress (C)" and "See solar event (D)" buttons jump to the day of each scenario.

> Times are approximate. If the official time is shorter, skip the blocks marked *(optional)*.

---

**0:00 – 0:25, Problem**
"On the way to Mars, a message to Earth takes up to 20 minutes to arrive, and sometimes it does not arrive at all.
Astronauts change gradually (sleep, heart, attention, mood) and every person is different. One threshold for
everyone can miss an important change in someone whose usual value is low… or alarm someone who is always high."

**0:25 – 0:45, Proposal**, *Crew (guided demo step 1)*
"Zero G Health compares each astronaut **with themselves**. It learns their 14-day baseline and alerts when they stop behaving
as usual. Here: four fictional crew members, six indicators, all computed on this laptop, with no network."

**0:45 – 1:30, Demo**, *Steps 2 to 4 (Cmdr. Rivera)*
- Day 40: "Everything within the usual range. Each indicator shows its value and 'their usual'; the chart compares
  the personal range with the population threshold."
- Day 54: "The simulator injected progressive fatigue from day 44. Zero G Health fires **Act: fatigue**. The alert says in one
  sentence what is going on and what to do; under 'Why?' it answers: what changed (sleep 6 h vs. their usual 6.8 h and
  more PVT-B lapses), by how much (z = 3 and 5.5), how it was detected (the formula with its numbers), what to do
  (postpone critical tasks, rest, repeat the test, notify the Medical Officer) and which source and level of evidence
  supports it."

**1:30 – 1:50, Where the fixed threshold is blind**, *Step 5 (Eng. Lindqvist, day 72)*
"His resting heart rate rose from 53 to 60 bpm and his variability fell. For a population threshold, 60 is normal.
For him it is not: z = 4.7. Zero G Health flags it; the fixed threshold does not."

**1:50 – 2:15, Without Earth**, *Steps 6 to 8*
- Day 97 (or the **Simulate blackout** button on the home page, on any day): "Communication blackout. The system keeps
  monitoring and showing alerts; reports stay queued."
- Switch to the **Medical Officer** role: "Alerts are sorted by priority. *Act* means notify the Medical Officer,
  *Watch* means repeat the measurement. I acknowledge Lindqvist's episode and it records who and when, with a note;
  if an Act alert stays unacknowledged for two days it is escalated. An alert stays open even if today's values are
  back to normal. Watch notices are sorted by z and the rest are grouped, to avoid alarm fatigue."
- "We generate the report for Earth: it stays **queued**. *(optional: move to day 105 and press 'Send queue';
  simulated transmission)*."

**2:15 – 2:45, Science**, *Step 9 (Validation lab)*
"How do we know it works? We tuned the cutoffs on 20 simulated missions and evaluated on **40 different ones**. The
*Act* level detected 98.9% of events with 0.78 false alarms per 30 astronaut-days; the fixed threshold, 88.9% with
1.87. But we are honest: on slow or large changes **the fixed threshold alerts earlier**, and if people are very
similar to each other, personalization adds nothing. This chart shows exactly **under which conditions** each method
wins."

**2:45 – 3:00, Impact and close**
"The same applies to Antarctica, submarines or Andean and Amazonian communities without a doctor. Zero G Health does not
diagnose: it tells each person, in plain words, what changed in *their* body and what follow-up to do, when Earth is
too far away."

---

**Honest note about day 32** (if someone checks Tanaka's history): Spec. Kenji Tanaka's (A4) **Act** alert on day 32
(PVT lapses, z = 4.5) does not match any injected event: his first event, a behavioral change, starts on day 52. It
is a genuine false positive of the detector. That is why the demo starts on day 40, outside the 7-day window of the
home page; if asked, use it to explain the measured rate: 0.78 false alarms per 30 astronaut-days at the Act level.

**If something fails**: if the interface says "The local engine is not responding", run `.\scripts\start.ps1` again.
If the data moved, `.\scripts\start.ps1 -Reset` restores exactly the same scenario (seed 7). In the public demo, use
"Reset demo".
