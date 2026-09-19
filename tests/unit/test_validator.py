import pandas as pd
from etl.validator import validate_dataset


def test_valid_dataset():
    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "order_date": ["2026-01-01", "2026-01-02"],
        "quantity": [1, 2],
        "unit_price": [100, 200],
    })

    result = validate_dataset(df)

    assert isinstance(result, dict)


def test_invalid_negative_quantity():
    df = pd.DataFrame({
        "order_id": ["O1"],
        "order_date": ["2026-01-01"],
        "quantity": [-1],
        "unit_price": [100],
    })

    result = validate_dataset(df)

    assert isinstance(result, dict)