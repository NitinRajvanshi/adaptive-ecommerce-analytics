from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

TABLE_NAME = "transactions"


def create_index_if_column_exists(
    engine: Engine,
    table_name: str,
    column_name: str,
    index_name: str,
) -> bool:
    """
    Create an index only when the requested column exists.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return False

    columns = [
        column["name"]
        for column in inspector.get_columns(table_name)
    ]

    if column_name not in columns:
        return False

    with engine.begin() as connection:
        connection.execute(
            text(
                f'CREATE INDEX IF NOT EXISTS '
                f'"{index_name}" '
                f'ON "{table_name}" '
                f'("{column_name}")'
            )
        )

    return True


def create_indexes(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> dict[str, bool]:
    """
    Create useful indexes for analytical queries.

    Indexes are created only for columns that actually exist.
    """

    index_definitions = {
        "idx_transactions_order_date": "order_date",
        "idx_transactions_customer_id": "customer_id",
        "idx_transactions_product_id": "product_id",
        "idx_transactions_category": "category",
        "idx_transactions_region": "region",
        "idx_transactions_order_status": "order_status",
    }

    results = {}

    for index_name, column_name in index_definitions.items():

        results[index_name] = create_index_if_column_exists(
            engine=engine,
            table_name=table_name,
            column_name=column_name,
            index_name=index_name,
        )

    return results


def get_indexes(
    engine: Engine,
    table_name: str = TABLE_NAME,
) -> list[dict]:
    """
    Return database indexes for a table.
    """

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return []

    return inspector.get_indexes(table_name)