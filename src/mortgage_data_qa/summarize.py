"""Analyst-friendly summary statistics for mortgage-style datasets."""

from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_dataframe(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Return compact descriptive summaries without making financial conclusions."""

    summary: dict[str, Any] = {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": list(dataframe.columns),
        "categorical": {},
        "numeric": {},
    }

    for column in ["agency", "product_type", "loan_purpose", "vintage"]:
        if column in dataframe.columns:
            summary["categorical"][column] = _top_counts(dataframe[column])

    for column in ["fico", "ltv", "dti", "coupon", "current_balance", "loan_age_months"]:
        if column in dataframe.columns:
            summary["numeric"][column] = _numeric_summary(dataframe[column])

    if "origination_date" in dataframe.columns:
        parsed_dates = pd.to_datetime(dataframe["origination_date"], errors="coerce")
        valid_dates = parsed_dates.dropna()
        summary["origination_date"] = {
            "valid_count": int(valid_dates.count()),
            "min": valid_dates.min().date().isoformat() if not valid_dates.empty else None,
            "max": valid_dates.max().date().isoformat() if not valid_dates.empty else None,
        }

    return summary


def format_summary_markdown(summary: dict[str, Any]) -> str:
    """Format summary output as markdown for inclusion in a QA report."""

    lines = [
        "## Dataset Summary",
        "",
        f"- Rows: {summary['row_count']:,}",
        f"- Columns: {summary['column_count']:,}",
    ]

    if summary.get("origination_date"):
        date_summary = summary["origination_date"]
        lines.extend(
            [
                f"- Valid origination dates: {date_summary['valid_count']:,}",
                f"- Origination date range: {date_summary['min'] or 'n/a'} to {date_summary['max'] or 'n/a'}",
            ]
        )

    categorical = summary.get("categorical", {})
    if categorical:
        lines.extend(["", "### Category Counts"])
        for column, counts in categorical.items():
            lines.append(f"- {column}: {_format_counts(counts)}")

    numeric = summary.get("numeric", {})
    if numeric:
        lines.extend(["", "### Numeric Fields"])
        lines.append("| Field | Count | Mean | Min | Median | Max |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for column, stats in numeric.items():
            lines.append(
                "| {field} | {count:,} | {mean} | {min_value} | {median} | {max_value} |".format(
                    field=column,
                    count=stats["count"],
                    mean=_format_number(stats["mean"]),
                    min_value=_format_number(stats["min"]),
                    median=_format_number(stats["median"]),
                    max_value=_format_number(stats["max"]),
                )
            )

    return "\n".join(lines)


def _top_counts(series: pd.Series, limit: int = 8) -> dict[str, int]:
    counts = series.fillna("<missing>").astype(str).str.strip().replace("", "<missing>").value_counts().head(limit)
    return {str(index): int(value) for index, value in counts.items()}


def _numeric_summary(series: pd.Series) -> dict[str, float | int | None]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return {"count": 0, "mean": None, "min": None, "median": None, "max": None}

    return {
        "count": int(numeric.count()),
        "mean": float(numeric.mean()),
        "min": float(numeric.min()),
        "median": float(numeric.median()),
        "max": float(numeric.max()),
    }


def _format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={value:,}" for key, value in counts.items()) or "n/a"


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}"

