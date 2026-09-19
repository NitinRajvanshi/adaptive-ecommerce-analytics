from __future__ import annotations

import time
from typing import Any

import pandas as pd
from sqlalchemy import text

TABLE_NAME = "transactions"


def table_exists(engine, table_name: str = TABLE_NAME) -> bool:
    """Check whether a table exists."""

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
            {"table_name": table_name},
        ).fetchone()

    return result is not None


def get_available_columns(
    engine,
    table_name: str = TABLE_NAME,
) -> list[str]:
    """Return available table columns."""

    if not table_exists(engine, table_name):
        return []

    with engine.connect() as connection:
        result = connection.execute(
            text(f'PRAGMA table_info("{table_name}")')
        ).fetchall()

    return [row[1] for row in result]


def get_existing_indexes(
    engine,
    table_name: str = TABLE_NAME,
) -> pd.DataFrame:
    """Return indexes currently defined on the table."""

    if not table_exists(engine, table_name):
        return pd.DataFrame(
            columns=[
                "index_name",
                "unique",
                "origin",
                "partial",
            ]
        )

    with engine.connect() as connection:
        indexes = connection.execute(
            text(f'PRAGMA index_list("{table_name}")')
        ).fetchall()

    records = []

    for row in indexes:
        records.append(
            {
                "index_name": row[1],
                "unique": bool(row[2]),
                "origin": row[3],
                "partial": bool(row[4]),
            }
        )

    return pd.DataFrame(records)


def get_indexed_columns(
    engine,
    table_name: str = TABLE_NAME,
) -> list[str]:
    """Return columns that currently have indexes."""

    indexes = get_existing_indexes(
        engine,
        table_name,
    )

    if indexes.empty:
        return []

    indexed_columns = []

    with engine.connect() as connection:
        for index_name in indexes["index_name"]:

            rows = connection.execute(
                text(
                    f'PRAGMA index_info("{index_name}")'
                )
            ).fetchall()

            for row in rows:
                if row[2] is not None:
                    indexed_columns.append(row[2])

    return sorted(set(indexed_columns))


def execute_timed_query(
    engine,
    query: str,
) -> dict[str, Any]:
    """Execute a SELECT query and measure execution time."""

    query_clean = query.strip()

    if not query_clean:
        raise ValueError("Query cannot be empty.")

    if not query_clean.lower().startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    start_time = time.perf_counter()

    with engine.connect() as connection:

        result = connection.execute(
            text(query_clean)
        )

        rows = result.fetchall()
        columns = list(result.keys())

    elapsed = time.perf_counter() - start_time

    dataframe = pd.DataFrame(
        rows,
        columns=columns,
    )

    return {
        "query": query_clean,
        "execution_time_seconds": elapsed,
        "row_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "dataframe": dataframe,
    }


def compare_query_performance(
    engine,
    query: str,
    runs: int = 3,
) -> dict[str, Any]:
    """Run the same query multiple times."""

    if runs < 1:
        raise ValueError(
            "runs must be at least 1."
        )

    timings = []

    for _ in range(runs):

        result = execute_timed_query(
            engine,
            query,
        )

        timings.append(
            result["execution_time_seconds"]
        )

    return {
        "query": query.strip(),
        "runs": runs,
        "average_time_seconds": (
            sum(timings) / len(timings)
        ),
        "minimum_time_seconds": min(timings),
        "maximum_time_seconds": max(timings),
        "timings": timings,
    }


def explain_query_plan(
    engine,
    query: str,
) -> pd.DataFrame:
    """Return SQLite query execution plan."""

    query_clean = query.strip()

    if not query_clean.lower().startswith("select"):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    explain_query = (
        f"EXPLAIN QUERY PLAN {query_clean}"
    )

    with engine.connect() as connection:

        result = connection.execute(
            text(explain_query)
        )

        rows = result.fetchall()
        columns = list(result.keys())

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def create_test_index(
    engine,
    column_name: str,
    table_name: str = TABLE_NAME,
) -> str:
    """
    Create a non-unique test index for a valid
    database column.
    """

    available_columns = get_available_columns(
        engine,
        table_name,
    )

    if column_name not in available_columns:
        raise ValueError(
            f"Column '{column_name}' does not exist."
        )

    index_name = (
        f"idx_performance_{column_name}"
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                f'''
                CREATE INDEX IF NOT EXISTS
                "{index_name}"
                ON "{table_name}"
                ("{column_name}")
                '''
            )
        )

    return index_name


def drop_test_index(
    engine,
    column_name: str,
) -> str:
    """Remove the performance test index."""

    index_name = (
        f"idx_performance_{column_name}"
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                f'DROP INDEX IF EXISTS "{index_name}"'
            )
        )

    return index_name


def clear_test_indexes(
    engine,
    table_name: str = TABLE_NAME,
) -> int:
    """
    Remove only indexes created by the
    performance demonstration.
    """

    indexes = get_existing_indexes(
        engine,
        table_name,
    )

    if indexes.empty:
        return 0

    removed = 0

    with engine.begin() as connection:

        for index_name in indexes["index_name"]:

            if str(index_name).startswith(
                "idx_performance_"
            ):

                connection.execute(
                    text(
                        f'DROP INDEX IF EXISTS '
                        f'"{index_name}"'
                    )
                )

                removed += 1

    return removed


def compare_index_performance(
    engine,
    query: str,
    column_name: str,
    runs: int = 3,
) -> dict[str, Any]:
    """
    Compare query execution before and after
    creating an index.

    Only the test index created by this function
    is removed/recreated. Existing project indexes
    are not removed.
    """

    if runs < 1:
        raise ValueError(
            "runs must be at least 1."
        )

    available_columns = get_available_columns(
        engine
    )

    if column_name not in available_columns:
        raise ValueError(
            f"Column '{column_name}' "
            "does not exist."
        )

    # Remove an existing performance-test index
    # so the baseline is genuinely unindexed.
    drop_test_index(
        engine,
        column_name,
    )

    # Baseline measurement
    before = compare_query_performance(
        engine,
        query,
        runs=runs,
    )

    before_plan = explain_query_plan(
        engine,
        query,
    )

    # Create test index
    index_name = create_test_index(
        engine,
        column_name,
    )

    # Indexed measurement
    after = compare_query_performance(
        engine,
        query,
        runs=runs,
    )

    after_plan = explain_query_plan(
        engine,
        query,
    )

    before_time = (
        before["average_time_seconds"]
    )

    after_time = (
        after["average_time_seconds"]
    )

    if before_time > 0:
        improvement_percentage = (
            (before_time - after_time)
            / before_time
        ) * 100
    else:
        improvement_percentage = 0.0

    return {
        "query": query.strip(),
        "column": column_name,
        "index_name": index_name,
        "runs": runs,
        "before": before,
        "after": after,
        "before_plan": before_plan,
        "after_plan": after_plan,
        "before_average_seconds": before_time,
        "after_average_seconds": after_time,
        "improvement_percentage": (
            improvement_percentage
        ),
    }


def get_performance_summary(
    engine,
) -> dict[str, Any]:
    """Return database performance information."""

    columns = get_available_columns(
        engine
    )

    indexes = get_existing_indexes(
        engine
    )

    return {
        "table_exists": table_exists(engine),
        "column_count": len(columns),
        "columns": columns,
        "index_count": len(indexes),
        "indexes": indexes,
        "indexed_columns": get_indexed_columns(
            engine
        ),
    }