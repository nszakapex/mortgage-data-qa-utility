"""Validation checks for synthetic/public-style mortgage CSV files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from mortgage_data_qa.schema import (
    COUPON_SUSPICIOUS_MAX,
    COUPON_SUSPICIOUS_MIN,
    DTI_MAX,
    DTI_MIN,
    FICO_MAX,
    FICO_MIN,
    LTV_MAX,
    LTV_MIN,
    REQUIRED_COLUMNS,
    VALID_LOAN_PURPOSES,
)


@dataclass(frozen=True)
class ValidationIssue:
    """One analyst-readable validation issue."""

    check: str
    severity: str
    message: str
    count: int
    rows: list[int] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResult:
    """Validation output for one dataframe or CSV file."""

    row_count: int
    column_count: int
    required_columns: list[str]
    missing_columns: list[str]
    issues: list[ValidationIssue]

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "ERROR" for issue in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")


def load_csv(csv_path: str | Path) -> pd.DataFrame:
    """Load a CSV while preserving loan IDs as text."""

    return pd.read_csv(csv_path, dtype={"loan_id": "string"})


def validate_csv(csv_path: str | Path) -> ValidationResult:
    """Validate a CSV file and return structured QA findings."""

    dataframe = load_csv(csv_path)
    return validate_dataframe(dataframe)


def validate_dataframe(dataframe: pd.DataFrame) -> ValidationResult:
    """Validate a dataframe that resembles a loan-level mortgage dataset."""

    issues: list[ValidationIssue] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]

    if missing_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message="Required columns are missing from the dataset.",
                count=len(missing_columns),
                columns=missing_columns,
            )
        )

    present_required_columns = [column for column in REQUIRED_COLUMNS if column in dataframe.columns]
    for column in present_required_columns:
        missing_mask = _missing_mask(dataframe[column])
        if missing_mask.any():
            issues.append(
                ValidationIssue(
                    check="missing_values",
                    severity="ERROR",
                    message=f"Column '{column}' contains missing values.",
                    count=int(missing_mask.sum()),
                    rows=_row_numbers(dataframe, missing_mask),
                    columns=[column],
                )
            )

    if "loan_id" in dataframe.columns:
        loan_ids = dataframe["loan_id"].astype("string").str.strip()
        duplicate_mask = loan_ids.notna() & (loan_ids != "") & loan_ids.duplicated(keep=False)
        if duplicate_mask.any():
            duplicate_ids = sorted(loan_ids[duplicate_mask].dropna().unique().tolist())
            issues.append(
                ValidationIssue(
                    check="duplicate_loan_id",
                    severity="ERROR",
                    message="Duplicate loan_id values were found.",
                    count=int(duplicate_mask.sum()),
                    rows=_row_numbers(dataframe, duplicate_mask),
                    columns=["loan_id"],
                    examples=duplicate_ids[:5],
                )
            )

    if "origination_date" in dataframe.columns:
        date_series = dataframe["origination_date"]
        present_mask = ~_missing_mask(date_series)
        parsed_dates = pd.to_datetime(date_series[present_mask], errors="coerce")
        malformed_mask = pd.Series(False, index=dataframe.index)
        malformed_mask.loc[parsed_dates[parsed_dates.isna()].index] = True
        if malformed_mask.any():
            issues.append(
                ValidationIssue(
                    check="malformed_origination_date",
                    severity="ERROR",
                    message="origination_date contains values that cannot be parsed as dates.",
                    count=int(malformed_mask.sum()),
                    rows=_row_numbers(dataframe, malformed_mask),
                    columns=["origination_date"],
                    examples=_examples(dataframe.loc[malformed_mask, "origination_date"]),
                )
            )

    _append_numeric_range_issue(
        issues,
        dataframe,
        column="fico",
        minimum=FICO_MIN,
        maximum=FICO_MAX,
        check="invalid_fico",
        message=f"fico must be numeric and between {FICO_MIN} and {FICO_MAX}.",
    )
    _append_numeric_range_issue(
        issues,
        dataframe,
        column="ltv",
        minimum=LTV_MIN,
        maximum=LTV_MAX,
        check="invalid_ltv",
        message=f"ltv must be numeric and between {LTV_MIN} and {LTV_MAX}.",
    )
    _append_numeric_range_issue(
        issues,
        dataframe,
        column="dti",
        minimum=DTI_MIN,
        maximum=DTI_MAX,
        check="invalid_dti",
        message=f"dti must be numeric and between {DTI_MIN} and {DTI_MAX}.",
    )

    if "loan_purpose" in dataframe.columns:
        purpose_series = dataframe["loan_purpose"]
        present_mask = ~_missing_mask(purpose_series)
        normalized = (
            purpose_series.astype("string")
            .str.strip()
            .str.lower()
            .str.replace("-", "_", regex=False)
            .str.replace(" ", "_", regex=False)
        )
        invalid_mask = present_mask & ~normalized.isin(VALID_LOAN_PURPOSES)
        if invalid_mask.any():
            issues.append(
                ValidationIssue(
                    check="invalid_loan_purpose",
                    severity="ERROR",
                    message="loan_purpose contains values outside the allowed purpose list.",
                    count=int(invalid_mask.sum()),
                    rows=_row_numbers(dataframe, invalid_mask),
                    columns=["loan_purpose"],
                    examples=_examples(dataframe.loc[invalid_mask, "loan_purpose"]),
                )
            )

    if "current_balance" in dataframe.columns:
        balance = pd.to_numeric(dataframe["current_balance"], errors="coerce")
        negative_balance_mask = balance.notna() & (balance < 0)
        if negative_balance_mask.any():
            issues.append(
                ValidationIssue(
                    check="negative_current_balance",
                    severity="ERROR",
                    message="current_balance contains negative values.",
                    count=int(negative_balance_mask.sum()),
                    rows=_row_numbers(dataframe, negative_balance_mask),
                    columns=["current_balance"],
                    examples=_examples(dataframe.loc[negative_balance_mask, "current_balance"]),
                )
            )

    if "coupon" in dataframe.columns:
        coupon_series = dataframe["coupon"]
        present_mask = ~_missing_mask(coupon_series)
        coupon = pd.to_numeric(coupon_series, errors="coerce")
        suspicious_coupon_mask = present_mask & (
            coupon.isna() | (coupon < COUPON_SUSPICIOUS_MIN) | (coupon > COUPON_SUSPICIOUS_MAX)
        )
        if suspicious_coupon_mask.any():
            issues.append(
                ValidationIssue(
                    check="suspicious_coupon",
                    severity="WARNING",
                    message=(
                        "coupon contains non-numeric values or values outside the "
                        f"{COUPON_SUSPICIOUS_MIN:.1f}-{COUPON_SUSPICIOUS_MAX:.1f} review band."
                    ),
                    count=int(suspicious_coupon_mask.sum()),
                    rows=_row_numbers(dataframe, suspicious_coupon_mask),
                    columns=["coupon"],
                    examples=_examples(dataframe.loc[suspicious_coupon_mask, "coupon"]),
                )
            )

    return ValidationResult(
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        required_columns=REQUIRED_COLUMNS.copy(),
        missing_columns=missing_columns,
        issues=issues,
    )


def _append_numeric_range_issue(
    issues: list[ValidationIssue],
    dataframe: pd.DataFrame,
    *,
    column: str,
    minimum: float,
    maximum: float,
    check: str,
    message: str,
) -> None:
    if column not in dataframe.columns:
        return

    series = dataframe[column]
    present_mask = ~_missing_mask(series)
    numeric = pd.to_numeric(series, errors="coerce")
    invalid_mask = present_mask & (numeric.isna() | (numeric < minimum) | (numeric > maximum))

    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                check=check,
                severity="ERROR",
                message=message,
                count=int(invalid_mask.sum()),
                rows=_row_numbers(dataframe, invalid_mask),
                columns=[column],
                examples=_examples(dataframe.loc[invalid_mask, column]),
            )
        )


def _missing_mask(series: pd.Series) -> pd.Series:
    text_values = series.astype("string").str.strip()
    return series.isna() | text_values.isna() | (text_values == "")


def _row_numbers(dataframe: pd.DataFrame, mask: pd.Series) -> list[int]:
    return [int(dataframe.index.get_loc(index)) + 2 for index in dataframe.index[mask]]


def _examples(series: pd.Series, limit: int = 5) -> list[str]:
    return [str(value) for value in series.dropna().astype(str).unique().tolist()[:limit]]

