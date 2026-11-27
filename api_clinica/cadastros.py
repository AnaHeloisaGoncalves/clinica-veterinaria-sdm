import re
import secrets
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .auth import cria_confirmacao, exigir_gestor, hash_senha, sessao, simula_email
from .db import database, query, write
from .email_acesso import enviar_acesso
from .validacao import CORES, CORES_VALIDAS, SEXOS, UFS, VIAS_VACINA, nome_valido, uf_valida
from .nascimento import (
    LIMITE_ANIMAL_PADRAO_ANOS, LIMITE_TUTOR_ANOS, LIMITES_ANIMAL_ANOS,
    Nascimento, chave_especie, idade_meses, validar_nascimento_tutor,
)

router = APIRouter(dependencies=[Depends(sessao)])
Nome = Annotated[str, Field(min_length=1, max_length=150)]
Id = Annotated[int, Field(gt=0)]


class Dados(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Pessoa(Dados):
    nome_completo: Nome
    cpf: str
    email: str = Field(max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    telefone: str | None = Field(default=None, max_length=20)

    _nome_valido = field_validator("nome_completo")(nome_valido)

    @field_validator("telefone")
    @classmethod
    def telefone_valido(cls, valor):
        if valor is not None and not re.fullmatch(
            r"(?:\+55[ ]?)?(?:\([1-9][0-9]\)|[1-9][0-9])[ ]?[2-9][0-9]{3,4}-?[0-9]{4}", valor
        ):
            raise ValueError("Informe um telefone brasileiro com DDD e 8 ou 9 dígitos")
        return valor

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, value):
        if not re.fullmatch(r"(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})", value):
            raise ValueError("Informe o CPF com 11 dígitos, com ou sem máscara")
        digits = value.replace(".", "").replace("-", "")
        if len(digits) != 11 or not digits.isascii() or not digits.isdecimal() or len(set(digits)) == 1:
            raise ValueError("CPF inválido")
        for size in (9, 10):
            digit = sum(int(n) * weight for n, weight in zip(digits[:size], range(size + 1, 1, -1))) * 10 % 11 % 10
            if digit != int(digits[size]):
                raise ValueError("CPF inválido")
        return digits


class Tutor(Pessoa):
    data_nascimento: Nascimento
    endereco_id: Id

    _validar_nascimento = field_validator("data_nascimento")(validar_nascimento_tutor)


class Veterinario(Pessoa):
    numero_crmv: str = Field(min_length=1, max_length=20)
    uf_crmv: str = Field(min_length=2, max_length=2)

    _uf_valida = field_validator("uf_crmv")(uf_valida)


class NovoVeterinario(Veterinario):
    senha: str = Field(min_length=12, max_length=256)


class Endereco(Dados):
    cep: str = Field(pattern=r"^[0-9]{5}-?[0-9]{3}$")
    logradouro: str = Field(min_length=1, max_length=160)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=120)
    bairro: str = Field(min_length=1, max_length=120)
    cidade: str = Field(min_length=1, max_length=120)
    uf: str = Field(min_length=2, max_length=2)
    codigo_ibge: str | None = Field(default=None, pattern=r"^[0-9]{7}$")


    _uf_valida = field_validator("uf")(uf_valida)

    @field_validator("cep")
    @classmethod
    def limpar_cep(cls, valor):
        return valor.replace("-", "")

    @field_validator("logradouro", "bairro", "cidade")
    @classmethod
    def validar_endereco(cls, valor):
        if not any(letra.isalpha() for letra in valor):
            raise ValueError("Informe um nome de endereço válido")
        return valor

    @field_validator("numero")
    @classmethod
    def validar_numero(cls, valor):
        if not re.fullmatch(r"(?:[0-9]+(?:[ -]?[A-Za-z])?|s/?n|sem número)", valor, re.IGNORECASE):
            raise ValueError("Informe o número do imóvel ou S/N")
        return valor


class Especie(Dados):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = None


class Raca(Especie):
    especie_id: Id


