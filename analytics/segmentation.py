from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> bool:
    """
    Check whether the analytics table exists.
    """

    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = :table_name
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(query),
            {"table_name": table_name},
        ).fetchone()

    return result is not None


def get_available_columns(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[str]:
    """
    Return columns available in the transactions table.
    """

    if not table_exists(engine, table_name):
        return []

    query = f'PRAGMA table_info("{table_name}")'

    with engine.connect() as connection:
        rows = connection.execute(text(query)).fetchall()

    return [row[1] for row in rows]


def _empty_dataframe(
    columns: list[str],
) -> pd.DataFrame:
    """
    Create an empty DataFrame with the requested columns.
    """

    return pd.DataFrame(columns=columns)


# ============================================================
# COLUMN DETECTION
# ============================================================

def _get_sales_column(
    available_columns: list[str],
) -> str | None:
    """
    Select the best available revenue column.
    """

    if "net_sales" in available_columns:
        return "net_sales"

    if "sales_amount" in available_columns:
        return "sales_amount"

    return None


def _customer_available(
    available_columns: list[str],
) -> bool:
    """
    Check whether customer-level analysis is possible.
    """

    return "customer_id" in available_columns


# ============================================================
# RFM CALCULATION
# ============================================================

def calculate_rfm(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate customer-level RFM metrics.

    RFM:
    - Recency: days since customer's most recent order
    - Frequency: number of distinct orders
    - Monetary: total customer revenue
    """

    available_columns = get_available_columns(
        engine,
        table_name,
    )

    required_columns = {
        "customer_id",
        "order_date",
    }

    if not required_columns.issubset(
        set(available_columns)
    ):
        return _empty_dataframe(
            [
                "customer_id",
                "recency",
                "frequency",
                "monetary",
            ]
        )

    sales_column = _get_sales_column(
        available_columns
    )

    if sales_column is None:
        return _empty_dataframe(
            [
                "customer_id",
                "recency",
                "frequency",
                "monetary",
            ]
        )

    order_expression = (
        "COUNT(DISTINCT order_id)"
        if "order_id" in available_columns
        else "COUNT(*)"
    )

    query = f"""
        SELECT
            customer_id,
            MAX(order_date) AS last_order_date,
            {order_expression} AS frequency,
            SUM({sales_column}) AS monetary
        FROM "{table_name}"
        WHERE customer_id IS NOT NULL
          AND order_date IS NOT NULL
        GROUP BY customer_id
    """

    with engine.connect() as connection:
        df = pd.read_sql_query(
            text(query),
            connection,
        )

    if df.empty:
        return _empty_dataframe(
            [
                "customer_id",
                "last_order_date",
                "recency",
                "frequency",
                "monetary",
            ]
        )

    df["last_order_date"] = pd.to_datetime(
        df["last_order_date"],
        errors="coerce",
    )

    # Use the latest transaction date as the analysis
    # reference date instead of today's date. This keeps
    # segmentation reproducible for historical datasets.
    reference_date = df["last_order_date"].max()

    df["recency"] = (
        reference_date - df["last_order_date"]
    ).dt.days

    df["frequency"] = pd.to_numeric(
        df["frequency"],
        errors="coerce",
    ).fillna(0)

    df["monetary"] = pd.to_numeric(
        df["monetary"],
        errors="coerce",
    ).fillna(0)

    return df[
        [
            "customer_id",
            "last_order_date",
            "recency",
            "frequency",
            "monetary",
        ]
    ].sort_values(
        "monetary",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# RFM SCORING
# ============================================================

def _score_recency(
    value: float,
    quantiles: list[float],
) -> int:
    """
    Score recency from 1 to 5.

    Lower recency is better because a recently active
    customer has fewer days since their last order.
    """

    q1, q2, q3, q4 = quantiles

    if value <= q1:
        return 5
    if value <= q2:
        return 4
    if value <= q3:
        return 3
    if value <= q4:
        return 2

    return 1


def _score_positive_metric(
    value: float,
    quantiles: list[float],
) -> int:
    """
    Score frequency or monetary value from 1 to 5.

    Higher values receive higher scores.
    """

    q1, q2, q3, q4 = quantiles

    if value <= q1:
        return 1
    if value <= q2:
        return 2
    if value <= q3:
        return 3
    if value <= q4:
        return 4

    return 5


def _safe_quantiles(
    series: pd.Series,
) -> list[float]:
    """
    Calculate four quantile boundaries safely.

    Handles datasets with very few or identical values.
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return [0.0, 0.0, 0.0, 0.0]

    quantiles = values.quantile(
        [0.20, 0.40, 0.60, 0.80]
    ).tolist()

    return [
        float(value)
        for value in quantiles
    ]


def calculate_rfm_scores(
    rfm_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add RFM scores and combined RFM score.
    """

    if rfm_df.empty:
        return rfm_df.copy()

    result = rfm_df.copy()

    recency_quantiles = _safe_quantiles(
        result["recency"]
    )

    frequency_quantiles = _safe_quantiles(
        result["frequency"]
    )

    monetary_quantiles = _safe_quantiles(
        result["monetary"]
    )

    result["r_score"] = result[
        "recency"
    ].apply(
        lambda value: _score_recency(
            float(value),
            recency_quantiles,
        )
    )

    result["f_score"] = result[
        "frequency"
    ].apply(
        lambda value: _score_positive_metric(
            float(value),
            frequency_quantiles,
        )
    )

    result["m_score"] = result[
        "monetary"
    ].apply(
        lambda value: _score_positive_metric(
            float(value),
            monetary_quantiles,
        )
    )

    result["rfm_score"] = (
        result["r_score"]
        + result["f_score"]
        + result["m_score"]
    )

    result["rfm_code"] = (
        result["r_score"].astype(str)
        + result["f_score"].astype(str)
        + result["m_score"].astype(str)
    )

    return result


# ============================================================
# CUSTOMER SEGMENTS
# ============================================================

def assign_customer_segments(
    rfm_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign interpretable customer segments using RFM scores.
    """

    if rfm_df.empty:
        return rfm_df.copy()

    result = rfm_df.copy()

    def segment_customer(row: pd.Series) -> str:
        r = int(row["r_score"])
        f = int(row["f_score"])
        m = int(row["m_score"])

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"

        if r >= 3 and f >= 4:
            return "Loyal Customers"

        if r >= 4 and f >= 2:
            return "Potential Loyalists"

        if r >= 4 and f == 1:
            return "New Customers"

        if r == 3 and f <= 2:
            return "Needs Attention"

        if r == 2 and f >= 3:
            return "At Risk"

        if r <= 2 and f <= 2:
            return "Lost Customers"

        return "Regular Customers"

    result["segment"] = result.apply(
        segment_customer,
        axis=1,
    )

    return result


# ============================================================
# SEGMENT SUMMARY
# ============================================================

def get_segment_summary(
    rfm_segmented_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create segment-level customer and revenue summary.
    """

    if rfm_segmented_df.empty:
        return _empty_dataframe(
            [
                "segment",
                "customer_count",
                "total_revenue",
                "average_revenue",
                "average_frequency",
                "average_recency",
            ]
        )

    summary = (
        rfm_segmented_df
        .groupby("segment", as_index=False)
        .agg(
            customer_count=(
                "customer_id",
                "nunique",
            ),
            total_revenue=(
                "monetary",
                "sum",
            ),
            average_revenue=(
                "monetary",
                "mean",
            ),
            average_frequency=(
                "frequency",
                "mean",
            ),
            average_recency=(
                "recency",
                "mean",
            ),
        )
    )

    total_revenue = summary[
        "total_revenue"
    ].sum()

    if total_revenue != 0:
        summary["revenue_contribution_pct"] = (
            summary["total_revenue"]
            / total_revenue
            * 100
        )
    else:
        summary["revenue_contribution_pct"] = 0.0

    return summary.sort_values(
        "total_revenue",
        ascending=False,
    ).reset_index(drop=True)


# ============================================================
# FULL SEGMENTATION PIPELINE
# ============================================================

def run_customer_segmentation(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> dict[str, Any]:
    """
    Execute the complete RFM segmentation pipeline.

    Returns:
        Dictionary containing RFM data, scored customers,
        segment assignments and segment summary.
    """

    available_columns = get_available_columns(
        engine,
        table_name,
    )

    if not table_exists(
        engine,
        table_name,
    ):
        return {
            "available": False,
            "reason": "Transactions table does not exist.",
            "rfm": pd.DataFrame(),
            "rfm_scores": pd.DataFrame(),
            "segment_summary": pd.DataFrame(),
        }

    if not _customer_available(
        available_columns
    ):
        return {
            "available": False,
            "reason": (
                "Customer segmentation requires "
                "a customer_id field."
            ),
            "rfm": pd.DataFrame(),
            "rfm_scores": pd.DataFrame(),
            "segment_summary": pd.DataFrame(),
        }

    rfm_df = calculate_rfm(
        engine,
        table_name,
    )

    if rfm_df.empty:
        return {
            "available": False,
            "reason": (
                "Insufficient data for RFM analysis. "
                "The dataset needs customer_id, order_date "
                "and a revenue field."
            ),
            "rfm": rfm_df,
            "rfm_scores": rfm_df,
            "segment_summary": pd.DataFrame(),
        }

    scored_df = calculate_rfm_scores(
        rfm_df
    )

    segmented_df = assign_customer_segments(
        scored_df
    )

    segment_summary = get_segment_summary(
        segmented_df
    )

    return {
        "available": True,
        "reason": "RFM segmentation completed successfully.",
        "rfm": rfm_df,
        "rfm_scores": segmented_df,
        "segment_summary": segment_summary,
    }