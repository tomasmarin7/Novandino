"""Independent physical checks on the exported plan, without solver variables."""
from itertools import combinations
from .schema import PHASES, Point
from .geometry import distance, travel, TICKS, ticks

EPS = 1e-4

def verify(s, plan):
    errors=[]
    def check(ok,message):
        if not ok: errors.append(message)
    bookings=plan['bookings']
    machines={m.id:m for m in s.machines}
    wells={w.id:w for w in s.wells}
    planned={w['id']:w for w in plan['wells']}
    check(set(planned)==set(wells),'Pozos incompletos o inesperados')
    for wid,w in wells.items():
        phases=planned[wid]['phases']
        for e,p in enumerate(phases):
            dur=ticks(w.durations.get(PHASES[e],s.durations[PHASES[e]]))/TICKS
            check(abs(p['end']-p['start']-dur)<EPS,f'{wid}: duración {p["id"]}')
            if e: check(p['start']+EPS>=phases[e-1]['end'],f'{wid}: precedencia')
        rig=[b for b in bookings if b['well']==wid and machines[b['machine']].kind=='rig']
        check(len(rig)==1,f'{wid}: asignación de perforadora')
        for req in s.requirements:
            for p in req.phases:
                e=PHASES.index(p)
                active=[b for b in bookings if b['well']==wid and machines[b['machine']].kind==req.kind and b['first']<=e<=b['last']]
                check(len(active)==1,f'{wid}: falta o duplica servicio {req.kind}/{p}')
                for b in active:
                    check(b['work_start']<=phases[e]['start']+EPS and b['work_end']+EPS>=phases[e]['end'],f'{wid}: servicio incompleto')
                    check(abs(b['demand']-req.demand)<EPS,f'{wid}: demanda física')
        demand=s.water_demand if w.water_demand is None else w.water_demand
        deliveries=[b for b in bookings if b['water'] and b['well']==wid]
        check(len(deliveries)==int(demand>0),f'{wid}: entregas de agua')
        for b in deliveries:
            check(b['end']<=phases[1]['start']+EPS,f'{wid}: agua tardía')
            check(abs(b['demand']-demand)<EPS and demand<=s.tank_capacity+EPS,f'{wid}: balance de agua')
        check(plan['makespan']+EPS>=phases[-1]['end'],f'{wid}: plazo final')

    for mid,m in machines.items():
        own=[b for b in bookings if b['machine']==mid]
        for b in own:
            pos=Point(**b['position'])
            check(b['start']+EPS>=m.available+travel(m.initial,pos,m,s)/TICKS,f'{mid}: disponibilidad o llegada inicial')
            check(b['end']<=plan['makespan']+EPS,f'{mid}: desconexión fuera del plan')
            check(distance(pos,wells[b['well']])<=(0 if m.kind in ('rig','water','test') else m.radius)+EPS,f'{mid}: cobertura')
            if m.kind!='rig':check(b['demand']<=m.capacity+EPS,f'{mid}: capacidad física individual')
        for a,b in combinations(own,2):
            if a['start']>b['start']:a,b=b,a
            different=distance(Point(**a['position']),Point(**b['position']))>EPS
            if different or m.kind in ('rig','water','test'):
                if m.kind=='water':
                    needed=travel(Point(**a['position']),s.depot,m,s)+ticks(s.refill_time)+travel(s.depot,Point(**b['position']),m,s)
                else:needed=travel(Point(**a['position']),Point(**b['position']),m,s)
                check(b['start']+EPS>=a['end']+needed/TICKS,f'{mid}: solapamiento o traslado imposible')
        boundaries=sorted({b[k] for b in own for k in ('start','end')})
        for a,b in zip(boundaries,boundaries[1:]):
            active=[o for o in own if o['start'] <= (a+b)/2 < o['end']]
            check(len(active)<=(1 if m.kind in ('rig','test','water') else m.simultaneous),f'{mid}: capacidad simultánea')
            if m.kind not in ('rig','water'):
                check(sum(o['demand'] for o in active)<=m.capacity+EPS,f'{mid}: capacidad física compartida')
        track=next(t for t in plan['machines'] if t['id']==mid)
        previous=m.initial
        last=0
        for e in track['events']:
            a,b=Point(**e['from']),Point(**e['to'])
            check(distance(previous,a)<EPS,f'{mid}: teletransporte en animación')
            check(abs(e['start']-last)<EPS,f'{mid}: hueco o solapamiento en animación')
            if e['state']=='travel':
                check((e['end']-e['start'])*m.speed+EPS>=distance(a,b,s.metric),f'{mid}: velocidad de animación')
            else:check(distance(a,b)<EPS,f'{mid}: movimiento durante servicio')
            previous=b
            last=e['end']
    if s.mode=='fleet': check(plan['makespan']<=s.deadline+EPS,'Plazo objetivo incumplido')
    return errors
