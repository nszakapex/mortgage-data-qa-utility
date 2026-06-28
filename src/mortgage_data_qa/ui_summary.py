"""Small presentation helpers for the Streamlit QA interface."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mortgage_data_qa.research_profiles import WorkbookValidationResult
from mortgage_data_qa.validate import ValidationIssue, ValidationResult


LOAN_LEVEL_CHECKS = {
    "duplicate_loan_id": "duplicate_loan_ids",
    "missing_required_columns": "missing_required_columns",
    "missing_values": "missing_values",
    "invalid_fico": "invalid_fico_values",
    "invalid_ltv": "invalid_ltv_values",
    "invalid_dti": "invalid_dti_values",
    "malformed_origination_date": "malformed_dates",
    "invalid_loan_purpose": "invalid_loan_purpose_values",
    "negative_current_balance": "negative_balances",
    "suspicious_coupon": "suspicious_coupon_values",
}


def summarize_validation_result(result: ValidationResult) -> dict[str, int | bool]:
    """Return compact metric counts derived from validation issues."""

    summary: dict[str, int | bool] = {
        "passed": result.passed,
        "total_rows": result.row_count,
        "total_error_findings": _severity_count(result.issues, "ERROR"),
        "total_warning_findings": _severity_count(result.issues, "WARNING"),
    }
    for metric_name in LOAN_LEVEL_CHECKS.values():
        summary[metric_name] = 0

    for issue in result.issues:
        metric_name = LOAN_LEVEL_CHECKS.get(issue.check)
        if metric_name:
            summary[metric_name] = int(summary[metric_name]) + issue.count

    return summary


def summarize_workbook_result(workbook_result: WorkbookValidationResult) -> dict[str, int | bool]:
    return {
        "passed": workbook_result.passed,
        "total_rows": workbook_result.row_count,
        "total_error_findings": workbook_result.error_count,
        "total_warning_findings": workbook_result.warning_count,
        "sheets_reviewed": len(workbook_result.sheet_results),
        "sheets_failed": sum(1 for sheet in workbook_result.sheet_results if not sheet.result.passed),
    }


def issues_to_records(issues: list[ValidationIssue]) -> list[dict[str, Any]]:
    """Flatten validation issues into table-ready records."""

    records: list[dict[str, Any]] = []
    for issue in issues:
        rows = issue.rows or [None]
        for row_number in rows:
            records.append(
                {
                    "issue_type": issue.check,
                    "severity": issue.severity,
                    "column": ", ".join(issue.columns) or "n/a",
                    "row": row_number if row_number is not None else "n/a",
                    "count": issue.count,
                    "message": issue.message,
                    "details": _issue_details(issue),
                }
            )
    return records


def workbook_issues_to_records(workbook_result: WorkbookValidationResult) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for sheet in workbook_result.sheet_results:
        for record in issues_to_records(sheet.result.issues):
            record = dict(record)
            record["sheet"] = sheet.sheet_name
            record["layout"] = sheet.sheet_type
            records.append(record)
    return records


def issue_to_dict(issue: ValidationIssue) -> dict[str, Any]:
    """Expose the issue dataclass as a plain dictionary for Streamlit expanders."""

    return asdict(issue)


def _severity_count(issues: list[ValidationIssue], severity: str) -> int:
    return sum(issue.count for issue in issues if issue.severity == severity)


def _issue_details(issue: ValidationIssue) -> str:
    if issue.examples:
        return "Examples: " + ", ".join(issue.examples)
    if issue.columns:
        return "Columns: " + ", ".join(issue.columns)
    return ""
