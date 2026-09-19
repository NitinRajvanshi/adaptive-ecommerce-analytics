from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def calculate_sales_amount(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate sales_amount when it is not already available.

    Formula:
        quantity × unit_price

    Existing sales_amount values are preserved.
    """

    transformed = df.copy()

    if "sales_amount" in transformed.columns:
        return transformed

    if (
        "quantity" in transformed.columns
        and "unit_price" in transformed.columns
    ):

        quantity = pd.to_numeric(
            transformed["quantity"],
            errors="coerce",
        )

        unit_price = pd.to_numeric(
            transformed["unit_price"],
            errors="coerce",
        )

        transformed["sales_amount"] = (
            quantity * unit_price
        )

    return transformed


def calculate_discount_amount(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate discount_amount when discount appears to be
    percentage-based.

    Example:
        sales_amount = 1000
        discount = 10
        discount_amount = 100

    If discount is absent, no column is created.

    If discount values are greater than 100, the function
    does not assume they are percentages and leaves the
    calculation as missing.
    """

    transformed = df.copy()

    if "discount" not in transformed.columns:
        return transformed

    if "sales_amount" not in transformed.columns:
        return transformed

    discount = pd.to_numeric(
        transformed["discount"],
        errors="coerce",
    )

    sales = pd.to_numeric(
        transformed["sales_amount"],
        errors="coerce",
    )

    percentage_mask = (
        discount >= 0
    ) & (
        discount <= 100
    )

    transformed["discount_amount"] = np.where(
        percentage_mask,
        sales * discount / 100,
        np.nan,
    )

    return transformed


def calculate_net_sales(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate net_sales when sales_amount and discount_amount
    are available.
    """

    transformed = df.copy()

    if (
        "sales_amount" in transformed.columns
        and "discount_amount" in transformed.columns
    ):

        sales = pd.to_numeric(
            transformed["sales_amount"],
            errors="coerce",
        )

        discount_amount = pd.to_numeric(
            transformed["discount_amount"],
            errors="coerce",
        )

        transformed["net_sales"] = (
            sales - discount_amount.fillna(0)
        )

    elif "sales_amount" in transformed.columns:

        transformed["net_sales"] = pd.to_numeric(
            transformed["sales_amount"],
            errors="coerce",
        )

    return transformed


def calculate_profit(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate profit when enough information is available.

    Priority:
        1. Preserve existing profit.
        2. Calculate net_sales - cost when cost exists.
    """

    transformed = df.copy()

    if "profit" in transformed.columns:
        return transformed

    if (
        "net_sales" in transformed.columns
        and "cost" in transformed.columns
    ):

        net_sales = pd.to_numeric(
            transformed["net_sales"],
            errors="coerce",
        )

        cost = pd.to_numeric(
            transformed["cost"],
            errors="coerce",
        )

        transformed["profit"] = (
            net_sales - cost
        )

    return transformed


def calculate_profit_margin(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate profit margin percentage.

    Formula:
        profit / net_sales × 100
    """

    transformed = df.copy()

    if (
        "profit" not in transformed.columns
        or "net_sales" not in transformed.columns
    ):
        return transformed

    profit = pd.to_numeric(
        transformed["profit"],
        errors="coerce",
    )

    net_sales = pd.to_numeric(
        transformed["net_sales"],
        errors="coerce",
    )

    transformed["profit_margin"] = np.where(
        net_sales != 0,
        (profit / net_sales) * 100,
        np.nan,
    )

    return transformed


def add_date_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create analytical date dimensions.
    """

    transformed = df.copy()

    if "order_date" not in transformed.columns:
        return transformed

    dates = pd.to_datetime(
        transformed["order_date"],
        errors="coerce",
    )

    transformed["order_year"] = (
        dates.dt.year
    )

    transformed["order_month"] = (
        dates.dt.month
    )

    transformed["order_month_name"] = (
        dates.dt.month_name()
    )

    transformed["order_quarter"] = (
        dates.dt.quarter
    )

    transformed["order_day"] = (
        dates.dt.day
    )

    transformed["order_day_name"] = (
        dates.dt.day_name()
    )

    transformed["order_week"] = (
        dates.dt.isocalendar().week.astype("Int64")
    )

    transformed["order_date_only"] = (
        dates.dt.date
    )

    return transformed


def add_transaction_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add row-level analytical features.
    """

    transformed = df.copy()

    # ---------------------------------------------------------
    # Total units
    # ---------------------------------------------------------

    if "quantity" in transformed.columns:

        transformed["quantity"] = pd.to_numeric(
            transformed["quantity"],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # Average item price
    # ---------------------------------------------------------

    if (
        "net_sales" in transformed.columns
        and "quantity" in transformed.columns
    ):

        quantity = transformed["quantity"]

        transformed["average_item_value"] = np.where(
            quantity != 0,
            transformed["net_sales"] / quantity,
            np.nan,
        )

    # ---------------------------------------------------------
    # Has customer
    # ---------------------------------------------------------

    if "customer_id" in transformed.columns:

        transformed["has_customer"] = (
            transformed["customer_id"]
            .notna()
            .astype(int)
        )

    # ---------------------------------------------------------
    # Has product
    # ---------------------------------------------------------

    if "product_id" in transformed.columns:

        transformed["has_product"] = (
            transformed["product_id"]
            .notna()
            .astype(int)
        )

    return transformed


def transform_dataset(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Execute the complete transformation pipeline.

    The input dataframe is not modified.
    """

    transformed = df.copy()

    report: dict[str, Any] = {
        "rows_before": len(transformed),
        "columns_before": len(transformed.columns),
        "steps": [],
    }

    # ---------------------------------------------------------
    # Step 1
    # ---------------------------------------------------------

    before_columns = set(
        transformed.columns
    )

    transformed = calculate_sales_amount(
        transformed
    )

    if "sales_amount" in transformed.columns:
        if "sales_amount" not in before_columns:

            report["steps"].append(
                {
                    "step": "Calculate sales_amount",
                    "status": "completed",
                    "formula": (
                        "quantity × unit_price"
                    ),
                }
            )

    # ---------------------------------------------------------
    # Step 2
    # ---------------------------------------------------------

    transformed = calculate_discount_amount(
        transformed
    )

    if "discount_amount" in transformed.columns:

        report["steps"].append(
            {
                "step": "Calculate discount_amount",
                "status": "completed",
                "formula": (
                    "sales_amount × discount / 100"
                ),
            }
        )

    # ---------------------------------------------------------
    # Step 3
    # ---------------------------------------------------------

    transformed = calculate_net_sales(
        transformed
    )

    if "net_sales" in transformed.columns:

        report["steps"].append(
            {
                "step": "Calculate net_sales",
                "status": "completed",
            }
        )

    # ---------------------------------------------------------
    # Step 4
    # ---------------------------------------------------------

    transformed = calculate_profit(
        transformed
    )

    if "profit" in transformed.columns:

        report["steps"].append(
            {
                "step": "Calculate profit",
                "status": "completed",
            }
        )

    # ---------------------------------------------------------
    # Step 5
    # ---------------------------------------------------------

    transformed = calculate_profit_margin(
        transformed
    )

    if "profit_margin" in transformed.columns:

        report["steps"].append(
            {
                "step": "Calculate profit_margin",
                "status": "completed",
                "formula": (
                    "profit / net_sales × 100"
                ),
            }
        )

    # ---------------------------------------------------------
    # Step 6
    # ---------------------------------------------------------

    transformed = add_date_features(
        transformed
    )

    if "order_year" in transformed.columns:

        report["steps"].append(
            {
                "step": "Create date features",
                "status": "completed",
            }
        )

    # ---------------------------------------------------------
    # Step 7
    # ---------------------------------------------------------

    transformed = add_transaction_features(
        transformed
    )

    report["steps"].append(
        {
            "step": "Create transaction features",
            "status": "completed",
        }
    )

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------

    report["rows_after"] = len(transformed)

    report["columns_after"] = len(
        transformed.columns
    )

    report["new_columns"] = [
        column
        for column in transformed.columns
        if column not in df.columns
    ]

    report["new_column_count"] = len(
        report["new_columns"]
    )

    return transformed, report