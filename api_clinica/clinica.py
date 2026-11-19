from datetime import date, datetime
from decimal import Decimal
from typing import Literal
import httpx

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .auth import sessao
from .db import database, query, write
from .cadastros import Pessoa, Endereco

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
    peso_registrado_kg: Decimal | None = Field(default=None, gt=0, max_digits=8, decimal_places=3)
    temperatura_c: Decimal | None = Field(default=None, gt=0, lt=100, max_digits=5, decimal_places=2)
    situacao: Literal["REALIZADA", "AGENDADA", "CANCELADA", "NAO_COMPARECEU"] = "REALIZADA"

    @model_validator(mode="after")
    def data_local(self):
        if self.data_hora.tzinfo is not None:
            raise ValueError("Informe data e hora local da clínica, sem fuso horário")
        if self.situacao == "REALIZADA" and self.peso_registrado_kg is None:
            raise ValueError("Informe o peso registrado para uma consulta realizada")
        if self.situacao in ("REALIZADA", "NAO_COMPARECEU") and self.data_hora > datetime.now():
            raise ValueError("O horário do atendimento ainda não chegou")
        return self

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
    situacao: Literal["APLICADA", "AGENDADA", "CANCELADA"] = "APLICADA"

    @model_validator(mode="after")
    def validar_datas(self):
        if self.situacao == "APLICADA" and not self.data_aplicacao:
            raise ValueError("Informe a data de aplicação")
        if self.situacao == "APLICADA":
            faltando = [
                nome for nome, valor in {
                    "fabricante": self.fabricante,
                    "número do lote": self.numero_lote,
                    "via de aplicação": self.via_aplicacao,
                    "validade do lote": self.validade_lote,
                }.items() if not valor
            ]
            if faltando:
                raise ValueError("Informe " + ", ".join(faltando) + " para vacina aplicada")
        if self.situacao == "AGENDADA" and not self.data_agendada:
            raise ValueError("Informe a data agendada")
        if self.situacao != "APLICADA" and (self.data_aplicacao or self.proxima_dose_em):
            raise ValueError("Aplicação e próxima dose só devem ser informadas para vacina aplicada")
        if self.data_aplicacao:
            if self.data_aplicacao > date.today():
                raise ValueError("A aplicação não pode estar no futuro")
            if self.validade_lote and self.validade_lote < self.data_aplicacao:
                raise ValueError("O lote estava vencido na data da aplicação")
            if self.proxima_dose_em and self.proxima_dose_em <= self.data_aplicacao:
                raise ValueError("A próxima dose deve ser posterior à aplicação")
        return self

def ensure_animal(db, animal_id):
    if not query(db, "SELECT id FROM animal WHERE id = %s AND situacao = 'ATIVO'", (animal_id,)):
        raise HTTPException(404, "Animal não encontrado ou inativo")

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
    if not query(db, "SELECT id FROM animal WHERE id = %s", (animal_id,)):
        raise HTTPException(404, "Animal não encontrado")
    consultas = query(db, "SELECT c.*, v.nome_completo AS veterinario_nome FROM consulta c JOIN veterinario v ON v.id = c.veterinario_id WHERE c.animal_id = %s ORDER BY c.data_hora DESC", (animal_id,))
    vacinas = query(db, "SELECT z.*, v.nome_completo AS veterinario_nome FROM vacina z JOIN veterinario v ON v.id = z.veterinario_id WHERE z.animal_id = %s ORDER BY COALESCE(z.data_aplicacao, z.data_agendada) DESC", (animal_id,))
    proximas = [dict(id=v["id"], nome_vacina=v["nome_vacina"], antirrabica=v["antirrabica"],
                     data_prevista=v["proxima_dose_em"] if v["situacao"] == "APLICADA" else v["data_agendada"])
                for v in vacinas if (v["situacao"] == "APLICADA" and v["proxima_dose_em"])
                or (v["situacao"] == "AGENDADA" and v["data_agendada"])]
    for dose in proximas:
        dose["prazo"] = "ATRASADA" if dose["data_prevista"] < date.today() else "PREVISTA"
    proximas.sort(key=lambda dose: dose["data_prevista"])
    microchip = query(db, "SELECT codigo_rfid, vinculado_em FROM vinculo_microchip WHERE animal_id = %s AND encerrado_em IS NULL", (animal_id,))
    return {"consultas": consultas, "vacinas": vacinas, "proximas_doses": proximas, "microchip": microchip[0] if microchip else None}


@router.get("/cep/{cep}")
def consultar_cep(cep: str):
    if len(cep) != 8 or not cep.isascii() or not cep.isdecimal():
        raise HTTPException(422, "Informe um CEP com 8 dígitos")
    try:
        resposta = httpx.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
    except httpx.TimeoutException as error:
        raise HTTPException(504, "A consulta do CEP demorou demais. Preencha o endereço manualmente.") from error
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(503, "ViaCEP indisponível. Preencha o endereço manualmente.") from error
    if not isinstance(dados, dict):
        raise HTTPException(503, "Resposta inválida do ViaCEP. Preencha o endereço manualmente.")
    if dados.get("erro"):
        raise HTTPException(404, "CEP não encontrado. Preencha o endereço manualmente.")
    return {"logradouro": dados.get("logradouro", ""), "bairro": dados.get("bairro", ""),
            "cidade": dados.get("localidade", ""), "uf": dados.get("uf", ""), "codigo_ibge": dados.get("ibge", "")}


class TutorComEndereco(Pessoa):
    data_nascimento: date
    endereco: Endereco


@router.post("/tutores", status_code=201)
def cadastrar_tutor(dados: TutorComEndereco, db=Depends(database)):
    # Endereço e tutor são gravados juntos: um CPF repetido não deixa endereço órfão.
    endereco = dados.endereco.model_dump()
    campos = ", ".join(endereco)
    marcadores = ", ".join(["%s"] * len(endereco))
    endereco_id, _ = write(db, f"INSERT INTO endereco ({campos}) VALUES ({marcadores})", tuple(endereco.values()))
    tutor = dados.model_dump(exclude={"endereco"})
    tutor["endereco_id"] = endereco_id
    campos = ", ".join(tutor)
    marcadores = ", ".join(["%s"] * len(tutor))
    tutor_id, _ = write(db, f"INSERT INTO tutor ({campos}) VALUES ({marcadores})", tuple(tutor.values()))
    db.commit()
    return {"id": tutor_id, **tutor}
