from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


def prepare_dataframe_for_database(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare a dataframe for SQLite storage.

    Datetime columns are converted to strings because SQLite
    does not have a dedicated datetime storage type.
    """

    prepared = df.copy()

    for column in prepared.columns:

        if pd.api.types.is_datetime64_any_dtype(
            prepared[column]
        ):

            prepared[column] = (
                prepared[column]
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

        elif str(
            prepared[column].dtype
        ).startswith("string"):

            prepared[column] = (
                prepared[column]
                .astype(object)
            )

    return prepared


def load_dataframe_to_database(
    df: pd.DataFrame,
    engine: Engine,
    table_name: str = TABLE_NAME,
    if_exists: str = "replace",
) -> dict[str, Any]:
    """
    Load a dataframe into SQLite using Pandas + SQLAlchemy.

    Returns a load report.
    """

    prepared = prepare_dataframe_for_database(
        df
    )

    prepared.to_sql(
        table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
    )

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    return {
        "table_name": table_name,
        "rows_loaded": len(prepared),
        "columns_loaded": len(prepared.columns),
        "table_created": table_name in tables,
        "columns": prepared.columns.tolist(),
    }


def get_table_columns(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[str]:
    """
    Return column names for a database table.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return []

    columns = inspector.get_columns(
        table_name
    )

    return [
        column["name"]
        for column in columns
    ]


def get_table_row_count(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> int:
    """
    Return the number of rows in a table.
    """

    with engine.connect() as connection:

        result = connection.exec_driver_sql(
            f'SELECT COUNT(*) FROM "{table_name}"'
        )

        return int(
            result.scalar_one()
        )