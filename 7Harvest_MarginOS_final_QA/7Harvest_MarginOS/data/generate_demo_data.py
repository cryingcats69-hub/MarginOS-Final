"""Deterministic illustrative data, never company operational records."""
from pathlib import Path
import numpy as np
import pandas as pd
SEED=2026
ROOT=Path(__file__).resolve().parent

def generate(out=ROOT,seed=SEED):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(seed)
    cats=['Pulses','Rice','Spice powders','Beans & peas','Whole spices','Miscellaneous','Flour','Seeds','Nuts & dry fruits']
    names=['Moong dal','Basmati rice','Turmeric powder','Black-eye beans','Cumin whole','Cooking oil','Atta','Sesame','Cashews']
    rk=[]
    for i in range(19):
        j=i%len(cats);typ='Rice Item' if cats[j]=='Rice' else ['RK Discount Item','RK Promo Item','Other'][i%3]
        rk.append([f'RK{i+1:03}','RK',cats[j],f'{names[j]} {500+(i%4)*500}g',typ,round(float(rng.uniform(6,32)),2),int(rng.choice([6,12,24])),180,'Ambient',bool(cats[j] in ['Rice','Pulses','Miscellaneous','Flour'])])
    so=['Malabar porotta','Whole wheat porotta','Whole wheat chapati','Rice idiyappam','Idli/dosa batter','Appam batter','Ragi batter','Palakkadan matta rice']
    for i,n in enumerate(so):rk.append([f'SO{i+1:03}','Soorya','Fresh & frozen',n,'Soorya',round(float(rng.uniform(7,20)),2),int(rng.choice([5,10])),int(rng.integers(5,15)),'Chilled',False])
    skus=pd.DataFrame(rk,columns=['sku','brand','category','name','type','unit_price','case_size','shelf_life_days','temperature','regulated_category'])
    skus['unit_cogs']=np.where(skus.brand=='RK',skus.unit_price*.625,skus.unit_price*.40).round(4)
    places=['Sharjah','Dubai','Ajman','Abu Dhabi','Al Ain'];outlets=[]
    for i in range(15):
        loc=places[i%5];outlets.append([f'O{i+1:02}',f'Synthetic Outlet {i+1}',loc,round(float(rng.uniform(0,45)),2),round(float(rng.uniform(0,45)),2),round(float(rng.uniform(.7,1.4)),3),int(rng.integers(8,12)),int(rng.integers(15,20))])
    outlets=pd.DataFrame(outlets,columns=['outlet','name','locality','x_km_proxy','y_km_proxy','demand_factor','window_start','window_end'])
    terms=[]
    for o in outlets.outlet:
        for t in ['RK Discount Item','RK Promo Item','Rice Item','Other']:
            terms.append([o,'RK',t,round(float(rng.uniform(0,.055)),4)])
        terms.append([o,'Soorya','Soorya',round(float(rng.uniform(.01,.055)),4)])
    terms=pd.DataFrame(terms,columns=['outlet','brand','type','rebate_rate'])
    fees=[]
    for o in outlets.outlet:
        fees.append([o,round(float(rng.uniform(300,1800)),2),round(float(rng.uniform(100,600)),2),round(float(rng.uniform(40,180)),2),round(float(rng.uniform(30,150)),2)])
    fees=pd.DataFrame(fees,columns=['outlet','listing_fee_upfront_aed','monthly_promoter_aed','monthly_display_aed','monthly_support_aed'])
    dates=pd.date_range('2025-04-01',periods=548,freq='D');rows=[]
    for s in skus.itertuples(index=False):
        for o in outlets.itertuples(index=False):
            base=rng.uniform(1.8,9.0)*o.demand_factor*(1.2 if s.brand=='Soorya' else 1)
            for dt in dates:
                dow=1.20 if dt.dayofweek in [4,5] else .93 if dt.dayofweek==0 else 1
                annual=1+.14*np.sin(2*np.pi*dt.dayofyear/365)
                # Illustrative calendar effect; not a verified UAE holiday schedule.
                event=1.25 if dt.month in [3,4,11] and dt.day<=12 else 1
                promo=int(rng.random()<.035);true=int(rng.poisson(max(.01,base*dow*annual*event*(1+.2*promo))))
                availability=int(rng.random()<.065);observed=min(true,int(rng.integers(0,max(1,true+1)))) if availability else true
                returned=int(rng.binomial(observed,.012));expired=int(rng.binomial(max(0,observed),.018 if s.brand=='Soorya' else .002))
                rows.append([dt.strftime('%Y-%m-%d'),o.outlet,s.sku,true,observed,max(0,true-observed),returned,expired,promo,round(observed*s.unit_price,2)])
    sales=pd.DataFrame(rows,columns=['date','outlet','sku','latent_demand_SYNTHETIC_ONLY','units_sold','lost_units_SYNTHETIC_ONLY','returns_units','expired_units','promotion_known','gross_sales_aed'])
    lots=[]
    for s in skus.itertuples(index=False):
        for o in outlets.outlet:
            for k in range(2):
                rec=dates[-1]-pd.Timedelta(days=int(rng.integers(0,max(2,s.shelf_life_days//3))))
                lots.append([f'{s.sku}-{o}-{k}',o,s.sku,rec.strftime('%Y-%m-%d'),(rec+pd.Timedelta(days=s.shelf_life_days)).strftime('%Y-%m-%d'),int(rng.integers(0,24))])
    lots=pd.DataFrame(lots,columns=['lot','outlet','sku','received_date','expiry_date','remaining_units'])
    vehicles=pd.DataFrame([['V1',500,.9,8,'Ambient'],['V2',350,1.2,8,'Chilled'],['V3',350,1.2,8,'Chilled'],['V4',500,.9,8,'Ambient']],columns=['vehicle','capacity_units','cost_per_km_aed','max_hours','temperature'])
    for name,frame in [('skus',skus),('outlets',outlets),('agreements',terms),('trade_fees',fees),('sales',sales),('inventory_lots',lots),('vehicles',vehicles)]:frame.to_csv(out/f'{name}.csv',index=False)
    return {n:pd.read_csv(out/f'{n}.csv') for n in ['skus','outlets','agreements','trade_fees','sales','inventory_lots','vehicles']}
if __name__=='__main__':
    d=generate();print({k:len(v) for k,v in d.items()})
