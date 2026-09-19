from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def add_order_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add order-level analytical features.
    """

    result = df.copy()

    # ---------------------------------------------------------
    # Order value
    # ---------------------------------------------------------

    if "net_sales" in result.columns:
        result["order_value"] = pd.to_numeric(
            result["net_sales"],
            errors="coerce",
        )

    elif "sales_amount" in result.columns:
        result["order_value"] = pd.to_numeric(
            result["sales_amount"],
            errors="coerce",
        )

    # ---------------------------------------------------------
    # High-value order flag
    #
    # This is NOT used as a business judgment.
    # It simply identifies orders above the dataset median.
    # ---------------------------------------------------------

    if "order_value" in result.columns:

        median_value = result[
            "order_value"
        ].median()

        result["is_high_value_order"] = (
            result["order_value"] > median_value
        ).astype("int")

    return result


def add_customer_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create customer-level features when customer_id exists.

    Features are calculated at transaction level and merged back
    into each transaction.
    """

    result = df.copy()

    required_columns = [
        "customer_id",
        "order_date",
    ]

    if not all(
        column in result.columns
        for column in required_columns
    ):
        return result

    # Need an order value for monetary calculations.
    if "order_value" in result.columns:

        value_column = "order_value"

    elif "net_sales" in result.columns:

        result["order_value"] = pd.to_numeric(
            result["net_sales"],
            errors="coerce",
        )

        value_column = "order_value"

    elif "sales_amount" in result.columns:

        result["order_value"] = pd.to_numeric(
            result["sales_amount"],
            errors="coerce",
        )

        value_column = "order_value"

    else:
        return result

    result["order_date"] = pd.to_datetime(
        result["order_date"],
        errors="coerce",
    )

    valid_customer_mask = (
        result["customer_id"].notna()
        & result["order_date"].notna()
    )

    customer_data = result.loc[
        valid_customer_mask
    ].copy()

    if customer_data.empty:
        return result

    # ---------------------------------------------------------
    # Customer order count
    # ---------------------------------------------------------

    customer_order_count = (
        customer_data
        .groupby("customer_id")
        .size()
        .rename("customer_order_count")
    )

    # ---------------------------------------------------------
    # Customer total spend
    # ---------------------------------------------------------

    customer_total_spend = (
        customer_data
        .groupby("customer_id")[value_column]
        .sum(min_count=1)
        .rename("customer_total_spend")
    )

    # ---------------------------------------------------------
    # Customer average order value
    # ---------------------------------------------------------

    customer_avg_order_value = (
        customer_data
        .groupby("customer_id")[value_column]
        .mean()
        .rename("customer_avg_order_value")
    )

    # ---------------------------------------------------------
    # First order date
    # ---------------------------------------------------------

    first_order_date = (
        customer_data
        .groupby("customer_id")["order_date"]
        .min()
        .rename("first_order_date")
    )

    # ---------------------------------------------------------
    # Last order date
    # ---------------------------------------------------------

    last_order_date = (
        customer_data
        .groupby("customer_id")["order_date"]
        .max()
        .rename("last_order_date")
    )

    customer_features = pd.concat(
        [
            customer_order_count,
            customer_total_spend,
            customer_avg_order_value,
            first_order_date,
            last_order_date,
        ],
        axis=1,
    )

    # ---------------------------------------------------------
    # Customer lifetime days
    # ---------------------------------------------------------

    customer_features[
        "customer_lifetime_days"
    ] = (
        customer_features["last_order_date"]
        - customer_features["first_order_date"]
    ).dt.days

    # ---------------------------------------------------------
    # Repeat customer flag
    # ---------------------------------------------------------

    customer_features[
        "is_repeat_customer"
    ] = (
        customer_features["customer_order_count"]
        > 1
    ).astype(int)

    # ---------------------------------------------------------
    # Merge back to transaction data
    # ---------------------------------------------------------

    result = result.merge(
        customer_features.reset_index(),
        on="customer_id",
        how="left",
        suffixes=("", "_customer"),
    )

    return result


