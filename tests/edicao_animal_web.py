"""Teste da interface com API simulada, sem alterar o banco local.

Execute com a clínica ligada: python -m unittest tests.edicao_animal_web -v
"""
import os
import unittest

from playwright.sync_api import sync_playwright, expect


class EdicaoAnimalWeb(unittest.TestCase):
    def test_editar_cancelar_validar_e_salvar(self):
        animal = dict(id=1, nome="Bento", tutor_id=1, especie_id=1, raca_id=1,
                      sexo="M", cor="Preto", peso_atual_kg="10.000",
                      data_nascimento=None, idade_estimada_meses=12, situacao="ATIVO")
        dados = {
            "animais": [animal],
            "tutores": [dict(id=1, nome_completo="Tutor", situacao="ATIVO")],
            "especies": [dict(id=i, nome=n, situacao="ATIVA") for i, n in [(1, "Cão"), (2, "Gato")]],
            "racas": [dict(id=i, nome=n, especie_id=e, situacao="ATIVA") for i, n, e in
                      [(1, "Labrador", 1), (2, "Siamês", 2), (3, "Sem raça definida (SRD)", 2)]],
        }
        requisicoes = []
        falhar = True

        def responder(route):
            nonlocal falhar
            request = route.request
            if request.method == "PUT":
                requisicoes.append(request.post_data_json)
                if falhar:
                    route.fulfill(status=409, json={"detail": "Não foi possível atualizar."})
                else:
                    animal.update(request.post_data_json)
                    route.fulfill(json=animal)
            else:
                route.fulfill(json=dados[request.url.rsplit("/", 1)[-1]])

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            base = os.getenv("TEST_API_URL", "http://127.0.0.1:8000")
            for entidade in dados:
                page.route(base + "/" + entidade, responder)
            page.route(base + "/animais/1", responder)
            page.goto(base)
            page.evaluate("(d) => { dados = d; token = 'teste'; animais(); }", dados)
            page.get_by_role("button", name="Editar Bento", exact=True).click()
            expect(page.get_by_label("Nome", exact=True)).to_have_value("Bento")
            expect(page.locator('[name="raca_id"]')).to_have_value("1")
            expect(page.locator('[name="codigo_rfid"]')).to_have_count(0)
            page.get_by_label("Nome", exact=True).fill("Descartar")
            page.get_by_role("button", name="Cancelar edição").click()
            self.assertEqual(requisicoes, [])
            page.get_by_role("button", name="Editar Bento", exact=True).click()
            page.locator('[name="especie_id"]').select_option("2")
            expect(page.locator('[name="raca_id"]')).to_have_value("")
            expect(page.locator('[name="raca_id"] option', has_text="Labrador")).to_have_count(0)
            page.locator('[name="raca_id"]').select_option("3")
            page.get_by_label("Nome", exact=True).fill("Bento atualizado")
            page.get_by_label("Peso (kg)").fill("11.5")
            page.get_by_role("button", name="Salvar alterações").click()
            expect(page.locator("#aviso")).to_contain_text("Não foi possível atualizar")
            expect(page.get_by_label("Nome", exact=True)).to_have_value("Bento atualizado")
            falhar = False
            page.get_by_role("button", name="Salvar alterações").click()
            expect(page.locator("#aviso")).to_contain_text("atualizados com sucesso")
            self.assertNotIn("codigo_rfid", requisicoes[-1])
            self.assertEqual(requisicoes[-1]["raca_id"], 3)
            self.assertEqual(requisicoes[-1]["especie_id"], 2)
            page.get_by_role("button", name="Editar Bento atualizado", exact=True).click()
            expect(page.get_by_label("Peso (kg)")).to_have_value("11.5")
            expect(page.locator('[name="raca_id"]')).to_have_value("3")
            browser.close()
