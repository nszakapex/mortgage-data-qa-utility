"""Validators for pool/research-style workbook sheets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from mortgage_data_qa.validate import ValidationIssue, ValidationResult, _examples, _missing_mask, _row_numbers

ORIGINATION_YEAR_MIN = 1990
CPR_ERROR_MAX = 100.0
CPR_WARNING_MAX = 50.0
WAC_WARNING_MAX = 15.0

VINTAGE_BALANCE_COLUMNS = ["Origination Year", "Balance"]

CPR_OWNER_INVESTOR_COLUMNS = [
    "Analysis Date",
    "Owner CPR",
    "Owner Balance",
    "Investor CPR",
    "Investor Balance",
]

CPR_SF_MULTI_COLUMNS = [
    "Analysis Date",
    "Owner CPR",
    "SF Balance",
    "2-4 CPR",
    "2-4 Balance",
]

MARKET_SHARE_SEGMENTS = (
    ("FTHB", "FTHB Orig  Balance", "FTB Avg ORIG_WAC"),
    ("Non-FTHB", "Non-FTHB Orig  Balance", "Non-FTHB Avg ORIG_WAC"),
    ("Second", "Second Orig  Balance", "Second Avg ORIG_WAC"),
    ("Investor", "Investor Orig  Balance", "Investor Avg ORIG_WAC"),
)


@dataclass(frozen=True)
class SheetValidationResult:
    sheet_name: str
    sheet_type: str
    result: ValidationResult


@dataclass
class WorkbookValidationResult:
    file_name: str
    profile: str = "mortgage_research_workbook"
    sheet_results: list[SheetValidationResult] = field(default_factory=list)
    selected_sheet: str | None = None

    @property
    def passed(self) -> bool:
        return all(sheet.result.passed for sheet in self.sheet_results)

    @property
    def error_count(self) -> int:
        return sum(sheet.result.error_count for sheet in self.sheet_results)

    @property
    def warning_count(self) -> int:
        return sum(sheet.result.warning_count for sheet in self.sheet_results)

    @property
    def row_count(self) -> int:
        return sum(sheet.result.row_count for sheet in self.sheet_results)

    @property
    def column_count(self) -> int:
        if not self.sheet_results:
            return 0
        return max(sheet.result.column_count for sheet in self.sheet_results)


def detect_sheet_type(dataframe: pd.DataFrame) -> str:
    columns = [str(column) for column in dataframe.columns]
    column_set = set(columns)

    if column_set >= set(VINTAGE_BALANCE_COLUMNS):
        return "vintage_balance"

    if column_set >= set(CPR_OWNER_INVESTOR_COLUMNS):
        return "cpr_owner_investor"

    if column_set >= set(CPR_SF_MULTI_COLUMNS):
        return "cpr_sf_multi"

    if _has_market_share_layout(columns):
        return "market_share"

    return "unknown"


def validate_research_sheet(dataframe: pd.DataFrame, *, sheet_name: str = "sheet") -> ValidationResult:
    sheet_type = detect_sheet_type(dataframe)
    if sheet_type == "vintage_balance":
        return validate_vintage_balance_sheet(dataframe, sheet_name=sheet_name)
    if sheet_type == "cpr_owner_investor":
        return validate_cpr_comparison_sheet(dataframe, variant="owner_investor", sheet_name=sheet_name)
    if sheet_type == "cpr_sf_multi":
        return validate_cpr_comparison_sheet(dataframe, variant="sf_multi", sheet_name=sheet_name)
    if sheet_type == "market_share":
        return validate_market_share_sheet(dataframe, sheet_name=sheet_name)

    return ValidationResult(
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        required_columns=[],
        missing_columns=[],
        issues=[
            ValidationIssue(
                check="unknown_research_sheet_layout",
                severity="ERROR",
                message=(
                    f"Sheet '{sheet_name}' does not match a recognized mortgage research workbook layout."
                ),
                count=1,
            )
        ],
    )


def validate_research_workbook(
    source: str | Path | BinaryIO,
    *,
    file_name: str,
    sheet_name: str | None = None,
) -> WorkbookValidationResult:
    workbook = pd.ExcelFile(source, engine="openpyxl")
    sheet_names = [sheet_name] if sheet_name else workbook.sheet_names
    results: list[SheetValidationResult] = []

    for name in sheet_names:
        dataframe = pd.read_excel(workbook, sheet_name=name, engine="openpyxl")
        sheet_type = detect_sheet_type(dataframe)
        validation = validate_research_sheet(dataframe, sheet_name=name)
        results.append(SheetValidationResult(sheet_name=name, sheet_type=sheet_type, result=validation))

    return WorkbookValidationResult(
        file_name=file_name,
        sheet_results=results,
        selected_sheet=sheet_name,
    )


def validate_vintage_balance_sheet(dataframe: pd.DataFrame, *, sheet_name: str = "sheet") -> ValidationResult:
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in VINTAGE_BALANCE_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message=f"Sheet '{sheet_name}' is missing required vintage balance columns.",
                count=len(missing_columns),
                columns=missing_columns,
            )
        )
        return _result(dataframe, VINTAGE_BALANCE_COLUMNS, missing_columns, issues)

    issues.extend(_mostly_empty_row_issues(dataframe, sheet_name))
    issues.extend(_origination_year_issues(dataframe, sheet_name))
    issues.extend(_non_negative_balance_issues(dataframe, "Balance", sheet_name))
    issues.extend(_missing_balance_issues(dataframe, "Balance", sheet_name))

    return _result(dataframe, VINTAGE_BALANCE_COLUMNS, missing_columns, issues)


def validate_cpr_comparison_sheet(
    dataframe: pd.DataFrame,
    *,
    variant: str,
    sheet_name: str = "sheet",
) -> ValidationResult:
    required_columns = CPR_OWNER_INVESTOR_COLUMNS if variant == "owner_investor" else CPR_SF_MULTI_COLUMNS
    issues: list[ValidationIssue] = []
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message=f"Sheet '{sheet_name}' is missing required CPR comparison columns.",
                count=len(missing_columns),
                columns=missing_columns,
            )
        )
        return _result(dataframe, required_columns, missing_columns, issues)

    issues.extend(_mostly_empty_row_issues(dataframe, sheet_name))
    issues.extend(_analysis_date_issues(dataframe, sheet_name))

    cpr_columns = [column for column in required_columns if "CPR" in column]
    balance_columns = [column for column in required_columns if "Balance" in column]

    for column in cpr_columns:
        issues.extend(_cpr_column_issues(dataframe, column, sheet_name))
    for column in balance_columns:
        issues.extend(_non_negative_balance_issues(dataframe, column, sheet_name))
        issues.extend(_missing_balance_issues(dataframe, column, sheet_name))

    return _result(dataframe, required_columns, missing_columns, issues)


def validate_market_share_sheet(dataframe: pd.DataFrame, *, sheet_name: str = "sheet") -> ValidationResult:
    issues: list[ValidationIssue] = []
    segment_columns = _resolve_market_share_columns(dataframe.columns)
    yr_columns = segment_columns["yr_columns"]
    balance_columns = segment_columns["balance_columns"]
    wac_columns = segment_columns["wac_columns"]

    if not yr_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message=f"Sheet '{sheet_name}' does not contain a recognizable YR column.",
                count=1,
                columns=["YR"],
            )
        )
    if not balance_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message=f"Sheet '{sheet_name}' does not contain recognizable segment balance columns.",
                count=1,
            )
        )
    if not wac_columns:
        issues.append(
            ValidationIssue(
                check="missing_required_columns",
                severity="ERROR",
                message=f"Sheet '{sheet_name}' does not contain recognizable segment average WAC columns.",
                count=1,
            )
        )

    if issues:
        return _result(dataframe, [], [], issues)

    issues.extend(_mostly_empty_row_issues(dataframe, sheet_name))
    issues.extend(_aligned_year_block_issues(dataframe, yr_columns, sheet_name))

    for yr_column in yr_columns:
        issues.extend(_origination_year_issues(dataframe, sheet_name, year_column=yr_column))

    for balance_column in balance_columns:
        issues.extend(_non_negative_balance_issues(dataframe, balance_column, sheet_name))
        issues.extend(_missing_balance_issues(dataframe, balance_column, sheet_name))

    for wac_column in wac_columns:
        issues.extend(_wac_column_issues(dataframe, wac_column, sheet_name))

    return _result(dataframe, [], [], issues)


def validate_generic_research_table(dataframe: pd.DataFrame) -> ValidationResult:
    issues: list[ValidationIssue] = []

    if dataframe.empty:
        issues.append(
            ValidationIssue(
                check="empty_table",
                severity="ERROR",
                message="The research table contains no rows.",
                count=1,
            )
        )
        return _result(dataframe, [], [], issues)

    if len(dataframe.columns) == 0:
        issues.append(
            ValidationIssue(
                check="missing_columns",
                severity="ERROR",
                message="The research table contains no columns.",
                count=1,
            )
        )
        return _result(dataframe, [], [], issues)

    issues.extend(_mostly_empty_row_issues(dataframe, "table"))

    duplicate_rows = dataframe.duplicated(keep=False)
    if duplicate_rows.any():
        issues.append(
            ValidationIssue(
                check="duplicate_rows",
                severity="WARNING",
                message="Duplicate rows were found in the research table.",
                count=int(duplicate_rows.sum()),
                rows=_row_numbers(dataframe, duplicate_rows),
            )
        )

    for column in dataframe.columns:
        missing_mask = _missing_mask(dataframe[column])
        if missing_mask.any():
            issues.append(
                ValidationIssue(
                    check="missing_values",
                    severity="WARNING",
                    message=f"Column '{column}' contains missing values.",
                    count=int(missing_mask.sum()),
                    rows=_row_numbers(dataframe, missing_mask),
                    columns=[str(column)],
                )
            )

    return _result(dataframe, [], [], issues)


def _result(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    missing_columns: list[str],
    issues: list[ValidationIssue],
) -> ValidationResult:
    return ValidationResult(
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        required_columns=required_columns.copy(),
        missing_columns=missing_columns,
        issues=issues,
    )


def _has_market_share_layout(columns: list[str]) -> bool:
    normalized = [_normalize_column_name(column) for column in columns]
    has_yr = any(_is_yr_column(name) for name in normalized)
    has_balance = any("orig balance" in name for name in normalized)
    has_wac = any("avg orig wac" in name or "orig wac" in name for name in normalized)
    return has_yr and has_balance and has_wac


def _resolve_market_share_columns(columns: pd.Index) -> dict[str, list[str]]:
    yr_columns: list[str] = []
    balance_columns: list[str] = []
    wac_columns: list[str] = []

    for column in columns:
        normalized = _normalize_column_name(column)
        if _is_yr_column(normalized):
            yr_columns.append(str(column))
        elif "orig balance" in normalized:
            balance_columns.append(str(column))
        elif "avg orig wac" in normalized or "orig wac" in normalized:
            wac_columns.append(str(column))

    return {"yr_columns": yr_columns, "balance_columns": balance_columns, "wac_columns": wac_columns}


def _is_yr_column(normalized_name: str) -> bool:
    return normalized_name == "yr" or normalized_name.startswith("yr.")


def _normalize_column_name(column: object) -> str:
    return " ".join(str(column).strip().lower().replace("_", " ").split())


def _mostly_empty_row_issues(dataframe: pd.DataFrame, sheet_name: str) -> list[ValidationIssue]:
    if dataframe.empty:
        return []

    empty_row_mask = dataframe.apply(
        lambda row: row.isna().all() or (row.astype("string").str.strip() == "").all(),
        axis=1,
    )
    if not empty_row_mask.any():
        return []

    return [
        ValidationIssue(
            check="mostly_empty_rows",
            severity="WARNING",
            message=f"Sheet '{sheet_name}' contains mostly empty rows.",
            count=int(empty_row_mask.sum()),
            rows=_row_numbers(dataframe, empty_row_mask),
        )
    ]


def _origination_year_issues(
    dataframe: pd.DataFrame,
    sheet_name: str,
    *,
    year_column: str = "Origination Year",
) -> list[ValidationIssue]:
    if year_column not in dataframe.columns:
        return []

    issues: list[ValidationIssue] = []
    current_year = datetime.now().year
    maximum_year = current_year + 1
    series = dataframe[year_column]
    present_mask = ~_missing_mask(series)
    numeric = pd.to_numeric(series, errors="coerce")
    invalid_mask = present_mask & (numeric.isna() | (numeric % 1 != 0))
    out_of_range_mask = present_mask & numeric.notna() & (
        (numeric < ORIGINATION_YEAR_MIN) | (numeric > maximum_year)
    )
    duplicate_mask = present_mask & numeric.notna() & series.duplicated(keep=False)

    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                check="invalid_origination_year",
                severity="ERROR",
                message=f"Column '{year_column}' must contain integer year values.",
                count=int(invalid_mask.sum()),
                rows=_row_numbers(dataframe, invalid_mask),
                columns=[year_column],
                examples=_examples(series.loc[invalid_mask]),
            )
        )

    if out_of_range_mask.any():
        issues.append(
            ValidationIssue(
                check="origination_year_out_of_range",
                severity="ERROR",
                message=(
                    f"Column '{year_column}' contains years outside "
                    f"{ORIGINATION_YEAR_MIN}-{maximum_year}."
                ),
                count=int(out_of_range_mask.sum()),
                rows=_row_numbers(dataframe, out_of_range_mask),
                columns=[year_column],
                examples=_examples(series.loc[out_of_range_mask]),
            )
        )

    if duplicate_mask.any():
        issues.append(
            ValidationIssue(
                check="duplicate_origination_year",
                severity="ERROR",
                message=f"Column '{year_column}' contains duplicate year values.",
                count=int(duplicate_mask.sum()),
                rows=_row_numbers(dataframe, duplicate_mask),
                columns=[year_column],
                examples=_examples(series.loc[duplicate_mask]),
            )
        )

    missing_mask = _missing_mask(series)
    if missing_mask.any():
        issues.append(
            ValidationIssue(
                check="missing_year_values",
                severity="ERROR",
                message=f"Column '{year_column}' contains missing year values.",
                count=int(missing_mask.sum()),
                rows=_row_numbers(dataframe, missing_mask),
                columns=[year_column],
            )
        )

    return issues


def _analysis_date_issues(dataframe: pd.DataFrame, sheet_name: str) -> list[ValidationIssue]:
    column = "Analysis Date"
    if column not in dataframe.columns:
        return []

    issues: list[ValidationIssue] = []
    series = dataframe[column]
    present_mask = ~_missing_mask(series)
    parsed = series[present_mask].map(_parse_yyyymm)
    invalid_mask = pd.Series(False, index=dataframe.index)
    invalid_mask.loc[parsed[parsed.isna()].index] = True

    duplicate_values = series[present_mask & ~invalid_mask]
    duplicate_mask = pd.Series(False, index=dataframe.index)
    duplicate_mask.loc[duplicate_values[duplicate_values.duplicated(keep=False)].index] = True

    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                check="invalid_analysis_date",
                severity="ERROR",
                message="Analysis Date values must use valid YYYYMM format.",
                count=int(invalid_mask.sum()),
                rows=_row_numbers(dataframe, invalid_mask),
                columns=[column],
                examples=_examples(series.loc[invalid_mask]),
            )
        )

    if duplicate_mask.any():
        issues.append(
            ValidationIssue(
                check="duplicate_analysis_date",
                severity="ERROR",
                message="Duplicate Analysis Date values were found.",
                count=int(duplicate_mask.sum()),
                rows=_row_numbers(dataframe, duplicate_mask),
                columns=[column],
                examples=_examples(series.loc[duplicate_mask]),
            )
        )

    valid_dates = parsed.dropna().sort_values()
    if len(valid_dates) >= 2:
        gaps = valid_dates.diff().dropna()
        gap_mask = pd.Series(False, index=dataframe.index)
        gap_rows: list[int] = []
        for index, gap in gaps.items():
            if gap > 1:
                gap_mask.loc[index] = True
                gap_rows.append(int(dataframe.index.get_loc(index)) + 2)
        if gap_mask.any():
            issues.append(
                ValidationIssue(
                    check="analysis_date_gaps",
                    severity="WARNING",
                    message="Analysis Date values are not mostly continuous month-to-month.",
                    count=int(gap_mask.sum()),
                    rows=gap_rows,
                    columns=[column],
                )
            )

    return issues


def _cpr_column_issues(dataframe: pd.DataFrame, column: str, sheet_name: str) -> list[ValidationIssue]:
    if column not in dataframe.columns:
        return []

    issues: list[ValidationIssue] = []
    series = dataframe[column]
    present_mask = ~_missing_mask(series)
    numeric = pd.to_numeric(series, errors="coerce")

    if present_mask.any() and numeric[present_mask].isna().all():
        issues.append(
            ValidationIssue(
                check="empty_cpr_column",
                severity="ERROR",
                message=f"Column '{column}' is entirely empty.",
                count=int(len(dataframe)),
                columns=[column],
            )
        )
        return issues

    missing_mask = _missing_mask(series)
    if missing_mask.any():
        issues.append(
            ValidationIssue(
                check="missing_cpr_values",
                severity="WARNING",
                message=f"Column '{column}' contains missing CPR values.",
                count=int(missing_mask.sum()),
                rows=_row_numbers(dataframe, missing_mask),
                columns=[column],
            )
        )

    numeric_present = present_mask & numeric.notna()
    non_numeric_mask = present_mask & numeric.isna()
    if non_numeric_mask.any():
        issues.append(
            ValidationIssue(
                check="invalid_cpr_values",
                severity="ERROR",
                message=f"Column '{column}' contains non-numeric CPR values.",
                count=int(non_numeric_mask.sum()),
                rows=_row_numbers(dataframe, non_numeric_mask),
                columns=[column],
                examples=_examples(series.loc[non_numeric_mask]),
            )
        )

    negative_mask = numeric_present & (numeric < 0)
    if negative_mask.any():
        issues.append(
            ValidationIssue(
                check="negative_cpr_values",
                severity="ERROR",
                message=f"Column '{column}' contains negative CPR values.",
                count=int(negative_mask.sum()),
                rows=_row_numbers(dataframe, negative_mask),
                columns=[column],
                examples=_examples(series.loc[negative_mask]),
            )
        )

    high_error_mask = numeric_present & (numeric > CPR_ERROR_MAX)
    if high_error_mask.any():
        issues.append(
            ValidationIssue(
                check="cpr_above_error_threshold",
                severity="ERROR",
                message=f"Column '{column}' contains CPR values above {CPR_ERROR_MAX:.0f}.",
                count=int(high_error_mask.sum()),
                rows=_row_numbers(dataframe, high_error_mask),
                columns=[column],
                examples=_examples(series.loc[high_error_mask]),
            )
        )

    high_warning_mask = numeric_present & (numeric > CPR_WARNING_MAX) & (numeric <= CPR_ERROR_MAX)
    if high_warning_mask.any():
        issues.append(
            ValidationIssue(
                check="cpr_above_review_threshold",
                severity="WARNING",
                message=f"Column '{column}' contains CPR values above review threshold {CPR_WARNING_MAX:.0f}.",
                count=int(high_warning_mask.sum()),
                rows=_row_numbers(dataframe, high_warning_mask),
                columns=[column],
                examples=_examples(series.loc[high_warning_mask]),
            )
        )

    return issues


def _non_negative_balance_issues(dataframe: pd.DataFrame, column: str, sheet_name: str) -> list[ValidationIssue]:
    if column not in dataframe.columns:
        return []

    series = dataframe[column]
    present_mask = ~_missing_mask(series)
    numeric = pd.to_numeric(series, errors="coerce")
    invalid_mask = present_mask & numeric.isna()
    negative_mask = present_mask & numeric.notna() & (numeric < 0)
    issues: list[ValidationIssue] = []

    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                check="invalid_balance_values",
                severity="ERROR",
                message=f"Column '{column}' contains non-numeric balance values.",
                count=int(invalid_mask.sum()),
                rows=_row_numbers(dataframe, invalid_mask),
                columns=[column],
                examples=_examples(series.loc[invalid_mask]),
            )
        )

    if negative_mask.any():
        issues.append(
            ValidationIssue(
                check="negative_balance_values",
                severity="ERROR",
                message=f"Column '{column}' contains negative balance values.",
                count=int(negative_mask.sum()),
                rows=_row_numbers(dataframe, negative_mask),
                columns=[column],
                examples=_examples(series.loc[negative_mask]),
            )
        )

    return issues


def _missing_balance_issues(dataframe: pd.DataFrame, column: str, sheet_name: str) -> list[ValidationIssue]:
    if column not in dataframe.columns:
        return []

    missing_mask = _missing_mask(dataframe[column])
    if not missing_mask.any():
        return []

    return [
        ValidationIssue(
            check="missing_balance_values",
            severity="ERROR",
            message=f"Column '{column}' contains missing balance values.",
            count=int(missing_mask.sum()),
            rows=_row_numbers(dataframe, missing_mask),
            columns=[column],
        )
    ]


def _wac_column_issues(dataframe: pd.DataFrame, column: str, sheet_name: str) -> list[ValidationIssue]:
    if column not in dataframe.columns:
        return []

    issues: list[ValidationIssue] = []
    series = dataframe[column]
    present_mask = ~_missing_mask(series)
    numeric = pd.to_numeric(series, errors="coerce")

    missing_mask = _missing_mask(series)
    if missing_mask.any():
        issues.append(
            ValidationIssue(
                check="missing_wac_values",
                severity="ERROR",
                message=f"Column '{column}' contains missing average WAC values.",
                count=int(missing_mask.sum()),
                rows=_row_numbers(dataframe, missing_mask),
                columns=[column],
            )
        )

    invalid_mask = present_mask & numeric.isna()
    if invalid_mask.any():
        issues.append(
            ValidationIssue(
                check="invalid_wac_values",
                severity="ERROR",
                message=f"Column '{column}' contains non-numeric average WAC values.",
                count=int(invalid_mask.sum()),
                rows=_row_numbers(dataframe, invalid_mask),
                columns=[column],
                examples=_examples(series.loc[invalid_mask]),
            )
        )

    negative_mask = present_mask & numeric.notna() & (numeric < 0)
    if negative_mask.any():
        issues.append(
            ValidationIssue(
                check="negative_wac_values",
                severity="ERROR",
                message=f"Column '{column}' contains negative average WAC values.",
                count=int(negative_mask.sum()),
                rows=_row_numbers(dataframe, negative_mask),
                columns=[column],
                examples=_examples(series.loc[negative_mask]),
            )
        )

    high_mask = present_mask & numeric.notna() & (numeric > WAC_WARNING_MAX)
    if high_mask.any():
        issues.append(
            ValidationIssue(
                check="wac_above_review_threshold",
                severity="WARNING",
                message=f"Column '{column}' contains average WAC values above {WAC_WARNING_MAX:.0f}.",
                count=int(high_mask.sum()),
                rows=_row_numbers(dataframe, high_mask),
                columns=[column],
                examples=_examples(series.loc[high_mask]),
            )
        )

    return issues


def _aligned_year_block_issues(
    dataframe: pd.DataFrame,
    yr_columns: list[str],
    sheet_name: str,
) -> list[ValidationIssue]:
    if len(yr_columns) < 2:
        return []

    reference = pd.to_numeric(dataframe[yr_columns[0]], errors="coerce")
    misaligned_columns: list[str] = []
    for column in yr_columns[1:]:
        compare = pd.to_numeric(dataframe[column], errors="coerce")
        if not reference.fillna(-1).equals(compare.fillna(-1)):
            misaligned_columns.append(column)

    if not misaligned_columns:
        return []

    return [
        ValidationIssue(
            check="misaligned_year_blocks",
            severity="ERROR",
            message="Repeated YR blocks do not align across market-share segments.",
            count=len(misaligned_columns),
            columns=[yr_columns[0], *misaligned_columns],
        )
    ]


def _parse_yyyymm(value: object) -> int | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]

    if len(text) != 6 or not text.isdigit():
        return None

    year = int(text[:4])
    month = int(text[4:])
    if month < 1 or month > 12:
        return None
    if year < ORIGINATION_YEAR_MIN:
        return None

    return year * 12 + month
