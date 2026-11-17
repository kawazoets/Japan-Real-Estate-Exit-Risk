"""Tokyo condominium transaction mean-price change: wards versus Tama.
Counts weight mean per-square-meter prices. This is a two-group mechanical
decomposition, not a quality-adjusted (repeat sales/hedonic) price index.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data"/"processed"/"reins_tokyo_ward_tama.csv"
OUTPUT=ROOT/"data"/"processed"/"tokyo_composition_decomposition.csv"
COLS=["from_month","to_month","tokyo_mean_sqm_from_man_yen","tokyo_mean_sqm_to_man_yen",
      "change_man_yen_sqm","within_region_change_man_yen_sqm",
      "ward_tama_mix_change_man_yen_sqm","within_region_share_pct",
      "ward_tama_mix_share_pct","ward_contract_share_from_pct",
      "ward_contract_share_to_pct","source_url","interpretation"]

def compute(rows,first="2025-10",last="2026-10"):
    lookup={(r["month"],r["region"]):r for r in rows}
    def count(month,region):
        return int(lookup[(month,region)]["contracts_count"])
    def price(month,region):
        return float(lookup[(month,region)]["mean_contract_sqm_price_man_yen"])
    for m in (first,last):
        if count(m,"Tokyo_wards")+count(m,"Tama")!=count(m,"Tokyo_total"):
            raise ValueError("Tokyo ward + Tama contracts != Tokyo total")
        if count(m,"Tokyo_total")<=0:raise ValueError("No Tokyo contracts")
        weighted=(count(m,"Tokyo_wards")*price(m,"Tokyo_wards")
                  +count(m,"Tama")*price(m,"Tama"))/count(m,"Tokyo_total")
        if abs(weighted-price(m,"Tokyo_total"))>0.015:
            raise ValueError("Ward + Tama weighted price inconsistent with REINS Tokyo mean")
    p=count(first,"Tokyo_wards")/count(first,"Tokyo_total")
    q=count(last,"Tokyo_wards")/count(last,"Tokyo_total")
    a,b=price(first,"Tokyo_wards"),price(first,"Tama")
    c,d=price(last,"Tokyo_wards"),price(last,"Tama")
    # Exact two-component identity:
    # [p*c+(1-p)*d] - [p*a+(1-p)*b]
    # = p*(c-a)+(1-p)*(d-b) + (q-p)*(c-d)
    within=p*(c-a)+(1-p)*(d-b)
    mix=(q-p)*(c-d)
    delta=within+mix
    if abs(delta-((q*c+(1-q)*d)-(p*a+(1-p)*b)))>1e-9:
        raise ArithmeticError("decomposition identity failed")
    return {
        "from_month":first,"to_month":last,
        "tokyo_mean_sqm_from_man_yen":price(first,"Tokyo_total"),
        "tokyo_mean_sqm_to_man_yen":price(last,"Tokyo_total"),
        "change_man_yen_sqm":round(delta,4),
        "within_region_change_man_yen_sqm":round(within,4),
        "ward_tama_mix_change_man_yen_sqm":round(mix,4),
        "within_region_share_pct":round(100*within/delta,2) if delta else None,
        "ward_tama_mix_share_pct":round(100*mix/delta,2) if delta else None,
        "ward_contract_share_from_pct":round(p*100,2),
        "ward_contract_share_to_pct":round(q*100,2),
        "source_url":"https://www.reins.or.jp/mw_202610_summary.pdf",
        "interpretation":"ONLY_WARDS_VERSUS_TAMA_COMPOSITION; NOT_SAME_AS_CONSTANT_QUALITY_HOUSING_INDEX",
    }

def main():
    with INPUT.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    out=compute(rows)
    with OUTPUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLS)
        writer.writeheader();writer.writerow(out)
    print("Tokyo wards-versus-Tama decomposition:",out)

if __name__=="__main__": main()
