"""Deterministic, clearly synthetic dataset for first-run product exploration."""
from __future__ import annotations
import numpy as np
import pandas as pd

def build_sample_dataset(rows: int = 120, seed: int = 17) -> pd.DataFrame:
    """Return reproducible fictional order records; never represents real customers."""
    if not isinstance(rows, int) or rows < 1 or rows > 5000:
        raise ValueError("rows must be an integer between 1 and 5000")
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=180, freq="D")
    products = np.array(["Accessories", "Home", "Electronics", "Office"])
    product = rng.choice(products, rows)
    units = rng.integers(1, 9, rows)
    base = pd.Series(product).map({"Accessories": 24.0, "Home": 68.0, "Electronics": 145.0, "Office": 39.0}).to_numpy()
    discount = rng.choice([0.0, .05, .10, .15, .20], rows, p=[.30, .20, .25, .15, .10])
    revenue = np.round(units * base * (1 - discount) * rng.uniform(.88, 1.12, rows), 2)
    frame = pd.DataFrame({
        "order_id": [f"SYN-{i:05d}" for i in range(1, rows + 1)],
        "order_date": rng.choice(dates, rows),
        "region": rng.choice(["North", "South", "East", "West"], rows),
        "sales_channel": rng.choice(["Online", "Retail", "Partner"], rows, p=[.55, .30, .15]),
        "customer_segment": rng.choice(["New", "Returning", "Business"], rows),
        "product_category": product, "units": units, "discount_rate": discount,
        "revenue": revenue,
        "order_status": rng.choice(["Completed", "Pending", "Returned"], rows, p=[.82, .12, .06]),
    })
    return frame.sort_values("order_date", kind="stable").reset_index(drop=True)

SAMPLE_DATASET_NOTICE = ("Synthetic demonstration data generated locally for product exploration. "
                         "It is fictional and must not be treated as real business or customer evidence.")