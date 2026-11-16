"""Append Tokyo resale condominium monthly statistics from newly published official REINS PDFs.

Only append after matching exact month, geography, section, and arithmetic.
No statistical values are invented. Existing observations are never silently rewritten.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import fitz
import requests
from .analyze import ROOT
from .reins_sources import parse_index

CSV_PATH=ROOT/"data"/"processed"/"reins_monthly.csv"
STATE=ROOT/"data"/"raw"/"reins_monthly_state.json"
COLUMNS=["observation_month","geography","inventory_count","contracts_count","contract_price_jpy",
         "contract_sqm_price_jpy","source_url","source_page","audit_note"]
BASE="https://www.reins.or.jp/library/"
PDF_RE=re.compile(r"/MW_(20\\d{4})data\\.pdf$", re.IGNORECASE)
RECORD_MONTH=re.compile(r"^(?:(?:20)?\\d{2}/)?(0[1-9]|1[0-2])$")
NUMERIC=re.compile(r"^[+\\-−－]?[\\d,]+(?:\\.\\d+)?$")
PAGE_INDEX_CONTRACT=1
PAGE_INDEX_INVENTORY=3

def latest_urls(session, current=None):
    current=current or date.today()
    links={}
    # Annual index URLs must really link to the PDF; never trust a guessed filename.
    for year in (current.year-1,current.year):
        try:
            resp=session.get(BASE+str(year)+".html",timeout=35,
                             headers={"User-Agent":"Japan-Real-Estate-Exit-Risk/1.0"})
            resp.raise_for_status()
        except requests.RequestException as exc:
            print("REINS index unavailable:",year,str(exc),file=sys.stderr)
            continue
        for (month,kind),url in parse_index(resp.text,resp.url).items():
            if kind!="east_japan":continue
            match=PDF_RE.search(urlparse(url).path)
            if not match or month != match.group(1)[:4]+"-"+match.group(1)[4:]:continue
            if month > current.strftime("%Y-%m"):continue
            links[month]=url
    return links

def numbers_from_tokiotable(text,month):
    """Extract the latest-month row from the Tokyo table on a *known* report page.

    The original PDF uses 13 columns: year/month, count, count yoy,
    sqm price, sqm yoy/mom, mean price, price yoy/mom, area yoy/mom, age.
    """
    normalized=text.replace("−","-").replace("－","-").replace("，",",")
    # The Tokyo prefecture section is explicitly bounded by prefecture headings.
    parts=re.split(r"[○◯]\\s*東京都",normalized,maxsplit=1)
    if len(parts)!=2: raise ValueError("Tokyo section heading not found")
    end=re.split(r"[○◯]\\s*埼玉県",parts[1],maxsplit=1)[0]
    month_num=int(month[-2:])
    matches=[]
    for line in end.splitlines():
        cells=line.strip().split()
        if len(cells)<12: continue
        first=cells[0]
        mo=RECORD_MONTH.fullmatch(first)
        if not mo or int(mo.group(1))!=month_num:continue
        if not all(NUMERIC.fullmatch(v) for v in cells[1:13]):continue
        try:
            values=[float(v.replace(",","")) for v in cells[1:13]]
        except ValueError:continue
        n=int(values[0]); sqm=values[2]; price=values[5]
        area=values[8]
        # Reject accidentally selected different tables or shifted columns.
        if not (50<=n<=1000000 and 1<=sqm<=2000 and 100<=price<=100000
                and 5<=area<=300 and abs(price/sqm-area)<0.6):
            continue
        matches.append((n,sqm,price))
    if len(matches)!=1:raise ValueError("Expected exactly one Tokyo row for "+month+", found "+str(len(matches)))
    return matches[0]

def extract_pdf(pdf_bytes,month):
    with fitz.open(stream=pdf_bytes,filetype="pdf") as doc:
        if len(doc)<4:raise ValueError("Report PDF shorter than four pages")
        cover=doc[0].get_text()
        year,mon=month.split("-")
        if year not in cover or not re.search(r"0?"+str(int(mon))+r"月",cover):
            raise ValueError("PDF cover does not match requested report month: "+month)
        n_contract,sqm_contract,price_contract=numbers_from_tokiotable(doc[PAGE_INDEX_CONTRACT].get_text(sort=True),month)
        n_stock,sqm_stock,price_stock=numbers_from_tokiotable(doc[PAGE_INDEX_INVENTORY].get_text(sort=True),month)
        return {
            "observation_month":month,"geography":"Tokyo",
            "inventory_count":n_stock,"contracts_count":n_contract,
            "contract_price_jpy":int(round(price_contract*10000)),
            "contract_sqm_price_jpy":int(round(sqm_contract*10000)),
            "source_page":"2;4",
            "audit_note":"PDF_AUTO_EXTRACTED_REINS_TOKYO_PREFECTURE_WITH_ARITHMETIC_CHECKS_NOT_OPERATOR_SPECIFIC",
            "_listing_price_jpy":int(round(price_stock*10000)),
            "_listing_sqm_price_jpy":int(round(sqm_stock*10000)),
        }

def load_rows():
    if not CSV_PATH.exists():return []
    with CSV_PATH.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def write_rows(rows):
    CSV_PATH.parent.mkdir(parents=True,exist_ok=True)
    with CSV_PATH.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(sorted(rows,key=lambda r:(r["observation_month"],r["geography"])))

def run(session=None):
    session=session or requests.Session()
    existing=load_rows()
    known={r["observation_month"] for r in existing if r.get("geography")=="Tokyo"}
    links=latest_urls(session)
    if not links:
        raise RuntimeError("No official REINS East Japan report links discovered")
    new=[]
    # Latest reports are prioritized; no alert for a previously recorded month.
    for month,url in sorted(links.items()):
        if month in known: continue
        response=session.get(url,timeout=90)
        response.raise_for_status()
        if not response.content.startswith(b"%PDF"):
            raise ValueError("Non-PDF response for "+month)
        record=extract_pdf(response.content,month)
        record["source_url"]=url
        record.pop("_listing_price_jpy")
        record.pop("_listing_sqm_price_jpy")
        existing.append(record)
        new.append(record)
    if new:write_rows(existing)
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({"checked_utc":datetime.now(timezone.utc).isoformat(),
           "new_months":[r["observation_month"] for r in new],
           "latest_official_month":max(links)},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print("new_months="+",".join(r["observation_month"] for r in new))
    return new

if __name__=="__main__":
    run()
