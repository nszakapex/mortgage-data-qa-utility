"""Tests for pipe/tab/semicolon delimited file loading."""

from io import BytesIO
from pathlib import Path

from mortgage_data_qa.validate import detect_delimiter, load_csv, read_delimited_table, validate_csv


def test_detect_pipe_delimiter():
    text = "loan_id|agency|fico\nA1|FNMA|740\n"
    assert detect_delimiter(text) == "|"


def test_load_pipe_delimited_csv_sample():
    sample = Path(__file__).resolve().parents[1] / "sample_data" / "synthetic_mortgage_loans_pipe.csv"
    result = validate_csv(sample)
    assert result.passed
    assert result.missing_columns == []
    assert result.row_count == 8


def test_load_pipe_bytes_with_aliased_headers():
    payload = (
        b"Loan Number|UPB|Note Rate|Credit Score|Agency|Product|Orig Year|"
        b"Closing Date|Purpose|Original LTV|Debt To Income|Loan Age\n"
        b"A1|350000|6.5|740|FNMA|30YR_FIXED|2024|2024-01-15|purchase|80|35|12\n"
    )
    dataframe = load_csv(BytesIO(payload))
    assert list(dataframe.columns)[:3] == ["loan_id", "current_balance", "coupon"]
    assert dataframe.iloc[0]["loan_id"] == "A1"


def test_read_delimited_table_preserves_comma_csv():
    sample = Path(__file__).resolve().parents[1] / "sample_data" / "clean_mortgage_loans.csv"
    dataframe = read_delimited_table(sample)
    assert "loan_id" in dataframe.columns
    assert len(dataframe.columns) == 12
