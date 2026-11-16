"""Direct comparison of source-documented core resale groups.
These observations remain company-wide and not Tokyo-specific. 
The 2025=>2026 Intellex 8940=>463A corporate reorganisation requires caution.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data"/"processed"/"company_ir_primary.csv"
OUT=ROOT/"data"/"processed"/"company_ir_comparisons.csv"
COLS=["group","from_year","to_year","inventory_yoy_pct","revenue_yoy_pct","gross_margin_from_pct","gross_margin_to_pct","inventory_days_from","inventory_days_to","resale_units_yoy_pct","note"]

def calc(rows):
    groups=defaultdict(dict)
    for row in rows:
        group="intellex" if row["ticker"] in ("8940","463A") else row["ticker"]
        groups[group][int(row["fiscal_end"][:4])]=row
    result=[]
    for group,record in sorted(groups.items()):
        years=sorted(record)
        for to_year in years:
            if to_year-1 not in record:continue
            old=record[to_year-1]
            new=record[to_year]
            prior=record.get(to_year-2,{})
            def metric(r,k):
                value=r.get(k,"")
                return int(value) if value else None
            inventory_old=metric(old,"inventory_jpy")
            inventory_new=metric(new,"inventory_jpy")
            inventory_prior=metric(prior,"inventory_jpy")
            revenue_old=metric(old,"revenue_jpy")
            revenue_new=metric(new,"revenue_jpy")
            gp_old=metric(old,"gross_profit_jpy")
            gp_new=metric(new,"gross_profit_jpy")
            cogs_old=metric(old,"cogs_jpy")
            cogs_new=metric(new,"cogs_jpy")
            sold_old=metric(old,"resale_condo_units_sold")
            sold_new=metric(new,"resale_condo_units_sold")
            def pct(a,b):
                return round(100*(a/b-1),2) if a is not None and b else None
            def days(end,begin,cogs):
                return round(365*(end+begin)/2/cogs,1) if all(x is not None for x in (end,begin,cogs)) and cogs>0 else None
            result.append({
                "group":group,"from_year":to_year-1,"to_year":to_year,
                "inventory_yoy_pct":pct(inventory_new,inventory_old),
                "revenue_yoy_pct":pct(revenue_new,revenue_old),
                "gross_margin_from_pct":round(100*gp_old/revenue_old,2) if gp_old is not None and revenue_old else None,
                "gross_margin_to_pct":round(100*gp_new/revenue_new,2) if gp_new is not None and revenue_new else None,
                "inventory_days_from":days(inventory_old,inventory_prior,cogs_old),
                "inventory_days_to":days(inventory_new,inventory_old,cogs_new),
                "resale_units_yoy_pct":pct(sold_new,sold_old),
                "note":"HOLDINGS_STRUCTURE_CHANGED_2026; GROUP_SCOPE_NOT_TOKYO_RESALE_ONLY" if group=="intellex" and to_year==2026 else "GROUP_SCOPE_NOT_TOKYO_RESALE_ONLY"
            })
    return result

def main():
    with SRC.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    result=calc(rows)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLS)
        writer.writeheader()
        writer.writerows(result)
    print("IR annual comparisons:",len(result))
if __name__=="__main__":main()
