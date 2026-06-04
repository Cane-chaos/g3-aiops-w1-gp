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
    result["mad_anomaly"] = result["memory_mb_rolling_mad_score"] > 3.5

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
        "memory_mb_rolling_mad_score",
        "z_anomaly",
        "mad_anomaly",
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
                "detector": "Rolling MAD",
                "rule": "memory_mb rolling MAD score > 3.5",
                "anomaly_points": int(anomalies["mad_anomaly"].sum()),
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
