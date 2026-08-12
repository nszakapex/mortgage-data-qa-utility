"""Tests for loan-level CSV header aliasing and authorized upload support."""

import pandas as pd

from mortgage_data_qa.profiles import ValidationProfile, suggest_profile_for_dataframe
from mortgage_data_qa.schema import canonicalize_loan_level_columns, looks_like_loan_level
from mortgage_data_qa.validate import validate_dataframe


def test_canonicalize_maps_common_real_world_headers():
    dataframe = pd.DataFrame(
        {
            "Loan Number": ["A1"],
            "Seller": ["FNMA"],
            "Product": ["30YR_FIXED"],
            "Orig Year": [2024],
            "Closing Date": ["2024-01-15"],
            "Purpose": ["purchase"],
            "Credit Score": [740],
            "Original LTV": [80.0],
            "Debt To Income": [35.0],
            "Note Rate": [6.5],
            "UPB": [350000.0],
            "Loan Age": [12],
        }
    )

    normalized = canonicalize_loan_level_columns(dataframe)
    result = validate_dataframe(normalized)

    assert "loan_id" in normalized.columns
    assert "current_balance" in normalized.columns
    assert "coupon" in normalized.columns
    assert result.passed
    assert result.missing_columns == []


def test_looks_like_loan_level_for_aliased_csv():
    dataframe = pd.DataFrame(
        {
            "loan_number": ["A1"],
            "agency": ["FNMA"],
            "product_type": ["30YR_FIXED"],
            "vintage": [2024],
            "orig_date": ["2024-01-15"],
            "purpose": ["purchase"],
            "fico": [740],
            "ltv": [80.0],
            "dti": [35.0],
            "interest_rate": [6.5],
            "current_upb": [350000.0],
            "age_months": [12],
        }
    )

    assert looks_like_loan_level(dataframe)
    assert suggest_profile_for_dataframe(dataframe, filename="tape.csv") is ValidationProfile.LOAN_LEVEL


def test_generic_profile_suggested_for_unrelated_csv():
    dataframe = pd.DataFrame({"metric": ["a", "b"], "value": [1, 2]})
    assert suggest_profile_for_dataframe(dataframe, filename="metrics.csv") is ValidationProfile.GENERIC_RESEARCH
