from engine import *
import pandas as pd

def test_rebate_example():
 a=pd.DataFrame([('A','RK','RK Discount Item',0.),('A','RK','Rice Item',.1)],columns=['outlet','brand','type','rate'])
 s=pd.DataFrame([('A','RK','RK Discount Item',300),('A','RK','Rice Item',150)],columns=['outlet','brand','type','sales'])
 assert abs(rebate_amount(s,a).rebate_value.sum()-15)<1e-8

def test_soorya_rebate():
 a=pd.DataFrame([('A','Soorya','Soorya',.05)],columns=['outlet','brand','type','rate'])
 s=pd.DataFrame([('A','Soorya','Soorya',2000)],columns=['outlet','brand','type','sales'])
 assert rebate_amount(s,a).rebate_value.sum()==100

def test_costs():
 assert abs(sum(COSTS['RK'].values())-.7451)<1e-8
 assert abs(sum(COSTS['Soorya'].values())-.5481)<1e-8

def test_replenishment():
 assert replenish([10]*7,0,3,safety=0)[0]==30
 assert replenish([10]*7,50,3,safety=0)[0]==0

def test_route_capacity():
 _,o,_,_=make_data(); routes=route_plan(o,{x:500 for x in o.outlet[:3]},capacity=400)
 assert sum(r['load'] for r in routes)==1500
 assert all(r['load']<=400 for r in routes)

def test_reproducible():
 x=make_data();y=make_data()
 for a,b in zip(x,y):pd.testing.assert_frame_equal(a,b)
