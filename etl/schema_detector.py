from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Canonical schema definition
# ---------------------------------------------------------------------------

CANONICAL_FIELDS: dict[str, dict[str, Any]] = {
    "order_id": {
        "aliases": [
            "order_id",
            "orderid",
            "order_number",
            "ordernumber",
            "transaction_id",
            "transactionid",
            "invoice_id",
            "invoiceid",
            "purchase_id",
            "purchaseid",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "order",
            "transaction",
            "invoice",
            "purchase",
        ],
    },
    "order_date": {
        "aliases": [
            "order_date",
            "orderdate",
            "order_datetime",
            "order_time",
            "purchase_date",
            "purchasedate",
            "purchase_datetime",
            "transaction_date",
            "transactiondate",
            "transaction_datetime",
            "date",
            "datetime",
        ],
        "expected_types": ["date-like"],
        "keywords": [
            "date",
            "datetime",
            "purchase",
            "transaction",
            "order",
        ],
    },
    "customer_id": {
        "aliases": [
            "customer_id",
            "customerid",
            "customer_number",
            "user_id",
            "userid",
            "user_number",
            "buyer_id",
            "buyerid",
            "client_id",
            "clientid",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "customer",
            "user",
            "buyer",
            "client",
        ],
    },
    "product_id": {
        "aliases": [
            "product_id",
            "productid",
            "product_number",
            "item_id",
            "itemid",
            "sku",
            "sku_id",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "product",
            "item",
            "sku",
        ],
    },
    "product_name": {
        "aliases": [
            "product",
            "product_name",
            "productname",
            "product_title",
            "producttitle",
            "item",
            "item_name",
            "itemname",
            "item_title",
            "itemtitle",
            "product_description",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "product",
            "item",
            "title",
            "name",
        ],
    },
    "category": {
        "aliases": [
            "category",
            "product_category",
            "productcategory",
            "product_type",
            "producttype",
            "item_category",
            "itemcategory",
            "department",
            "segment",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "category",
            "type",
            "department",
            "segment",
        ],
    },
    "quantity": {
        "aliases": [
            "quantity",
            "qty",
            "units",
            "units_sold",
            "unit_sold",
            "quantity_sold",
            "number_of_units",
            "items_sold",
            "volume",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "quantity",
            "qty",
            "units",
            "sold",
            "items",
            "volume",
        ],
    },
    "unit_price": {
        "aliases": [
            "unit_price",
            "unitprice",
            "price",
            "selling_price",
            "sellingprice",
            "sale_price",
            "saleprice",
            "item_price",
            "itemprice",
            "product_price",
            "productprice",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "price",
            "selling",
            "sale",
        ],
    },
    "sales_amount": {
        "aliases": [
            "sales_amount",
            "salesamount",
            "sales",
            "revenue",
            "revenue_amount",
            "total_sales",
            "total_amount",
            "order_amount",
            "transaction_amount",
            "amount",
            "net_sales",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "sales",
            "revenue",
            "amount",
            "total",
        ],
    },
    "discount": {
        "aliases": [
            "discount",
            "discount_amount",
            "discountamount",
            "discount_percentage",
            "discountpercentage",
            "discount_percent",
            "discountpercent",
            "discount_rate",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "discount",
            "rebate",
            "markdown",
        ],
    },
    "cost": {
        "aliases": [
            "cost",
            "unit_cost",
            "unitcost",
            "cost_price",
            "costprice",
            "total_cost",
            "totalcost",
            "purchase_cost",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "cost",
            "expense",
            "purchase",
        ],
    },
    "profit": {
        "aliases": [
            "profit",
            "profit_amount",
            "profitamount",
            "net_profit",
            "gross_profit",
            "profit_value",
        ],
        "expected_types": ["numeric"],
        "keywords": [
            "profit",
            "margin",
        ],
    },
    "region": {
        "aliases": [
            "region",
            "location",
            "area",
            "sales_region",
            "salesregion",
            "territory",
            "zone",
            "market",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "region",
            "location",
            "area",
            "territory",
            "zone",
            "market",
        ],
    },
    "country": {
        "aliases": [
            "country",
            "country_name",
            "countryname",
            "nation",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "country",
            "nation",
        ],
    },
    "city": {
        "aliases": [
            "city",
            "city_name",
            "cityname",
            "town",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "city",
            "town",
        ],
    },
    "payment_method": {
        "aliases": [
            "payment_method",
            "paymentmethod",
            "payment_type",
            "paymenttype",
            "payment",
            "method_of_payment",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "payment",
            "method",
        ],
    },
    "order_status": {
        "aliases": [
            "order_status",
            "orderstatus",
            "status",
            "transaction_status",
            "transactionstatus",
            "purchase_status",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "status",
            "order",
            "transaction",
        ],
    },
    "return_status": {
        "aliases": [
            "return_status",
            "returnstatus",
            "returned",
            "return",
            "is_returned",
            "refund_status",
            "refundstatus",
        ],
        "expected_types": ["categorical", "boolean"],
        "keywords": [
            "return",
            "returned",
            "refund",
        ],
    },
    "currency": {
        "aliases": [
            "currency",
            "currency_code",
            "currencycode",
            "currency_type",
            "currencytype",
        ],
        "expected_types": ["categorical"],
        "keywords": [
            "currency",
            "currency_code",
        ],
    },
}


