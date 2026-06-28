"""Tests for mortgage research workbook validators."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from mortgage_data_qa.research_profiles import (
    detect_sheet_type,
    validate_cpr_comparison_sheet,
    validate_generic_research_table,
    validate_market_share_sheet,
    validate_research_workbook,
    validate_vintage_balance_sheet,
)


def test_detect_sheet_type_for_vintage_balance():
    dataframe = pd.DataFrame({"Origination Year": [2021], "Balance": [1000.0]})
    assert detect_sheet_type(dataframe) == "vintage_balance"


def test_vintage_balance_validation_flags_duplicate_year_and_negative_balance():
    dataframe = pd.DataFrame(
        {
            "Origination Year": [2021, 2021, 1985],
            "Balance": [1000.0, -10.0, None],
        }
    )

    result = validate_vintage_balance_sheet(dataframe)
    checks = {issue.check for issue in result.issues}

    assert not result.passed
    assert "duplicate_origination_year" in checks
    assert "negative_balance_values" in checks
    assert "origination_year_out_of_range" in checks
    assert "missing_balance_values" in checks


def test_vintage_balance_clean_data_passes():
    dataframe = pd.DataFrame(
        {
            "Origination Year": [2020, 2021, 2022],
            "Balance": [1000.0, 2000.0, 3000.0],
        }
    )

    result = validate_vintage_balance_sheet(dataframe)

    assert result.passed
    assert result.issues == []


def test_cpr_owner_investor_validation_flags_invalid_dates_and_high_cpr():
    dataframe = pd.DataFrame(
        {
            "Analysis Date": [202401, 202402, 202404, "bad"],
            "Owner CPR": [12.5, -1.0, 55.0, 10.0],
            "Owner Balance": [100.0, 200.0, None, 300.0],
            "Investor CPR": [11.0, 12.0, 120.0, 10.0],
            "Investor Balance": [90.0, 180.0, 270.0, 360.0],
        }
    )

    result = validate_cpr_comparison_sheet(dataframe, variant="owner_investor")
    checks = {issue.check for issue in result.issues}

    assert not result.passed
    assert "invalid_analysis_date" in checks
    assert "analysis_date_gaps" in checks
    assert "negative_cpr_values" in checks
    assert "cpr_above_review_threshold" in checks
    assert "cpr_above_error_threshold" in checks
    assert "missing_balance_values" in checks


def test_cpr_sf_multi_clean_data_passes():
    dataframe = pd.DataFrame(
        {
            "Analysis Date": [202401, 202402, 202403],
            "Owner CPR": [10.0, 11.0, 12.0],
            "SF Balance": [1000.0, 1100.0, 1200.0],
            "2-4 CPR": [9.0, 10.0, 11.0],
            "2-4 Balance": [900.0, 950.0, 980.0],
        }
    )

    result = validate_cpr_comparison_sheet(dataframe, variant="sf_multi")

    assert result.passed
    assert result.issues == []


def test_market_share_validation_flags_misaligned_years_and_high_wac():
    dataframe = pd.DataFrame(
        {
            "YR": [2021, 2022],
            "FTHB Orig  Balance": [100.0, 200.0],
            "FTB Avg ORIG_WAC": [3.5, 16.0],
            "YR.1": [2021, 2023],
            "Non-FTHB Orig  Balance": [300.0, 400.0],
            "Non-FTHB Avg ORIG_WAC": [4.0, 4.5],
            "YR.2": [2021, 2022],
            "Second Orig  Balance": [500.0, 600.0],
            "Second Avg ORIG_WAC": [4.2, 4.3],
            "YR.3": [2021, 2022],
            "Investor Orig  Balance": [700.0, 800.0],
            "Investor Avg ORIG_WAC": [4.8, 4.9],
        }
    )

    result = validate_market_share_sheet(dataframe)
    checks = {issue.check for issue in result.issues}

    assert not result.passed
    assert "misaligned_year_blocks" in checks
    assert "wac_above_review_threshold" in checks


def test_market_share_clean_data_passes():
    dataframe = pd.DataFrame(
        {
            "YR": [2021, 2022],
            "FTHB Orig  Balance": [100.0, 200.0],
            "FTB Avg ORIG_WAC": [3.5, 3.6],
            "YR.1": [2021, 2022],
            "Non-FTHB Orig  Balance": [300.0, 400.0],
            "Non-FTHB Avg ORIG_WAC": [4.0, 4.1],
            "YR.2": [2021, 2022],
            "Second Orig  Balance": [500.0, 600.0],
            "Second Avg ORIG_WAC": [4.2, 4.3],
            "YR.3": [2021, 2022],
            "Investor Orig  Balance": [700.0, 800.0],
            "Investor Avg ORIG_WAC": [4.8, 4.9],
        }
    )

    result = validate_market_share_sheet(dataframe)

    assert result.passed
    assert result.issues == []


def test_generic_research_profile_flags_empty_and_duplicate_rows():
    empty = pd.DataFrame()
    empty_result = validate_generic_research_table(empty)
    assert not empty_result.passed
    assert any(issue.check == "empty_table" for issue in empty_result.issues)

    dataframe = pd.DataFrame({"segment": ["A", "A"], "value": [1, 1]})
    result = validate_generic_research_table(dataframe)
    checks = {issue.check for issue in result.issues}

    assert "duplicate_rows" in checks
    assert "missing_values" not in checks


def test_synthetic_pool_research_workbook_passes():
    sample_path = Path(__file__).resolve().parents[1] / "sample_data" / "synthetic_pool_research.xlsx"
    if not sample_path.exists():
        pytest.skip("Synthetic workbook sample has not been generated yet.")

    result = validate_research_workbook(sample_path, file_name=sample_path.name)

    assert result.passed
    assert len(result.sheet_results) == 5
