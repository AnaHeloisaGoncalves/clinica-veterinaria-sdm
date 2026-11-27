"""Regressões para os requisitos do PDF A3-SDM, somente em base descartável."""
import os
import secrets
import unittest
from concurrent.futures import ThreadPoolExecutor

from api_clinica.auth import cria_confirmacao
from api_clinica.db import database, query
from tests import entrega3
from tests.entrega2 import cpf


@unittest.skipUnless(os.getenv('ALLOW_TEST_DATA') == '1', 'Use banco descartável')
class RequisitosA3(unittest.TestCase):
    setUp = entrega3.EntregaTres.setUp
    tearDown = entrega3.EntregaTres.tearDown
    criar_animal = entrega3.EntregaTres.criar_animal

    def test_substituicao_rfid_historico_e_concorrencia(self):
        animal_id = self.criar_animal()
        path = f'/clinica/animais/{animal_id}/microchip'
        codigo = 'NOVO-' + self.run_id
        novo = self.client.post(path, json={'codigo_rfid': codigo})
        self.assertEqual(novo.status_code, 201, novo.text)
        h = self.client.get(f'/clinica/animais/{animal_id}/historico').json()
        self.assertEqual(h['microchip']['codigo_rfid'], codigo)
        self.assertEqual(len(h['vinculos_microchip']), 2)
        self.assertIsNotNone(h['vinculos_microchip'][1]['encerrado_em'])
        self.assertTrue(all(m['veterinario_nome'] for m in h['vinculos_microchip']))
        for codigo_usado in (codigo, self.animal['codigo_rfid']):
            self.assertEqual(self.client.post(path, json={'codigo_rfid': codigo_usado}).status_code, 409)
        with ThreadPoolExecutor(max_workers=2) as pool:
            respostas = list(pool.map(lambda n: self.client.post(path, json={'codigo_rfid': f'CONCORRENTE-{self.run_id}-{n}'}), [1, 2]))
        self.assertTrue(all(r.status_code == 201 for r in respostas))
        h = self.client.get(f'/clinica/animais/{animal_id}/historico').json()
        self.assertEqual(len(h['vinculos_microchip']), 4)
        self.assertEqual(sum(m['encerrado_em'] is None for m in h['vinculos_microchip']), 1)
        self.assertEqual(self.client.post(path, json={'codigo_rfid': '   '}).status_code, 422)

    def test_edicao_tutor_atomica_metadados_e_inativacao(self):
        self.criar_animal()
        tutor_id = self.animal['tutor_id']
        antes = self.client.get(f'/tutores/{tutor_id}').json()
        self.assertIn('cadastrado_em', antes)
        endereco = dict(cep='01001000', logradouro='Rua Teste', numero='10', bairro='Centro', cidade='São Paulo', uf='SP')
        dados = {k: antes[k] for k in ('nome_completo', 'cpf', 'email', 'telefone', 'data_nascimento')}
        dados.update(nome_completo='Tutor alterado', endereco=endereco)
        r = self.client.put(f'/clinica/tutores/{tutor_id}', json=dados)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotEqual(r.json()['endereco_id'], antes['endereco_id'])
        outro = self.client.post('/clinica/tutores', json={**dados, 'cpf': cpf(700000000 + secrets.randbelow(99999999))}).json()
        gen = database()
        db = next(gen)
        try:
            count = query(db, 'SELECT COUNT(*) AS n FROM endereco')[0]['n']
            db.commit()
            duplicado = self.client.put(f'/clinica/tutores/{tutor_id}', json={**dados, 'cpf': outro['cpf']})
            self.assertEqual(duplicado.status_code, 409)
            self.assertEqual(query(db, 'SELECT COUNT(*) AS n FROM endereco')[0]['n'], count)
        finally:
            gen.close()
        self.assertEqual(self.client.delete(f'/tutores/{tutor_id}').status_code, 204)
        self.assertEqual(self.client.get(f'/tutores/{tutor_id}').json()['situacao'], 'INATIVO')

    def test_veterinario_confirmacao_e_permissoes(self):
        senha = secrets.token_urlsafe(18)
        dados = dict(nome_completo='Profissional teste', cpf=cpf(800000000 + secrets.randbelow(99999999)),
                     email=self.run_id + '@example.test', numero_crmv=self.run_id, uf_crmv='SP', senha=senha)
        r = self.client.post('/veterinarios', json=dados)
        self.assertEqual(r.status_code, 201, r.text)
        vet = r.json()
        self.assertNotIn('senha_hash', vet)
        self.assertFalse(vet['senha_confirmada'])
        self.assertIn('ultimo_acesso_em', vet)
        self.assertEqual(self.client.post('/login', json={'email': dados['email'], 'senha': senha}).status_code, 403)
        self.assertEqual(self.client.post(f"/veterinarios/{vet['id']}/reenviar-confirmacao").status_code, 204)
        gen = database()
        db = next(gen)
        try:
            codigo = cria_confirmacao(db, vet['id'])
            db.commit()
        finally:
            gen.close()
        self.assertEqual(self.client.post('/confirmar-senha', json={'codigo': codigo}).status_code, 204)
        self.assertEqual(self.client.post('/confirmar-senha', json={'codigo': codigo}).status_code, 400)
        token = self.client.post('/login', json={'email': dados['email'], 'senha': senha}).json()['token_acesso']
        h = {'Authorization': 'Bearer ' + token}
        self.assertEqual(self.client.post('/veterinarios', json=dados, headers=h).status_code, 403)
        self.assertEqual(self.client.post(f"/veterinarios/{vet['id']}/reenviar-confirmacao", headers=h).status_code, 403)
        self.assertEqual(self.client.delete(f"/veterinarios/{vet['id']}").status_code, 204)
        self.assertEqual(self.client.get('/animais', headers=h).status_code, 401)

    def test_atualizacao_animal_rejeita_raca_incompativel(self):
        animal_id = self.criar_animal()
        especies = self.client.get('/especies').json()
        outra = next(e for e in especies if e['id'] != self.animal['especie_id'])
        raca = self.client.post('/racas', json={'nome': 'Raça teste', 'especie_id': outra['id']}).json()
        dados = {k: v for k, v in self.animal.items() if k != 'codigo_rfid'}
        self.assertEqual(self.client.put(f'/animais/{animal_id}', json={**dados, 'raca_id': raca['id']}).status_code, 409)
        dados.update(especie_id=outra['id'], raca_id=raca['id'], nome='Animal atualizado')
        r = self.client.put(f'/animais/{animal_id}', json=dados)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['nome'], 'Animal atualizado')
