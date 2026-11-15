<template>
  <div class="page en" lang="en">
    <header class="page-head"><h1>BASAL · Autonomous crew health monitoring</h1></header>

    <section class="intro">
      <p class="lede">Each astronaut is compared with <b>their own baseline</b>. BASAL flags when a health indicator stops being
        normal for that person, explains what changed and suggests a conservative follow-up — on board, without Internet.</p>
      <dl class="pitch">
        <div><dt>Problem</dt><dd>On the way to Mars a message takes up to 20 min each way and there are blackouts: Earth cannot watch crew health in real time.</dd></div>
        <div><dt>Solution</dt><dd>Personal baselines (robust z-score: median and MAD of each astronaut's own history) on six indicators, with explainable alerts and an onboard medical-officer workflow.</dd></div>
        <div><dt>Evidence</dt><dd>On 40 simulated missions held out from tuning, the "act" level detects <b>98.9%</b> of injected events with
          <b>0.78</b> false-alarm episodes per 30 astronaut-days. A fixed population threshold: 88.9% and 1.87. <i>Simulated data.</i></dd></div>
      </dl>
    </section>

    <section>
      <div class="sec-h"><h2>What it monitors</h2></div>
      <div class="table-wrap"><table class="table">
        <thead><tr><th>Indicator</th><th>Sensor</th><th>Worrying when it</th></tr></thead>
        <tbody>
          <tr><td>Resting heart rate</td><td>Wearable ECG</td><td>rises</td></tr>
          <tr><td>Heart rate variability (RMSSD)</td><td>Wearable ECG, sleep</td><td>falls</td></tr>
          <tr><td>Sleep duration</td><td>Actigraphy</td><td>falls</td></tr>
          <tr><td>Radiation dose rate</td><td>Personal dosimeter</td><td>rises</td></tr>
          <tr><td>PVT-B lapses and false starts</td><td>3-min tablet test</td><td>rises</td></tr>
          <tr><td>Mood (self-report)</td><td>Daily check-in</td><td>falls</td></tr>
        </tbody>
      </table></div>
    </section>

    <section>
      <div class="sec-h"><h2>How to read the demo</h2></div>
      <ul class="steps">
        <li><b>Watch</b> (amber) = repeat the measurement. <b>Act</b> (dark amber) = notify the medical officer. Levels always show an icon and text, never color alone.</li>
        <li>An alert stays open until the medical officer acknowledges, postpones or resolves it, even if today's values are back to normal.</li>
        <li>"Simulate blackout" keeps detection running on board; reports wait in the queue until the link returns.</li>
        <li>Cutoffs (watch |z| ≥ 2.5, act ≥ 4.5 or 3 days in watch) are experimental parameters tuned on simulation, not clinical limits.</li>
        <li>Educational prototype, not a medical device. No diagnosis or medication is ever suggested.</li>
      </ul>
      <div class="row wrap go">
        <router-link class="btn primary" to="/">Open the demo</router-link>
        <router-link class="btn" to="/lab/validation">Validation results</router-link>
      </div>
    </section>
  </div>
</template>

<style scoped>
.en { max-width: 900px; }
.intro { display: grid; gap: 18px; }
.lede { font-family: var(--serif); font-size: 1.35rem; line-height: 1.4; margin: 0; }
.pitch { margin: 0; display: grid; gap: 10px; border-left: 2px solid var(--blue); padding-left: 14px; }
.pitch div { display: grid; grid-template-columns: 90px minmax(0, 1fr); gap: 10px; }
.pitch dt { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--blue); padding-top: 3px; }
.pitch dd { margin: 0; color: var(--text-2); line-height: 1.5; }
.pitch dd b { color: var(--ink); }
.steps { margin: 0; padding-left: 18px; display: grid; gap: 8px; color: var(--text-2); line-height: 1.5; }
.go { margin-top: 16px; gap: 10px; }
@media (max-width: 640px) { .pitch div { grid-template-columns: 1fr; gap: 2px; } .lede { font-size: 1.15rem; } }
</style>