class Animal(Dados):
    nome: str = Field(min_length=1, max_length=100)
    data_nascimento: Nascimento | None = None
    idade_estimada_meses: int | None = Field(default=None, ge=0)
    sexo: Literal["M", "F", "NI"]
    cor: str = Field(min_length=1, max_length=80)
    peso_atual_kg: Decimal = Field(gt=0, max_digits=8, decimal_places=3)
    tutor_id: Id
    especie_id: Id
    raca_id: Id | None = None

    _nome_valido = field_validator("nome")(nome_valido)

    @field_validator("cor")
    @classmethod
    def validar_cor(cls, valor):
        cor = valor.casefold()
        if cor not in CORES_VALIDAS:
            raise ValueError("Selecione uma coloração do catálogo")
        return cor

    @model_validator(mode="after")
    def verifica_idade(self):
        if self.data_nascimento is not None:
            self.idade_estimada_meses = idade_meses(self.data_nascimento, date.today())
            if self.idade_estimada_meses < 0:
                raise ValueError("O nascimento do animal não pode estar no futuro")
        elif self.idade_estimada_meses is None:
            raise ValueError("Informe a data de nascimento ou a idade estimada")
        return self


class NovoAnimal(Animal):
    codigo_rfid: str = Field(pattern=r"^[0-9]{15}$")

    @field_validator("codigo_rfid")
    @classmethod
    def validar_codigo_rfid(cls, valor):
        if len(set(valor)) == 1:
            raise ValueError("Informe um código RFID válido de 15 dígitos")
        return valor


@router.get("/regras-nascimento")
def regras_nascimento(db=Depends(database)):
    return {
        "hoje": date.today().isoformat(),
        "sexos": SEXOS,
        "cores": CORES,
        "ufs": UFS,
        "vias_vacina": VIAS_VACINA,
        "limite_tutor_meses": LIMITE_TUTOR_ANOS * 12,
        "limite_animal_meses": {e["id"]: limite_animal(e["nome"]) for e in query(db, "SELECT id, nome FROM especie")},
    }


def limite_animal(especie):
    return LIMITES_ANIMAL_ANOS.get(chave_especie(especie), LIMITE_ANIMAL_PADRAO_ANOS) * 12


def validar_animal(db, dados):
    especies = query(db, "SELECT nome FROM especie WHERE id = %s FOR SHARE", (dados.especie_id,))
    if not especies:
        raise HTTPException(409, "Espécie não encontrada.")
    limite = limite_animal(especies[0]["nome"])
    if dados.idade_estimada_meses > limite:
        raise HTTPException(422, f"A idade máxima de cadastro para esta espécie é {limite} meses.")
    validar_raca(db, dados)


def atualizar_idade(registro, hoje):
    if registro["data_nascimento"] is not None:
        registro["idade_estimada_meses"] = idade_meses(registro["data_nascimento"], hoje)
    return registro


def validar_raca(db, dados):
    if dados.raca_id is not None and not query(
        db, "SELECT id FROM raca WHERE id = %s AND especie_id = %s",
        (dados.raca_id, dados.especie_id),
    ):
        raise HTTPException(409, "A raça precisa pertencer à espécie escolhida.")


