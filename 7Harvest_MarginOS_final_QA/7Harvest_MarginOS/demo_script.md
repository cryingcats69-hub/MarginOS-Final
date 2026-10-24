# 90-second live demo

**Before starting:** Install requirements, generate data, launch Streamlit and open Executive Overview. No internet is needed after installation. Keep the sample outlet and SKU selected in the sidebar.

**0:00–0:15 — Context.** “7Harvest faces margin pressure from costs and shelf-presence fees. MarginOS demonstrates three integrated decisions. All transactions are clearly synthetic; company-provided cost and rebate rules are preserved.”

**0:15–0:40 — FreshFlow.** Open FreshFlow. Point out ML vs seasonal-naive holdout MAE and forecast band. Show FEFO saleable stock and case-size delivery recommendation. Click **Send delivery to RouteSync**.

**0:40–0:55 — RouteSync.** Open RouteSync. Show the transferred delivery, feasible capacity loads, route map and baseline comparison. Explain distances are synthetic proxies and time windows are not yet enforced.

**0:55–1:10 — TradeSmart.** Select account and change rebate-rate slider. Show the live waterfall and contribution delta. State the customer-by-item-Type rebate calculation is from the official context; actual rates are synthetic.

**1:10–1:25 — SmartShelf.** Open SmartShelf. Filter RK category; show SKU margin-versus-velocity and recommendation scores. Explain no SKU is automatically delisted.

**1:25–1:30 — Close.** “The next step is a pilot using actual authorised sales, inventory, contracts and route data. These outputs demonstrate methodology, not verified savings.”

## Fallback

If model training is slow, demonstrate TradeSmart and SmartShelf first; forecasting is cached after its first successful run. If the app is not installed on the presentation machine, use a local laptop with preinstalled dependencies.
