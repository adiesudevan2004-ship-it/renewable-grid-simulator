# Work split — 2 people

The core build (Phases 0-5) is already done and verified. This divides ownership so each
person can genuinely explain and defend their half to the guide — not an even split of
lines of code, an even split of **things you can be asked about and answer confidently**.

**Member 1 — Adwaith S Dev (System ID: 2024418186)** — "Data & Intelligence"
**Member 2 — Gaurav Rustagi (System ID: 2024519071)** — "Simulation & Experience"

Assigned in the order names were given, not by any tested skill fit — swap the two sections'
content below (keeping the names as-is) if either of you would rather take the other half.

---

## Member 1 — Adwaith S Dev (2024418186) — Data & Intelligence

**Owns:** `data_gen.py`, `train_model.py`, `data/`, `model/`
**SRS sections:** FR-DG-1..5 (Data Generation), FR-FM-1..5 (Forecasting Model) — [SRS §3.1.1, §3.1.2]

You should be able to explain, unprompted:
- Why demand/solar/wind are generated the way they are (daily double-peak, weekday/weekend
  split, the twice-yearly seasonal pattern, cloud-cover noise, wind's AR(1) persistence)
- **The two-cosine cancellation bug** in the seasonal curve (`DECISIONS.md`) — a great "here's
  a real bug I found and fixed" story for a viva
- Why solar/wind are stored as **capacity factors** (0-1), not MW — so the simulation can
  scale them by whatever capacity the dashboard sliders pick
- The forecasting model's feature set (lags, rolling average, calendar fields), why HORIZON=3h,
  and the chronological (not random) train/test split
- The headline result: **63% lower MAE than the naive "yesterday same hour" baseline**
- The honest ablation finding in `DECISIONS.md` — a naive forecast captures ~90% of the
  simulation-level benefit; the ML model's real edge is its raw accuracy, which would matter
  more on real (less regular) utility data

**Remaining tasks:**
- [ ] Write the report's Data Generation + Forecasting Model sections (can lift directly from
      `data_gen.py`/`train_model.py` docstrings and `DECISIONS.md`)
- [ ] Rehearse explaining the accuracy comparison table (`model/accuracy_report.txt`)
- [ ] Optional stretch: try substituting a real public dataset for one piece (e.g. real solar
      irradiance data for one city) and compare — strengthens the "could this scale to real
      data" answer in `DEMO_SCRIPT.md`

## Member 2 — Gaurav Rustagi (2024519071) — Simulation & Experience

**Owns:** `sim/engine.py`, `app.py`, `test_engine.py`
**SRS sections:** FR-SE-1..6 (Simulation Engine), FR-UI-1..7 (Dashboard) — [SRS §3.1.3, §3.1.4]

You should be able to explain, unprompted:
- The Reactive vs. Forecast-Driven dispatch rule (`HOLD_BACK_FRACTION`, `PEAK_AHEAD_THRESHOLD`)
- **The energy-conservation bug** (`DECISIONS.md`) — the two modes were bit-for-bit identical
  at first, why that happened, and why the Time-of-Day peak/off-peak fix is the honest
  solution, not a workaround
- Why renewable % stays ~flat between modes but cost/CO2 don't — the single most likely
  question from the guide
- How the dashboard is wired (sliders → `cached_run()` → side-by-side comparison → timeline
  charts) and the performance fix (caching the model load: 5.7s → 0.26s per interaction)
- The microgrid rescale (60MW → 5MW) and why the ₹18/kWh backup-cost assumption is realistic,
  not inflated

**Remaining tasks:**
- [ ] Write the report's Simulation Engine + Dashboard sections
- [ ] Own the **live demo delivery** — rehearse `DEMO_SCRIPT.md` end to end, including the
      "remove the battery" move that shows the effect honestly collapsing to zero
- [ ] Take the screenshots/recording for the report from the running dashboard

## Shared

- [ ] SRS (`docs/SRS.docx` or wherever your copy lives) — both review, since both wrote
      requirements you're each implementing
- [ ] Final report intro/conclusion, SDG alignment section
- [ ] `test_engine.py` + the boundary stress-test sweep — both should run it once locally and
      understand what "6/6 checks passed" is actually asserting
- [ ] Slide deck — one slide per phase is a natural structure; whoever owns that phase drafts
      its slide

---

## A note on git attribution

Every commit so far is under one git identity, since this was built in a single session. If
your evaluation looks at commit history as evidence of contribution, going forward each of
you should commit under your own identity from your own machine:

```bash
git config user.name "Your Name"
git config user.email "your@email.com"
```

(run inside the `renewable-grid-simulator/` folder — this sets it for this repo only, not
globally). From here on, make your own commits into your own module (Member 1 commits inside
`data_gen.py`/`train_model.py`/`data/`/`model/`, Member 2 inside `sim/`/`app.py`) so the log
reflects the split above.
