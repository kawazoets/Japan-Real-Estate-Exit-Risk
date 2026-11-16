"""Generate a brief source-linked GitHub Issue for the newly detected REINS month."""
from __future__ import annotations
import csv
import os
from .analyze import ROOT

def main():
    months=[x for x in os.environ.get("NEW_MONTHS","").split(",") if x]
    if not months: raise SystemExit("No new publication month")
    with (ROOT/"data"/"processed"/"reins_monthly.csv").open(encoding="utf-8",newline="") as f:
        rows={x["observation_month"]:x for x in csv.DictReader(f) if x["geography"]=="Tokyo"}
    print("東日本レインズの月次統計が新たに公開され、東京都の中古マンション市場データをGitHubに保存しました。\n")
    for month in months:
        r=rows[month]
        print("## "+month)
        print("- 売出在庫："+format(int(r["inventory_count"]),",")+"件")
        print("- 成約件数："+format(int(r["contracts_count"]),",")+"件")
        print("- 成約平均価格："+format(int(r["contract_price_jpy"])//10000,",")+"万円")
        if r.get("listing_price_jpy"):
            print("- 売出在庫の平均価格："+format(int(r["listing_price_jpy"])//10000,",")+"万円")
        print("- 在庫÷当月成約件数："+format(int(r["inventory_count"])/int(r["contracts_count"]),".2f"))
        print("- 一次資料："+r["source_url"])
        print("- 参照ページ："+r["source_page"]+"\n")
    print("注意：在庫÷当月成約件数は販売期間ではありません。売出平均価格と成約平均価格の差は同一物件の値引きではありません。")
    print("この更新は東京の買取再販業者の『出口渋滞』を立証するものではありません。")

if __name__=="__main__":main()
