# Renewable Energy Grid Simulator

An interactive microgrid simulator that shows how AI-based demand forecasting reduces
reliance on fossil-fuel backup power — aligned with **SDG 7** (Affordable & Clean Energy)
and **SDG 13** (Climate Action).

Sliders control solar/wind/battery capacity; the dashboard shows the live effect on
renewable utilization %, CO2 emissions avoided, and cost saved — comparing a **Reactive**
dispatch strategy (no forecasting) against a **Forecast-Driven** one (battery scheduled
ahead of predicted demand).

Full requirements: see `docs/SRS.docx` (or the copy the guide has).

## Project structure

```
data/           synthetic demand/solar/wind datasets (generated, gitignored)
model/          trained forecasting model + accuracy report (generated, gitignored)
sim/            simulation engine (reactive vs forecast-driven dispatch logic)
notebooks/      scratch analysis / plots used while building each phase
app.py          Streamlit dashboard (entry point)
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Build order (see SRS Section 6 for full detail)

1. `python data_gen.py` — generates a year of synthetic hourly demand/solar/wind → `data/`
2. `python train_model.py` — trains the forecasting model + naive baseline → `model/`
3. `sim/engine.py` — reactive vs. forecast-driven simulation logic (imported by the app)
4. `streamlit run app.py` — launches the dashboard

## Status

Phases 0-4 done and verified end-to-end (data generation, forecasting model, simulation
engine, dashboard). See [DECISIONS.md](DECISIONS.md) for the non-obvious design calls made
along the way — in particular, why Forecast-Driven mode's advantage shows up in cost/CO₂
rather than raw renewable %, and the honest AI-vs-naive-forecast ablation result.

Remaining: Phase 5 polish (visual pass, full demo rehearsal, report/slides). Reliability
already stress-tested — 14/14 boundary capacity combinations (all-zero, all-max, zero
battery, etc.) run cleanly with no crashes or NaN output.

To run:
```bash
python data_gen.py        # regenerate synthetic data (only needed once, or after changing data_gen.py)
python train_model.py     # retrain the forecasting model (only needed once, or after changing it)
python test_engine.py     # regression check: forecast-driven genuinely beats reactive
streamlit run app.py      # launch the dashboard
```
