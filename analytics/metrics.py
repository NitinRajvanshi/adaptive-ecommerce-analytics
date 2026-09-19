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
    Return available columns from the analytics table.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return set()

    return {
        column["name"]
        for column in inspector.get_columns(
            table_name
        )
    }


def execute_metric_query(
    engine: Engine,
    query: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Execute a single metric query.
    """

    if params is None:
        params = {}

    with engine.connect() as connection:

        result = connection.execute(
            text(query),
            params,
        )

        return result.scalar()


def _get_sales_column(
    columns: set[str],
) -> str | None:
    """
    Select the best available sales field.
    """

    if "net_sales" in columns:
        return "net_sales"

    if "sales_amount" in columns:
        return "sales_amount"

    if "order_value" in columns:
        return "order_value"

    return None


# ============================================================
# Core Revenue Metrics
# ============================================================

def calculate_total_revenue(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate total revenue using the best available sales field.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return None

    query = f"""
        SELECT
            COALESCE(SUM("{sales_column}"), 0)
        FROM "{table_name}"
    """

    value = execute_metric_query(
        engine,
        query,
    )

    return float(value or 0)


def calculate_total_orders(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> int | None:
    """
    Calculate total unique orders.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_id" in columns:

        query = f"""
            SELECT
                COUNT(DISTINCT "order_id")
            FROM "{table_name}"
            WHERE "order_id" IS NOT NULL
        """

    else:

        query = f"""
            SELECT COUNT(*)
            FROM "{table_name}"
        """

    value = execute_metric_query(
        engine,
        query,
    )

    return int(value or 0)


def calculate_total_quantity(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate total units sold.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "quantity" not in columns:
        return None

    query = f"""
        SELECT
            COALESCE(SUM("quantity"), 0)
        FROM "{table_name}"
    """

    value = execute_metric_query(
        engine,
        query,
    )

    return float(value or 0)


def calculate_average_order_value(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate average order value.

    If order_id exists, first aggregate transaction rows into
    orders so multi-line orders are not treated as separate orders.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return None

    if "order_id" in columns:

        query = f"""
            SELECT
                AVG(order_total)
            FROM (
                SELECT
                    "order_id",
                    SUM("{sales_column}") AS order_total
                FROM "{table_name}"
                WHERE "order_id" IS NOT NULL
                GROUP BY "order_id"
            )
        """

    else:

        query = f"""
            SELECT
                AVG("{sales_column}")
            FROM "{table_name}"
        """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# Customer Metrics
# ============================================================

def calculate_unique_customers(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> int | None:
    """
    Count unique customers when customer_id is available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "customer_id" not in columns:
        return None

    query = f"""
        SELECT
            COUNT(DISTINCT "customer_id")
        FROM "{table_name}"
        WHERE "customer_id" IS NOT NULL
    """

    value = execute_metric_query(
        engine,
        query,
    )

    return int(value or 0)


def calculate_repeat_customer_rate(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate the percentage of customers with more than one
    transaction/order.

    Returns a percentage between 0 and 100.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    required = {
        "customer_id",
    }

    if not required.issubset(columns):
        return None

    if "order_id" in columns:

        query = f"""
            SELECT
                AVG(
                    CASE
                        WHEN order_count > 1 THEN 1.0
                        ELSE 0.0
                    END
                ) * 100
            FROM (
                SELECT
                    "customer_id",
                    COUNT(DISTINCT "order_id")
                        AS order_count
                FROM "{table_name}"
                WHERE "customer_id" IS NOT NULL
                GROUP BY "customer_id"
            )
        """

    else:

        query = f"""
            SELECT
                AVG(
                    CASE
                        WHEN transaction_count > 1 THEN 1.0
                        ELSE 0.0
                    END
                ) * 100
            FROM (
                SELECT
                    "customer_id",
                    COUNT(*) AS transaction_count
                FROM "{table_name}"
                WHERE "customer_id" IS NOT NULL
                GROUP BY "customer_id"
            )
        """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# Product Metrics
# ============================================================

def calculate_unique_products(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> int | None:
    """
    Count unique products when product_id exists.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "product_id" not in columns:
        return None

    query = f"""
        SELECT
            COUNT(DISTINCT "product_id")
        FROM "{table_name}"
        WHERE "product_id" IS NOT NULL
    """

    value = execute_metric_query(
        engine,
        query,
    )

    return int(value or 0)


# ============================================================
# Profit Metrics
# ============================================================

def calculate_total_profit(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate total profit when profit is available.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "profit" not in columns:
        return None

    query = f"""
        SELECT
            COALESCE(SUM("profit"), 0)
        FROM "{table_name}"
    """

    value = execute_metric_query(
        engine,
        query,
    )

    return float(value or 0)


def calculate_profit_margin(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate overall profit margin.

    Formula:

        total profit / total net sales × 100
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "profit" not in columns:
        return None

    sales_column = _get_sales_column(
        columns
    )

    if sales_column is None:
        return None

    query = f"""
        SELECT
            CASE
                WHEN SUM("{sales_column}") = 0
                THEN NULL
                ELSE
                    SUM("profit")
                    / SUM("{sales_column}")
                    * 100
            END
        FROM "{table_name}"
    """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# Pricing Metrics
# ============================================================

def calculate_average_selling_price(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate average unit price.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "unit_price" not in columns:
        return None

    query = f"""
        SELECT
            AVG("unit_price")
        FROM "{table_name}"
        WHERE "unit_price" IS NOT NULL
    """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# Return Metrics
# ============================================================

def calculate_return_rate(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate return rate when return_status exists.

    Recognized returned values:
        returned
        return
        refunded
        refund

    Returns percentage from 0 to 100.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "return_status" not in columns:
        return None

    if "order_id" in columns:

        query = f"""
            SELECT
                CASE
                    WHEN COUNT(DISTINCT "order_id") = 0
                    THEN NULL
                    ELSE
                        SUM(
                            CASE
                                WHEN LOWER(
                                    TRIM("return_status")
                                ) IN (
                                    'returned',
                                    'return',
                                    'refunded',
                                    'refund'
                                )
                                THEN 1
                                ELSE 0
                            END
                        ) * 100.0
                        / COUNT(DISTINCT "order_id")
                END
            FROM "{table_name}"
        """

    else:

        query = f"""
            SELECT
                CASE
                    WHEN COUNT(*) = 0
                    THEN NULL
                    ELSE
                        SUM(
                            CASE
                                WHEN LOWER(
                                    TRIM("return_status")
                                ) IN (
                                    'returned',
                                    'return',
                                    'refunded',
                                    'refund'
                                )
                                THEN 1
                                ELSE 0
                            END
                        ) * 100.0
                        / COUNT(*)
                END
            FROM "{table_name}"
        """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# Data Quality Metrics
# ============================================================

def calculate_missing_value_rate(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> float | None:
    """
    Calculate percentage of missing cells in the database table.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if not columns:
        return None

    column_expressions = [
        f"""
        SUM(
            CASE
                WHEN "{column}" IS NULL
                THEN 1
                ELSE 0
            END
        )
        """
        for column in columns
    ]

    total_missing_expression = " + ".join(
        column_expressions
    )

    total_cell_expression = (
        f"COUNT(*) * {len(columns)}"
    )

    query = f"""
        SELECT
            CASE
                WHEN {total_cell_expression} = 0
                THEN NULL
                ELSE
                    (
                        {total_missing_expression}
                    ) * 100.0
                    / {total_cell_expression}
            END
        FROM "{table_name}"
    """

    value = execute_metric_query(
        engine,
        query,
    )

    if value is None:
        return None

    return float(value)


# ============================================================
# KPI Collection
# ============================================================

def calculate_all_metrics(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> dict[str, Any]:
    """
    Calculate all available KPIs.

    Metrics unavailable for a particular dataset are returned
    as None rather than causing an exception.
    """

    if not get_available_columns(
        engine,
        table_name,
    ):
        return {}

    metrics = {
        "total_revenue": calculate_total_revenue(
            engine,
            table_name,
        ),
        "total_orders": calculate_total_orders(
            engine,
            table_name,
        ),
        "total_quantity": calculate_total_quantity(
            engine,
            table_name,
        ),
        "average_order_value":
            calculate_average_order_value(
                engine,
                table_name,
            ),
        "unique_customers":
            calculate_unique_customers(
                engine,
                table_name,
            ),
        "repeat_customer_rate":
            calculate_repeat_customer_rate(
                engine,
                table_name,
            ),
        "unique_products":
            calculate_unique_products(
                engine,
                table_name,
            ),
        "total_profit":
            calculate_total_profit(
                engine,
                table_name,
            ),
        "profit_margin":
            calculate_profit_margin(
                engine,
                table_name,
            ),
        "average_selling_price":
            calculate_average_selling_price(
                engine,
                table_name,
            ),
        "return_rate":
            calculate_return_rate(
                engine,
                table_name,
            ),
        "missing_value_rate":
            calculate_missing_value_rate(
                engine,
                table_name,
            ),
    }

    return metrics


def metrics_to_dataframe(
    metrics: dict[str, Any],
) -> pd.DataFrame:
    """
    Convert metrics dictionary into a display-friendly dataframe.
    """

    records = []

    for name, value in metrics.items():

        records.append(
            {
                "metric": name,
                "value": value,
            }
        )

    return pd.DataFrame(records)