def add_crud(path, table, schema, create_schema, inactive):
    metadata = {"tutor": ("cadastrado_em",), "veterinario": (
        "cadastrado_em", "senha_confirmada", "senha_confirmada_em", "ultimo_acesso_em", "administrador",
    )}.get(table, ())
    columns = ", ".join(("id", *schema.model_fields, "situacao", *metadata))

    def get_one(db, registro_id):
        rows = query(db, f"SELECT {columns} FROM {table} WHERE id = %s", (registro_id,))
        if not rows:
            raise HTTPException(404, "Registro não encontrado")
        return atualizar_idade(rows[0], date.today()) if table == "animal" else rows[0]

    def require_admin(db, vet):
        if table == "veterinario":
            exigir_gestor(db, vet)

    @router.get(path, name=f"listar_{table}")
    def list_records(db=Depends(database)):
        rows = query(db, f"SELECT {columns} FROM {table} ORDER BY id")
        if table == "animal":
            hoje = date.today()
            return [atualizar_idade(row, hoje) for row in rows]
        return rows

    @router.get(path + "/{registro_id}", name=f"consultar_{table}")
    def get_record(registro_id: Id, db=Depends(database)):
        return get_one(db, registro_id)

    @router.post(path, status_code=201, name=f"criar_{table}")
    def create_record(dados: create_schema, db=Depends(database), vet=Depends(sessao)):
        require_admin(db, vet)
        if table == "animal":
            validar_animal(db, dados)
        values = dados.model_dump()
        rfid = values.pop("codigo_rfid", None)
        if table == "veterinario":
            values["senha_hash"] = hash_senha(values.pop("senha"))
        fields = ", ".join(values)
        placeholders = ", ".join(["%s"] * len(values))
        registro_id, _ = write(db, f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", tuple(values.values()))
        if rfid is not None:
            write(db, "INSERT INTO vinculo_microchip (animal_id, veterinario_id, codigo_rfid) VALUES (%s, %s, %s)",
                  (registro_id, vet["id"], rfid))
        codigo = cria_confirmacao(db, registro_id) if table == "veterinario" else None
        db.commit()
        if codigo:
            simula_email(values["email"], codigo)
        return get_one(db, registro_id)

    @router.put(path + "/{registro_id}", name=f"atualizar_{table}")
    def update_record(registro_id: Id, dados: schema, db=Depends(database), vet=Depends(sessao)):
        require_admin(db, vet)
        rows = query(db, f"SELECT {columns} FROM {table} WHERE id = %s FOR UPDATE", (registro_id,))
        if not rows:
            raise HTTPException(404, "Registro não encontrado")
        if table == "animal":
            validar_animal(db, dados)
        values = dados.model_dump()
        assignments = ", ".join(f"{field} = %s" for field in values)
        write(db, f"UPDATE {table} SET {assignments} WHERE id = %s", (*values.values(), registro_id))
        codigo = None
        if table == "veterinario" and rows[0]["email"] != values["email"]:
            write(db, "UPDATE veterinario SET senha_confirmada = FALSE, senha_confirmada_em = NULL WHERE id = %s", (registro_id,))
            write(db, "DELETE FROM sessao WHERE veterinario_id = %s", (registro_id,))
            codigo = cria_confirmacao(db, registro_id)
        db.commit()
        if codigo:
            simula_email(values["email"], codigo)
        return get_one(db, registro_id)

    @router.delete(path + "/{registro_id}", status_code=204, name=f"inativar_{table}")
    def inactive_record(registro_id: Id, db=Depends(database), vet=Depends(sessao)):
        require_admin(db, vet)
        if table == "veterinario" and registro_id == vet["id"]:
            raise HTTPException(409, "Você não pode inativar a própria conta.")
        get_one(db, registro_id)
        write(db, f"UPDATE {table} SET situacao = %s WHERE id = %s", (inactive, registro_id))
        if table == "veterinario":
            write(db, "DELETE FROM sessao WHERE veterinario_id = %s", (registro_id,))
        db.commit()
        return Response(status_code=204)



@router.get("/veterinarios/acessos")
def listar_acessos(db=Depends(database), vet=Depends(sessao)):
    exigir_gestor(db, vet)
    return query(db, """
        SELECT id, nome_completo, email, numero_crmv, uf_crmv, situacao, senha_confirmada,
               administrador, id = %s AS propria_conta
        FROM veterinario ORDER BY nome_completo, id
        """, (vet["id"],))


@router.post("/veterinarios/convites", status_code=201)
def convidar(dados: Veterinario, db=Depends(database), vet=Depends(sessao)):
    exigir_gestor(db, vet)
    registro_id, _ = write(db, """
        INSERT INTO veterinario (nome_completo, cpf, email, telefone, numero_crmv, uf_crmv, senha_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (dados.nome_completo, dados.cpf, dados.email, dados.telefone,
              dados.numero_crmv, dados.uf_crmv, hash_senha(secrets.token_urlsafe(32))))
    codigo = cria_confirmacao(db, registro_id, "convite")
    db.commit()
    enviar_acesso(dados.email, codigo, "convite")
    return {"id": registro_id}


@router.post("/veterinarios/{registro_id}/reenviar-convite", status_code=204)
def reenviar_convite(registro_id: Id, db=Depends(database), vet=Depends(sessao)):
    exigir_gestor(db, vet)
    rows = query(db, """
        SELECT email, situacao, senha_confirmada FROM veterinario WHERE id = %s FOR UPDATE
        """, (registro_id,))
    if not rows:
        raise HTTPException(404, "Veterinário não encontrado.")
    conta = rows[0]
    if conta["situacao"] != "ATIVO" or conta["senha_confirmada"]:
        raise HTTPException(409, "O reenvio está disponível para contas ativas com convite pendente.")
    codigo = cria_confirmacao(db, registro_id, "convite")
    db.commit()
    enviar_acesso(conta["email"], codigo, "convite")
    return Response(status_code=204)


add_crud("/tutores", "tutor", Tutor, Tutor, "INATIVO")
add_crud("/animais", "animal", Animal, NovoAnimal, "INATIVO")
add_crud("/especies", "especie", Especie, Especie, "INATIVA")
add_crud("/racas", "raca", Raca, Raca, "INATIVA")
add_crud("/enderecos", "endereco", Endereco, Endereco, "INATIVO")
add_crud("/veterinarios", "veterinario", Veterinario, NovoVeterinario, "INATIVO")
