# AGENTS.md

Guidance for coding agents working on this repository.

## Mission

Build and maintain a simple Python 3.12 utility that validates synthetic or public-style mortgage CSV data. The workflow should feel useful for research, analytics, SQL-style data thinking, SAS-style analytics context, and data QA review without relying on confidential company data.

## Working Rules

- Use synthetic or public-style data only.
- Do not claim this is an official tool for any employer or client.
- Do not invent credit, valuation, performance, or investment conclusions.
- Keep code readable, explicit, and easy to test.
- Prefer pandas for CSV loading, validation masks, and summaries.
- Preserve analyst-readable markdown output.
- Add or update pytest coverage when changing validation behavior.
- Keep SQL examples generic and runnable against synthetic tables.
- Treat SAS-style analytics as context for disciplined tabular QA, cohorting, and summary thinking; do not add SAS dependencies unless explicitly requested.

## Domain Conventions

- Required fields live in `src/mortgage_data_qa/schema.py`.
- Validation rules live in `src/mortgage_data_qa/validate.py`.
- Summary-only logic lives in `src/mortgage_data_qa/summarize.py`.
- Report formatting lives in `src/mortgage_data_qa/report.py`.
- Treat thresholds as configurable research assumptions, not universal mortgage rules.
- Keep transformations easy to translate into SQL-style filters, grouping, and aggregate checks.

## Definition of Done

- `pytest` passes.
- README instructions still work.
- Sample data remains fake and contains no personal borrower information.
- Reports describe data quality findings only.
