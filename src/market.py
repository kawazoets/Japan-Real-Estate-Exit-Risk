"""Check independently transcribed REINS monthly market observations.

No values are scraped from arbitrary PDF text. A sourced figure is accepted only
with an exact page reference and observation geography.
"""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data"/"processed"/"reins_monthly.csv"
OUTPUT=ROOT/"data"/"processed"/"market_signals.csv"
FIELDS=["observation_month","geography","inventory_count","contracts_count","contract_price_jpy",
        "contract_sqm_price_jpy","source_url","source_page","audit_note"]
SIGNALS=["observation_month","geography","inventory_count","contracts_count",
         "inventory_to_monthly_contracts_ratio","contract_price_jpy","contract_sqm_price_jpy",
         "listing_price_jpy","listing_sqm_price_jpy","source_url","source_page","audit_flag"]

def positive_int(v):
    try:
        if not v or "." in str(v) or int(v)<0:return None
        return int(v)
    except (ValueError,TypeError):return None

def nonnegative_float(v):
    try:
        if v is None or str(v).strip()=="":return None
        number=float(v)
        return number if number>=0 else None
    except (ValueError,TypeError):return None

def validate(rows):
    out=[]
    seen=set()
    for r in rows:
        month=r.get("observation_month","")
        geography=r.get("geography","").strip()
        try:
            dt=date.fromisoformat(month+"-01")
            month_ok=2000<=dt.year<=2100
        except ValueError:month_ok=False
        key=(month,geography)
        if not month_ok or not geography:raise ValueError("Missing month/geography for market observation")
        if key in seen:raise ValueError("Duplicate month/geography: "+repr(key))
        seen.add(key)
        url=r.get("source_url","")
        page=r.get("source_page","").strip()
        if not url.startswith("https://www.reins.or.jp/") or not page:
            raise ValueError("Only sourced official REINS reports with page numbers qualify: "+str(key))
        inventory=positive_int(r.get("inventory_count"))
        contracts=positive_int(r.get("contracts_count"))
        if inventory is None or contracts is None:raise ValueError("Missing counts in "+str(key))
        sale_price=nonnegative_float(r.get("contract_price_jpy"))
        sqm_price=nonnegative_float(r.get("contract_sqm_price_jpy"))
        listing_price=nonnegative_float(r.get("listing_price_jpy"))
        listing_sqm_price=nonnegative_float(r.get("listing_sqm_price_jpy"))
        ratio=round(inventory/contracts,2) if contracts>0 else None
        out.append({
            "observation_month":month,"geography":geography,
            "inventory_count":inventory,"contracts_count":contracts,
            "inventory_to_monthly_contracts_ratio":ratio,
            "contract_price_jpy":sale_price,"contract_sqm_price_jpy":sqm_price,
            "listing_price_jpy":listing_price,"listing_sqm_price_jpy":listing_sqm_price,
            "source_url":url,"source_page":page,
            "audit_flag":"SOURCE_PAGE_STATED_NOT_INDEPENDENTLY_VERIFIED",
        })
    return out

def main():
    if INPUT.exists():
        with INPUT.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
    else:rows=[]
    signals=validate(rows)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=SIGNALS)
        writer.writeheader();writer.writerows(signals)
    print("REINS market observations with source pages:",len(signals))
    if not signals:
        print("No source-verified prices or counts yet: do not publish a market trend.")
if __name__=="__main__":main()
