from datetime import date, datetime
from decimal import Decimal
from typing import Literal
import httpx

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .auth import sessao
from .db import database, query, write
from .cadastros import Pessoa, Endereco
from .nascimento import Nascimento, chave_especie, validar_nascimento_tutor
from .vacinas import VACINAS
from .validacao import VIAS_VACINA
from .integracao import snapshot_animal, nova_operacao, enviar

router = APIRouter(prefix="/clinica", dependencies=[Depends(sessao)])

class DadosClinicos(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Consulta(DadosClinicos):
    animal_id: int = Field(gt=0)
    data_hora: datetime
    motivo: str = Field(min_length=1, max_length=10000)
    anamnese: str | None = Field(default=None, max_length=10000)
    sintomas: str | None = Field(default=None, max_length=10000)
    diagnostico: str | None = Field(default=None, max_length=10000)
    tratamento_prescrito: str | None = Field(default=None, max_length=10000)
    observacoes: str | None = Field(default=None, max_length=10000)
    prescricao_medicamentos: str | None = Field(default=None, max_length=10000)
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
    vacina_codigo: str = Field(max_length=60, exclude=True)
    fabricante: str | None = Field(default=None, max_length=120)
    numero_lote: str | None = Field(default=None, max_length=120)
    via_aplicacao: str | None = Field(default=None, max_length=60)
    validade_lote: date | None = None
    observacoes: str | None = Field(default=None, max_length=10000)
    data_agendada: date | None = None
    data_aplicacao: date | None = None
    dose_etapa: str = Field(min_length=1, max_length=60)
    proxima_dose_em: date | None = None
    situacao: Literal["APLICADA", "AGENDADA", "CANCELADA"] = "APLICADA"

    @field_validator("via_aplicacao")
    @classmethod
    def validar_via(cls, valor):
        if valor is None:
            return None
        valor = valor.upper()
        if valor not in VIAS_VACINA:
            raise ValueError("Selecione uma via de aplicação da lista")
        return valor

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

def insert_clinical(db, table, model, extra, commit=True):
    values = model.model_dump()
    values.update(extra)
    fields = ", ".join(values)
    placeholders = ", ".join(["%s"] * len(values))
    registro_id, _ = write(db, f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", tuple(values.values()))
    if commit:
        db.commit()
    return registro_id

@router.post("/consultas", status_code=201)
def criar_consulta(dados: Consulta, db=Depends(database), vet=Depends(sessao)):
    ensure_animal(db, dados.animal_id)
    registro_id = insert_clinical(db, "consulta", dados, {"veterinario_id": vet["id"]})
    return query(db, "SELECT c.*, v.nome_completo AS veterinario_nome FROM consulta c JOIN veterinario v ON v.id = c.veterinario_id WHERE c.id = %s", (registro_id,))[0]

@router.get("/catalogo-vacinas")
def catalogo_vacinas(db=Depends(database)):
    especies = query(db, "SELECT id, nome FROM especie")
    return [
        {"codigo": codigo, "nome": nome, "tipo": tipo, "antirrabica": antirrabica,
         "especies": [e["id"] for e in especies if chave_especie(e["nome"]) in compatibilidade]}
        for codigo, (nome, tipo, compatibilidade, antirrabica) in VACINAS.items()
    ]


@router.post("/vacinas", status_code=201)
def criar_vacina(dados: Vacina, db=Depends(database), vet=Depends(sessao)):
    animais = query(db, """
        SELECT e.nome FROM animal a JOIN especie e ON e.id = a.especie_id
        WHERE a.id = %s AND a.situacao = 'ATIVO' FOR SHARE
        """, (dados.animal_id,))
    if not animais:
        raise HTTPException(404, "Animal não encontrado ou inativo")
    vacina = VACINAS.get(dados.vacina_codigo)
    if not vacina:
        raise HTTPException(422, "Selecione uma vacina do catálogo.")
    nome, tipo, especies, antirrabica = vacina
    if chave_especie(animais[0]["nome"]) not in especies:
        raise HTTPException(422, "A vacina selecionada não está no catálogo para esta espécie.")
    registro_id = insert_clinical(db, "vacina", dados, {
        "veterinario_id": vet["id"], "nome_vacina": nome,
        "tipo_vacina": tipo, "antirrabica": antirrabica,
    }, commit=False)
    operacao_id = None
    if antirrabica and dados.situacao == "APLICADA":
        animal = snapshot_animal(db, dados.animal_id)
        responsavel = query(db, "SELECT nome_completo, numero_crmv, uf_crmv FROM veterinario WHERE id=%s", (vet["id"],))[0]
        payload = {
            "animal": animal, "vacina_id": registro_id, "nome_vacina": nome,
            "antirrabica": True, "fabricante": dados.fabricante, "numero_lote": dados.numero_lote,
            "data_aplicacao": dados.data_aplicacao,
            "veterinario": f"{responsavel['nome_completo']} / {responsavel['numero_crmv']}-{responsavel['uf_crmv']}",
        }
        operacao_id = nova_operacao(db, dados.animal_id, "VACINA_ANTIRRABICA", payload, registro_id)
    db.commit()
    if operacao_id:
        enviar(db, operacao_id)
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
    vinculos = query(db, """SELECT m.id, m.codigo_rfid, m.vinculado_em, m.encerrado_em,
        m.veterinario_id, v.nome_completo AS veterinario_nome
        FROM vinculo_microchip m JOIN veterinario v ON v.id=m.veterinario_id
        WHERE m.animal_id=%s ORDER BY m.id DESC""", (animal_id,))
    microchip = next((m for m in vinculos if m["encerrado_em"] is None), None)
    return {"consultas": consultas, "vacinas": vacinas, "proximas_doses": proximas,
            "microchip": microchip, "vinculos_microchip": vinculos}


class Microchip(DadosClinicos):
    codigo_rfid: str = Field(min_length=1, max_length=48)


@router.post("/animais/{animal_id}/microchip", status_code=201)
def substituir_microchip(animal_id: int, dados: Microchip, db=Depends(database), vet=Depends(sessao)):
    # Serializa substituições do mesmo animal e mantém encerramento + novo vínculo atômicos.
    if not query(db, "SELECT id FROM animal WHERE id=%s AND situacao='ATIVO' FOR UPDATE", (animal_id,)):
        raise HTTPException(404, "Animal não encontrado ou inativo")
    if query(db, "SELECT id FROM vinculo_microchip WHERE codigo_rfid=%s", (dados.codigo_rfid,)):
        raise HTTPException(409, "RFID já está em uso ou pertence ao histórico de um animal")
    write(db, "UPDATE vinculo_microchip SET encerrado_em=CURRENT_TIMESTAMP WHERE animal_id=%s AND encerrado_em IS NULL", (animal_id,))
    registro_id, _ = write(db, "INSERT INTO vinculo_microchip (animal_id, veterinario_id, codigo_rfid) VALUES (%s,%s,%s)",
                          (animal_id, vet["id"], dados.codigo_rfid))
    db.commit()
    return query(db, "SELECT id, animal_id, veterinario_id, codigo_rfid, vinculado_em, encerrado_em FROM vinculo_microchip WHERE id=%s", (registro_id,))[0]


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
    data_nascimento: Nascimento
    endereco: Endereco

    _validar_nascimento = field_validator("data_nascimento")(validar_nascimento_tutor)


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


@router.put("/tutores/{tutor_id}")
def atualizar_tutor(tutor_id: int, dados: TutorComEndereco, db=Depends(database)):
    if not query(db, "SELECT id FROM tutor WHERE id=%s FOR UPDATE", (tutor_id,)):
        raise HTTPException(404, "Tutor não encontrado")
    # Um novo endereço evita modificar outros tutores que compartilhem o anterior.
    endereco = dados.endereco.model_dump()
    endereco_id, _ = write(db, f"INSERT INTO endereco ({', '.join(endereco)}) VALUES ({', '.join(['%s'] * len(endereco))})", tuple(endereco.values()))
    tutor = dados.model_dump(exclude={"endereco"})
    tutor["endereco_id"] = endereco_id
    write(db, f"UPDATE tutor SET {', '.join(f'{c}=%s' for c in tutor)} WHERE id=%s", (*tutor.values(), tutor_id))
    db.commit()
    return query(db, "SELECT * FROM tutor WHERE id=%s", (tutor_id,))[0]
