# Project Brief

## Objective

Create a compact Python 3.12 utility for validating synthetic or public-style mortgage CSV and Excel data before analyst review.

## Scope

The utility focuses on simple, explainable data QA:

- Required column checks for loan-level files.
- Missing value checks.
- Duplicate loan identifier checks.
- Date parsing checks.
- FICO, LTV, and DTI range checks.
- Loan purpose code checks.
- Negative current balance checks.
- Suspicious coupon checks.
- Mortgage research workbook validation for vintage balance, CPR comparison, and market-share sheets.
- Validation profiles: `loan_level`, `mortgage_research_workbook`, and `generic_research`.
- Markdown report generation.
- CLI and Streamlit UI for demo/workflow testing.

## Non-Goals

- No confidential data.
- No official company workflow claims.
- No pricing, valuation, trading, credit decisioning, or investment recommendations.
- No personally identifiable borrower data.
- No AI/OpenAI features or database backend.

## Primary User

An analyst, data engineer, or research-oriented reviewer who wants a lightweight first pass over a mortgage-style CSV file or pool/research Excel workbook.
