"""Validation profile registry and dispatch."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from mortgage_data_qa.research_profiles import (
    WorkbookValidationResult,
    validate_generic_research_table,
    validate_research_sheet,
    validate_research_workbook,
)
from mortgage_data_qa.validate import ValidationResult, validate_dataframe


class ValidationProfile(StrEnum):
    LOAN_LEVEL = "loan_level"
    MORTGAGE_RESEARCH_WORKBOOK = "mortgage_research_workbook"
    GENERIC_RESEARCH = "generic_research"


PROFILE_LABELS: dict[ValidationProfile, str] = {
    ValidationProfile.LOAN_LEVEL: "Loan-level mortgage data",
    ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK: "Mortgage research workbook",
    ValidationProfile.GENERIC_RESEARCH: "Generic research table",
}


def default_profile_for_filename(filename: str) -> ValidationProfile:
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK
    return ValidationProfile.LOAN_LEVEL


def profile_label(profile: ValidationProfile | str) -> str:
    try:
        return PROFILE_LABELS[ValidationProfile(profile)]
    except ValueError:
        return str(profile)


def validate_dataframe_with_profile(
    dataframe: pd.DataFrame,
    profile: ValidationProfile | str,
    *,
    sheet_name: str = "sheet",
) -> ValidationResult:
    selected = ValidationProfile(profile)
    if selected is ValidationProfile.LOAN_LEVEL:
        return validate_dataframe(dataframe)
    if selected is ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK:
        return validate_research_sheet(dataframe, sheet_name=sheet_name)
    return validate_generic_research_table(dataframe)


def validate_workbook_file(
    source: str | Path | BinaryIO,
    *,
    file_name: str,
    sheet_name: str | None = None,
) -> WorkbookValidationResult:
    return validate_research_workbook(source, file_name=file_name, sheet_name=sheet_name)


def load_excel_sheet(source: str | Path | BinaryIO, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(source, sheet_name=sheet_name, engine="openpyxl")


def list_excel_sheets(source: str | Path | BinaryIO) -> list[str]:
    workbook = pd.ExcelFile(source, engine="openpyxl")
    return workbook.sheet_names
