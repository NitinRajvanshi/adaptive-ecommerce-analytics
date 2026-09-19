from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_PATH = Path(
    "database/ecommerce_analytics.db"
)


def get_database_url(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """
    Build a SQLite database URL.
    """

    path = Path(database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return f"sqlite:///{path.as_posix()}"


def create_database_engine(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Engine:
    """
    Create a SQLAlchemy SQLite engine.
    """

    database_url = get_database_url(
        database_path
    )

    engine = create_engine(
        database_url,
        future=True,
    )

    return engine


def test_database_connection(
    engine: Engine,
) -> bool:
    """
    Test whether the database connection works.
    """

    try:

        with engine.connect() as connection:

            connection.exec_driver_sql(
                "SELECT 1"
            )

        return True

    except Exception:
        return False