"""Shared schema and rule constants for mortgage-style datasets."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = [
    "loan_id",
    "agency",
    "product_type",
    "vintage",
    "origination_date",
    "loan_purpose",
    "fico",
    "ltv",
    "dti",
    "coupon",
    "current_balance",
    "loan_age_months",
]

# Map common real-world / research CSV headers onto the canonical loan-level schema.
# Keys are normalized aliases (lowercase, stripped, spaces/dashes -> underscores).
COLUMN_ALIASES: dict[str, str] = {
    "loan_id": "loan_id",
    "loanid": "loan_id",
    "loan_number": "loan_id",
    "loannumber": "loan_id",
    "loan_no": "loan_id",
    "id": "loan_id",
    "agency": "agency",
    "seller": "agency",
    "seller_name": "agency",
    "product_type": "product_type",
    "product": "product_type",
    "product_name": "product_type",
    "mortgage_product": "product_type",
    "vintage": "vintage",
    "orig_year": "vintage",
    "origination_year": "vintage",
    "origination_date": "origination_date",
    "orig_date": "origination_date",
    "closing_date": "origination_date",
    "close_date": "origination_date",
    "loan_purpose": "loan_purpose",
    "purpose": "loan_purpose",
    "purpose_code": "loan_purpose",
    "fico": "fico",
    "credit_score": "fico",
    "cs_fico": "fico",
    "borrower_fico": "fico",
    "ltv": "ltv",
    "orig_ltv": "ltv",
    "original_ltv": "ltv",
    "oltv": "ltv",
    "dti": "dti",
    "debt_to_income": "dti",
    "backend_dti": "dti",
    "coupon": "coupon",
    "note_rate": "coupon",
    "interest_rate": "coupon",
    "rate": "coupon",
    "current_balance": "current_balance",
    "upb": "current_balance",
    "current_upb": "current_balance",
    "unpaid_balance": "current_balance",
    "unpaid_principal_balance": "current_balance",
    "balance": "current_balance",
    "loan_age_months": "loan_age_months",
    "loan_age": "loan_age_months",
    "age_months": "loan_age_months",
    "age": "loan_age_months",
}

VALID_LOAN_PURPOSES = {
    "purchase",
    "rate_term_refinance",
    "cash_out_refinance",
    "streamline_refinance",
}

FICO_MIN = 300
FICO_MAX = 850

LTV_MIN = 0
LTV_MAX = 125

DTI_MIN = 0
DTI_MAX = 65

COUPON_SUSPICIOUS_MIN = 1.0
COUPON_SUSPICIOUS_MAX = 12.0

# If at least this many required fields are present after aliasing, treat as loan-level.
LOAN_LEVEL_MATCH_THRESHOLD = 8


def normalize_header_name(column: object) -> str:
    """Normalize a CSV header for alias matching."""

    text = str(column).strip().lower()
    text = text.replace("-", "_").replace("/", "_")
    text = " ".join(text.split())
    return text.replace(" ", "_")


def canonicalize_loan_level_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with recognizable headers renamed to REQUIRED_COLUMNS names."""

    renamed: dict[str, str] = {}
    used_targets: set[str] = set()

    for column in dataframe.columns:
        canonical = COLUMN_ALIASES.get(normalize_header_name(column))
        if not canonical or canonical in used_targets:
            continue
        if str(column) != canonical:
            renamed[str(column)] = canonical
        used_targets.add(canonical)

    result = dataframe.rename(columns=renamed).copy()
    if "loan_id" in result.columns:
        result["loan_id"] = result["loan_id"].astype("string")
    return result


def matched_loan_level_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return canonical loan-level columns found after alias normalization."""

    normalized = canonicalize_loan_level_columns(dataframe)
    return [column for column in REQUIRED_COLUMNS if column in normalized.columns]


def looks_like_loan_level(dataframe: pd.DataFrame) -> bool:
    """Heuristic: enough recognizable loan-level fields to use that profile."""

    return len(matched_loan_level_columns(dataframe)) >= LOAN_LEVEL_MATCH_THRESHOLD
