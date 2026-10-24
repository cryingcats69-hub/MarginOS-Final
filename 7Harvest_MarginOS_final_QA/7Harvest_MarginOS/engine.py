import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.spatial.distance import cdist

SEED=2026
COSTS={'RK':{'cogs':.625,'vehicle':.0175,'rent':.015,'pallet':.0125,'gondola':.0088,'support':.0225,'promoter':.015,'rebate':.0288},'Soorya':{'cogs':.40,'vehicle':.05,'rent':.0167,'support':.0267,'promoter':.0047,'rebate':.03,'expiry':.02}}
CATEGORIES=['Pulses','Miscellaneous','Spice powders','Seeds','Beans & peas','Whole spices','Rice','Flour','Nuts & dry fruits']
SHARES=[23,21,19,9,9,7,7,3,2]
BRANDED=[.25,.61,.54,.41,.30,.46,.64,.50,.44]

def make_data(seed=SEED):
 r=np.random.default_rng(seed)
 cats=np.repeat(CATEGORIES,SHARES)
 skus=[]
 for i,cat in enumerate(cats):
  brand='RK' if r.random()<BRANDED[CATEGORIES.index(cat)] else 'Other'
  typ=('Rice Item' if cat=='Rice' and brand=='RK' else ('RK Promo Item' if r.random()<.14 else 'RK Discount Item') if brand=='RK' else 'Other')
  skus.append((f'RK-{i+1:03}', 'RK',cat,typ,brand,round(float(r.uniform(5,35)),2),int(r.integers(90,450)),0))
 soorya=['Malabar porotta','Whole wheat porotta','Whole wheat chapati','Rice idiyappam','Idli/dosa batter','Appam batter','Ragi batter','Palakkadan matta rice']
 for i,cat in enumerate(soorya):skus.append((f'SO-{i+1:03}','Soorya',cat,'Soorya','Soorya',round(float(r.uniform(6,25)),2),int(r.integers(35,110)),int(r.integers(4,12))))
 sku=pd.DataFrame(skus,columns=['sku','brand','category','type','label','unit_price','base_daily_units','shelf_life_days'])
 outlets=pd.DataFrame({'outlet':[f'OUT-{i+1:02}' for i in range(12)],'x':r.uniform(0,35,12),'y':r.uniform(0,30,12),'demand_factor':r.uniform(.5,1.6,12),'channel':['Modern trade']*6+['General trade']*6})
 agreements=[]
 for outlet in outlets.outlet:
  for typ in ['RK Discount Item','RK Promo Item','Rice Item','Other']:
   agreements.append((outlet,'RK',typ,round(float(r.uniform(0,.06)),4)))
  agreements.append((outlet,'Soorya','Soorya',round(float(r.uniform(.01,.055)),4)))
 agreements=pd.DataFrame(agreements,columns=['outlet','brand','type','rate'])
 days=pd.date_range('2026-01-01',periods=120)
 records=[]
 for row in sku.itertuples(index=False):
  for o in outlets.itertuples(index=False):
   baseline=row.base_daily_units/12*o.demand_factor
   for t,date in enumerate(days):
    season=1+.16*np.sin(2*np.pi*t/30)+.08*np.cos(2*np.pi*t/7)
    units=int(r.poisson(max(.1,baseline*season*(1+.10*(date.dayofweek in [5,6])))))
    records.append((date,row.sku,o.outlet,row.brand,row.category,row.type,units,round(units*row.unit_price,2)))
 sales=pd.DataFrame(records,columns=['date','sku','outlet','brand','category','type','units','sales'])
 return sku,outlets,agreements,sales

def rebate_amount(lines,agreements):
 grouped=lines.groupby(['outlet','brand','type'],as_index=False)['sales'].sum()
 merged=grouped.merge(agreements,on=['outlet','brand','type'],how='left',validate='many_to_one')
 if merged.rate.isna().any():raise ValueError('Missing customer/type agreement')
 merged['rebate_value']=merged.sales*merged.rate
 return merged

def margin_by_brand(sales,agreements):
 rebates=rebate_amount(sales,agreements).groupby('brand').rebate_value.sum()
 out=[]
 for brand,group in sales.groupby('brand'):
  revenue=group.sales.sum(); fixed=sum(v for k,v in COSTS[brand].items() if k!='rebate')
  cost=revenue*fixed+rebates.get(brand,0)
  out.append((brand,revenue,cost,revenue-cost,(revenue-cost)/revenue,rebates.get(brand,0)))
 return pd.DataFrame(out,columns=['brand','revenue','listed_costs','contribution_before_overhead','contribution_rate','actual_synthetic_rebate'])

