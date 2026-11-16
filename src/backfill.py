"""Resume historical EDINET discovery automatically from 2021 in bounded batches."""
from __future__ import annotations
import argparse
import json
import os
from datetime import date,timedelta
from pathlib import Path
from .edinet import ROOT, discover, download_csvs
from .extract import extract_all

STATE=ROOT/"data"/"raw"/"backfill_state.json"
ORIGIN=date(2021,1,1)

def execute(days=120,archive_limit=50,delay=2.5):
    key=os.environ.get("EDINET_API_KEY","").strip()
    if not key: raise SystemExit("Missing EDINET_API_KEY")
    state=json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"next_date":ORIGIN.isoformat()}
    start=date.fromisoformat(state["next_date"])
    yesterday=date.today()-timedelta(days=1)
    if start<=yesterday:
        span=min(days,(yesterday-start).days+1)
        scanned,files=discover(start,span,key,delay)
        next_date=start+timedelta(days=span)
        state["next_date"]=next_date.isoformat()
        state["last_batch_start"]=start.isoformat()
        state["last_batch_days"]=span
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("historical batch:",start,span,"dates; next",next_date)
    else:
        print("historical backfill date scan complete")
    # Important: annual filings only; limit prevents excessively large runs.
    downloaded=download_csvs(key,archive_limit,delay)
    extracted=extract_all()
    print("archives downloaded:",downloaded,"annual candidate rows extracted:",extracted)
    return state

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--days",type=int,default=120)
    parser.add_argument("--archive-limit",type=int,default=50)
    parser.add_argument("--delay",type=float,default=2.5)
    args=parser.parse_args()
    if not 1<=args.days<=180: raise SystemExit("days must be 1..180")
    execute(args.days,args.archive_limit,args.delay)
if __name__=="__main__":main()
