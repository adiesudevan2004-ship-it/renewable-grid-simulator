"""
Renewable Energy Grid Simulator — Streamlit dashboard entry point.

Phase 0: scaffold only. This will grow into the full dashboard (FR-UI-1..7 in the SRS):
capacity sliders, reactive/forecast-driven mode toggle, supply-vs-demand chart, battery
SoC chart, and the renewable %/CO2 avoided/cost saved stat tiles.
"""
import streamlit as st

st.set_page_config(page_title="Renewable Energy Grid Simulator", page_icon="⚡", layout="wide")

st.title("⚡ Renewable Energy Grid Simulator")
st.caption("AI-based demand forecasting for smarter renewable grid dispatch — SDG 7 & SDG 13")

st.success("Hello grid! Phase 0 scaffold is running.")
st.info(
    "Next up — Phase 1: generate a year of synthetic hourly demand/solar/wind data "
    "(`data_gen.py`), then Phase 2's forecasting model, Phase 3's simulation engine, "
    "and finally the real controls/charts here."
)
