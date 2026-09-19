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
    """Check whether the transactions table exists."""

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
    """Return available database columns."""

    if not table_exists(engine, table_name):
        return []

    query = f'PRAGMA table_info("{table_name}")'

    with engine.connect() as connection:
        rows = connection.execute(
            text(query)
        ).fetchall()

    return [row[1] for row in rows]


def execute_query(
    engine: Engine,
    query: str,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Execute a SQL query and return a DataFrame."""

    with engine.connect() as connection:
        return pd.read_sql_query(
            text(query),
            connection,
            params=params or {},
        )


def _empty_insights() -> pd.DataFrame:
    """Return a standardized empty insight table."""

    return pd.DataFrame(
        columns=[
            "insight_type",
            "priority",
            "title",
            "finding",
            "recommendation",
            "metric",
            "value",
        ]
    )


# ============================================================
# GENERIC INSIGHT BUILDER
# ============================================================

def _create_insight(
    insight_type: str,
    priority: str,
    title: str,
    finding: str,
    recommendation: str,
    metric: str = "",
    value: Any = None,
) -> dict[str, Any]:
    """Create one standardized insight record."""

    return {
        "insight_type": insight_type,
        "priority": priority,
        "title": title,
        "finding": finding,
        "recommendation": recommendation,
        "metric": metric,
        "value": value,
    }


# ============================================================
# REVENUE INSIGHTS
# ============================================================

def generate_revenue_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate insights from overall revenue performance."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    sales_column = None

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"

    if sales_column is None:
        return []

    query = f"""
        SELECT
            SUM({sales_column}) AS total_revenue,
            AVG({sales_column}) AS average_transaction_value
        FROM "{table_name}"
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    total_revenue = float(
        df.iloc[0]["total_revenue"] or 0
    )

    average_value = float(
        df.iloc[0]["average_transaction_value"] or 0
    )

    insights = []

    if total_revenue > 0:
        insights.append(
            _create_insight(
                insight_type="Revenue",
                priority="Medium",
                title="Revenue baseline established",
                finding=(
                    f"The dataset generated total revenue "
                    f"of {total_revenue:,.2f}."
                ),
                recommendation=(
                    "Use this revenue baseline to evaluate "
                    "future sales trends and business growth."
                ),
                metric="Total Revenue",
                value=total_revenue,
            )
        )

    if average_value > 0:
        insights.append(
            _create_insight(
                insight_type="Revenue",
                priority="Low",
                title="Average transaction value identified",
                finding=(
                    f"The average transaction value is "
                    f"{average_value:,.2f}."
                ),
                recommendation=(
                    "Track average transaction value over time "
                    "to identify changes in customer spending."
                ),
                metric="Average Transaction Value",
                value=average_value,
            )
        )

    return insights


# ============================================================
# MONTHLY TREND INSIGHTS
# ============================================================

def generate_trend_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Analyze monthly revenue movement."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "order_date" not in columns:
        return []

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"
    else:
        return []

    query = f"""
        SELECT
            strftime('%Y-%m', order_date) AS month,
            SUM({sales_column}) AS revenue
        FROM "{table_name}"
        WHERE order_date IS NOT NULL
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month
    """

    df = execute_query(
        engine,
        query,
    )

    if len(df) < 2:
        return []

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["revenue"]
    )

    if len(df) < 2:
        return []

    previous_revenue = float(
        df.iloc[-2]["revenue"]
    )

    latest_revenue = float(
        df.iloc[-1]["revenue"]
    )

    if previous_revenue == 0:
        return []

    percentage_change = (
        (latest_revenue - previous_revenue)
        / abs(previous_revenue)
        * 100
    )

    latest_month = df.iloc[-1]["month"]

    if percentage_change > 10:
        priority = "High"
        title = "Revenue increased significantly"
        recommendation = (
            "Investigate the products, customers and regions "
            "driving the recent increase and assess whether "
            "the pattern can be sustained."
        )

    elif percentage_change < -10:
        priority = "High"
        title = "Revenue declined significantly"
        recommendation = (
            "Investigate recent product, customer and regional "
            "performance to identify potential causes of the decline."
        )

    else:
        priority = "Low"
        title = "Revenue remained relatively stable"
        recommendation = (
            "Continue monitoring monthly revenue for emerging "
            "growth or decline patterns."
        )

    return [
        _create_insight(
            insight_type="Trend",
            priority=priority,
            title=title,
            finding=(
                f"Revenue for {latest_month} was "
                f"{latest_revenue:,.2f}, representing a "
                f"{percentage_change:.1f}% change from the "
                f"previous month."
            ),
            recommendation=recommendation,
            metric="Month-over-Month Revenue Change",
            value=percentage_change,
        )
    ]


