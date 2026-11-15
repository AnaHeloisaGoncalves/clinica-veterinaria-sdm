import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from .db import database, query, write

router = APIRouter()
bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("uvicorn.error")


class Login(BaseModel):
    email: str
    senha: str = Field(max_length=256)


class Confirmacao(BaseModel):
    codigo: str = Field(min_length=32, max_length=128)


def hash_senha(senha):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(senha.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verifica_senha(senha, stored):
    try:
        algorithm, salt, expected = stored.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(digest, bytes.fromhex(expected))
    except (ValueError, TypeError, AttributeError):
        return False


def jwt_secret():
    secret = os.getenv("JWT_SECRET", "")
    if len(secret.encode()) < 32:
        raise HTTPException(503, "Configure JWT_SECRET com pelo menos 32 bytes")
    return secret


def unauthorized():
    return HTTPException(401, "Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"})


def sessao(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(database)):
    if credentials is None:
        raise unauthorized()
    try:
        token = jwt.decode(
            credentials.credentials, jwt_secret(), algorithms=["HS256"],
            options={"require": ["sub", "jti", "exp"]},
        )
    except jwt.InvalidTokenError as error:
        raise unauthorized() from error
    rows = query(db, """
        SELECT v.id, s.id AS sessao_id FROM sessao s
        JOIN veterinario v ON v.id = s.veterinario_id
        WHERE s.id = %s AND v.id = %s AND s.expira_em > UTC_TIMESTAMP()
              AND v.situacao = 'ATIVO' AND v.senha_confirmada = TRUE
        """, (token["jti"], token["sub"]))
    if not rows:
        raise unauthorized()
    return rows[0]


@router.post("/login")
def login(dados: Login, db=Depends(database)):
    rows = query(db, """
        SELECT id, senha_hash, senha_confirmada, situacao
        FROM veterinario WHERE email = %s FOR UPDATE
        """, (dados.email,))
    if not rows:
        raise unauthorized()
    vet = rows[0]
    if not verifica_senha(dados.senha, vet["senha_hash"]):
        raise unauthorized()
    if vet["situacao"] != "ATIVO" or not vet["senha_confirmada"]:
        raise HTTPException(403, "Conta inativa ou sem confirmação")
    expira = datetime.now(timezone.utc) + timedelta(hours=8)
    sessao_id = secrets.token_hex(32)
    token = jwt.encode({"sub": str(vet["id"]), "jti": sessao_id, "exp": expira}, jwt_secret(), algorithm="HS256")
    write(db, "INSERT INTO sessao (id, veterinario_id, expira_em) VALUES (%s, %s, %s)",
          (sessao_id, vet["id"], expira.replace(tzinfo=None)))
    write(db, "UPDATE veterinario SET ultimo_acesso_em = UTC_TIMESTAMP() WHERE id = %s", (vet["id"],))
    db.commit()
    return {"token_acesso": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
def logout(vet=Depends(sessao), db=Depends(database)):
    write(db, "DELETE FROM sessao WHERE id = %s", (vet["sessao_id"],))
    db.commit()
    return Response(status_code=204)


def cria_confirmacao(db, vet_id):
    codigo = secrets.token_urlsafe(32)
    digest = hashlib.sha256(codigo.encode()).hexdigest()
    write(db, "UPDATE veterinario SET confirmacao_hash = %s, confirmacao_expira_em = UTC_TIMESTAMP() + INTERVAL 1 HOUR WHERE id = %s",
          (digest, vet_id))
    return codigo


def simula_email(email, codigo):
    logger.info("E-mail simulado para %s. Código de confirmação: %s", email, codigo)


@router.post("/confirmar-senha", status_code=204)
def confirmar(dados: Confirmacao, db=Depends(database)):
    digest = hashlib.sha256(dados.codigo.encode()).hexdigest()
    _, count = write(db, """
        UPDATE veterinario SET senha_confirmada = TRUE, senha_confirmada_em = UTC_TIMESTAMP(),
            confirmacao_hash = NULL, confirmacao_expira_em = NULL
        WHERE confirmacao_hash = %s AND confirmacao_expira_em > UTC_TIMESTAMP()
              AND situacao = 'ATIVO'
        """, (digest,))
    if not count:
        raise HTTPException(400, "Código inválido ou expirado")
    db.commit()
    return Response(status_code=204)
