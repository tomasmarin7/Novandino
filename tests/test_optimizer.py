from copy import deepcopy
import threading
import pytest
from pydantic import ValidationError
from backend.schema import make_demo,Scenario,Point,Well,Machine,Requirement,PHASES
from backend.optimizer import solve
from backend.verify import verify

def compact(n=3):
    s=make_demo(n)
    s.durations={p:1 for p in PHASES}
    s.time_limit=3
    return s

def test_complete_schedule_and_independent_verifier():
    s=compact()
    r=solve(s)
    assert r['status'] in ('OPTIMAL','FEASIBLE')
    assert r['verification']['valid']
    assert len(r['wells'])==3
    assert verify(s,r)==[]
    assert all(abs(w['phases'][1]['end']-w['phases'][1]['start']-1)<1e-6 for w in r['wells'])
    assert any(e['state']=='refill' for t in r['machines'] for e in t['events'])
    for t in r['machines']:
        assert all(e['end']<=r['makespan']+1e-6 for e in t['events'])

def test_verifier_detects_teleport_and_capacity_corruption():
    s=compact(2)
    r=solve(s)
    bad=deepcopy(r)
    b=next(b for b in bad['bookings'] if b['machine'].startswith('G'))
    b['position']={'x':9999,'y':9999}
    assert any('cobertura' in e for e in verify(s,bad))
    bad=deepcopy(r)
    track=next(t for t in bad['machines'] if len(t['events'])>1)
    track['events'][1]['from']['x']+=100
    assert any('teletransporte' in e for e in verify(s,bad))

def shared_case(capacity=40,simultaneous=2):
    s=compact(2)
    s.wells=[Well(id='P01',x=100,y=100),Well(id='P02',x=300,y=100)]
    s.machines=[Machine(id='D01',kind='rig',initial=s.depot,speed=10000,radius=0,setup=0,disconnect=0),
                Machine(id='D02',kind='rig',initial=s.depot,speed=10000,radius=0,setup=0,disconnect=0),
                Machine(id='G01',kind='generator',initial=s.depot,speed=10000,radius=110,capacity=capacity,
                        simultaneous=simultaneous,setup=0,disconnect=0)]
    s.water_demand=0
    s.requirements=[Requirement(kind='generator',phases=['drill'],demand=20)]
    s.mode='fleet'
    s.deadline=7.1
    return s

def test_auxiliary_can_share_from_a_non_well_coordinate():
    s=shared_case()
    r=solve(s)
    assert r['status']=='OPTIMAL'
    g=[b for b in r['bookings'] if b['machine']=='G01']
    assert len(g)==2
    assert g[0]['position']==g[1]['position']
    assert g[0]['position'] not in [{'x':w.x,'y':w.y} for w in s.wells]
    assert g[0]['work_start']==g[1]['work_start']

@pytest.mark.parametrize('capacity,k',[(20,2),(40,1)])
def test_physical_and_simultaneous_limits_are_both_enforced(capacity,k):
    assert solve(shared_case(capacity,k))['status']=='INFEASIBLE'

def test_fleet_minimization_can_leave_available_units_unused():
    s=compact(1)
    s.mode='fleet';s.deadline=40
    r=solve(s)
    assert r['status']=='OPTIMAL'
    assert r['fleet_used']['rig']==1
    assert r['fleet_used']['test']==1
    assert r['makespan']<=40

def test_fixed_drilling_duration_and_schema_errors():
    d=make_demo(1).model_dump()
    d['wells'][0]['durations']={'drill':5}
    with pytest.raises(ValidationError,match='perforación'):Scenario.model_validate(d)
    d=make_demo(1).model_dump();d['water_demand']=50
    with pytest.raises(ValidationError,match='tanque'):Scenario.model_validate(d)
    d=make_demo(1).model_dump();d['machines']=[m for m in d['machines'] if m['kind']!='generator']
    with pytest.raises(ValidationError,match='generator'):Scenario.model_validate(d)

def test_manhattan_travel_has_corner_and_no_teleport():
    s=compact(2);s.metric='manhattan_demo'
    r=solve(s)
    assert r['verification']['valid']
    assert any(len(e['path'])==3 for t in r['machines'] for e in t['events'] if e['state']=='travel')

def test_cancel_before_solving():
    event=threading.Event();event.set()
    assert solve(compact(1),cancelled=event)['status']=='CANCELLED'

def test_disconnect_after_last_phase_is_included():
    s=compact(1)
    for m in s.machines:
        if m.kind=='test':m.disconnect=3
    r=solve(s)
    assert r['makespan']>=r['wells'][0]['completion']+3-1e-5

def test_individual_availability_and_duration_overrides():
    s=compact(2)
    for m in s.machines:
        if m.kind=='test':m.available=50
    s.wells[0].durations={'pump':3}
    r=solve(s)
    assert all(w['phases'][3]['start']>=50 for w in r['wells'])
    p=r['wells'][0]['phases'][4]
    assert p['end']-p['start']==3

def test_distinct_auxiliary_routes_and_all_wells_in_multiple_cases():
    for seed in (7,91):
        s=compact(5);s.seed=seed;s.wells=make_demo(5,seed).wells
        r=solve(s)
        assert r['status'] in ('OPTIMAL','FEASIBLE')
        assert not verify(s,r)
