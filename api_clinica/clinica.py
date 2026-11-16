from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .auth import sessao
from .db import database, query, write

router = APIRouter(prefix="/clinica", dependencies=[Depends(sessao)])

class DadosClinicos(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Consulta(DadosClinicos):
    animal_id: int = Field(gt=0)
    data_hora: datetime
    motivo: str | None = None
    anamnese: str | None = None
    sintomas: str | None = None
    diagnostico: str | None = None
    tratamento_prescrito: str | None = None
    observacoes: str | None = None
    prescricao_medicamentos: str | None = None
    peso_registrado_kg: float | None = Field(default=None, gt=0)
    temperatura_c: float | None = None
    situacao: str = Field(default="REALIZADA", min_length=1, max_length=20)

class Vacina(DadosClinicos):
    animal_id: int = Field(gt=0)
    nome_vacina: str = Field(min_length=1, max_length=120)
    tipo_vacina: str | None = Field(default=None, max_length=60)
    antirrabica: bool = False
    fabricante: str | None = Field(default=None, max_length=120)
    numero_lote: str | None = Field(default=None, max_length=120)
    via_aplicacao: str | None = Field(default=None, max_length=60)
    validade_lote: date | None = None
    observacoes: str | None = None
    data_agendada: date | None = None
    data_aplicacao: date | None = None
    dose_etapa: str | None = Field(default=None, max_length=60)
    proxima_dose_em: date | None = None
    situacao: str = Field(default="APLICADA", min_length=1, max_length=10)

def ensure_animal(db, animal_id):
    if not query(db, "SELECT id FROM animal WHERE id = %s", (animal_id,)):
        raise HTTPException(404, "Animal não encontrado")

def insert_clinical(db, table, model, extra):
    values = model.model_dump()
    values.update(extra)
    fields = ", ".join(values)
    placeholders = ", ".join(["%s"] * len(values))
    registro_id, _ = write(db, f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", tuple(values.values()))
    db.commit()
    return registro_id

@router.post("/consultas", status_code=201)
def criar_consulta(dados: Consulta, db=Depends(database), vet=Depends(sessao)):
    ensure_animal(db, dados.animal_id)
    registro_id = insert_clinical(db, "consulta", dados, {"veterinario_id": vet["id"]})
    return query(db, "SELECT c.*, v.nome_completo AS veterinario_nome FROM consulta c JOIN veterinario v ON v.id = c.veterinario_id WHERE c.id = %s", (registro_id,))[0]

@router.post("/vacinas", status_code=201)
def criar_vacina(dados: Vacina, db=Depends(database), vet=Depends(sessao)):
    ensure_animal(db, dados.animal_id)
    registro_id = insert_clinical(db, "vacina", dados, {"veterinario_id": vet["id"]})
    return query(db, "SELECT z.*, v.nome_completo AS veterinario_nome FROM vacina z JOIN veterinario v ON v.id = z.veterinario_id WHERE z.id = %s", (registro_id,))[0]

@router.get("/animais/{animal_id}/historico")
def historico_animal(animal_id: int, db=Depends(database)):
    ensure_animal(db, animal_id)
    consultas = query(db, "SELECT c.*, v.nome_completo AS veterinario_nome FROM consulta c JOIN veterinario v ON v.id = c.veterinario_id WHERE c.animal_id = %s ORDER BY c.data_hora DESC", (animal_id,))
    vacinas = query(db, "SELECT z.*, v.nome_completo AS veterinario_nome FROM vacina z JOIN veterinario v ON v.id = z.veterinario_id WHERE z.animal_id = %s ORDER BY COALESCE(z.data_aplicacao, z.data_agendada) DESC", (animal_id,))
    proximas = query(db, "SELECT id, nome_vacina, antirrabica, proxima_dose_em, situacao FROM vacina WHERE animal_id = %s AND proxima_dose_em IS NOT NULL ORDER BY proxima_dose_em", (animal_id,))
    return {"consultas": consultas, "vacinas": vacinas, "proximas_doses": proximas}
