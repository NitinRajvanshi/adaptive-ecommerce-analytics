from __future__ import annotations

from typing import Any

import pandas as pd

from etl.schema_detector import (
    CANONICAL_FIELDS,
    detect_column_candidates,
)


def build_initial_mapping(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build an initial source-to-canonical mapping using
    the highest-confidence schema detection result.

    Args:
        df: Source DataFrame.

    Returns:
        DataFrame containing the initial mapping.
    """

    candidates = detect_column_candidates(df)

    records: list[dict[str, Any]] = []

    for source_column, column_candidates in candidates.items():

        if not column_candidates:
            continue

        best = column_candidates[0]

        records.append(
            {
                "source_column": source_column,
                "canonical_field": best[
                    "detected_field"
                ],
                "confidence": best[
                    "confidence"
                ],
                "confidence_percent": (
                    f"{best['confidence'] * 100:.1f}%"
                ),
                "confidence_level": best[
                    "confidence_level"
                ],
                "match_reason": best[
                    "match_reason"
                ],
            }
        )

    return pd.DataFrame(records)


def get_available_canonical_fields() -> list[str]:
    """
    Return all supported canonical fields.

    Returns:
        List of canonical field names.
    """

    return list(CANONICAL_FIELDS.keys())


def validate_mapping(
    mapping_df: pd.DataFrame,
) -> tuple[bool, list[str]]:
    """
    Validate a proposed source-to-canonical mapping.

    Validation rules:

    - Every source column should have a mapping.
    - A canonical field should not be assigned to multiple
      source columns.

    Args:
        mapping_df: Mapping DataFrame.

    Returns:
        Tuple containing validation status and error messages.
    """

    errors: list[str] = []

    required_columns = {
        "source_column",
        "canonical_field",
    }

    missing_columns = (
        required_columns
        - set(mapping_df.columns)
    )

    if missing_columns:
        errors.append(
            "Mapping table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

        return False, errors

    if mapping_df["source_column"].isna().any():
        errors.append(
            "One or more source columns are empty."
        )

    if mapping_df["canonical_field"].isna().any():
        errors.append(
            "One or more canonical fields are empty."
        )

    if (
        mapping_df["canonical_field"]
        .astype(str)
        .str.strip()
        .eq("")
        .any()
    ):
        errors.append(
            "One or more canonical fields are blank."
        )

    duplicated_canonical_fields = (
        mapping_df[
            mapping_df["canonical_field"]
            .duplicated(keep=False)
        ]["canonical_field"]
        .astype(str)
        .unique()
        .tolist()
    )

    if duplicated_canonical_fields:
        errors.append(
            "Multiple source columns are mapped to "
            "the same canonical field: "
            + ", ".join(
                sorted(
                    duplicated_canonical_fields
                )
            )
        )

    return (
        len(errors) == 0,
        errors,
    )


def create_mapping_dict(
    mapping_df: pd.DataFrame,
) -> dict[str, str]:
    """
    Convert a validated mapping DataFrame into
    a source-to-canonical dictionary.

    Args:
        mapping_df: Validated mapping DataFrame.

    Returns:
        Dictionary such as:
        {"Transaction_ID": "order_id"}
    """

    is_valid, errors = validate_mapping(
        mapping_df
    )

    if not is_valid:
        raise ValueError(
            "Invalid mapping: "
            + " | ".join(errors)
        )

    return dict(
        zip(
            mapping_df["source_column"].astype(str),
            mapping_df["canonical_field"].astype(str),
        )
    )


def apply_mapping(
    df: pd.DataFrame,
    mapping: dict[str, str],
) -> pd.DataFrame:
    """
    Apply a confirmed source-to-canonical mapping.

    Columns that are not included in the mapping are
    retained using their original names.

    Args:
        df: Source DataFrame.
        mapping: Source-to-canonical mapping dictionary.

    Returns:
        DataFrame with mapped column names.
    """

    missing_source_columns = [
        source_column
        for source_column in mapping
        if source_column not in df.columns
    ]

    if missing_source_columns:
        raise ValueError(
            "Mapping references source columns that "
            "do not exist in the dataset: "
            + ", ".join(missing_source_columns)
        )

    mapped_df = df.rename(
        columns=mapping
    ).copy()

    return mapped_df


def get_low_confidence_mappings(
    mapping_df: pd.DataFrame,
    threshold: float = 0.70,
) -> pd.DataFrame:
    """
    Return mappings below a confidence threshold.

    Args:
        mapping_df: Mapping DataFrame.
        threshold: Minimum acceptable confidence.

    Returns:
        DataFrame containing low-confidence mappings.
    """

    return mapping_df[
        mapping_df["confidence"] < threshold
    ].copy()