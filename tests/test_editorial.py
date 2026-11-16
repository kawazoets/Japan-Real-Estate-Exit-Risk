from src.editorial import render

def test_no_publication_from_unsourced_or_incomplete_data():
    report=render([],[])
    assert "NOT READY FOR PUBLICATION" in report
    assert "Tokyo-market observations (monthly): **0**" in report

def test_coverage_does_not_equal_causality():
    company=[{"ticker":"2975","fiscal_end":"2024-11-30","inventory_days":"250"},
             {"ticker":"2975","fiscal_end":"2025-11-30","inventory_days":"280"}]
    market=[{"geography":"Tokyo","observation_month":f"2025-{m:02d}"} for m in range(1,13)]
    report=render(company,market)
    assert "DATA COVERAGE THRESHOLD REACHED" in report
    assert "not proof of exit congestion" in report
