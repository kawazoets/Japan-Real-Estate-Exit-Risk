"""Extract auditable, machine-read accounting facts from EDINET type=5 ZIP.
Do not treat machine-extracted observations as independently verified findings.
"""
from __future__ import annotations
import csv
import io
import json
import zipfile
from pathlib import Path
from collections import defaultdict
from .edinet import ROOT, load_csv, write_csv

FIELDS=["ticker","company","fiscal_end","period_months","scope","inventory_jpy","revenue_jpy","cogs_jpy","gross_profit_jpy","short_term_debt_jpy","interest_expense_jpy","operating_cash_flow_jpy","source_doc_id","source_url","audit_note"]
CANDIDATES=ROOT/"data"/"processed"/"financial_candidates.csv"
MAP={
    "revenue_jpy":{"NetSales","Revenue","OperatingRevenue"},
    "cogs_jpy":{"CostOfSales","CostOfRevenue"},
    "gross_profit_jpy":{"GrossProfit"},
    "short_term_debt_jpy":{"ShortTermLoansPayable","ShortTermBorrowings","ShortTermLoans"},
    "interest_expense_jpy":{"InterestExpensesNOE","InterestExpensesOpeCF"},
    "operating_cash_flow_jpy":{"NetCashProvidedByUsedInOperatingActivities"},
    "inventory_jpy":{"Inventories"},
}
RE_STOCK={"RealEstateForSale","RealEstateForSaleInProcess","CostsOnRealEstateBusiness","LandAndBuildingsForSaleInLots"}
ALL_STOCK=RE_STOCK|{"DevelopmentProjectsInProgress","MerchandiseAndFinishedGoods","WorkInProcess"}
STOCK_CONTEXT="CurrentYearInstant"
DURATION_CONTEXT="CurrentYearDuration"

def parse_zip(blob):
    """EDINET XBRL_TO_CSV files are UTF-16, tab-delimited, 9 columns."""
    facts=defaultdict(set)
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        targets=[name for name in archive.namelist() if name.lower().endswith(".csv")
                 and ("xbrl_to_csv/" in name.lower() or "xbrl_to_csv\\" in name.lower())
                 and "jpcrp030000" in name.lower()]
        for name in targets:
            raw=archive.read(name)
            # UTF-16 with BOM on production; some archives use LE without BOM.
            txt=raw.decode("utf-16") if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else raw.decode("utf-16-le")
            rows=csv.reader(io.StringIO(txt),delimiter="\t")
            next(rows,None)
            for cells in rows:
                if len(cells)<9: continue
                element,label,ctx,relative,scope,period,unit,unit_name,value=cells[:9]
                if ctx not in (STOCK_CONTEXT,DURATION_CONTEXT): continue
                if unit.upper() not in ("JPY","JPYUNIT"): continue
                if "NonConsolidated" in ctx or "Member" in ctx: continue
                if scope.strip() in ("個別","非連結","Non-Consolidated"): continue
                key=element.split(":")[-1]
                if not element.startswith(("jppfs_cor:","ifrs-full:","jpigp_cor:")): continue
                rawvalue=value.strip().replace(",","").replace("△","-").replace("▲","-").replace("－","-")
                if rawvalue.startswith("(") and rawvalue.endswith(")"): rawvalue="-"+rawvalue[1:-1]
                try: amount=int(rawvalue)
                except ValueError: continue
                if ctx==STOCK_CONTEXT and (key in ALL_STOCK or key in MAP["inventory_jpy"] or key in MAP["short_term_debt_jpy"]):
                    facts[(key,ctx)].add(amount)
                if ctx==DURATION_CONTEXT and any(key in MAP[m] for m in
                    ("revenue_jpy","cogs_jpy","gross_profit_jpy","interest_expense_jpy","operating_cash_flow_jpy")):
                    facts[(key,ctx)].add(amount)
    return facts

def pick(facts, names, ctx):
    available=[(name,v) for name in sorted(names) for v in facts.get((name,ctx),set())]
    unique={v for _,v in available}
    if len(unique)==1: return next(iter(unique)),[name for name,_ in available],""
    if len(unique)>1: return None,[name for name,_ in available],"CONFLICT"
    return None,[],"MISSING"

def extract(document, blob):
    if str(document.get("doc_type_code")) not in ("120","130"): return None
    end=document.get("period_end")
    if not end or len(end)!=10: return None
    facts=parse_zip(blob)
    row={k:"" for k in FIELDS}
    row.update({"ticker":document["ticker"],"company":document["company"],
                "fiscal_end":end,"period_months":"12","scope":"consolidated",
                "source_doc_id":document["doc_id"],
                "source_url":"https://api.edinet-fsa.go.jp/api/v2/documents/"+document["doc_id"]+"?type=5"})
    audit={"status":"MACHINE_EXTRACTED_UNREVIEWED","tags":{},"missing":[],"conflicts":[]}
    for metric,tags in MAP.items():
        ctx=STOCK_CONTEXT if metric in ("inventory_jpy","short_term_debt_jpy") else DURATION_CONTEXT
        value,used,flag=pick(facts,tags,ctx)
        if value is not None: row[metric]=value
        if used: audit["tags"][metric]=used
        if flag=="CONFLICT": audit["conflicts"].append(metric)
        elif flag=="MISSING": audit["missing"].append(metric)
    # Property inventory components are explicitly separated; never silently conflate with
    # merchandise, inventory totals, or development real estate.
    components={}
    for name in sorted(RE_STOCK):
        value,_,flag=pick(facts,{name},STOCK_CONTEXT)
        if value is not None: components[name]=value
        elif flag=="CONFLICT": audit["conflicts"].append(name)
    if components: audit["property_stock_components_jpy"]=components
    # Only construct total if ALL components are unambiguous; preserve origin.
    if row["inventory_jpy"]=="": 
        if components and not any(x in audit["conflicts"] for x in RE_STOCK):
            row["inventory_jpy"]=sum(components.values())
            audit["inventory_definition"]="SUM_DISCLOSED_REAL_ESTATE_COMPONENTS_NOT_TOTAL_INVENTORIES"
        else: audit["inventory_definition"]="NOT_AVAILABLE"
    else: audit["inventory_definition"]="BALANCE_SHEET_TOTAL_INVENTORIES"
    if not facts: audit["status"]="NO_ELIGIBLE_FACTS"
    row["audit_note"]=json.dumps(audit,ensure_ascii=False,sort_keys=True)
    return row

def extract_all():
    docs=load_csv(ROOT/"data"/"raw"/"edinet_documents.csv")
    directory=ROOT/"data"/"raw"/"filings"
    existing={x["source_doc_id"]:x for x in load_csv(CANDIDATES)}
    changes=0
    for doc in docs:
        path=directory/(doc["doc_id"]+".zip")
        if doc["doc_id"] in existing or not path.exists(): continue
        row=extract(doc,path.read_bytes())
        if row:
            existing[doc["doc_id"]]=row
            changes+=1
    write_csv(CANDIDATES,sorted(existing.values(),key=lambda r:(r["ticker"],r["fiscal_end"],r["source_doc_id"])),FIELDS)
    print(f"candidate facts: {len(existing)} (new {changes})")
    return changes

if __name__=="__main__":
    extract_all()
