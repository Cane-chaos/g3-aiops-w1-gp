from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_METRIC_COLUMNS: dict[str, set[str]] = {
    "cart-service.csv": {
        "timestamp",
        "memory_usage_bytes",
        "memory_limit_bytes",
        "cpu_usage_percent",
        "http_requests_per_sec",
        "http_p99_latency_ms",
        "http_5xx_rate",
        "jvm_gc_pause_ms_avg",
        "container_restart_count",
    },
    "api-gateway.csv": {
        "timestamp",
        "http_requests_per_sec",
        "http_p99_latency_ms",
        "http_5xx_rate",
        "cart_upstream_error_rate",
        "product_upstream_error_rate",
        "active_connections",
    },
    "order-service.csv": {
        "timestamp",
        "http_requests_per_sec",
        "http_p99_latency_ms",
        "http_5xx_rate",
        "upstream_timeout_rate",
    },
    "payment-service.csv": {
        "timestamp",
        "http_requests_per_sec",
        "http_p99_latency_ms",
        "http_5xx_rate",
        "upstream_timeout_rate",
    },
    "product-service.csv": {
        "timestamp",
        "http_requests_per_sec",
        "http_p99_latency_ms",
        "cpu_usage_percent",
        "http_5xx_rate",
    },
}


REQUIRED_LOG_COLUMNS = {"timestamp", "level", "service", "pod", "trace_id", "message"}


def validate_metrics(metrics_dir: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for csv_path in sorted(metrics_dir.glob("*.csv")):
        df = pd.read_csv(csv_path)
        missing = sorted(REQUIRED_METRIC_COLUMNS.get(csv_path.name, {"timestamp"}) - set(df.columns))
        timestamps = pd.to_datetime(df["timestamp"], utc=True).sort_values().reset_index(drop=True)
        diffs = timestamps.diff().dropna()
        gaps = []
        for idx, delta in diffs[diffs > pd.Timedelta(seconds=45)].items():
            gaps.append(
                {
                    "from": timestamps.iloc[int(idx) - 1].isoformat(),
                    "to": timestamps.iloc[int(idx)].isoformat(),
                    "gap_seconds": float(delta.total_seconds()),
                }
            )
        results[csv_path.name] = {
            "rows": int(len(df)),
            "missing_columns": missing,
            "timestamp_min": timestamps.min().isoformat(),
            "timestamp_max": timestamps.max().isoformat(),
            "large_gaps": gaps,
        }
    return results


def validate_logs(logs_dir: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for log_path in sorted(logs_dir.glob("*.jsonl")):
        invalid_json_lines: list[int] = []
        missing_field_lines: list[int] = []
        first_timestamp = None
        last_timestamp = None
        rows = 0
        level_counts: dict[str, int] = {}
        service_counts: dict[str, int] = {}

        with log_path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                rows += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    invalid_json_lines.append(line_no)
                    continue

                if REQUIRED_LOG_COLUMNS - set(record):
                    missing_field_lines.append(line_no)
                timestamp = pd.to_datetime(record.get("timestamp"), utc=True, errors="coerce")
                if not pd.isna(timestamp):
                    first_timestamp = timestamp if first_timestamp is None else min(first_timestamp, timestamp)
                    last_timestamp = timestamp if last_timestamp is None else max(last_timestamp, timestamp)
                level = str(record.get("level", "UNKNOWN"))
                service = str(record.get("service", "UNKNOWN"))
                level_counts[level] = level_counts.get(level, 0) + 1
                service_counts[service] = service_counts.get(service, 0) + 1

        results[log_path.name] = {
            "rows": rows,
            "invalid_json_lines": invalid_json_lines[:20],
            "missing_field_lines": missing_field_lines[:20],
            "timestamp_min": first_timestamp.isoformat() if first_timestamp is not None else None,
            "timestamp_max": last_timestamp.isoformat() if last_timestamp is not None else None,
            "level_counts": level_counts,
            "service_counts": service_counts,
        }
    return results


def validate_dataset(data_dir: Path) -> dict[str, Any]:
    metrics_dir = data_dir / "metrics"
    logs_dir = data_dir / "logs"
    return {
        "source_dir": str(data_dir),
        "metrics": validate_metrics(metrics_dir),
        "logs": validate_logs(logs_dir),
    }


def write_validation_summary(data_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = validate_dataset(data_dir)
    (output_dir / "validation_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


if __name__ == "__main__":
    write_validation_summary(Path("g3-data/g3"), Path("reports/generated"))
