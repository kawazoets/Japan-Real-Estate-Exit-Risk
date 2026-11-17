"""Validate 23-ward five-district October condominium resale evidence without inventing turnover time."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"data"/"processed"/"tokyo_23wards_five_regions_202610.csv"
REGIONS={"central3","south","west","north","east"}
def read():
    with PATH.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def validate(rows):
    codes=[r["region_code"] for r in rows]
    if len(rows)!=5 or set(codes)!=REGIONS or len(set(codes))!=5:
        raise ValueError("Expected exactly Tokyo wards five districts; original scope cannot change")
    if any(r["observation_month"]!="2026-10" for r in rows):
        raise ValueError("Unknown reporting month")
    if sum(int(r["contracts_count"]) for r in rows)!=1343:
        raise ValueError("Sum of district contracts differs from REINS official Tokyo wards total")
    if sum(int(r["inventory_count"]) for r in rows)!=28322:
        raise ValueError("Sum of district stocks differs from 31981 Tokyo minus 3659 Tama")
    for r in rows:
        n=int(r["contracts_count"]);stock=int(r["inventory_count"])
        ratio=float(r["stock_to_monthly_contract_ratio"])
        if n<=0 or stock<=0 or abs(ratio-stock/n)>0.011:
            raise ValueError("Invalid district stock-to-contract signal")
        if r["audit_status"]!="SECONDARY_REINS_TRANSCRIPTION_OFFICIAL_DISTRICT_PDF_CROSSCHECK_PENDING":
            raise ValueError("Do not silently promote secondary district figures into official verification")
    return True
def main():
    validate(read())
    print("Five-district Tokyo resale controls passed: contracts=1343, stock=28322; primary crosscheck pending")
if __name__=="__main__":main()
