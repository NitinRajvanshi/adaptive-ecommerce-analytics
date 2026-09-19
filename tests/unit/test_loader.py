import pandas as pd
import pytest
from etl.loader import (
    DataLoadError,
    get_dataset_summary,
    load_csv,
)


def test_load_csv(tmp_path):
    file_path = tmp_path / "sample.csv"

    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "quantity": [2, 3],
        "unit_price": [100, 200],
    })

    df.to_csv(file_path, index=False)

    loaded = load_csv(file_path)

    assert len(loaded) == 2
    assert "order_id" in loaded.columns


def test_invalid_extension(tmp_path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello")

    with pytest.raises(DataLoadError):
        load_csv(file_path)


def test_dataset_summary():
    df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "quantity": [1, 2],
    })

    summary = get_dataset_summary(df)

    assert summary["rows"] == 2
    assert summary["columns"] == 2