from __future__ import annotations

from pathlib import Path

from build_features import write_cart_features
from correlate_and_report import build_evidence_summary, write_charts, write_correlation_timeline, write_log_pattern_outputs
from detect_anomalies import write_anomalies
from validate_data import write_validation_summary


def run_pipeline() -> None:
    data_dir = Path("g3-data/g3")
    output_dir = Path("reports/generated")
    figures_dir = Path("reports/figures")
    docs_asset_dir = Path("docs/assets/g3")

    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    docs_asset_dir.mkdir(parents=True, exist_ok=True)

    validation = write_validation_summary(data_dir, output_dir)
    write_cart_features(data_dir, output_dir)
    write_anomalies(output_dir, output_dir)
    _, log_summary = write_log_pattern_outputs(data_dir, output_dir)
    write_correlation_timeline(output_dir)
    write_charts(output_dir, docs_asset_dir)
    summary = build_evidence_summary(data_dir, output_dir, validation, log_summary)

    print("Pipeline completed")
    print(f"Cart metric rows: {summary['rows']['cart_metrics']}")
    print(f"Pattern log events: {summary['rows']['cart_pattern_logs']}")
    print(f"Earliest cache warning line: {summary['log_pattern_first_occurrence']['cache_eviction_failed']['line']}")
    print(f"Evidence summary: {output_dir / 'g3_evidence_summary.json'}")


if __name__ == "__main__":
    run_pipeline()
