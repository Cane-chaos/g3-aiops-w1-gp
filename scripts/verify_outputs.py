from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    Path("reports/generated/validation_summary.json"),
    Path("reports/generated/features_cart_service.csv"),
    Path("reports/generated/anomalies.csv"),
    Path("reports/generated/detector_comparison.csv"),
    Path("reports/generated/log_pattern_events.csv"),
    Path("reports/generated/log_pattern_counts.csv"),
    Path("reports/generated/correlation_timeline.csv"),
    Path("reports/generated/g3_evidence_summary.json"),
    Path("reports/generated/FINDINGS.generated.md"),
    Path("reports/figures/cart_metrics_evidence.png"),
    Path("reports/figures/cart_log_pattern_timeline.png"),
    Path("reports/figures/cart_anomaly_detector_comparison.png"),
    Path("notebooks/analysis.ipynb"),
    Path("docs/g3-lab-presentation.html"),
    Path("FINDINGS.md"),
    Path("SUBMIT.md"),
]


def verify_files() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        raise SystemExit("Missing required outputs:\n" + "\n".join(f"- {path}" for path in missing))


def verify_summary() -> None:
    summary_path = Path("reports/generated/g3_evidence_summary.json")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    expected_patterns = ["cache_eviction_failed", "gc_overhead", "oom_imminent", "oom_killed"]
    missing_patterns = [
        pattern
        for pattern in expected_patterns
        if summary["log_pattern_counts"].get(pattern, 0) <= 0
    ]
    if missing_patterns:
        raise SystemExit("Missing expected log pattern evidence:\n" + "\n".join(f"- {pattern}" for pattern in missing_patterns))

    detectors = summary["detectors"]
    if "rolling_mad_memory_score_gt_3_5_points" in detectors:
        raise SystemExit("MAD detector should be removed from the evidence summary.")
    if "operational_pressure_rule_points" in detectors:
        raise SystemExit("Operational pressure rule should be removed from the evidence summary.")

    detector_counts = {
        "rolling_zscore_memory_abs_gt_3_points": detectors["rolling_zscore_memory_abs_gt_3_points"],
        "ewma_memory_abs_gt_3_points": detectors["ewma_memory_abs_gt_3_points"],
        "isolation_forest_multivariate_points": detectors["isolation_forest_multivariate_points"],
    }
    empty_detectors = [name for name, count in detector_counts.items() if count <= 0]
    if empty_detectors:
        raise SystemExit("Detector produced no anomaly points:\n" + "\n".join(f"- {name}" for name in empty_detectors))

    if summary["rows"]["cart_metrics"] <= 0 or summary["rows"]["cart_pattern_logs"] <= 0:
        raise SystemExit("Summary row counts are empty.")

    detection = summary.get("detection_evidence", {})
    for detector in ["rolling_zscore", "ewma", "isolation_forest"]:
        if detector not in detection:
            raise SystemExit(f"Missing detection evidence for {detector}.")


def verify_narrative_evidence() -> None:
    required_phrases = [
        "Detection evidence",
        "metric-first, log-backtrace",
        "Nguồn evidence và phương pháp",
        "Raw source",
        "Generated artifact",
        "First metric anomaly",
        "Supporting log evidence sớm nhất",
        "OOM/restart collapse",
        "Worst degraded runtime window",
        "Phương hướng giải quyết",
        "không dùng",
    ]
    findings = Path("FINDINGS.md").read_text(encoding="utf-8")
    slide = Path("docs/g3-lab-presentation.html").read_text(encoding="utf-8")
    for phrase in required_phrases:
        if phrase not in findings:
            raise SystemExit(f"FINDINGS.md is missing evidence phrase: {phrase}")
    for phrase in ["Evidence nào được detect", "Why This Order", "metric-first, log-backtrace", "Source", "Method", "Isolation Forest", "Rolling Z-score"]:
        if phrase not in slide:
            raise SystemExit(f"Presentation is missing evidence phrase: {phrase}")


def main() -> None:
    verify_files()
    verify_summary()
    verify_narrative_evidence()
    print("Output verification passed")


if __name__ == "__main__":
    main()
