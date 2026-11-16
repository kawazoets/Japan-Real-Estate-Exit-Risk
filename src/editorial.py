"""Publication gate: data coverage and absence of unsupported conclusions."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from .analyze import ROOT

def load(path):
    if not path.exists():return []
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def render(company,market):
    recent=[r for r in company if (r.get("fiscal_end") or "")[:4] in ("2024","2025","2026")]
    per_company=defaultdict(set)
    for r in recent:
        if r.get("inventory_days","").strip():
            per_company[r["ticker"]].add(r["fiscal_end"][:4])
    series={ticker:sorted(years) for ticker,years in per_company.items() if len(years)>=2}
    tokyo=[r for r in market if "東京" in r.get("geography","") or "Tokyo" in r.get("geography","")]
    months={r["observation_month"] for r in tokyo}
    ready=bool(series) and len(months)>=12
    lines=["# Publication readiness: Tokyo condominium resale exit congestion","",
           "**NOT READY FOR PUBLICATION**" if not ready else "**DATA COVERAGE THRESHOLD REACHED — analytical review still required**","",
           "Core question: Are resale operators unable to liquidate condominium inventory at expected prices, despite rising Tokyo real-estate valuations?","",
           "- Preliminary company indicator rows (2024-2026): **"+str(len(recent))+"**",
           "- Companies with >=2 annual inventory-day readings: **"+str(len(series))+"**",
           "- Tokyo-market observations (monthly): **"+str(len(months))+"**",
           "",
           "This is a DATA COVERAGE gate, not proof of exit congestion. Observations may still be machine-extracted and company-wide rather than Tokyo condominium-specific.","",
           "## Required before a Facebook article","",
           "1. Consecutive fiscal years with compatible inventory definitions; inspect EDINET report against extracted figures.",
           "2. Relevant condominium segment exposure (Tokyo / resale), not just mixed corporate holdings.",
           "3. Sourced REINS Tokyo-level monthly inventory, contracts and realized price series; cite precise pages.",
           "4. Contrast inventory turnover, margins and funding pressure with contemporaneous market activity.",
           "5. Explicitly handle REINS' 2025 registration-system changes before comparing contract counts across the break.",
           "6. Do not treat REINS stock-to-monthly-contracts ratio as a literal time-on-market or matched ask-to-sale discount.",
           "",
           "## Potential longitudinal company sets (unverified)",""]
    if series: lines += ["- "+k+": "+", ".join(v) for k,v in sorted(series.items())]
    else: lines.append("- None yet")
    return "\n".join(lines)+"\n"

def main():
    company=load(ROOT/"data"/"processed"/"candidate_indicators.csv")
    market=load(ROOT/"data"/"processed"/"market_signals.csv")
    target=ROOT/"docs"/"EDITORIAL.md"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(render(company,market),encoding="utf-8")
    print("Saved publication gate:",target)
if __name__=="__main__":main()
