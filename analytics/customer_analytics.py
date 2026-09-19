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
    """
    Check whether the transactions table exists.
    """

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
    """
    Return the columns available in the transactions table.
    """

    try:
        query = text(
            f"PRAGMA table_info({TABLE_NAME})"
        )

        with engine.connect() as connection:
            rows = connection.execute(query).fetchall()

        return {
            row[1]
            for row in rows
        }

    except Exception:
        return set()


def _get_sales_column(
    available_columns: set[str],
) -> Optional[str]:
    """
    Select the preferred revenue column.
    """

    if "net_sales" in available_columns:
        return "net_sales"

    if "sales_amount" in available_columns:
        return "sales_amount"

    return None


def _empty_dataframe(
    columns: list[str],
) -> pd.DataFrame:
    """
    Return an empty DataFrame with known columns.
    """

    return pd.DataFrame(
        columns=columns
    )


def _customer_available(
    available_columns: set[str],
) -> bool:
    """
    Check whether customer-level analysis is possible.
    """

    return "customer_id" in available_columns


# ============================================================
# CUSTOMER REVENUE
# ============================================================

def get_customer_revenue(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return customers ranked by total revenue.
    """

    empty_columns = [
        "customer_id",
        "revenue",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            empty_columns
        )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return _empty_dataframe(
            empty_columns
        )

    query = text(
        f"""
        SELECT
            customer_id,
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue
        FROM {TABLE_NAME}
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
        ORDER BY revenue DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={
                "limit": int(limit)
            },
        )

    if not df.empty:
        df["revenue"] = pd.to_numeric(
            df["revenue"],
            errors="coerce",
        ).fillna(0)

    return df


# ============================================================
# CUSTOMER ORDER FREQUENCY
# ============================================================

def get_customer_order_frequency(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return customers ranked by number of orders.
    """

    empty_columns = [
        "customer_id",
        "order_count",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            empty_columns
        )

    if "order_id" in columns:

        order_expression = (
            "COUNT(DISTINCT order_id)"
        )

    else:

        order_expression = "COUNT(*)"

    query = text(
        f"""
        SELECT
            customer_id,
            {order_expression} AS order_count
        FROM {TABLE_NAME}
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
        ORDER BY order_count DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={
                "limit": int(limit)
            },
        )

    if not df.empty:
        df["order_count"] = pd.to_numeric(
            df["order_count"],
            errors="coerce",
        ).fillna(0).astype(int)

    return df


# ============================================================
# CUSTOMER AVERAGE ORDER VALUE
# ============================================================

def get_customer_average_order_value(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return average order value for each customer.
    """

    empty_columns = [
        "customer_id",
        "revenue",
        "order_count",
        "average_order_value",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            empty_columns
        )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return _empty_dataframe(
            empty_columns
        )

    if "order_id" in columns:

        order_expression = (
            "COUNT(DISTINCT order_id)"
        )

    else:

        order_expression = "COUNT(*)"

    query = text(
        f"""
        SELECT
            customer_id,
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue,
            {order_expression} AS order_count,
            CASE
                WHEN {order_expression} = 0
                THEN 0
                ELSE
                    SUM(
                        COALESCE(
                            {sales_column},
                            0
                        )
                    )
                    /
                    {order_expression}
            END AS average_order_value
        FROM {TABLE_NAME}
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
        ORDER BY average_order_value DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={
                "limit": int(limit)
            },
        )

    if not df.empty:
        for column in [
            "revenue",
            "average_order_value",
        ]:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            ).fillna(0)

        df["order_count"] = pd.to_numeric(
            df["order_count"],
            errors="coerce",
        ).fillna(0).astype(int)

    return df


# ============================================================
# TOP CUSTOMERS
# ============================================================

def get_top_customers(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return a combined customer performance table.
    """

    empty_columns = [
        "customer_id",
        "revenue",
        "order_count",
        "average_order_value",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            empty_columns
        )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return _empty_dataframe(
            empty_columns
        )

    if "order_id" in columns:
        order_expression = (
            "COUNT(DISTINCT order_id)"
        )
    else:
        order_expression = "COUNT(*)"

    query = text(
        f"""
        SELECT
            customer_id,

            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue,

            {order_expression} AS order_count,

            CASE
                WHEN {order_expression} = 0
                THEN 0
                ELSE
                    SUM(
                        COALESCE(
                            {sales_column},
                            0
                        )
                    )
                    /
                    {order_expression}
            END AS average_order_value

        FROM {TABLE_NAME}

        WHERE customer_id IS NOT NULL

        GROUP BY customer_id

        ORDER BY revenue DESC

        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={
                "limit": int(limit)
            },
        )

    if not df.empty:

        df["revenue"] = pd.to_numeric(
            df["revenue"],
            errors="coerce",
        ).fillna(0)

        df["order_count"] = pd.to_numeric(
            df["order_count"],
            errors="coerce",
        ).fillna(0).astype(int)

        df["average_order_value"] = pd.to_numeric(
            df["average_order_value"],
            errors="coerce",
        ).fillna(0)

    return df


# ============================================================
# REPEAT CUSTOMER ANALYSIS
# ============================================================