def calculate_rfm_features(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Calculate RFM features.

    R = Recency
    F = Frequency
    M = Monetary

    RFM is calculated only when customer_id, order_date,
    and a monetary field are available.
    """

    result = df.copy()

    required = [
        "customer_id",
        "order_date",
    ]

    if not all(
        column in result.columns
        for column in required
    ):
        return result

    # ---------------------------------------------------------
    # Monetary field
    # ---------------------------------------------------------

    if "order_value" in result.columns:

        value_column = "order_value"

    elif "net_sales" in result.columns:

        result["order_value"] = pd.to_numeric(
            result["net_sales"],
            errors="coerce",
        )

        value_column = "order_value"

    elif "sales_amount" in result.columns:

        result["order_value"] = pd.to_numeric(
            result["sales_amount"],
            errors="coerce",
        )

        value_column = "order_value"

    else:
        return result

    result["order_date"] = pd.to_datetime(
        result["order_date"],
        errors="coerce",
    )

    valid_mask = (
        result["customer_id"].notna()
        & result["order_date"].notna()
    )

    customer_data = result.loc[
        valid_mask
    ].copy()

    if customer_data.empty:
        return result

    # ---------------------------------------------------------
    # Reference date
    # ---------------------------------------------------------

    if reference_date is None:

        reference_date = (
            customer_data["order_date"].max()
            + pd.Timedelta(days=1)
        )

    reference_date = pd.Timestamp(
        reference_date
    )

    # ---------------------------------------------------------
    # Recency
    # ---------------------------------------------------------

    last_purchase = (
        customer_data
        .groupby("customer_id")["order_date"]
        .max()
    )

    recency = (
        reference_date - last_purchase
    ).dt.days

    recency.name = "recency_days"

    # ---------------------------------------------------------
    # Frequency
    # ---------------------------------------------------------

    frequency = (
        customer_data
        .groupby("customer_id")
        .size()
    )

    frequency.name = "frequency"

    # ---------------------------------------------------------
    # Monetary
    # ---------------------------------------------------------

    monetary = (
        customer_data
        .groupby("customer_id")[value_column]
        .sum(min_count=1)
    )

    monetary.name = "monetary"

    # ---------------------------------------------------------
    # Combine RFM
    # ---------------------------------------------------------

    rfm = pd.concat(
        [
            recency,
            frequency,
            monetary,
        ],
        axis=1,
    )

    # ---------------------------------------------------------
    # Merge back
    # ---------------------------------------------------------

    result = result.merge(
        rfm.reset_index(),
        on="customer_id",
        how="left",
    )

    return result


def create_rfm_scores(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create relative RFM scores from 1 to 5.

    Recency:
        Lower is better → score is reversed.

    Frequency:
        Higher receives a higher score.

    Monetary:
        Higher receives a higher score.

    Quantile ranking is used when enough unique values exist.
    """

    result = df.copy()

    required_columns = [
        "recency_days",
        "frequency",
        "monetary",
    ]

    if not all(
        column in result.columns
        for column in required_columns
    ):
        return result

    def score_series(
        series: pd.Series,
        reverse: bool = False,
    ) -> pd.Series:

        valid = series.notna()

        if valid.sum() < 2:
            return pd.Series(
                np.nan,
                index=series.index,
            )

        unique_values = series[
            valid
        ].nunique()

        if unique_values < 2:
            scores = pd.Series(
                3,
                index=series.index,
                dtype="float",
            )

            scores[~valid] = np.nan

            return scores

        ranks = series.rank(
            method="average",
            pct=True,
        )

        if reverse:
            ranks = 1 - ranks + (
                1 / max(valid.sum(), 1)
            )

        scores = np.ceil(
            ranks * 5
        ).clip(
            lower=1,
            upper=5,
        )

        scores[~valid] = np.nan

        return scores

    result["recency_score"] = score_series(
        result["recency_days"],
        reverse=True,
    )

    result["frequency_score"] = score_series(
        result["frequency"],
    )

    result["monetary_score"] = score_series(
        result["monetary"],
    )

    result["rfm_score"] = (
        result["recency_score"]
        + result["frequency_score"]
        + result["monetary_score"]
    )

    result["rfm_segment"] = np.select(
        [
            result["rfm_score"] >= 13,
            result["rfm_score"] >= 9,
            result["rfm_score"] >= 6,
        ],
        [
            "High RFM Score",
            "Medium RFM Score",
            "Low RFM Score",
        ],
        default="Insufficient Data",
    )

    return result


def add_product_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add product-level analytical features when product
    information is available.
    """

    result = df.copy()

    if "product_id" not in result.columns:
        return result

    if "order_value" not in result.columns:

        if "net_sales" in result.columns:

            result["order_value"] = pd.to_numeric(
                result["net_sales"],
                errors="coerce",
            )

        elif "sales_amount" in result.columns:

            result["order_value"] = pd.to_numeric(
                result["sales_amount"],
                errors="coerce",
            )

        else:
            return result

    product_features = (
        result
        .groupby("product_id")
        .agg(
            product_order_count=(
                "product_id",
                "size",
            ),
            product_total_sales=(
                "order_value",
                "sum",
            ),
            product_average_order_value=(
                "order_value",
                "mean",
            ),
        )
        .reset_index()
    )

    result = result.merge(
        product_features,
        on="product_id",
        how="left",
        suffixes=("", "_product"),
    )

    return result


def add_region_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add region-level analytical features when region exists.
    """

    result = df.copy()

    if "region" not in result.columns:
        return result

    if "order_value" not in result.columns:

        if "net_sales" in result.columns:

            result["order_value"] = pd.to_numeric(
                result["net_sales"],
                errors="coerce",
            )

        elif "sales_amount" in result.columns:

            result["order_value"] = pd.to_numeric(
                result["sales_amount"],
                errors="coerce",
            )

        else:
            return result

    region_features = (
        result
        .groupby("region")
        .agg(
            region_order_count=(
                "region",
                "size",
            ),
            region_total_sales=(
                "order_value",
                "sum",
            ),
            region_average_order_value=(
                "order_value",
                "mean",
            ),
        )
        .reset_index()
    )

    result = result.merge(
        region_features,
        on="region",
        how="left",
        suffixes=("", "_region"),
    )

    return result


def engineer_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Execute the complete feature engineering pipeline.
    """

    result = df.copy()

    report: dict[str, Any] = {
        "rows_before": len(result),
        "columns_before": len(result.columns),
        "steps": [],
    }

    # ---------------------------------------------------------
    # Order features
    # ---------------------------------------------------------

    before = set(result.columns)

    result = add_order_features(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "Order features",
            "status": "completed",
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # Customer features
    # ---------------------------------------------------------

    before = set(result.columns)

    result = add_customer_features(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "Customer features",
            "status": (
                "completed"
                if new_columns
                else "skipped - customer data unavailable"
            ),
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # RFM
    # ---------------------------------------------------------

    before = set(result.columns)

    result = calculate_rfm_features(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "RFM features",
            "status": (
                "completed"
                if new_columns
                else "skipped - insufficient data"
            ),
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # RFM scores
    # ---------------------------------------------------------

    before = set(result.columns)

    result = create_rfm_scores(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "RFM scoring",
            "status": (
                "completed"
                if new_columns
                else "skipped - RFM unavailable"
            ),
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # Product features
    # ---------------------------------------------------------

    before = set(result.columns)

    result = add_product_features(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "Product features",
            "status": (
                "completed"
                if new_columns
                else "skipped - product data unavailable"
            ),
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # Regional features
    # ---------------------------------------------------------

    before = set(result.columns)

    result = add_region_features(result)

    new_columns = [
        column
        for column in result.columns
        if column not in before
    ]

    report["steps"].append(
        {
            "step": "Regional features",
            "status": (
                "completed"
                if new_columns
                else "skipped - region data unavailable"
            ),
            "new_columns": new_columns,
        }
    )

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------

    report["rows_after"] = len(result)
    report["columns_after"] = len(result.columns)

    report["new_columns"] = [
        column
        for column in result.columns
        if column not in df.columns
    ]

    report["new_column_count"] = len(
        report["new_columns"]
    )

    return result, report