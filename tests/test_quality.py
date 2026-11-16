import json
from src.quality import check_rows
from src.analyze import calculate

def row(end="2020-11-30",stock="100",definition="SUM_DISCLOSED_REAL_ESTATE_COMPONENTS_NOT_TOTAL_INVENTORIES"):
    return {
        "ticker":"2975","company":"Test","scope":"consolidated","fiscal_end":end,"period_months":"12",
        "inventory_jpy":stock,"revenue_jpy":"200","cogs_jpy":"150","gross_profit_jpy":"50",
        "source_doc_id":"S100TEST","audit_note":json.dumps({"status":"MACHINE_EXTRACTED_UNREVIEWED",
           "inventory_definition":definition,"conflicts":[]})
    }

def test_qa_flags_missing_figures():
    a=row();a["gross_profit_jpy"]=""
    assert check_rows([a])[0]["comparison_eligible"]=="NO"

def test_qa_checks_sales_cost_margin():
    a=row();a["gross_profit_jpy"]="100"
    assert check_rows([a])[0]["gross_profit_arithmetic"]=="MISMATCH"

def test_qa_pass_is_not_independent_verification():
    assert check_rows([row()])[0]["comparison_eligible"]=="POTENTIAL_ONLY"

def test_turnover_rejected_if_years_not_adjacent():
    results=calculate([row(),row(end="2022-11-30",stock="150")])
    assert results[-1]["inventory_days"] is None

def test_turnover_rejected_if_stock_definition_changes():
    results=calculate([row(),row(end="2021-11-30",stock="150",definition="BALANCE_SHEET_TOTAL_INVENTORIES")])
    assert results[-1]["inventory_days"] is None

def test_turnover_accepted_if_comparable():
    results=calculate([row(),row(end="2021-11-30",stock="150")])
    assert results[-1]["inventory_days"] == round(365*125/150,2)
