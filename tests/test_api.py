import time
from fastapi.testclient import TestClient
from backend.app import app

def test_api_job_and_validation():
    with TestClient(app) as c:
        assert c.get('/api/health').json()['ok']
        s=c.get('/api/scenario/demo?count=2&seed=8').json()
        s['time_limit']=2
        assert c.post('/api/scenario/validate',json=s).status_code==200
        response=c.post('/api/solve',json=s)
        assert response.status_code==202
        jid=response.json()['id']
        for _ in range(100):
            j=c.get('/api/jobs/'+jid).json()
            if j['state'] in ('done','error'):break
            time.sleep(.05)
        assert j['state']=='done',j
        assert j['result']['verification']['valid']
        s['durations']['drill']=-1
        assert c.post('/api/solve',json=s).status_code==422
        assert c.get('/api/jobs/not-real').status_code==404
