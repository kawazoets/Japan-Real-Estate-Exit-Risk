"""Strict checks of a directly observed condo-resale operator's price-band conversion signals."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"data"/"processed"/"tokyo_resale_segment_evidence.csv"

def read():
    with PATH.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def verify(rows):
    company=[r for r in rows if r["group_id"]=="star_mica"
             and r["metric"]=="actively_marketed_inventory"
             and r["as_of"]=="2026-08-31"]
    if len(company)!=2:raise ValueError("Two price-band company inventory rows required")
    stocks={r["price_band_jpy"]:int(r["amount"]) for r in company}
    if stocks!={"under_100m":442,"100m_or_more":42}:
        raise ValueError("Company resale stock did not reconcile to public PDF")
    if sum(stocks.values())!=484:raise ValueError("Active selling stocks inconsistent")
    star_rates=[r for r in rows if r["group_id"]=="star_mica" and r["metric"]=="monthly_equivalent_contract_rate"]
    for r in star_rates:
        if r["verification"] not in ("COMPANY_PRIMARY_PDF_SCREEN_VERIFIED","COMPANY_CALCULATED_FROM_REINS_PDF_SCREEN_VERIFIED"):
            raise ValueError("Tokyo market or company contract rates cannot be silently promoted")
        if r["geography"]=="companywide" and r["limitation"]=="MARKET_NOT_COMPANY":
            raise ValueError("Company selling conversion and Tokyo market rates confused")
        if r["geography"]=="Tokyo_prefecture" and r["limitation"]!="MARKET_NOT_COMPANY":
            raise ValueError("Tokyo market rate wrongly identified as company contract rate")
    for band,prior,current in [("under_100m",30,27),("100m_or_more",17,9)]:
        matches=[r for r in star_rates if r["segment"]=="renovated_condo_for_sale" and r["price_band_jpy"]==band]
        by_period={r["as_of"]:int(r["amount"]) for r in matches}
        if by_period!={"2025-06-01_to_2025-08-31":prior,"2026-06-01_to_2026-08-31":current}:
            raise ValueError("Company selling rate or date mismatch")
    if len([r for r in rows if r["group_id"]=="landnet" and r["metric"]=="purchase_and_resale_closings"])!=1:
        raise ValueError("Landnet direct purchase resale metric missing")
    return True

if __name__=="__main__":
    verify(read())
    print("Company and Tokyo condo resale signals checked: 484 company active-sale units, separate market and company rates")
