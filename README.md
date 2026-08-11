# mortgage-data-qa-utility

A portfolio-ready Python 3.12 project for validating synthetic or public-style mortgage CSV and Excel datasets. It checks common loan-level and pool/research-style data quality issues and produces an analyst-readable markdown QA report.

This is an independent learning and portfolio project. It is not an official AD&Co tool and should not be run on confidential company data.

## What It Does

- Validates required mortgage-style loan-level fields.
- Flags missing values, duplicate `loan_id` values, malformed dates, invalid numeric ranges, invalid loan purposes, negative balances, and suspicious coupons.
- Validates pool/research-style Excel workbook sheets (vintage balance, CPR comparison, market-share layouts).
- Supports three validation profiles: loan-level, mortgage research workbook, and generic research table.
- Generates a markdown report suitable for analyst review.
- Provides both a CLI and a lightweight Streamlit UI for demo/workflow testing.
- Includes synthetic sample data and pytest coverage.

## Why It Matters

Mortgage analytics workflows often start with basic trust checks: is the data complete, parseable, deduplicated, and within expected review bands? This project shows how to turn those checks into repeatable code that can support research-style data intake before deeper cohort, performance, or pool analysis.

## Quickstart

```bash
cd mortgage-data-qa-utility
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows
make install
make demo                          # runs tests, then launches Streamlit
```

Or install manually:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`pyproject.toml` is the canonical dependency source. `requirements.txt` is kept as a simple mirror.

## CLI vs Streamlit

| Surface | Best for | Inputs |
| --- | --- | --- |
| **CLI** | Quick loan CSV checks; Excel research workbooks with `--profile` | `.csv`, `.xlsx`, `.xls` |
| **Streamlit UI** | Live walkthroughs, sheet selection, all-sheets workbook review | `.csv`, `.xlsx`, `.xls` |

Default profiles:

- `.csv` → `loan_level`
- `.xlsx` / `.xls` → `mortgage_research_workbook`

## Run the CLI

Loan-level FAIL and PASS samples:

```bash
python -m mortgage_data_qa sample_data/synthetic_mortgage_loans.csv
python -m mortgage_data_qa sample_data/clean_mortgage_loans.csv
```

Research workbook PASS and FAIL samples:

```bash
python -m mortgage_data_qa sample_data/synthetic_pool_research.xlsx
python -m mortgage_data_qa sample_data/synthetic_pool_research_fail.xlsx
```

Optional flags:

```bash
python -m mortgage_data_qa sample_data/synthetic_pool_research.xlsx --sheet Investor_balance_vintageOrigin
python -m mortgage_data_qa sample_data/synthetic_mortgage_loans.csv --profile loan_level --output qa_report.md
mortgage-data-qa sample_data/synthetic_pool_research_fail.xlsx
```

`qa_report.md` is gitignored, so generated reports stay local unless you choose another output path.

## Run the Streamlit UI

```bash
make streamlit
# or
streamlit run streamlit_app.py
```

The Streamlit UI lets you:

- Drag and drop a synthetic or approved mortgage-style CSV or Excel workbook.
- Choose a validation profile: loan-level, mortgage research workbook, or generic research table.
- Validate a single sheet or all sheets in an Excel workbook.
- View pass/fail status, summary metrics, issue details, and grouped findings.
- Test with flawed/clean loan samples and clean/flawed research workbooks without uploading anything.
- Download the generated markdown report as `qa_report.md`.

Do not upload confidential, client, proprietary, or internal company data. This is an independent AD&Co-inspired portfolio project, not an official AD&Co tool.

## Sample QA Report Excerpt

The intentionally flawed loan sample produces a report section like this:

```markdown
## QA Status

- Status: FAIL
- Rows reviewed: 16
- Columns reviewed: 12
- Error checks triggered: 8
- Warning checks triggered: 1
```

Demo samples:

- `sample_data/synthetic_mortgage_loans.csv` — loan-level FAIL
- `sample_data/clean_mortgage_loans.csv` — loan-level PASS (`synthetic_mortgage_loans_clean.csv` is an alias of the same file)
- `sample_data/synthetic_pool_research.xlsx` — research workbook PASS
- `sample_data/synthetic_pool_research_fail.xlsx` — research workbook FAIL

## Run Tests

```bash
make test
# or
python -m pytest -q
```

## GitHub Actions

The workflow in `.github/workflows/test.yml` includes `workflow_dispatch`, so tests can be run manually from the GitHub mobile app or a phone browser:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Select **Test Project**.
4. Tap **Run workflow**.
5. Choose the `main` branch.

## Sample Data Schema (loan-level)

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

## AD&Co Relevance

This project is relevant to an AD&Co-inspired research and data workflow because it demonstrates:

- Data intake checks before analysis.
- Repeatable validation logic for loan-level CSV files and pool/research Excel workbooks.
- Analyst-friendly markdown reporting and a lightweight Streamlit walkthrough UI.
- Clear separation between schema, validation, profiles, summary, reporting, and tests.
- Responsible handling of synthetic/public-style data only.

It is not affiliated with, endorsed by, or built for official use by AD&Co.

## Limitations

- Rules are intentionally simple and are not production credit policy.
- Thresholds are generic QA review bands, not financial recommendations.
- The project does not model prepayments, defaults, losses, securitization structures, or valuation.
- The sample data is synthetic and should not be used for market conclusions.
- Findings are data-quality checks only; they are not credit, valuation, or investment conclusions.

## Resume Bullets

- Built a Python/pandas mortgage data QA utility that validates loan-level CSV files for schema completeness, missingness, duplicates, malformed dates, numeric range errors, invalid purpose codes, negative balances, and suspicious coupons.
- Added a mortgage research workbook profile for pool/research Excel sheets (vintage balance, CPR comparison, and wide market-share layouts) with analyst-readable markdown reporting.
- Shipped a Streamlit demo UI with CSV/Excel upload, profile selection, single-sheet and all-sheets workbook validation, and downloadable QA reports.
- Added pytest coverage and GitHub Actions (including Streamlit import smoke checks) for portable portfolio review and mobile-triggered CI runs.

## Project Layout

```text
mortgage-data-qa-utility/
  src/mortgage_data_qa/
    __main__.py
    schema.py
    validate.py
    profiles.py
    research_profiles.py
    summarize.py
    ui_summary.py
    report.py
  streamlit_app.py
  Makefile
  tests/
  sample_data/
  docs/
  prompts/
  .github/workflows/test.yml
```
