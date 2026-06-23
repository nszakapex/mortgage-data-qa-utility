# Project Brief

## Objective

Create a compact Python 3.12 utility for validating synthetic or public-style mortgage CSV data before analyst review.

## Scope

The utility focuses on simple, explainable data QA:

- Required column checks.
- Missing value checks.
- Duplicate loan identifier checks.
- Date parsing checks.
- FICO, LTV, and DTI range checks.
- Loan purpose code checks.
- Negative current balance checks.
- Suspicious coupon checks.
- Markdown report generation.

## Non-Goals

- No confidential data.
- No official company workflow claims.
- No pricing, valuation, trading, credit decisioning, or investment recommendations.
- No personally identifiable borrower data.

## Primary User

An analyst, data engineer, or research-oriented reviewer who wants a lightweight first pass over a mortgage-style CSV file.

