import re

path = 'scripts/correlate_and_report.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update write_correlation_timeline
code = code.replace(
    'anomalies.groupby("window")[["z_anomaly", "if_anomaly"]]',
    'anomalies.groupby("window")[["z_anomaly", "ewma_anomaly", "if_anomaly"]]'
)

# 2. Update write_charts to plot ewma points
plot_old = """    ax.scatter(if_points["timestamp"], if_points["memory_pct"], s=14, color="#dc2626", alpha=0.75, label="Isolation Forest anomaly")
    ax.scatter(z_points["timestamp"], z_points["memory_pct"], s=18, facecolors="none", edgecolors="#2563eb", label="Rolling Z-score |z|>3")"""
plot_new = """    ewma_points = anomalies[anomalies["ewma_anomaly"]]
    ax.scatter(if_points["timestamp"], if_points["memory_pct"], s=14, color="#dc2626", alpha=0.75, label="Isolation Forest anomaly")
    ax.scatter(z_points["timestamp"], z_points["memory_pct"], s=18, facecolors="none", edgecolors="#2563eb", label="Rolling Z-score |z|>3")
    ax.scatter(ewma_points["timestamp"], ewma_points["memory_pct"], s=22, marker='^', facecolors="none", edgecolors="#16a34a", label="EWMA |z|>3")"""
code = code.replace(plot_old, plot_new)

# 3. Update build_evidence_summary
first_extract_old = """    first_z = anomalies[anomalies["z_anomaly"]].iloc[0]
    first_if = anomalies[anomalies["if_anomaly"]].iloc[0]
    z_peak = timeline.loc[timeline["z_anomaly"].idxmax()]
    if_peak = timeline.loc[timeline["if_anomaly"].idxmax()]"""
first_extract_new = """    first_z = anomalies[anomalies["z_anomaly"]].iloc[0]
    first_ewma = anomalies[anomalies["ewma_anomaly"]].iloc[0]
    first_if = anomalies[anomalies["if_anomaly"]].iloc[0]
    z_peak = timeline.loc[timeline["z_anomaly"].idxmax()]
    ewma_peak = timeline.loc[timeline["ewma_anomaly"].idxmax()]
    if_peak = timeline.loc[timeline["if_anomaly"].idxmax()]"""
code = code.replace(first_extract_old, first_extract_new)

detectors_old = """        "detectors": {
            "rolling_zscore_memory_abs_gt_3_points": int(anomalies["z_anomaly"].sum()),
            "isolation_forest_multivariate_points": int(anomalies["if_anomaly"].sum()),"""
detectors_new = """        "detectors": {
            "rolling_zscore_memory_abs_gt_3_points": int(anomalies["z_anomaly"].sum()),
            "ewma_memory_abs_gt_3_points": int(anomalies["ewma_anomaly"].sum()),
            "isolation_forest_multivariate_points": int(anomalies["if_anomaly"].sum()),"""
code = code.replace(detectors_old, detectors_new)

det_evidence_old = """            "rolling_zscore": {
                "first_timestamp": first_z["timestamp"].isoformat(),
                "first_memory_mb": round(float(first_z["memory_mb"]), 2),
                "first_memory_pct": round(float(first_z["memory_pct"]), 2),
                "first_zscore": round(float(first_z["memory_mb_rolling_zscore"]), 2),
                "peak_window": z_peak["timestamp"].isoformat(),
                "peak_window_points": int(z_peak["z_anomaly"]),
            },
            "isolation_forest": {"""
det_evidence_new = """            "rolling_zscore": {
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
            "isolation_forest": {"""
code = code.replace(det_evidence_old, det_evidence_new)


# 4. Update write_findings narrative
code = code.replace(
    'chạy hai detector thật sự có trong hệ thống: Rolling Z-score và Isolation Forest',
    'chạy ba detector thật sự có trong hệ thống: Rolling Z-score, EWMA và Isolation Forest'
)
code = code.replace(
    '- **Rolling Z-score** bắt pha memory spike/drop',
    '- **EWMA** phản ứng sớm hơn với thay đổi xu hướng do ưu tiên trọng số gần nhất.\n- **Rolling Z-score** bắt pha memory spike/drop'
)
code = code.replace(
    'Rolling Z-score và Isolation Forest',
    'Rolling Z-score, EWMA và Isolation Forest'
)

det_table_old = """| Rolling Z-score | Memory spike/drop so với baseline 1 giờ gần nhất | `abs(memory_mb_rolling_zscore) > 3`; rolling window = 120 samples trước đó | `memory_mb` từ `features_cart_service.csv` | {summary['detectors']['rolling_zscore_memory_abs_gt_3_points']} |"""
det_table_new = """| Rolling Z-score | Memory spike/drop so với baseline 1 giờ gần nhất | `abs(memory_mb_rolling_zscore) > 3`; rolling window = 120 samples trước đó | `memory_mb` từ `features_cart_service.csv` | {summary['detectors']['rolling_zscore_memory_abs_gt_3_points']} |
| EWMA | Thay đổi xu hướng với trọng số nghiêng về quá khứ gần | `abs(memory_mb_ewma_score) > 3`; span = 120 | `memory_mb` từ `features_cart_service.csv` | {summary['detectors']['ewma_memory_abs_gt_3_points']} |"""
code = code.replace(det_table_old, det_table_new)

code = code.replace(
    'Detector set hiện tại chỉ dùng **hai phương pháp**: Rolling Z-score và Isolation Forest.',
    'Detector set hiện tại dùng **ba phương pháp**: Rolling Z-score, EWMA và Isolation Forest.'
)
code = code.replace(
    'Repo hiện **không dùng** MAD, IQR, EWMA, Operational Pressure Rule hoặc Drain3.',
    'Repo hiện **không dùng** MAD, IQR, Operational Pressure Rule hoặc Drain3.'
)

evid_table_old = """| Incident memory spike/drop | `reports/generated/anomalies.csv` | Rolling Z-score `abs(z)>3` | `{detection['rolling_zscore']['peak_window']}` | peak window có `{detection['rolling_zscore']['peak_window_points']}` memory anomaly points |"""
evid_table_new = """| Incident memory spike/drop | `reports/generated/anomalies.csv` | Rolling Z-score `abs(z)>3` | `{detection['rolling_zscore']['peak_window']}` | peak window có `{detection['rolling_zscore']['peak_window_points']}` memory anomaly points |
| EWMA trend shift | `reports/generated/anomalies.csv` | EWMA `abs(score)>3` | `{detection['ewma']['peak_window']}` | peak window có `{detection['ewma']['peak_window_points']}` ewma anomaly points |"""
code = code.replace(evid_table_old, evid_table_new)

code = code.replace(
    '- Isolation Forest là detector đầu tiên chọn trạng thái metric degradation rõ ràng.',
    '- Isolation Forest là detector đầu tiên chọn trạng thái metric degradation rõ ràng.\n- EWMA cho phép phản ứng nhanh hơn với các đường chéo memory liên tục.'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("correlate_and_report.py updated successfully.")
