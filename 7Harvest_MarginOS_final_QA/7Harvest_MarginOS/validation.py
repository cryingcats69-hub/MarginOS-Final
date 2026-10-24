"""Independent integrity checks and leakage-safe rolling forecast evaluation."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

def audit_integrity(d):
    issues=[]
    sk,ou,sa,ag,lo=d['skus'],d['outlets'],d['sales'],d['agreements'],d['inventory_lots']
    for name,frame,cols in [('skus',sk,['sku']),('outlets',ou,['outlet']),('agreements',ag,['outlet','brand','type']),('inventory_lots',lo,['lot']),('sales',sa,['date','outlet','sku'])]:
        if frame.duplicated(cols).any():issues.append(f'{name}: duplicate key')
    for name,frame,col,ref in [('sales',sa,'sku',sk.sku),('sales',sa,'outlet',ou.outlet),('inventory_lots',lo,'sku',sk.sku),('inventory_lots',lo,'outlet',ou.outlet),('agreements',ag,'outlet',ou.outlet),('trade_fees',d['trade_fees'],'outlet',ou.outlet)]:
        if not set(frame[col]).issubset(set(ref)):issues.append(f'{name}: orphan {col}')
    if (sa.units_sold<0).any() or (sa.gross_sales_aed<0).any():issues.append('negative sales')
    if not np.allclose(sa.gross_sales_aed.to_numpy(),sa.units_sold.to_numpy()*sa.sku.map(sk.set_index('sku').unit_price).to_numpy(),atol=.011):issues.append('sales value does not reconcile')
    if not (sa.units_sold+sa.lost_units_SYNTHETIC_ONLY==sa.latent_demand_SYNTHETIC_ONLY).all():issues.append('latent demand does not reconcile')
    if (lo.remaining_units<0).any() or (pd.to_datetime(lo.expiry_date)<pd.to_datetime(lo.received_date)).any():issues.append('invalid lots')
    if not (ag.rebate_rate.between(0,1)).all():issues.append('invalid rebate rates')
    combos=sa[['outlet','sku']].drop_duplicates().merge(sk[['sku','brand','type']],on='sku').merge(ag,on=['outlet','brand','type'],how='left')
    if combos.rebate_rate.isna().any():issues.append('missing agreements')
    return issues

def recursive_backtest(sales,sku,outlet,holdout_days=60):
    """Train on prefix only, recursively forecast holdout; never use holdout observations as features."""
    s=sales[(sales.sku==sku)&(sales.outlet==outlet)].sort_values('date').copy()
    s['date']=pd.to_datetime(s.date)
    y=s.units_sold.to_numpy(dtype=float); dates=s.date.to_numpy()
    if len(y)<holdout_days+70:raise ValueError('Insufficient history')
    cutoff=len(y)-holdout_days
    X=[];target=[]
    for i in range(14,cutoff):
        dt=pd.Timestamp(dates[i]);X.append([dt.dayofweek,dt.month,y[i-1],y[i-7],y[i-14],np.mean(y[i-7:i])]);target.append(y[i])
    model=HistGradientBoostingRegressor(max_iter=90,max_leaf_nodes=12,l2_regularization=2,random_state=2026).fit(np.array(X),np.array(target))
    history=list(y[:cutoff]); predictions=[]
    for i in range(cutoff,len(y)):
        dt=pd.Timestamp(dates[i]);features=np.array([[dt.dayofweek,dt.month,history[-1],history[-7],history[-14],np.mean(history[-7:])]])
        pred=max(0,float(model.predict(features)[0]));predictions.append(pred);history.append(pred)
    actual=y[cutoff:];naive=y[cutoff-7:len(y)-7]
    def met(pred):
        err=np.asarray(pred)-actual
        return {'MAE':float(np.abs(err).mean()),'WAPE':float(np.abs(err).sum()/actual.sum()) if actual.sum()>0 else np.nan,'bias':float(err.mean())}
    return {'ML':met(predictions),'seasonal_naive':met(naive),'test_start':str(pd.Timestamp(dates[cutoff]).date()),'test_end':str(pd.Timestamp(dates[-1]).date()),'train_end':str(pd.Timestamp(dates[cutoff-1]).date())}
