import pandas as pd
from database.schema import load_dataframe_to_database
from sqlalchemy import create_engine


def test_database_load():
    engine = create_engine("sqlite:///:memory:")

    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "quantity": [1, 2],
        "unit_price": [100, 200],
    })

    load_dataframe_to_database(df, engine=engine)

    result = pd.read_sql(
        "SELECT * FROM transactions",
        engine,
    )

    assert len(result) == 2