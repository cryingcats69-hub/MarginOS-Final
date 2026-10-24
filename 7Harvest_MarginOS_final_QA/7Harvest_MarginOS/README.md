# 7Harvest MarginOS

Offline-first, synthetic-data consulting proof of concept for the 7Harvest FMCG Consulting Challenge 2026.

## Launch

From this directory:

```bash
python -m pip install -r requirements.txt
python data/generate_demo_data.py
streamlit run app.py
```

Open the local URL printed by Streamlit. Python 3.10+ recommended. Installation requires access to packages once; thereafter the app requires no internet, API keys or accounts. Run tests with `python -m pytest tests -q`.

## Seven pages

1. Executive Overview: synthetic account contribution and high-level decisions.
2. FreshFlow Demand & Expiry: historical chronological holdout, seasonal-naive benchmark, gradient-boosted model, recursive 7/14-day forecast, FEFO stock, case-size replenishment and scenario transfer.
3. RouteSync Delivery Planner: synthetic depot coordinates, temperature-compatible capacitated tours, feasible baseline, comparative costs and export.
4. TradeSmart Retail Profitability: exact customer-by-item-Type rebates for RK and single customer-wide discount for Soorya; negotiation sensitivity and contribution waterfall.
5. SmartShelf Portfolio Optimiser: transparent weighted SKU scoring, category filtering, local heatmap, recommendations and CSV.
6. Scenario Comparison & Impact: separate impact windows, no double counting.
7. Data, Assumptions & Model Quality: source assumptions, reference costs, CSV data download and limitations.

## Source of truth

Official competition brief and Seven Harvest Business Context are authoritative for brand definitions, expense rates, item-type rebate mechanics and competition requirements. `7 HARVEST` brainstorming is not authoritative. All transaction rows, locations, unit prices, rebate agreements, fees, inventory lots, and delivery costs are generated synthetic examples, NOT company records. Company revenue mix is inconsistent: 67/33 graphic vs 73/27 prose. No definitive ratio is used.

Published cost benchmarks as fraction of brand sales:
- RK: COGS .625, vehicle .0175, rent .015, pallet .0125, gondola .0088, price-offs .0225, promoters .015, rebate .0288. Published total .7450.
- Soorya: COGS .40, vehicle .05, rent .0167, support .0267, promoters .0047, rebate .03, damage/expiry .02. Published total .5480.
- Totals differ from component sums by 0.01 percentage points due to rounding. Rates are contextual brand averages, not customer contracts; overheads excluded.

## Auditable calculations

- RK rebate = sum over each customer and item Type of gross sales × that customer's Type rate. Soorya = customer total × that customer's single discount rate.
- Contribution = synthetic gross sales − synthetic SKU unit COGS × units − contract-specific synthetic rebates − explicitly applied synthetic account trade fees. No unprovided overhead. Other historical brand-level percentages are contextual and are **not** stacked on top of synthetic expense rows.
- Forecast uses lag 1/7/14 and shifted 7-day rolling mean, weekday and month. Training/validation/test split chronological 65/17/18%; historical test is one-step prediction using observed past lagged sales; future forecast recursive. WAPE = sum absolute errors / sum actual sales (undefined if denominator zero), bias = mean(predicted − actual). Heuristic interval = prediction ± validation absolute-error 90th percentile, not a calibrated probability.
- Replenishment target = demand forecast within usable shelf-life window after lead time × (1+safety), minus FEFO saleable inventory. Round up to full cases; cap by available supply. Projected unsold is a simple deterministic planning approximation, not lot-level forward simulation.
- Route distances are Euclidean distances between *synthetic* points; monetary cost = proxy kilometres × assumed cost per km. Capacity and temperature are enforced. Time windows, maximum operating hours, real traffic, fleet availability and actual company vehicle cost are NOT enforced.
- SmartShelf weighted score normalises SKU units, gross margin proxy and outlet coverage; essential-category low scorers are protected. Do not treat scores as market share, verified net profitability, or proof of substitution.

## Known gaps (important)

This is a functional demonstration, not a production-ready deployment. No custom CSV upload/validation UI, full FEFO forward lot depletion, calibrated stockout probabilities, causal promotion analysis, rigorous constrained time-window routing, explicit transfer-demand delisting simulator, or causal listing-fee/payback model. Forecast training is per selected SKU/outlet and cached; evaluation uses one chronological holdout rather than rolling-origin cross-validation. Cross-module results cannot be safely summed due to differing time windows. No claims of validated savings. Consult the official brief before presenting as company evidence.

## Data replacement

See `data_dictionary.md`. Replace CSVs only with company-authorised data, preserve schemas and foreign keys, remove synthetic-only latent-demand columns, and adapt all assumptions and models before treating outputs as company decision support. Do not distribute confidential agreements.

## Verification

`python -m pytest tests -q` verifies 9 automated checks. App startup depends on local Streamlit installation. Run `streamlit run app.py --server.headless true` for a local smoke test. A demo script is in `demo_script.md`.


## Presentation Mode
Open **Presentation Mode** in the sidebar to walk through Soorya replenishment, retailer rebate negotiation, and RK assortment. Each tab includes interactive scenario controls and speaker notes. See `DESIGN_CHANGELOG.md` for regression status and known limitations.
