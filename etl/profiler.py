from __future__ import annotations

from typing import Any

import pandas as pd

DATE_PARSE_THRESHOLD = 0.80


def calculate_memory_usage(df: pd.DataFrame) -> float:
    """
    Calculate the approximate memory usage of a DataFrame in MB.

    Args:
        df: DataFrame to analyze.

    Returns:
        Memory usage in megabytes.
    """

    memory_bytes = df.memory_usage(
        index=True,
        deep=True,
    ).sum()

    return float(memory_bytes / (1024 * 1024))


def calculate_missing_values(df: pd.DataFrame) -> int:
    """
    Calculate the total number of missing cells.

    Args:
        df: DataFrame to analyze.

    Returns:
        Total missing cell count.
    """

    return int(df.isna().sum().sum())


def calculate_duplicate_rows(df: pd.DataFrame) -> int:
    """
    Calculate the number of exact duplicate rows.

    Args:
        df: DataFrame to analyze.

    Returns:
        Number of duplicate rows.
    """

    return int(df.duplicated().sum())


def detect_date_like_column(
    series: pd.Series,
) -> bool:
    """
    Determine whether a column is likely to contain dates.

    The column is considered date-like when at least 80% of
    non-null values can be parsed as dates.

    Args:
        series: Column to inspect.

    Returns:
        True when the column appears to be date-like.
    """

    non_null_values = series.dropna()

    if non_null_values.empty:
        return False

    if pd.api.types.is_datetime64_any_dtype(series):
        return True

    if pd.api.types.is_numeric_dtype(series):
        return False

    parsed_dates = pd.to_datetime(
        non_null_values,
        errors="coerce",
        format="mixed",
    )

    parse_success_rate = parsed_dates.notna().mean()

    return bool(
        parse_success_rate >= DATE_PARSE_THRESHOLD
    )


def detect_column_type(
    series: pd.Series,
) -> str:
    """
    Classify a column as numeric, date-like, categorical,
    boolean, or other.

    Args:
        series: Column to classify.

    Returns:
        Detected column type.
    """

    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    if detect_date_like_column(series):
        return "date-like"

    if (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
        or pd.api.types.is_categorical_dtype(series)
    ):
        return "categorical"

    return "other"


def profile_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate column-level profiling information.

    Args:
        df: DataFrame to profile.

    Returns:
        DataFrame containing one row per source column.
    """

    records: list[dict[str, Any]] = []

    row_count = len(df)

    for column in df.columns:
        series = df[column]

        missing_count = int(series.isna().sum())

        if row_count > 0:
            missing_percentage = (
                missing_count / row_count
            ) * 100
        else:
            missing_percentage = 0.0

        records.append(
            {
                "column": str(column),
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": round(
                    missing_percentage,
                    2,
                ),
                "unique_values": int(
                    series.nunique(dropna=True)
                ),
                "detected_type": detect_column_type(
                    series
                ),
            }
        )

    return pd.DataFrame(records)


def profile_dataset(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """
    Generate a complete profile of a DataFrame.

    Args:
        df: DataFrame to profile.

    Returns:
        Dictionary containing dataset-level and
        column-level profiling information.
    """

    column_profile = profile_columns(df)

    numeric_columns = column_profile.loc[
        column_profile["detected_type"] == "numeric",
        "column",
    ].tolist()

    categorical_columns = column_profile.loc[
        column_profile["detected_type"] == "categorical",
        "column",
    ].tolist()

    date_columns = column_profile.loc[
        column_profile["detected_type"] == "date-like",
        "column",
    ].tolist()

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "memory_usage_mb": round(
            calculate_memory_usage(df),
            2,
        ),
        "missing_value_count": calculate_missing_values(
            df
        ),
        "duplicate_row_count": calculate_duplicate_rows(
            df
        ),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_columns": date_columns,
        "column_profile": column_profile,
    }