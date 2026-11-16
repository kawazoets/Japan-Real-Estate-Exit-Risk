from src.compare_ir import calc

def item(ticker,year,inventory,revenue,cogs,profit,units):
    return {
        "ticker":ticker,"fiscal_end":f"{year}-05-31","inventory_jpy":str(inventory),
        "revenue_jpy":str(revenue),"cogs_jpy":str(cogs),
        "gross_profit_jpy":str(profit),"resale_condo_units_sold":str(units),
    }

def test_actual_intellex_annual_primary_ir_numbers():
    rows=[
       item("8940",2024,20308,42702,36870,5831,1129),
       item("8940",2025,28563,44793,36822,7971,1052),
       item("463A",2026,37412,58471,49153,9317,1043),
    ]
    comparisons=calc(rows)
    assert len(comparisons)==2
    row=comparisons[-1]
    assert row["inventory_yoy_pct"]==30.98
    assert row["resale_units_yoy_pct"]==-0.86
    assert row["inventory_days_from"]==242.2
    assert row["inventory_days_to"]==245.0
    assert row["note"].startswith("HOLDINGS_STRUCTURE_CHANGED_2026")

def test_no_turnover_days_when_cogs_absent():
    rows=[
       item("2975",2023,86584,48877,"",8422,""),
       item("2975",2024,95811,55849,"",9816,""),
       item("2975",2025,105029,69158,"",12275,""),
    ]
    result=calc(rows)
    assert result[-1]["inventory_days_to"] is None
