import pandas as pd
from analytics.metrics import calculate_all_metrics
from sqlalchemy import create_engine


def test_metrics():
    engine = create_engine("sqlite:///:memory:")

    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "quantity": [2, 3],
        "unit_price": [100, 200],
    })

    df["sales_amount"] = df["quantity"] * df["unit_price"]

    df.to_sql(
        "transactions",
        engine,
        index=False,
        if_exists="replace",
    )

    metrics = calculate_all_metrics(engine)

    assert isinstance(metrics, dict)