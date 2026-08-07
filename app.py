"""
Phase 4 — Streamlit dashboard (SRS FR-UI-1..FR-UI-7).

Sliders control solar/wind/battery capacity; the top section always shows Reactive vs.
Forecast-Driven side by side for the SAME capacities (the pitch's core claim, always
visible, no extra clicks) — the bottom section shows a detailed demand-vs-supply and
battery-SoC timeline for whichever mode/week is selected in the sidebar (FR-UI-3).

Run: streamlit run app.py
"""
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from sim.engine import (
    DEFAULT_BATTERY_MWH,
    DEFAULT_BATTERY_POWER_MW,
    DEFAULT_SOLAR_MW,
    DEFAULT_WIND_MW,
    PEAK_HOURS,
    run_simulation,
)

st.set_page_config(page_title="Renewable Energy Grid Simulator", page_icon="⚡", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
MODEL_PATH = Path(__file__).parent / "model" / "forecast_model.pkl"

if not (DATA_DIR / "demand.csv").exists():
    st.error("No synthetic data found. Run `python data_gen.py` first (Phase 1), then reload.")
    st.stop()
if not MODEL_PATH.exists():
    st.error("No trained forecasting model found. Run `python train_model.py` first (Phase 2), then reload.")
    st.stop()


def fmt_rs(amount: float) -> str:
    """Indian Lakh/Crore formatting — 'Rs 4,243,660,709' is not something a human reads at
    a glance; 'Rs 4.24 Crore' is. 1 Crore = 1,00,00,000; 1 Lakh = 1,00,000."""
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 1_00_00_000:
        return f"{sign}Rs {amount / 1_00_00_000:,.2f} Cr"
    if amount >= 1_00_000:
        return f"{sign}Rs {amount / 1_00_000:,.2f} L"
    return f"{sign}Rs {amount:,.0f}"


@st.cache_data(show_spinner=False)
def cached_run(solar, wind, batt_mwh, batt_mw, mode):
    return run_simulation(solar, wind, batt_mwh, batt_mw, mode=mode)


SAMPLE_WEEKS = {
    "June — summer": ("2025-06-09", "2025-06-15"),
    "January — winter": ("2025-01-13", "2025-01-19"),
    "April — shoulder season": ("2025-04-14", "2025-04-20"),
    "October — shoulder season": ("2025-10-13", "2025-10-19"),
}
PEAK_WINDOW_LABEL = f"{min(PEAK_HOURS)}:00–{max(PEAK_HOURS) + 1}:00"

st.title("⚡ Renewable Energy Grid Simulator")
st.caption(
    "AI-based demand forecasting for smarter renewable grid dispatch on a campus-scale "
    "microgrid — SDG 7 (Affordable & Clean Energy) & SDG 13 (Climate Action)"
)

with st.sidebar:
    st.header("Grid capacity")
    solar_mw = st.slider("Solar capacity (MW)", 0.0, 15.0, float(DEFAULT_SOLAR_MW), step=0.5)
    wind_mw = st.slider("Wind capacity (MW)", 0.0, 10.0, float(DEFAULT_WIND_MW), step=0.5)
    battery_mwh = st.slider("Battery capacity (MWh)", 0.0, 60.0, float(DEFAULT_BATTERY_MWH), step=2.0)
    battery_mw = st.slider("Battery power rating (MW)", 0.0, 15.0, float(DEFAULT_BATTERY_POWER_MW), step=0.5)

    st.divider()
    st.header("Detailed view")
    detail_mode_label = st.radio("Dispatch strategy to inspect", ["Reactive", "Forecast-Driven"], index=1)
    detail_mode = "reactive" if detail_mode_label == "Reactive" else "forecast_driven"
    week_label = st.selectbox("Sample week", list(SAMPLE_WEEKS.keys()))

    st.divider()
    with st.expander("ℹ️ How this works"):
        st.markdown(
            "- **Data**: 1 synthetic year (8,760 hours) of demand/solar/wind — see `data_gen.py`.\n"
            "- **Forecast**: a RandomForest model predicts demand 3h ahead, beating a naive "
            "'same hour yesterday' baseline by 63% lower error — see `train_model.py`.\n"
            "- **Reactive**: the battery reacts to the current hour only.\n"
            "- **Forecast-Driven**: the battery holds back charge when the model says a bigger "
            "peak is still coming, saving it for that peak instead of a smaller shortfall now.\n"
            "- **Why cost/CO₂ move but renewable % barely does**: shifting *when* the battery "
            "discharges can't change the *total* energy balance over a year — but it CAN shift "
            "fossil use away from the 6–10pm peak-tariff window (costlier, dirtier diesel-peaker "
            "power) toward cheaper, cleaner off-peak hours. Full reasoning in `DECISIONS.md`."
        )

with st.spinner("Running simulation..."):
    reactive = cached_run(solar_mw, wind_mw, battery_mwh, battery_mw, "reactive")
    forecast_driven = cached_run(solar_mw, wind_mw, battery_mwh, battery_mw, "forecast_driven")

# ---------------------------------------------------------------------------
# FR-UI-6: always-visible side-by-side comparison — the pitch's core claim.
# ---------------------------------------------------------------------------
st.subheader("Reactive vs. Forecast-Driven — same grid, same year")

cost_delta = forecast_driven.cost_saved_rs - reactive.cost_saved_rs
co2_delta = forecast_driven.co2_avoided_tons - reactive.co2_avoided_tons
peak_fossil_delta_pct = (
    100 * (forecast_driven.fossil_peak_mwh - reactive.fossil_peak_mwh) / reactive.fossil_peak_mwh
    if reactive.fossil_peak_mwh
    else 0.0
)

col_r, col_f = st.columns(2)
with col_r:
    st.markdown("#### 🔁 Reactive")
    st.caption("Battery reacts to the current hour only — no lookahead.")
    st.metric("Renewable utilization", f"{reactive.renewable_pct:.1f}%")
    st.metric("CO2 avoided / year", f"{reactive.co2_avoided_tons:,.1f} t")
    st.metric("Cost saved / year", fmt_rs(reactive.cost_saved_rs))
    st.metric(f"Fossil use in {PEAK_WINDOW_LABEL} peak", f"{reactive.fossil_peak_mwh:,.0f} MWh")
with col_f:
    st.markdown("#### 🤖 Forecast-Driven")
    st.caption("Battery uses the Phase 2 AI model's forecast to save charge for the real peak.")
    st.metric("Renewable utilization", f"{forecast_driven.renewable_pct:.1f}%")
    st.metric("CO2 avoided / year", f"{forecast_driven.co2_avoided_tons:,.1f} t", delta=f"{co2_delta:,.1f} t")
    st.metric("Cost saved / year", fmt_rs(forecast_driven.cost_saved_rs), delta=fmt_rs(cost_delta))
    st.metric(
        f"Fossil use in {PEAK_WINDOW_LABEL} peak",
        f"{forecast_driven.fossil_peak_mwh:,.0f} MWh",
        delta=f"{peak_fossil_delta_pct:+.1f}%",
        delta_color="inverse",
    )

peak_fossil_reduction_pct = -peak_fossil_delta_pct + 0.0  # "+0.0" avoids a -0.0 display
# artifact when peak_fossil_delta_pct is exactly 0 (e.g. battery power slider at 0, so both
# modes are identical) — found live-testing that edge case, where this rendered as "shifting
# -0.0% of fossil backup", not a real negative value.

st.info(
    f"With this capacity mix, Forecast-Driven dispatch saves an extra **{fmt_rs(cost_delta)}** and "
    f"avoids **{co2_delta:,.1f} more tons of CO₂** a year than Reactive dispatch — by shifting "
    f"**{peak_fossil_reduction_pct:.1f}%** of fossil backup use away from the expensive, high-emission "
    f"{PEAK_WINDOW_LABEL} peak window. Renewable utilization itself is similar between modes by "
    f"design (see ℹ️ *How this works* in the sidebar) — the real advantage is *when* "
    f"fossil backup gets used, not how much."
)

st.divider()

# ---------------------------------------------------------------------------
# FR-UI-4 / FR-UI-5: detailed timeline for the selected mode + sample week
# ---------------------------------------------------------------------------
result = forecast_driven if detail_mode == "forecast_driven" else reactive
start, end = SAMPLE_WEEKS[week_label]
week = result.timeline.loc[start:end].copy()
week["renewable_direct_mw"] = week["demand_mw"] - week["battery_discharge_mw"] - week["fossil_mw"]

st.subheader(f"Demand vs. supply — {detail_mode_label} mode, {week_label}")
fig = go.Figure()
fig.add_trace(go.Scatter(x=week.index, y=week["fossil_mw"], name="Fossil backup",
                          stackgroup="one", line=dict(width=0.5, color="#e03131")))
fig.add_trace(go.Scatter(x=week.index, y=week["battery_discharge_mw"], name="Battery discharge",
                          stackgroup="one", line=dict(width=0.5, color="#1971c2")))
fig.add_trace(go.Scatter(x=week.index, y=week["renewable_direct_mw"], name="Renewable (direct)",
                          stackgroup="one", line=dict(width=0.5, color="#2f9e44")))
fig.add_trace(go.Scatter(x=week.index, y=week["demand_mw"], name="Total demand",
                          line=dict(color="black", dash="dot")))
fig.update_layout(
    height=420, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="MW",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader(f"Battery state of charge — {detail_mode_label} mode, {week_label}")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=week.index, y=week["battery_soc_mwh"], name="Battery SoC",
                           fill="tozeroy", line=dict(color="#f08c00")))
fig2.add_hline(y=battery_mwh, line_dash="dash", line_color="gray", annotation_text="capacity")
fig2.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="MWh")
st.plotly_chart(fig2, use_container_width=True)

st.caption(
    "Synthetic data (Phase 1) and forecasting model (Phase 2) — see data_gen.py / train_model.py. "
    "Cost/CO₂ figures use a Time-of-Day peak-hour weighting; see DECISIONS.md for why that's the "
    "honest place forecast-driven dispatch's advantage shows up. Illustrative figures, not audited."
)
