# MarginOS dashboard refresh — validation and scope

## Changes
- Executive styling: navy #243B53, off-white backgrounds, restrained teal, consistent Plotly defaults, metric cards and typography.
- Added Presentation Mode with three scenario tabs and speaker cues. All scenario values are calculated from existing data/functions and current widget inputs.
- Fixed stale SKU widget state when switching brand.
- Added chart titles/units for the forecast, route and trade waterfall views.
- Preserved the synthetic-data notice, calculation modules, model evaluation and existing exports.

## Validation
- `python -m compileall -q app.py` — passed.
- `python -m pytest -q` — 21 passed.
- Streamlit is not installed in the build environment; interactive browser checks and launch verification could not be performed. Run `streamlit run app.py` after installing requirements, and click through the 3 presentation tabs.

## Outstanding known model limitations
- Expiry lots are not fully simulated batch-by-batch through future expiry.
- TradeSmart baseline omits some outlet expenses; do not present it as fully loaded contribution.
- RouteSync does not enforce time windows and uses synthetic distance proxies.
- SmartShelf gross contribution excludes rebate and shared trade costs; assortment transfer is an adjustable assumption, not a measured causal estimate.
- Scenario deltas with different time horizons must not be added together.
- Presentation Mode's 35% buffer is an explicit *hypothetical baseline assumption*, not observed company policy.
