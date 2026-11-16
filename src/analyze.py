"""Risk indicators based only on provenance-backed, annual accounting facts."""
from __future__ import annotations
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"processed"
HEAD=["ticker","company","fiscal_end","period_months","scope","inventory_jpy","revenue_jpy","cogs_jpy","gross_profit_jpy","short_term_debt_jpy","interest_expense_jpy","operating_cash_flow_jpy","source_doc_id","source_url","audit_note"]
METRICS=["inventory_jpy","revenue_jpy","cogs_jpy","gross_profit_jpy","short_term_debt_jpy","interest_expense_jpy","operating_cash_flow_jpy"]

def safe_float(value):
    try:
        return float(value) if value is not None and str(value).strip() else None
    except (TypeError,ValueError):
        return None

def ratio(a,b):
    return a/b if a is not None and b is not None and b!=0 else None

def input_rows():
    file=OUT/"financial_facts.csv"
    if not file.exists():
        OUT.mkdir(parents=True,exist_ok=True)
        with file.open("w",encoding="utf-8",newline="") as f:
            csv.writer(f).writerow(HEAD)
    with file.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def calculate(rows):
    grouped=defaultdict(list)
    for row in rows:
        if row.get("scope") not in ("consolidated","nonconsolidated"): continue
        if not (row.get("source_doc_id") or row.get("source_url")): continue
        try: datetime.strptime(row["fiscal_end"],"%Y-%m-%d")
        except (KeyError,ValueError): continue
        grouped[(row["ticker"],row["scope"])].append(row)
    output=[]
    for key, records in sorted(grouped.items()):
        records.sort(key=lambda r:r["fiscal_end"])
        previous=None
        for row in records:
            data={k:safe_float(row.get(k)) for k in METRICS}
            annual=safe_float(row.get("period_months"))==12
            comparable=previous is not None and annual and safe_float(previous.get("period_months"))==12
            stock=data["inventory_jpy"]
            prev_stock=safe_float(previous.get("inventory_jpy")) if comparable else None
            average_stock=(stock+prev_stock)/2 if stock is not None and prev_stock is not None else None
            turnover=ratio(data["cogs_jpy"],average_stock) if annual else None
            days=round(365/turnover,2) if turnover and turnover>0 else None
            inv_growth=ratio(stock-prev_stock,prev_stock) if stock is not None and prev_stock is not None and comparable else None
            gross_margin=ratio(data["gross_profit_jpy"],data["revenue_jpy"]) if annual else None
            result={k:row.get(k,"") for k in ("ticker","company","fiscal_end","scope","source_doc_id","source_url")}
            result.update({
                "inventory_jpy":stock,
                "inventory_yoy_pct":round(inv_growth*100,2) if inv_growth is not None else None,
                "inventory_days":days,
                "gross_margin_pct":round(gross_margin*100,2) if gross_margin is not None else None,
                "short_term_debt_jpy":data["short_term_debt_jpy"],
                "interest_expense_jpy":data["interest_expense_jpy"],
                "operating_cash_flow_jpy":data["operating_cash_flow_jpy"],
                "audit_flag":"NOT_TOKYO_SEGMENT_SPECIFIC",
            })
            output.append(result)
            previous=row
    return output

def main():
    result=calculate(input_rows())
    fields=["ticker","company","fiscal_end","scope","inventory_jpy","inventory_yoy_pct","inventory_days","gross_margin_pct","short_term_debt_jpy","interest_expense_jpy","operating_cash_flow_jpy","source_doc_id","source_url","audit_flag"]
    with (OUT/"risk_indicators.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    # Provisional observations are kept separate from independently verified facts.
    candidate_file=OUT/"financial_candidates.csv"
    candidate_rows=[]
    if candidate_file.exists():
        with candidate_file.open(encoding="utf-8",newline="") as input_file:
            candidate_rows=list(csv.DictReader(input_file))
    import json
    provisional=[r for r in candidate_rows if json.loads(r.get("audit_note") or "{}").get("status")=="MACHINE_EXTRACTED_UNREVIEWED"]
    candidates=calculate(provisional)
    with (OUT/"candidate_indicators.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for row in candidates:
            row["audit_flag"]="MACHINE_EXTRACTED_UNREVIEWED_NOT_TOKYO_SPECIFIC"
            writer.writerow(row)
    status=ROOT/"docs"/"STATUS.md"
    status.parent.mkdir(parents=True,exist_ok=True)
    status.write_text("# Data availability\n\nVerified annual observations: **"+str(len(result))+"**\n\nMachine-extracted, unreviewed observations: **"+str(len(candidate_rows))+"**\n\n"+
        ("Indicators computed from source-linked, separately verified fact table.\n" if result else
         "No verified accounting observations yet. The workflow does **not** infer financial deterioration from missing data.\n")+
        "\nThe filing index is evidence discovery, not a distress score.\n",encoding="utf-8")
    print("Verified indicator rows:",len(result),"machine-extracted candidate rows:",len(candidate_rows))

if __name__=="__main__":
    main()
