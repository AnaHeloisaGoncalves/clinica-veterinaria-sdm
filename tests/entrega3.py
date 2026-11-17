"""Testes com MySQL real; use somente banco de demonstração."""
import os
import secrets
import unittest
from datetime import date, timedelta
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from api_clinica.main import app
from api_clinica.db import database, query
from tests.entrega2 import cpf

@unittest.skipUnless(os.getenv("ALLOW_TEST_DATA") == "1", "Defina ALLOW_TEST_DATA=1 em um banco descartável")
class EntregaTres(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        login = self.client.post("/login", json={"email": "demo@example.test", "senha": os.environ["DEMO_PASSWORD"]})
        self.assertEqual(login.status_code, 200)
        self.client.headers["Authorization"] = "Bearer " + login.json()["token_acesso"]
        self.run_id = secrets.token_hex(5)

    def tearDown(self):
        self.client.post("/logout")
        self.client.close()

    def criar_animal(self):
        tutor = self.client.post("/clinica/tutores", json={
            "nome_completo": "Tutor Teste " + self.run_id, "cpf": cpf(400000000 + secrets.randbelow(99999999)),
            "email": self.run_id + "@example.test", "data_nascimento": "1990-01-01",
            "endereco": {"cep": "01001000", "logradouro": "Praça da Sé", "numero": "1",
                         "bairro": "Sé", "cidade": "São Paulo", "uf": "SP"}})
        self.assertEqual(tutor.status_code, 201, tutor.text)
        especie = self.client.get("/especies").json()[0]
        self.animal = dict(nome="Bento " + self.run_id, tutor_id=tutor.json()["id"], especie_id=especie["id"],
                           raca_id=None, data_nascimento=None, idade_estimada_meses=0,
                           sexo="M", cor="preto", peso_atual_kg=3, codigo_rfid="TEST-" + self.run_id)
        resposta = self.client.post("/animais", json=self.animal)
        self.assertEqual(resposta.status_code, 201, resposta.text)
        return resposta.json()["id"]

    def test_fluxo_clinico_e_rfid(self):
        animal_id = self.criar_animal()
        repetido = self.client.post("/animais", json=self.animal)
        self.assertEqual(repetido.status_code, 409)
        self.assertIn("RFID", repetido.json()["detail"])
        consulta = self.client.post("/clinica/consultas", json={
            "animal_id": animal_id, "data_hora": "2026-11-16T10:00:00", "situacao": "REALIZADA",
            "anamnese": "Demonstração", "sintomas": "Sem queixas", "diagnostico": "Avaliação de rotina",
            "prescricao_medicamentos": "Sem prescrição", "peso_registrado_kg": 3, "temperatura_c": 38.5})
        self.assertEqual(consulta.status_code, 201, consulta.text)
        vacina = dict(animal_id=animal_id, nome_vacina="Antirrábica teste", antirrabica=True,
                      data_aplicacao=str(date.today()), proxima_dose_em=str(date.today() + timedelta(days=365)),
                      fabricante="Fictício", numero_lote="DEMO", via_aplicacao="SC", dose_etapa="1", situacao="APLICADA")
        self.assertEqual(self.client.post("/clinica/vacinas", json=vacina).status_code, 201)
        sem_proxima = {**vacina, "proxima_dose_em": None, "antirrabica": False}
        self.assertEqual(self.client.post("/clinica/vacinas", json=sem_proxima).status_code, 201)
        historico = self.client.get(f"/clinica/animais/{animal_id}/historico").json()
        self.assertEqual(len(historico["consultas"]), 1)
        self.assertEqual(len(historico["vacinas"]), 2)
        self.assertEqual(len(historico["proximas_doses"]), 1)
        self.assertEqual(historico["consultas"][0]["veterinario_nome"], "Veterinária Demonstração")
        self.assertEqual(historico["microchip"]["codigo_rfid"], self.animal["codigo_rfid"])
        self.assertEqual({v["antirrabica"] for v in historico["vacinas"]}, {0, 1})

    def test_datas_situacao_e_responsavel(self):
        animal_id = self.criar_animal()
        base = dict(animal_id=animal_id, nome_vacina="Teste")
        for dados in [
            base, {**base, "situacao": "INVALIDA"},
            {**base, "data_aplicacao": str(date.today() + timedelta(days=1))},
            {**base, "data_aplicacao": "2026-01-10", "proxima_dose_em": "2026-01-09"},
            {**base, "data_aplicacao": "2026-01-10", "validade_lote": "2026-01-09"},
            {**base, "situacao": "AGENDADA"},
            {**base, "situacao": "CANCELADA", "proxima_dose_em": "2027-01-01"},
            {**base, "data_aplicacao": "2026-01-10", "veterinario_id": 999}
        ]:
            with self.subTest(dados=dados):
                self.assertEqual(self.client.post("/clinica/vacinas", json=dados).status_code, 422)
        self.assertEqual(self.client.post("/clinica/consultas", json={
            "animal_id": animal_id, "data_hora": "2026-01-10T10:00:00", "situacao": "INVALIDA"}).status_code, 422)

    def test_agendamento_cancelamento_e_atraso(self):
        animal_id = self.criar_animal()
        for situacao in ["AGENDADA", "CANCELADA"]:
            resposta = self.client.post("/clinica/vacinas", json={
                "animal_id": animal_id, "nome_vacina": situacao, "situacao": situacao, "data_agendada": "2020-01-01"})
            self.assertEqual(resposta.status_code, 201)
        h = self.client.get(f"/clinica/animais/{animal_id}/historico").json()
        self.assertEqual(len(h["proximas_doses"]), 1)
        self.assertEqual(h["proximas_doses"][0]["prazo"], "ATRASADA")

    def test_cep_inexistente_timeout_indisponivel(self):
        request = httpx.Request("GET", "https://viacep.com.br")
        for resposta, status in [(httpx.Response(200, json={"erro": True}, request=request), 404),
                                  (httpx.Response(503, request=request), 503)]:
            with patch("api_clinica.clinica.httpx.get", return_value=resposta):
                self.assertEqual(self.client.get("/clinica/cep/00000000").status_code, status)
        with patch("api_clinica.clinica.httpx.get", side_effect=httpx.ReadTimeout("teste")):
            self.assertEqual(self.client.get("/clinica/cep/01001000").status_code, 504)
        self.assertEqual(self.client.get("/clinica/cep/abc").status_code, 422)

    def test_sem_token_e_logout(self):
        token = self.client.headers.pop("Authorization")
        for caminho in ["/clinica/animais/1/historico", "/clinica/cep/01001000"]:
            self.assertEqual(self.client.get(caminho).status_code, 401)
        self.client.headers["Authorization"] = token
        self.assertEqual(self.client.post("/logout").status_code, 204)
        self.assertEqual(self.client.get("/animais").status_code, 401)

    def test_tutor_duplicado_nao_deixa_endereco(self):
        tutor = self.client.get("/tutores").json()[0]
        gen = database()
        db = next(gen)
        try:
            antes = query(db, "SELECT COUNT(*) AS total FROM endereco")[0]["total"]
            resposta = self.client.post("/clinica/tutores", json={
                "nome_completo": "Duplicado", "cpf": tutor["cpf"], "email": "dup@example.test",
                "data_nascimento": "1990-01-01", "endereco": {
                    "cep": "01001000", "logradouro": "Praça da Sé", "numero": "2",
                    "bairro": "Sé", "cidade": "São Paulo", "uf": "SP"}})
            self.assertEqual(resposta.status_code, 409)
            db.commit()
            depois = query(db, "SELECT COUNT(*) AS total FROM endereco")[0]["total"]
            self.assertEqual(antes, depois)
        finally:
            gen.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)

