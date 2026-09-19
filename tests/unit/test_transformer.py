import pandas as pd
from etl.transformer import transform_dataset


def test_transform_dataset():
    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_date": ["2026-01-01", "2026-01-02"],
        "quantity": [2, 3],
        "unit_price": [100, 200],
    })

    transformed, report = transform_dataset(df)

    assert isinstance(transformed, pd.DataFrame)
    assert isinstance(report, dict)
    assert len(transformed) == 2