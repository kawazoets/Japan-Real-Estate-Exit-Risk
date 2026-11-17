"""Cohort-wide coverage accountability.

Every original research group is represented every time. Two IR examples
cannot silently become the full project and no company is quietly dropped.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from .analyze import ROOT

GROUPS=ROOT/"config"/"company_groups.csv"
CONFIG=ROOT/"config"/"companies.csv"
PRIMARY_SOURCES=ROOT/"config"/"primary_source_index.csv"
EDINET=ROOT/"data"/"raw"/"edinet_documents.csv"
EXTRACTED=ROOT/"data"/"processed"/"financial_candidates.csv"
IR=ROOT/"data"/"processed"/"company_ir_primary.csv"
COMPARISON=ROOT/"data"/"processed"/"comparison_nine_primary.csv"
OUT=ROOT/"data"/"processed"/"coverage_15_groups.csv"
REPORT=ROOT/"docs"/"COHORT_COVERAGE.md"
YEARS=(2024,2025,2026)
EXPECTED_GROUPS=15
EXPECTED_SYMBOLS=16
FIELDS=["group_id","company","cohort","ticker_codes","fiscal_year",
        "edinet_annual_indexed","edinet_annual_extracted",
        "primary_ir_rows","verified_full_year_rows","inventory_observed",
        "company_wide_comparison_ready","tokyo_resale_segment_verified",
        "coverage_state","source_ids","notes"]

def read(path):
    if not path.exists():return []
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def validate_groups(groups,company_rows):
    if len(groups)!=EXPECTED_GROUPS:
        raise ValueError(f"Expected {EXPECTED_GROUPS} distinct groups, got {len(groups)}")
    if len(company_rows)!=EXPECTED_SYMBOLS:
        raise ValueError(f"Expected {EXPECTED_SYMBOLS} original tickers, got {len(company_rows)}")
    registered=[c["ticker"] for c in company_rows]
    if len(set(registered))!=EXPECTED_SYMBOLS:
        raise ValueError("Duplicate security code in original cohort")
    mapped=[t for g in groups for t in g["tickers"].split("|")]
    if len(mapped)!=EXPECTED_SYMBOLS or set(mapped)!=set(registered):
        raise ValueError("The 15 groups must cover every one of the 16 registered security codes exactly once")
    if len(set(mapped))!=len(mapped):
        raise ValueError("A stock ticker belongs to more than one group")
    if sum(g["cohort"]=="core" for g in groups)!=6:
        raise ValueError("The six core resale groups cannot be silently removed")
    if sum(g["cohort"]=="comparison" for g in groups)!=9:
        raise ValueError("The nine comparison groups cannot be silently removed")
    successor=[g for g in groups if "8940" in g["tickers"].split("|")]
    if len(successor)!=1 or "463A" not in successor[0]["tickers"].split("|"):
        raise ValueError("Intellex must be one group across its holding-company transition")

def validate_primary_sources(groups, sources):
    expected={g["group_id"] for g in groups}
    actual=[r["group_id"] for r in sources]
    if len(actual)!=len(expected) or set(actual)!=expected or len(set(actual))!=len(actual):
        raise ValueError("Primary-source index must contain all 15 groups, exactly once")
    for r in sources:
        if not r.get("primary_document_or_ir_url","").startswith("https://"):
            raise ValueError("Missing usable primary-source entry for "+r["group_id"])

def build(groups,company_rows,documents,extracted,ir,verified,comparison=None):
    comparison=comparison or []
    validate_groups(groups,company_rows)
    output=[]
    for g in groups:
        symbols=set(g["tickers"].split("|"))
        for year in YEARS:
            ds=[r for r in documents if r.get("ticker") in symbols
                and r.get("doc_type_code") in ("120","130")
                and str(r.get("period_end","")).startswith(str(year))]
            xs=[r for r in extracted if r.get("ticker") in symbols
                and str(r.get("fiscal_end","")).startswith(str(year))]
            is_=[r for r in ir if r.get("ticker") in symbols
                and str(r.get("fiscal_end","")).startswith(str(year))]
            vs=[r for r in verified if r.get("ticker") in symbols
                and str(r.get("fiscal_end","")).startswith(str(year))]
            cs=[r for r in comparison if r.get("group_id")==g["group_id"]
                and str(r.get("accounting_year"))==str(year)]
            inv=(any(r.get("inventory_jpy","").strip() for r in xs+is_+vs) or
                 any(r.get("inventory_total_or_combined_mJPY","").strip() for r in cs))
            ir_complete=any(all(r.get(k,"").strip() for k in
                        ("inventory_jpy","revenue_jpy","cogs_jpy","gross_profit_jpy")) for r in is_)
            state=("VERIFIED_ANNUAL" if vs else
                   "IR_COMPLETE_UNAUDITED" if ir_complete else
                   "IR_PARTIAL_UNAUDITED" if is_ else
                   "COMPARISON_DOCUMENTED_NOT_RESALE" if cs else
                   "EDINET_CANDIDATE_UNVERIFIED" if xs else
                   "ANNUAL_DISCOVERED" if ds else "NOT_COLLECTED")
            src=sorted({r.get("source_doc_id") or r.get("doc_id") for r in ds+xs+vs}
                       - {"",None})
            output.append({
                "group_id":g["group_id"],"company":g["canonical_company"],
                "cohort":g["cohort"],"ticker_codes":g["tickers"],"fiscal_year":year,
                "edinet_annual_indexed":len(ds),"edinet_annual_extracted":len(xs),
                "primary_ir_rows":len(is_)+len(cs),"verified_full_year_rows":len(vs),
                "inventory_observed":"YES" if inv else "NO",
                "company_wide_comparison_ready":"CANDIDATE_ONLY" if ir_complete or vs else "NO",
                "tokyo_resale_segment_verified":"NO",
                "coverage_state":state,"source_ids":"|".join(src),
                "notes":("Potential new company structure; require reconciliation" if g["group_id"]=="intellex" and year==2026
                         else "COMPARISON_GROUP_MIXED_INVENTORY_NOT_TOKYO_RESALE" if cs else ""),
            })
    return output

def render(rows):
    ids=sorted({r["group_id"] for r in rows})
    count=lambda state:sum(x["coverage_state"]==state for x in rows)
    lines=["# 15-group cohort coverage — NO silent reduction","",
           "**MANDATORY scope:** 15 economic groups, 16 ticker identifiers, six core resale groups and nine comparison groups.",
           "**Calendar-year fiscal ends tracked:** 2024, 2025, 2026. Missing data is not evidence of financial health or distress.",
           "",
           "Annual group-years expected: **"+str(len(rows))+"**.",
           "Group-years with some primary IR data: **"+str(sum(int(r["primary_ir_rows"])>0 for r in rows))+"**.",
           "Group-years with independently validated facts: **"+str(sum(int(r["verified_full_year_rows"])>0 for r in rows))+"**.",
           "Group-years with Tokyo-resale-specific verified inventory: **0**.",
           "",
           "## All mandatory economic groups","",
           "| Group | Classification | 2024 | 2025 | 2026 |",
           "|---|---|---|---|---|"]
    for gid in ids:
        rs={r["fiscal_year"]:r for r in rows if r["group_id"]==gid}
        r=next(iter(rs.values()))
        lines.append("| "+r["company"]+" | "+r["cohort"]+" | "+" | ".join(rs[year]["coverage_state"] for year in YEARS)+" |")
    lines += ["",
              "## Research guardrails","",
              "- Never publish a two-company IR comparison as a 15-company conclusion.",
              "- Do not count 8940 and successor 463A as different companies.",
              "- Keep companies with zero findings visible, never silently exclude them.",
              "- 'IR_COMPLETE_UNAUDITED' means present fields, not vetted or segment-comparable data.",
              "- Inventories for new developments, lease assets and houses cannot be equated with Tokyo used-condominium resale inventory.",
              "- A full 15-company conclusion requires explicit coverage, classifications, missing-data discussion and cited figures.",
              "",
              "The table is generated by src/cohort.py and should be updated by GitHub Actions.",
              ""]
    return "\n".join(lines)

def main():
    groups=read(GROUPS)
    validate_primary_sources(groups,read(PRIMARY_SOURCES))
    cohort=build(groups,read(CONFIG),read(EDINET),read(EXTRACTED),read(IR),
                 read(ROOT/"data"/"processed"/"financial_facts.csv"),read(COMPARISON))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS)
        w.writeheader();w.writerows(cohort)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(render(cohort),encoding="utf-8")
    print(f"Mandatory groups: {len(groups)}; yearly coverage rows: {len(cohort)}")
    print("IR-covered group-years:",sum(int(r["primary_ir_rows"])>0 for r in cohort))

if __name__=="__main__": main()
