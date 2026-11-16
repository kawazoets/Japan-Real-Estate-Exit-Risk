# Research protocol — 東京中古マンション買取再販業者の出口渋滞

## Main question
Have resale operators begun to face a prolonged exit from Tokyo condominium inventories, and does this pressure propagate to secondary-market transaction prices?

We **do not** generalize property-company inventories as Tokyo condominium stock. Each cross-company measure must identify segment mix, inventory definition, debt profile, and disclosure period.

## Evidence hierarchy
1. Original annual reports filed on EDINET, tied to EDINET document IDs.
2. REINS regional market data, keeping seller type and geography explicit.
3. Quarterly/half-year statements only as interim directional evidence, not combined mechanically with full-year figures.
4. Narrative claims remain hypotheses until supported by traceable observations.

## Company comparability
- **Core sample:** firms with genuine resale/acquisition stock. Document condominium share if disclosed.
- **Comparison only:** developers of new investment condominiums and companies dominated by land development, rental, or detached houses.
- Never combine sales from all segments with condominium inventory for a false turnover metric.

## Metrics to test the exit-congestion thesis
- Ending inventory; growth versus sales/cost of goods sold.
- Inventory days with annual cost of sales and average opening/closing inventory.
- Gross margin and gross margin compression.
- Short-term debt, interest expenses, operating cash flow.
- Candidate distress signal: inventory duration rises while gross margin falls and borrowing pressure increases — with at least two annual periods and verified comparable inventory definitions.
- Compare corporate data with Tokyo-specific secondary market listing stock, contract counts, and realized prices; disclose differences in scope.

## Critical caveats
- A negative operating cash flow can reflect aggressive buying, not an unsold stock problem.
- Inventory growth alone does not establish exit congestion.
- For yearly observations, consolidated balance-sheet concepts can have different definitions from disclosed real-estate inventory components.
- Automated extract rows live in `financial_candidates.csv`, with XBRL tags and unreviewed status. Independent verification is necessary before asserting a numerical conclusion.
- EDINET source CSV files use UTF-16 tab-separated XBRL fact records. See official EDINET user documentation: https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/download/ESE140133.pdf

## Publication style
No generic real-estate-market commentary. Publication should foreground one specific numerical discovery, test its rival explanation, and deliver a defensible interpretation. Numbers and claims must be traceable.

## Backfill
The daily workflow progressively indexes original annual EDINET filings from 2021 to present, 120 calendar days per successful run. It writes `data/raw/backfill_state.json`. Source IDs, machine-extracted facts and provisional indicators are retained in GitHub. Original ZIP payloads are not newly committed; they may be fetched again from EDINET as necessary.
