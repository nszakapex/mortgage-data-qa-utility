"""Markdown reporting for mortgage-style data QA results."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from mortgage_data_qa.summarize import format_summary_markdown, summarize_dataframe
from mortgage_data_qa.validate import ValidationResult, load_csv, validate_dataframe


def generate_markdown_report(
    dataframe: pd.DataFrame,
    *,
    dataset_name: str = "dataset",
    validation_result: ValidationResult | None = None,
) -> str:
    """Generate an analyst-readable markdown QA report."""

    result = validation_result or validate_dataframe(dataframe)
    summary = summarize_dataframe(dataframe)
    status = "PASS" if result.passed else "FAIL"

    lines = [
        f"# Mortgage Data QA Report: {dataset_name}",
        "",
        "This report is for synthetic or public-style mortgage data only.",
        "",
        "## QA Status",
        "",
        f"- Status: {status}",
        f"- Rows reviewed: {result.row_count:,}",
        f"- Columns reviewed: {result.column_count:,}",
        f"- Error checks triggered: {result.error_count:,}",
        f"- Warning checks triggered: {result.warning_count:,}",
        "",
    ]

    if result.missing_columns:
        lines.extend(
            [
                "## Missing Required Columns",
                "",
                ", ".join(f"`{column}`" for column in result.missing_columns),
                "",
            ]
        )

    lines.extend([format_summary_markdown(summary), "", "## QA Findings", ""])

    if not result.issues:
        lines.extend(["No QA issues were found.", ""])
    else:
        lines.append("| Severity | Check | Count | Columns | Rows | Examples |")
        lines.append("| --- | --- | ---: | --- | --- | --- |")
        for issue in result.issues:
            lines.append(
                "| {severity} | {check} | {count:,} | {columns} | {rows} | {examples} |".format(
                    severity=issue.severity,
                    check=issue.check,
                    count=issue.count,
                    columns=", ".join(f"`{column}`" for column in issue.columns) or "n/a",
                    rows=", ".join(str(row) for row in issue.rows[:12]) or "n/a",
                    examples=", ".join(f"`{example}`" for example in issue.examples[:5]) or "n/a",
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- Findings identify data quality conditions only; they do not imply credit, valuation, or investment conclusions.",
            "- Review thresholds are intentionally simple and should be adjusted for the dataset owner, product scope, and research question.",
            "- Do not run this utility on confidential company data unless the environment and permissions have been explicitly approved.",
            "",
        ]
    )

    return "\n".join(lines)


def build_report_from_csv(csv_path: str | Path) -> str:
    path = Path(csv_path)
    dataframe = load_csv(path)
    result = validate_dataframe(dataframe)
    return generate_markdown_report(dataframe, dataset_name=path.name, validation_result=result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a markdown QA report for a mortgage-style CSV.")
    parser.add_argument("csv_path", help="Path to the CSV file to validate.")
    parser.add_argument("--output", "-o", help="Optional markdown output path.")
    args = parser.parse_args()

    report = build_report_from_csv(args.csv_path)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()

