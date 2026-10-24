import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from core import COSTS,validate,rebates,contribution,evaluate_forecast,fefo_stock,replenish,route_plan,sku_scores
from data.generate_demo_data import generate
st.set_page_config(page_title='7Harvest MarginOS',layout='wide',page_icon='📊',initial_sidebar_state='expanded')
st.markdown("""<style>
:root {--navy:#243B53;--teal:#087E8B;--line:#DDE5EC}
.stApp {background:#F7F9FC;color:#243B53}
section[data-testid="stSidebar"] {background:#EDF2F7;border-right:1px solid #D9E2EC}
h1,h2,h3 {color:#243B53;letter-spacing:-.025em}
h1 {font-size:2.05rem!important} h2 {font-size:1.42rem!important}
div[data-testid="stMetric"] {background:#FFFFFF;border:1px solid #DFE7EF;border-radius:12px;padding:16px;box-shadow:0 2px 9px rgba(36,59,83,.035)}
div[data-testid="stMetricLabel"] {color:#526779} div[data-testid="stMetricValue"] {color:#243B53;font-size:1.65rem}
div.stButton>button[kind="primary"] {background:#243B53;border-color:#243B53;color:white}
div.stButton>button {border-radius:8px}
[data-testid="stAlert"] {border-radius:9px}
[data-testid="stPlotlyChart"] {background:white;border:1px solid #E1E8EF;border-radius:12px;padding:8px}
[data-testid="stDataFrame"] {border-radius:10px;overflow:hidden}
.block-container {padding-top:1.3rem;max-width:1450px}
.dashboard-kicker {font-size:.77rem;font-weight:700;letter-spacing:.11em;color:#087E8B;text-transform:uppercase}
.demo-note {background:white;border-left:4px solid #087E8B;border-radius:6px;padding:12px 16px;color:#334E68;margin:10px 0 18px}
</style>""",unsafe_allow_html=True)
PLOT_TEMPLATE=dict(layout=dict(font=dict(family='Arial',color='#243B53',size=12),paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',colorway=['#087E8B','#356A98','#C28C45','#66788A'],margin=dict(l=28,r=20,t=55,b=45),hovermode='x unified',legend=dict(orientation='h',y=-.22),xaxis=dict(showgrid=False,zeroline=False),yaxis=dict(gridcolor='#E8EDF2',zeroline=False)))
_original_plotly_chart=st.plotly_chart
def professional_chart(fig,*args,**kwargs):
    if hasattr(fig,'update_layout'):
        fig.update_layout(**PLOT_TEMPLATE['layout'])
    return _original_plotly_chart(fig,*args,**kwargs)
st.plotly_chart=professional_chart

def section_intro(kicker,title,description):
    st.markdown(f'<div class="dashboard-kicker">{kicker}</div>',unsafe_allow_html=True)
    st.header(title)
    st.caption(description)

def scenario_comparison(label,baseline,proposed,unit='AED',scope='Illustrative scenario'):
    a,b,c=st.columns(3)
    fmt=lambda v: f'{unit} {v:,.0f}' if unit=='AED' else f'{v:,.1f} {unit}'
    a.metric('Baseline',fmt(baseline))
    b.metric('Proposed',fmt(proposed))
    c.metric('Difference',fmt(proposed-baseline))
    st.caption(f'{label} · {scope} · Calculated from synthetic data; not realised savings.')
@st.cache_data(show_spinner='Loading reproducible synthetic dataset...')
def load():
    path=Path(__file__).parent/'data';names=['skus','outlets','agreements','trade_fees','sales','inventory_lots','vehicles']
    if not all((path/(n+'.csv')).exists() for n in names):return generate(path)
    return {n:pd.read_csv(path/(n+'.csv')) for n in names}
@st.cache_data(show_spinner='Training and evaluating model...')
def forecast_cached(sales,sku,outlet,horizon):return evaluate_forecast(sales,sku,outlet,horizon)
def download(df,name):st.download_button('Download '+name,df.to_csv(index=False).encode(),file_name=name+'.csv',mime='text/csv')
d=load();validate(d);skus=d['skus'];sales=d['sales'];outlets=d['outlets'];terms=d['agreements'];fees=d['trade_fees']
st.markdown('<div class="dashboard-kicker">7HARVEST · DECISION INTELLIGENCE</div>',unsafe_allow_html=True)
st.title('MarginOS | Margin beyond price')
st.warning('SYNTHETIC DEMO / NOT ACTUAL 7HARVEST DATA — operational records, agreements, coordinates and scenario savings are illustrative.')
page=st.sidebar.radio('Navigation',['Executive Overview','FreshFlow Demand & Expiry','RouteSync Delivery Planner','TradeSmart Retail Profitability','SmartShelf Portfolio Optimiser','Scenario Comparison & Impact','Data, Assumptions & Model Quality','Presentation Mode'])
brand=st.sidebar.selectbox('Brand',['Soorya','RK'],key='brand');outlet=st.sidebar.selectbox('Retail outlet',outlets.outlet.tolist(),key='outlet');horizon=st.sidebar.selectbox('Forecast horizon (days)',[7,14],key='horizon')
if st.sidebar.button('Reset scenarios'):
    for k in ['plan','trade_delta','shelf_delta','route_delta','presentation_trade_rate','presentation_expiry_adjust','presentation_assortment_transfer','presentation_supply','presentation_days','presentation_category','presentation_trade_outlet','presentation_shelf_outlet','presentation_soorya_sku','presentation_soorya_outlet']:st.session_state.pop(k,None)
    st.rerun()
subset=skus[skus.brand==brand]
if st.session_state.get('sku') not in subset.sku.values: st.session_state['sku']=subset.sku.iloc[0]
sku=st.sidebar.selectbox('SKU',subset.sku.tolist(),format_func=lambda x:skus.set_index('sku').loc[x,'name'],key='sku')
if page=='Executive Overview':
    section_intro('Executive intelligence','Protect margin beyond price','A single view of commercial performance and the three decision levers. All values are synthetic.')
    c=contribution(sales,skus,terms,fees,months=18);a,b,c3=st.columns(3);a.metric('Synthetic gross sales',f"AED {sales.gross_sales_aed.sum():,.0f}");b.metric('Synthetic contribution after modelled trade fees, before overhead',f"AED {c.contribution_aed.sum():,.0f}");c3.metric('Synthetic outlets',len(outlets))
    st.plotly_chart(px.bar(c,x='outlet',y='contribution_aed',title='Illustrative contribution by account'),use_container_width=True)
    st.caption('Contribution includes synthetic COGS, rebates, listing fees and 18 months of recurring trade fees; excludes vehicle expense, expiry losses and overhead.')
    st.info('Use FreshFlow to produce a delivery recommendation, RouteSync to route it, TradeSmart to test negotiated terms and SmartShelf to review assortment. Each page uses the same synthetic dataset.')
elif page=='FreshFlow Demand & Expiry':
    section_intro('01 · Demand & inventory','FreshFlow | Forecast and replenish','Forecast observed sell-through, inspect uncertainty and test case-constrained replenishment.')
    try:
        future,m,test=forecast_cached(sales,sku,outlet,horizon)
        cols=st.columns(4)
        for col,(k,v) in zip(cols,[(k,m[k]) for k in ['ML MAE','Naive MAE','ML WAPE','Bias units']]):col.metric(k,f'{v:.2f}' if 'WAPE' not in k else f'{v:.1%}')
        st.caption(f"Chronological train through {m['train_end']}; validation through {m['validation_end']}; untouched test {m['test_start']} to {m['test_end']}. Test evaluation is one-step using past observed lags; future forecast is recursive. Intervals are heuristic validation-error bounds.")
        fig=go.Figure();fig.add_trace(go.Scatter(x=test.date,y=test.units_sold,name='Observed test sales'));fig.add_trace(go.Scatter(x=test.date,y=test.ML,name='ML test estimate'));fig.add_trace(go.Scatter(x=test.date,y=test.seasonal_naive,name='Seasonal naive'));fig.update_layout(title='Holdout: observed sales vs model estimates',xaxis_title='Date',yaxis_title='Units sold / predicted')
        st.plotly_chart(fig,use_container_width=True)
        fig2=go.Figure();fig2.add_trace(go.Scatter(x=future.date,y=future.high_heuristic,line=dict(width=0),showlegend=False));fig2.add_trace(go.Scatter(x=future.date,y=future.low_heuristic,fill='tonexty',name='Heuristic range',line=dict(width=0)));fig2.add_trace(go.Scatter(x=future.date,y=future.predicted_units,name='Forecast'));fig2.update_layout(title='Recursive future forecast with heuristic range',xaxis_title='Forecast date',yaxis_title='Units (not a calibrated probability)')
        st.plotly_chart(fig2,use_container_width=True)
        stock=fefo_stock(d['inventory_lots'][(d['inventory_lots'].sku==sku)&(d['inventory_lots'].outlet==outlet)],pd.to_datetime(sales.date.max()))
        item=skus.set_index('sku').loc[sku];available=st.number_input('Available supply (units)',0,20000,2000);safety=st.slider('Safety stock',0.,.5,.15,.05);lead=st.slider('Lead time (days)',0,5,1)
        rec=replenish(future.predicted_units,stock,int(item.case_size),int(item.shelf_life_days),available,lead,safety)
        chosen=st.number_input('Delivery units (editable; multiples of case size recommended)',0,20000,int(rec['deliver_units']),step=int(item.case_size))
        st.write(f"Saleable FEFO stock: **{stock} units** · Recommended: **{rec['deliver_units']} units** · Projected unsold within horizon: **{rec['expected_unsold_units']:.1f} units**")
        if chosen>available:st.error('Plan infeasible: exceeds available supply')
        elif chosen%int(item.case_size):st.error('Plan infeasible: quantity not a case multiple')
        else:
            if st.button('Send delivery to RouteSync'):st.session_state.plan={'outlet':outlet,'sku':sku,'units':chosen,'temperature':item.temperature};st.success('Delivery plan saved to RouteSync')
        download(future,'freshflow_forecast')
    except Exception as e:st.error(f'Model unavailable: {e}. Review data quality and history.')
elif page=='RouteSync Delivery Planner':
    section_intro('02 · Logistics','RouteSync | Capacity-compatible delivery','Compare feasible capacity and temperature-compatible route plans using synthetic distances.')
    plan=st.session_state.get('plan')
    if plan:st.info(f"FreshFlow plan: {plan['units']} units of {plan['sku']} to {plan['outlet']}")
    else:st.info('Using a labelled illustrative default plan until a FreshFlow delivery is sent.')
    temp=plan['temperature'] if plan else 'Chilled';qty=plan['units'] if plan else 60
    deliveries=[(o,int(qty*(.6+.08*i)),temp) for i,o in enumerate(outlets.outlet[:8])]
    if plan:deliveries=[(o,q,t) for o,q,t in deliveries if o!=plan['outlet']]+[(plan['outlet'],plan['units'],plan['temperature'])]
    multiplier=st.slider('Delivery volume multiplier',.5,2.,1.,.1);deliveries=[(o,int(q*multiplier),t) for o,q,t in deliveries]
    try:
        opt,unmet=route_plan(outlets,deliveries,d['vehicles']);base,_=route_plan(outlets,deliveries,d['vehicles'],'baseline')
        x=sum(r['distance_proxy_km'] for r in opt);y=sum(r['distance_proxy_km'] for r in base)
        a,b,c=st.columns(3);a.metric('Optimised distance proxy',f'{x:.1f} km');b.metric('Baseline distance proxy',f'{y:.1f} km');c.metric('Cost difference (synthetic)',f"AED {sum(r['cost_aed'] for r in base)-sum(r['cost_aed'] for r in opt):.1f}")
        st.caption('Synthetic Euclidean-coordinate proxy, not UAE road kilometres. Capacity and temperature are enforced; driver schedules and time windows are not enforced in this demonstration.')
        fig=go.Figure()
        for i,r in enumerate(opt):
            pts=[(0.,0.)]+[(float(outlets.set_index('outlet').loc[o,'x_km_proxy']),float(outlets.set_index('outlet').loc[o,'y_km_proxy'])) for o,q in r['stops']]+[(0.,0.)]
            fig.add_trace(go.Scatter(x=[p[0] for p in pts],y=[p[1] for p in pts],mode='lines+markers',name=f'Route {i+1}'))
        fig.update_layout(xaxis_title='Synthetic X coordinate',yaxis_title='Synthetic Y coordinate');fig.update_layout(title='Synthetic delivery route geometry',xaxis_title='Synthetic X (km proxy)',yaxis_title='Synthetic Y (km proxy)')
        st.plotly_chart(fig,use_container_width=True)
        route_df=pd.DataFrame([{'route':i+1,'vehicle':r['vehicle'],'stops':', '.join(f'{o}:{q}' for o,q in r['stops']),'load':r['load'],'capacity':r['capacity'],'distance_proxy_km':r['distance_proxy_km'],'cost_aed':r['cost_aed']} for i,r in enumerate(opt)]);st.dataframe(route_df,use_container_width=True);download(route_df,'routesync_routes')
        if unmet:st.error(f'Unmet deliveries: {unmet}')
        st.session_state.route_delta=(sum(r['cost_aed'] for r in base)-sum(r['cost_aed'] for r in opt)) if not unmet else None
    except Exception as e:st.error(str(e))
elif page=='TradeSmart Retail Profitability':
    section_intro('03 · Trade economics','TradeSmart | Retail profitability','Simulate account-level commercial terms using the agreed item-type rebate calculation.')
    lines=sales[(sales.outlet==outlet)&(sales.sku.isin(subset.sku))].copy();agreement=terms[(terms.outlet==outlet)&(terms.brand==brand)].copy()
    st.dataframe(agreement,use_container_width=True);base_rebate=rebates(lines,skus,terms).rebate_aed.sum();gross=lines.gross_sales_aed.sum();cogs=(lines.merge(skus[['sku','unit_cogs']],on='sku').eval('units_sold * unit_cogs')).sum()
    discount=st.slider('Change each agreed rebate rate (percentage points)',-3.,3.,0.,.25);sales_change=st.slider('Gross sales scenario change (%)',-30,30,0);support=st.number_input('Additional support spend (AED, over dataset period)',0.,100000.,0.,100.);fee=st.number_input('Additional listing fee (AED)',0.,100000.,0.,100.)
    modified=agreement.copy();modified['rebate_rate']=(modified.rebate_rate+discount/100).clip(0,1);terms2=terms.copy();terms2.loc[modified.index,'rebate_rate']=modified.rebate_rate
    scenario=lines.copy();scenario['gross_sales_aed']*=1+sales_change/100;scenario['units_sold']*=1+sales_change/100
    rb=rebates(scenario,skus,terms2).rebate_aed.sum();newgross=scenario.gross_sales_aed.sum();newcogs=cogs*(1+sales_change/100)
    baseline=gross-cogs-base_rebate;new=newgross-newcogs-rb-support-fee;st.session_state.trade_delta=new-baseline
    a,b,c=st.columns(3);a.metric('Baseline contribution (excl. other costs)',f'AED {baseline:,.0f}');b.metric('Scenario contribution',f'AED {new:,.0f}');c.metric('Difference',f'AED {new-baseline:,.0f}')
    waterfall=go.Figure(go.Waterfall(x=['Gross sales','COGS','Rebates','Added trade fees','Contribution'],measure=['absolute','relative','relative','relative','total'],y=[newgross,-newcogs,-rb,-support-fee,0]));waterfall.update_layout(title='Scenario contribution bridge',yaxis_title='AED',xaxis_title='Contribution components')
    st.plotly_chart(waterfall,use_container_width=True)
    st.caption('Contribution shown excludes unprovided overhead and costs not explicitly modelled here. Listing-fee break-even requires incremental contribution, not gross sales. Changes in demand are hypothetical, not causal estimates.')
    ranking=contribution(sales,skus,terms,fees,months=18);st.dataframe(ranking.sort_values('contribution_aed'),use_container_width=True);download(ranking,'tradesmart_account_contribution')
    st.subheader('Illustrative performance-linked rebate')
    st.caption('Hypothetical tiers ONLY; the official documents do not establish tiered agreements.')
    st.line_chart(pd.DataFrame({'sales':[gross*.7,gross,gross*1.3],'flat_rebate':[gross*.7*.03,gross*.03,gross*1.3*.03],'illustrative_tier':[gross*.7*.02,gross*.03,gross*1.3*.04]}).set_index('sales'))
elif page=='SmartShelf Portfolio Optimiser':
    section_intro('04 · Assortment','SmartShelf | Portfolio intelligence','Review sales, contribution proxies and local distribution before recommending assortment changes.')
    w1=st.slider('Velocity weight',0,100,40);w2=st.slider('Contribution weight',0,100,35);w3=st.slider('Outlet coverage weight',0,100,25)
    if w1+w2+w3==0:st.error('Choose at least one positive weight');st.stop()
    s=sku_scores(sales,skus,(w1,w2,w3));s=s[s.brand==brand];cat=st.selectbox('Category',['All']+sorted(s.category.unique().tolist()));s=s if cat=='All' else s[s.category==cat]
    st.plotly_chart(px.scatter(s,x='units',y='contribution_proxy',color='action',hover_name='name',size='sales',title='Margin proxy vs sales velocity'),use_container_width=True)
    st.plotly_chart(px.bar(s.sort_values('sales',ascending=False),x='name',y='sales',title='SKU sales comparison'),use_container_width=True)
    hm=sales[sales.sku.isin(s.sku)].groupby(['outlet','sku'],as_index=False).units_sold.sum().pivot(index='outlet',columns='sku',values='units_sold').fillna(0)
    st.plotly_chart(px.imshow(hm,aspect='auto',title='Outlet × SKU units heatmap'),use_container_width=True)
    st.dataframe(s[['sku','name','category','units','sales','contribution_proxy','outlets','score','action','confidence']],use_container_width=True);download(s,'smartshelf_sku_scores')
    st.caption('Scores are relative to synthetic SKU distributions. No automated delisting. Contribution proxy excludes rebates and shared trade costs; validate substitute demand and account requirements before action.')
elif page=='Scenario Comparison & Impact':
    section_intro('05 · Decision comparison','Scenario comparison & impact','Compare like-for-like outcomes. Incompatible periods are deliberately not added together.')
    rows=[['TradeSmart',st.session_state.get('trade_delta'), 'AED over 548 days; hypothetical'],['RouteSync',st.session_state.get('route_delta'),'AED per illustrative routing run']]
    st.dataframe(pd.DataFrame(rows,columns=['Module','Scenario difference','Unit and time window']),use_container_width=True)
    st.info('Differences are intentionally NOT added: periods and scopes differ, and savings could overlap. FreshFlow and SmartShelf are decision-support scenarios without verified monetary attribution.')
    download(pd.DataFrame(rows,columns=['module','difference_aed','scope']),'scenario_comparison')
elif page=='Data, Assumptions & Model Quality':
    section_intro('Governance','Data, assumptions & model quality','Company context, synthetic inputs, model status and transparent limitations.')
    st.write('**Source facts:** official competition brief and Seven Harvest Business Context. **All operational records:** generated synthetic demo data, seed 2026.')
    st.write('Official listed-expense percentages (share of sales; before overhead):');st.dataframe(pd.DataFrame(COSTS).fillna('—'))
    st.warning('Official context inconsistency: revenue mix chart says RK/Soorya ≈67/33, prose says ≈73/27. No definitive split used. Listed cost sums differ from published totals by 0.01 percentage points due to rounding.')
    st.write('Synthetic event calendar: illustrative uplift for first 12 days of March, April and November; these dates are NOT validated holiday dates. Synthetic latent demand is kept solely for simulation and never used as a model feature.')
    st.write('Model: chronological train/validation/test, gradient boosting versus seasonal naive; one-step historical test with observed lagged sales, recursive future forecasts, heuristic error bounds. Route solver: capacity/temperature-compatible nearest-neighbour, not time-window-feasible VRP.')
    for name,frame in d.items():
        with st.expander(f'{name} ({len(frame):,} rows)'):
            st.dataframe(frame.head(20));download(frame,name+'_synthetic')


if page=='Presentation Mode':
    section_intro('Live demonstration · 90 seconds','Presentation Mode','Three interactive decisions, each with a baseline, a proposed scenario and a concise speaker cue.')
    st.info('SYNTHETIC DEMO / NOT ACTUAL 7HARVEST DATA. Scenario benefits are hypothetical and must not be represented as company savings.')
    tab1,tab2,tab3=st.tabs(['01 · Soorya expiry','02 · Retail trade terms','03 · RK assortment'])
    with tab1:
        st.subheader('FreshFlow | Replenish to expected demand')
        soorya=skus[skus.brand=='Soorya']
        psku=st.selectbox('Soorya product',soorya.sku.tolist(),format_func=lambda x:skus.set_index('sku').loc[x,'name'],key='presentation_soorya_sku')
        p_outlet=st.selectbox('Delivery outlet',outlets.outlet.tolist(),key='presentation_soorya_outlet')
        ph=st.select_slider('Forecast days',[7,14],value=7,key='presentation_days')
        try:
            pred,metrics,_=forecast_cached(sales,psku,p_outlet,ph)
            item=soorya.set_index('sku').loc[psku]
            lots=d['inventory_lots'][(d['inventory_lots'].sku==psku)&(d['inventory_lots'].outlet==p_outlet)]
            onhand=fefo_stock(lots,pd.to_datetime(sales.date.max()))
            supply=st.number_input('Available new supply (units)',0,20000,500,key='presentation_supply')
            safety=st.slider('Safety allowance',0.,.5,.15,.05,key='presentation_expiry_adjust')
            recommendation=replenish(pred.predicted_units,onhand,int(item.case_size),int(item.shelf_life_days),supply,1,safety)
            base_units=int(min(supply,(int(np.ceil((pred.predicted_units.sum()*1.35)/item.case_size))*item.case_size)))
            proposed=int(recommendation['deliver_units'])
            scenario_comparison('Delivery quantities',base_units,proposed,unit='units',scope=f'{ph}-day demand scenario; baseline is a 35% demand buffer, capped by supply')
            st.plotly_chart(px.line(pred,x='date',y='predicted_units',title='Projected daily observed sales demand',labels={'date':'Forecast date','predicted_units':'Units per day'}),use_container_width=True)
            st.markdown('<div class="demo-note"><b>Speaker cue:</b> “Instead of sending a fixed buffer, we forecast demand and cap the proposed delivery by case size and available supply. These are simulated quantities, not verified reductions in expiry.”</div>',unsafe_allow_html=True)
            if st.button('Use this delivery in RouteSync',type='primary'):
                st.session_state.plan={'outlet':p_outlet,'sku':psku,'units':proposed,'temperature':item.temperature}
                st.success('Delivery saved. Open RouteSync in the navigation to compare route plans.')
        except Exception as exc: st.error(f'Forecast not available: {exc}')
    with tab2:
        st.subheader('TradeSmart | Renegotiate an illustrative account')
        po=st.selectbox('Retail account',outlets.outlet.tolist(),key='presentation_trade_outlet')
        lines=sales[sales.outlet==po].copy()
        rk_lines=lines[lines.sku.isin(skus[skus.brand=='RK'].sku)]
        base=rebates(rk_lines,skus,terms).rebate_aed.sum()
        shift=st.slider('Change rebate rates (percentage points)',-3.,3.,-1.,.25,key='presentation_trade_rate')
        changed=terms.copy()
        mask=(changed.outlet==po)&(changed.brand=='RK')
        changed.loc[mask,'rebate_rate']=(changed.loc[mask,'rebate_rate']+shift/100).clip(0,1)
        new=rebates(rk_lines,skus,changed).rebate_aed.sum()
        scenario_comparison('RK rebate expense',base,new,scope='Entire synthetic observation period; lower is favourable, subject to negotiation')
        chart=go.Figure(go.Bar(x=['Current agreement','Hypothetical agreement'],y=[base,new],text=[f'AED {base:,.0f}',f'AED {new:,.0f}'],textposition='auto'))
        chart.update_layout(title='Customer-specific rebate expenditure',yaxis_title='Rebates (AED)',xaxis_title='Agreement scenario')
        st.plotly_chart(chart,use_container_width=True)
        st.markdown('<div class="demo-note"><b>Speaker cue:</b> “Our engine applies the actual rule structure—customer by item type—but the agreement rates are synthetic. The difference shows negotiation exposure, not a guaranteed saving.”</div>',unsafe_allow_html=True)
    with tab3:
        st.subheader('SmartShelf | Review the local RK range')
        po=st.selectbox('Retail account',outlets.outlet.tolist(),key='presentation_shelf_outlet')
        rk=skus[skus.brand=='RK']
        categories=sorted(rk.category.unique())
        category=st.selectbox('Product category',categories,key='presentation_category')
        transfer=st.slider('Hypothetical sales transfer to retained products (%)',0,100,50,5,key='presentation_assortment_transfer')
        selected=rk[rk.category==category]
        local=sales[(sales.outlet==po)&(sales.sku.isin(selected.sku))].groupby('sku',as_index=False).agg(units=('units_sold','sum'),gross=('gross_sales_aed','sum'))
        local=selected[['sku','name','unit_cogs','wholesale_price']].merge(local,on='sku',how='left').fillna({'units':0,'gross':0})
        local['gross_contribution_before_trade']=local.gross-local.units*local.unit_cogs
        if len(local)<2: st.warning('At least two products are needed to illustrate assortment consolidation.')
        else:
            local=local.sort_values('gross_contribution_before_trade')
            candidate=local.iloc[0]
            lost=float(candidate.gross_contribution_before_trade)
            survivors=local.iloc[1:]
            avg_margin=float(survivors.gross_contribution_before_trade.sum()/survivors.gross.sum()) if survivors.gross.sum()>0 else 0
            retained=float(candidate.gross*transfer/100*avg_margin)
            scenario_comparison('Gross contribution before trade',float(local.gross_contribution_before_trade.sum()),float(local.gross_contribution_before_trade.sum()-lost+retained),scope='Full synthetic observation period; excludes rebates, cannibalisation uncertainty and delisting costs')
            st.plotly_chart(px.bar(local,x='name',y='gross_contribution_before_trade',title='Local SKU contribution before trade expense',labels={'name':'SKU','gross_contribution_before_trade':'Gross contribution (AED)'}),use_container_width=True)
            st.markdown(f'<div class="demo-note"><b>Speaker cue:</b> “We flag <b>{candidate["name"]}</b> for review, not automatic delisting. The result changes with the assumed demand transfer. Retailer obligations and substitution must be validated before acting.”</div>',unsafe_allow_html=True)
            st.dataframe(local[['name','units','gross','gross_contribution_before_trade']],use_container_width=True,hide_index=True)
    st.caption('Presentation mode uses the existing data and calculation functions. No favourable result is hardcoded. The baseline and proposed scenarios may be better or worse depending on the inputs.')
