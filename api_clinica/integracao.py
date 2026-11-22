import json
import os
import uuid
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from .auth import sessao
from .db import database, query, write

router = APIRouter(prefix="/clinica", dependencies=[Depends(sessao)])


def headers(chave=None):
    result = {"X-API-Key": os.getenv("GOVERNO_API_KEY", "")}
    if chave:
        result["Idempotency-Key"] = chave
    return result


def url(path):
    return os.getenv("GOVERNO_URL", "http://127.0.0.1:8001").rstrip("/") + "/api/governo" + path


def snapshot_animal(db, animal_id):
    rows = query(db, """
        SELECT a.nome, e.nome AS especie, t.nome_completo AS tutor, m.codigo_rfid AS microchip
        FROM animal a JOIN especie e ON e.id=a.especie_id JOIN tutor t ON t.id=a.tutor_id
        JOIN vinculo_microchip m ON m.animal_id=a.id AND m.encerrado_em IS NULL
        WHERE a.id=%s FOR UPDATE
        """, (animal_id,))
    if not rows:
        raise HTTPException(409, "Animal precisa de vínculo vigente de microchip")
    return rows[0]


def nova_operacao(db, animal_id, tipo, payload, vacina_id=None):
    key = str(uuid.uuid4())
    registro_id, _ = write(db, """
        INSERT INTO integracao_governo
        (animal_id, vacina_id, tipo_operacao, chave_idempotencia, situacao, payload_envio)
        VALUES (%s,%s,%s,%s,'PENDENTE',%s)
        """, (animal_id, vacina_id, tipo, key, json.dumps(jsonable_encoder(payload), ensure_ascii=False)))
    return registro_id


def enviar(db, registro_id):
    # O bloqueio dura até o resultado local ser persistido. Reenvios concorrentes
    # aguardam e depois encontram CONFIRMADA. Uma queda libera a transação pendente.
    rows = query(db, "SELECT * FROM integracao_governo WHERE id=%s FOR UPDATE", (registro_id,))
    if not rows:
        raise HTTPException(404, "Integração não encontrada")
    op = rows[0]
    if op["situacao"] == "CONFIRMADA":
        db.commit()
        return op
    payload = json.loads(op["payload_envio"]) if isinstance(op["payload_envio"], str) else op["payload_envio"]
    paths = {
        "CADASTRO_ANIMAL": ("POST", "/animais"),
        "ATUALIZACAO_ANIMAL": ("PUT", "/animais/" + quote(payload.get("microchip", ""), safe="")),
        "VACINA_ANTIRRABICA": ("POST", "/vacinacoes-antirrabicas"),
    }
    method, path = paths[op["tipo_operacao"]]
    write(db, "UPDATE integracao_governo SET situacao='ENVIADA', quantidade_tentativas=quantidade_tentativas+1 WHERE id=%s", (registro_id,))
    status, protocolo, erro = "PENDENTE", None, None
    try:
        response = httpx.request(method, url(path), json=payload,
                                headers=headers(op["chave_idempotencia"]), timeout=5)
        if response.is_success:
            result = response.json()
            if result.get("situacao") != "CONFIRMADA" or not result.get("protocolo"):
                raise ValueError("Resposta sem protocolo de confirmação")
            status, protocolo = "CONFIRMADA", result["protocolo"]
        else:
            status = "PENDENTE" if response.status_code >= 500 or response.status_code in (408, 429) else "FALHA"
            erro = f"Governo retornou HTTP {response.status_code}"
    except (httpx.HTTPError, ValueError, AttributeError):
        erro = "Falha de comunicação ou resposta inválida. Reenvie a mesma operação."
    write(db, """
        UPDATE integracao_governo SET situacao=%s, protocolo_externo=%s, mensagem_erro=%s,
        respondida_em=UTC_TIMESTAMP() WHERE id=%s
        """, (status, protocolo, erro, registro_id))
    db.commit()
    return query(db, "SELECT * FROM integracao_governo WHERE id=%s", (registro_id,))[0]


@router.get("/integracoes")
def listar(animal_id: int | None = None, db=Depends(database)):
    if animal_id is not None:
        return query(db, "SELECT * FROM integracao_governo WHERE animal_id=%s ORDER BY id DESC", (animal_id,))
    return query(db, "SELECT * FROM integracao_governo ORDER BY id DESC")


@router.post("/integracoes/{registro_id}/reenviar")
def reenviar(registro_id: int, db=Depends(database)):
    return enviar(db, registro_id)


@router.post("/animais/{animal_id}/sincronizar")
def sincronizar(animal_id: int, db=Depends(database)):
    payload = snapshot_animal(db, animal_id)
    try:
        response = httpx.get(url("/animais/" + quote(payload["microchip"], safe="")), headers=headers(), timeout=5)
        if response.status_code == 404:
            tipo = "CADASTRO_ANIMAL"
        elif response.is_success:
            tipo = "ATUALIZACAO_ANIMAL"
        else:
            raise HTTPException(503, "Governo indisponível para consultar o cadastro")
    except httpx.HTTPError as error:
        raise HTTPException(503, "Governo indisponível para consultar o cadastro") from error
    op = nova_operacao(db, animal_id, tipo, payload)
    db.commit()
    return enviar(db, op)


@router.get("/animais/{animal_id}/governo")
def consultar_governo(animal_id: int, db=Depends(database)):
    payload = snapshot_animal(db, animal_id)
    db.commit()
    try:
        response = httpx.get(url("/animais/" + quote(payload["microchip"], safe="")), headers=headers(), timeout=5)
        if response.status_code == 404:
            raise HTTPException(404, "Animal ainda não cadastrado no governo simulado")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(503, "Governo indisponível") from error
