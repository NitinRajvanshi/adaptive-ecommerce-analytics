import pandas as pd
from etl.cleaner import clean_dataset
from etl.feature_engineering import engineer_features
from etl.transformer import transform_dataset


def test_etl_pipeline():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "order_date": [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ],
        "quantity": [1, 2, 3],
        "unit_price": [100, 200, 300],
    })

    cleaned, cleaning_report = clean_dataset(df)

    transformed, transformation_report = transform_dataset(
        cleaned
    )

    featured, feature_report = engineer_features(
        transformed
    )

    assert len(featured) > 0
    assert isinstance(cleaning_report, dict)
    assert isinstance(transformation_report, dict)
    assert isinstance(feature_report, dict)