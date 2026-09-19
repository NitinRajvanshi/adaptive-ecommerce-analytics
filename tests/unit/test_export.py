import pandas as pd
from utils.export import (
    combine_report_sections,
    dataframe_to_csv_bytes,
    insights_to_dataframe,
    metrics_to_dataframe,
)


def test_dataframe_to_csv():
    df = pd.DataFrame({
        "name": ["A", "B"],
        "value": [10, 20],
    })

    result = dataframe_to_csv_bytes(df)

    assert isinstance(result, bytes)
    assert b"name" in result
    assert b"value" in result


def test_metrics_to_dataframe():
    metrics = {
        "total_revenue": 1000,
        "total_orders": 10,
    }

    result = metrics_to_dataframe(metrics)

    assert len(result) == 2
    assert "metric" in result.columns
    assert "value" in result.columns


def test_insights_to_dataframe():
    insights = {
        "insights": pd.DataFrame({
            "category": ["Revenue"],
            "insight": ["Revenue increased"],
        })
    }

    result = insights_to_dataframe(insights)

    assert len(result) == 1


def test_combine_report_sections():
    sections = {
        "metrics": pd.DataFrame({
            "metric": ["Revenue"],
            "value": [1000],
        }),
        "products": pd.DataFrame({
            "product": ["Laptop"],
            "revenue": [500],
        }),
    }

    result = combine_report_sections(sections)

    assert "section" in result.columns
    assert len(result) == 2