# Japan Real Estate Exit Risk / 東京中古マンション「出口渋滞」

**研究上の問い：東京の中古マンション買取再販業者に、在庫の長期化と資金回収難が実際に起きているか。それは中古マンション価格へどう波及するか。**

一般論は語らない。一次資料の数字から市場の矛盾を発見し、切れ味のある論説を発表する。企業の売上が伸びていても、在庫・借入・資金回収期間がそれを上回っていないかを追跡する。

## 現状（初期構築）
- `config/companies.csv`: 調査候補15社（企業・証券コード・区分を管理）。約20社への拡張を予定。
- `src/edinet.py`: EDINET API v2で開示資料を検索し、CSV ZIPアーカイブを保存。資料IDと取得日を記録する。
- `src/analyze.py`: **検証済み**財務数値のみから在庫回転期間、粗利率、借入金・営業CFなどを算出。未検証値を推定しない。
- `.github/workflows/update.yml`: 毎週火・金に提出書類を確認する GitHub Actions。
- `data/processed/reins_monthly.csv`: REINS月次データの記録用テンプレート。

**現段階では、財務数値の自動抽出、REINSのPDF自動解析、20社への対象拡張は未完了です。** 資料の発見と財務データの検証済み収集は別工程です。空欄をゼロ扱いしません。

## 初回セットアップ
1. [EDINET](https://disclosure2.edinet-fsa.go.jp/) でAPIキーを取得する。
2. GitHub の **Settings → Secrets and variables → Actions → New repository secret** に `EDINET_API_KEY` として登録する。公開リポジトリのファイルにキーを書かない。
3. **Settings → Actions → General → Workflow permissions** で `Read and write permissions` を許可する。
4. **Actions → Update exit-risk evidence → Run workflow** で手動確認。以後火・金に定期実行する。
5. 2021年以降の過去分は `start`（例: 2021-01-01）と `days`（例: 30）を指定し、分割実行する。履歴の一括取得はまだ行っていない。

## 指標
- 在庫回転期間（日） = 365 × 期首期末平均棚卸資産 ÷ 年間売上原価。期首期末が比較可能な12か月決算に限る。
- 在庫増加率 = （期末棚卸資産－前期末棚卸資産）÷前期末棚卸資産。
- 粗利率 = 売上総利益 ÷ 売上高。
- 営業CFの赤字だけで販売不振と判定しない。大量仕入れなどの成長投資でも発生する。
- EDINETの企業連結数値と東京中古マンションの地域別在庫は同じ母集団ではない。
- REINSの売出在庫は個人・業者混在。業者保有在庫と同一視しない。

## 一次資料
- [EDINET API](https://disclosure2.edinet-fsa.go.jp/)
- [東日本REINS](https://www.reins.or.jp/)

## Facebook
更新したデータの報告ではなく、検証済みの**独自の発見**とその経済的意味を投稿する。