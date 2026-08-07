# Design decisions log

Non-obvious decisions made while building, and why — so they don't get silently relitigated
or misremembered later. Mirrors how the SRS's phased plan maps to `sim/engine.py`
(FR-SE-1..FR-SE-6).

## Reactive vs. Forecast-Driven: the energy-conservation bug (Phase 3)

**What happened:** the first working version of `sim/engine.py` had Forecast-Driven mode
hold back battery discharge when a bigger demand peak was still forecast ahead, spending the
smaller shortfall on fossil instead and saving the battery for the real peak. Reasonable-
sounding — and it produced **bit-for-bit identical annual totals** to Reactive mode. Not a
rounding effect: identical to 6 decimal places.

**Root cause:** charging behaviour is identical in both modes (there's never a reason to
turn down free renewable surplus), so total annual energy captured by the battery is fixed
regardless of dispatch mode. Whatever charge gets "held back" in one hour simply gets
discharged in some other hour instead — nothing is wasted, so total annual discharge (and
therefore total annual fossil MWh) is a near-fixed quantity, invariant to *when* you choose
to discharge. Redistributing discharge timing alone cannot move that total. This is a real
mathematical property of the system, not a bug in the loop logic.

**The fix:** stopped trying to move the *total* fossil MWh, and instead made the *value* of
avoiding it depend on *when* it's avoided — modelling a real Indian DISCOM Time-of-Day (ToD)
tariff structure (18:00–22:00 = peak, everything else = off-peak), with a peak-hour cost
multiplier (1.6x) and CO2 multiplier (1.3x) representing costlier/dirtier diesel-peaker
backup vs. cheaper/cleaner baseload. Forecast-Driven mode's hold-back logic genuinely does
shift battery coverage toward the expensive/dirty peak window and fossil use toward the
cheap/clean off-peak window — same total energy, real cost/CO2 advantage. `renewable_pct`
and `total_fossil_mwh` are intentionally near-identical between modes (that's the honest
result of the argument above, not a leftover bug) — `cost_saved_rs` and `co2_avoided_tons`
are where the real difference shows up, plus the `fossil_peak_mwh` breakdown.

**Sizing matters:** this only shows up at all if the battery is large enough, relative to
demand, to actually be a meaningful lever. At the original small defaults (15 MW / 60 MWh
against ~58 MW average demand) the yearly battery throughput was ~1,000 MWh against ~378,000
MWh of fossil — under 0.3% of the picture, so no dispatch policy could move the needle
visibly. Defaults were resized to 60 MW / 300 MWh (see `sim/engine.py`'s `DEFAULT_*`
constants) specifically so the dashboard sliders demo something real.

## Ablation check: is this really "AI", or would any dumb rule do the same thing?

Ran a direct comparison with three variants at the final tuned settings:

| Dispatch | Cost saved vs. Reactive |
|---|---|
| Reactive (no forecast at all) | baseline |
| Forecast-driven using a **naive** "same hour yesterday" guess | +1.99% |
| Forecast-driven using the **real trained RandomForest** (Phase 2) | +2.20% |

**Honest finding:** most of the benefit (≈90%) comes from having *any* forward-looking
signal at all, not specifically from the ML model's superior accuracy — because this
project's synthetic demand data is quite regular (the same daily/weekly pattern repeats with
only mild noise), so even "yesterday, same hour" is already a strong predictor of "is a
bigger peak still coming." The ML model's real, decisive advantage is Phase 2's raw
forecast accuracy (63% lower MAE than naive) — that comparison stands on its own regardless
of this simulation. The simulation-level AI-vs-naive gap is smaller specifically *because*
synthetic data this regular doesn't give an ML model much irregularity to exploit; real
utility demand (weather shocks, special events, holidays) has more of exactly the
irregularity where a genuinely learned model would pull further ahead of a naive rule. This
nuance is worth stating plainly in the report/demo rather than overclaiming — it's a more
credible, defensible story than pretending the gap is larger than it measured.

## HOLD_BACK_FRACTION / PEAK_AHEAD_THRESHOLD tuning

`HOLD_BACK_FRACTION = 0.15`, `PEAK_AHEAD_THRESHOLD = 1.02` were chosen empirically by sweeping
several combinations against the default capacities and picking the pair that produced a
clear, demo-visible effect (~1.8% cost improvement, ~7% peak-hour fossil reduction) without
being so aggressive it reads as an arbitrarily rigged knob. See `sim/engine.py`'s comments
for the exact meaning of each.

## Grid scale rescale — 60MW to 5MW (Phase 5 polish)

The first four phases were built and verified against `MEAN_DEMAND_MW = 60` (peak ~108 MW).
That's small-city/regional-grid scale, not a microgrid — and it made the dashboard's cost
figures balloon into the billions of Rupees, which would have visibly contradicted the
pitch's own "simulated microgrid" framing the moment a guide looked at the numbers.

Rescaled to `MEAN_DEMAND_MW = 5` (peak ~9 MW) — genuine large-campus/small-community
microgrid territory — and regenerated data (Phase 1) + retrained the model (Phase 2) at the
new scale (model accuracy improvement over naive baseline: unchanged at 63%, as expected —
a linear rescale of demand doesn't change the *relative* pattern the model has to learn).
Capacity defaults in `sim/engine.py` were rescaled proportionally (same solar/wind/battery-
to-demand ratios as the 60MW version). Re-ran `test_engine.py` after rescaling — same
relative effect size (+1.9% cost, -8.2% peak-hour fossil), confirming the tuned
`HOLD_BACK_FRACTION`/`PEAK_AHEAD_THRESHOLD` constants transfer across scale.

**Sanity-checked the resulting absolute number isn't just "smaller but still fake":**
₹18,000/MWh (₹18/kWh) for fossil backup is actually a *conservative* estimate for
continuous diesel-genset fuel cost alone at MW scale (real-world large gensets run
~0.25–0.3 L/kWh, and diesel is ~₹90–100/L in India, i.e. ~₹22.50–30/kWh on fuel alone,
before capex/maintenance). At default capacities: total demand ≈42,400 MWh/year, of which
renewable+battery covers ≈45% (≈19,100 MWh) — a full all-diesel baseline would cost
≈₹76 Cr/year, of which ≈₹37.5 Cr/year is what renewable+battery actually avoids (the
`cost_saved_rs` figure the dashboard shows). Both are believable order-of-magnitude figures
for real diesel economics at this scale, not inflated by the rescale — verified directly
against `run_simulation()`'s output rather than estimated, after an earlier draft of this
note had the baseline and avoided-cost figures backwards.

## Seasonal demand curve — two-cosine cancellation bug (Phase 1)

First version of `generate_demand()`'s seasonal factor summed two independently-phased
12-month cosines (one peaking in winter, one in summer). They *partially cancelled each
other out* at each peak (each term is near its own opposite-phase minimum exactly when the
other term peaks), producing an almost-flat monthly average that didn't visibly read as
seasonal on the summary chart. Fixed by using a single 6-month-period cosine instead
(`cos(4π(day-15)/365)`), which genuinely peaks twice a year (mid-Jan, mid-Jul) with a
shared trough at the shoulder months — see `data_gen.py`'s comment for the exact reasoning.
