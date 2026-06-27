# mortgage-data-qa-utility

A portfolio-ready Python 3.12 project for validating synthetic or public-style mortgage CSV datasets. It checks common loan-level data quality issues and produces an analyst-readable markdown QA report.

This is an independent learning and portfolio project. It is not an official AD&Co tool and should not be run on confidential company data.

## What It Does

- Validates required mortgage-style fields.
- Flags missing values, duplicate `loan_id` values, malformed dates, invalid numeric ranges, invalid loan purposes, negative balances, and suspicious coupons.
- Summarizes agencies, product types, purposes, vintages, date ranges, and numeric fields.
- Generates a markdown report suitable for analyst review.
- Provides both a CLI and a lightweight Streamlit UI for demo/workflow testing.
- Includes synthetic sample data and pytest coverage.

## Why It Matters

Mortgage analytics workflows often start with basic trust checks: is the data complete, parseable, deduplicated, and within expected review bands? This project shows how to turn those checks into repeatable code that can support research-style data intake before deeper cohort, performance, or pool analysis.

## Install

```bash
cd mortgage-data-qa-utility
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` is the canonical dependency source. `requirements.txt` is kept as a simple mirror for local environments that still prefer requirements-based installs.

## Run the CLI

```bash
python -m mortgage_data_qa sample_data\synthetic_mortgage_loans.csv --output qa_report.md
python -m mortgage_data_qa sample_data\clean_mortgage_loans.csv --output clean_qa_report.md
mortgage-data-qa sample_data\synthetic_mortgage_loans.csv
```

On macOS or Linux, use:

```bash
python -m mortgage_data_qa sample_data/synthetic_mortgage_loans.csv --output qa_report.md
```

## Run the Streamlit UI

The project includes a lightweight drag-and-drop UI for demo and workflow testing. It reuses the existing package validation and markdown report functions; it does not add a database, AI features, or external services.

```bash
streamlit run streamlit_app.py
```

The Streamlit UI lets you:

- Drag and drop a synthetic or approved mortgage-style CSV.
- Run the same deterministic QA checks used by the CLI.
- View pass/fail status, summary metrics, issue details, and grouped findings.
- Test with the flawed sample CSV or the clean sample CSV without uploading anything.
- Download the generated markdown report as `qa_report.md`.

Do not upload confidential, client, proprietary, or internal company data. This is an independent AD&Co-inspired portfolio project, not an official AD&Co tool.

## Sample QA Report Excerpt

The intentionally flawed sample produces a report section like this:

```markdown
## QA Status

- Status: FAIL
- Rows reviewed: 16
- Columns reviewed: 12
- Error checks triggered: 8
- Warning checks triggered: 1
```

The clean sample is included as a quick PASS case for demos and regression checks.

## Run Tests

```bash
python -m pytest -q
```

On macOS or Linux:

```bash
python -m pytest
```

## GitHub Actions

The workflow in `.github/workflows/test.yml` includes `workflow_dispatch`, so tests can be run manually from the GitHub mobile app or a phone browser:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Test Project**.
4. Tap **Run workflow**.
5. Choose the `main` branch.

## Sample Data Schema

| Column | Description | Example |
| --- | --- | --- |
| `loan_id` | Synthetic unique loan identifier | `SYNTH-0001` |
| `agency` | Agency-style category | `FNMA` |
| `product_type` | Mortgage product label | `30YR_FIXED` |
| `vintage` | Origination year cohort | `2024` |
| `origination_date` | Loan origination date | `2024-02-12` |
| `loan_purpose` | Allowed values: `purchase`, `rate_term_refinance`, `cash_out_refinance`, `streamline_refinance` | `purchase` |
| `fico` | Borrower credit score-style field | `742` |
| `ltv` | Loan-to-value percentage | `78.5` |
| `dti` | Debt-to-income percentage | `34.1` |
| `coupon` | Note rate or coupon-style percentage | `6.625` |
| `current_balance` | Current unpaid principal balance-style field | `286450.25` |
| `loan_age_months` | Months since origination | `63` |

The `synthetic_mortgage_loans.csv` sample intentionally includes a few synthetic QA issues so the report demonstrates the validator. The `synthetic_mortgage_loans_clean.csv` sample uses the same schema but should pass validation. `clean_mortgage_loans.csv` is a short alias of the clean sample for copy/paste-friendly CLI demos.

## AD&Co Relevance

This project is relevant to an AD&Co-inspired research and data workflow because it demonstrates:

- Data intake checks before analysis.
- Repeatable validation logic for loan-level or pool-level CSV files.
- Analyst-friendly markdown reporting.
- Clear separation between schema, validation, summary, reporting, and tests.
- Responsible handling of synthetic/public-style data only.

It is not affiliated with, endorsed by, or built for official use by AD&Co.

## Limitations

- Rules are intentionally simple and are not production credit policy.
- Thresholds are generic QA review bands, not financial recommendations.
- The project does not model prepayments, defaults, losses, securitization structures, or valuation.
- The sample data is synthetic and should not be used for market conclusions.
- CSV parsing assumes a flat file with one row per synthetic loan record.

## Resume Bullets

- Built a Python/pandas mortgage data QA utility that validates loan-level CSV files for schema completeness, missingness, duplicates, malformed dates, numeric range errors, invalid purpose codes, negative balances, and suspicious coupons.
- Designed analyst-readable markdown reporting with dataset summaries and issue tables for repeatable research data intake.
- Added pytest coverage and GitHub Actions manual test execution to support portable portfolio review and mobile-triggered CI checks.

## Project Layout

```text
mortgage-data-qa-utility/
  src/mortgage_data_qa/
    __main__.py
    schema.py
    validate.py
    summarize.py
    ui_summary.py
    report.py
  streamlit_app.py
  tests/
  sample_data/
  docs/
  prompts/
  .github/workflows/test.yml
```
