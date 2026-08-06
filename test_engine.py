"""
Phase 3 regression check — run after any change to sim/engine.py, data_gen.py, or
train_model.py. Not a full test suite, just the exit-check that matters most: does
Forecast-Driven mode genuinely, measurably beat Reactive mode on the same data?

An earlier version of engine.py failed this silently (both modes returned bit-for-bit
identical results) until this check would have caught it — see DECISIONS.md.

Run: python test_engine.py
"""
from sim.engine import run_simulation, DEFAULT_SOLAR_MW, DEFAULT_WIND_MW, DEFAULT_BATTERY_MWH, DEFAULT_BATTERY_POWER_MW


def main():
    reactive = run_simulation(
        DEFAULT_SOLAR_MW, DEFAULT_WIND_MW, DEFAULT_BATTERY_MWH, DEFAULT_BATTERY_POWER_MW, mode="reactive"
    )
    forecast_driven = run_simulation(
        DEFAULT_SOLAR_MW, DEFAULT_WIND_MW, DEFAULT_BATTERY_MWH, DEFAULT_BATTERY_POWER_MW, mode="forecast_driven"
    )

    checks = [
        ("Forecast-driven is NOT identical to reactive (the original bug)",
         reactive.cost_saved_rs != forecast_driven.cost_saved_rs),
        ("Forecast-driven cost saved >= reactive",
         forecast_driven.cost_saved_rs >= reactive.cost_saved_rs),
        ("Forecast-driven CO2 avoided >= reactive",
         forecast_driven.co2_avoided_tons >= reactive.co2_avoided_tons),
        ("Forecast-driven peak-hour fossil <= reactive",
         forecast_driven.fossil_peak_mwh <= reactive.fossil_peak_mwh),
        ("Renewable % is sane (0-100)", 0 <= reactive.renewable_pct <= 100),
        ("No negative fossil/demand totals",
         reactive.total_fossil_mwh >= 0 and reactive.total_demand_mwh > 0),
    ]

    print(f"{'Reactive':<20}cost_saved=Rs{reactive.cost_saved_rs:,.0f}  co2={reactive.co2_avoided_tons:,.0f}t  "
          f"renewable%={reactive.renewable_pct:.2f}  fossil_peak={reactive.fossil_peak_mwh:,.0f}MWh")
    print(f"{'Forecast-driven':<20}cost_saved=Rs{forecast_driven.cost_saved_rs:,.0f}  co2={forecast_driven.co2_avoided_tons:,.0f}t  "
          f"renewable%={forecast_driven.renewable_pct:.2f}  fossil_peak={forecast_driven.fossil_peak_mwh:,.0f}MWh")
    cost_delta = 100 * (forecast_driven.cost_saved_rs - reactive.cost_saved_rs) / reactive.cost_saved_rs
    peak_delta = 100 * (forecast_driven.fossil_peak_mwh - reactive.fossil_peak_mwh) / reactive.fossil_peak_mwh
    print(f"Cost saved improvement: {cost_delta:+.2f}%   Peak-hour fossil change: {peak_delta:+.2f}%")
    print()

    passed = 0
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        passed += ok
    print(f"\n{passed}/{len(checks)} checks passed")

    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
