"""Streamlit UI for running mortgage CSV data-quality checks."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd
import streamlit as st

from mortgage_data_qa.report import generate_markdown_report
from mortgage_data_qa.ui_summary import issue_to_dict, issues_to_records, summarize_validation_result
from mortgage_data_qa.validate import validate_dataframe


ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT_DIR / "sample_data"
SAMPLES = {
    "Use flawed sample": SAMPLE_DIR / "synthetic_mortgage_loans.csv",
    "Use clean sample": SAMPLE_DIR / "synthetic_mortgage_loans_clean.csv",
}


def main() -> None:
    st.set_page_config(page_title="Mortgage Data QA Utility", page_icon=":bar_chart:", layout="wide")
    _inject_styles()

    st.title("Mortgage Data QA Utility")
    st.caption("Upload a synthetic or approved mortgage-style CSV to run data-quality checks before analysis.")
    st.warning("Do not upload confidential, client, proprietary, or internal company data.")

    dataframe, dataset_name = _load_dataset()
    if dataframe is None:
        _render_empty_state()
        return

    with st.spinner("Running deterministic QA checks..."):
        result = validate_dataframe(dataframe)
        report = generate_markdown_report(dataframe, dataset_name=dataset_name, validation_result=result)
        summary = summarize_validation_result(result)

    _render_status(result.passed, dataset_name)
    _render_metrics(summary)
    _render_issue_details(result.issues)
    _render_report(report)


def _load_dataset() -> tuple[pd.DataFrame | None, str]:
    st.subheader("CSV input")
    left, right = st.columns([2, 1], gap="large")

    with left:
        uploaded_file = st.file_uploader(
            "Drag and drop a CSV file",
            type=["csv"],
            help="Use synthetic or approved mortgage-style CSV files only.",
        )

    with right:
        sample_choice = st.selectbox(
            "Or test with sample data",
            ["No sample"] + list(SAMPLES.keys()),
            index=0,
        )

    if uploaded_file is not None:
        return _read_csv(uploaded_file), uploaded_file.name

    if sample_choice != "No sample":
        sample_path = SAMPLES[sample_choice]
        return _read_csv(sample_path), sample_path.name

    return None, ""


def _read_csv(source: str | Path | BinaryIO) -> pd.DataFrame:
    return pd.read_csv(source, dtype={"loan_id": "string"})


def _render_empty_state() -> None:
    st.info(
        "Upload a CSV or choose a synthetic sample to see pass/fail status, issue counts, row-level findings, "
        "and a downloadable markdown QA report."
    )


def _render_status(passed: bool, dataset_name: str) -> None:
    status = "PASS" if passed else "FAIL"
    status_class = "status-pass" if passed else "status-fail"
    st.markdown(
        f"""
        <section class="qa-status {status_class}">
          <div>
            <span class="eyebrow">Current QA run</span>
            <h2>{status}</h2>
            <p>{dataset_name}</p>
          </div>
          <span class="status-pill">{'Ready for analysis' if passed else 'Review required'}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_metrics(summary: dict[str, int | bool]) -> None:
    metric_rows = [
        ("Total rows", summary["total_rows"]),
        ("Total errors", summary["total_error_findings"]),
        ("Total warnings", summary["total_warning_findings"]),
        ("Duplicate loan IDs", summary["duplicate_loan_ids"]),
        ("Missing required columns", summary["missing_required_columns"]),
        ("Missing values", summary["missing_values"]),
        ("Invalid FICO values", summary["invalid_fico_values"]),
        ("Invalid LTV values", summary["invalid_ltv_values"]),
        ("Invalid DTI values", summary["invalid_dti_values"]),
        ("Malformed dates", summary["malformed_dates"]),
        ("Invalid loan purpose values", summary["invalid_loan_purpose_values"]),
        ("Negative balances", summary["negative_balances"]),
        ("Suspicious coupon values", summary["suspicious_coupon_values"]),
    ]

    st.subheader("Summary")
    cols = st.columns(4)
    for index, (label, value) in enumerate(metric_rows):
        with cols[index % len(cols)]:
            st.metric(label, f"{int(value):,}")


def _render_issue_details(issues) -> None:
    st.subheader("Issue detail")
    if not issues:
        st.success("No QA issues were found in this dataset.")
        return

    records = issues_to_records(issues)
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)

    with st.expander("Grouped validation issues"):
        for issue in issues:
            st.json(issue_to_dict(issue), expanded=False)


def _render_report(report: str) -> None:
    st.subheader("Markdown report")
    st.download_button(
        "Download markdown report",
        data=report,
        file_name="qa_report.md",
        mime="text/markdown",
        type="primary",
    )
    st.markdown(report)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        /* Hallmark component: Streamlit workbench; tone: restrained financial QA; anchor hue: slate blue */
        .block-container {
            max-width: 1180px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.015em;
        }

        [data-testid="stMetric"] {
            background: rgba(248, 250, 252, 0.72);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 14px;
            padding: 1rem 1.1rem;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.05);
        }

        .qa-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1.4rem 0 1.25rem;
            padding: 1.3rem 1.4rem;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(255,255,255,0.86), rgba(248,250,252,0.82));
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
        }

        .qa-status h2 {
            margin: 0;
            font-size: 2rem;
            line-height: 1;
        }

        .qa-status p {
            margin: 0.35rem 0 0;
            color: rgba(51, 65, 85, 0.9);
        }

        .eyebrow {
            display: block;
            margin-bottom: 0.35rem;
            color: rgba(71, 85, 105, 0.9);
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .status-pill {
            border-radius: 999px;
            padding: 0.45rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 700;
        }

        .status-pass .status-pill {
            background: rgba(22, 101, 52, 0.1);
            color: rgb(22, 101, 52);
        }

        .status-fail .status-pill {
            background: rgba(153, 27, 27, 0.09);
            color: rgb(153, 27, 27);
        }

        @media (max-width: 640px) {
            .qa-status {
                align-items: flex-start;
                flex-direction: column;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
