"""Prevent silent loss of any of nine comparison groups.

Comparison-group stock cannot be treated as Tokyo used-condominium resale inventory.
"""
import csv
from src.cohort import GROUPS, COMPARISON, read, build
from src.cohort import CONFIG

def test_all_nine_comparison_groups_have_source_linked_observations():
    groups=read(GROUPS)
    sources=read(COMPARISON)
    actual={r["group_id"] for r in sources}
    expected={g["group_id"] for g in groups if g["cohort"]=="comparison"}
    assert len(expected)==9
    assert actual==expected
    assert all(r["source_url"].startswith("https://") for r in sources)
    assert not any(r["group_id"] not in expected for r in sources)

def test_comparison_rows_are_never_treated_as_verified_tokyo_resale():
    groups=read(GROUPS)
    annual=build(groups, read(CONFIG), [], [], [], [], read(COMPARISON))
    assert len(annual)==45
    for row in annual:
        if row["cohort"]=="comparison" and row["coverage_state"]=="COMPARISON_DOCUMENTED_NOT_RESALE":
            assert row["tokyo_resale_segment_verified"]=="NO"
            assert row["verified_full_year_rows"]==0
            assert row["company_wide_comparison_ready"]=="NO"