# ============================================================
# PRODUCT INSIGHTS
# ============================================================

def generate_product_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate insights from product performance."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    product_column = None

    if "product_name" in columns:
        product_column = "product_name"
    elif "product_id" in columns:
        product_column = "product_id"

    if product_column is None:
        return []

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"
    else:
        return []

    query = f"""
        SELECT
            {product_column} AS product,
            SUM({sales_column}) AS revenue
        FROM "{table_name}"
        WHERE {product_column} IS NOT NULL
        GROUP BY {product_column}
        ORDER BY revenue DESC
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["revenue"]
    )

    if df.empty:
        return []

    insights = []

    top_product = df.iloc[0]

    insights.append(
        _create_insight(
            insight_type="Product",
            priority="Medium",
            title="Top revenue-generating product identified",
            finding=(
                f"{top_product['product']} generated "
                f"{float(top_product['revenue']):,.2f} "
                f"in revenue."
            ),
            recommendation=(
                "Monitor this product's availability and "
                "performance because it represents an important "
                "source of revenue."
            ),
            metric="Top Product Revenue",
            value=float(top_product["revenue"]),
        )
    )

    if len(df) >= 3:
        bottom_product = df.iloc[-1]

        insights.append(
            _create_insight(
                insight_type="Product",
                priority="Medium",
                title="Lowest revenue-generating product identified",
                finding=(
                    f"{bottom_product['product']} generated "
                    f"{float(bottom_product['revenue']):,.2f} "
                    f"in revenue."
                ),
                recommendation=(
                    "Review demand, pricing, availability and "
                    "marketing performance for this product."
                ),
                metric="Lowest Product Revenue",
                value=float(bottom_product["revenue"]),
            )
        )

    return insights


# ============================================================
# CATEGORY INSIGHTS
# ============================================================

def generate_category_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate category-level business insights."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "category" not in columns:
        return []

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"
    else:
        return []

    query = f"""
        SELECT
            category,
            SUM({sales_column}) AS revenue
        FROM "{table_name}"
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY revenue DESC
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["revenue"]
    )

    if df.empty:
        return []

    total_revenue = df["revenue"].sum()

    if total_revenue == 0:
        return []

    top_category = df.iloc[0]

    contribution = (
        float(top_category["revenue"])
        / float(total_revenue)
        * 100
    )

    return [
        _create_insight(
            insight_type="Category",
            priority="Medium",
            title="Highest-contributing category identified",
            finding=(
                f"{top_category['category']} generated "
                f"{float(top_category['revenue']):,.2f}, "
                f"representing {contribution:.1f}% of "
                f"category revenue."
            ),
            recommendation=(
                "Monitor this category's performance and "
                "evaluate opportunities to maintain or expand "
                "its contribution."
            ),
            metric="Top Category Revenue Contribution",
            value=contribution,
        )
    ]


# ============================================================
# REGIONAL INSIGHTS
# ============================================================

