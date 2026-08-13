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


def test_streamlit_app_bootstraps_src_on_sys_path():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    streamlit_app = importlib.import_module("streamlit_app")
    src = str(Path(streamlit_app.__file__).resolve().parent / "src")

    assert Path(src).is_dir()
    assert src in sys.path


def test_requirements_txt_uses_plain_wheels_for_cloud():
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    lines = [
        line.strip()
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    assert lines == [
        "pandas>=2.2,<3.0",
        "openpyxl>=3.1,<4.0",
        "streamlit>=1.36,<2.0",
    ]
    assert not any(line.startswith("-e") or line == "." for line in lines)


def test_report_module_exports_streamlit_helpers():
    from mortgage_data_qa.report import (
        generate_markdown_report,
        generate_profile_report,
        generate_research_workbook_report,
    )

    assert callable(generate_markdown_report)
    assert callable(generate_profile_report)
    assert callable(generate_research_workbook_report)
