"""Demonstração visual do reenvio manual. Use bancos descartáveis."""
import os
import secrets
from datetime import date, timedelta
from pathlib import Path

import httpx
from playwright.sync_api import expect, sync_playwright

from tests.entrega2 import cpf

if os.getenv("ALLOW_TEST_DATA") != "1":
    raise SystemExit("Use ALLOW_TEST_DATA=1 com bancos descartáveis.")
base = os.getenv("TEST_API_URL", "http://127.0.0.1:8000")
gov = os.getenv("GOVERNO_URL", "http://127.0.0.1:8001") + "/api/governo"
headers = {"X-API-Key": os.environ["GOVERNO_API_KEY"]}
run = secrets.token_hex(5)
out = Path("docs/evidencias")
out.mkdir(exist_ok=True, parents=True)
with httpx.Client(base_url=base, timeout=15) as api:
    response = api.post("/login", json={"email": "demo@example.test", "senha": os.environ["DEMO_PASSWORD"]})
    response.raise_for_status()
    api.headers["Authorization"] = "Bearer " + response.json()["token_acesso"]
    tutor = api.post("/clinica/tutores", json={
        "nome_completo": "Tutor Demonstração " + run, "cpf": cpf(600000000 + secrets.randbelow(99999999)),
        "email": run + "@example.test", "data_nascimento": "1990-01-01",
        "endereco": {"cep": "01001000", "logradouro": "Praça da Sé", "numero": "1", "bairro": "Sé",
                     "cidade": "São Paulo", "uf": "SP"}})
    tutor.raise_for_status()
    especie = api.get("/especies").json()[0]["id"]
    nome = "Bento Integração " + run
    animal = api.post("/animais", json={"nome": nome, "idade_estimada_meses": 12, "sexo": "M",
        "cor": "preto", "peso_atual_kg": 10, "tutor_id": tutor.json()["id"],
        "especie_id": especie, "codigo_rfid": "WEB-" + run})
    animal.raise_for_status()
    httpx.put(gov + "/simulacao", headers=headers, json={"indisponivel": True}).raise_for_status()
    try:
        vacina = api.post("/clinica/vacinas", json={"animal_id": animal.json()["id"], "nome_vacina": "Antirrábica demo",
            "antirrabica": True, "fabricante": "Fictício", "numero_lote": "DEMO-4", "via_aplicacao": "SC",
            "dose_etapa": "Reforço", "validade_lote": str(date.today() + timedelta(days=365)),
            "data_aplicacao": str(date.today()), "situacao": "APLICADA"})
        vacina.raise_for_status()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base)
            page.get_by_label("E-mail", exact=True).fill("demo@example.test")
            page.get_by_label("Senha", exact=True).fill(os.environ["DEMO_PASSWORD"])
            page.get_by_role("button", name="Entrar", exact=True).click()
            page.get_by_role("button", name="Animais", exact=True).click()
            page.get_by_role("button", name="Ficha de " + nome, exact=True).click()
            expect(page.get_by_text("VACINA_ANTIRRABICA · PENDENTE", exact=False)).to_be_visible()
            page.screenshot(path=str(out / "m4-pendente.png"), full_page=True)
            httpx.put(gov + "/simulacao", headers=headers, json={"indisponivel": False}).raise_for_status()
            page.get_by_role("button", name="Reenviar comunicação", exact=True).click()
            expect(page.get_by_text("VACINA_ANTIRRABICA · CONFIRMADA", exact=False)).to_be_visible()
            page.screenshot(path=str(out / "m4-confirmada.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not errors, errors
            browser.close()
    finally:
        httpx.put(gov + "/simulacao", headers=headers, json={"indisponivel": False})
        api.post("/logout")
print("OK: vacina salva durante indisponibilidade; ficha pendente, reenvio manual e protocolo confirmado; layout celular.")
