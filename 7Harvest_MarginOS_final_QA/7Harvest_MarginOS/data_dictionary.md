# Synthetic data dictionary

All files under `data/` are generated with seed 2026 by `generate_demo_data.py`. None are actual 7Harvest records.

| File | Key | Fields |
|---|---|---|
| skus.csv | sku | brand, category, name, type, unit_price, unit_cogs, case_size, shelf_life_days, temperature, regulated_category |
| outlets.csv | outlet | name, locality, x_km_proxy, y_km_proxy, demand_factor, window_start, window_end |
| agreements.csv | outlet + brand + type | rebate_rate (fraction) |
| trade_fees.csv | outlet | listing_fee_upfront_aed, monthly_promoter_aed, monthly_display_aed, monthly_support_aed |
| sales.csv | date + outlet + sku | units_sold, gross_sales_aed, returns_units, expired_units, promotion_known, latent_demand_SYNTHETIC_ONLY, lost_units_SYNTHETIC_ONLY |
| inventory_lots.csv | lot | outlet, sku, received_date, expiry_date, remaining_units |
| vehicles.csv | vehicle | capacity_units, cost_per_km_aed, max_hours, temperature |

`latent_demand_SYNTHETIC_ONLY` and `lost_units_SYNTHETIC_ONLY` are synthetic generator diagnostics, not observations and NOT ML features. `x_km_proxy` and `y_km_proxy` are not GPS coordinates. Synthetic dates/events are illustrative, not a verified holiday calendar.

## Replacing data

1. Obtain explicit permission to use operational data; remove or anonymise personally identifying and confidential contract information.
2. Prepare all seven tables with the same columns and matching keys; keep sales dates in ISO format.
3. Confirm the rebate Type mapping with 7Harvest, and verify which fees apply to which outlets and periods.
4. Remove the synthetic-only latent demand fields and revise any cost proxies with actual recorded costs.
5. Run `python -m pytest tests -q`, then inspect model quality and financial reconciliation before any business decisions.
6. Do not rerun the generator after replacing data; it overwrites the demo CSVs.