def generate_regional_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate geographic business insights."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "region" not in columns:
        return []

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"
    else:
        return []

    query = f"""
        SELECT
            region,
            SUM({sales_column}) AS revenue
        FROM "{table_name}"
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY revenue DESC
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["revenue"]
    )

    if df.empty:
        return []

    total_revenue = df["revenue"].sum()

    if total_revenue == 0:
        return []

    top_region = df.iloc[0]

    contribution = (
        float(top_region["revenue"])
        / float(total_revenue)
        * 100
    )

    insights = [
        _create_insight(
            insight_type="Regional",
            priority="Medium",
            title="Highest-contributing region identified",
            finding=(
                f"{top_region['region']} generated "
                f"{float(top_region['revenue']):,.2f}, "
                f"representing {contribution:.1f}% of "
                f"regional revenue."
            ),
            recommendation=(
                "Evaluate what products and customer segments "
                "are driving this regional performance."
            ),
            metric="Top Region Revenue Contribution",
            value=contribution,
        )
    ]

    if len(df) >= 3:
        lowest_region = df.iloc[-1]

        insights.append(
            _create_insight(
                insight_type="Regional",
                priority="Low",
                title="Lowest-contributing region identified",
                finding=(
                    f"{lowest_region['region']} generated "
                    f"{float(lowest_region['revenue']):,.2f} "
                    f"in revenue."
                ),
                recommendation=(
                    "Review product demand, customer activity "
                    "and sales coverage in this region."
                ),
                metric="Lowest Region Revenue",
                value=float(lowest_region["revenue"]),
            )
        )

    return insights


# ============================================================
# CUSTOMER INSIGHTS
# ============================================================

def generate_customer_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate customer-level business insights."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "customer_id" not in columns:
        return []

    if "net_sales" in columns:
        sales_column = "net_sales"
    elif "sales_amount" in columns:
        sales_column = "sales_amount"
    else:
        return []

    query = f"""
        SELECT
            customer_id,
            SUM({sales_column}) AS revenue,
            COUNT(DISTINCT order_id) AS order_count
        FROM "{table_name}"
        WHERE customer_id IS NOT NULL
        GROUP BY customer_id
        ORDER BY revenue DESC
    """

    if "order_id" not in columns:
        query = f"""
            SELECT
                customer_id,
                SUM({sales_column}) AS revenue,
                COUNT(*) AS order_count
            FROM "{table_name}"
            WHERE customer_id IS NOT NULL
            GROUP BY customer_id
            ORDER BY revenue DESC
        """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce",
    )

    df["order_count"] = pd.to_numeric(
        df["order_count"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["revenue"]
    )

    if df.empty:
        return []

    insights = []

    top_customer = df.iloc[0]

    insights.append(
        _create_insight(
            insight_type="Customer",
            priority="Medium",
            title="Highest-value customer identified",
            finding=(
                f"Customer {top_customer['customer_id']} "
                f"generated {float(top_customer['revenue']):,.2f} "
                f"across {int(top_customer['order_count'])} "
                f"orders."
            ),
            recommendation=(
                "Monitor high-value customers and evaluate "
                "retention strategies for important accounts."
            ),
            metric="Top Customer Revenue",
            value=float(top_customer["revenue"]),
        )
    )

    repeat_customers = df[
        df["order_count"] > 1
    ]

    repeat_rate = (
        len(repeat_customers)
        / len(df)
        * 100
        if len(df) > 0
        else 0
    )

    insights.append(
        _create_insight(
            insight_type="Customer",
            priority="Medium",
            title="Repeat customer activity identified",
            finding=(
                f"{repeat_rate:.1f}% of identifiable customers "
                f"placed more than one order."
            ),
            recommendation=(
                "Use repeat-purchase behavior to evaluate "
                "customer retention and loyalty opportunities."
            ),
            metric="Repeat Customer Rate",
            value=repeat_rate,
        )
    )

    return insights


# ============================================================
# PROFITABILITY INSIGHTS
# ============================================================

def generate_profit_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate profitability insights when profit data exists."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "profit" not in columns:
        return []

    query = f"""
        SELECT
            SUM(profit) AS total_profit,
            AVG(profit) AS average_profit
        FROM "{table_name}"
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    total_profit = float(
        df.iloc[0]["total_profit"] or 0
    )

    average_profit = float(
        df.iloc[0]["average_profit"] or 0
    )

    insights = []

    if total_profit < 0:
        insights.append(
            _create_insight(
                insight_type="Profitability",
                priority="High",
                title="Overall profitability is negative",
                finding=(
                    f"Total recorded profit is "
                    f"{total_profit:,.2f}."
                ),
                recommendation=(
                    "Review pricing, costs, discounts and "
                    "product-level profitability to identify "
                    "the main sources of negative profit."
                ),
                metric="Total Profit",
                value=total_profit,
            )
        )

    else:
        insights.append(
            _create_insight(
                insight_type="Profitability",
                priority="Medium",
                title="Positive profitability identified",
                finding=(
                    f"Total recorded profit is "
                    f"{total_profit:,.2f}."
                ),
                recommendation=(
                    "Identify products and customer segments "
                    "that contribute most to profit."
                ),
                metric="Total Profit",
                value=total_profit,
            )
        )

    insights.append(
        _create_insight(
            insight_type="Profitability",
            priority="Low",
            title="Average transaction profit identified",
            finding=(
                f"Average recorded profit per transaction "
                f"is {average_profit:,.2f}."
            ),
            recommendation=(
                "Track this metric alongside revenue to "
                "understand whether sales growth is translating "
                "into profitability."
            ),
            metric="Average Profit",
            value=average_profit,
        )
    )

    return insights


# ============================================================
# RETURN INSIGHTS
# ============================================================

