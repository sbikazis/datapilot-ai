import pandas as pd
import pytest
from sample_workspace import SAMPLE_DATASET_NOTICE, build_sample_dataset

def test_sample_is_reproducible_and_has_expected_schema():
    first, second = build_sample_dataset(), build_sample_dataset()
    pd.testing.assert_frame_equal(first, second)
    assert list(first.columns) == ["order_id", "order_date", "region", "sales_channel", "customer_segment", "product_category", "units", "discount_rate", "revenue", "order_status"]

def test_sample_has_valid_types_and_fictional_identifiers():
    frame = build_sample_dataset(rows=40)
    assert len(frame) == 40
    assert pd.api.types.is_datetime64_any_dtype(frame["order_date"])
    assert pd.api.types.is_numeric_dtype(frame["revenue"])
    assert frame["order_id"].str.startswith("SYN-").all()
    assert frame["revenue"].gt(0).all()
    assert "fictional" in SAMPLE_DATASET_NOTICE.lower()

@pytest.mark.parametrize("rows", [0, -1, 5001, 1.5, "20"])
def test_invalid_sample_size_is_rejected(rows):
    with pytest.raises(ValueError):
        build_sample_dataset(rows=rows)