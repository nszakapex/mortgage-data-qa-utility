"""Shared schema and rule constants for mortgage-style synthetic datasets."""

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

