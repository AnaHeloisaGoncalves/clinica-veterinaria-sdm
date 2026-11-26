"""Executa os testes em MySQL descartável e governo SQLite separado.

Requer usuário de testes com CREATE/DROP DATABASE. Nunca usa a base da apresentação.
No Mac configurado: .venv/bin/python -m scripts.testes_isolados
"""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import httpx
import mysql.connector
from dotenv import load_dotenv


def porta():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    load_dotenv()
    root = Path(__file__).resolve().parent.parent
    nome = 'clinica_test_' + secrets.token_hex(6)
    pasta = root / '.local-run' / nome
    pasta.mkdir(parents=True)
    user = os.getenv('TEST_DB_ADMIN_USER', 'root')
    password = os.getenv('TEST_DB_ADMIN_PASSWORD', '')
    db = mysql.connector.connect(host=os.getenv('DB_HOST', '127.0.0.1'),
                                 port=int(os.getenv('DB_PORT', '3306')), user=user, password=password)
    processos = []
    logs = []
    try:
        with db.cursor() as cur:
            cur.execute(f'CREATE DATABASE `{nome}`')
            cur.execute(f'USE `{nome}`')
            sql = (root / 'database/banco1.sql').read_text()
            for stmt in sql.split(';'):
                if stmt.strip() and not stmt.strip().startswith(('CREATE DATABASE', 'USE ')):
                    cur.execute(stmt)
        db.commit()
        api_port, gov_port = porta(), porta()
        env = dict(os.environ, DB_NAME=nome, DB_USER=user, DB_PASSWORD=password,
                   DEMO_PASSWORD=secrets.token_urlsafe(24), JWT_SECRET=secrets.token_urlsafe(48),
                   GOVERNO_API_KEY=secrets.token_urlsafe(40), GOVERNO_DB=str(pasta / 'governo.sqlite3'),
                   GOVERNO_URL=f'http://127.0.0.1:{gov_port}',
                   TEST_API_URL=f'http://127.0.0.1:{api_port}', TEST_ARTIFACT_DIR=str(pasta), ALLOW_TEST_DATA='1')
        subprocess.run([sys.executable, '-m', 'scripts.demo'], cwd=root, env=env, check=True)
        for module, port in [('api_governo.main:app', gov_port), ('api_clinica.main:app', api_port)]:
            log = (pasta / (module.split('.')[0] + '.log')).open('w')
            logs.append(log)
            processos.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', module, '--host', '127.0.0.1', '--port', str(port)], cwd=root, env=env, stdout=log, stderr=log))
            for _ in range(100):
                try:
                    if httpx.get(f'http://127.0.0.1:{port}/health', timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.1)
            else:
                raise RuntimeError(f'Serviço não iniciou; consulte {pasta}')
        resultado = subprocess.run([sys.executable, '-m', 'unittest', 'tests.entrega2', 'tests.entrega3',
                                    'tests.entrega4', 'tests.requisitos_a3', 'tests.edicao_animal_web',
                                    'tests.gestao_web', '-v'], cwd=root, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (pasta / 'resultado.txt').write_text(resultado.stdout)
        print(resultado.stdout)
        print(f'Evidências: {pasta}')
        return resultado.returncode
    finally:
        for processo in processos:
            processo.terminate()
        for processo in processos:
            try:
                processo.wait(timeout=10)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait()
        for log in logs:
            log.close()
        with db.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS `{nome}`')
        db.close()


if __name__ == '__main__':
    raise SystemExit(main())
