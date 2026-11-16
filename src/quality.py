"""Data-quality checks for *machine extracted* EDINET observations.

This is a rejection/triage report, not an audit opinion. It must never silently
promote machine-extracted figures to independently verified financial facts.
"""
from __future__ import annotations
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from .analyze import ROOT, safe_float

INPUT=ROOT/"data"/"processed"/"financial_candidates.csv"
OUTPUT=ROOT/"data"/"processed"/"quality_checks.csv"
REPORT=ROOT/"docs"/"QUALITY.md"
FIELDS=["ticker","company","fiscal_end","doc_id","status","inventory_definition","missing_critical","gross_profit_arithmetic","cash_flow_available","comparison_eligible","reason"]

def check_rows(rows):
    result=[]
    for r in rows:
        try: audit=json.loads(r.get("audit_note") or "{}")
        except ValueError: audit={"status":"INVALID_AUDIT_NOTE"}
        stock=safe_float(r.get("inventory_jpy"))
        sale=safe_float(r.get("revenue_jpy"))
        cogs=safe_float(r.get("cogs_jpy"))
        gp=safe_float(r.get("gross_profit_jpy"))
        definition=audit.get("inventory_definition","NOT_AVAILABLE")
        missing=[k for k,val in (("inventory_jpy",stock),("revenue_jpy",sale),("cogs_jpy",cogs),("gross_profit_jpy",gp)) if val is None]
        if any(val is not None and val<0 for val in (stock,sale,cogs)):
            missing.append("NEGATIVE_STOCK_OR_SALES")
        arithmetic="UNAVAILABLE"
        if all(v is not None for v in (sale,cogs,gp)):
            difference=(sale-cogs)-gp
            tolerance=max(1.0,abs(sale)*0.0001)
            arithmetic="OK" if abs(difference)<=tolerance else "MISMATCH"
        reason=[]
        if missing: reason.append("CRITICAL_FIELDS_MISSING_OR_INVALID")
        if arithmetic!="OK": reason.append("GROSS_PROFIT_RECONCILIATION_"+arithmetic)
        if definition not in ("BALANCE_SHEET_TOTAL_INVENTORIES","SUM_DISCLOSED_REAL_ESTATE_COMPONENTS_NOT_TOTAL_INVENTORIES"):
            reason.append("INVENTORY_DEFINITION_UNAVAILABLE")
        if audit.get("status")!="MACHINE_EXTRACTED_UNREVIEWED":
            reason.append("NO_ELIGIBLE_FACTS_OR_NOT_REVIEWABLE")
        if audit.get("conflicts"): reason.append("CONFLICTING_XBRL_TAGS")
        if str(r.get("period_months"))!="12": reason.append("NOT_FULL_YEAR")
        result.append({
            "ticker":r.get("ticker",""),"company":r.get("company",""),"fiscal_end":r.get("fiscal_end",""),
            "doc_id":r.get("source_doc_id",""),"status":audit.get("status","MISSING"),
            "inventory_definition":definition,
            "missing_critical":"|".join(missing),
            "gross_profit_arithmetic":arithmetic,
            "cash_flow_available":"YES" if safe_float(r.get("operating_cash_flow_jpy")) is not None else "NO",
            "comparison_eligible":"POTENTIAL_ONLY" if not reason else "NO",
            "reason":"|".join(reason),
        })
    return result

def main():
    if INPUT.exists():
        with INPUT.open(encoding="utf-8-sig",newline="") as file:
            rows=list(csv.DictReader(file))
    else: rows=[]
    checked=check_rows(rows)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(checked)
    rejected=[r for r in checked if r["comparison_eligible"]=="NO"]
    counts=Counter(reason for row in rejected for reason in row["reason"].split("|"))
    lines=["# Preliminary extraction QA (NOT audited financials)","","Machine-extracted observations: **"+str(len(checked))+"**.",
           "Rows passing basic arithmetic/completeness screening: **"+str(len(checked)-len(rejected))+"**.",
           "Rows rejected for longitudinal comparison: **"+str(len(rejected))+"**.","",
           "A row passing screening is **not** independently verified and does **not** prove Tokyo condominium exit congestion.","",
           "## Rejection reasons",""]
    lines += ["- "+key+": "+str(value) for key,value in sorted(counts.items())] if counts else ["- None recorded"]
    lines+=["","## Rejected filing IDs",""]
    lines += ["- "+r["ticker"]+" / "+r["doc_id"]+" / "+r["reason"] for r in rejected] if rejected else ["- None"]
    lines += ["","Do not compute price impact or company-wide conclusions from this candidate table.",""]
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text("\n".join(lines),encoding="utf-8")
    print("Preliminary observations:",len(checked),"rejected:",len(rejected))

if __name__=="__main__":main()
