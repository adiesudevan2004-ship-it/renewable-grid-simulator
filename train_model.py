"""
Phase 2 — Demand forecasting model (SRS FR-FM-1..FR-FM-5).

Trains a scikit-learn model to forecast demand HORIZON hours ahead of "now" (the point at
which the forecast is issued), using only features that would actually be known at that
moment (past demand, calendar fields) — never a future value. Compares it against a naive
"same hour, previous day" baseline, since the whole point of the Forecast-Driven simulation
mode (Phase 3) is that this model needs to demonstrably beat that baseline, not just exist.

HORIZON = 3h: long enough to matter for pre-charging the battery ahead of a peak, short
enough to stay forecastable from recent lag features.

Run:  python train_model.py
Output: model/forecast_model.pkl (model + feature list + horizon, bundled together so
        Phase 3 can't accidentally load a model with a mismatched feature order),
        model/accuracy_report.txt
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

DATA_DIR = Path(__file__).parent / "data"
MODEL_DIR = Path(__file__).parent / "model"
HORIZON = 3       # hours ahead being forecast
TEST_FRACTION = 0.2  # chronological (not random) split — this is time-series data
SEED = 42

FEATURE_COLS = [
    "hour", "dow", "month", "is_weekend",
    "demand_now", "lag_1h", "lag_24h", "lag_168h", "roll24_mean",
]


def build_features(demand: pd.Series) -> pd.DataFrame:
    """FR-FM-1: calendar features + lag values + rolling average, target = demand H ahead."""
    df = pd.DataFrame(index=demand.index)
    df["hour"] = demand.index.hour
    df["dow"] = demand.index.dayofweek
    df["month"] = demand.index.month
    df["is_weekend"] = (demand.index.dayofweek >= 5).astype(int)

    df["demand_now"] = demand
    df["lag_1h"] = demand.shift(1)
    df["lag_24h"] = demand.shift(24)
    df["lag_168h"] = demand.shift(168)
    df["roll24_mean"] = demand.shift(1).rolling(24).mean()

    df["target"] = demand.shift(-HORIZON)                 # actual demand at t+HORIZON
    df["naive_pred"] = demand.shift(24 - HORIZON)          # demand at (t+HORIZON)-24, i.e. "same hour yesterday"

    return df.dropna()


def main():
    MODEL_DIR.mkdir(exist_ok=True)
    demand = pd.read_csv(DATA_DIR / "demand.csv", index_col="timestamp", parse_dates=True)["demand_mw"]

    df = build_features(demand)
    split_idx = int(len(df) * (1 - TEST_FRACTION))
    train, test = df.iloc[:split_idx], df.iloc[split_idx:]

    X_train, y_train = train[FEATURE_COLS], train["target"]
    X_test, y_test = test[FEATURE_COLS], test["target"]

    model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=SEED, n_jobs=-1)
    model.fit(X_train, y_train)
    model_pred = model.predict(X_test)

    naive_pred = test["naive_pred"]

    def report(name, y_true, y_pred):
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        return mae, rmse

    model_mae, model_rmse = report("Model", y_test, model_pred)
    naive_mae, naive_rmse = report("Naive baseline", y_test, naive_pred)

    improvement_mae = 100 * (naive_mae - model_mae) / naive_mae
    improvement_rmse = 100 * (naive_rmse - model_rmse) / naive_rmse

    lines = [
        f"Forecast horizon: {HORIZON}h ahead",
        f"Train rows: {len(train)}   Test rows: {len(test)}  (chronological {int((1-TEST_FRACTION)*100)}/{int(TEST_FRACTION*100)} split)",
        "",
        f"{'Model':<20}{'MAE (MW)':>12}{'RMSE (MW)':>12}",
        f"{'RandomForest':<20}{model_mae:>12.2f}{model_rmse:>12.2f}",
        f"{'Naive (t-24+H)':<20}{naive_mae:>12.2f}{naive_rmse:>12.2f}",
        "",
        f"Model improvement over naive baseline: {improvement_mae:.1f}% lower MAE, {improvement_rmse:.1f}% lower RMSE",
    ]
    report_text = "\n".join(lines)
    print(report_text)

    (MODEL_DIR / "accuracy_report.txt").write_text(report_text, encoding="utf-8")

    joblib.dump(
        {"model": model, "feature_cols": FEATURE_COLS, "horizon": HORIZON},
        MODEL_DIR / "forecast_model.pkl",
    )
    print(f"\nSaved model/forecast_model.pkl and model/accuracy_report.txt")

    if improvement_mae <= 0:
        print(
            "\nWARNING: the trained model did not beat the naive baseline on MAE. "
            "Forecast-Driven mode in Phase 3 will not show a meaningful advantage over "
            "Reactive mode until this is fixed (more trees / different features / longer horizon check)."
        )


if __name__ == "__main__":
    main()
