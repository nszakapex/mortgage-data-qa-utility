# CLAUDE.md

This repository is a portfolio project for mortgage-style CSV data QA using Python, pandas, pytest, and SQL-style analytical thinking.

When making changes:

- Use Python 3.12-compatible syntax.
- Keep validation logic simple enough for an analyst to audit.
- Use only synthetic or public-style sample data.
- Never describe the project as an official company tool.
- Avoid financial conclusions; report data quality conditions only.
- Debug Python and SQL-style logic carefully: reproduce the issue, isolate the smallest failing check, and preserve analyst-readable output.
- Run `pytest` before handing off changes.

Recommended local commands:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src python -m pytest
PYTHONPATH=src python -m mortgage_data_qa.report sample_data/synthetic_mortgage_loans.csv --output qa_report.md
```
