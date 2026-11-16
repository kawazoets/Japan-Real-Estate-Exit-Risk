# Tokyo resale condominium market — first sourced observation

**As-of:** 2026-11-16 (REINS October 2026 Monthly Market Watch, published 2026-11-10)

## Observation (Tokyo metropolitan prefecture, not Tokyo 23 wards)

| Market measure | Oct 2025 | Oct 2026 | Direction |
|---|---:|---:|---|
| REINS registered resale condominium inventory (units) | 22,722 | 31,981 | +40.7% |
| REINS contract registrations (units) | 2,234 | 1,670 | -25.2% |
| Mean transacted condominium price (JPY 10,000) | 7,028 | 6,640 | -5.5% |
| Mean active listing price (JPY 10,000) | 8,031 | 9,442 | +17.6% |
| Listed stock / that month's contract registrations | 10.17 | 19.15 | 1.88x |

**Official source:** https://www.reins.or.jp/pdf/trend/mw/MW_202610data.pdf  
**PDF pages:** printed p. 2 (contract situation, Tokyo), p. 4 (inventory situation, Tokyo).  
**Source release date:** November 10, 2026.

These data point to striking divergence **between seller-side listed inventory valuation and realized transaction-market averages**. The active-listing and contracted-property pools differ: the 9,442- vs 6,640-(10,000 JPY) figures **are not a matched price markdown**, and are **not evidence of a 2,802(10,000 JPY) negotiation discount**.

The stock/transaction ratio is only a market **pressure indicator**. It is NOT a literal 19.15-month sales time or cohort-specific inventory turnover. REINS changed its system in January 2025; its publisher warns that contract volumes might be affected.

## What this can and cannot establish

- **Established for Tokyo:** more resale condominium listings; fewer reported transactions; lower average transacted prices, while average active-listing prices rise.
- **Not established:** which listings are broker/developer-owned; whether specific resale operators deliberately discount or are unable to sell; matched-pair discount rates; the causal impact on Tokyo land prices.
- **Next empirical test:** compare the same period with core resale operators' FY2024–FY2026 inventory days, gross margins, debt funding, and operating cash flow. Refuse conflation of new-development inventory with resale condominium inventory.

## Editorial thesis under investigation

東京では中古マンションの売り物件が積み上がり、実際の取引は減り、成約平均価格も下がっている。それでも売出物件の平均価格は上がっている。

この乖離を資金繰りの面から説明できるか。高値で売れるまで待てる業者と、資金回収を急ぐ業者の差が成約価格にどう現れるか。現時点では**仮説であって結論ではない**。

## Data series

The source-linked observations (Oct 2025–Oct 2026) are in `data/processed/reins_monthly.csv`, including source URL, PDF page labels, and a provenance note. The REINS series includes owner-listed as well as brokerage/realtor listings and does not isolate repurchase/resale operators.
