from copy import deepcopy
import pytest
from src.peer_matrix import build,validate_relevance
from src.cohort import GROUPS,IR,COMPARISON,read
from src.peer_matrix import RELEVANCE

def test_research_tiers_keep_all_15_and_no_verified_tokyo_claim():
    groups=read(GROUPS)
    ratings=validate_relevance(groups,read(RELEVANCE))
    assert len(ratings)==15
    rows=build(groups,read(IR),read(COMPARISON),read(RELEVANCE))
    assert len(rows)==15
    assert sum(r["provisional_relevance"]=="FOCUS_CANDIDATE" for r in rows)==3
    assert sum(r["provisional_relevance"]=="CONDITIONAL_CORE" for r in rows)==3
    assert sum(r["provisional_relevance"]=="COMPARISON_ONLY" for r in rows)==9
    assert not any(r["usable_for_tokyo_exit_conclusion"]=="YES" for r in rows)

def test_refuse_promotion_without_tokyo_and_used_condo_evidence():
    groups=read(GROUPS)
    ratings=deepcopy(read(RELEVANCE))
    ratings[0]["usable_for_tokyo_exit_conclusion"]="YES"
    with pytest.raises(ValueError):
        validate_relevance(groups,ratings)

def test_refuse_incomplete_tier_assessment():
    with pytest.raises(ValueError):
        validate_relevance(read(GROUPS),read(RELEVANCE)[:3])

def test_prevent_undocumented_tier_change():
    groups=read(GROUPS)
    ratings=deepcopy(read(RELEVANCE))
    ratings[0]["provisional_relevance"]="COMPARISON_ONLY"
    with pytest.raises(ValueError):
        validate_relevance(groups,ratings)
