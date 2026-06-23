from pathlib import Path

import pandas as pd

from mortgage_data_qa.validate import validate_dataframe


def test_missing_required_columns_are_reported():
    dataframe = pd.DataFrame({"loan_id": ["A1"], "agency": ["FNMA"]})

    result = validate_dataframe(dataframe)

    assert not result.passed
    assert "product_type" in result.missing_columns
    assert "current_balance" in result.missing_columns
    assert any(issue.check == "missing_required_columns" for issue in result.issues)


def test_validate_dataframe_detects_core_data_quality_issues():
    dataframe = pd.DataFrame(
        {
            "loan_id": ["L1", "L1", "L3", ""],
            "agency": ["FNMA", "FHLMC", None, "GNMA"],
            "product_type": ["30YR_FIXED", "30YR_FIXED", "15YR_FIXED", "ARM_5_1"],
            "vintage": [2021, 2021, 2022, 2023],
            "origination_date": ["2021-01-15", "not-a-date", "2020-02-30", None],
            "loan_purpose": ["purchase", "bad_purpose", "cash_out_refinance", ""],
            "fico": [720, 299, "abc", 851],
            "ltv": [80, -1, 130, "bad"],
            "dti": [35, 66, -5, None],
            "coupon": [3.5, 0.25, 13.5, "bad"],
            "current_balance": [250000, -10, 0, 100000],
            "loan_age_months": [10, 20, 30, None],
        }
    )

    result = validate_dataframe(dataframe)
    checks = {issue.check for issue in result.issues}

    assert not result.passed
    assert "missing_values" in checks
    assert "duplicate_loan_id" in checks
    assert "malformed_origination_date" in checks
    assert "invalid_fico" in checks
    assert "invalid_ltv" in checks
    assert "invalid_dti" in checks
    assert "invalid_loan_purpose" in checks
    assert "negative_current_balance" in checks
    assert "suspicious_coupon" in checks


def test_clean_dataframe_passes_without_errors_or_warnings():
    dataframe = pd.DataFrame(
        {
            "loan_id": ["L100"],
            "agency": ["FNMA"],
            "product_type": ["30YR_FIXED"],
            "vintage": [2024],
            "origination_date": ["2024-01-31"],
            "loan_purpose": ["purchase"],
            "fico": [740],
            "ltv": [80.0],
            "dti": [35.0],
            "coupon": [6.5],
            "current_balance": [350000.0],
            "loan_age_months": [12],
        }
    )

    result = validate_dataframe(dataframe)

    assert result.passed
    assert result.error_count == 0
    assert result.warning_count == 0


def test_clean_sample_csv_passes_validation():
    sample_path = Path(__file__).resolve().parents[1] / "sample_data" / "synthetic_mortgage_loans_clean.csv"
    dataframe = pd.read_csv(sample_path)

    result = validate_dataframe(dataframe)

    assert result.passed
    assert result.issues == []
