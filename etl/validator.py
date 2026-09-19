from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

REQUIRED_FIELDS = [
    "order_id",
    "order_date",
    "quantity",
]

PRICE_FIELDS = [
    "unit_price",
    "sales_amount",
]

NUMERIC_FIELDS = [
    "quantity",
    "unit_price",
    "sales_amount",
    "discount",
    "cost",
    "profit",
]


@dataclass
class ValidationIssue:
    category: str
    severity: str
    issue: str
    count: int
    percentage: float
    explanation: str


def _percentage(count: int, total: int) -> float:
    """Safely calculate a percentage."""
    if total <= 0:
        return 0.0

    return round((count / total) * 100, 2)


def _get_unmapped_columns(
    df: pd.DataFrame,
    mapping: dict[str, str] | None,
) -> list[str]:
    """
    Return source columns that were not mapped to a canonical field.
    """
    if not mapping:
        return list(df.columns)

    mapped_source_columns = set(mapping.keys())

    return [
        column
        for column in df.columns
        if column not in mapped_source_columns
    ]


def validate_schema(
    df: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Validate the structure of the canonical dataset.
    """

    issues: list[ValidationIssue] = []

    # ---------------------------------------------------------
    # Empty dataset
    # ---------------------------------------------------------
    if df.empty:
        issues.append(
            ValidationIssue(
                category="SCHEMA",
                severity="ERROR",
                issue="Empty dataset",
                count=0,
                percentage=0.0,
                explanation="The dataset contains no rows.",
            )
        )

    # ---------------------------------------------------------
    # Duplicate column names
    # ---------------------------------------------------------
    duplicate_columns = df.columns[df.columns.duplicated()].tolist()

    if duplicate_columns:
        issues.append(
            ValidationIssue(
                category="SCHEMA",
                severity="ERROR",
                issue="Duplicate column names",
                count=len(duplicate_columns),
                percentage=0.0,
                explanation=(
                    f"Duplicate columns detected: {duplicate_columns}"
                ),
            )
        )

    # ---------------------------------------------------------
    # Required fields
    # ---------------------------------------------------------
    missing_required = [
        field
        for field in REQUIRED_FIELDS
        if field not in df.columns
    ]

    if missing_required:
        issues.append(
            ValidationIssue(
                category="SCHEMA",
                severity="ERROR",
                issue="Missing required fields",
                count=len(missing_required),
                percentage=0.0,
                explanation=(
                    "Required fields missing: "
                    + ", ".join(missing_required)
                ),
            )
        )

    # ---------------------------------------------------------
    # Price requirement
    # ---------------------------------------------------------
    available_price_fields = [
        field
        for field in PRICE_FIELDS
        if field in df.columns
    ]

    if not available_price_fields:
        issues.append(
            ValidationIssue(
                category="SCHEMA",
                severity="ERROR",
                issue="Missing price field",
                count=1,
                percentage=0.0,
                explanation=(
                    "At least one of unit_price or sales_amount "
                    "must be available."
                ),
            )
        )

    # ---------------------------------------------------------
    # Unmapped source columns
    # ---------------------------------------------------------
    unmapped_columns = _get_unmapped_columns(df, mapping)

    if unmapped_columns:
        issues.append(
            ValidationIssue(
                category="SCHEMA",
                severity="INFO",
                issue="Unmapped source columns",
                count=len(unmapped_columns),
                percentage=0.0,
                explanation=(
                    "These source columns were not mapped to canonical "
                    f"fields: {unmapped_columns}"
                ),
            )
        )

    return {
        "issues": issues,
        "missing_required_fields": missing_required,
        "available_price_fields": available_price_fields,
        "duplicate_columns": duplicate_columns,
        "unmapped_columns": unmapped_columns,
    }


def validate_values(df: pd.DataFrame) -> dict[str, Any]:
    """
    Validate values inside the dataset.

    This function does not modify the dataframe.
    """

    issues: list[ValidationIssue] = []

    row_count = len(df)

    # ---------------------------------------------------------
    # Missing values
    # ---------------------------------------------------------
    missing_by_column = df.isna().sum()
    total_missing = int(missing_by_column.sum())

    if total_missing > 0:
        total_cells = max(df.shape[0] * df.shape[1], 1)

        issues.append(
            ValidationIssue(
                category="VALUES",
                severity="WARNING",
                issue="Missing values",
                count=total_missing,
                percentage=_percentage(total_missing, total_cells),
                explanation=(
                    "Missing values were detected. Optional fields may "
                    "contain missing values, but required fields should "
                    "be reviewed carefully."
                ),
            )
        )

    # ---------------------------------------------------------
    # Invalid order dates
    # ---------------------------------------------------------
    invalid_date_count = 0

    if "order_date" in df.columns:
        original = df["order_date"]

        non_missing = original.notna()

        parsed = pd.to_datetime(
            original,
            errors="coerce",
            format="mixed",
        )

        invalid_date_count = int(
            (non_missing & parsed.isna()).sum()
        )

        if invalid_date_count > 0:
            issues.append(
                ValidationIssue(
                    category="VALUES",
                    severity="ERROR",
                    issue="Invalid dates",
                    count=invalid_date_count,
                    percentage=_percentage(
                        invalid_date_count,
                        int(non_missing.sum()),
                    ),
                    explanation=(
                        "Some non-empty order_date values cannot be "
                        "interpreted as valid dates."
                    ),
                )
            )

    # ---------------------------------------------------------
    # Numeric validation
    # ---------------------------------------------------------
    invalid_numeric_count = 0

    numeric_details: dict[str, int] = {}

    for column in NUMERIC_FIELDS:

        if column not in df.columns:
            continue

        series = df[column]

        non_missing = series.notna()

        converted = pd.to_numeric(
            series,
            errors="coerce",
        )

        invalid_count = int(
            (non_missing & converted.isna()).sum()
        )

        if invalid_count > 0:
            numeric_details[column] = invalid_count
            invalid_numeric_count += invalid_count

    if invalid_numeric_count > 0:
        total_numeric_values = sum(
            int(df[column].notna().sum())
            for column in NUMERIC_FIELDS
            if column in df.columns
        )

        issues.append(
            ValidationIssue(
                category="VALUES",
                severity="ERROR",
                issue="Invalid numeric values",
                count=invalid_numeric_count,
                percentage=_percentage(
                    invalid_numeric_count,
                    total_numeric_values,
                ),
                explanation=(
                    f"Non-numeric values detected in: {numeric_details}"
                ),
            )
        )

    # ---------------------------------------------------------
    # Negative quantities
    # ---------------------------------------------------------
    negative_quantity_count = 0

    if "quantity" in df.columns:

        quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce",
        )

        negative_quantity_count = int(
            (quantity < 0).sum()
        )

        if negative_quantity_count > 0:
            issues.append(
                ValidationIssue(
                    category="BUSINESS_RULE",
                    severity="ERROR",
                    issue="Negative quantities",
                    count=negative_quantity_count,
                    percentage=_percentage(
                        negative_quantity_count,
                        row_count,
                    ),
                    explanation=(
                        "Quantity values below zero were detected. "
                        "These should be reviewed before analytics."
                    ),
                )
            )

    # ---------------------------------------------------------
    # Negative unit prices
    # ---------------------------------------------------------
    negative_price_count = 0

    if "unit_price" in df.columns:

        price = pd.to_numeric(
            df["unit_price"],
            errors="coerce",
        )

        negative_price_count = int(
            (price < 0).sum()
        )

        if negative_price_count > 0:
            issues.append(
                ValidationIssue(
                    category="BUSINESS_RULE",
                    severity="ERROR",
                    issue="Negative unit prices",
                    count=negative_price_count,
                    percentage=_percentage(
                        negative_price_count,
                        row_count,
                    ),
                    explanation=(
                        "Negative unit prices were detected."
                    ),
                )
            )

    # ---------------------------------------------------------
    # Negative sales amount
    # ---------------------------------------------------------
    negative_sales_count = 0

    if "sales_amount" in df.columns:

        sales = pd.to_numeric(
            df["sales_amount"],
            errors="coerce",
        )

        negative_sales_count = int(
            (sales < 0).sum()
        )

        if negative_sales_count > 0:
            issues.append(
                ValidationIssue(
                    category="BUSINESS_RULE",
                    severity="WARNING",
                    issue="Negative sales amounts",
                    count=negative_sales_count,
                    percentage=_percentage(
                        negative_sales_count,
                        row_count,
                    ),
                    explanation=(
                        "Negative sales amounts were detected. "
                        "These may represent returns or refunds, so "
                        "they are flagged rather than automatically removed."
                    ),
                )
            )

    # ---------------------------------------------------------
    # Discount validation
    # ---------------------------------------------------------
    invalid_discount_count = 0

    if "discount" in df.columns:

        discount = pd.to_numeric(
            df["discount"],
            errors="coerce",
        )

        invalid_discount_count = int(
            (discount < 0).sum()
        )

        if invalid_discount_count > 0:
            issues.append(
                ValidationIssue(
                    category="BUSINESS_RULE",
                    severity="WARNING",
                    issue="Negative discounts",
                    count=invalid_discount_count,
                    percentage=_percentage(
                        invalid_discount_count,
                        row_count,
                    ),
                    explanation=(
                        "Negative discount values were detected. "
                        "Discount semantics will be handled during "
                        "transformation."
                    ),
                )
            )

    return {
        "issues": issues,
        "missing_value_count": total_missing,
        "missing_by_column": missing_by_column.to_dict(),
        "invalid_date_count": invalid_date_count,
        "invalid_numeric_count": invalid_numeric_count,
        "negative_quantity_count": negative_quantity_count,
        "negative_price_count": negative_price_count,
        "negative_sales_count": negative_sales_count,
        "invalid_discount_count": invalid_discount_count,
    }


def detect_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detect exact duplicates and suspicious duplicate transactions.

    Exact duplicates can normally be removed during cleaning.

    Suspicious duplicates are only flagged because they may represent
    legitimate multiple line items or transactions.
    """

    issues: list[ValidationIssue] = []

    row_count = len(df)

    # ---------------------------------------------------------
    # Exact duplicates
    # ---------------------------------------------------------
    duplicate_mask = df.duplicated(keep="first")

    exact_duplicate_count = int(duplicate_mask.sum())

    if exact_duplicate_count > 0:
        issues.append(
            ValidationIssue(
                category="DUPLICATES",
                severity="WARNING",
                issue="Exact duplicate rows",
                count=exact_duplicate_count,
                percentage=_percentage(
                    exact_duplicate_count,
                    row_count,
                ),
                explanation=(
                    "Rows that are completely identical were detected. "
                    "These are candidates for removal during cleaning."
                ),
            )
        )

    # ---------------------------------------------------------
    # Suspicious duplicates
    # ---------------------------------------------------------
    potential_duplicate_count = 0
    potential_duplicate_groups = 0

    key_candidates = [
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
    ]

    available_keys = [
        column
        for column in key_candidates
        if column in df.columns
    ]

    # Require the key combination to contain enough identifying
    # information. This prevents over-flagging datasets that only
    # have order_id.
    if len(available_keys) >= 3:

        duplicate_key_mask = df.duplicated(
            subset=available_keys,
            keep=False,
        )

        duplicate_groups = (
            df.loc[duplicate_key_mask]
            .groupby(available_keys, dropna=False)
            .size()
        )

        suspicious_groups = duplicate_groups[
            duplicate_groups > 1
        ]

        potential_duplicate_groups = int(
            len(suspicious_groups)
        )

        potential_duplicate_count = int(
            duplicate_groups[
                duplicate_groups > 1
            ].sum()
        )

        if potential_duplicate_count > 0:
            issues.append(
                ValidationIssue(
                    category="DUPLICATES",
                    severity="INFO",
                    issue="Potential duplicate transactions",
                    count=potential_duplicate_count,
                    percentage=_percentage(
                        potential_duplicate_count,
                        row_count,
                    ),
                    explanation=(
                        "Multiple rows share the same transaction "
                        f"identity fields: {available_keys}. "
                        "These rows are flagged for review and are "
                        "not automatically deleted."
                    ),
                )
            )

    return {
        "issues": issues,
        "exact_duplicate_count": exact_duplicate_count,
        "potential_duplicate_count": potential_duplicate_count,
        "potential_duplicate_groups": potential_duplicate_groups,
        "duplicate_key_columns": available_keys,
    }


def calculate_quality_score(
    df: pd.DataFrame,
    schema_report: dict[str, Any],
    value_report: dict[str, Any],
    duplicate_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate an explainable data quality score from 0 to 100.

    Penalties are proportional to issue rates and capped so that
    one category cannot completely dominate the score.
    """

    score = 100.0
    penalties: list[dict[str, Any]] = []

    row_count = len(df)
    total_cells = max(df.shape[0] * df.shape[1], 1)

    # ---------------------------------------------------------
    # Missing values
    # Maximum penalty: 20 points
    # ---------------------------------------------------------
    missing_rate = (
        value_report["missing_value_count"]
        / total_cells
    )

    missing_penalty = min(
        20.0,
        missing_rate * 20.0,
    )

    if missing_penalty > 0:
        penalties.append(
            {
                "reason": "Missing values",
                "penalty": round(missing_penalty, 2),
            }
        )

    score -= missing_penalty

    # ---------------------------------------------------------
    # Exact duplicates
    # Maximum penalty: 15 points
    # ---------------------------------------------------------
    duplicate_rate = (
        duplicate_report["exact_duplicate_count"]
        / max(row_count, 1)
    )

    duplicate_penalty = min(
        15.0,
        duplicate_rate * 15.0,
    )

    if duplicate_penalty > 0:
        penalties.append(
            {
                "reason": "Exact duplicate rows",
                "penalty": round(duplicate_penalty, 2),
            }
        )

    score -= duplicate_penalty

    # ---------------------------------------------------------
    # Invalid dates
    # Maximum penalty: 20 points
    # ---------------------------------------------------------
    invalid_date_count = value_report["invalid_date_count"]

    date_denominator = max(
        row_count - value_report["missing_by_column"].get(
            "order_date",
            0,
        ),
        1,
    )

    invalid_date_rate = (
        invalid_date_count / date_denominator
    )

    date_penalty = min(
        20.0,
        invalid_date_rate * 20.0,
    )

    if date_penalty > 0:
        penalties.append(
            {
                "reason": "Invalid dates",
                "penalty": round(date_penalty, 2),
            }
        )

    score -= date_penalty

    # ---------------------------------------------------------
    # Invalid numeric values
    # Maximum penalty: 20 points
    # ---------------------------------------------------------
    numeric_columns = [
        column
        for column in NUMERIC_FIELDS
        if column in df.columns
    ]

    numeric_total = sum(
        int(df[column].notna().sum())
        for column in numeric_columns
    )

    invalid_numeric_rate = (
        value_report["invalid_numeric_count"]
        / max(numeric_total, 1)
    )

    numeric_penalty = min(
        20.0,
        invalid_numeric_rate * 20.0,
    )

    if numeric_penalty > 0:
        penalties.append(
            {
                "reason": "Invalid numeric values",
                "penalty": round(numeric_penalty, 2),
            }
        )

    score -= numeric_penalty

    # ---------------------------------------------------------
    # Business rule violations
    # Maximum penalty: 25 points
    # ---------------------------------------------------------
    business_invalid_count = (
        value_report["negative_quantity_count"]
        + value_report["negative_price_count"]
        + value_report["invalid_discount_count"]
    )

    business_rate = (
        business_invalid_count
        / max(row_count, 1)
    )

    business_penalty = min(
        25.0,
        business_rate * 25.0,
    )

    if business_penalty > 0:
        penalties.append(
            {
                "reason": "Business rule violations",
                "penalty": round(business_penalty, 2),
            }
        )

    score -= business_penalty

    # ---------------------------------------------------------
    # Missing required fields
    # Maximum penalty: 30 points per issue, capped at 60
    # ---------------------------------------------------------
    missing_required_count = len(
        schema_report["missing_required_fields"]
    )

    missing_price_field = (
        len(schema_report["available_price_fields"]) == 0
    )

    schema_penalty = 0.0

    if missing_required_count > 0:
        schema_penalty += min(
            60.0,
            missing_required_count * 30.0,
        )

    if missing_price_field:
        schema_penalty += 30.0

    if schema_penalty > 0:
        penalties.append(
            {
                "reason": "Missing required schema fields",
                "penalty": round(schema_penalty, 2),
            }
        )

    score -= schema_penalty

    score = max(
        0.0,
        min(100.0, score),
    )

    return {
        "score": round(score, 2),
        "penalties": penalties,
    }


def validate_dataset(
    df: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run the complete data quality validation pipeline.

    Returns a structured validation report.
    """

    schema_report = validate_schema(
        df,
        mapping=mapping,
    )

    value_report = validate_values(df)

    duplicate_report = detect_duplicates(df)

    all_issues = (
        schema_report["issues"]
        + value_report["issues"]
        + duplicate_report["issues"]
    )

    score_report = calculate_quality_score(
        df,
        schema_report,
        value_report,
        duplicate_report,
    )

    issue_records = [
        asdict(issue)
        for issue in all_issues
    ]

    error_count = sum(
        1
        for issue in all_issues
        if issue.severity == "ERROR"
    )

    warning_count = sum(
        1
        for issue in all_issues
        if issue.severity == "WARNING"
    )

    info_count = sum(
        1
        for issue in all_issues
        if issue.severity == "INFO"
    )

    return {
        "quality_score": score_report["score"],
        "penalties": score_report["penalties"],
        "issues": issue_records,
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "schema": schema_report,
        "values": value_report,
        "duplicates": duplicate_report,
        "is_valid": error_count == 0,
    }