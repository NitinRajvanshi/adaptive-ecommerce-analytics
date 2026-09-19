from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

TEXT_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
    "product_name",
    "category",
    "region",
    "country",
    "city",
    "payment_method",
    "order_status",
    "return_status",
    "currency",
]


NUMERIC_COLUMNS = [
    "quantity",
    "unit_price",
    "sales_amount",
    "discount",
    "cost",
    "profit",
]


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names.

    Example:
        Order ID -> order_id
        Product-Name -> product_name
    """

    cleaned = df.copy()

    cleaned.columns = (
        cleaned.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    return cleaned


def remove_exact_duplicates(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """
    Remove completely identical rows.

    Returns:
        cleaned dataframe
        number of rows removed
    """

    before = len(df)

    cleaned = df.drop_duplicates(
        keep="first"
    ).copy()

    removed = before - len(cleaned)

    return cleaned, removed


def clean_text_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean whitespace and normalize text fields.

    Category-like values are normalized using title case.
    """

    cleaned = df.copy()

    for column in TEXT_COLUMNS:

        if column not in cleaned.columns:
            continue

        # Convert non-null values to strings
        cleaned[column] = cleaned[column].apply(
            lambda value: (
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

    # ---------------------------------------------------------
    # Category normalization
    # ---------------------------------------------------------

    if "category" in cleaned.columns:

        cleaned["category"] = (
            cleaned["category"]
            .astype("string")
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    # ---------------------------------------------------------
    # Region normalization
    # ---------------------------------------------------------

    if "region" in cleaned.columns:

        cleaned["region"] = (
            cleaned["region"]
            .astype("string")
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    # ---------------------------------------------------------
    # Payment method normalization
    # ---------------------------------------------------------

    if "payment_method" in cleaned.columns:

        cleaned["payment_method"] = (
            cleaned["payment_method"]
            .astype("string")
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    return cleaned


def convert_dates(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert known date fields to pandas datetime.
    Invalid dates become NaT.
    """

    cleaned = df.copy()

    if "order_date" in cleaned.columns:

        cleaned["order_date"] = pd.to_datetime(
            cleaned["order_date"],
            errors="coerce",
            format="mixed",
        )

    return cleaned


def convert_numeric_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert known numeric columns to numeric dtype.

    Invalid numeric values become NaN.
    """

    cleaned = df.copy()

    for column in NUMERIC_COLUMNS:

        if column not in cleaned.columns:
            continue

        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce",
        )

    return cleaned


def clean_business_values(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Handle clearly invalid business values.

    Negative quantities and negative unit prices are converted
    to missing values.

    Negative sales amounts are intentionally preserved because
    they can represent returns/refunds.
    """

    cleaned = df.copy()

    changes: dict[str, int] = {}

    # ---------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------

    if "quantity" in cleaned.columns:

        quantity = pd.to_numeric(
            cleaned["quantity"],
            errors="coerce",
        )

        invalid_mask = quantity < 0

        count = int(invalid_mask.sum())

        if count > 0:
            quantity.loc[invalid_mask] = np.nan

        cleaned["quantity"] = quantity

        changes["negative_quantity_fixed"] = count

    # ---------------------------------------------------------
    # Unit price
    # ---------------------------------------------------------

    if "unit_price" in cleaned.columns:

        price = pd.to_numeric(
            cleaned["unit_price"],
            errors="coerce",
        )

        invalid_mask = price < 0

        count = int(invalid_mask.sum())

        if count > 0:
            price.loc[invalid_mask] = np.nan

        cleaned["unit_price"] = price

        changes["negative_unit_price_fixed"] = count

    # ---------------------------------------------------------
    # Discount
    # ---------------------------------------------------------

    if "discount" in cleaned.columns:

        discount = pd.to_numeric(
            cleaned["discount"],
            errors="coerce",
        )

        invalid_mask = discount < 0

        count = int(invalid_mask.sum())

        if count > 0:
            discount.loc[invalid_mask] = np.nan

        cleaned["discount"] = discount

        changes["negative_discount_fixed"] = count

    return cleaned, changes


def clean_dataset(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Execute the complete deterministic cleaning pipeline.

    The original dataframe is never modified.
    """

    cleaned = df.copy()

    report: dict[str, Any] = {
        "rows_before": len(cleaned),
        "columns_before": len(cleaned.columns),
        "steps": [],
    }

    # ---------------------------------------------------------
    # Step 1: Column names
    # ---------------------------------------------------------

    original_columns = cleaned.columns.tolist()

    cleaned = clean_column_names(cleaned)

    if original_columns != cleaned.columns.tolist():

        report["steps"].append(
            {
                "step": "Standardize column names",
                "status": "completed",
                "details": (
                    f"{original_columns} -> "
                    f"{cleaned.columns.tolist()}"
                ),
            }
        )

    # ---------------------------------------------------------
    # Step 2: Exact duplicates
    # ---------------------------------------------------------

    cleaned, duplicates_removed = (
        remove_exact_duplicates(cleaned)
    )

    report["duplicates_removed"] = (
        duplicates_removed
    )

    report["steps"].append(
        {
            "step": "Remove exact duplicates",
            "status": "completed",
            "rows_removed": duplicates_removed,
        }
    )

    # ---------------------------------------------------------
    # Step 3: Text cleaning
    # ---------------------------------------------------------

    cleaned = clean_text_columns(cleaned)

    report["steps"].append(
        {
            "step": "Clean text and categories",
            "status": "completed",
        }
    )

    # ---------------------------------------------------------
    # Step 4: Dates
    # ---------------------------------------------------------

    cleaned = convert_dates(cleaned)

    report["steps"].append(
        {
            "step": "Convert dates",
            "status": "completed",
        }
    )

    # ---------------------------------------------------------
    # Step 5: Numeric conversion
    # ---------------------------------------------------------

    cleaned = convert_numeric_columns(
        cleaned
    )

    report["steps"].append(
        {
            "step": "Convert numeric columns",
            "status": "completed",
        }
    )

    # ---------------------------------------------------------
    # Step 6: Business rules
    # ---------------------------------------------------------

    cleaned, business_changes = (
        clean_business_values(cleaned)
    )

    report["business_value_changes"] = (
        business_changes
    )

    report["steps"].append(
        {
            "step": "Apply business validation rules",
            "status": "completed",
            "changes": business_changes,
        }
    )

    # ---------------------------------------------------------
    # Final statistics
    # ---------------------------------------------------------

    report["rows_after"] = len(cleaned)
    report["columns_after"] = len(cleaned.columns)

    report["rows_removed"] = (
        report["rows_before"]
        - report["rows_after"]
    )

    report["missing_values_after"] = int(
        cleaned.isna().sum().sum()
    )

    return cleaned, report