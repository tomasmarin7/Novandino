"""Joint scheduling/routing/coverage CP-SAT model; see docs/MODELO.md.

The certificate is for the finite candidate set and 0.1-hour discretization only.
"""
from __future__ import annotations
from collections import defaultdict
from itertools import combinations
import math
import threading
import time
from ortools.sat.python import cp_model
from .schema import Scenario, Point, PHASES, LABELS, KINDS
from .geometry import TICKS, ticks, travel, distance, anchors, candidates, coordinates, path

def groups(indices):
    result = []
    for i in sorted(indices):
        if result and result[-1][-1]+1 == i:
            result[-1].append(i)
        else:
            result.append([i])
    return result

class Progress(cp_model.CpSolverSolutionCallback):
    def __init__(self, cmax, notify, cancelled):
        super().__init__()
        self.cmax, self.notify, self.cancelled = cmax, notify, cancelled
        self.count = 0

    def on_solution_callback(self):
        self.count += 1
        self.notify({'stage':'solving', 'message':'Mejorando el plan factible', 'solutions':self.count,
                     'best_hours':self.value(self.cmax)/TICKS, 'elapsed':self.wall_time})
        if self.cancelled.is_set():
            self.stop_search()

def solve(s: Scenario, notify=lambda _: None, cancelled=None):
    cancelled = cancelled or threading.Event()
    begin = time.monotonic()
    notify({'stage':'building','message':'Construyendo restricciones de rutas, fases y capacidades'})
    model = cp_model.CpModel()
    n = len(s.wells)
    machines = {m.id:m for m in s.machines}
    by_kind = {k:[m for m in s.machines if m.kind==k] for k in KINDS}
    durations = [[ticks(w.durations.get(p,s.durations[p])) for p in PHASES] for w in s.wells]
    diagonal = s.width+s.height
    margin = max(ticks(2*diagonal/m.speed + m.setup+m.disconnect+s.refill_time+s.delivery_time+1) for m in s.machines)
    horizon = sum(map(sum,durations)) + (n+2)*margin + max(ticks(m.available) for m in s.machines)
    if horizon > 100_000_000:
        raise ValueError('Escenario demasiado extenso: revisa velocidades, área y duraciones.')
    starts, ends = {}, {}
    for i in range(n):
        for e in range(7):
            starts[i,e] = model.new_int_var(0,horizon,f'b_{i}_{e}')
            ends[i,e] = model.new_int_var(0,horizon,f'f_{i}_{e}')
            model.add(ends[i,e] == starts[i,e]+durations[i][e])
            if e:
                # Construction and testing are two uninterrupted work blocks.
                if e == 3:
                    model.add(starts[i,e] >= ends[i,e-1])
                else:
                    model.add(starts[i,e] == ends[i,e-1])
    used = {m.id:model.new_bool_var('used_'+m.id) for m in s.machines}
    bookings = defaultdict(list)
    alternatives = defaultdict(list)
    counter = 0

    def book(m, i, first, last, pos, demand=1, water=False):
        nonlocal counter
        counter += 1
        chosen = model.new_bool_var(f'x_{counter}')
        if water:
            a = model.new_int_var(0,horizon,f'delivery_{counter}')
            b = a+ticks(s.delivery_time)
            model.add(b <= starts[i,1]).only_enforce_if(chosen)
            work_start, work_end = a,b
        else:
            work_start,work_end = starts[i,first],ends[i,last]
            a = work_start-ticks(m.setup)
            b = work_end+ticks(m.disconnect)
        size = model.new_int_var(0,horizon,f'size_{counter}')
        interval = model.new_optional_interval_var(a,size,b,chosen,f'iv_{counter}')
        model.add(a >= ticks(m.available)+travel(m.initial,pos,m,s)).only_enforce_if(chosen)
        model.add(b <= horizon).only_enforce_if(chosen)
        model.add_implication(chosen,used[m.id])
        item = dict(machine=m.id,well=i,first=first,last=last,pos=pos,p=chosen,start=a,end=b,
                    work_start=work_start,work_end=work_end,interval=interval,demand=demand,water=water)
        bookings[m.id].append(item)
        alternatives[(i,'water' if water else m.kind,first,last)].append(item)
        return item

    for i,w in enumerate(s.wells):
        for m in by_kind['rig']:
            book(m,i,0,2,w)
        demand = s.water_demand if w.water_demand is None else w.water_demand
        if demand:
            for m in by_kind['water']:
                if m.capacity >= demand:
                    book(m,i,1,1,w,demand,water=True)

    pools = {m.id:anchors(s,m) for m in s.machines if m.kind not in ('rig','water')}
    for req in s.requirements:
        for indices in groups([PHASES.index(p) for p in req.phases]):
            for i,w in enumerate(s.wells):
                for m in by_kind[req.kind]:
                    if m.capacity < req.demand:
                        continue
                    for pos in candidates(s,m,w,pools[m.id]):
                        book(m,i,indices[0],indices[-1],pos,req.demand)

    for options in alternatives.values():
        model.add_exactly_one(o['p'] for o in options)

    for m in s.machines:
        items = bookings[m.id]
        if not items:
            model.add(used[m.id]==0)
            continue
        model.add(used[m.id] <= sum(o['p'] for o in items))
        ivs = [o['interval'] for o in items]
        if m.kind in ('rig','water','test'):
            model.add_no_overlap(ivs)
        else:
            model.add_cumulative(ivs,[1]*len(ivs),m.simultaneous)
            # Quantization is conservative: round demands up and capacity down.
            model.add_cumulative(ivs,[math.ceil(o['demand']*100-1e-8) for o in items],math.floor(m.capacity*100+1e-8))
        for a,b in combinations(items,2):
            if (a['well'],a['first'],a['last']) == (b['well'],b['first'],b['last']):
                continue  # alternatives of the very same service
            same = distance(a['pos'],b['pos']) < 1e-5
            if same and m.kind not in ('rig','water','test'):
                continue
            before = model.new_bool_var(f'order_{m.id}_{a["p"].index}_{b["p"].index}')
            if m.kind=='water':
                ab = travel(a['pos'],s.depot,m,s)+ticks(s.refill_time)+travel(s.depot,b['pos'],m,s)
                ba = travel(b['pos'],s.depot,m,s)+ticks(s.refill_time)+travel(s.depot,a['pos'],m,s)
            else:
                ab = travel(a['pos'],b['pos'],m,s)
                ba = travel(b['pos'],a['pos'],m,s)
            model.add(b['start'] >= a['end']+ab).only_enforce_if([a['p'],b['p'],before])
            model.add(a['start'] >= b['end']+ba).only_enforce_if([a['p'],b['p'],before.Not()])

    cmax = model.new_int_var(0,horizon,'makespan')
    # Include final auxiliary disconnection, not return to depot.
    for i in range(n):
        model.add(cmax >= ends[i,6])
    for items in bookings.values():
        for o in items:
            model.add(cmax >= o['end']).only_enforce_if(o['p'])
    if s.mode=='fleet':
        model.add(cmax <= math.floor(s.deadline*TICKS+1e-8))
        model.minimize(sum(used.values())*(horizon+1)+cmax)
    else:
        model.minimize(cmax*(len(s.machines)+1)+sum(used.values()))

    # Feasible conservative serial seed: useful even before optimization improves it.
    now = max(ticks(m.available) for m in s.machines)
    chosen_seed = []
    for i in range(n):
        now += margin
        at = now
        for e in range(7):
            model.add_hint(starts[i,e],at)
            model.add_hint(ends[i,e],at+durations[i][e])
            at += durations[i][e]
        for key, options in alternatives.items():
            if key[0] != i:
                continue
            selected = options[0]  # well itself, first compatible machine
            chosen_seed.append(selected)
            for o in options:
                model.add_hint(o['p'],int(o is selected))
            if selected['water']:
                model.add_hint(selected['start'],now-ticks(s.delivery_time))
        now = at
    for mid,var in used.items():
        model.add_hint(var,int(any(o['machine']==mid for o in chosen_seed)))
    model.add_hint(cmax,now)
    validation = model.validate()
    if validation:
        raise ValueError('Modelo inválido: '+validation)
    if cancelled.is_set():
        return {'status':'CANCELLED','message':'Cálculo cancelado.'}
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = s.time_limit
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = s.seed
    callback = Progress(cmax,notify,cancelled)
    done = threading.Event()
    def monitor():
        while not done.wait(.1):
            if cancelled.is_set():
                solver.stop_search()
                return
    watcher = threading.Thread(target=monitor,daemon=True)
    watcher.start()
    notify({'stage':'solving','message':'Buscando un plan coordinado','variables':len(model.proto.variables),'constraints':len(model.proto.constraints)})
    try:
        status = solver.solve(model,callback)
    finally:
        done.set()
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return {'status':'CANCELLED' if cancelled.is_set() else solver.status_name(status),
            'message': 'No existe un plan dentro del plazo, flota y posiciones candidatas configurados.' if status==cp_model.INFEASIBLE else 'No se encontró un plan en el tiempo disponible. Aumenta el tiempo de cálculo o reduce el caso.',
            'solve_seconds':round(time.monotonic()-begin,3)}
    notify({'stage':'verifying','message':'Verificando movimientos, servicios e inventarios'})
    output = extract(s,solver,starts,ends,bookings,cmax)
    obj,bound = solver.objective_value,solver.best_objective_bound
    output.update(status=solver.status_name(status), cancelled=cancelled.is_set(),
        solve_seconds=round(time.monotonic()-begin,3), solutions=callback.count,
        objective_value=obj, objective_bound=bound, relative_gap=max(0,(obj-bound)/max(1,abs(obj))),
        proof_scope='Posiciones candidatas sin cuadrícula; tiempo discretizado a 0,1 h. No certifica el óptimo del espacio continuo.',
        candidate_count=sum(len(v) for v in pools.values()), model_variables=len(model.proto.variables),
        objective='Menor número total de unidades dentro del plazo; desempate por duración.' if s.mode=='fleet' else 'Menor plazo total; desempate por número de unidades utilizadas.',
        assumptions=['Geometría sintética: no representa caminos ni topografía real.',
            'Una entrega de agua antes de perforar; tanque fijo por pozo. Sin reabastecimiento durante la perforación.',
            'Construcción y ensayo son bloques sin interrupciones; puede haber espera entre ambos.',
            'Capacidades reservadas también durante conexión y desconexión.',
            'La flota recomendada usa los máximos disponibles y minimiza unidades, no costo monetario.'])
    from .verify import verify
    errors = verify(s,output)
    if errors:
        raise RuntimeError('El verificador rechazó el plan: '+'; '.join(errors[:6]))
    output['verification'] = {'valid':True,'checks':['precedencia','duraciones','asignación','cobertura','capacidad','continuidad espacial','agua','plazo']}
    return output

