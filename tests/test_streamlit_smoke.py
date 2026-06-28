"""Smoke tests for Streamlit app imports and report API compatibility."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def test_streamlit_app_imports_without_error():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    streamlit_app = importlib.import_module("streamlit_app")

    assert hasattr(streamlit_app, "main")


def test_report_module_exports_streamlit_helpers():
    from mortgage_data_qa.report import (
        generate_markdown_report,
        generate_profile_report,
        generate_research_workbook_report,
    )

    assert callable(generate_markdown_report)
    assert callable(generate_profile_report)
    assert callable(generate_research_workbook_report)
