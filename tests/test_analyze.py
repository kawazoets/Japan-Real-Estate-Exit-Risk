from src.analyze import calculate
from src.edinet import normalized_ticker

def test_edinet_security_code():
    assert normalized_ticker("29750")=="2975"
    assert normalized_ticker("2975")=="2975"
    assert normalized_ticker("463A0")=="463A"
    assert normalized_ticker(None)==""

def test_inventory_days_only_when_comparable_annual():
    row={"ticker":"2975","company":"X","scope":"consolidated","period_months":"12","inventory_jpy":"100","cogs_jpy":"100","revenue_jpy":"150","gross_profit_jpy":"50","source_doc_id":"S00001"}
    old=dict(row,fiscal_end="2024-12-31")
    new=dict(row,fiscal_end="2025-12-31",inventory_jpy="200",cogs_jpy="150")
    result=calculate([old,new])
    assert result[0]["inventory_days"] is None
    assert result[1]["inventory_days"]==365.0
    assert result[1]["inventory_yoy_pct"]==100.0

def test_no_source_no_verdict():
    row={"ticker":"2975","scope":"consolidated","fiscal_end":"2025-12-31","period_months":"12","inventory_jpy":"100","cogs_jpy":"90"}
    assert calculate([row])==[]
