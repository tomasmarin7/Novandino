"""Local API and production React static host. Start from the project root."""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .schema import Scenario, make_demo
from .optimizer import solve

app=FastAPI(title='Litio Planner',version='0.1.0',description='Simulador local de rutas y fases sincronizadas.')
pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='litio-solver')
jobs={}
lock=threading.Lock()

@app.get('/api/health')
def health(): return {'ok':True,'engine':'OR-Tools CP-SAT','version':'0.1.0'}

@app.get('/api/scenario/demo')
def demo(count:int=Query(6,ge=1,le=16),seed:int=Query(42,ge=0,le=2147483647)):
    return make_demo(count,seed)

@app.post('/api/scenario/validate')
def validate(s:Scenario): return s

@app.post('/api/solve',status_code=202)
def start(s:Scenario):
    with lock:
        if sum(j['state'] in ('queued','running') for j in jobs.values())>=3:
            raise HTTPException(429,'Hay tres cálculos pendientes. Cancela uno o espera.')
        for key in list(jobs):
            if len(jobs)>20 and jobs[key]['state'] not in ('queued','running'): del jobs[key]
        jid=uuid.uuid4().hex
        jobs[jid]={'id':jid,'state':'queued','progress':{'stage':'queued','message':'En cola'},'result':None,'error':None,
                   'cancel':threading.Event(),'created':time.time()}
    def notify(progress):
        with lock:jobs[jid]['progress']={**jobs[jid]['progress'],**progress}
    def run():
        with lock:
            j=jobs[jid]
            if j['cancel'].is_set():
                j.update(state='cancelled')
                return
            j['state']='running'
        try:
            result=solve(s,notify,j['cancel'])
            with lock:j.update(state='done',result=result)
        except Exception as exc:
            with lock:j.update(state='error',error=str(exc))
    pool.submit(run)
    return {'id':jid}

@app.get('/api/jobs/{jid}')
def job(jid:str):
    with lock:
        if jid not in jobs:raise HTTPException(404,'Cálculo no encontrado.')
        return {k:v for k,v in jobs[jid].items() if k!='cancel'}

@app.delete('/api/jobs/{jid}')
def cancel(jid:str):
    with lock:
        if jid not in jobs:raise HTTPException(404,'Cálculo no encontrado.')
        jobs[jid]['cancel'].set()
    return {'requested':True}

DIST=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if (DIST/'assets').exists(): app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')

@app.get('/')
def index():
    if not (DIST/'index.html').exists():
        raise HTTPException(503,'Primero ejecuta npm run build en frontend, o usa Vite en el puerto 5173.')
    return FileResponse(DIST/'index.html')
