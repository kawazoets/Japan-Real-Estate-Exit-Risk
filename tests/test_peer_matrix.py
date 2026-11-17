from src.peer_matrix import build
from src.cohort import GROUPS, CONFIG, IR, COMPARISON, read

def test_fixed_fifteen_peer_rows_with_no_false_resale_claim():
    groups=read(GROUPS)
    rows=build(groups,read(IR),read(COMPARISON))
    assert len(rows)==15
    assert len({r["group_id"] for r in rows})==15
    assert len([r for r in rows if r["cohort"]=="core"])==6
    assert len([r for r in rows if r["cohort"]=="comparison"])==9
    assert all(r["tokyo_used_condo_resale_inference"]=="NOT_ESTABLISHED" for r in rows)

def test_2026_dear_life_property_growth_stays_in_comparison_group():
    rows=build(read(GROUPS),read(IR),read(COMPARISON))
    d=next(x for x in rows if x["group_id"]=="dear_life")
    assert d["stock_yoy_pct"]==82.9
    assert d["cohort"]=="comparison"
    assert d["revenue_yoy_pct"]==""

def test_missing_stock_does_not_become_zero():
    rows=build(read(GROUPS),read(IR),read(COMPARISON))
    fuji=next(x for x in rows if x["group_id"]=="fuji_jutaku")
    assert fuji["stock_yoy_pct"]==""
    assert fuji["data_status"]=="PUBLIC_SOURCE_TRANSCRIBED_UNREVIEWED"
