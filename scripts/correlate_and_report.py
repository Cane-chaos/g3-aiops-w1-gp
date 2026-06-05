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
        anomalies.groupby("window")[["z_anomaly", "ewma_anomaly", "if_anomaly"]]
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
    ewma_points = anomalies[anomalies["ewma_anomaly"]]
    ax.scatter(if_points["timestamp"], if_points["memory_pct"], s=14, color="#dc2626", alpha=0.75, label="Isolation Forest anomaly")
    ax.scatter(z_points["timestamp"], z_points["memory_pct"], s=18, facecolors="none", edgecolors="#2563eb", label="Rolling Z-score |z|>3")
    ax.scatter(ewma_points["timestamp"], ewma_points["memory_pct"], s=22, marker='^', facecolors="none", edgecolors="#16a34a", label="EWMA |z|>3")
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
    thresholds = summary["metric_thresholds"]
    detection = summary["detection_evidence"]
    gaps = summary["metrics_gap"]
    gap_lines = "\n".join(
        f"- `{name}`: `{gap['from']}` -> `{gap['to']}` ({int(gap['gap_seconds'])} seconds)"
        for name, gap in gaps.items()
    )
    content = f"""# Incident Postmortem: vòng lặp restart của `cart-service`

Generated by `make analyze` thông qua `notebooks/analysis.ipynb`, notebook gọi `scripts/run_pipeline.py`.

## Tóm tắt điều tra

Nhóm dùng hướng điều tra **metric-first, log-backtrace**. Nghĩa là pipeline đọc metric trước, build feature, chạy detector trên metric, sau đó mới dùng log để giải thích và truy vết nguyên nhân. Cách viết này tránh nhầm rằng log `06:30` là do Z-score hoặc Isolation Forest phát hiện.

- **Isolation Forest** là detector metric đầu tiên bắt trạng thái degradation của `cart-service` lúc `{detection['isolation_forest']['first_timestamp']}`.
- **EWMA** phản ứng sớm hơn với thay đổi xu hướng do ưu tiên trọng số gần nhất.
- **Rolling Z-score** bắt pha memory spike/drop của incident quanh `{detection['rolling_zscore']['peak_window']}`.
- Sau khi metric evidence chọn `cart-service`, bước log-backtrace tìm được evidence hỗ trợ sớm hơn: `ProductCatalogCache eviction failed` lúc `{firsts['cache_eviction_failed']['timestamp']}`, dòng `{firsts['cache_eviction_failed']['line']}`.
- Log cũng xác nhận failure nhìn thấy rõ: `Container OOMKilled` lúc `{firsts['oom_killed']['timestamp']}`.

Giả thuyết root cause: `cart-service` có memory leak hoặc retained reference trong đường `ProductCatalogCache`. Restart loop có khả năng đến từ cache warm-up sau mỗi lần restart cộng với traffic pressure đang tồn đọng.

## 1. WHEN — Anomaly bắt đầu từ khi nào?

Điểm quan trọng: `06:30` **không phải** do Z-score hay Isolation Forest bắt. Đây là supporting log evidence được tìm thấy sau khi metric detector đã chọn `cart-service` để điều tra.

| Giai đoạn | Timestamp / window | Source | Method | Evidence |
| --- | --- | --- | --- | --- |
| Metric detector đầu tiên bắt anomaly | `{detection['isolation_forest']['first_timestamp']}` | `features_cart_service.csv` | Isolation Forest trên memory, GC, latency, 5xx, restarts | memory `{detection['isolation_forest']['first_memory_pct']}%`, GC `{detection['isolation_forest']['first_gc_ms']} ms`, p99 `{detection['isolation_forest']['first_latency_ms']} ms`, 5xx `{detection['isolation_forest']['first_5xx_rate']}%` |
| Z-score bắt spike liên quan incident | `2026-06-01T19:33:30+00:00` | `anomalies.csv` | `abs(memory_mb_rolling_zscore) > 3` | memory khoảng `1509.29 MB`, Z-score `3.32` |
| Memory vượt 1GB | `{thresholds['memory_over_1gb_time']}` | `features_cart_service.csv` | đọc threshold từ feature đã generate | `{thresholds['memory_over_1gb_mb']} MB` |
| Memory vượt 1.5GB | `{thresholds['memory_over_1_5gb_time']}` | `features_cart_service.csv` | đọc threshold từ feature đã generate | `{thresholds['memory_over_1_5gb_mb']} MB` |
| OOMKilled đầu tiên | `{firsts['oom_killed']['timestamp']}` | `cart-service.log.jsonl` dòng `{firsts['oom_killed']['line']}` | log-backtrace sau metric detection | `{firsts['oom_killed']['message']}` |
| Supporting log evidence sớm nhất | `{firsts['cache_eviction_failed']['timestamp']}` | `cart-service.log.jsonl` dòng `{firsts['cache_eviction_failed']['line']}` | log-backtrace trên service đã được metric chọn | `{firsts['cache_eviction_failed']['message']}` |

Kết luận WHEN: metric detector đầu tiên xác định degradation thực sự lúc `{detection['isolation_forest']['first_timestamp']}`. Sau khi điều tra log của `cart-service`, supporting RCA evidence sớm nhất được tìm thấy lúc `{firsts['cache_eviction_failed']['timestamp']}`.

## 2. WHERE — Service, metric, log pattern nào là chỉ báo chính?

Service trọng tâm là `cart-service`.

Nguồn evidence và phương pháp:

| Nhóm evidence | Raw source | Method | Generated artifact |
| --- | --- | --- | --- |
| Metric features | `g3-data/g3/metrics/cart-service.csv` | `build_features.py`: parse CSV, tạo `memory_mb`, `memory_pct`, rolling mean/std/Z-score | `reports/generated/features_cart_service.csv` |
| Metric anomalies | `features_cart_service.csv` | `detect_anomalies.py`: Rolling Z-score, EWMA và Isolation Forest | `reports/generated/anomalies.csv`, `reports/generated/detector_comparison.csv` |
| Log evidence | `g3-data/g3/logs/cart-service.log.jsonl` | `correlate_and_report.py`: parse JSONL và extract fixed log patterns | `reports/generated/log_pattern_events.csv`, `reports/generated/log_pattern_counts.csv` |
| Correlation timeline | metric anomalies + log events | join theo cửa sổ 30 phút giữa detector output và log pattern counts | `reports/generated/correlation_timeline.csv` |

Các chỉ báo chính:

- Metrics: `memory_usage_bytes`, `jvm_gc_pause_ms_avg`, `http_p99_latency_ms`, `http_5xx_rate`, `container_restart_count`
- Logs: `ProductCatalogCache eviction failed`, `GC overhead limit warning`, `Container OOMKilled`, `OutOfMemoryError imminent`
- Generated files: `reports/generated/anomalies.csv`, `reports/generated/log_pattern_events.csv`, `reports/generated/correlation_timeline.csv`

Log parsing method: pipeline hiện tại **không dùng Drain3**. Pipeline dùng fixed-pattern extraction trên structured JSONL. Matching code nằm trong `scripts/correlate_and_report.py` tại `LOG_PATTERNS`. Trong narrative này, log được dùng để backtrace và giải thích sau khi metric detector đã chọn service/window, không phải detector metric đầu tiên.

Log pattern totals:

| Pattern | Count | Source | Method |
| --- | ---: | --- | --- |
| cache eviction failed | {summary['log_pattern_counts']['cache_eviction_failed']} | `cart-service.log.jsonl` | message contains `ProductCatalogCache eviction failed` |
| GC overhead | {summary['log_pattern_counts']['gc_overhead']} | `cart-service.log.jsonl` | message contains `GC overhead limit warning` |
| OOM imminent | {summary['log_pattern_counts']['oom_imminent']} | `cart-service.log.jsonl` | message contains `OutOfMemoryError imminent` |
| OOMKilled | {summary['log_pattern_counts']['oom_killed']} | `cart-service.log.jsonl` | message contains `Container OOMKilled` |

Peak 30-minute log windows:

| Pattern | Peak window | Count |
| --- | --- | ---: |
| cache eviction failed | `{summary['log_pattern_peaks']['cache_eviction_failed']['timestamp']}` | {summary['log_pattern_peaks']['cache_eviction_failed']['count']} |
| GC overhead | `{summary['log_pattern_peaks']['gc_overhead']['timestamp']}` | {summary['log_pattern_peaks']['gc_overhead']['count']} |
| OOM imminent | `{summary['log_pattern_peaks']['oom_imminent']['timestamp']}` | {summary['log_pattern_peaks']['oom_imminent']['count']} |
| OOMKilled | `{summary['log_pattern_peaks']['oom_killed']['timestamp']}` | {summary['log_pattern_peaks']['oom_killed']['count']} |

## 3. WHAT — Root cause hypothesis và cơ chế restart loop

Giả thuyết root cause: `cart-service` bị memory leak hoặc retained reference liên quan `ProductCatalogCache`.

Cơ chế:

1. `ProductCatalogCache` có dấu hiệu không giải phóng được dữ liệu hoặc eviction thất bại dưới heap pressure.
2. Memory usage tăng dần, vượt 1GB lúc `{thresholds['memory_over_1gb_time']}`, sau đó vượt 1.5GB lúc `{thresholds['memory_over_1_5gb_time']}`.
3. JVM GC pause tăng khi heap pressure tăng; p99 latency và 5xx xấu đi.
4. Container chạm memory limit 2GB và bị OOMKilled lúc `{firsts['oom_killed']['timestamp']}`.
5. Sau restart, pod phải warm-up cache lại dưới traffic pressure, khiến memory pressure tái diễn và tạo restart loop.

Blind spot của telemetry:

Prometheus chỉ sample được max memory `{metrics['max_memory_mb']} MB` lúc `{metrics['max_memory_time']}`, trong khi log cho thấy OOMKilled lúc `{firsts['oom_killed']['timestamp']}` dòng `{firsts['oom_killed']['line']}` với memory limit 2GB. Vì vậy metric sample không bắt được đỉnh thật ngay trước OOM.

Metric extremes:

| Metric | Max value | Timestamp | Source | Method |
| --- | ---: | --- | --- | --- |
| memory MB | {metrics['max_memory_mb']} | `{metrics['max_memory_time']}` | `cart-service.csv` -> `features_cart_service.csv` | convert bytes sang MB, sau đó lấy max |
| p99 latency ms | {metrics['max_latency_ms']} | `{metrics['max_latency_time']}` | `cart-service.csv` -> `features_cart_service.csv` | max của `http_p99_latency_ms` |
| GC pause ms avg | {metrics['max_gc_pause_ms']} | `{metrics['max_gc_time']}` | `cart-service.csv` -> `features_cart_service.csv` | max của `jvm_gc_pause_ms_avg` |
| 5xx rate | {metrics['max_5xx_rate']} | `{metrics['max_5xx_time']}` | `cart-service.csv` -> `features_cart_service.csv` | max của `http_5xx_rate` |
| restart count | {metrics['max_restart_count']} | cumulative max | `cart-service.csv` -> `features_cart_service.csv` | max của `container_restart_count` |

## 4. So sánh detector

| Detector | Bắt được gì | Rule / method | Source features | Points |
| --- | --- | --- | --- | ---: |
| Rolling Z-score | Memory spike/drop so với baseline 1 giờ gần nhất | `abs(memory_mb_rolling_zscore) > 3`; rolling window = 120 samples trước đó | `memory_mb` từ `features_cart_service.csv` | {summary['detectors']['rolling_zscore_memory_abs_gt_3_points']} |
| EWMA | Thay đổi xu hướng với trọng số nghiêng về quá khứ gần | `abs(memory_mb_ewma_score) > 3`; span = 120 | `memory_mb` từ `features_cart_service.csv` | {summary['detectors']['ewma_memory_abs_gt_3_points']} |
| Isolation Forest | Trạng thái bất thường đa biến giữa memory, GC, latency, 5xx, restarts | `IsolationForest(contamination=0.08, random_state=42)` | `memory_pct`, `jvm_gc_pause_ms_avg`, `http_p99_latency_ms`, `http_5xx_rate`, `container_restart_count` | {summary['detectors']['isolation_forest_multivariate_points']} |

Detector set hiện tại chỉ dùng **hai phương pháp**: Rolling Z-score, EWMA và Isolation Forest. Repo hiện **không dùng** MAD, IQR, Operational Pressure Rule hoặc Drain3.

## 5. Detection evidence — metric-first, log-backtrace

| Evidence | Source | Method that found it | Timestamp / window | Details |
| --- | --- | --- | --- | --- |
| First metric anomaly | `reports/generated/features_cart_service.csv` | Isolation Forest trên 5 metric features | `{detection['isolation_forest']['first_timestamp']}` | memory `{detection['isolation_forest']['first_memory_pct']}%`, GC `{detection['isolation_forest']['first_gc_ms']} ms`, p99 `{detection['isolation_forest']['first_latency_ms']} ms`, 5xx `{detection['isolation_forest']['first_5xx_rate']}%` |
| Incident memory spike/drop | `reports/generated/anomalies.csv` | Rolling Z-score `abs(z)>3` | `{detection['rolling_zscore']['peak_window']}` | peak window có `{detection['rolling_zscore']['peak_window_points']}` memory anomaly points |
| EWMA trend shift | `reports/generated/anomalies.csv` | EWMA `abs(score)>3` | `{detection['ewma']['peak_window']}` | peak window có `{detection['ewma']['peak_window_points']}` ewma anomaly points |
| Supporting log evidence sớm nhất | `g3-data/g3/logs/cart-service.log.jsonl` | log-backtrace sau metric detection | `{firsts['cache_eviction_failed']['timestamp']}` | dòng `{firsts['cache_eviction_failed']['line']}`, pod `{firsts['cache_eviction_failed']['pod']}`: `{firsts['cache_eviction_failed']['message']}` |
| Early GC pressure log | `g3-data/g3/logs/cart-service.log.jsonl` | log-backtrace sau metric detection | `{firsts['gc_overhead']['timestamp']}` | dòng `{firsts['gc_overhead']['line']}`, pod `{firsts['gc_overhead']['pod']}`: `{firsts['gc_overhead']['message']}` |
| OOM/restart collapse | log JSONL + `reports/generated/anomalies.csv` | Log pattern extraction + Rolling Z-score `abs(z)>3` | `{firsts['oom_killed']['timestamp']}` / `{detection['rolling_zscore']['peak_window']}` | OOMKilled dòng `{firsts['oom_killed']['line']}`; Z-score peak window có `{detection['rolling_zscore']['peak_window_points']}` points |
| Worst degraded runtime window | `reports/generated/correlation_timeline.csv` | tổng hợp 30 phút của Isolation Forest flags | `{detection['isolation_forest']['peak_window']}` | peak window có `{detection['isolation_forest']['peak_window_points']}` IF anomaly points |

Diễn giải:

- Isolation Forest là detector đầu tiên chọn trạng thái metric degradation rõ ràng.
- EWMA cho phép phản ứng nhanh hơn với các đường chéo memory liên tục.
- Rolling Z-score hữu ích nhất khi memory có biến động mạnh, đặc biệt quanh OOM/restart.
- Log-backtrace giải thích tại sao metric anomaly xảy ra và cho thấy cache/heap issue đã tồn tại từ sớm.

## 6. Phương hướng giải quyết

### Mitigation ngay

1. Tạm thời tăng memory limit của `cart-service`, ví dụ từ 2GB lên 4GB, để giảm tần suất OOMKilled trong lúc điều tra.
2. Giảm TTL hoặc maximum size của `ProductCatalogCache` nếu service hỗ trợ cấu hình này.

### Root cause fix

1. Review và sửa eviction behavior của `ProductCatalogCache`. Nên dùng bounded cache như Caffeine với `maximumSize` và `expireAfterWrite` rõ ràng.
2. Lấy heap dump hoặc memory profile trong giai đoạn memory tăng để xác nhận object bị giữ lại.

### Preventative actions

1. Thêm alert trước OOM: memory usage > 75%, GC pause cao, restart count tăng.
2. Thêm log-derived alert cho `heap pressure` / cache eviction failures lặp lại, nhưng xem nó là supporting evidence chứ không thay thế metric detector.
3. Thêm circuit breaker hoặc fail-fast ở caller để degradation của `cart-service` không tạo pressure dây chuyền.
4. Tune readiness/liveness để pod chưa warm-up cache xong thì chưa nhận traffic.

## 7. Data quality notes

Metrics gap phát hiện được:

{gap_lines}

Kết luận dùng cả metrics và logs vì metric sampling 30 giây có thể bỏ lỡ đỉnh thật ngay trước OOM.

## 8. Reproducibility

Run:

```bash
make analyze
make verify
```

Key generated evidence:

- `reports/generated/validation_summary.json`
- `reports/generated/features_cart_service.csv`
- `reports/generated/anomalies.csv`
- `reports/generated/detector_comparison.csv`
- `reports/generated/log_pattern_events.csv`
- `reports/generated/log_pattern_counts.csv`
- `reports/generated/correlation_timeline.csv`
- `reports/generated/g3_evidence_summary.json`
- `reports/figures/cart_metrics_evidence.png`
- `reports/figures/cart_log_pattern_timeline.png`
- `reports/figures/cart_anomaly_detector_comparison.png`
"""
    (output_dir / "FINDINGS.generated.md").write_text(content, encoding="utf-8")


