import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import numpy as np
import pytest
from core import validate,rebates,contribution,replenish,route_plan,sku_scores,forecasting_frame
ROOT=Path(__file__).resolve().parents[1]/'data'
@pytest.fixture(scope='module')
def d():return {n:pd.read_csv(ROOT/f'{n}.csv') for n in ['skus','outlets','agreements','trade_fees','sales','inventory_lots','vehicles']}
def test_all_foreign_keys(d):
 for k,ref,col in [('sales','skus','sku'),('sales','outlets','outlet'),('inventory_lots','skus','sku'),('inventory_lots','outlets','outlet'),('agreements','outlets','outlet'),('trade_fees','outlets','outlet')]:assert set(d[k][col]).issubset(set(d[ref][col]))
def test_agreement_coverage(d):
 assert not d['agreements'].duplicated(['outlet','brand','type']).any()
 assert rebates(d['sales'],d['skus'],d['agreements']).rebate_rate.notna().all()
def test_sales_reconciliation(d):
 p=d['sales'].sku.map(d['skus'].set_index('sku').unit_price)
 assert np.allclose(d['sales'].gross_sales_aed,d['sales'].units_sold*p,atol=.011)
def test_soorya_discount(d):
 t=d['sales'].query("outlet=='O01' and sku=='SO001'").head(1)
 r=rebates(t,d['skus'],d['agreements'])
 assert r.rebate_aed.iloc[0]==pytest.approx(r.gross_sales_aed.iloc[0]*r.rebate_rate.iloc[0])
def test_negative_upload(d):
 bad=dict(d);bad['sales']=d['sales'].head(10).copy();bad['sales'].loc[bad['sales'].index[0],'units_sold']=-1
 with pytest.raises(ValueError,match='Negative'):validate(bad)
def test_unknown_sku(d):
 bad=dict(d);bad['sales']=d['sales'].head(10).copy();bad['sales'].loc[bad['sales'].index[0],'sku']='UNKNOWN'
 with pytest.raises(ValueError,match='Unknown SKU'):validate(bad)
def test_missing_terms(d):
 t=d['sales'].query("outlet=='O01' and sku=='SO001'").head(1)
 with pytest.raises(ValueError,match='Missing'):rebates(t,d['skus'],d['agreements'].query("outlet!='O01'"))
def test_zero_demand_replenish():assert replenish([0]*7,0,12,5,30)['deliver_units']==0
def test_insufficient_capacity(d):
 v=d['vehicles'].query("temperature=='Chilled'").head(1).copy();v.loc[:,'capacity_units']=1
 routes,unmet=route_plan(d['outlets'],[('O01',100,'Chilled')],v)
 assert sum(r['load'] for r in routes)==100 and all(r['load']<=1 for r in routes)
def test_no_future_lag_leakage(d):
 f=forecasting_frame(d['sales'],'SO001','O01');raw=d['sales'].query("sku=='SO001' and outlet=='O01'").sort_values('date').reset_index(drop=True)
 assert np.allclose(f.lag1,raw.units_sold.shift(1).dropna().iloc[13:].to_numpy())
def test_weight_change(d):
 a=sku_scores(d['sales'],d['skus'],(1,0,0));b=sku_scores(d['sales'],d['skus'],(0,1,0))
 assert not np.allclose(a.score,b.score)
def test_missing_upload_columns(d):
 bad=dict(d);bad['sales']=d['sales'].drop(columns='date')
 with pytest.raises(ValueError,match='missing columns'):validate(bad)
@pytest.mark.xfail(strict=True,reason='Existing replenishment does not account for expiry dates of existing stock')
def test_existing_stock_expiring_before_consumption():
 assert replenish([10]*7,100,10,3,100)['deliver_units']>=40
@pytest.mark.xfail(strict=True,reason='Existing routing does not enforce max_hours')
def test_route_max_hours(d):
 v=d['vehicles'].query("temperature=='Chilled'").head(1).copy();v.loc[:,'max_hours']=0
 routes,_=route_plan(d['outlets'],[('O01',10,'Chilled')],v)
 assert not routes
@pytest.mark.xfail(strict=True,reason='No uploaded data validation UI')
def test_upload_control_present():
 assert 'st.file_uploader' in (Path(__file__).resolve().parents[1]/'app.py').read_text()
