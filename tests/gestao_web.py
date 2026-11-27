"""Fluxos de gestão no navegador com APIs e banco de testes reais."""
import os
import secrets
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from tests.entrega2 import cpf


@unittest.skipUnless(os.getenv('ALLOW_TEST_DATA') == '1', 'Use banco descartável')
class GestaoWeb(unittest.TestCase):
    def captura(self, page, nome):
        if os.getenv('TEST_ARTIFACT_DIR'):
            page.screenshot(path=str(Path(os.environ['TEST_ARTIFACT_DIR']) / nome), full_page=True)

    def test_gestao_completa_desktop_e_mobile(self):
        run = secrets.token_hex(5)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            erros = []
            page.on('pageerror', lambda e: erros.append(str(e)))
            page.goto(os.environ['TEST_API_URL'])
            page.locator('#login [name=email]').fill('demo@example.test')
            page.locator('#login [name=senha]').fill(os.environ['DEMO_PASSWORD'])
            page.get_by_role('button', name='Entrar', exact=True).click()
            expect(page.get_by_role('heading', name='Painel da clínica')).to_be_visible()
            # Gerar cadastro fictício pela mesma API usada pela tela.
            dados = dict(nome_completo='Tutor UI ' + run, cpf=cpf(600000000 + secrets.randbelow(99999999)),
                         data_nascimento='1990-01-01', email=run+'@example.test',
                         endereco=dict(cep='01001000', logradouro='Rua Teste', numero='1', bairro='Centro', cidade='São Paulo', uf='SP'))
            tutor = page.evaluate('(d) => api("/clinica/tutores", "POST", d)', dados)
            especie = page.evaluate('() => dados.especies[0].id')
            animal = page.evaluate('(d) => api("/animais", "POST", d)', dict(
                nome='Animal UI ' + run, tutor_id=tutor['id'], especie_id=especie, raca_id=None,
                idade_estimada_meses=12, sexo='M', cor='Preto', peso_atual_kg=5, codigo_rfid='UI-'+run))
            page.evaluate('() => navegar("tutores")')
            page.locator(f'[data-editar-tutor="{tutor["id"]}"]').click()
            expect(page.locator('#tutor [name=numero]')).to_have_value('1')
            page.locator('#tutor [name=numero]').fill('42')
            page.get_by_role('button', name='Salvar tutor', exact=True).click()
            expect(page.locator('#aviso')).to_contain_text('atualizado')
            page.locator(f'[data-editar-tutor="{tutor["id"]}"]').click()
            expect(page.locator('#tutor [name=numero]')).to_have_value('42')
            self.captura(page, 'tutor-edicao.png')
            page.evaluate('() => navegar("animais")')
            page.locator(f'[data-ficha="{animal["id"]}"]').click()
            expect(page.get_by_role('heading', name='Vínculos de microchip')).to_be_visible()
            page.locator('#substituir-microchip [name=codigo_rfid]').fill('UI-NOVO-'+run)
            page.on('dialog', lambda d: d.accept())
            page.get_by_role('button', name='Vincular novo microchip').click()
            expect(page.locator('#aviso')).to_contain_text('Histórico anterior preservado')
            expect(page.get_by_role('heading', name='UI-'+run+' · Encerrado', exact=True)).to_be_visible()
            self.captura(page, 'microchip-historico.png')
            page.evaluate('() => navegar("veterinarios")')
            form = page.locator('#veterinario')
            for key, value in dict(nome_completo='Vet UI '+run, cpf=cpf(900000000 + secrets.randbelow(99999999)),
                                   email='vet-'+run+'@example.test', numero_crmv='UI-'+run,
                                   uf_crmv='SP', senha='SenhaFicticia-'+run).items():
                form.locator(f'[name={key}]').fill(value)
            page.get_by_role('button', name='Salvar profissional').click()
            expect(page.locator('#aviso')).to_contain_text('Profissional salvo')
            expect(page.get_by_role('heading', name='Vet UI '+run, exact=True)).to_be_visible()
            self.captura(page, 'veterinarios.png')
            page.evaluate('() => navegar("catalogos")')
            page.locator('#especie [name=nome]').fill('Espécie UI '+run)
            page.locator('#especie [name=descricao]').fill('Descrição de teste')
            page.get_by_role('button', name='Cadastrar espécie', exact=True).click()
            expect(page.locator('#aviso')).to_contain_text('Cadastro realizado')
            page.get_by_role('button', name='Editar Espécie UI '+run, exact=True).click()
            page.locator('#editar-catalogo [name=descricao]').fill('Descrição alterada')
            page.get_by_role('button', name='Salvar catálogo').click()
            expect(page.locator('#aviso')).to_contain_text('atualizado')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.evaluate('() => navegar("animais")')
            page.locator(f'[data-editar-animal="{animal["id"]}"]').click()
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            expect(page.get_by_role('button', name='Salvar alterações')).to_be_visible()
            self.captura(page, 'animal-mobile.png')
            self.assertEqual(erros, [])
            browser.close()
