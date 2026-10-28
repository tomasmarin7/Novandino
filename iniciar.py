"""Portable local launcher: prepare an isolated runtime, then serve the built UI."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent

def local_health(port: int) -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
            data = json.load(response)
        return data.get('ok') is True and data.get('engine') == 'OR-Tools CP-SAT'
    except (OSError, ValueError, urllib.error.URLError):
        return False

def choose_port(first: int) -> tuple[int, bool]:
    if not 1024 <= first <= 65525:
        raise ValueError('LITIO_PORT debe estar entre 1024 y 65525.')
    for port in range(first, first+10):
        if local_health(port):
            return port, True
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port, False
            except OSError:
                continue
    raise RuntimeError('Los diez puertos probados están ocupados. Cambia LITIO_PORT.')

def prepare() -> Path:
    if sys.version_info < (3, 11):
        raise RuntimeError('Se necesita Python 3.11 o posterior; se recomienda 3.12.')
    if not (ROOT/'frontend/dist/index.html').is_file():
        raise RuntimeError('Falta la página compilada. Ejecuta npm ci y npm run build en frontend.')
    runtime = ROOT/'.venv'
    executable = runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not executable.exists():
        print('Preparando el entorno Python dentro del proyecto…', flush=True)
        venv.EnvBuilder(with_pip=True).create(runtime)
    requirements = ROOT/'requirements-runtime.txt'
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = runtime/'.litio-runtime'
    probe = subprocess.run([str(executable), '-c', 'import fastapi, uvicorn, ortools, pydantic'], capture_output=True)
    if probe.returncode or not stamp.exists() or stamp.read_text() != fingerprint:
        print('Instalando dependencias locales. La primera ejecución necesita Internet…', flush=True)
        subprocess.run([str(executable), '-m', 'pip', 'install', '-r', str(requirements)], check=True, cwd=ROOT)
        stamp.write_text(fingerprint)
    return executable

def main() -> int:
    executable = prepare()
    if '--prepare-only' in sys.argv:
        print('Entorno listo. No se inició el servidor.')
        return 0
    port, running = choose_port(int(os.environ.get('LITIO_PORT', '8000')))
    url = f'http://127.0.0.1:{port}'
    print(f'\nLitio Planner: {url}\nMantén esta ventana abierta. Para detenerlo pulsa Ctrl+C.\n', flush=True)
    browser_enabled = os.environ.get('LITIO_NO_BROWSER') != '1'
    if running:
        print('El simulador ya estaba ejecutándose en este equipo.')
        if browser_enabled:
            webbrowser.open(url)
        return 0
    process = subprocess.Popen([str(executable), '-m', 'uvicorn', 'backend.app:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT)
    stop = threading.Event()
    def open_when_ready():
        deadline = time.monotonic()+45
        while not stop.wait(.3) and time.monotonic()<deadline and process.poll() is None:
            if local_health(port):
                if browser_enabled:
                    webbrowser.open(url)
                return
    threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return 0
    finally:
        stop.set()

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f'\nError: {error}', file=sys.stderr)
        raise SystemExit(1)
