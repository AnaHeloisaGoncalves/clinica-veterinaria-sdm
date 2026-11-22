import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

load_dotenv()
app = FastAPI(title="Governo simulado — demonstração acadêmica")


@contextmanager
def banco():
    db = sqlite3.connect(os.getenv("GOVERNO_DB", "governo.sqlite3"), timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS animal (
                microchip TEXT PRIMARY KEY, dados TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS vacinacao (
                chave TEXT PRIMARY KEY, microchip TEXT NOT NULL, dados TEXT NOT NULL, vacina_id INTEGER UNIQUE NOT NULL,
                FOREIGN KEY (microchip) REFERENCES animal(microchip)
            );
            CREATE TABLE IF NOT EXISTS operacao (
                chave TEXT PRIMARY KEY, requisicao TEXT NOT NULL,
                protocolo TEXT UNIQUE NOT NULL, resposta TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS simulacao (
                id INTEGER PRIMARY KEY CHECK (id=1), indisponivel INTEGER NOT NULL
            );
            INSERT OR IGNORE INTO simulacao VALUES (1,0);
        """)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    finally:
        db.close()


def autorizado(x_api_key: str = Header(default="")):
    import hmac
    key = os.getenv("GOVERNO_API_KEY", "")
    if len(key) < 32:
        raise HTTPException(503, "Configure GOVERNO_API_KEY")
    if not hmac.compare_digest(x_api_key, key):
        raise HTTPException(401, "Chave inválida")


def disponivel():
    with banco() as db:
        if db.execute("SELECT indisponivel FROM simulacao WHERE id=1").fetchone()[0]:
            raise HTTPException(503, "Indisponibilidade simulada")


class Animal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    microchip: str = Field(min_length=1, max_length=48)
    nome: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=80)
    tutor: str = Field(min_length=1, max_length=150)


class Vacinacao(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    animal: Animal
    vacina_id: int = Field(gt=0)
    nome_vacina: str = Field(min_length=1, max_length=120)
    antirrabica: bool
    fabricante: str = Field(min_length=1, max_length=120)
    numero_lote: str = Field(min_length=1, max_length=120)
    data_aplicacao: date
    veterinario: str = Field(min_length=1, max_length=150)

    @model_validator(mode="after")
    def conferir(self):
        if not self.antirrabica or self.data_aplicacao > date.today():
            raise ValueError("Informe uma aplicação antirrábica válida")
        return self


def processar(tipo, dados, chave, atualizar=False):
    try:
        uuid.UUID(chave)
    except ValueError as error:
        raise HTTPException(422, "Chave de idempotência deve ser UUID") from error
    payload = dados.model_dump(mode="json")
    requisicao = json.dumps({"tipo": tipo, "dados": payload}, sort_keys=True, ensure_ascii=False)
    with banco() as db:
        anterior = db.execute("SELECT * FROM operacao WHERE chave=?", (chave,)).fetchone()
        if anterior:
            if anterior["requisicao"] != requisicao:
                raise HTTPException(409, "Chave já utilizada com outros dados")
            return json.loads(anterior["resposta"])
        animal = payload["animal"] if tipo == "VACINA_ANTIRRABICA" else payload
        existe = db.execute("SELECT 1 FROM animal WHERE microchip=?", (animal["microchip"],)).fetchone()
        if tipo == "CADASTRO_ANIMAL" and existe:
            raise HTTPException(409, "Animal já cadastrado")
        if atualizar and not existe:
            raise HTTPException(404, "Animal não encontrado")
        if atualizar:
            db.execute("UPDATE animal SET dados=? WHERE microchip=?",
                       (json.dumps(animal, ensure_ascii=False), animal["microchip"]))
        elif not existe:
            db.execute("INSERT INTO animal VALUES (?,?)",
                       (animal["microchip"], json.dumps(animal, ensure_ascii=False)))
        if tipo == "VACINA_ANTIRRABICA":
            if db.execute("SELECT 1 FROM vacinacao WHERE vacina_id=?", (payload["vacina_id"],)).fetchone():
                raise HTTPException(409, "Aplicação já registrada com outra chave")
            db.execute("INSERT INTO vacinacao VALUES (?,?,?,?)",
                       (chave, animal["microchip"], json.dumps(payload, ensure_ascii=False), payload["vacina_id"]))
        resultado = {"protocolo": str(uuid.uuid4()), "situacao": "CONFIRMADA",
                     "microchip": animal["microchip"], "tipo_operacao": tipo}
        db.execute("INSERT INTO operacao VALUES (?,?,?,?)",
                   (chave, requisicao, resultado["protocolo"], json.dumps(resultado)))
        return resultado


private = [Depends(autorizado), Depends(disponivel)]


@app.get("/health")
def health():
    return {"status": "ok", "servico": "governo-simulado"}


@app.post("/api/governo/animais", dependencies=private)
def cadastrar(dados: Animal, idempotency_key: str = Header()):
    return processar("CADASTRO_ANIMAL", dados, idempotency_key)


@app.put("/api/governo/animais/{microchip:path}", dependencies=private)
def atualizar(microchip: str, dados: Animal, idempotency_key: str = Header()):
    if microchip != dados.microchip:
        raise HTTPException(422, "Microchip divergente")
    return processar("ATUALIZACAO_ANIMAL", dados, idempotency_key, atualizar=True)


@app.get("/api/governo/animais/{microchip:path}", dependencies=private)
def consultar(microchip: str):
    with banco() as db:
        row = db.execute("SELECT dados FROM animal WHERE microchip=?", (microchip,)).fetchone()
        if not row:
            raise HTTPException(404, "Animal não encontrado")
        vacinas = db.execute("SELECT dados FROM vacinacao WHERE microchip=?", (microchip,)).fetchall()
        return {"animal": json.loads(row["dados"]), "vacinas": [json.loads(v["dados"]) for v in vacinas]}


@app.post("/api/governo/vacinacoes-antirrabicas", dependencies=private)
def vacinar(dados: Vacinacao, idempotency_key: str = Header()):
    return processar("VACINA_ANTIRRABICA", dados, idempotency_key)


@app.get("/api/governo/operacoes/{protocolo}", dependencies=private)
def operacao(protocolo: str):
    with banco() as db:
        row = db.execute("SELECT resposta FROM operacao WHERE protocolo=?", (protocolo,)).fetchone()
        if not row:
            raise HTTPException(404, "Protocolo não encontrado")
        return json.loads(row["resposta"])


class Simulacao(BaseModel):
    indisponivel: bool


@app.put("/api/governo/simulacao", dependencies=[Depends(autorizado)])
def simular(dados: Simulacao):
    with banco() as db:
        db.execute("UPDATE simulacao SET indisponivel=? WHERE id=1", (dados.indisponivel,))
    return dados
