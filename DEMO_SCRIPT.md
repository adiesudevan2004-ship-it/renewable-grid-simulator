# Demo script — live walkthrough

Keep this open on a second screen/phone while presenting. Total time: ~3 minutes. Run
`streamlit run app.py` before you start so it's already loaded — the first request after
starting the server takes ~5-6s (loading the trained model), everything after that is
near-instant.

## 1. Open with the comparison, not the sliders (30s)

Don't touch anything yet. Point at the two columns already on screen:

> "This is a full year of a campus-scale microgrid — solar, wind, a battery, and real hourly
> demand. Same grid, same year, two different ways of deciding when the battery charges and
> discharges. Reactive just reacts to right now. Forecast-Driven uses an AI model to know a
> demand peak is coming a few hours ahead, and saves battery charge for it instead of
> spending it early."

Point at the **Cost saved / year** and **Fossil use in peak** deltas: "That's the entire
pitch in two numbers — same hardware, smarter timing, real Rupees and real CO2."

## 2. Move a slider live (60s)

Drag **Solar capacity** up (e.g. 6 → 12 MW). Narrate while it updates:

> "If we double the solar array... [numbers update] ...renewable utilization jumps, and
> notice the Forecast-Driven advantage gets *bigger*, not smaller — more capacity means more
> surplus to work with, so smarter timing matters more, not less."

Drag **Battery capacity** to near 0, then back up:

> "And if I take the battery away almost entirely... [advantage collapses toward zero] ...the
> two strategies become identical. That's expected and it's honest — the AI model isn't
> magic, it's specifically valuable *because* there's a battery whose timing can be optimized.
> No battery, nothing to optimize."

**This second move is worth doing deliberately** — it pre-empts the obvious "is this just
made up" question by showing the effect behaves exactly how the underlying mechanism
predicts it should.

Reset both sliders back to default (double-click each, or drag back) before continuing.

## 3. Show the timeline chart (45s)

Switch the sidebar's **Sample week** to "January — winter", dispatch strategy to
"Forecast-Driven". Point at the stacked area chart:

> "Green is renewable meeting demand directly, blue is the battery, red is fossil backup.
> Watch the evening ramp — that's exactly where the battery is choosing to hold back a little
> early on, so it has more available right at the peak."

Flip the radio to "Reactive" on the same week and back — the visual difference in *when* red
(fossil) appears is the whole story in one glance.

## 4. Close on SDG framing + honesty (30s)

> "This maps directly to SDG 7 and SDG 13 — better utilization of the same renewable capacity,
> and a real, quantified CO2 reduction. And I want to be upfront about one thing: the AI
> model's edge over a simple 'yesterday same hour' guess is real but modest on this synthetic
> data, because the data is fairly regular. Real-world demand has more irregularity — weather
> shocks, events — where I'd expect the ML model's accuracy advantage, which is a full 63%
> lower error than the naive guess, to matter more. That's a direction for future validation
> against real utility data."

That last line pre-empts a sharp guide's "would this actually hold up on real data" question
by answering it before it's asked — see `DECISIONS.md`'s ablation section for the numbers
behind this claim.

## Anticipated questions

- **"Why doesn't renewable % change between the two modes?"** → Because redistributing *when*
  the battery discharges can't change the *total* energy balance over a full year (energy
  conservation) — the real advantage is *when* fossil backup is used (peak vs. off-peak
  tariff/emissions), not how much. Full reasoning in `DECISIONS.md`.
- **"Is this real data?"** → No, synthetic — deliberately, so the demo works offline and
  reliably regardless of venue Wi-Fi (see the SRS, Section 2.5). Realistic patterns (daily
  double-peak, weekday/weekend, seasonal, cloud/wind weather noise), not real utility
  readings.
- **"What's the Rs figure based on?"** → An illustrative diesel-backup cost (Rs18/kWh) and a
  real Indian DISCOM Time-of-Day peak-tariff structure (6-10pm costs more) — see
  `sim/engine.py`'s constants and `DECISIONS.md`'s scale sanity-check.
- **"Could this scale to a real grid?"** → The architecture (Data → Forecast → Simulation →
  Dashboard, see the SRS's Section 4) doesn't assume synthetic data — swapping in a real
  demand/weather dataset only changes Phase 1's data generation module, nothing downstream.
