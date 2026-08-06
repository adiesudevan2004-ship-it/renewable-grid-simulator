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

Phase 0 — scaffold. See the SRS for the full phased plan and requirement list.
