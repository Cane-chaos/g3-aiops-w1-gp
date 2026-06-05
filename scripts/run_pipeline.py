from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

from build_features import write_cart_features
from correlate_and_report import build_evidence_summary, write_charts, write_correlation_timeline, write_log_pattern_outputs
from detect_anomalies import write_anomalies
from validate_data import write_validation_summary


SUBMIT_TEMPLATE = """# SUBMIT.md

## 1. Phản ánh của nhóm

Nhóm dùng pipeline metric-first, log-backtrace để điều tra incident. Nội dung chi tiết cần được hoàn thiện dựa trên các artifact đã generate từ `make analyze`.

## 2. Phân công công việc

- Member 1: TODO
- Member 2: TODO
- Member 3: TODO

Ghi chú: chỉ ghi các phương pháp đã implement trong repo. Hiện hệ thống dùng Rolling Z-score, Isolation Forest và fixed log pattern extraction; không dùng EWMA, IQR, MAD hoặc Drain3.
"""


def ensure_submit_template(path: Path) -> None:
    if not path.exists():
        path.write_text(SUBMIT_TEMPLATE, encoding="utf-8")


def run_pipeline(data_dir: Path, output_dir: Path, figures_dir: Path, docs_asset_dir: Path, findings_path: Path, submit_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    docs_asset_dir.mkdir(parents=True, exist_ok=True)
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    submit_path.parent.mkdir(parents=True, exist_ok=True)

    validation = write_validation_summary(data_dir, output_dir)
    write_cart_features(data_dir, output_dir)
    write_anomalies(output_dir, output_dir)
    _, log_summary = write_log_pattern_outputs(data_dir, output_dir)
    write_correlation_timeline(output_dir)
    write_charts(output_dir, docs_asset_dir)
    summary = build_evidence_summary(data_dir, output_dir, validation, log_summary)
    shutil.copyfile(output_dir / "FINDINGS.generated.md", findings_path)
    ensure_submit_template(submit_path)

    print("Pipeline completed")
    print(f"Cart metric rows: {summary['rows']['cart_metrics']}")
    print(f"Pattern log events: {summary['rows']['cart_pattern_logs']}")
    print(f"Earliest cache warning line: {summary['log_pattern_first_occurrence']['cache_eviction_failed']['line']}")
    print(f"Evidence summary: {output_dir / 'g3_evidence_summary.json'}")
    print(f"Final findings: {findings_path}")
    print(f"Submission template: {submit_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the G3 offline AIOps evidence pipeline from raw telemetry to deliverables.")
    parser.add_argument("--data-dir", type=Path, default=Path("g3-data/g3"), help="Raw telemetry directory containing metrics/ and logs/.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/generated"), help="Directory for generated CSV/JSON/Markdown evidence.")
    parser.add_argument("--figures-dir", type=Path, default=Path("reports/figures"), help="Directory for generated report figures.")
    parser.add_argument("--docs-asset-dir", type=Path, default=Path("docs/assets/g3"), help="Directory for docs-ready chart assets.")
    parser.add_argument("--findings-path", type=Path, default=Path("FINDINGS.md"), help="Final findings markdown path.")
    parser.add_argument("--submit-path", type=Path, default=Path("SUBMIT.md"), help="Submission markdown path.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        figures_dir=args.figures_dir,
        docs_asset_dir=args.docs_asset_dir,
        findings_path=args.findings_path,
        submit_path=args.submit_path,
    )
