# 7Harvest MarginOS — Final QA and demonstration readiness

## Verdict
**Conditional / not fully demonstration-certified.** Tested source: `7Harvest_MarginOS_presentation.zip`. Static and computational checks completed; browser-level Streamlit interaction and clean installation were **not** executed because Streamlit is not installed in this environment and the package index is unreachable. The application therefore must be smoke-tested on the presentation laptop before the event.

## Executed tests
`python -m pytest -q`: **33 passed, 3 expected failures (xfail), 0 unexpected failures**. `python -m compileall -q app.py core.py data tests`: passed. The 3 xfails explicitly represent known, unimplemented requirements; they are not successes.

| Feature | Result | Evidence / qualification |
|---|---|---|
| Clean install and Streamlit browser launch | NOT TESTED | `streamlit` unavailable; pip could not reach package index |
| Demo data load | PASS (Python) | 221,940 sales rows, 27 SKUs, 15 outlets, 75 agreement rows; CSVs parsed |
| Referential integrity | PASS | All checked SKU/outlet keys valid; agreement keys unique and complete |
| Gross sales reconciliation | PASS | Unit price × units reconciles to gross sales |
| Forecast training | PASS (Python) | Gradient boosting fit and predictions executed on SO001/O01 |
| Historical vs forecast separation | PASS (code) | Distinct holdout and recursive future outputs; browser legend not tested |
| Chronological holdout | PASS (code) | Train, validation and test periods sequential |
| MAE/WAPE/bias | PASS (sample) | Calculated from holdout predictions, not hardcoded |
| Leakage | PASS (feature inspection) | Lagged observed sales; no latent demand or future target in feature list. Holdout is one-step, not recursive |
| Forecast uncertainty | PASS (label inspection) | Heuristic validation-error interval, not calibrated probability |
| RK type-based rebates | PASS | Separate customer/type aggregation and rate application |
| Soorya customer discount | PASS | One customer/Soorya type rate applied to gross sales |
| Missing rebate agreement | PASS | Raises explicit ValueError |
| Listing fee payback | FAIL / NOT IMPLEMENTED | No actual contribution-based listing fee payback calculation or display |
| Retail contribution | PARTIAL | Fixed overview to include modeled listing and recurring trade fees; vehicle, expiry, overhead excluded |
| Replenishment case and supply limits | PASS | Case multiple and available supply constraints tested |
| Existing stock expiry by lot | FAIL | FEFO only excludes already-expired lots; no future lot depletion/expiry simulation |
| Route capacity | PASS | Capacity enforced even when deliveries require multiple trips |
| Temperature compatibility | PASS | Incompatible demand reported unmet |
| Route time windows / max hours | FAIL | Not enforced; displayed routes cannot be called time-feasible |
| Route recalculation on multiplier | PASS (code), UI NOT TESTED | Slider feeds deliveries and route_plan on rerun |
| SmartShelf scoring weights | PASS | Different weight sets produce different scores |
| Outlet-specific SmartShelf main page | FAIL | Global outlet filter does not restrict the main SmartShelf dataset |
| Scenario reconciliation | PARTIAL | Incompatible windows not summed; TradeSmart omits existing trade fees from scenario bridge |
| CSV export | PASS (code), UI NOT TESTED | Download buttons serialize DataFrames; actual browser downloads untested |
| Invalid uploaded CSV | FAIL | No file upload control; core validator rejects negatives, unknown SKUs and missing columns when invoked |
| Extreme chart inputs | NOT TESTED | No browser renderer available |
| Reset | PARTIAL | Expanded reset to presentation selections; browser state not tested |
| No external APIs | PASS (source inspection) | No API calls in core application; dependency installation still requires packages |
| All buttons and filters | NOT VERIFIED | Streamlit browser interaction unavailable; some global filters do not propagate |

## Forecast example (actual executed, SO001/O01, one-step test)
- Train end: 2026-03-27; validation end: 2026-06-25; test: 2026-06-26 to 2026-09-30.
- ML MAE: **2.9515 units**; seasonal naive MAE: **3.9897 units**.
- ML WAPE: **36.38%**; seasonal naive WAPE: **49.17%**.
- ML bias (prediction minus observed): **-0.1853 units/day**.
- These metrics describe one synthetic outlet/SKU series, not portfolio-wide accuracy; holdout uses observed lagged values.

