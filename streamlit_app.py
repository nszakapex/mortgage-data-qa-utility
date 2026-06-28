"""Streamlit UI for running mortgage data-quality checks."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from mortgage_data_qa.profiles import (
    ValidationProfile,
    default_profile_for_filename,
    load_excel_sheet,
    profile_label,
    validate_dataframe_with_profile,
    validate_workbook_file,
)
from mortgage_data_qa.report import generate_markdown_report, generate_profile_report, generate_research_workbook_report
from mortgage_data_qa.ui_summary import (
    issue_to_dict,
    issues_to_records,
    summarize_validation_result,
    summarize_workbook_result,
    workbook_issues_to_records,
)
from mortgage_data_qa.validate import load_csv, validate_dataframe


ROOT_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT_DIR / "sample_data"
CSV_SAMPLES = {
    "Use flawed loan sample": SAMPLE_DIR / "synthetic_mortgage_loans.csv",
    "Use clean loan sample": SAMPLE_DIR / "clean_mortgage_loans.csv",
}
WORKBOOK_SAMPLE = SAMPLE_DIR / "synthetic_pool_research.xlsx"

PROFILE_OPTIONS = [
    ValidationProfile.LOAN_LEVEL,
    ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK,
    ValidationProfile.GENERIC_RESEARCH,
]


def main() -> None:
    st.set_page_config(page_title="Mortgage Data QA Utility", page_icon=":bar_chart:", layout="wide")
    _inject_styles()

    st.title("Mortgage Data QA Utility")
    st.caption(
        "Upload synthetic or approved mortgage-style CSV or Excel files to run data-quality checks before analysis."
    )
    st.warning("Do not upload confidential, client, proprietary, or internal company data.")

    uploaded_file, sample_choice = _render_input_controls()
    if uploaded_file is None and sample_choice == "No sample":
        _render_empty_state()
        return

    file_name, file_bytes, suffix = _resolve_upload(uploaded_file, sample_choice)
    default_profile = default_profile_for_filename(file_name)
    profile = _render_profile_selector(default_profile, suffix)

    if profile is ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK and suffix in {".xlsx", ".xls"}:
        _run_workbook_validation(file_bytes, file_name)
        return

    _run_table_validation(file_bytes, file_name, profile, suffix)


def _render_input_controls() -> tuple[object | None, str]:
    st.subheader("Data input")
    left, right = st.columns([2, 1], gap="large")

    with left:
        uploaded_file = st.file_uploader(
            "Drag and drop a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Use synthetic or approved mortgage-style files only.",
        )

    with right:
        sample_options = ["No sample", *CSV_SAMPLES.keys()]
        if WORKBOOK_SAMPLE.exists():
            sample_options.append("Use synthetic research workbook")
        sample_choice = st.selectbox("Or test with sample data", sample_options, index=0)

    return uploaded_file, sample_choice


def _resolve_upload(
    uploaded_file: object | None,
    sample_choice: str,
) -> tuple[str, bytes, str]:
    if uploaded_file is not None:
        return uploaded_file.name, uploaded_file.getvalue(), Path(uploaded_file.name).suffix.lower()

    if sample_choice in CSV_SAMPLES:
        sample_path = CSV_SAMPLES[sample_choice]
        return sample_path.name, sample_path.read_bytes(), sample_path.suffix.lower()

    if sample_choice == "Use synthetic research workbook":
        return WORKBOOK_SAMPLE.name, WORKBOOK_SAMPLE.read_bytes(), WORKBOOK_SAMPLE.suffix.lower()

    raise RuntimeError("No input selected")


def _render_profile_selector(default_profile: ValidationProfile, suffix: str) -> ValidationProfile:
    labels = [profile_label(option) for option in PROFILE_OPTIONS]
    default_index = PROFILE_OPTIONS.index(default_profile)
    selected_label = st.selectbox(
        "Validation profile",
        labels,
        index=default_index,
        help="Loan-level checks apply to loan CSVs. Mortgage research workbook checks pool/research summary sheets.",
    )
    selected = PROFILE_OPTIONS[labels.index(selected_label)]

    if suffix in {".xlsx", ".xls"} and selected is ValidationProfile.LOAN_LEVEL:
        st.info("Excel workbooks are usually validated with the Mortgage research workbook profile.")

    return selected


def _run_workbook_validation(file_bytes: bytes, file_name: str) -> None:
    buffer = io.BytesIO(file_bytes)
    workbook = pd.ExcelFile(buffer, engine="openpyxl")
    sheet_names = workbook.sheet_names

    validate_all = st.checkbox("Validate all sheets", value=True)
    selected_sheet = None
    if not validate_all:
        selected_sheet = st.selectbox("Sheet", sheet_names)

    with st.spinner("Running deterministic workbook QA checks..."):
        buffer.seek(0)
        workbook_result = validate_workbook_file(
            buffer,
            file_name=file_name,
            sheet_name=selected_sheet,
        )
        report = generate_research_workbook_report(workbook_result)
        summary = summarize_workbook_result(workbook_result)

    _render_status(workbook_result.passed, file_name, profile_label(ValidationProfile.MORTGAGE_RESEARCH_WORKBOOK))
    _render_workbook_metrics(summary)
    _render_workbook_sheet_status(workbook_result)
    _render_issue_details(workbook_issues_to_records(workbook_result))
    _render_report(report)


def _run_table_validation(file_bytes: bytes, file_name: str, profile: ValidationProfile, suffix: str) -> None:
    buffer = io.BytesIO(file_bytes)
    sheet_name = "sheet"

    if suffix in {".xlsx", ".xls"}:
        workbook = pd.ExcelFile(buffer, engine="openpyxl")
        sheet_name = st.selectbox("Sheet", workbook.sheet_names)
        buffer.seek(0)
        dataframe = load_excel_sheet(buffer, sheet_name)
    elif profile is ValidationProfile.LOAN_LEVEL:
        dataframe = load_csv(buffer)
    else:
        dataframe = pd.read_csv(buffer)

    with st.spinner("Running deterministic QA checks..."):
        if profile is ValidationProfile.LOAN_LEVEL:
            result = validate_dataframe(dataframe)
            report = generate_markdown_report(dataframe, dataset_name=file_name, validation_result=result)
        else:
            result = validate_dataframe_with_profile(dataframe, profile, sheet_name=sheet_name)
            report = generate_profile_report(
                dataframe,
                dataset_name=file_name,
                profile=profile,
                validation_result=result,
                sheet_name=sheet_name,
            )
        summary = summarize_validation_result(result)

    _render_status(result.passed, file_name, profile_label(profile))
    _render_table_metrics(summary, profile)
    _render_issue_details(issues_to_records(result.issues))
    with st.expander("Grouped validation issues"):
        for issue in result.issues:
            st.json(issue_to_dict(issue), expanded=False)
    _render_report(report)


def _render_empty_state() -> None:
    st.info(
        "Upload a CSV/Excel file or choose a synthetic sample to see pass/fail status, issue counts, row-level "
        "findings, and a downloadable markdown QA report."
    )


def _render_status(passed: bool, dataset_name: str, profile_name: str) -> None:
    status = "PASS" if passed else "FAIL"
    status_class = "status-pass" if passed else "status-fail"
    st.markdown(
        f"""
        <section class="qa-status {status_class}">
          <div>
            <span class="eyebrow">Current QA run</span>
            <h2>{status}</h2>
            <p>{dataset_name}</p>
            <p>{profile_name}</p>
          </div>
          <span class="status-pill">{'Ready for analysis' if passed else 'Review required'}</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_table_metrics(summary: dict[str, int | bool], profile: ValidationProfile) -> None:
    st.subheader("Summary")
    base_metrics = [
        ("Total rows", summary["total_rows"]),
        ("Total errors", summary["total_error_findings"]),
        ("Total warnings", summary["total_warning_findings"]),
    ]

    if profile is ValidationProfile.LOAN_LEVEL:
        metric_rows = base_metrics + [
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
    else:
        metric_rows = base_metrics

    cols = st.columns(4)
    for index, (label, value) in enumerate(metric_rows):
        with cols[index % len(cols)]:
            st.metric(label, f"{int(value):,}")


def _render_workbook_metrics(summary: dict[str, int | bool]) -> None:
    st.subheader("Summary")
    metric_rows = [
        ("Sheets reviewed", summary["sheets_reviewed"]),
        ("Sheets failed", summary["sheets_failed"]),
        ("Total rows", summary["total_rows"]),
        ("Total errors", summary["total_error_findings"]),
        ("Total warnings", summary["total_warning_findings"]),
    ]
    cols = st.columns(5)
    for index, (label, value) in enumerate(metric_rows):
        with cols[index % len(cols)]:
            st.metric(label, f"{int(value):,}")


def _render_workbook_sheet_status(workbook_result) -> None:
    st.subheader("Per-sheet status")
    records = []
    for sheet in workbook_result.sheet_results:
        records.append(
            {
                "sheet": sheet.sheet_name,
                "layout": sheet.sheet_type,
                "status": "PASS" if sheet.result.passed else "FAIL",
                "rows": sheet.result.row_count,
                "errors": sheet.result.error_count,
                "warnings": sheet.result.warning_count,
            }
        )
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)


def _render_issue_details(records: list[dict]) -> None:
    st.subheader("Issue detail")
    if not records:
        st.success("No QA issues were found in this dataset.")
        return

    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)


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
