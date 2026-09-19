from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


def get_available_columns(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> set[str]:
    """
    Return the columns currently available in the database table.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return set()

    columns = inspector.get_columns(
        table_name
    )

    return {
        column["name"]
        for column in columns
    }


def table_exists(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> bool:
    """
    Check whether the analytics table exists.
    """

    inspector = inspect(engine)

    return table_name in inspector.get_table_names()


def execute_query(
    engine: Engine,
    query: str,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Execute a SQL query and return a dataframe.

    Queries in this project are internally generated from
    predefined SQL templates.
    """

    if params is None:
        params = {}

    with engine.connect() as connection:

        return pd.read_sql_query(
            text(query),
            connection,
            params=params,
        )


# ============================================================
# Core Metrics
# ============================================================

def query_total_sales(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate total net sales.

    Falls back to sales_amount when net_sales isn't available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            SUM("{value_column}") AS total_sales
        FROM "{table_name}"
    """

    return execute_query(
        engine,
        query,
    )


def query_total_orders(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Count orders.

    Uses DISTINCT order_id when available.
    Otherwise falls back to row count.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_id" in columns:

        expression = (
            'COUNT(DISTINCT "order_id")'
        )

    else:

        expression = "COUNT(*)"

    query = f"""
        SELECT
            {expression} AS total_orders
        FROM "{table_name}"
    """

    return execute_query(
        engine,
        query,
    )


def query_total_quantity(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate total quantity sold.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "quantity" not in columns:
        return pd.DataFrame()

    query = f"""
        SELECT
            SUM("quantity") AS total_quantity
        FROM "{table_name}"
    """

    return execute_query(
        engine,
        query,
    )


def query_average_order_value(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate average order value.

    Uses order_value when available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_value" in columns:

        value_column = "order_value"

    elif "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    if "order_id" in columns:

        query = f"""
            SELECT
                AVG(order_total) AS average_order_value
            FROM (
                SELECT
                    "order_id",
                    SUM("{value_column}") AS order_total
                FROM "{table_name}"
                GROUP BY "order_id"
            )
        """

    else:

        query = f"""
            SELECT
                AVG("{value_column}")
                AS average_order_value
            FROM "{table_name}"
        """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Time Analytics
# ============================================================

def query_monthly_sales(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate monthly sales.

    Uses generated order_year and order_month fields when
    available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_year" not in columns:
        return pd.DataFrame()

    if "order_month" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "order_year" AS year,
            "order_month" AS month,
            SUM("{value_column}") AS total_sales
        FROM "{table_name}"
        GROUP BY
            "order_year",
            "order_month"
        ORDER BY
            "order_year",
            "order_month"
    """

    return execute_query(
        engine,
        query,
    )


def query_daily_sales(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate sales by date.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_date_only" in columns:

        date_column = "order_date_only"

    elif "order_date" in columns:

        date_column = "order_date"

    else:

        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "{date_column}" AS order_date,
            SUM("{value_column}") AS total_sales
        FROM "{table_name}"
        GROUP BY "{date_column}"
        ORDER BY "{date_column}"
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Category Analytics
# ============================================================

def query_sales_by_category(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate sales by product category.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "category" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "category",
            SUM("{value_column}") AS total_sales,
            COUNT(*) AS transaction_count
        FROM "{table_name}"
        GROUP BY "category"
        ORDER BY total_sales DESC
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Region Analytics
# ============================================================

def query_sales_by_region(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate sales by region.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "region" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "region",
            SUM("{value_column}") AS total_sales,
            COUNT(*) AS transaction_count
        FROM "{table_name}"
        GROUP BY "region"
        ORDER BY total_sales DESC
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Product Analytics
# ============================================================

def query_top_products(
    engine: Engine,
    table_name: str = TABLE_NAME,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return top products by sales.

    Product ID is preferred. Product name is included when
    available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "product_id" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    if "product_name" in columns:

        product_name_expression = (
            '"product_name"'
        )

    else:

        product_name_expression = (
            "NULL"
        )

    query = f"""
        SELECT
            "product_id",
            {product_name_expression}
                AS product_name,
            SUM("{value_column}")
                AS total_sales,
            COUNT(*) AS transaction_count
        FROM "{table_name}"
        GROUP BY
            "product_id",
            {product_name_expression}
        ORDER BY total_sales DESC
        LIMIT :limit_value
    """

    return execute_query(
        engine,
        query,
        {
            "limit_value": int(limit),
        },
    )


# ============================================================
# Customer Analytics
# ============================================================

def query_top_customers(
    engine: Engine,
    table_name: str = TABLE_NAME,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return customers ranked by total spend.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "customer_id" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "customer_id",
            SUM("{value_column}")
                AS total_spend,
            COUNT(*) AS transaction_count
        FROM "{table_name}"
        WHERE "customer_id" IS NOT NULL
        GROUP BY "customer_id"
        ORDER BY total_spend DESC
        LIMIT :limit_value
    """

    return execute_query(
        engine,
        query,
        {
            "limit_value": int(limit),
        },
    )


# ============================================================
# Payment Analytics
# ============================================================

def query_sales_by_payment_method(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate sales by payment method.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "payment_method" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "payment_method",
            SUM("{value_column}")
                AS total_sales,
            COUNT(*) AS transaction_count
        FROM "{table_name}"
        GROUP BY "payment_method"
        ORDER BY total_sales DESC
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Order Status Analytics
# ============================================================

def query_sales_by_order_status(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate transaction and sales distribution by order status.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_status" not in columns:
        return pd.DataFrame()

    if "net_sales" in columns:

        value_column = "net_sales"

    elif "sales_amount" in columns:

        value_column = "sales_amount"

    else:

        return pd.DataFrame()

    query = f"""
        SELECT
            "order_status",
            COUNT(*) AS transaction_count,
            SUM("{value_column}")
                AS total_sales
        FROM "{table_name}"
        GROUP BY "order_status"
        ORDER BY transaction_count DESC
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Profit Analytics
# ============================================================

def query_profit_summary(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Calculate total profit and average profit margin when
    those fields are available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "profit" not in columns:
        return pd.DataFrame()

    margin_expression = (
        'AVG("profit_margin")'
        if "profit_margin" in columns
        else "NULL"
    )

    query = f"""
        SELECT
            SUM("profit") AS total_profit,
            {margin_expression}
                AS average_profit_margin
        FROM "{table_name}"
    """

    return execute_query(
        engine,
        query,
    )


# ============================================================
# Complete Analytics Collection
# ============================================================

def run_core_analytics(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> dict[str, pd.DataFrame]:
    """
    Execute all available core SQL analytics.

    Individual queries that are not applicable to a dataset
    return empty dataframes rather than raising errors.
    """

    if not table_exists(
        engine,
        table_name,
    ):
        return {}

    analytics = {
        "total_sales": query_total_sales(
            engine,
            table_name,
        ),
        "total_orders": query_total_orders(
            engine,
            table_name,
        ),
        "total_quantity": query_total_quantity(
            engine,
            table_name,
        ),
        "average_order_value": query_average_order_value(
            engine,
            table_name,
        ),
        "monthly_sales": query_monthly_sales(
            engine,
            table_name,
        ),
        "daily_sales": query_daily_sales(
            engine,
            table_name,
        ),
        "sales_by_category": query_sales_by_category(
            engine,
            table_name,
        ),
        "sales_by_region": query_sales_by_region(
            engine,
            table_name,
        ),
        "top_products": query_top_products(
            engine,
            table_name,
        ),
        "top_customers": query_top_customers(
            engine,
            table_name,
        ),
        "sales_by_payment_method":
            query_sales_by_payment_method(
                engine,
                table_name,
            ),
        "sales_by_order_status":
            query_sales_by_order_status(
                engine,
                table_name,
            ),
        "profit_summary": query_profit_summary(
            engine,
            table_name,
        ),
    }

    return analytics