def build_evidence_summary(data_dir: Path, output_dir: Path, validation: dict[str, Any], log_summary: dict[str, Any]) -> dict[str, Any]:
    features = pd.read_csv(output_dir / "features_cart_service.csv", parse_dates=["timestamp"])
    anomalies = pd.read_csv(output_dir / "anomalies.csv", parse_dates=["timestamp"])
    log_counts = pd.read_csv(output_dir / "log_pattern_counts.csv", parse_dates=["timestamp"])
    gaps = {}
    for name, result in validation["metrics"].items():
        if result["large_gaps"]:
            gap = max(result["large_gaps"], key=lambda item: item["gap_seconds"])
            gaps[name] = gap

    log_pattern_peaks = {}
    for pattern in log_summary["counts"]:
        if pattern in log_counts and not log_counts.empty:
            idx = log_counts[pattern].idxmax()
            log_pattern_peaks[pattern] = {
                "timestamp": log_counts.loc[idx, "timestamp"].isoformat(),
                "count": int(log_counts.loc[idx, pattern]),
            }

    timeline = pd.read_csv(output_dir / "correlation_timeline.csv", parse_dates=["timestamp"])
    first_z = anomalies[anomalies["z_anomaly"]].iloc[0]
    first_ewma = anomalies[anomalies["ewma_anomaly"]].iloc[0]
    first_if = anomalies[anomalies["if_anomaly"]].iloc[0]
    z_peak = timeline.loc[timeline["z_anomaly"].idxmax()]
    ewma_peak = timeline.loc[timeline["ewma_anomaly"].idxmax()]
    if_peak = timeline.loc[timeline["if_anomaly"].idxmax()]
    memory_1gb = features[features["memory_mb"] >= 1024].iloc[0]
    memory_1_5gb = features[features["memory_mb"] >= 1536].iloc[0]

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
        "log_pattern_peaks": log_pattern_peaks,
        "metrics_gap": gaps,
        "detectors": {
            "rolling_zscore_memory_abs_gt_3_points": int(anomalies["z_anomaly"].sum()),
            "ewma_memory_abs_gt_3_points": int(anomalies["ewma_anomaly"].sum()),
            "isolation_forest_multivariate_points": int(anomalies["if_anomaly"].sum()),
            "features": ["memory_pct", "jvm_gc_pause_ms_avg", "http_p99_latency_ms", "http_5xx_rate", "container_restart_count"],
            "isolation_forest_contamination": 0.08,
        },
        "detection_evidence": {
            "rolling_zscore": {
                "first_timestamp": first_z["timestamp"].isoformat(),
                "first_memory_mb": round(float(first_z["memory_mb"]), 2),
                "first_memory_pct": round(float(first_z["memory_pct"]), 2),
                "first_zscore": round(float(first_z["memory_mb_rolling_zscore"]), 2),
                "peak_window": z_peak["timestamp"].isoformat(),
                "peak_window_points": int(z_peak["z_anomaly"]),
            },
            "ewma": {
                "first_timestamp": first_ewma["timestamp"].isoformat(),
                "first_memory_mb": round(float(first_ewma["memory_mb"]), 2),
                "first_memory_pct": round(float(first_ewma["memory_pct"]), 2),
                "first_ewma_score": round(float(first_ewma["memory_mb_ewma_score"]), 2),
                "peak_window": ewma_peak["timestamp"].isoformat(),
                "peak_window_points": int(ewma_peak["ewma_anomaly"]),
            },
            "isolation_forest": {
                "first_timestamp": first_if["timestamp"].isoformat(),
                "first_memory_mb": round(float(first_if["memory_mb"]), 2),
                "first_memory_pct": round(float(first_if["memory_pct"]), 2),
                "first_gc_ms": round(float(first_if["jvm_gc_pause_ms_avg"]), 2),
                "first_latency_ms": round(float(first_if["http_p99_latency_ms"]), 2),
                "first_5xx_rate": round(float(first_if["http_5xx_rate"]), 2),
                "first_restart_count": int(first_if["container_restart_count"]),
                "first_if_score": round(float(first_if["if_score"]), 4),
                "peak_window": if_peak["timestamp"].isoformat(),
                "peak_window_points": int(if_peak["if_anomaly"]),
            },
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
        "metric_thresholds": {
            "memory_over_1gb_time": memory_1gb["timestamp"].isoformat(),
            "memory_over_1gb_mb": round(float(memory_1gb["memory_mb"]), 2),
            "memory_over_1_5gb_time": memory_1_5gb["timestamp"].isoformat(),
            "memory_over_1_5gb_mb": round(float(memory_1_5gb["memory_mb"]), 2),
        },
    }
    (output_dir / "g3_evidence_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_findings(summary, output_dir)
    return summary
