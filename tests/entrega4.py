"""Testes da integração com MySQL e governo simulado reais em banco descartável."""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from unittest.mock import patch

import httpx

from api_clinica.db import database, query
from tests import entrega3
import unittest


@unittest.skipUnless(os.getenv("ALLOW_TEST_DATA") == "1", "Use um banco descartável")
class EntregaQuatro(unittest.TestCase):
    setUp = entrega3.EntregaTres.setUp
    tearDown = entrega3.EntregaTres.tearDown
    criar_animal = entrega3.EntregaTres.criar_animal

    def test_integracao_falha_reenvio_idempotencia(self):
        animal_id = self.criar_animal()
        governo = os.getenv("GOVERNO_URL", "http://127.0.0.1:8001") + "/api/governo"
        headers = {"X-API-Key": os.environ["GOVERNO_API_KEY"]}
        vacina = dict(animal_id=animal_id, nome_vacina="Antirrábica teste", antirrabica=True,
                      fabricante="Fictício", numero_lote="TESTE", via_aplicacao="SC",
                      validade_lote=str(date.today() + timedelta(days=365)), dose_etapa="1",
                      data_aplicacao=str(date.today()), situacao="APLICADA")
        self.assertEqual(httpx.put(governo + "/simulacao", headers=headers,
                                  json={"indisponivel": True}).status_code, 200)
        self.addCleanup(lambda: httpx.put(governo + "/simulacao", headers=headers, json={"indisponivel": False}))
        response = self.client.post("/clinica/vacinas", json=vacina)
        self.assertEqual(response.status_code, 201, response.text)
        vacina_id = response.json()["id"]
        ops = self.client.get("/clinica/integracoes", params={"animal_id": animal_id}).json()
        self.assertEqual(len(ops), 1)
        op = ops[0]
        self.assertEqual(op["situacao"], "PENDENTE")
        self.assertEqual(op["quantidade_tentativas"], 1)
        self.assertEqual(op["vacina_id"], vacina_id)
        self.assertEqual(len(self.client.get(f"/clinica/animais/{animal_id}/historico").json()["vacinas"]), 1)
        self.assertEqual(httpx.put(governo + "/simulacao", headers=headers,
                                  json={"indisponivel": False}).status_code, 200)
        antigo_nome = self.animal["nome"]
        atualizado = self.animal.copy()
        atualizado.pop("codigo_rfid")
        atualizado["nome"] = "Nome após registro da vacina"
        self.assertEqual(self.client.put(f"/animais/{animal_id}", json=atualizado).status_code, 200)
        path = f"/clinica/integracoes/{op['id']}/reenviar"
        # O governo grava a operação e a resposta se perde. O próximo envio usa a mesma chave.
        real_request = httpx.request

        def resposta_perdida(*args, **kwargs):
            result = real_request(*args, **kwargs)
            self.assertEqual(result.status_code, 200, result.text)
            raise httpx.ReadTimeout("Resposta perdida após gravação")

        with patch("api_clinica.integracao.httpx.request", side_effect=resposta_perdida):
            self.assertEqual(self.client.post(path).json()["situacao"], "PENDENTE")
        confirmada = self.client.post(path).json()
        self.assertEqual(confirmada["situacao"], "CONFIRMADA")
        self.assertEqual(confirmada["chave_idempotencia"], op["chave_idempotencia"])
        self.assertEqual(confirmada["quantidade_tentativas"], 3)
        self.assertEqual(self.client.post(path).json()["quantidade_tentativas"], 3)
        externo = self.client.get(f"/clinica/animais/{animal_id}/governo").json()
        self.assertEqual(len(externo["vacinas"]), 1)
        self.assertEqual(externo["vacinas"][0]["animal"]["nome"], antigo_nome)
        self.assertEqual(externo["vacinas"][0]["vacina_id"], vacina_id)
        protocolo = confirmada["protocolo_externo"]
        self.assertEqual(httpx.get(governo + "/operacoes/" + protocolo, headers=headers).json()["protocolo"], protocolo)
        gen = database()
        db = next(gen)
        try:
            payload = query(db, "SELECT payload_envio FROM integracao_governo WHERE id=%s", (op["id"],))[0]["payload_envio"]
        finally:
            gen.close()
        import json
        payload = json.loads(payload) if isinstance(payload, str) else payload
        replay_headers = {**headers, "Idempotency-Key": op["chave_idempotencia"]}
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: httpx.post(governo + "/vacinacoes-antirrabicas",
                                                        headers=replay_headers, json=payload), range(3)))
        self.assertTrue(all(r.json()["protocolo"] == protocolo for r in results))
        conflito = httpx.post(governo + "/vacinacoes-antirrabicas", headers=replay_headers,
                             json={**payload, "numero_lote": "OUTRO"})
        self.assertEqual(conflito.status_code, 409)
        invalid = httpx.post(governo + "/vacinacoes-antirrabicas",
                             headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
                             json={**payload, "antirrabica": False})
        self.assertEqual(invalid.status_code, 422)
        outra_chave = httpx.post(governo + "/vacinacoes-antirrabicas",
                                headers={**headers, "Idempotency-Key": str(uuid.uuid4())}, json=payload)
        self.assertEqual(outra_chave.status_code, 409)
        # Reconsultar após todos os replays comprova a contagem persistida,
        # além da igualdade dos protocolos retornados pelas respostas.
        externo_apos_replays = self.client.get(f"/clinica/animais/{animal_id}/governo")
        self.assertEqual(externo_apos_replays.status_code, 200)
        self.assertEqual(len(externo_apos_replays.json()["vacinas"]), 1)
        self.assertEqual(externo_apos_replays.json()["vacinas"][0]["vacina_id"], vacina_id)
        self.assertEqual(httpx.get(governo + "/animais/" + self.animal["codigo_rfid"]).status_code, 401)
        outras = self.client.post("/clinica/vacinas", json={**vacina, "antirrabica": False})
        self.assertEqual(outras.status_code, 201)
        self.assertEqual(len(self.client.get("/clinica/integracoes", params={"animal_id": animal_id}).json()), 1)

    def test_sincronizacao_cadastro_atualizacao(self):
        animal_id = self.criar_animal()
        result = self.client.post(f"/clinica/animais/{animal_id}/sincronizar")
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["situacao"], "CONFIRMADA")
        self.assertEqual(result.json()["tipo_operacao"], "CADASTRO_ANIMAL")
        values = self.animal.copy()
        values.pop("codigo_rfid")
        values["nome"] = "Nome atualizado"
        self.assertEqual(self.client.put(f"/animais/{animal_id}", json=values).status_code, 200)
        result = self.client.post(f"/clinica/animais/{animal_id}/sincronizar").json()
        self.assertEqual(result["tipo_operacao"], "ATUALIZACAO_ANIMAL")
        self.assertEqual(result["situacao"], "CONFIRMADA")
        self.assertEqual(self.client.get(f"/clinica/animais/{animal_id}/governo").json()["animal"]["nome"], "Nome atualizado")


    def test_rejeicao_corrigida_e_vacinas_sem_comunicacao(self):
        animal_id = self.criar_animal()
        vacina = dict(animal_id=animal_id, nome_vacina="Teste", dose_etapa="1",
                      fabricante="Fictício", numero_lote="TESTE", via_aplicacao="SC",
                      validade_lote=str(date.today() + timedelta(days=365)),
                      data_aplicacao=str(date.today()), antirrabica=True)
        with patch.dict(os.environ, {"GOVERNO_API_KEY": "chave-incorreta-para-o-teste"}):
            response = self.client.post("/clinica/vacinas", json=vacina)
        self.assertEqual(response.status_code, 201)
        op = self.client.get("/clinica/integracoes", params={"animal_id": animal_id}).json()[0]
        self.assertEqual(op["situacao"], "FALHA")
        self.assertIn("401", op["mensagem_erro"])
        result = self.client.post(f"/clinica/integracoes/{op['id']}/reenviar").json()
        self.assertEqual(result["situacao"], "CONFIRMADA")
        for situacao in ("AGENDADA", "CANCELADA"):
            response = self.client.post("/clinica/vacinas", json={
                "animal_id": animal_id, "nome_vacina": "Teste", "dose_etapa": "1",
                "antirrabica": True, "situacao": situacao, "data_agendada": str(date.today())})
            self.assertEqual(response.status_code, 201)
        self.assertEqual(len(self.client.get("/clinica/integracoes", params={"animal_id": animal_id}).json()), 1)
