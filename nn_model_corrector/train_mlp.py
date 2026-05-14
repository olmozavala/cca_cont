from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

from nn_model_corrector.dataset_generator import DEFAULT_CONFIG_PATH, generate_dataset, load_config, rmse


def train_from_dataset(dataset: pd.DataFrame, test_fraction: float = 0.2) -> dict[str, float]:
    """Train a small MLPRegressor and return baseline/model RMSE metrics."""
    try:
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import mean_squared_error
        from sklearn.neural_network import MLPRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install scikit-learn to train the MLP model") from exc

    feature_cols = [col for col in dataset.columns if col.startswith("forecast_")]
    clean = dataset.dropna(subset=["target_max_otres"]).copy()
    if len(clean) < 5:
        raise ValueError("Need at least 5 samples with targets to train/test an MLP")

    split_idx = max(1, min(len(clean) - 1, int(len(clean) * (1 - test_fraction))))
    train = clean.iloc[:split_idx]
    test = clean.iloc[split_idx:]

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42),
    )
    model.fit(train[feature_cols], train["target_max_otres"])
    predictions = model.predict(test[feature_cols])

    model_rmse = math.sqrt(mean_squared_error(test["target_max_otres"], predictions))
    baseline_rmse = rmse(test["target_max_otres"], test["baseline_forecast_max"])
    return {
        "train_samples": float(len(train)),
        "test_samples": float(len(test)),
        "baseline_rmse": baseline_rmse,
        "mlp_rmse": model_rmse,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train a simple MLP for OTRES daily max correction.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to dataset YAML config.")
    parser.add_argument("--dataset", default=None, help="Use an existing dataset CSV instead of querying DB.")
    args = parser.parse_args()

    if args.dataset:
        dataset = pd.read_csv(args.dataset)
    else:
        dataset = generate_dataset(load_config(args.config))

    metrics = train_from_dataset(dataset)
    print(f"Train samples: {int(metrics['train_samples'])}")
    print(f"Test samples: {int(metrics['test_samples'])}")
    print(f"Baseline RMSE: {metrics['baseline_rmse']:.4f}")
    print(f"MLP RMSE: {metrics['mlp_rmse']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

