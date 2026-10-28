import pytest
from fastapi.testclient import TestClient
from backend.remote import create_app

TOKEN = 'synthetic-test-only-token-at-least-32-characters'

def test_private_entry_covers_ui_and_api():
    with TestClient(create_app(TOKEN), base_url='https://litio.test') as c:
        assert c.get('/').status_code == 401
        assert c.get('/api/health').status_code == 401
        assert c.get('/access/incorrect').status_code == 401
        login = c.get('/access/'+TOKEN, follow_redirects=False)
        assert login.status_code == 303
        assert 'HttpOnly' in login.headers['set-cookie']
        assert 'Secure' in login.headers['set-cookie']
        assert login.headers['referrer-policy'] == 'no-referrer'
        assert c.get('/api/health').json()['ok']
        assert c.get('/').status_code == 200

def test_bearer_for_server_health_checks():
    with TestClient(create_app(TOKEN)) as c:
        assert c.get('/api/health', headers={'Authorization':'Bearer '+TOKEN}).status_code == 200
        assert c.get('/api/health', headers={'Authorization':'Bearer bad'}).status_code == 401

def test_refuse_weak_entry_secret():
    with pytest.raises(RuntimeError):
        create_app('short')
