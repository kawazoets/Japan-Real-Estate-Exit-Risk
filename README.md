## レインズ月次更新・通知

- [REINS Monthly Tokyo Market Monitor](.github/workflows/reins-monthly.yml) は毎日 **10:40 シンガポール時間**に東日本レインズの公式月例PDFの公開を確認する（GitHub Actions の cron は 02:40 UTC）。
- 新しい公表月が **既存の最新月より新しい場合のみ**、東京都中古マンションの売出在庫、成約件数、成約平均価格、売出平均価格、㎡単価をPDFの当該月の行から抽出して追記する。
- 元PDFに該当する月・地域・数値構成を確認できなければ**更新せずにエラーで停止**する。手入力した過去の月別数値を上書きしない。
- データの保存に成功した新規月のみ、GitHub Issueを作成し、リポジトリ所有者 `kawazoets` を担当者にして通知する。メール通知の配送はGitHubの通知設定による。
- ChatGPT側にも「東日本レインズ月次更新通知」の条件付き日次監視を別途設定済み。新規公表がなければ通知しない。
- 月次CSV: [reins_monthly.csv](data/processed/reins_monthly.csv) ｜ 市場圧力指標: [market_signals.csv](data/processed/market_signals.csv)
- **対象は東京都全体の中古マンション**。東京23区だけではなく、所有者が買取再販業者であるかの識別もできない。売出平均と成約平均は別々の物件集団で、差額は値引額ではない。

# Japan Real Estate Exit Risk / 東京中古マンション「出口渋滞」

**研究上の問い：東京の中古マンション買取再販業者に、在庫の長期化と資金回収難が実際に起きているか。それは中古マンション価格へどう波及するか。**

一般論は語らない。一次資料の数字から市場の矛盾を発見し、切れ味のある論説を発表する。企業の売上が伸びていても、在庫・借入・資金回収期間がそれを上回っていないかを追跡する。

## 最初の市場側の発見（2026年10月）
**東京都の中古マンション売出在庫は前年同月比+40.7%、成約件数は-25.2%、平均成約価格は-5.5%。一方、売出在庫の平均価格は+17.6%。** 出典：東日本REINS 2026年10月月例マーケットウォッチ（2026-11-10公表、p.2/4）。異なる物件群の平均価格の差は**値引き額ではない**。

- [市場データ（2025年10月〜2026年10月）](data/processed/reins_monthly.csv)
- [最初の市場観測と限界](docs/MARKET_SNAPSHOT.md)
- [研究・論説の公開条件](docs/EDITORIAL.md)

**業者の出口渋滞が立証されたわけではありません。** 買取再販業者の資金回収に関する証拠は、今後のEDINET年次データで検証します。

## 現状（初期構築）
- `config/companies.csv`: 調査候補15社（企業・証券コード・区分を管理）。約20社への拡張を予定。
- `src/edinet.py`: EDINET API v2で開示資料を検索し、CSV ZIPアーカイブを保存。資料IDと取得日を記録する。
- `src/analyze.py`: **検証済み**財務数値のみから在庫回転期間、粗利率、借入金・営業CFなどを算出。未検証値を推定しない。
- `.github/workflows/update.yml`: 毎日09:12（シンガポール時間）に提出書類を確認し、2021年から過去資料を120日ずつ遡らず順に収集する GitHub Actions。
- `data/processed/reins_monthly.csv`: REINS月次データの記録用テンプレート。

**現段階では、財務数値の機械抽出候補は実装済み（検証済みへの昇格は未実装）。REINSのPDF自動解析、20社への対象拡張は未完了です。** 資料の発見と財務データの検証済み収集は別工程です。空欄をゼロ扱いしません。

## 初回セットアップ
1. [EDINET](https://disclosure2.edinet-fsa.go.jp/) でAPIキーを取得する。
2. GitHub の **Settings → Secrets and variables → Actions → New repository secret** に `EDINET_API_KEY` として登録する。公開リポジトリのファイルにキーを書かない。
3. **Settings → Actions → General → Workflow permissions** で `Read and write permissions` を許可する。
4. **Actions → Update exit-risk evidence → Run workflow** で手動確認。以後毎日定期実行する。
5. 2021年以降の過去分は、日次実行ごとに120日分ずつ自動バックフィルする。進捗は `data/raw/backfill_state.json` に記録し、中断時は再開する。

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