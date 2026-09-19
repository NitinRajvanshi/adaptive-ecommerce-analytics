import pandas as pd
from etl.profiler import profile_dataset


def test_profile_dataset():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O2"],
        "quantity": [1, 2, 2],
        "unit_price": [100, 200, 200],
    })

    profile = profile_dataset(df)

    assert isinstance(profile, dict)

    # The profiler should return column-level profiling information.
    assert profile

    # Verify that the expected source columns are represented
    # somewhere in the profiling result.
    profile_text = str(profile).lower()

    assert "order_id" in profile_text
    assert "quantity" in profile_text
    assert "unit_price" in profile_text