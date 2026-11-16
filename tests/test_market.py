import pytest
from src.reins_sources import parse_index
from src.market import validate

def test_only_official_reins_pdf_links():
    html='''<a href="/pdf/trend/mw/MW_202610data.pdf">Oct report</a>
    <a href="/pdf/trend/mw/ZMW_202610data.pdf">National</a>
    <a href="https://other.example/MW_202610data.pdf">Fake</a>'''
    found=parse_index(html,"https://www.reins.or.jp/library/2026.html")
    assert found[("2026-10","east_japan")].endswith("/MW_202610data.pdf")
    assert found[("2026-10","national")].endswith("/ZMW_202610data.pdf")
    assert len(found)==2

def test_no_document_link_without_market_observation():
    assert validate([])==[]

def test_refuse_unsourced_monthly_counts():
    row={"observation_month":"2026-10","geography":"Tokyo",
         "inventory_count":"100","contracts_count":"20",
         "source_url":"https://example.org/report.pdf","source_page":"3"}
    with pytest.raises(ValueError): validate([row])

def test_inventory_to_contracts_ratio_not_claimed_to_be_sales_months():
    row={"observation_month":"2026-10","geography":"Tokyo",
         "inventory_count":"100","contracts_count":"20",
         "contract_price_jpy":"40000000","contract_sqm_price_jpy":"800000",
         "source_url":"https://www.reins.or.jp/pdf/trend/mw/MW_202610data.pdf",
         "source_page":"2"}
    result=validate([row])[0]
    assert result["inventory_to_monthly_contracts_ratio"]==5.0
    assert result["audit_flag"]=="SOURCE_PAGE_STATED_NOT_INDEPENDENTLY_VERIFIED"