def extract(s,solver,starts,ends,bookings,cmax):
    selected = []
    for mid,items in bookings.items():
        for o in items:
            if solver.value(o['p']):
                selected.append({'machine':mid,'well':s.wells[o['well']].id,'first':o['first'],'last':o['last'],
                    'position':coordinates(o['pos']),'start':solver.value(o['start'])/TICKS,
                    'end':solver.value(o['end'])/TICKS,'work_start':solver.value(o['work_start'])/TICKS,
                    'work_end':solver.value(o['work_end'])/TICKS,'demand':o['demand'],'water':o['water']})
    well_plans = []
    for i,w in enumerate(s.wells):
        phases=[]
        for e,p in enumerate(PHASES):
            phases.append({'id':p,'label':LABELS[e],'start':solver.value(starts[i,e])/TICKS,'end':solver.value(ends[i,e])/TICKS,
                'machines':sorted({o['machine'] for o in selected if o['well']==w.id and not o['water'] and o['first']<=e<=o['last']})})
        well_plans.append({'id':w.id,**coordinates(w),'phases':phases,'completion':phases[-1]['end'],
            'water_demand':s.water_demand if w.water_demand is None else w.water_demand})
    tracks=[]
    for m in s.machines:
        own=sorted([o for o in selected if o['machine']==m.id],key=lambda o:(o['start'],o['end']))
        stops=[]
        for o in own:
            if stops and stops[-1]['position']==o['position'] and m.kind!='water':
                stops[-1]['end']=max(stops[-1]['end'],o['end'])
                stops[-1]['bookings'].append(o)
            else:
                stops.append({'position':o['position'],'start':o['start'],'end':o['end'],'bookings':[o]})
        events=[]
        pos=m.initial
        at=m.available
        def event(kind,start,end,a,b=None,wells=None,label=None):
            if end-start <= 1e-7:
                return
            events.append({'state':kind,'start':round(start,5),'end':round(end,5),
                'from':coordinates(a),'to':coordinates(b or a),'path':path(a,b or a,s.metric),
                'wells':wells or [],'label':label or kind})
        if m.available:
            event('unavailable',0,m.available,pos,label='No disponible')
        for idx,stop in enumerate(stops):
            dest=Point(**stop['position'])
            if m.kind=='water' and idx:
                back=travel(pos,s.depot,m,s)/TICKS
                event('travel',at,at+back,pos,s.depot,label='Regreso a recarga')
                at+=back
                pos=s.depot
                event('refill',at,at+ticks(s.refill_time)/TICKS,pos,label='Recarga de agua')
                at+=ticks(s.refill_time)/TICKS
            duration=travel(pos,dest,m,s)/TICKS
            depart=stop['start']-duration
            event('idle',at,depart,pos,label='Disponible / espera')
            event('travel',depart,stop['start'],pos,dest,label='Traslado')
            boundaries={stop['start'],stop['end']}
            for o in stop['bookings']:
                boundaries.update([o['start'],o['end'],o['work_start'],o['work_end']])
                wp=next(w for w in well_plans if w['id']==o['well'])
                for phase in wp['phases']:
                    if o['work_start']<phase['start']<o['work_end']: boundaries.add(phase['start'])
                    if o['work_start']<phase['end']<o['work_end']: boundaries.add(phase['end'])
            bs=sorted(boundaries)
            for a,b in zip(bs,bs[1:]):
                mid=(a+b)/2
                active=[o for o in stop['bookings'] if o['start']<=mid<o['end']]
                work=[o for o in active if o['work_start']<=mid<o['work_end']]
                state='service' if work else ('setup' if active else 'idle')
                label='Servicio' if work else ('Conexión / desconexión' if active else 'Disponible / espera')
                if m.kind=='water': state,label='delivery','Entrega de agua'
                elif m.kind in ('rig','test') and work:
                    wp=next(w for w in well_plans if w['id']==work[0]['well'])
                    phase=next((p for p in wp['phases'] if p['start']<=mid<p['end']),None)
                    if phase:
                        label=phase['label']
                        if phase['id']=='recovery':state='reserved'
                event(state,a,b,dest,wells=sorted({o['well'] for o in active}),label=label)
            pos=dest
            at=stop['end']
        event('idle',at,solver.value(cmax)/TICKS,pos,label='Disponible / fin de trabajo')
        tracks.append({'id':m.id,'kind':m.kind,'used':bool(own),'initial':coordinates(m.initial),
            'radius':m.radius,'simultaneous':m.simultaneous,'capacity':m.capacity,'events':events,
            'travel_hours':round(sum(e['end']-e['start'] for e in events if e['state']=='travel'),3),
            'service_hours':round(sum(e['end']-e['start'] for e in events if e['state'] in ('service','reserved','delivery','setup')),3)})
    fleet={k:sum(t['used'] and t['kind']==k for t in tracks) for k in KINDS}
    return {'makespan':solver.value(cmax)/TICKS,'wells':well_plans,'machines':tracks,'bookings':selected,
        'fleet_used':fleet,'fleet_available':{k:sum(m.kind==k for m in s.machines) for k in KINDS},
        'scenario':s.model_dump(),'construction_end':max(w['phases'][2]['end'] for w in well_plans)}
