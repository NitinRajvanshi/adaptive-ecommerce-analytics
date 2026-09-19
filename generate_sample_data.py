from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
ROW_COUNT = 20_000


def generate_sample_dataset() -> pd.DataFrame:
    """Generate a synthetic e-commerce transaction dataset."""

    rng = np.random.default_rng(RANDOM_SEED)

    products = {
        "Laptop": ("Electronics", 65000, 48000),
        "Smartphone": ("Electronics", 28000, 19000),
        "Headphones": ("Electronics", 3500, 2100),
        "Keyboard": ("Electronics", 1800, 1000),
        "Office Chair": ("Furniture", 8500, 5200),
        "Desk": ("Furniture", 12000, 7600),
        "Backpack": ("Accessories", 2200, 1200),
        "Shoes": ("Fashion", 4500, 2600),
        "T-Shirt": ("Fashion", 1200, 650),
        "Watch": ("Accessories", 5500, 3100),
    }

    product_names = list(products.keys())

    start_date = pd.Timestamp("2025-01-01")
    end_date = pd.Timestamp("2026-08-31")

    order_dates = pd.to_datetime(
        rng.integers(
            start_date.value // 10**9,
            end_date.value // 10**9,
            size=ROW_COUNT,
        ),
        unit="s",
    )

    selected_products = rng.choice(
        product_names,
        size=ROW_COUNT,
    )

    quantities = rng.integers(
        1,
        6,
        size=ROW_COUNT,
    )

    rows = []

    for index in range(ROW_COUNT):
        product = selected_products[index]

        category, selling_price, cost = products[product]

        quantity = int(quantities[index])

        discount = float(
            rng.choice(
                [0, 5, 10, 15, 20],
                p=[0.35, 0.20, 0.20, 0.15, 0.10],
            )
        )

        rows.append(
            {
                "order_id": f"ORD{index + 1:06d}",
                "order_date": order_dates[index].strftime("%Y-%m-%d"),
                "customer_id": f"CUST{rng.integers(1, 3501):05d}",
                "product_id": f"PROD{product_names.index(product) + 1:03d}",
                "product_name": product,
                "category": category,
                "quantity": quantity,
                "unit_price": selling_price,
                "discount": discount,
                "cost": cost * quantity,
                "region": rng.choice(
                    ["North", "South", "East", "West"],
                    p=[0.25, 0.25, 0.20, 0.30],
                ),
                "payment_method": rng.choice(
                    [
                        "UPI",
                        "Credit Card",
                        "Debit Card",
                        "Net Banking",
                        "COD",
                    ],
                    p=[0.35, 0.25, 0.15, 0.15, 0.10],
                ),
                "order_status": rng.choice(
                    [
                        "Completed",
                        "Cancelled",
                        "Pending",
                        "Returned",
                    ],
                    p=[0.86, 0.05, 0.05, 0.04],
                ),
            }
        )

    return pd.DataFrame(rows)


def introduce_data_quality_issues(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Add controlled data-quality issues."""

    rng = np.random.default_rng(RANDOM_SEED)

    # Missing customer IDs
    missing_customer_indices = rng.choice(
        df.index,
        size=100,
        replace=False,
    )

    df.loc[
        missing_customer_indices,
        "customer_id",
    ] = np.nan

    # Missing categories
    missing_category_indices = rng.choice(
        df.index,
        size=50,
        replace=False,
    )

    df.loc[
        missing_category_indices,
        "category",
    ] = np.nan

    # Inconsistent category capitalization
    category_indices = rng.choice(
        df.index,
        size=100,
        replace=False,
    )

    df.loc[
        category_indices,
        "category",
    ] = (
        df.loc[
            category_indices,
            "category",
        ]
        .astype("string")
        .str.lower()
    )

    # Invalid dates
    invalid_date_indices = rng.choice(
        df.index,
        size=10,
        replace=False,
    )

    df.loc[
        invalid_date_indices,
        "order_date",
    ] = "INVALID_DATE"

    # Invalid quantities
    invalid_quantity_indices = rng.choice(
        df.index,
        size=10,
        replace=False,
    )

    df.loc[
        invalid_quantity_indices,
        "quantity",
    ] = -1

    # Add 100 exact duplicate rows
    duplicate_rows = df.sample(
        n=100,
        random_state=RANDOM_SEED,
    )

    df = pd.concat(
        [
            df,
            duplicate_rows,
        ],
        ignore_index=True,
    )

    return df


def main() -> None:
    """Generate and save the sample dataset."""

    output_path = Path(
        "data",
        "sample_sales.csv",
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = generate_sample_dataset()

    df = introduce_data_quality_issues(df)

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"Sample dataset created: {output_path}"
    )

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(f"  - {column}")


if __name__ == "__main__":
    main()