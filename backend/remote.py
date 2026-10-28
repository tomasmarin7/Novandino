"""Authenticated temporary remote entrypoint; local app remains unchanged.

Run uvicorn backend.remote:create_app --factory with LITIO_ACCESS_TOKEN set.
The /access/<token> link sets an HttpOnly HTTPS cookie and redirects to /.
Disable access logs so the entry link is not recorded in server logs.
"""
import os
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from .app import app as local_app

def create_app(token: str | None = None):
    secret = token or os.environ.get('LITIO_ACCESS_TOKEN', '')
    if len(secret) < 32:
        raise RuntimeError('LITIO_ACCESS_TOKEN debe contener al menos 32 caracteres aleatorios.')
    remote = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @remote.middleware('http')
    async def require_access(request: Request, call_next):
        path = request.url.path
        if path.startswith('/access/'):
            supplied = path[len('/access/'):]
            if secrets.compare_digest(supplied.encode(), secret.encode()):
                response = RedirectResponse('/', status_code=303)
                response.set_cookie('litio_access', secret, max_age=86400,
                                    httponly=True, secure=True, samesite='lax', path='/')
            else:
                response = HTMLResponse('Enlace de acceso inválido.', status_code=401)
        else:
            cookie = request.cookies.get('litio_access', '')
            authorization = request.headers.get('authorization', '')
            supplied = authorization[7:] if authorization.startswith('Bearer ') else cookie
            if not secrets.compare_digest(supplied.encode(), secret.encode()):
                response = HTMLResponse('''<!doctype html><html lang="es"><meta charset="utf-8">
                    <meta name="viewport" content="width=device-width,initial-scale=1">
                    <title>Litio · Acceso privado</title>
                    <body style="margin:0;background:#000;color:#ddd;font:16px Arial;display:grid;place-items:center;min-height:100vh">
                    <main style="padding:32px;max-width:480px"><h1>Litio / acceso privado</h1>
                    <p>Abre el enlace de acceso completo que recibiste en el chat.</p></main></body></html>''', status_code=401)
            else:
                response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    remote.mount('/', local_app)
    return remote