## Defects corrected in this QA pass
1. Overview contribution previously omitted synthetic listing and recurring trade fees; now includes these and clearly labels remaining exclusions. Previous omission in this dataset: **AED 174,015.48** over 18 modeled months.
2. Scenario reset now also clears presentation-specific selectors, supply and horizon, instead of leaving those controls unchanged.
3. Route scenario no longer records a monetary benefit when deliveries are unmet.
4. Added 15 targeted QA tests, including 3 strict expected failures for unresolved deficiencies.

## Outstanding material limitations
- Browser launch, chart rendering, all buttons, download clicks, and full clean installation remain unverified.
- No uploaded CSV interface; negative and unknown input checks are only exercised programmatically.
- No validated listing-fee payback metric, promoter causal uplift, or fully allocated contribution.
- Replenishment does not simulate FEFO lot consumption and expiry through time; `expected_unsold_units` is only a simple aggregate estimate.
- Routing is straight-line nearest-neighbour with capacity/temperature checks; no time windows, travel time, vehicle hours, real road network, or fleet scheduling.
- Main SmartShelf does not obey global outlet selection, and scores exclude rebates/shared trade costs.
- Forecast holdout is one-step with observed lags; recursive future accuracy is not established by that metric.
- Model can train on synthetic historical observed sales only; synthetic seasonality is illustrative, not a validated UAE event calendar.
- TradeSmart what-if does not include all existing retailer costs, so its difference is a partial contribution comparison.
- The synthetic 548-day dataset runs 2025-04-01 through 2026-09-30.

## Installation and launch
On the event laptop, use Python 3.11 or 3.12. From the extracted `7Harvest_MarginOS` directory:

Windows PowerShell:
```
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

macOS/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Install dependencies and open the app once while online, then disconnect network and verify the same workflow. If `py -3.11` is not available, use the installed compatible Python executable. Do not claim the app is offline-ready until this laptop test succeeds.

## 90-second demonstration (rehearsal plan, not browser-verified)
- **0–10 s:** Open **Executive Overview**; point out the synthetic-data warning and three summary KPIs. Say: “This is a reproducible proof of concept, not 7Harvest's operational data.”
- **10–35 s:** Choose **Presentation Mode** → **01 · Soorya expiry**. Keep default SKU/outlet; change **Safety allowance** from 15% to 5%. Point to baseline/proposed units and the forecast. Say: “Demand forecasts inform a case- and supply-constrained delivery proposal. Expiry benefit is not yet validated.”
- **35–58 s:** Select **02 · Retail trade terms**; choose a retail account and change **Change rebate rates** from -1.00 to -0.50 percentage points. Point to baseline/proposed rebate expense. Say: “RK rebate calculations are performed separately by item type; the agreement rates here are synthetic.”
- **58–80 s:** Select **03 · RK assortment**; choose a category with two or more products, then change **Hypothetical sales transfer** from 50% to 25%. Point to gross contribution comparison. Say: “The result is sensitive to substitution assumptions; we recommend review, not automatic delisting.”
- **80–90 s:** Point to synthetic-data disclaimer and conclude: “The model makes assumptions and trade-offs visible before a real pilot.”

## Backup demonstration
1. Before event: run the app, warm the chosen forecast cache, export `freshflow_forecast.csv`, `tradesmart_account_contribution.csv`, and `smartshelf_sku_scores.csv`, and take screenshots of the three presentation tabs at the exact chosen settings. Keep them in a local offline folder.
2. If forecasting fails: show the saved forecast CSV and its **actual recorded** test metrics, clearly marking them as a previously executed synthetic demonstration; do not pretend the live model just ran.
3. If routing fails: skip RouteSync; show its saved route CSV or screenshot from a successful rehearsal and disclose that the optimisation is not running live.
4. If Streamlit fails: show the three locally saved screenshots in sequence and use the 90-second script; avoid claiming live interactivity.
5. Do not use screenshots or metrics from another run unless their date, SKU, outlet, and settings are recorded.
