"""Tests for validation profile dispatch."""

import pandas as pd

from mortgage_data_qa.profiles import (
    ValidationProfile,
    default_profile_for_filename,
    validate_dataframe_with_profile,
)


def test_default_profile_for_excel_is_research_workbook():
    assert default_profile_for_filename("Pool_research.xlsx") == ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK


def test_default_profile_for_csv_is_loan_level():
    assert default_profile_for_filename("loans.csv") == ValidationProfile.LOAN_LEVEL


def test_loan_level_profile_uses_existing_validator():
    dataframe = pd.DataFrame({"loan_id": ["A1"], "agency": ["FNMA"]})
    result = validate_dataframe_with_profile(dataframe, ValidationProfile.LOAN_LEVEL)

    assert not result.passed
    assert any(issue.check == "missing_required_columns" for issue in result.issues)


def test_generic_research_profile_runs_on_simple_table():
    dataframe = pd.DataFrame({"metric": ["balance"], "value": [100.0]})
    result = validate_dataframe_with_profile(dataframe, ValidationProfile.GENERIC_RESEARCH)

    assert result.passed
