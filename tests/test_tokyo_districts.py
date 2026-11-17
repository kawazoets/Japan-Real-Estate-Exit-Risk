import pytest
from src.tokyo_districts import read,validate

def test_all_five_wards_districts_balance_to_official_totals():
    assert validate(read())

def test_reject_missing_district():
    with pytest.raises(ValueError):
        validate(read()[:-1])

def test_reject_silent_promotion_to_primary_source():
    rows=read()
    rows[0]["audit_status"]="PRIMARY_VERIFIED"
    with pytest.raises(ValueError):
        validate(rows)

def test_reject_false_inventory_ratio():
    rows=read()
    rows[0]["stock_to_monthly_contract_ratio"]="7.00"
    with pytest.raises(ValueError):
        validate(rows)
