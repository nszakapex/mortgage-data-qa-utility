import pandas as pd

from mortgage_data_qa.ui_summary import issues_to_records, summarize_validation_result, summarize_workbook_result
from mortgage_data_qa.validate import validate_dataframe
from mortgage_data_qa.research_profiles import (
    SheetValidationResult,
    WorkbookValidationResult,
    validate_vintage_balance_sheet,
)


def test_summarize_validation_result_counts_issue_findings():
    dataframe = pd.DataFrame(
        {
            "loan_id": ["L1", "L1"],
            "agency": ["FNMA", "FNMA"],
            "product_type": ["30YR_FIXED", "30YR_FIXED"],
            "vintage": [2024, 2024],
            "origination_date": ["2024-01-31", "bad-date"],
            "loan_purpose": ["purchase", "invalid"],
            "fico": [740, 200],
            "ltv": [80, 150],
            "dti": [35, 70],
            "coupon": [6.5, 14],
            "current_balance": [350000, -1],
            "loan_age_months": [12, 13],
        }
    )

    result = validate_dataframe(dataframe)
    summary = summarize_validation_result(result)

    assert summary["passed"] is False
    assert summary["total_rows"] == 2
    assert summary["duplicate_loan_ids"] == 2
    assert summary["invalid_fico_values"] == 1
    assert summary["invalid_ltv_values"] == 1
    assert summary["invalid_dti_values"] == 1
    assert summary["suspicious_coupon_values"] == 1


def test_issues_to_records_preserves_issue_context():
    dataframe = pd.DataFrame(
        {
            "loan_id": ["L1", "L1"],
            "agency": ["FNMA", "FNMA"],
            "product_type": ["30YR_FIXED", "30YR_FIXED"],
            "vintage": [2024, 2024],
            "origination_date": ["2024-01-31", "2024-02-01"],
            "loan_purpose": ["purchase", "purchase"],
            "fico": [740, 741],
            "ltv": [80, 81],
            "dti": [35, 36],
            "coupon": [6.5, 6.6],
            "current_balance": [350000, 340000],
            "loan_age_months": [12, 13],
        }
    )

    result = validate_dataframe(dataframe)
    records = issues_to_records(result.issues)

    assert records
    assert records[0]["issue_type"] == "duplicate_loan_id"
    assert records[0]["severity"] == "ERROR"
    assert records[0]["column"] == "loan_id"


def test_summarize_workbook_result_counts_sheets():
    sheet_result = SheetValidationResult(
        sheet_name="Investor_balance_vintageOrigin",
        sheet_type="vintage_balance",
        result=validate_vintage_balance_sheet(
            pd.DataFrame({"Origination Year": [2021], "Balance": [100.0]}),
        ),
    )
    workbook_result = WorkbookValidationResult(
        file_name="synthetic_pool_research.xlsx",
        sheet_results=[sheet_result],
    )

    summary = summarize_workbook_result(workbook_result)

    assert summary["passed"] is True
    assert summary["sheets_reviewed"] == 1
    assert summary["sheets_failed"] == 0
