"""
Phase 1 — Synthetic data generation (SRS FR-DG-1..FR-DG-5).

Generates one year of realistic-looking hourly electricity demand, plus solar and wind
CAPACITY FACTORS (0-1, not MW) — the Simulation Engine (Phase 3) scales these by whatever
capacity the user sets on the dashboard sliders, per FR-SE-1. Keeping solar/wind as
capacity factors here (rather than baking in a fixed MW capacity) is what lets the
dashboard sliders work without regenerating data.

Run:  python data_gen.py
Output: data/demand.csv, data/solar.csv, data/wind.csv, data/summary_plots.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 42
YEAR = 2025  # arbitrary non-leap reference year -> 365 days * 24h = 8,760 hourly records
DATA_DIR = Path(__file__).parent / "data"

MEAN_DEMAND_MW = 60.0  # nominal microgrid scale — tune to taste, doesn't need to match a real grid


def _time_index():
    return pd.date_range(f"{YEAR}-01-01", periods=365 * 24, freq="h")


def _daily_weather_noise(n_days, rng, persistence=0.85, scale=1.0):
    """Smooth day-to-day random-walk factor (weather persistence), one value per day."""
    walk = np.zeros(n_days)
    walk[0] = rng.normal(0, scale)
    for i in range(1, n_days):
        walk[i] = persistence * walk[i - 1] + rng.normal(0, scale * (1 - persistence))
    return walk


def generate_demand(index, rng):
    """FR-DG-1: daily double-peak + weekday/weekend + seasonal variation + noise."""
    hour = index.hour.values
    dow = index.dayofweek.values  # 0=Mon .. 6=Sun
    day_of_year = index.dayofyear.values
    is_weekend = dow >= 5

    morning = 0.85 * np.exp(-((hour - 8) ** 2) / (2 * 2.2 ** 2))
    evening = 1.00 * np.exp(-((hour - 19) ** 2) / (2 * 2.6 ** 2))
    daily_shape = 0.55 + morning + evening  # ~0.55 (3am trough) to ~1.55 (7pm peak)

    weekday_factor = np.where(is_weekend, 0.87, 1.0)  # less commercial/industrial load

    # Twice-yearly (period 365/2) cosine: peaks at day~15 (mid-Jan, heating) AND day~197
    # (mid-Jul, cooling), trough at the shoulder months (~Apr, ~Oct) in between. Using one
    # 6-month-period term instead of two independently-phased 12-month terms avoids them
    # partially cancelling each other out at each peak (an earlier version of this did that
    # by accident, which made the seasonal swing barely visible on the summary chart).
    seasonal_factor = 1.0 + 0.12 * np.cos(4 * np.pi * (day_of_year - 15) / 365)

    n_days = 365
    weather = _daily_weather_noise(n_days, rng, persistence=0.85, scale=0.04)
    weather_hourly = np.repeat(weather, 24)
    hourly_noise = rng.normal(1.0, 0.02, size=len(index))

    demand_mw = (
        MEAN_DEMAND_MW
        * daily_shape
        * weekday_factor
        * seasonal_factor
        * (1 + weather_hourly)
        * hourly_noise
    )
    demand_mw = np.clip(demand_mw, MEAN_DEMAND_MW * 0.25, None)
    return pd.Series(demand_mw, index=index, name="demand_mw")


def generate_solar(index, rng):
    """FR-DG-2: bounded by daylight hours, seasonal amplitude, cloud-cover noise."""
    hour = index.hour.values + index.minute.values / 60.0
    day_of_year = index.dayofyear.values

    daylight_hours = 12 + 2.5 * np.cos(2 * np.pi * (day_of_year - 172) / 365)
    sunrise = 12 - daylight_hours / 2
    sunset = 12 + daylight_hours / 2
    frac = (hour - sunrise) / (sunset - sunrise)
    shape = np.clip(np.sin(np.pi * np.clip(frac, 0, 1)), 0, None)
    shape = np.where((hour > sunrise) & (hour < sunset), shape, 0.0)

    seasonal_amp = 0.75 + 0.25 * np.cos(2 * np.pi * (day_of_year - 172) / 365)

    n_days = 365
    is_cloudy_day = rng.random(n_days) < 0.15  # ~15% of days overcast
    clear_factor = rng.uniform(0.85, 1.0, n_days)
    cloudy_factor = rng.uniform(0.25, 0.65, n_days)
    daily_cloud_factor = np.where(is_cloudy_day, cloudy_factor, clear_factor)
    cloud_hourly = np.repeat(daily_cloud_factor, 24)

    hourly_noise = rng.normal(1.0, 0.03, size=len(index))

    cf = shape * seasonal_amp * cloud_hourly * hourly_noise
    return pd.Series(np.clip(cf, 0, 1), index=index, name="solar_cf")


def generate_wind(index, rng):
    """FR-DG-3: semi-random (AR(1) wind speed -> power-curve), independent of time of day."""
    day_of_year = index.dayofyear.values
    n = len(index)

    seasonal_wind_factor = 1.0 + 0.15 * np.cos(2 * np.pi * (day_of_year - 15) / 365)  # windier in winter

    mean_speed, phi = 7.0, 0.90  # m/s, hour-to-hour persistence
    speed = np.zeros(n)
    speed[0] = mean_speed
    innovations = rng.normal(0, 1.4, n)
    for t in range(1, n):
        speed[t] = mean_speed + phi * (speed[t - 1] - mean_speed) + innovations[t]
    speed = np.clip(speed, 0, None) * seasonal_wind_factor

    cut_in, rated, cut_out = 3.0, 12.0, 25.0  # typical small-turbine power curve, m/s
    cf = np.zeros(n)
    ramp = (speed >= cut_in) & (speed < rated)
    full = (speed >= rated) & (speed < cut_out)
    cf[ramp] = ((speed[ramp] - cut_in) / (rated - cut_in)) ** 3
    cf[full] = 1.0
    return pd.Series(np.clip(cf, 0, 1), index=index, name="wind_cf")


def make_summary_plot(demand, solar, wind, out_path):
    """FR-DG-5: summary plots so the dataset can be visually sanity-checked."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 9))

    week = slice(f"{YEAR}-06-09", f"{YEAR}-06-15")
    axes[0].plot(demand[week].index, demand[week].values, color="#d9480f")
    axes[0].set_title("Demand — sample week, June (MW)")

    axes[1].plot(solar[week].index, solar[week].values, color="#f08c00", label="solar CF")
    axes[1].plot(wind[week].index, wind[week].values, color="#1971c2", label="wind CF", alpha=0.7)
    axes[1].set_title("Solar & wind capacity factor — sample week, June")
    axes[1].legend()

    monthly_demand = demand.resample("ME").mean()
    axes[2].bar(monthly_demand.index.strftime("%b"), monthly_demand.values, color="#495057")
    axes[2].set_title("Average demand by month (MW) — seasonal sanity check")

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    index = _time_index()

    demand = generate_demand(index, rng)
    solar = generate_solar(index, rng)
    wind = generate_wind(index, rng)

    demand.to_frame().rename_axis("timestamp").to_csv(DATA_DIR / "demand.csv")
    solar.to_frame().rename_axis("timestamp").to_csv(DATA_DIR / "solar.csv")
    wind.to_frame().rename_axis("timestamp").to_csv(DATA_DIR / "wind.csv")

    make_summary_plot(demand, solar, wind, DATA_DIR / "summary_plots.png")

    print(f"Generated {len(index)} hourly records ({index[0].date()} .. {index[-1].date()})")
    print(f"Demand  MW — min {demand.min():.1f}  mean {demand.mean():.1f}  max {demand.max():.1f}")
    print(f"Solar   CF — mean {solar.mean():.3f}  max {solar.max():.3f}")
    print(f"Wind    CF — mean {wind.mean():.3f}  max {wind.max():.3f}")
    print(f"Saved CSVs + summary_plots.png to {DATA_DIR}/")


if __name__ == "__main__":
    main()