def normalize_column_name(column: str) -> str:
    """
    Normalize a source column name into a comparable representation.

    Examples:
        "Order ID"       -> "order_id"
        "order-id"       -> "order_id"
        "ORDER_ID"       -> "order_id"
        "Transaction ID" -> "transaction_id"
        "OrderID"        -> "orderid"
    """

    value = str(column).strip().lower()

    # Convert camel-case boundaries:
    # OrderID -> Order_ID
    value = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        "_",
        value,
    )

    value = value.replace("-", "_")
    value = value.replace(" ", "_")

    value = re.sub(
        r"[^a-z0-9_]",
        "",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return value.strip("_")


def _normalize_for_matching(value: str) -> str:
    """
    Remove separators for additional fuzzy comparisons.

    Example:
        order_id -> orderid
        order-id -> orderid
    """

    return re.sub(
        r"[^a-z0-9]",
        "",
        normalize_column_name(value),
    )


def _get_detected_type(series: pd.Series) -> str:
    """
    Determine the broad data type of a source column.

    Returns:
        numeric, date-like, categorical, boolean, or other.
    """

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    non_null = series.dropna()

    if non_null.empty:
        return "categorical"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "date-like"

    if not pd.api.types.is_numeric_dtype(series):
        parsed_dates = pd.to_datetime(
            non_null,
            errors="coerce",
            format="mixed",
        )

        parse_rate = parsed_dates.notna().mean()

        if parse_rate >= 0.80:
            return "date-like"

    return "categorical"


def _calculate_name_similarity(
    source_column: str,
    alias: str,
) -> float:
    """
    Calculate normalized name similarity between a source
    column and an alias.
    """

    source = _normalize_for_matching(
        source_column
    )

    target = _normalize_for_matching(alias)

    if not source or not target:
        return 0.0

    if source == target:
        return 1.0

    return SequenceMatcher(
        None,
        source,
        target,
    ).ratio()


def _calculate_keyword_score(
    normalized_column: str,
    keywords: list[str],
) -> float:
    """
    Calculate a simple semantic keyword score.
    """

    compact_column = _normalize_for_matching(
        normalized_column
    )

    if not compact_column:
        return 0.0

    matches = 0

    for keyword in keywords:
        compact_keyword = _normalize_for_matching(
            keyword
        )

        if (
            compact_keyword
            and compact_keyword in compact_column
        ):
            matches += 1

    if not keywords:
        return 0.0

    return min(
        matches / max(len(keywords), 1),
        1.0,
    )


def _calculate_value_signal(
    series: pd.Series,
    canonical_field: str,
) -> float:
    """
    Calculate a lightweight semantic signal from sample values.

    This is intentionally conservative. It provides supporting
    evidence rather than making a decision by itself.
    """

    non_null = series.dropna()

    if non_null.empty:
        return 0.0

    sample = non_null.astype(str).head(100)

    if canonical_field == "order_date":
        parsed = pd.to_datetime(
            sample,
            errors="coerce",
            format="mixed",
        )

        return float(parsed.notna().mean())

    if canonical_field in {
        "quantity",
        "unit_price",
        "sales_amount",
        "discount",
        "cost",
        "profit",
    }:
        numeric = pd.to_numeric(
            sample,
            errors="coerce",
        )

        return float(numeric.notna().mean())

    if canonical_field in {
        "order_id",
        "customer_id",
        "product_id",
    }:
        value_strings = sample.str.lower()

        identifier_pattern = value_strings.str.match(
            r"^[a-z]+[_-]?\d+$",
            na=False,
        )

        return float(
            identifier_pattern.mean()
        )

    return 0.0


def _score_candidate(
    source_column: str,
    series: pd.Series,
    canonical_field: str,
) -> dict[str, Any]:
    """
    Calculate the confidence score for one source-column /
    canonical-field combination.
    """

    definition = CANONICAL_FIELDS[
        canonical_field
    ]

    aliases = definition["aliases"]
    expected_types = definition[
        "expected_types"
    ]
    keywords = definition["keywords"]

    normalized_source = normalize_column_name(
        source_column
    )

    normalized_aliases = {
        normalize_column_name(alias)
        for alias in aliases
    }

    detected_type = _get_detected_type(
        series
    )

    # ---------------------------------------------------------------
    # 1. Exact alias match
    # ---------------------------------------------------------------

    if normalized_source in normalized_aliases:
        return {
            "source_column": source_column,
            "detected_field": canonical_field,
            "confidence": 0.99,
            "confidence_level": "High",
            "detected_type": detected_type,
            "match_reason": "Exact alias match",
        }

    # ---------------------------------------------------------------
    # 2. Fuzzy column-name similarity
    # ---------------------------------------------------------------

    name_similarity = max(
        (
            _calculate_name_similarity(
                source_column,
                alias,
            )
            for alias in aliases
        ),
        default=0.0,
    )

    # ---------------------------------------------------------------
    # 3. Keyword signal
    # ---------------------------------------------------------------

    keyword_score = _calculate_keyword_score(
        normalized_source,
        keywords,
    )

    # ---------------------------------------------------------------
    # 4. Data-type compatibility
    # ---------------------------------------------------------------

    type_score = (
        1.0
        if detected_type in expected_types
        else 0.0
    )

    # ---------------------------------------------------------------
    # 5. Value-based supporting signal
    # ---------------------------------------------------------------

    value_score = _calculate_value_signal(
        series,
        canonical_field,
    )

    # ---------------------------------------------------------------
    # Combined confidence
    # ---------------------------------------------------------------

    confidence = (
        (name_similarity * 0.55)
        + (keyword_score * 0.20)
        + (type_score * 0.15)
        + (value_score * 0.10)
    )

    confidence = min(
        max(confidence, 0.0),
        0.98,
    )

    if confidence >= 0.90:
        confidence_level = "High"
    elif confidence >= 0.70:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"

    reasons: list[str] = []

    if name_similarity >= 0.85:
        reasons.append("strong name similarity")
    elif name_similarity >= 0.70:
        reasons.append("moderate name similarity")

    if keyword_score > 0:
        reasons.append("semantic keyword match")

    if type_score > 0:
        reasons.append(
            f"compatible data type ({detected_type})"
        )

    if value_score >= 0.80:
        reasons.append("supporting value pattern")

    match_reason = (
        ", ".join(reasons)
        if reasons
        else "weak semantic evidence"
    )

    return {
        "source_column": source_column,
        "detected_field": canonical_field,
        "confidence": round(
            confidence,
            4,
        ),
        "confidence_level": confidence_level,
        "detected_type": detected_type,
        "match_reason": match_reason,
    }


def detect_column_candidates(
    df: pd.DataFrame,
    top_n: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """
    Detect candidate canonical fields for every source column.

    Args:
        df: Source DataFrame.
        top_n: Number of candidates retained per source column.

    Returns:
        Dictionary mapping source columns to candidate mappings.
    """

    candidates: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for source_column in df.columns:

        column_candidates = []

        for canonical_field in CANONICAL_FIELDS:

            result = _score_candidate(
                source_column=str(source_column),
                series=df[source_column],
                canonical_field=canonical_field,
            )

            column_candidates.append(result)

        column_candidates.sort(
            key=lambda item: item["confidence"],
            reverse=True,
        )

        candidates[str(source_column)] = (
            column_candidates[:top_n]
        )

    return candidates


def detect_schema(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce the best candidate mapping for every source column.

    Args:
        df: Source DataFrame.

    Returns:
        DataFrame containing source columns, detected fields,
        confidence scores and supporting evidence.
    """

    candidates = detect_column_candidates(
        df
    )

    records: list[dict[str, Any]] = []

    for source_column, column_candidates in candidates.items():

        if not column_candidates:
            continue

        best_candidate = column_candidates[0]

        records.append(
            {
                "source_column": source_column,
                "detected_field": best_candidate[
                    "detected_field"
                ],
                "confidence": best_candidate[
                    "confidence"
                ],
                "confidence_percent": (
                    f"{best_candidate['confidence'] * 100:.1f}%"
                ),
                "confidence_level": best_candidate[
                    "confidence_level"
                ],
                "detected_type": best_candidate[
                    "detected_type"
                ],
                "match_reason": best_candidate[
                    "match_reason"
                ],
            }
        )

    return pd.DataFrame(records)


def get_mapping_candidates(
    df: pd.DataFrame,
    source_column: str,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """
    Return the top candidate mappings for one source column.

    Args:
        df: Source DataFrame.
        source_column: Column for which candidates are required.
        top_n: Maximum number of candidates.

    Returns:
        Ranked candidate mappings.
    """

    if source_column not in df.columns:
        raise KeyError(
            f"Source column not found: {source_column}"
        )

    candidates = detect_column_candidates(
        df,
        top_n=top_n,
    )

    return candidates[
        str(source_column)
    ]