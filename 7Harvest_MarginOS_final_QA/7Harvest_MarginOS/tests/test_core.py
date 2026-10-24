import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest
from core import rebates,fefo_stock,replenish,route_plan,sku_scores,validate,evaluate_forecast
from data.generate_demo_data import generate
@pytest.fixture(scope='module')
def data(tmp_path_factory):return generate(tmp_path_factory.mktemp('demo'))
def test_rebate_by_type():
    sku=pd.DataFrame([['A','RK','Rice Item'],['B','RK','Other']],columns=['sku','brand','type']);lines=pd.DataFrame([['O','A',100],['O','B',200]],columns=['outlet','sku','gross_sales_aed']);terms=pd.DataFrame([['O','RK','Rice Item',.1],['O','RK','Other',0]],columns=['outlet','brand','type','rebate_rate']);assert rebates(lines,sku,terms).rebate_aed.sum()==10
def test_fefo():
    l=pd.DataFrame([['2026-01-01',50],['2026-12-31',20]],columns=['expiry_date','remaining_units']);assert fefo_stock(l,'2026-02-01')==20
def test_case_capacity():
    r=replenish([10]*7,0,12,5,available_supply=30);assert r['deliver_units']%12==0 and r['deliver_units']<=30
def test_validation(data):assert validate(data)
def test_deterministic(tmp_path):
    a=generate(tmp_path/'a');b=generate(tmp_path/'b');pd.testing.assert_frame_equal(a['sales'],b['sales'])
def test_routes_capacity(data):
    routes,unmet=route_plan(data['outlets'],[('O01',1000,'Chilled')],data['vehicles']);assert not unmet and sum(r['load'] for r in routes)==1000 and all(r['load']<=r['capacity'] for r in routes)
def test_routes_incompatible(data):
    v=data['vehicles'].query("temperature=='Ambient'");routes,unmet=route_plan(data['outlets'],[('O01',10,'Chilled')],v);assert unmet and not routes
def test_scores(data):
    s=sku_scores(data['sales'].head(5000),data['skus']);assert s.score.between(0,100).all()
def test_forecast(data):
    f,m,t=evaluate_forecast(data['sales'],'SO001','O01');assert len(f)==7 and t.date.min()>pd.Timestamp(m['validation_end']) and f.predicted_units.ge(0).all()
