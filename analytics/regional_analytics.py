from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


# ============================================================
# DATABASE HELPERS
# ============================================================

def table_exists(engine: Engine) -> bool:
    """Check whether the transactions table exists."""

    try:
        query = text(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = :table_name
            """
        )

        with engine.connect() as connection:
            result = connection.execute(
                query,
                {"table_name": TABLE_NAME},
            ).fetchone()

        return result is not None

    except Exception:
        return False


def get_available_columns(engine: Engine) -> set[str]:
    """Return available columns from the transactions table."""

    try:
        query = text(
            f"PRAGMA table_info({TABLE_NAME})"
        )

        with engine.connect() as connection:
            rows = connection.execute(query).fetchall()

        return {row[1] for row in rows}

    except Exception:
        return set()


def _get_sales_column(
    available_columns: set[str],
) -> Optional[str]:
    """Select the preferred revenue column."""

    if "net_sales" in available_columns:
        return "net_sales"

    if "sales_amount" in available_columns:
        return "sales_amount"

    return None


def _empty_dataframe(
    columns: list[str],
) -> pd.DataFrame:
    """Return an empty DataFrame with known columns."""

    return pd.DataFrame(columns=columns)


def _get_order_expression(
    available_columns: set[str],
) -> str:
    """Return an adaptive order-count expression."""

    if "order_id" in available_columns:
        return "COUNT(DISTINCT order_id)"

    return "COUNT(*)"


# ============================================================
# REGION PERFORMANCE
# ============================================================

def get_region_performance(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate revenue, orders, quantity, AOV and profit
    by region.
    """

    base_columns = [
        "region",
        "revenue",
        "order_count",
        "quantity_sold",
        "average_order_value",
    ]

    if not table_exists(engine):
        return _empty_dataframe(base_columns)

    columns = get_available_columns(engine)

    if "region" not in columns:
        return _empty_dataframe(base_columns)

    sales_column = _get_sales_column(columns)
    order_expression = _get_order_expression(columns)

    select_parts = [
        "region",
    ]

    if sales_column:
        select_parts.append(
            f"""
            SUM(
                COALESCE({sales_column}, 0)
            ) AS revenue
            """
        )

    select_parts.append(
        f"{order_expression} AS order_count"
    )

    if "quantity" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(quantity, 0)
            ) AS quantity_sold
            """
        )

    if sales_column:
        select_parts.append(
            f"""
            CASE
                WHEN {order_expression} = 0
                THEN 0
                ELSE
                    SUM(
                        COALESCE({sales_column}, 0)
                    )
                    /
                    {order_expression}
            END AS average_order_value
            """
        )

    if "profit" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(profit, 0)
            ) AS profit
            """
        )

    query = text(
        f"""
        SELECT
            {",".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY
            {"revenue DESC" if sales_column else "region"}
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
        )

    return df


# ============================================================
# REGIONAL CONTRIBUTION
# ============================================================

def calculate_regional_contribution(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate each region's percentage contribution
    to total revenue.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            [
                "region",
                "revenue",
                "contribution_percentage",
            ]
        )

    columns = get_available_columns(engine)

    if "region" not in columns:
        return _empty_dataframe(
            [
                "region",
                "revenue",
                "contribution_percentage",
            ]
        )

    sales_column = _get_sales_column(columns)

    if sales_column is None:
        return _empty_dataframe(
            [
                "region",
                "revenue",
                "contribution_percentage",
            ]
        )

    query = text(
        f"""
        SELECT
            region,
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue
        FROM {TABLE_NAME}
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY revenue DESC
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
        )

    if df.empty:
        return _empty_dataframe(
            [
                "region",
                "revenue",
                "contribution_percentage",
            ]
        )

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    ).fillna(0)

    total_revenue = df["revenue"].sum()

    if total_revenue == 0:
        df["contribution_percentage"] = 0.0
    else:
        df["contribution_percentage"] = (
            df["revenue"]
            / total_revenue
            * 100
        )

    return df.reset_index(drop=True)


# ============================================================
# TOP REGIONS
# ============================================================

def get_top_regions(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return the highest-revenue regions.
    """

    regional_df = get_region_performance(
        engine
    )

    if regional_df.empty:
        return regional_df

    if "revenue" not in regional_df.columns:
        return regional_df.head(limit)

    return (
        regional_df
        .sort_values(
            "revenue",
            ascending=False,
        )
        .head(limit)
        .reset_index(drop=True)
    )


# ============================================================
# LOW-PERFORMING REGIONS
# ============================================================

def get_low_performing_regions(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return the lowest-revenue regions.
    """

    regional_df = get_region_performance(
        engine
    )

    if regional_df.empty:
        return regional_df

    if "revenue" not in regional_df.columns:
        return regional_df.head(limit)

    return (
        regional_df
        .sort_values(
            "revenue",
            ascending=True,
        )
        .head(limit)
        .reset_index(drop=True)
    )


# ============================================================
# COUNTRY PERFORMANCE
# ============================================================

def get_country_performance(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate revenue, orders, quantity and profit
    by country when country is available.
    """

    empty_columns = [
        "country",
        "revenue",
        "order_count",
        "quantity_sold",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if "country" not in columns:
        return _empty_dataframe(
            empty_columns
        )

    sales_column = _get_sales_column(columns)
    order_expression = _get_order_expression(columns)

    select_parts = [
        "country",
        f"{order_expression} AS order_count",
    ]

    if sales_column:
        select_parts.insert(
            1,
            f"""
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue
            """
        )

    if "quantity" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(
                    quantity,
                    0
                )
            ) AS quantity_sold
            """
        )

    if "profit" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(
                    profit,
                    0
                )
            ) AS profit
            """
        )

    query = text(
        f"""
        SELECT
            {",".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY
            {"revenue DESC" if sales_column else "country"}
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
        )

    return df


# ============================================================
# CITY PERFORMANCE
# ============================================================

def get_city_performance(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate revenue, orders and quantity by city
    when city is available.
    """

    empty_columns = [
        "city",
        "revenue",
        "order_count",
        "quantity_sold",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if "city" not in columns:
        return _empty_dataframe(
            empty_columns
        )

    sales_column = _get_sales_column(columns)
    order_expression = _get_order_expression(columns)

    select_parts = [
        "city",
        f"{order_expression} AS order_count",
    ]

    if sales_column:
        select_parts.insert(
            1,
            f"""
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue
            """
        )

    if "quantity" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(
                    quantity,
                    0
                )
            ) AS quantity_sold
            """
        )

    if "profit" in columns:
        select_parts.append(
            """
            SUM(
                COALESCE(
                    profit,
                    0
                )
            ) AS profit
            """
        )

    query = text(
        f"""
        SELECT
            {",".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY
            {"revenue DESC" if sales_column else "city"}
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
        )

    return df


# ============================================================
# COMPLETE REGIONAL ANALYTICS
# ============================================================

def run_regional_analytics(
    engine: Engine,
    limit: int = 10,
) -> dict[str, pd.DataFrame]:
    """
    Run the complete regional analytics suite.
    """

    return {
        "region_performance":
            get_region_performance(
                engine
            ),

        "regional_contribution":
            calculate_regional_contribution(
                engine
            ),

        "top_regions":
            get_top_regions(
                engine,
                limit,
            ),

        "low_performing_regions":
            get_low_performing_regions(
                engine,
                limit,
            ),

        "country_performance":
            get_country_performance(
                engine
            ),

        "city_performance":
            get_city_performance(
                engine
            ),
    }