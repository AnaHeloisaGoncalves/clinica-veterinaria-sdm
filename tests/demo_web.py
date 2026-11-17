"""Demonstração no Chromium com API e MySQL reais; grava somente dados fictícios."""
import os
import secrets
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect
from tests.entrega2 import cpf

load_dotenv()
if os.getenv("ALLOW_TEST_DATA") != "1":
    raise SystemExit("Defina ALLOW_TEST_DATA=1 e use um banco de testes.")
destino = Path("docs/evidencias")
destino.mkdir(parents=True, exist_ok=True)
run = secrets.token_hex(3)
nome_tutor = "Tutor Demo " + run
nome_animal = "Bento " + run
rfid = "DEMO-" + run
erros = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1366, "height": 900})
    page.on("pageerror", lambda error: erros.append(str(error)))
    page.goto(os.getenv("TEST_API_URL", "http://127.0.0.1:8000"))
    page.get_by_label("E-mail", exact=True).fill("demo@example.test")
    page.get_by_label("Senha", exact=True).fill(os.environ["DEMO_PASSWORD"])
    page.get_by_role("button", name="Entrar", exact=True).click()
    expect(page.get_by_role("heading", name="Painel da clínica")).to_be_visible()
    page.screenshot(path=str(destino / "01-painel.png"))
    page.get_by_role("button", name="Tutores", exact=True).click()
    page.get_by_label("CEP", exact=True).fill("00000000")
    page.get_by_role("button", name="Consultar CEP").click()
    expect(page.get_by_role("status")).to_contain_text("CEP não encontrado", timeout=15000)
    expect(page.get_by_label("Logradouro", exact=True)).to_be_editable()
    page.screenshot(path=str(destino / "02-cep-inexistente.png"))
    page.get_by_label("CEP", exact=True).fill("01001-000")
    page.get_by_role("button", name="Consultar CEP").click()
    expect(page.get_by_label("Logradouro", exact=True)).to_have_value("Praça da Sé", timeout=15000)
    page.get_by_label("Nome completo", exact=True).fill(nome_tutor)
    page.get_by_label("CPF", exact=True).fill(cpf(500000000 + secrets.randbelow(99999999)))
    page.get_by_label("Nascimento", exact=True).fill("1995-01-01")
    page.get_by_label("E-mail", exact=True).fill(run + "@example.test")
    page.get_by_label("Número", exact=True).fill("10")
    page.get_by_label("Complemento", exact=True).fill("Demonstração")
    page.screenshot(path=str(destino / "03-tutor-cep.png"), full_page=True)
    page.get_by_role("button", name="Cadastrar tutor", exact=True).click()
    expect(page.get_by_role("status")).to_have_text("Tutor cadastrado com sucesso.")
    page.get_by_role("button", name="Animais", exact=True).click()

    def preencher_animal():
        page.get_by_label("Nome", exact=True).fill(nome_animal)
        page.get_by_label("Código RFID", exact=True).fill(rfid)
        page.get_by_role("combobox", name="Tutor", exact=True).select_option(label=nome_tutor)
        page.get_by_role("combobox", name="Espécie", exact=True).select_option(label="Cão")
        page.get_by_role("combobox", name="Raça (opcional)", exact=True).select_option(label="Labrador")
        page.get_by_role("combobox", name="Espécie", exact=True).select_option(label="Gato")
        expect(page.get_by_role("combobox", name="Raça (opcional)", exact=True)).to_have_value("")
        page.get_by_label("Sexo", exact=True).fill("M")
        page.get_by_label("Cor", exact=True).fill("Preto")
        page.get_by_label("Peso (kg)", exact=True).fill("4.5")
        page.get_by_label("Idade estimada (meses)", exact=True).fill("12")

    preencher_animal()
    page.get_by_role("button", name="Cadastrar animal", exact=True).click()
    expect(page.get_by_role("status")).to_have_text("Animal cadastrado e RFID vinculado.")
    preencher_animal()
    page.get_by_role("button", name="Cadastrar animal", exact=True).click()
    expect(page.get_by_role("status")).to_contain_text("RFID já está em uso")
    page.screenshot(path=str(destino / "04-rfid-duplicado.png"), full_page=True)
    page.get_by_role("button", name="Atendimento", exact=True).click()
    consulta = page.locator("#consulta")
    consulta.get_by_role("combobox", name="Animal", exact=True).select_option(label=nome_animal)
    consulta.get_by_label("Data e hora da consulta").fill(str(date.today()) + "T10:00")
    for label, value in {"Motivo": "Avaliação de rotina", "Anamnese": "Animal ativo",
                         "Sintomas": "Sem queixas", "Diagnóstico": "Avaliação demonstrativa",
                         "Tratamento": "Acompanhamento", "Prescrição de medicamentos": "Sem prescrição",
                         "Observações": "Dados fictícios para apresentação"}.items():
        consulta.get_by_label(label, exact=True).fill(value)
    consulta.get_by_label("Peso registrado (kg)").fill("4.5")
    consulta.get_by_label("Temperatura (°C)").fill("38.5")
    consulta.get_by_role("button", name="Registrar consulta").click()
    expect(page.get_by_role("status")).to_contain_text("Consulta registrada")
    vacina = page.locator("#vacina")
    vacina.get_by_role("combobox", name="Animal", exact=True).select_option(label=nome_animal)
    vacina.get_by_label("Nome da vacina").fill("Antirrábica demo")
    vacina.get_by_label("Vacina antirrábica", exact=True).check()
    vacina.get_by_label("Fabricante", exact=True).fill("Fabricante fictício")
    vacina.get_by_label("Número do lote").fill("DEMO-001")
    vacina.get_by_label("Via de aplicação").fill("SC")
    vacina.get_by_label("Dose / etapa").fill("1")
    vacina.get_by_label("Data de aplicação", exact=True).fill(str(date.today()))
    vacina.get_by_label("Próxima dose (opcional)").fill(str(date.today() + timedelta(days=365)))
    vacina.get_by_role("button", name="Registrar vacina").click()
    expect(page.get_by_role("status")).to_contain_text("Vacina registrada")
    # Confirma o caso antes quebrado: próxima dose em branco.
    vacina.get_by_role("combobox", name="Animal", exact=True).select_option(label=nome_animal)
    vacina.get_by_label("Nome da vacina").fill("Vacina demo sem próxima dose")
    vacina.get_by_label("Data de aplicação", exact=True).fill(str(date.today()))
    vacina.get_by_role("button", name="Registrar vacina").click()
    expect(page.get_by_role("status")).to_contain_text("Vacina registrada")
    page.get_by_role("button", name="Animais", exact=True).click()
    page.get_by_role("button", name="Ficha de " + nome_animal, exact=True).click()
    expect(page.get_by_role("heading", name="Histórico de consultas")).to_be_visible()
    expect(page.get_by_text("Avaliação demonstrativa", exact=True)).to_be_visible()
    expect(page.get_by_text("Antirrábica: Sim", exact=True)).to_be_visible()
    page.screenshot(path=str(destino / "05-historicos.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(destino / "06-celular.png"), full_page=True)
    page.get_by_role("button", name="Sair", exact=True).click()
    expect(page.get_by_role("heading", name="Acesso do veterinário")).to_be_visible()
    page.get_by_label("E-mail", exact=True).fill("demo@example.test")
    page.get_by_label("Senha", exact=True).fill(os.environ["DEMO_PASSWORD"])
    page.get_by_role("button", name="Entrar", exact=True).click()
    expect(page.get_by_role("heading", name="Painel da clínica")).to_be_visible()
    # Simula a rejeição de uma sessão expirada para testar a reação da interface.
    page.route("**/tutores", lambda route: route.fulfill(status=401, content_type="application/json",
                                                     body='{"detail":"Credenciais inválidas"}'))
    page.get_by_role("button", name="Tutores", exact=True).click()
    expect(page.get_by_role("heading", name="Acesso do veterinário")).to_be_visible()
    assert not erros, erros
    browser.close()
print("OK: login, CEP real, tutor, animal sem raça/nascimento, RFID duplicado, consulta, vacinas, ficha, celular, logout e sessão expirada.")
