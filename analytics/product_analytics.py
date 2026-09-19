from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


def get_available_columns(engine: Engine) -> set[str]:
    """
    Return the columns currently available in the transactions table.
    """
    try:
        query = text(f"PRAGMA table_info({TABLE_NAME})")

        with engine.connect() as connection:
            rows = connection.execute(query).fetchall()

        return {row[1] for row in rows}

    except Exception:
        return set()


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


def _get_sales_column(available_columns: set[str]) -> Optional[str]:
    """
    Select the best available sales column.
    """
    if "net_sales" in available_columns:
        return "net_sales"

    if "sales_amount" in available_columns:
        return "sales_amount"

    return None


def _empty_dataframe(columns: list[str]) -> pd.DataFrame:
    """
    Return an empty DataFrame with the requested columns.
    """
    return pd.DataFrame(columns=columns)


def get_top_products_by_revenue(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return products ranked by total revenue.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            ["product_id", "product_name", "revenue"]
        )

    columns = get_available_columns(engine)
    sales_column = _get_sales_column(columns)

    if not sales_column:
        return _empty_dataframe(
            ["product_id", "product_name", "revenue"]
        )

    product_column = (
        "product_id"
        if "product_id" in columns
        else None
    )

    name_column = (
        "product_name"
        if "product_name" in columns
        else None
    )

    if not product_column and not name_column:
        return _empty_dataframe(
            ["product_id", "product_name", "revenue"]
        )

    group_column = product_column or name_column

    select_parts = [
        f"{group_column} AS product_key"
    ]

    if product_column:
        select_parts.append(
            "product_id"
        )
    else:
        select_parts.append(
            "NULL AS product_id"
        )

    if name_column:
        select_parts.append(
            "MAX(product_name) AS product_name"
        )
    else:
        select_parts.append(
            "NULL AS product_name"
        )

    select_parts.append(
        f"SUM(COALESCE({sales_column}, 0)) AS revenue"
    )

    query = text(
        f"""
        SELECT
            {", ".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE {group_column} IS NOT NULL
        GROUP BY {group_column}
        ORDER BY revenue DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={"limit": int(limit)},
        )

    if not df.empty:
        df["revenue"] = pd.to_numeric(
            df["revenue"],
            errors="coerce",
        ).fillna(0)

    return df.drop(
        columns=["product_key"],
        errors="ignore",
    )


def get_top_products_by_quantity(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return products ranked by quantity sold.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            ["product_id", "product_name", "quantity_sold"]
        )

    columns = get_available_columns(engine)

    if "quantity" not in columns:
        return _empty_dataframe(
            ["product_id", "product_name", "quantity_sold"]
        )

    product_column = (
        "product_id"
        if "product_id" in columns
        else None
    )

    name_column = (
        "product_name"
        if "product_name" in columns
        else None
    )

    if not product_column and not name_column:
        return _empty_dataframe(
            ["product_id", "product_name", "quantity_sold"]
        )

    group_column = product_column or name_column

    select_parts = [
        f"{group_column} AS product_key"
    ]

    if product_column:
        select_parts.append("product_id")
    else:
        select_parts.append("NULL AS product_id")

    if name_column:
        select_parts.append(
            "MAX(product_name) AS product_name"
        )
    else:
        select_parts.append(
            "NULL AS product_name"
        )

    select_parts.append(
        "SUM(COALESCE(quantity, 0)) AS quantity_sold"
    )

    query = text(
        f"""
        SELECT
            {", ".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE {group_column} IS NOT NULL
        GROUP BY {group_column}
        ORDER BY quantity_sold DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={"limit": int(limit)},
        )

    if not df.empty:
        df["quantity_sold"] = pd.to_numeric(
            df["quantity_sold"],
            errors="coerce",
        ).fillna(0)

    return df.drop(
        columns=["product_key"],
        errors="ignore",
    )


def get_top_products_by_profit(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return products ranked by total profit.

    Profit analytics is only available when the dataset
    contains a profit column.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            ["product_id", "product_name", "profit"]
        )

    columns = get_available_columns(engine)

    if "profit" not in columns:
        return _empty_dataframe(
            ["product_id", "product_name", "profit"]
        )

    product_column = (
        "product_id"
        if "product_id" in columns
        else None
    )

    name_column = (
        "product_name"
        if "product_name" in columns
        else None
    )

    if not product_column and not name_column:
        return _empty_dataframe(
            ["product_id", "product_name", "profit"]
        )

    group_column = product_column or name_column

    select_parts = [
        f"{group_column} AS product_key"
    ]

    if product_column:
        select_parts.append("product_id")
    else:
        select_parts.append("NULL AS product_id")

    if name_column:
        select_parts.append(
            "MAX(product_name) AS product_name"
        )
    else:
        select_parts.append(
            "NULL AS product_name"
        )

    select_parts.append(
        "SUM(COALESCE(profit, 0)) AS profit"
    )

    query = text(
        f"""
        SELECT
            {", ".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE {group_column} IS NOT NULL
        GROUP BY {group_column}
        ORDER BY profit DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={"limit": int(limit)},
        )

    if not df.empty:
        df["profit"] = pd.to_numeric(
            df["profit"],
            errors="coerce",
        ).fillna(0)

    return df.drop(
        columns=["product_key"],
        errors="ignore",
    )


def get_category_performance(
    engine: Engine,
) -> pd.DataFrame:
    """
    Return category-level revenue, quantity and profit
    when those fields are available.
    """

    if not table_exists(engine):
        return _empty_dataframe(
            ["category", "revenue", "quantity_sold", "profit"]
        )

    columns = get_available_columns(engine)

    if "category" not in columns:
        return _empty_dataframe(
            ["category", "revenue", "quantity_sold", "profit"]
        )

    sales_column = _get_sales_column(columns)

    select_parts = ["category"]

    if sales_column:
        select_parts.append(
            f"SUM(COALESCE({sales_column}, 0)) AS revenue"
        )

    if "quantity" in columns:
        select_parts.append(
            "SUM(COALESCE(quantity, 0)) AS quantity_sold"
        )

    if "profit" in columns:
        select_parts.append(
            "SUM(COALESCE(profit, 0)) AS profit"
        )

    if len(select_parts) == 1:
        return _empty_dataframe(
            ["category"]
        )

    query = text(
        f"""
        SELECT
            {", ".join(select_parts)}
        FROM {TABLE_NAME}
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY
            {"revenue DESC" if sales_column else "category"}
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    return df


def calculate_product_contribution(
    engine: Engine,
) -> pd.DataFrame:
    """
    Calculate each product's percentage contribution
    to total revenue.
    """

    products = get_top_products_by_revenue(
        engine,
        limit=100000,
    )

    if products.empty or "revenue" not in products.columns:
        return _empty_dataframe(
            [
                "product_id",
                "product_name",
                "revenue",
                "contribution_percentage",
            ]
        )

    total_revenue = products["revenue"].sum()

    if total_revenue == 0:
        products["contribution_percentage"] = 0.0
    else:
        products["contribution_percentage"] = (
            products["revenue"]
            / total_revenue
            * 100
        )

    return products.sort_values(
        "contribution_percentage",
        ascending=False,
    ).reset_index(drop=True)


def get_low_performing_products(
    engine: Engine,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Return products with the lowest revenue.
    """

    products = calculate_product_contribution(engine)

    if products.empty:
        return products

    return (
        products
        .sort_values("revenue", ascending=True)
        .head(limit)
        .reset_index(drop=True)
    )


def run_product_analytics(
    engine: Engine,
    limit: int = 10,
) -> dict[str, pd.DataFrame]:
    """
    Run the complete product analytics suite.
    """

    return {
        "top_products_by_revenue": get_top_products_by_revenue(
            engine,
            limit,
        ),
        "top_products_by_quantity": get_top_products_by_quantity(
            engine,
            limit,
        ),
        "top_products_by_profit": get_top_products_by_profit(
            engine,
            limit,
        ),
        "category_performance": get_category_performance(
            engine,
        ),
        "product_contribution": calculate_product_contribution(
            engine,
        ),
        "low_performing_products": get_low_performing_products(
            engine,
            limit,
        ),
    }