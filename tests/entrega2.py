import json
import os
import secrets
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from api_clinica.auth import cria_confirmacao, hash_senha
from api_clinica.db import database, write

BASE = os.getenv("TEST_API_URL", "http://127.0.0.1:8000")


def cpf(prefix):
    digits = f"{prefix:09d}"
    for size in (9, 10):
        digit = sum(int(n) * weight for n, weight in zip(digits, range(size + 1, 1, -1))) * 10 % 11 % 10
        digits += str(digit)
    return digits


class EntregaDois(unittest.TestCase):
    def test_autenticacao_e_cadastros(self):
        db_generator = database()
        db = next(db_generator)
        self.addCleanup(db_generator.close)
        run = secrets.token_hex(6)
        senha = secrets.token_urlsafe(24)
        emails = [f"{run}-{i}@example.test" for i in range(3)]
        ids = []
        base = 100000000 + secrets.randbelow(299999990)
        for i, email in enumerate(emails):
            vet, _ = write(db, """
                INSERT INTO veterinario
                    (nome_completo, cpf, numero_crmv, uf_crmv, email, senha_hash,
                     situacao, administrador)
                VALUES ('Veterinário de teste', %s, %s, 'SP', %s, %s, %s, %s)
                """, (cpf(base + i), f"{run}-{i}", email, hash_senha(senha),
                      "INATIVO" if i == 1 else "ATIVO", i == 0))
            ids.append(vet)
        codigo = cria_confirmacao(db, ids[0])
        write(db, "UPDATE veterinario SET senha_confirmada = TRUE WHERE id = %s", (ids[1],))
        db.commit()

        def call(method, path, status, data=None, token=None):
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = "Bearer " + token
            request = Request(BASE + path, method=method, headers=headers,
                              data=None if data is None else json.dumps(data).encode())
            try:
                response = urlopen(request, timeout=5)
            except HTTPError as error:
                response = error
            with response:
                content = response.read()
                self.assertEqual(response.code, status, f"{method} {path}")
                return json.loads(content) if content else None

        call("GET", "/health", 200)
        call("GET", "/tutores", 401)
        call("POST", "/login", 401, {"email": emails[0], "senha": "incorreta"})
        for email in emails:
            call("POST", "/login", 403, {"email": email, "senha": senha})
        call("POST", "/confirmar-senha", 204, {"codigo": codigo})
        call("POST", "/confirmar-senha", 400, {"codigo": codigo})
        token = call("POST", "/login", 200, {"email": emails[0], "senha": senha})["token_acesso"]

        endereco = dict(cep="01001000", logradouro="Praça da Sé", numero="1",
                        bairro="Sé", cidade="São Paulo", uf="SP")
        endereco_id = call("POST", "/enderecos", 201, endereco, token)["id"]
        tutor = dict(nome_completo="Tutor de teste", cpf=cpf(base + 3),
                     data_nascimento="1990-01-01", email=f"{run}@example.test", endereco_id=endereco_id)
        tutor_id = call("POST", "/tutores", 201, tutor, token)["id"]
        tutor_path = f"/tutores/{tutor_id}"
        call("POST", "/tutores", 409, tutor, token)
        call("POST", "/tutores", 422, {**tutor, "cpf": "123"}, token)
        self.assertEqual(call("GET", tutor_path, 200, token=token)["cpf"], tutor["cpf"])
        tutor["nome_completo"] = "Tutor atualizado"
        call("PUT", tutor_path, 200, tutor, token)
        self.assertEqual(call("GET", tutor_path, 200, token=token)["nome_completo"], tutor["nome_completo"])

        especie = call("POST", "/especies", 201, {"nome": "Cão"}, token)["id"]
        outra = call("POST", "/especies", 201, {"nome": "Gato"}, token)["id"]
        raca = call("POST", "/racas", 201, {"nome": "SRD", "especie_id": especie}, token)["id"]
        animal = dict(nome="Bento", idade_estimada_meses=12, sexo="M", cor="preto",
                      peso_atual_kg=10, tutor_id=tutor_id, especie_id=especie, raca_id=raca,
                      codigo_rfid=f"TESTE-{run}")
        call("POST", "/animais", 409, {**animal, "especie_id": outra}, token)
        call("POST", "/animais", 201, animal, token)
        call("POST", "/animais", 409, animal, token)
        call("DELETE", tutor_path, 204, token=token)
        self.assertEqual(call("GET", tutor_path, 200, token=token)["situacao"], "INATIVO")
        call("POST", "/logout", 204, token=token)
        call("GET", "/tutores", 401, token=token)


if __name__ == "__main__":
    if os.getenv("ALLOW_TEST_DATA") != "1":
        raise SystemExit("Use um banco descartável e defina ALLOW_TEST_DATA=1.")
    unittest.main(verbosity=2)
