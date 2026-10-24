"""Auditable, reusable business calculations for synthetic demo scenarios."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
COSTS={'RK':{'cogs':.625,'vehicle':.0175,'rent':.015,'pallet':.0125,'gondola':.0088,'support':.0225,'promoter':.015,'rebate':.0288},'Soorya':{'cogs':.4,'vehicle':.05,'rent':.0167,'support':.0267,'promoter':.0047,'rebate':.03,'expiry':.02}}

def validate(data):
    for key,cols in {'sales':['date','outlet','sku','units_sold','gross_sales_aed'],'skus':['sku','brand','type','unit_price','unit_cogs'],'agreements':['outlet','brand','type','rebate_rate']}.items():
        if key not in data or not set(cols).issubset(data[key]):raise ValueError(f'{key}: missing columns {set(cols)-set(data.get(key,pd.DataFrame()).columns)}')
    s=data['sales'];sku=data['skus']
    if s[['date','outlet','sku']].duplicated().any():raise ValueError('Duplicate daily outlet-SKU records')
    if (s.units_sold<0).any() or (s.gross_sales_aed<0).any():raise ValueError('Negative sales')
    if not set(s.sku).issubset(sku.sku):raise ValueError('Unknown SKU in sales')
    pd.to_datetime(s.date,errors='raise')
    return True

def rebates(lines,skus,agreements):
    t=lines.merge(skus[['sku','brand','type']],on='sku',validate='many_to_one')
    grouped=t.groupby(['outlet','brand','type'],as_index=False).gross_sales_aed.sum()
    result=grouped.merge(agreements,on=['outlet','brand','type'],validate='many_to_one',how='left')
    if result.rebate_rate.isna().any():raise ValueError('Missing customer/item-type rebate agreement')
    result['rebate_aed']=result.gross_sales_aed*result.rebate_rate
    return result

def contribution(lines,skus,agreements,trade_fees=None,months=1):
    t=lines.merge(skus[['sku','brand','unit_cogs']],on='sku',validate='many_to_one')
    t['cogs_aed']=t.units_sold*t.unit_cogs
    g=t.groupby('outlet',as_index=False).agg(gross_sales_aed=('gross_sales_aed','sum'),cogs_aed=('cogs_aed','sum'))
    r=rebates(lines,skus,agreements).groupby('outlet',as_index=False).rebate_aed.sum()
    g=g.merge(r,on='outlet',how='left').fillna({'rebate_aed':0})
    if trade_fees is not None:
        f=trade_fees.copy();f['trade_fees_aed']=f.listing_fee_upfront_aed+months*(f.monthly_promoter_aed+f.monthly_display_aed+f.monthly_support_aed)
        g=g.merge(f[['outlet','trade_fees_aed']],on='outlet',how='left')
    else:g['trade_fees_aed']=0
    g['trade_fees_aed']=g.trade_fees_aed.fillna(0)
    g['contribution_aed']=g.gross_sales_aed-g.cogs_aed-g.rebate_aed-g.trade_fees_aed
    return g

def forecasting_frame(sales,sku,outlet):
    s=sales[(sales.sku==sku)&(sales.outlet==outlet)].copy();s['date']=pd.to_datetime(s.date);s=s.sort_values('date').reset_index(drop=True)
    if len(s)<100:raise ValueError('At least 100 days of history required')
    s['dow']=s.date.dt.dayofweek;s['month']=s.date.dt.month
    for k in [1,7,14]:s[f'lag{k}']=s.units_sold.shift(k)
    s['mean7']=s.units_sold.shift(1).rolling(7).mean()
    return s.dropna().reset_index(drop=True)

def evaluate_forecast(sales,sku,outlet,horizon=7):
    frame=forecasting_frame(sales,sku,outlet);features=['dow','month','lag1','lag7','lag14','mean7']
    n=len(frame);a=int(n*.65);b=int(n*.82)
    train,valid,test=frame.iloc[:a],frame.iloc[a:b],frame.iloc[b:]
    model=HistGradientBoostingRegressor(max_iter=90,max_leaf_nodes=12,l2_regularization=2,random_state=2026)
    model.fit(train[features],train.units_sold)
    vp=np.maximum(0,model.predict(valid[features]));tp=np.maximum(0,model.predict(test[features]));naive=test.lag7.to_numpy()
    # Test features contain only historically observed lags. For actual future dates use recursive predictions.
    metrics={'ML MAE':float(mean_absolute_error(test.units_sold,tp)),'Naive MAE':float(mean_absolute_error(test.units_sold,naive)),'ML WAPE':float(np.abs(test.units_sold-tp).sum()/test.units_sold.sum()) if test.units_sold.sum()>0 else np.nan,'Naive WAPE':float(np.abs(test.units_sold-naive).sum()/test.units_sold.sum()) if test.units_sold.sum()>0 else np.nan,'Bias units':float(np.mean(tp-test.units_sold)),'train_end':str(train.date.max().date()),'validation_end':str(valid.date.max().date()),'test_start':str(test.date.min().date()),'test_end':str(test.date.max().date()),'heuristic_error_p90':float(np.percentile(np.abs(valid.units_sold-vp),90))}
    history=frame.units_sold.astype(float).tolist();end=frame.date.max();future=[]
    for i in range(horizon):
        dt=end+pd.Timedelta(days=i+1)
        x=pd.DataFrame([{'dow':dt.dayofweek,'month':dt.month,'lag1':history[-1],'lag7':history[-7],'lag14':history[-14],'mean7':np.mean(history[-7:])}]);y=max(0,float(model.predict(x[features])[0]));history.append(y)
        future.append([dt,y,max(0,y-metrics['heuristic_error_p90']),y+metrics['heuristic_error_p90']])
    test_view=test[['date','units_sold']].copy();test_view['ML']=tp;test_view['seasonal_naive']=naive
    return pd.DataFrame(future,columns=['date','predicted_units','low_heuristic','high_heuristic']),metrics,test_view

def fefo_stock(lots,asof):
    l=lots.copy();l['expiry_date']=pd.to_datetime(l.expiry_date);l=l[l.expiry_date>=pd.Timestamp(asof)]
    return int(l.remaining_units.clip(lower=0).sum())

def replenish(daily_forecast,stock,case_size,shelf_life_days,available_supply=10000,lead_days=1,safety=.15):
    if case_size<=0 or available_supply<0 or stock<0:raise ValueError('Invalid inventory inputs')
    arr=np.maximum(0,np.asarray(daily_forecast,dtype=float));effective=max(0,min(len(arr)-lead_days,int(shelf_life_days)))
    target=float(arr[lead_days:lead_days+effective].sum()*(1+safety))
    needed=max(0,target-stock);cases=int(np.ceil(needed/case_size));units=cases*case_size
    if units>available_supply:units=int(available_supply//case_size)*case_size
    expected_unsold=max(0,stock+units-float(arr[lead_days:lead_days+effective].sum()))
    return {'deliver_units':units,'target_units':target,'expected_unsold_units':expected_unsold,'available_supply_units':available_supply}

def route_plan(outlets,deliveries,vehicles,mode='nearest'):
    """Capacitated temperature-compatible depot tours. Coordinates are synthetic straight-line proxies."""
    if vehicles.empty or (vehicles.capacity_units<=0).any() or (vehicles.cost_per_km_aed<0).any():raise ValueError('Vehicles must have positive capacities and nonnegative costs')
    lookup=outlets.set_index('outlet');v=vehicles.to_dict('records');pending=[(o,int(q),temp) for o,q,temp in deliveries if q>0];routes=[];unmet=[]
    for o,q,temp in pending:
        if o not in lookup.index:raise ValueError(f'Unknown outlet {o}')
        if not any(x['temperature']==temp for x in v):unmet.append((o,q,'No compatible vehicle'))
    pending=[p for p in pending if not any(u[0]==p[0] and u[2]=='No compatible vehicle' for u in unmet)]
    for temp in sorted(set(p[2] for p in pending)):
        compatible=[x for x in v if x['temperature']==temp]
        remaining={o:q for o,q,t in pending if t==temp}
        while any(q>0 for q in remaining.values()):
            vehicle=compatible[len(routes)%len(compatible)];cap=int(vehicle['capacity_units']);load=0;stops=[];pos=np.array([0.,0.]);km=0.
            while load<cap:
                candidates=[o for o,q in remaining.items() if q>0]
                if not candidates:break
                if mode=='baseline':o=sorted(candidates)[0]
                else:o=min(candidates,key=lambda z:np.linalg.norm(lookup.loc[z,['x_km_proxy','y_km_proxy']].to_numpy(float)-pos))
                q=min(cap-load,remaining[o]);point=lookup.loc[o,['x_km_proxy','y_km_proxy']].to_numpy(float)
                km+=float(np.linalg.norm(point-pos));pos=point;load+=q;remaining[o]-=q;stops.append((o,q))
            km+=float(np.linalg.norm(pos));routes.append({'vehicle':vehicle['vehicle'],'temperature':temp,'stops':stops,'load':load,'capacity':cap,'distance_proxy_km':km,'cost_aed':km*float(vehicle['cost_per_km_aed'])})
    return routes,unmet

def sku_scores(lines,skus,weights=(.4,.35,.25)):
    s=lines.groupby('sku',as_index=False).agg(units=('units_sold','sum'),sales=('gross_sales_aed','sum'),outlets=('outlet','nunique'),returns=('returns_units','sum'))
    s=s.merge(skus,on='sku');s['contribution_proxy']=s.sales-s.units*s.unit_cogs
    for k in ['units','contribution_proxy','outlets']:
        lo,hi=s[k].min(),s[k].max();s[k+'_norm']=(s[k]-lo)/(hi-lo) if hi>lo else .5
    w=np.array(weights,dtype=float);w=w/w.sum()
    s['score']=100*(w[0]*s.units_norm+w[1]*s.contribution_proxy_norm+w[2]*s.outlets_norm)
    s['action']=np.select([s.score>=65,s.score>=45,s.score>=25],['Invest','Keep','Consolidate'],default='Review for Delisting')
    s.loc[s.regulated_category & (s.action=='Review for Delisting'),'action']='Keep'
    s['confidence']='Illustrative: validate account requirements and substitution'
    return s
