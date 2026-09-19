import pandas as pd
from etl.schema_detector import detect_schema


def test_schema_detection():
    df = pd.DataFrame({
        "Order ID": ["O1", "O2"],
        "Order Date": ["2026-01-01", "2026-01-02"],
        "Quantity": [2, 3],
        "Unit Price": [100, 200],
    })

    result = detect_schema(df)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty

    assert "source_column" in result.columns
    assert "detected_field" in result.columns

    detected_fields = result["detected_field"].dropna().tolist()

    assert "order_id" in detected_fields
    assert "order_date" in detected_fields
    assert "quantity" in detected_fields
    assert "unit_price" in detected_fields