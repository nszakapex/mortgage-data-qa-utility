# CLAUDE.md

This repository is a portfolio project for mortgage-style CSV and Excel data QA using Python, pandas, pytest, Streamlit, and SQL-style analytical thinking.

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
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mortgage_data_qa sample_data/synthetic_mortgage_loans.csv
python -m mortgage_data_qa sample_data/synthetic_pool_research_fail.xlsx
python -m streamlit run streamlit_app.py
```
