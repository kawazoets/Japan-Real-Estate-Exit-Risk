import pytest
from copy import deepcopy
from src.segment_evidence import read,verify

def test_price_band_sales_stock_and_conversion_controls():
    assert verify(read())

def test_cannot_blend_tokyo_market_with_companywide_listings():
    rows=deepcopy(read())
    r=next(x for x in rows if x["geography"]=="Tokyo_prefecture")
    r["limitation"]="NOT_TOKYO_EXCLUSIVE"
    with pytest.raises(ValueError):
        verify(rows)

def test_company_active_sale_stock_is_exactly_484():
    rows=deepcopy(read())
    r=next(x for x in rows if x["metric"]=="actively_marketed_inventory")
    r["amount"]="4420"
    with pytest.raises(ValueError):
        verify(rows)
