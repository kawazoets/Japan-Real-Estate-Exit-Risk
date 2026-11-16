"""Discover official East Japan REINS monthly report URLs without inventing market figures.

Discovery records are *documents*, not observations of sale prices or listing counts.
All numerical facts require separately verified, correctly scoped extraction.
"""
from __future__ import annotations
import argparse
import csv
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests

ROOT=Path(__file__).resolve().parents[1]
PAGES=["https://www.reins.or.jp/library/"+str(y)+".html" for y in range(2024,2027)]
OUTPUT=ROOT/"data"/"raw"/"reins_source_index.csv"
FIELDS=["report_month","report_kind","pdf_url","index_page","discovered_utc","verification"]
PDF_RE=re.compile(r"(?P<kind>Z?MW)_(?P<month>20\d{4})data\.pdf$",re.IGNORECASE)

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            href=dict(attrs).get("href")
            if href: self.hrefs.append(href)

def parse_index(html,base):
    parser=Anchors()
    parser.feed(html)
    found={}
    for href in parser.hrefs:
        url=urljoin(base,href)
        u=urlparse(url)
        if u.scheme!="https" or u.hostname not in ("www.reins.or.jp","reins.or.jp"): continue
        m=PDF_RE.search(u.path)
        if not m: continue
        key=(m.group("month")[:4]+"-"+m.group("month")[4:],
             "national" if m.group("kind").upper()=="ZMW" else "east_japan")
        found[key]=url
    return found

def update(session=None):
    session=session or requests.Session()
    existing={}
    if OUTPUT.exists():
        with OUTPUT.open(encoding="utf-8",newline="") as f:
            existing={(x["report_month"],x["report_kind"]):x for x in csv.DictReader(f)}
    errors=[]
    discovered=0
    for page in PAGES:
        try:
            response=session.get(page,timeout=35,headers={"User-Agent":"Japan-Real-Estate-Exit-Risk research/1.0"})
            response.raise_for_status()
            pdfs=parse_index(response.text,page)
            for (month,kind),url in pdfs.items():
                # Do not replace a previously captured PDF url without re-review.
                if (month,kind) not in existing:
                    existing[(month,kind)]={
                        "report_month":month,"report_kind":kind,"pdf_url":url,
                        "index_page":page,"discovered_utc":datetime.now(timezone.utc).isoformat(),
                        "verification":"OFFICIAL_INDEX_LINK_DISCOVERED_NOT_PARSED",
                    }
                    discovered+=1
        except requests.RequestException as exc:
            errors.append(page+": "+str(exc))
    if errors and not existing:
        raise RuntimeError("Unable to access any REINS index: "+"; ".join(errors))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(existing.values(),key=lambda r:(r["report_month"],r["report_kind"])))
    print("REINS report links:",len(existing),"new:",discovered,"index errors:",len(errors))
    for problem in errors: print("NOTICE:",problem)
    return discovered

if __name__=="__main__":
    update()
