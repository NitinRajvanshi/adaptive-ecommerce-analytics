import pandas as pd
from analytics.insights import generate_all_insights
from sqlalchemy import create_engine


def test_generate_insights():
    engine = create_engine("sqlite:///:memory:")

    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "order_date": pd.to_datetime([
            "2026-01-01",
            "2026-01-02",
            "2026-02-01",
        ]),
        "quantity": [1, 2, 3],
        "unit_price": [100, 200, 300],
        "sales_amount": [100, 400, 900],
    })

    df.to_sql(
        "transactions",
        engine,
        index=False,
        if_exists="replace",
    )

    result = generate_all_insights(engine)

    assert result is not None