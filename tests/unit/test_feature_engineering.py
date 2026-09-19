import pandas as pd
from etl.feature_engineering import engineer_features


def test_feature_engineering():
    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_date": pd.to_datetime([
            "2026-01-01",
            "2026-01-02",
        ]),
        "quantity": [2, 3],
        "unit_price": [100, 200],
    })

    featured, report = engineer_features(df)

    assert isinstance(featured, pd.DataFrame)
    assert isinstance(report, dict)
    assert len(featured) == 2