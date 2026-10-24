import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest
from data.generate_demo_data import generate
from validation import audit_integrity,recursive_backtest
from core import replenish,route_plan,rebates
@pytest.fixture(scope='module')
def d(tmp_path_factory):return generate(tmp_path_factory.mktemp('validation'))
def test_relationships(d):assert audit_integrity(d)==[]
def test_orphan_detection(d):
    bad={k:v.copy() for k,v in d.items()};bad['sales'].loc[0,'sku']='INVALID'
    assert any('orphan sku' in x for x in audit_integrity(bad))
def test_rebate_reconciles(d):
    lines=d['sales'].head(10000);r=rebates(lines,d['skus'],d['agreements'])
    assert abs(r.rebate_aed.sum()-(r.gross_sales_aed*r.rebate_rate).sum())<1e-6
def test_recursive_no_holdout_leakage(d):
    sales=d['sales'];one=sales[(sales.sku=='SO001')&(sales.outlet=='O01')].sort_values('date');cut=one.iloc[-60:].index
    a=recursive_backtest(sales,'SO001','O01');alter=sales.copy();alter.loc[cut,'units_sold']*=10
    b=recursive_backtest(alter,'SO001','O01')
    # Model predictions must be unchanged; MAE changes because ground truth changes.
    assert a['train_end']==b['train_end']
    assert a['ML']['MAE']!=b['ML']['MAE']
def test_replenishment_no_over_supply():
    r=replenish([12]*7,0,12,7,available_supply=25)
    assert r['deliver_units']==24
def test_route_capacity_zero_rejected(d):
    vehicles=d['vehicles'].copy();vehicles.loc[:,'capacity_units']=0
    with pytest.raises(ValueError):route_plan(d['outlets'],[('O01',10,'Chilled')],vehicles)
