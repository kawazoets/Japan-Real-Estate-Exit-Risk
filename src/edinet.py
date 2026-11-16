"""Discover EDINET filings and archive disclosure-derived CSV ZIPs."""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.edinet-fsa.go.jp/api/v2"
RAW = ROOT / "data" / "raw"
FIELDS = ["ticker","company","doc_id","edinet_code","submit_datetime","period_start","period_end","doc_type_code","doc_description","xbrl_flag","csv_flag","source_api","retrieved_utc"]

def companies():
    with (ROOT / "config" / "companies.csv").open(encoding="utf-8-sig", newline="") as f:
        return {row["ticker"]: row for row in csv.DictReader(f)}

def normalized_ticker(security_code):
    code = str(security_code or "").strip()
    return code[:4] if len(code)==5 and code.endswith("0") else (code if len(code)==4 else "")

def fetch(session, url, key, params):
    params = dict(params, **{"Subscription-Key":key})
    for attempt in range(4):
        try:
            response = session.get(url, params=params, timeout=45)
            if response.status_code in (429,500,502,503,504):
                time.sleep(min(30,3*2**attempt))
                continue
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt==3:
                raise
            time.sleep(min(30,3*2**attempt))
    raise RuntimeError("EDINET request failed: "+url)

def discover_day(session, key, day, universe):
    response = fetch(session, API+"/documents.json", key, {"date":day,"type":2})
    payload = response.json()
    if payload.get("metadata",{}).get("status") not in (None,"200",200):
        raise RuntimeError("EDINET API status: "+str(payload["metadata"]))
    rows=[]
    for document in payload.get("results") or []:
        ticker=normalized_ticker(document.get("secCode"))
        if ticker not in universe or str(document.get("docTypeCode")) not in {"120","130","140","150","160","170"}:
            continue
        if str(document.get("withdrawalStatus") or "0") not in ("0",""):
            continue
        rows.append({
            "ticker":ticker, "company":universe[ticker]["company"], "doc_id":document.get("docID",""),
            "edinet_code":document.get("edinetCode",""), "submit_datetime":document.get("submitDateTime",""),
            "period_start":document.get("periodStart",""), "period_end":document.get("periodEnd",""),
            "doc_type_code":document.get("docTypeCode",""), "doc_description":document.get("docDescription",""),
            "xbrl_flag":document.get("xbrlFlag",""), "csv_flag":document.get("csvFlag",""),
            "source_api":API+"/documents.json?date="+day+"&type=2",
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
        })
    return rows

def load_csv(path):
    if not path.exists(): return []
    with path.open(encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def discover(start, days, key, delay):
    universe=companies()
    state=RAW/"scanned_dates.json"
    scanned=set(json.loads(state.read_text()) if state.exists() else [])
    manifest=RAW/"edinet_documents.csv"
    records={r["doc_id"]:r for r in load_csv(manifest)}
    with requests.Session() as session:
        for i in range(days):
            day=(start+timedelta(days=i)).isoformat()
            if day > date.today().isoformat(): break
            if day in scanned: continue
            for row in discover_day(session,key,day,universe):
                records[row["doc_id"]]=row
            scanned.add(day)
            write_csv(manifest,sorted(records.values(),key=lambda r:(r["submit_datetime"],r["doc_id"])),FIELDS)
            state.parent.mkdir(parents=True,exist_ok=True)
            state.write_text(json.dumps(sorted(scanned),ensure_ascii=False,indent=2)+"\n")
            time.sleep(delay)
    return len(scanned),len(records)

def download_csvs(key, limit, delay):
    manifest=load_csv(RAW/"edinet_documents.csv")
    directory=RAW/"filings"
    directory.mkdir(parents=True,exist_ok=True)
    count=0
    with requests.Session() as session:
        for row in manifest:
            doc_id=row["doc_id"]
            if str(row["csv_flag"])!="1" or not doc_id: continue
            destination=directory/(doc_id+".zip")
            if destination.exists(): continue
            if count>=limit: break
            response=fetch(session,API+"/documents/"+doc_id,key,{"type":5})
            if not zipfile.is_zipfile(io.BytesIO(response.content)):
                raise RuntimeError("Expected ZIP for EDINET "+doc_id)
            destination.write_bytes(response.content)
            count+=1
            time.sleep(delay)
    return count

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--start",default=(date.today()-timedelta(days=12)).isoformat())
    parser.add_argument("--days",type=int,default=13)
    parser.add_argument("--download",type=int,default=8)
    parser.add_argument("--delay",type=float,default=3.0)
    args=parser.parse_args()
    key=os.environ.get("EDINET_API_KEY","").strip()
    if not key: raise SystemExit("Missing EDINET_API_KEY. Add GitHub Actions repository secret.")
    if not (1<=args.days<=60): raise SystemExit("--days must be between 1 and 60")
    scanned,found=discover(date.fromisoformat(args.start),args.days,key,args.delay)
    downloaded=download_csvs(key,args.download,args.delay)
    print(f"EDINET scanned={scanned}; matched filings={found}; downloaded ZIPs={downloaded}")

if __name__=="__main__":
    main()
