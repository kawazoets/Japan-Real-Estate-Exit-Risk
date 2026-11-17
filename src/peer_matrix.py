"""A fixed 15-group peer comparison that NEVER turns mixed-use stock into Tokyo condo resale stock."""
from __future__ import annotations
import csv
from collections import defaultdict
from .analyze import ROOT
from .cohort import GROUPS, IR, COMPARISON, read, validate_groups, CONFIG
RELEVANCE=ROOT/"config"/"tokyo_resale_relevance.csv"

OUT=ROOT/"data"/"processed"/"peer_matrix_15.csv"
COLUMNS=["group_id","company","cohort","provisional_relevance","analysis_role","tokyo_share_verified","used_condo_resale_segment_verified","usable_for_tokyo_exit_conclusion","latest_comparable_fiscal_year_pair",
         "stock_yoy_pct","stock_definition","revenue_yoy_pct",
         "operating_profit_yoy_pct","operating_cashflow_prev_mJPY",
         "operating_cashflow_latest_mJPY","source_url","data_status",
         "tokyo_used_condo_resale_inference"]

def num(r,k):
    if r is None:return None
    v=r.get(k,"")
    try:return float(v) if v not in ("",None) else None
    except (TypeError,ValueError):return None

def pct(new,old):
    return round((new/old-1)*100,2) if new is not None and old not in (None,0) else ""

def annual_map(rows,year_field,group_field):
    out=defaultdict(dict)
    for r in rows:
        group=r.get(group_field,"")
        if not group:continue
        y=int(str(r[year_field])[:4])
        if y in out[group]:
            raise ValueError("Duplicate group fiscal year: "+group+" "+str(y))
        out[group][y]=r
    return out

def validate_relevance(groups,relevance):
    expected={g["group_id"] for g in groups}
    ids=[r["group_id"] for r in relevance]
    if len(ids)!=15 or len(set(ids))!=15 or set(ids)!=expected:
        raise ValueError("All 15 study groups require exactly one explicit relevance classification")
    counts={"FOCUS_CANDIDATE":0,"CONDITIONAL_CORE":0,"COMPARISON_ONLY":0}
    for r in relevance:
        value=r["provisional_relevance"]
        if value not in counts:raise ValueError("Unexpected evidence relevance class")
        counts[value]+=1
        if r["usable_for_tokyo_exit_conclusion"] not in ("NO","YES"):
            raise ValueError("Missing evidence gate for "+r["group_id"])
        if r["usable_for_tokyo_exit_conclusion"]=="YES" and (r["tokyo_share_verified"]!="YES" or r["used_condo_resale_segment_verified"]!="YES"):
            raise ValueError("Cannot claim Tokyo used-condo resale inference without Tokyo and segment verification")
        cohort=next(g["cohort"] for g in groups if g["group_id"]==r["group_id"])
        if cohort=="comparison" and value!="COMPARISON_ONLY":
            raise ValueError("Comparison group cannot silently become a core Tokyo-resale company")
        if cohort=="core" and value=="COMPARISON_ONLY":
            raise ValueError("Original core group cannot silently be excluded")
    if counts!={"FOCUS_CANDIDATE":3,"CONDITIONAL_CORE":3,"COMPARISON_ONLY":9}:
        raise ValueError("Research weighting must remain three candidates, three conditional, nine comparison")
    return {r["group_id"]:r for r in relevance}

def build(groups,core,comparison,relevance=None):
    relevance=read(RELEVANCE) if relevance is None else relevance
    relevance_by_id=validate_relevance(groups,relevance)
    core_norm=[]
    for r in core:
        ticker=r.get("ticker")
        core_norm.append(dict(r,group_id="intellex" if ticker in ("8940","463A") else
          next((g["group_id"] for g in groups if ticker in g["tickers"].split("|")),"")))
    c=annual_map(core_norm,"fiscal_end","group_id")
    b=annual_map(comparison,"accounting_year","group_id")
    out=[]
    for g in groups:
        group=g["group_id"]
        tag=relevance_by_id[group]
        evidence={k:tag[k] for k in ("provisional_relevance","analysis_role","tokyo_share_verified","used_condo_resale_segment_verified","usable_for_tokyo_exit_conclusion")}
        eligible=c.get(group,{}) if g["cohort"]=="core" else b.get(group,{})
        candidates=[y for y in eligible if (y-1) in eligible]
        if not candidates: 
            out.append({"group_id":group,"company":g["canonical_company"],"cohort":g["cohort"],**evidence,
                "latest_comparable_fiscal_year_pair":"","stock_yoy_pct":"","stock_definition":"NOT_AVAILABLE",
                "revenue_yoy_pct":"","operating_profit_yoy_pct":"",
                "operating_cashflow_prev_mJPY":"","operating_cashflow_latest_mJPY":"",
                "source_url":"","data_status":"MISSING_CONSECUTIVE_FISCAL_YEARS",
                "tokyo_used_condo_resale_inference":"NOT_ESTABLISHED"})
            continue
        y=max(candidates);old=eligible[y-1];new=eligible[y]
        if g["cohort"]=="core":
            old_stock=num(old,"inventory_jpy")
            new_stock=num(new,"inventory_jpy")
            old_sales=num(old,"revenue_jpy")
            new_sales=num(new,"revenue_jpy")
            definition="CORE_GROUP_WIDE_PROPERTY_STOCK_OR_UNDISCLOSED_COMPONENTS"
            source=new.get("source_inventory_url","")
            profit_old=profit_new=None
            cf_old=cf_new=None
        else:
            old_stock=num(old,"inventory_total_or_combined_mJPY")
            new_stock=num(new,"inventory_total_or_combined_mJPY")
            if old.get("inventory_definition")!=new.get("inventory_definition"):
                old_stock=new_stock=None
            old_sales=num(old,"revenue_mJPY")
            new_sales=num(new,"revenue_mJPY")
            definition=new.get("inventory_definition") or "NOT_AVAILABLE"
            source=new.get("source_url","")
            profit_old=num(old,"operating_profit_mJPY")
            profit_new=num(new,"operating_profit_mJPY")
            cf_old=num(old,"operating_cashflow_mJPY")
            cf_new=num(new,"operating_cashflow_mJPY")
        out.append({
            "group_id":group,"company":g["canonical_company"],"cohort":g["cohort"],**evidence,
            "latest_comparable_fiscal_year_pair":f"{y-1}-{y}",
            "stock_yoy_pct":pct(new_stock,old_stock),"stock_definition":definition,
            "revenue_yoy_pct":pct(new_sales,old_sales),
            "operating_profit_yoy_pct":pct(profit_new,profit_old),
            "operating_cashflow_prev_mJPY":cf_old if cf_old is not None else "",
            "operating_cashflow_latest_mJPY":cf_new if cf_new is not None else "",
            "source_url":source,
            "data_status":"PUBLIC_SOURCE_TRANSCRIBED_UNREVIEWED",
            "tokyo_used_condo_resale_inference":"NOT_ESTABLISHED",
        })
    if len(out)!=15 or len({r["group_id"] for r in out})!=15:
        raise ValueError("Fixed original 15-group cohort was lost")
    return out

def main():
    groups=read(GROUPS)
    validate_groups(groups,read(CONFIG))
    matrix=build(groups,read(IR),read(COMPARISON),read(RELEVANCE))
    with OUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS)
        writer.writeheader();writer.writerows(matrix)
    print("Peer matrix groups:",len(matrix),"year-pairs:",sum(bool(x["latest_comparable_fiscal_year_pair"]) for x in matrix))
if __name__=="__main__":main()