def get_repeat_customer_analysis(
    engine: Engine,
) -> pd.DataFrame:
    """
    Classify customers into one-time and repeat customers.
    """

    empty_columns = [
        "customer_type",
        "customer_count",
        "percentage",
    ]

    if not table_exists(engine):
        return _empty_dataframe(
            empty_columns
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            empty_columns
        )

    if "order_id" in columns:

        order_expression = (
            "COUNT(DISTINCT order_id)"
        )

    else:

        order_expression = "COUNT(*)"

    query = text(
        f"""
        WITH customer_orders AS (
            SELECT
                customer_id,
                {order_expression} AS order_count
            FROM {TABLE_NAME}
            WHERE customer_id IS NOT NULL
            GROUP BY customer_id
        ),

        classified_customers AS (
            SELECT
                CASE
                    WHEN order_count > 1
                    THEN 'Repeat Customer'
                    ELSE 'One-Time Customer'
                END AS customer_type
            FROM customer_orders
        ),

        totals AS (
            SELECT
                COUNT(*) AS total_customers
            FROM classified_customers
        )

        SELECT
            customer_type,
            COUNT(*) AS customer_count,
            ROUND(
                COUNT(*) * 100.0
                /
                NULLIF(
                    (SELECT total_customers FROM totals),
                    0
                ),
                2
            ) AS percentage

        FROM classified_customers

        GROUP BY customer_type

        ORDER BY customer_count DESC
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
        )

    if not df.empty:
        df["customer_count"] = pd.to_numeric(
            df["customer_count"],
            errors="coerce",
        ).fillna(0).astype(int)

        df["percentage"] = pd.to_numeric(
            df["percentage"],
            errors="coerce",
        ).fillna(0)

    return df


# ============================================================
# CUSTOMER CONTRIBUTION
# ============================================================

def calculate_customer_contribution(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate each customer's contribution to total revenue.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            [
                "customer_id",
                "revenue",
                "contribution_percentage",
            ]
        )

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return _empty_dataframe(
            [
                "customer_id",
                "revenue",
                "contribution_percentage",
            ]
        )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return _empty_dataframe(
            [
                "customer_id",
                "revenue",
                "contribution_percentage",
            ]
        )

    query = text(
        f"""
        SELECT
            customer_id,
            SUM(
                COALESCE(
                    {sales_column},
                    0
                )
            ) AS revenue
        FROM {TABLE_NAME}
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
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
                "customer_id",
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

    return df.reset_index(
        drop=True
    )


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def get_customer_summary(
    engine: Engine,
) -> dict:
    """
    Return high-level customer statistics.
    """

    if not table_exists(engine):
        return {
            "customer_available": False,
            "total_customers": None,
            "repeat_customers": None,
            "one_time_customers": None,
            "repeat_customer_rate": None,
        }

    columns = get_available_columns(engine)

    if not _customer_available(columns):
        return {
            "customer_available": False,
            "total_customers": None,
            "repeat_customers": None,
            "one_time_customers": None,
            "repeat_customer_rate": None,
        }

    if "order_id" in columns:
        order_expression = (
            "COUNT(DISTINCT order_id)"
        )
    else:
        order_expression = "COUNT(*)"

    query = text(
        f"""
        WITH customer_orders AS (
            SELECT
                customer_id,
                {order_expression} AS order_count
            FROM {TABLE_NAME}
            WHERE customer_id IS NOT NULL
            GROUP BY customer_id
        )

        SELECT

            COUNT(*) AS total_customers,

            SUM(
                CASE
                    WHEN order_count > 1
                    THEN 1
                    ELSE 0
                END
            ) AS repeat_customers,

            SUM(
                CASE
                    WHEN order_count = 1
                    THEN 1
                    ELSE 0
                END
            ) AS one_time_customers

        FROM customer_orders
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query
        ).fetchone()

    if row is None:
        return {
            "customer_available": True,
            "total_customers": 0,
            "repeat_customers": 0,
            "one_time_customers": 0,
            "repeat_customer_rate": 0.0,
        }

    total_customers = int(
        row[0] or 0
    )

    repeat_customers = int(
        row[1] or 0
    )

    one_time_customers = int(
        row[2] or 0
    )

    repeat_rate = (
        repeat_customers
        / total_customers
        * 100
        if total_customers
        else 0.0
    )

    return {
        "customer_available": True,
        "total_customers": total_customers,
        "repeat_customers": repeat_customers,
        "one_time_customers": one_time_customers,
        "repeat_customer_rate": repeat_rate,
    }


# ============================================================
# COMPLETE CUSTOMER ANALYTICS
# ============================================================

def run_customer_analytics(
    engine: Engine,
    limit: int = 10,
) -> dict[str, pd.DataFrame | dict]:
    """
    Run the complete customer analytics suite.
    """

    return {
        "customer_revenue": get_customer_revenue(
            engine,
            limit,
        ),
        "customer_order_frequency":
            get_customer_order_frequency(
                engine,
                limit,
            ),
        "customer_average_order_value":
            get_customer_average_order_value(
                engine,
                limit,
            ),
        "top_customers": get_top_customers(
            engine,
            limit,
        ),
        "repeat_customer_analysis":
            get_repeat_customer_analysis(
                engine
            ),
        "customer_contribution":
            calculate_customer_contribution(
                engine
            ),
        "customer_summary":
            get_customer_summary(
                engine
            ),
    }