def forecast(sales,sku_id,outlet_id,horizon=7):
 sub=sales[(sales.sku==sku_id)&(sales.outlet==outlet_id)].sort_values('date').copy()
 if len(sub)<35:raise ValueError('At least 35 daily records needed')
 sub['day']=np.arange(len(sub));sub['dow']=sub.date.dt.dayofweek
 for lag in [1,7]:sub[f'lag{lag}']=sub.units.shift(lag)
 sub['avg7']=sub.units.shift(1).rolling(7).mean()
 sub=sub.dropna(); features=['day','dow','lag1','lag7','avg7']
 split=int(len(sub)*.8);train,test=sub.iloc[:split],sub.iloc[split:]
 model=RandomForestRegressor(n_estimators=65,max_depth=9,min_samples_leaf=2,random_state=SEED,n_jobs=-1)
 model.fit(train[features],train.units)
 pred=model.predict(test[features]); mae=mean_absolute_error(test.units,pred);rmse=np.sqrt(mean_squared_error(test.units,pred))
 # Recursive forward forecast: no future actual sales used.
 history=sales[(sales.sku==sku_id)&(sales.outlet==outlet_id)].sort_values('date').units.astype(float).tolist()
 future=[]
 for h in range(horizon):
  date=sales.date.max()+pd.Timedelta(days=h+1)
  x=pd.DataFrame([{'day':len(history),'dow':date.dayofweek,'lag1':history[-1],'lag7':history[-7],'avg7':np.mean(history[-7:])}])
  y=max(0,float(model.predict(x[features])[0]));future.append((date,y));history.append(y)
 return pd.DataFrame(future,columns=['date','forecast_units']),{'MAE':mae,'RMSE':rmse,'holdout_days':len(test),'baseline_MAE':mean_absolute_error(test.units,test.lag7)}

def replenish(forecast_units,on_hand,shelf_life,lead_days=1,safety=0.15):
 demand=np.asarray(forecast_units,dtype=float); window=len(demand) if shelf_life==0 else min(len(demand),shelf_life)
 target=np.sum(demand[:window])*(1+safety)
 return max(0,int(np.ceil(target-on_hand))),max(0,round(on_hand-target,2))

def route_plan(outlets,deliveries,capacity=400):
 # Nearest-neighbour capacitated routing with a depot at (0,0); Euclidean proxy, not road km.
 lookup=outlets.set_index('outlet');pending={k:float(v) for k,v in deliveries.items() if v>0};routes=[]
 while pending:
  route=[];load=0;pos=np.array([0.,0.]);dist=0.
  while pending and load<capacity:
   choices=[k for k,v in pending.items() if v>0]
   if not choices:break
   k=min(choices,key=lambda z:np.linalg.norm(pos-lookup.loc[z,['x','y']].to_numpy(dtype=float)))
   q=min(capacity-load,pending[k]);point=lookup.loc[k,['x','y']].to_numpy(dtype=float)
   dist+=float(np.linalg.norm(point-pos));pos=point;load+=q;route.append((k,q));pending[k]-=q
   if pending[k]<=0:del pending[k]
  dist+=float(np.linalg.norm(pos));routes.append({'stops':route,'load':load,'distance_proxy':dist})
 return routes

def trade_scenario(sales,agreements,outlet,brand,rebate_reduction=0,listing_fee=2000,trade_support=0):
 s=sales[(sales.outlet==outlet)&(sales.brand==brand)]
 rev=float(s.sales.sum());base=float(rebate_amount(s,agreements).rebate_value.sum())
 revised=max(0,base*(1-rebate_reduction));cogs=rev*COSTS[brand]['cogs']
 other=rev*sum(v for k,v in COSTS[brand].items() if k not in ['rebate','cogs'])
 contribution=rev-cogs-other-revised-trade_support
 return {'revenue':rev,'current_rebate':base,'scenario_rebate':revised,'contribution_after_listing':contribution-listing_fee,'listing_coverage':(contribution/listing_fee if listing_fee>0 else np.nan),'delta_vs_base':base-revised-trade_support}

def sku_scores(sales,skus,agreements):
 a=sales.groupby(['sku','brand','category','type'],as_index=False).agg(revenue=('sales','sum'),units=('units','sum'),outlets=('outlet','nunique'))
 b=rebate_amount(sales,agreements).groupby(['brand','type'],as_index=False).agg(rebate=('rebate_value','sum'),sales=('sales','sum'))
 b['rate']=b.rebate/b.sales
 a=a.merge(b[['brand','type','rate']],on=['brand','type'])
 a['contribution']=a.revenue*(1-a.brand.map(lambda x:sum(v for k,v in COSTS[x].items() if k!='rebate'))-a.rate)
 a['score']=100*(.45*a.contribution.rank(pct=True)+.35*a.units.rank(pct=True)+.20*a.outlets.rank(pct=True))
 a['action']=np.select([a.score<25,a.score<45,a.score>=75],['Review / pilot delist','Fix or relocate','Prioritise'],default='Maintain')
 return a.sort_values('score',ascending=False)