def generate_return_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """Generate return-related insights when return data exists."""

    columns = get_available_columns(
        engine,
        table_name,
    )

    if "return_status" not in columns:
        return []

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            SUM(
                CASE
                    WHEN LOWER(CAST(return_status AS TEXT))
                    IN ('returned', 'return', 'yes', 'true')
                    THEN 1
                    ELSE 0
                END
            ) AS returned_rows
        FROM "{table_name}"
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    total_rows = int(
        df.iloc[0]["total_rows"] or 0
    )

    returned_rows = int(
        df.iloc[0]["returned_rows"] or 0
    )

    if total_rows == 0:
        return []

    return_rate = (
        returned_rows
        / total_rows
        * 100
    )

    if return_rate > 10:
        priority = "High"
    elif return_rate > 5:
        priority = "Medium"
    else:
        priority = "Low"

    return [
        _create_insight(
            insight_type="Returns",
            priority=priority,
            title="Return activity identified",
            finding=(
                f"{return_rate:.1f}% of recorded transactions "
                f"are marked as returned."
            ),
            recommendation=(
                "Investigate return reasons, products and "
                "customer patterns to identify opportunities "
                "for reducing avoidable returns."
            ),
            metric="Return Rate",
            value=return_rate,
        )
    ]


# ============================================================
# DATA QUALITY INSIGHTS
# ============================================================

def generate_data_quality_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict[str, Any]]:
    """
    Generate a basic data-quality insight from database contents.
    """

    columns = get_available_columns(
        engine,
        table_name,
    )

    if not columns:
        return []

    conditions = []

    for column in columns:
        conditions.append(
            f"""
            CASE
                WHEN "{column}" IS NULL
                THEN 1
                ELSE 0
            END
            """
        )

    null_expression = " + ".join(
        conditions
    )

    query = f"""
        SELECT
            COUNT(*) AS total_rows,
            SUM({null_expression}) AS null_cells
        FROM "{table_name}"
    """

    df = execute_query(
        engine,
        query,
    )

    if df.empty:
        return []

    total_rows = int(
        df.iloc[0]["total_rows"] or 0
    )

    null_cells = int(
        df.iloc[0]["null_cells"] or 0
    )

    if total_rows == 0:
        return []

    total_cells = total_rows * len(columns)

    missing_rate = (
        null_cells
        / total_cells
        * 100
    )

    if missing_rate == 0:
        priority = "Low"
        title = "No missing values detected"
    elif missing_rate <= 5:
        priority = "Low"
        title = "Low level of missing data detected"
    elif missing_rate <= 15:
        priority = "Medium"
        title = "Moderate missing data detected"
    else:
        priority = "High"
        title = "High missing-data rate detected"

    return [
        _create_insight(
            insight_type="Data Quality",
            priority=priority,
            title=title,
            finding=(
                f"Approximately {missing_rate:.1f}% of "
                f"database cells contain missing values."
            ),
            recommendation=(
                "Review missing-value patterns before using "
                "the affected fields for business decisions."
            ),
            metric="Missing Cell Rate",
            value=missing_rate,
        )
    ]


# ============================================================
# INSIGHT ENGINE
# ============================================================

def generate_all_insights(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """
    Generate all available business insights.

    Only insight modules supported by the dataset's
    available fields are executed.
    """

    if not table_exists(
        engine,
        table_name,
    ):
        return _empty_insights()

    insight_generators = [
        generate_revenue_insights,
        generate_trend_insights,
        generate_product_insights,
        generate_category_insights,
        generate_regional_insights,
        generate_customer_insights,
        generate_profit_insights,
        generate_return_insights,
        generate_data_quality_insights,
    ]

    insights: list[dict[str, Any]] = []

    for generator in insight_generators:
        try:
            generated = generator(
                engine,
                table_name,
            )
            insights.extend(generated)
        except Exception:
            # One unsupported analytical module should not
            # break the complete insight engine.
            continue

    if not insights:
        return _empty_insights()

    result = pd.DataFrame(
        insights
    )

    priority_order = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    result["_priority_order"] = (
        result["priority"]
        .map(priority_order)
        .fillna(3)
    )

    result = result.sort_values(
        "_priority_order"
    ).drop(
        columns=["_priority_order"]
    )

    return result.reset_index(
        drop=True
    )


def run_insight_engine(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> dict[str, Any]:
    """
    Execute the complete business insight engine.
    """

    if not table_exists(
        engine,
        table_name,
    ):
        return {
            "available": False,
            "reason": "Transactions table does not exist.",
            "insights": _empty_insights(),
            "insight_count": 0,
        }

    insights_df = generate_all_insights(
        engine,
        table_name,
    )

    if insights_df.empty:
        return {
            "available": False,
            "reason": (
                "No business insights could be generated "
                "from the available dataset fields."
            ),
            "insights": insights_df,
            "insight_count": 0,
        }

    return {
        "available": True,
        "reason": (
            "Business insight generation completed successfully."
        ),
        "insights": insights_df,
        "insight_count": len(insights_df),
    }