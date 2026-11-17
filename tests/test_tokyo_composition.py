import pytest
from src.tokyo_composition import compute

def observations():
    return [
      {"month":"2025-10","region":"Tokyo_wards","contracts_count":"1836","mean_contract_sqm_price_man_yen":"135.03"},
      {"month":"2025-10","region":"Tama","contracts_count":"398","mean_contract_sqm_price_man_yen":"56.60"},
      {"month":"2025-10","region":"Tokyo_total","contracts_count":"2234","mean_contract_sqm_price_man_yen":"121.06"},
      {"month":"2026-10","region":"Tokyo_wards","contracts_count":"1343","mean_contract_sqm_price_man_yen":"129.69"},
      {"month":"2026-10","region":"Tama","contracts_count":"327","mean_contract_sqm_price_man_yen":"57.63"},
      {"month":"2026-10","region":"Tokyo_total","contracts_count":"1670","mean_contract_sqm_price_man_yen":"115.58"},
    ]

def test_ward_tama_decomposition():
    d=compute(observations())
    assert d["within_region_share_pct"]==76.78
    assert d["ward_tama_mix_share_pct"]==23.22
    assert d["ward_contract_share_from_pct"]==82.18
    assert d["ward_contract_share_to_pct"]==80.42
    assert abs(d["change_man_yen_sqm"]+5.4772)<1e-3

def test_refuse_ward_tama_count_mismatch():
    rows=observations()
    rows[0]["contracts_count"]="1000"
    with pytest.raises(ValueError): compute(rows)

def test_refuse_inconsistent_published_mean():
    rows=observations()
    rows[2]["mean_contract_sqm_price_man_yen"]="95.00"
    with pytest.raises(ValueError): compute(rows)
