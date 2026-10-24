# Independent validation report — 7Harvest MarginOS v2

## Tests passed
- 15 automated tests passed (`pytest -q tests`), including original nine and six new audit tests.
- Deterministic synthetic generation; sales/product/outlet/contract/lot foreign keys and key uniqueness.
- Sales amounts reconcile to observed units times SKU wholesale price; latent synthetic demand equals observed sales plus simulated lost units.
- Customer/type rebates reconcile arithmetically; route temperature/capacity checks and case/supply caps.
- Actual trained HistGradientBoostingRegressor, chronological split, and a separate 60-day recursive backtest.
- Model inputs in `core.forecasting_frame` are lagged observed sales, prior rolling average and calendar; hidden latent demand not used.

## Tests failed / checks not passed
- Full browser interactivity and chart-refresh tests NOT EXECUTED: Streamlit is not installed in this validation environment.
- Original app's displayed one-step MAE/WAPE are not multi-day recursive performance and can mislead if described as 7/14-day performance.
- Inventory expiry simulation is incomplete: `fefo_stock` sums eligible lots but `replenish` uses scalar stock, not lot-by-lot expiry consumption.
- Route planner does not enforce time windows, driver hours, unique physical vehicle reuse, or real-road distances; multi-trip reuse may be infeasible.
- SmartShelf contribution excludes rebates and trade costs and cannot substantiate delisting profitability.
- TradeSmart scenario contribution excludes other brand cost lines; the outlet ranking allocates the full 18-month period fees without verified fee dates.
- Scenario state can become stale when global retailer/brand selection changes; no automatic invalidation or chart interaction tests.

## Problems discovered
1. Original test graph uses observed historical lag values at each test date; this is valid for one-step prediction but not for a multi-day deployment claim.
2. Synthetic `expired_units` is sampled from sold units independently and is not deducted from sales or reconciled with physical inventory; it is a synthetic write-off indicator, not a stock-flow ledger.
3. Expiry stock calculation includes lots expiring on the as-of date and does not account for consumption timing or lead time.
4. Replenishment projected unsold is a simplistic horizon surplus, not an expiry-batch simulation. User-selected delivery quantity does not recalculate the projected waste.
5. The routing engine can assign repeated trips to the same named vehicle without checking the operating day; original code would loop forever for a zero-capacity vehicle.
6. RK's per-SKU synthetic COGS is fixed at the official brand average 62.5%, and Soorya at 40%: no real SKU cost differentiation. Costs and margins are not empirical product economics.
7. Soorya rebate agreements are represented by a single type per outlet (correct arithmetic), but there are no actual signed agreements or verified performance tiers.
8. Listing fees are represented as one upfront amount plus monthly charges, without effective dates; monthly periods are assumed.
9. SmartShelf score normalization across all brands can bias within-brand recommendations; no demand-transfer or cannibalization model.
10. Charts are bound to filtered data in code, but reactive refresh was not independently browser-tested.

## Corrections implemented
- Added `validation.py`: reproducible integrity audit and genuine recursive 60-day holdout evaluation without holdout actual values in the recursive feature history.
- Added `tests/test_validation.py` for integrity, orphan detection, rebate reconciliation, leakage evaluation, supply limits, and zero-capacity vehicle rejection.
- Patched route planner to reject nonpositive vehicle capacities and negative per-km cost instead of hanging.
- Exported `model_validation_results.csv` with per-series model/baseline metrics.
- Preserved original financial outcomes; no performance or margin numbers were tuned to look better.

## Remaining limitations
- Critical business logic issues above are **not yet corrected**. This is an audited development build, not a validated competition-ready financial optimizer.
- Synthetic latent demand, stockouts, returns, expiry and lots are not derived from a single balanced inventory-flow simulation.
- Financial outcomes are not real company savings. Brand-level official rates are historical contextual benchmarks, not per-account contract rates.
- Forecast uncertainty is a 90th percentile absolute validation residual heuristic, not a calibrated 90% predictive interval.
- Route savings are cost differences from synthetic Euclidean coordinates and assumed AED/km, not observed logistics savings.
- The official company context has conflicting RK/Soorya revenue mix percentages (67/33 graphic vs 73/27 prose); neither is adopted as definitive.

## Actual model performance on synthetic holdout data
Evaluated 27 SKUs × two outlets (O01, O08), 60 holdout days each; 54 separate recursive forecasts. Metrics are **unweighted means of per-series metrics**, not pooled portfolio WAPE. Bias = mean(prediction - actual).

| Group | ML MAE | ML WAPE | ML bias | Naive MAE | Naive WAPE |
|---|---:|---:|---:|---:|---:|
| Overall | 1.987 | 43.09% | +0.127 | 2.614 | 57.36% |
| RK | 1.880 | 44.63% | +0.096 | 2.495 | 59.72% |
| Soorya | 2.242 | 39.43% | +0.199 | 2.897 | 51.77% |
| Pulses | 1.713 | 46.8% | +0.033 | 2.244 | 61.2% |
| Rice | 1.765 | 45.1% | +0.113 | 2.158 | 56.4% |
| Spice powders | 1.933 | 40.7% | +0.196 | 2.592 | 54.7% |
| Beans & peas | 2.005 | 51.2% | +0.269 | 2.658 | 68.2% |
| Whole spices | 2.177 | 46.7% | +0.729 | 2.625 | 58.0% |
| Fresh & frozen | 2.242 | 39.4% | +0.199 | 2.897 | 51.8% |

**Reproduce:** `python -m pytest -q tests`; rerun the backtest with `validation.recursive_backtest` on the included CSVs. No future actuals enter recursive model features. The baseline uses actual values from seven days earlier for scoring; for a deployment-style multi-day baseline beyond seven days, this would also need recursive seasonal-naive generation, so the current baseline is optimistic relative to a strictly deployment-like baseline.
