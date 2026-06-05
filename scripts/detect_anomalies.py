from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


DETECTOR_FEATURES = [
    "memory_pct",
    "jvm_gc_pause_ms_avg",
    "http_p99_latency_ms",
    "http_5xx_rate",
    "container_restart_count",
]


def detect_cart_anomalies(features: pd.DataFrame, contamination: float = 0.08) -> pd.DataFrame:
    result = features.copy()
    result["z_anomaly"] = result["memory_mb_rolling_zscore"].abs() > 3
    result["memory_spike_anomaly"] = result["memory_mb_rolling_zscore"] > 3
    result["memory_drop_anomaly"] = result["memory_mb_rolling_zscore"] < -3

    ewma_mean = result["memory_mb"].ewm(span=120, adjust=False).mean()
    ewma_std = result["memory_mb"].ewm(span=120, adjust=False).std()
    result["memory_mb_ewma_score"] = (result["memory_mb"] - ewma_mean) / ewma_std
    result["ewma_anomaly"] = result["memory_mb_ewma_score"].fillna(0).abs() > 3


    model_input = result[DETECTOR_FEATURES].ffill().bfill()
    scaled = StandardScaler().fit_transform(model_input)
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42)
    result["if_anomaly"] = model.fit_predict(scaled) == -1
    result["if_score"] = model.decision_function(scaled)
    return result


def write_anomalies(input_dir: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(input_dir / "features_cart_service.csv")
    anomalies = detect_cart_anomalies(features)
    anomaly_cols = [
        "timestamp",
        "memory_mb",
        "memory_pct",
        "jvm_gc_pause_ms_avg",
        "http_p99_latency_ms",
        "http_5xx_rate",
        "container_restart_count",
        "memory_mb_rolling_zscore",
        "z_anomaly",
        "memory_spike_anomaly",
        "memory_drop_anomaly",
        "memory_mb_ewma_score",
        "ewma_anomaly",
        "if_anomaly",
        "if_score",
    ]
    anomalies[anomaly_cols].to_csv(output_dir / "anomalies.csv", index=False)

    comparison = pd.DataFrame(
        [
            {
                "detector": "Rolling Z-score",
                "rule": "abs(memory_mb rolling z-score) > 3",
                "anomaly_points": int(anomalies["z_anomaly"].sum()),
            },
            {
                "detector": "EWMA",
                "rule": "abs(memory_mb ewma_score span=120) > 3",
                "anomaly_points": int(anomalies["ewma_anomaly"].sum()),
            },
            {
                "detector": "Isolation Forest",
                "rule": "multivariate score over memory_pct, GC, latency, 5xx, restarts",
                "anomaly_points": int(anomalies["if_anomaly"].sum()),
            },
        ]
    )
    comparison.to_csv(output_dir / "detector_comparison.csv", index=False)
    return anomalies


if __name__ == "__main__":
    write_anomalies(Path("reports/generated"), Path("reports/generated"))
