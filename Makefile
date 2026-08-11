.PHONY: install test lint demo cli-loan cli-workbook streamlit

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m ruff check .

demo: install test
	@echo "Launching Streamlit demo UI..."
	python -m streamlit run streamlit_app.py

cli-loan:
	python -m mortgage_data_qa sample_data/synthetic_mortgage_loans.csv

cli-workbook:
	python -m mortgage_data_qa sample_data/synthetic_pool_research_fail.xlsx

streamlit:
	python -m streamlit run streamlit_app.py
