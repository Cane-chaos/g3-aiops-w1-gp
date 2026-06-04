from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


LOG_PATTERNS = {
    "cache_eviction_failed": "ProductCatalogCache eviction failed",
    "gc_overhead": "GC overhead limit warning",
    "oom_imminent": "OutOfMemoryError imminent",
    "oom_killed": "Container OOMKilled",
}


def parse_cart_log_patterns(data_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = []
    counts = {key: 0 for key in LOG_PATTERNS}
    firsts: dict[str, Any] = {}
    log_path = data_dir / "logs" / "cart-service.log.jsonl"

    with log_path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            record = json.loads(line)
            timestamp = pd.to_datetime(record["timestamp"], utc=True)
            message = record.get("message", "")
            for key, pattern in LOG_PATTERNS.items():
                if pattern in message:
                    counts[key] += 1
                    firsts.setdefault(
                        key,
                        {
                            "timestamp": record["timestamp"],
                            "line": line_no,
                            "message": message,
                            "pod": record.get("pod"),
                        },
                    )
                    rows.append(
                        {
                            "timestamp": timestamp,
                            "line": line_no,
                            "pattern": key,
                            "message": message,
                            "pod": record.get("pod"),
                        }
                    )
    return pd.DataFrame(rows), {"counts": counts, "first_occurrence": firsts}


def write_log_pattern_outputs(data_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern_rows, summary = parse_cart_log_patterns(data_dir)
    pattern_rows.to_csv(output_dir / "log_pattern_events.csv", index=False)

    if pattern_rows.empty:
        counts = pd.DataFrame()
    else:
        counts = (
            pattern_rows.assign(count=1)
            .set_index("timestamp")
            .groupby("pattern")["count"]
            .resample("30min")
            .sum()
            .unstack(0)
            .fillna(0)
        )
    counts.to_csv(output_dir / "log_pattern_counts.csv")
    return counts, summary


def write_correlation_timeline(output_dir: Path) -> pd.DataFrame:
    anomalies = pd.read_csv(output_dir / "anomalies.csv", parse_dates=["timestamp"])
    log_counts = pd.read_csv(output_dir / "log_pattern_counts.csv", parse_dates=["timestamp"])
    anomalies["window"] = anomalies["timestamp"].dt.floor("30min")
    anomaly_counts = (
        anomalies.groupby("window")[["z_anomaly", "mad_anomaly", "if_anomaly"]]
        .sum()
        .reset_index()
        .rename(columns={"window": "timestamp"})
    )
    timeline = pd.merge(log_counts, anomaly_counts, on="timestamp", how="outer").fillna(0)
    timeline.to_csv(output_dir / "correlation_timeline.csv", index=False)
    return timeline


def write_charts(output_dir: Path, docs_asset_dir: Path) -> None:
    docs_asset_dir.mkdir(parents=True, exist_ok=True)
    (output_dir.parent / "figures").mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(output_dir / "features_cart_service.csv", parse_dates=["timestamp"])
    anomalies = pd.read_csv(output_dir / "anomalies.csv", parse_dates=["timestamp"])
    log_counts = pd.read_csv(output_dir / "log_pattern_counts.csv", parse_dates=["timestamp"])

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(4, 1, figsize=(14, 9), sharex=True)
    axes[0].plot(features["timestamp"], features["memory_mb"], color="#2563eb", lw=1.2, label="memory MB")
    axes[0].axhline(2048, color="#dc2626", ls="--", lw=1, label="2GB limit")
    axes[0].set_ylabel("Memory MB")
    axes[0].legend(loc="upper left")
    axes[1].plot(features["timestamp"], features["jvm_gc_pause_ms_avg"], color="#7c3aed", lw=1, label="GC pause avg")
    axes[1].set_ylabel("GC ms")
    axes[1].legend(loc="upper left")
    axes[2].plot(features["timestamp"], features["http_p99_latency_ms"], color="#f97316", lw=1, label="p99 latency")
    axes[2].set_ylabel("Latency ms")
    axes[2].legend(loc="upper left")
    axes[3].plot(features["timestamp"], features["http_5xx_rate"], color="#dc2626", lw=1, label="5xx rate")
    axes[3].step(features["timestamp"], features["container_restart_count"], color="#111827", where="post", lw=1.2, label="restart count")
    axes[3].set_ylabel("5xx / restarts")
    axes[3].legend(loc="upper left")
    for ax in axes:
        ax.axvline(pd.Timestamp("2026-06-01T06:30:08Z"), color="#16a34a", ls=":", lw=1.2)
        ax.axvspan(pd.Timestamp("2026-06-01T11:29:30Z"), pd.Timestamp("2026-06-01T12:00:00Z"), color="#facc15", alpha=0.18)
        ax.axvline(pd.Timestamp("2026-06-01T19:59:02Z"), color="#dc2626", ls=":", lw=1.2)
    axes[0].set_title("Cart-service metrics evidence from Prometheus CSV: memory, GC, latency, 5xx, restarts")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.tight_layout()
    fig.savefig(docs_asset_dir / "cart_metrics_evidence.png", dpi=180)
    fig.savefig(output_dir.parent / "figures" / "cart_metrics_evidence.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = {
        "cache_eviction_failed": "#16a34a",
        "gc_overhead": "#7c3aed",
        "oom_imminent": "#f97316",
        "oom_killed": "#dc2626",
    }
    for col in [c for c in log_counts.columns if c != "timestamp"]:
        ax.plot(log_counts["timestamp"], log_counts[col], marker="o", ms=2, lw=1.4, color=colors.get(col), label=col)
    ax.axvspan(pd.Timestamp("2026-06-01T11:29:30Z"), pd.Timestamp("2026-06-01T12:00:00Z"), color="#facc15", alpha=0.18, label="metrics gap")
    ax.set_title("Cart-service log pattern counts per 30 minutes from JSONL")
    ax.set_ylabel("Pattern count / 30min")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    fig.savefig(docs_asset_dir / "cart_log_pattern_timeline.png", dpi=180)
    fig.savefig(output_dir.parent / "figures" / "cart_log_pattern_timeline.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(anomalies["timestamp"], anomalies["memory_pct"], color="#94a3b8", lw=1, label="memory % of 2GB limit")
    if_points = anomalies[anomalies["if_anomaly"]]
    z_points = anomalies[anomalies["z_anomaly"]]
    mad_points = anomalies[anomalies["mad_anomaly"]]
    ax.scatter(if_points["timestamp"], if_points["memory_pct"], s=14, color="#dc2626", alpha=0.75, label="Isolation Forest anomaly")
    ax.scatter(z_points["timestamp"], z_points["memory_pct"], s=18, facecolors="none", edgecolors="#2563eb", label="Rolling Z-score |z|>3")
    ax.scatter(mad_points["timestamp"], mad_points["memory_pct"], s=18, marker="x", color="#7c3aed", label="Rolling MAD score>3.5")
    ax.axvline(pd.Timestamp("2026-06-01T06:30:08Z"), color="#16a34a", ls=":", lw=1.2, label="first log warning")
    ax.axvline(pd.Timestamp("2026-06-01T19:59:02Z"), color="#dc2626", ls=":", lw=1.2, label="OOMKilled")
    ax.axhline(100, color="#991b1b", ls="--", lw=1, label="2GB limit")
    ax.set_title("Anomaly detector comparison on cart-service memory trajectory")
    ax.set_ylabel("Memory % of limit")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    fig.savefig(docs_asset_dir / "cart_anomaly_detector_comparison.png", dpi=180)
    fig.savefig(output_dir.parent / "figures" / "cart_anomaly_detector_comparison.png", dpi=180)
    plt.close(fig)


def write_findings(summary: dict[str, Any], output_dir: Path) -> None:
    firsts = summary["log_pattern_first_occurrence"]
    metrics = summary["metric_extremes"]
    content = f"""# G3 AIOps Evidence Findings

Generated by `python3 scripts/run_pipeline.py`.

## WHEN

The earliest silent signal is `ProductCatalogCache eviction failed` at `{firsts['cache_eviction_failed']['timestamp']}` in `cart-service.log.jsonl` line `{firsts['cache_eviction_failed']['line']}`.

## WHERE

The incident starts in `cart-service`. The strongest early indicators are `memory_usage_bytes`, `jvm_gc_pause_ms_avg`, and `http_p99_latency_ms`.

Log pattern counts:

- cache eviction failed: {summary['log_pattern_counts']['cache_eviction_failed']}
- GC overhead: {summary['log_pattern_counts']['gc_overhead']}
- OOM imminent: {summary['log_pattern_counts']['oom_imminent']}
- OOMKilled: {summary['log_pattern_counts']['oom_killed']}

## WHAT

The likely root cause is a memory leak in product catalog cache references. The restart loop is explained by cache warm-up after each restart plus traffic pressure. Prometheus only observed a max memory sample of {metrics['max_memory_mb']} MB at `{metrics['max_memory_time']}`, while logs show OOMKilled at `{firsts['oom_killed']['timestamp']}` line `{firsts['oom_killed']['line']}` with a 2GB memory limit. This supports the telemetry blind spot explanation.

## Detector Comparison

- Rolling Z-score anomaly points: {summary['detectors']['rolling_zscore_memory_abs_gt_3_points']}
- Rolling MAD anomaly points: {summary['detectors']['rolling_mad_memory_score_gt_3_5_points']}
- Isolation Forest anomaly points: {summary['detectors']['isolation_forest_multivariate_points']}
"""
    (output_dir / "FINDINGS.generated.md").write_text(content, encoding="utf-8")


def build_evidence_summary(data_dir: Path, output_dir: Path, validation: dict[str, Any], log_summary: dict[str, Any]) -> dict[str, Any]:
    features = pd.read_csv(output_dir / "features_cart_service.csv", parse_dates=["timestamp"])
    anomalies = pd.read_csv(output_dir / "anomalies.csv")
    gaps = {}
    for name, result in validation["metrics"].items():
        if result["large_gaps"]:
            gap = max(result["large_gaps"], key=lambda item: item["gap_seconds"])
            gaps[name] = gap

    summary = {
        "source_files": {
            "cart_metrics": str(data_dir / "metrics" / "cart-service.csv"),
            "cart_logs": str(data_dir / "logs" / "cart-service.log.jsonl"),
        },
        "rows": {
            "cart_metrics": int(len(features)),
            "cart_pattern_logs": int(sum(log_summary["counts"].values())),
        },
        "log_pattern_counts": log_summary["counts"],
        "log_pattern_first_occurrence": log_summary["first_occurrence"],
        "metrics_gap": gaps,
        "detectors": {
            "rolling_zscore_memory_abs_gt_3_points": int(anomalies["z_anomaly"].sum()),
            "rolling_mad_memory_score_gt_3_5_points": int(anomalies["mad_anomaly"].sum()),
            "isolation_forest_multivariate_points": int(anomalies["if_anomaly"].sum()),
            "features": ["memory_pct", "jvm_gc_pause_ms_avg", "http_p99_latency_ms", "http_5xx_rate", "container_restart_count"],
            "isolation_forest_contamination": 0.08,
        },
        "metric_extremes": {
            "max_memory_mb": round(float(features["memory_mb"].max()), 2),
            "max_memory_time": features.loc[features["memory_mb"].idxmax(), "timestamp"].isoformat(),
            "max_latency_ms": round(float(features["http_p99_latency_ms"].max()), 2),
            "max_latency_time": features.loc[features["http_p99_latency_ms"].idxmax(), "timestamp"].isoformat(),
            "max_gc_pause_ms": round(float(features["jvm_gc_pause_ms_avg"].max()), 2),
            "max_gc_time": features.loc[features["jvm_gc_pause_ms_avg"].idxmax(), "timestamp"].isoformat(),
            "max_5xx_rate": round(float(features["http_5xx_rate"].max()), 2),
            "max_5xx_time": features.loc[features["http_5xx_rate"].idxmax(), "timestamp"].isoformat(),
            "max_restart_count": int(features["container_restart_count"].max()),
        },
    }
    (output_dir / "g3_evidence_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_findings(summary, output_dir)
    return summary
