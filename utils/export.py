from __future__ import annotations

from io import BytesIO

import pandas as pd


def dataframe_to_csv_bytes(
    df: pd.DataFrame,
) -> bytes:
    """Convert a DataFrame into downloadable CSV bytes."""

    if df is None:
        raise ValueError("DataFrame cannot be None.")

    return df.to_csv(
        index=False
    ).encode("utf-8")


def metrics_to_dataframe(
    metrics: dict,
) -> pd.DataFrame:
    """Convert metrics dictionary into a DataFrame."""

    if not metrics:
        return pd.DataFrame(
            columns=["metric", "value"]
        )

    return pd.DataFrame(
        [
            {
                "metric": key,
                "value": value,
            }
            for key, value in metrics.items()
        ]
    )


def insights_to_dataframe(
    insights_result: dict,
) -> pd.DataFrame:
    """Extract insight records as a DataFrame."""

    if not insights_result:
        return pd.DataFrame()

    insights_df = insights_result.get(
        "insights"
    )

    if insights_df is None:
        return pd.DataFrame()

    if isinstance(
        insights_df,
        pd.DataFrame,
    ):
        return insights_df.copy()

    return pd.DataFrame(insights_df)


def combine_report_sections(
    sections: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Combine multiple report DataFrames into one
    standardized report table.
    """

    records = []

    for section_name, dataframe in sections.items():

        if dataframe is None:
            continue

        if dataframe.empty:
            continue

        for _, row in dataframe.iterrows():

            record = {
                "section": section_name
            }

            record.update(
                row.to_dict()
            )

            records.append(record)

    if not records:
        return pd.DataFrame(
            columns=[
                "section"
            ]
        )

    return pd.DataFrame(records)


def dataframe_to_excel_bytes(
    df: pd.DataFrame,
) -> bytes:
    """
    Convert a DataFrame into an Excel workbook.

    Uses an in-memory buffer so no temporary file
    is required.
    """

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Report",
        )

    output.seek(0)

    return output.getvalue()