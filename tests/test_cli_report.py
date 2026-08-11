"""CLI report builder coverage for CSV and Excel inputs."""

from pathlib import Path

from mortgage_data_qa.report import build_report_from_path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"


def test_build_report_from_loan_csv_fail_sample():
    report = build_report_from_path(SAMPLE_DIR / "synthetic_mortgage_loans.csv")
    assert "Status: FAIL" in report
    assert "loan_id" in report or "QA Findings" in report


def test_build_report_from_clean_research_workbook():
    report = build_report_from_path(SAMPLE_DIR / "synthetic_pool_research.xlsx")
    assert "Mortgage Research Workbook QA Report" in report
    assert "Status: PASS" in report
    assert "SF_vs_Multi_CPR_30YR" in report


def test_build_report_from_fail_research_workbook():
    report = build_report_from_path(SAMPLE_DIR / "synthetic_pool_research_fail.xlsx")
    assert "Mortgage Research Workbook QA Report" in report
    assert "Status: FAIL" in report


def test_build_report_single_sheet_from_workbook():
    report = build_report_from_path(
        SAMPLE_DIR / "synthetic_pool_research.xlsx",
        sheet_name="Investor_balance_vintageOrigin",
    )
    assert "Sheets reviewed: Investor_balance_vintageOrigin" in report
    assert "Status: PASS" in report
