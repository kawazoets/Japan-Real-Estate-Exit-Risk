import csv
import io
import pytest
from src.cohort import validate_groups,validate_primary_sources,build,render

def groups():
    text="""group_id,canonical_company,tickers,cohort
g01,Company 01,2975,core
g02,Company 02,8940|463A,core
g03,Company 03,3294,core
g04,Company 04,3299,core
g05,Company 05,2991,core
g06,Company 06,8860,core
g07,Company 07,8923,comparison
g08,Company 08,3277,comparison
g09,Company 09,3297,comparison
g10,Company 10,3475,comparison
g11,Company 11,3486,comparison
g12,Company 12,3245,comparison
g13,Company 13,2982,comparison
g14,Company 14,3248,comparison
g15,Company 15,8844,comparison
"""
    return list(csv.DictReader(io.StringIO(text)))

def registered(gs):
    return [{"ticker":symbol} for g in gs for symbol in g["tickers"].split("|")]

def test_original_scope_15_groups_and_16_symbols_is_enforced():
    gs=groups();registered_rows=registered(gs)
    validate_groups(gs,registered_rows)
    assert len(build(gs,registered_rows,[],[],[],[]))==45
    with pytest.raises(ValueError):
        validate_groups(gs[:2],registered_rows)

def test_old_and_new_intellex_are_one_group():
    gs=groups()
    ir=[{"ticker":"8940","fiscal_end":"2025-05-31","inventory_jpy":"1"},
        {"ticker":"463A","fiscal_end":"2026-05-31","inventory_jpy":"2"}]
    rows=build(gs,registered(gs),[],[],ir,[])
    intellex=[r for r in rows if r["group_id"]=="g02"]
    assert len(intellex)==3
    assert intellex[1]["primary_ir_rows"]==1
    assert intellex[2]["primary_ir_rows"]==1

def test_partial_primary_ir_data_is_never_promoted_to_verified():
    gs=groups();ir=[{"ticker":"2975","fiscal_end":"2025-11-30","inventory_jpy":"200"}]
    rows=build(gs,registered(gs),[],[],ir,[])
    match=next(r for r in rows if r["group_id"]=="g01" and r["fiscal_year"]==2025)
    assert match["coverage_state"]=="IR_PARTIAL_UNAUDITED"
    assert match["verified_full_year_rows"]==0
    assert "NO silent reduction" in render(rows)

def test_primary_source_index_cannot_drop_13_companies():
    gs=groups()
    good=[{"group_id":g["group_id"],"primary_document_or_ir_url":"https://example.com/ir"} for g in gs]
    validate_primary_sources(gs,good)
    with pytest.raises(ValueError):
        validate_primary_sources(gs,good[:2])
