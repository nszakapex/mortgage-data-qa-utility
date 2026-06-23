import pandas as pd

from mortgage_data_qa.report import generate_markdown_report
from mortgage_data_qa.summarize import format_summary_markdown, summarize_dataframe


def test_summarize_dataframe_returns_expected_counts_and_stats():
    dataframe = pd.DataFrame(
        {
            "agency": ["FNMA", "FHLMC", "FNMA"],
            "product_type": ["30YR_FIXED", "15YR_FIXED", "30YR_FIXED"],
            "loan_purpose": ["purchase", "rate_term_refinance", "purchase"],
            "vintage": [2023, 2023, 2024],
            "origination_date": ["2023-01-15", "2023-02-15", "2024-03-01"],
            "fico": [720, 760, 700],
            "ltv": [80, 70, 85],
            "dti": [33, 28, 41],
            "coupon": [6.25, 5.75, 6.5],
            "current_balance": [300000, 210000, 420000],
            "loan_age_months": [18, 17, 4],
        }
    )

    summary = summarize_dataframe(dataframe)

    assert summary["row_count"] == 3
    assert summary["categorical"]["agency"]["FNMA"] == 2
    assert summary["numeric"]["current_balance"]["max"] == 420000
    assert summary["origination_date"]["min"] == "2023-01-15"


def test_format_summary_markdown_includes_core_sections():
    dataframe = pd.DataFrame(
        {
            "agency": ["FNMA"],
            "fico": [740],
            "origination_date": ["2024-01-31"],
        }
    )

    markdown = format_summary_markdown(summarize_dataframe(dataframe))

    assert "## Dataset Summary" in markdown
    assert "Rows: 1" in markdown
    assert "| Field | Count | Mean | Min | Median | Max |" in markdown


def test_generate_markdown_report_includes_findings_table():
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

    report = generate_markdown_report(dataframe, dataset_name="unit_test.csv")

    assert "# Mortgage Data QA Report: unit_test.csv" in report
    assert "| Severity | Check | Count | Columns | Rows | Examples |" in report
    assert "duplicate_loan_id" in report
