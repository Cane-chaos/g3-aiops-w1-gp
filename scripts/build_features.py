from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_cart_metrics(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "metrics" / "cart-service.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def build_cart_features(cart: pd.DataFrame, window: int = 120) -> pd.DataFrame:
    features = cart.copy()
    features["memory_mb"] = features["memory_usage_bytes"] / 1024 / 1024
    features["memory_pct"] = features["memory_usage_bytes"] / features["memory_limit_bytes"] * 100
    features["memory_rate_mb_per_min"] = features["memory_mb"].diff() * 2
    features["latency_rate_ms_per_min"] = features["http_p99_latency_ms"].diff() * 2
    features["gc_rate_ms_per_min"] = features["jvm_gc_pause_ms_avg"].diff() * 2

    for col in ["memory_mb", "memory_pct", "jvm_gc_pause_ms_avg", "http_p99_latency_ms", "http_5xx_rate"]:
        rolling = features[col].rolling(window, min_periods=10)
        mean = rolling.mean()
        std = rolling.std().replace(0, np.nan)
        features[f"{col}_rolling_mean_1h"] = mean
        features[f"{col}_rolling_std_1h"] = std
        features[f"{col}_rolling_zscore"] = (features[col] - mean) / std

    return features.replace([np.inf, -np.inf], np.nan)


def write_cart_features(data_dir: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    cart = load_cart_metrics(data_dir)
    features = build_cart_features(cart)
    features.to_csv(output_dir / "features_cart_service.csv", index=False)
    return features


if __name__ == "__main__":
    write_cart_features(Path("g3-data/g3"), Path("reports/generated"))
