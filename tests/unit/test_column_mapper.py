import pandas as pd
from etl.column_mapper import (
    apply_mapping,
    create_mapping_dict,
)


def test_create_mapping_dict():
    mapping_df = pd.DataFrame({
        "source_column": [
            "Order ID",
            "Quantity",
            "Price",
        ],
        "canonical_field": [
            "order_id",
            "quantity",
            "unit_price",
        ],
    })

    mapping = create_mapping_dict(mapping_df)

    assert isinstance(mapping, dict)
    assert mapping["Order ID"] == "order_id"
    assert mapping["Quantity"] == "quantity"
    assert mapping["Price"] == "unit_price"


def test_apply_mapping():
    df = pd.DataFrame({
        "Order ID": ["O1"],
        "Quantity": [2],
        "Price": [100],
    })

    mapping = {
        "Order ID": "order_id",
        "Quantity": "quantity",
        "Price": "unit_price",
    }

    result = apply_mapping(df, mapping)

    assert "order_id" in result.columns
    assert "quantity" in result.columns
    assert "unit_price" in result.columns