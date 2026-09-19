import pandas as pd
from etl.cleaner import clean_dataset


def test_clean_dataset():
    df = pd.DataFrame({
        "order_id": ["O1", "O1", "O2"],
        "order_date": ["2026-01-01", "2026-01-01", "2026-01-02"],
        "quantity": [1, 1, 2],
        "unit_price": [100, 100, 200],
    })

    cleaned, report = clean_dataset(df)

    assert isinstance(cleaned, pd.DataFrame)
    assert isinstance(report, dict)
    assert len(cleaned) <= len(df)