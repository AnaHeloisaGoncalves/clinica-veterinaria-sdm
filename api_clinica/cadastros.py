from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .auth import cria_confirmacao, hash_senha, sessao, simula_email
from .db import database, query, write

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

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, value):
        digits = value.replace(".", "").replace("-", "")
        if len(digits) != 11 or not digits.isascii() or not digits.isdecimal() or len(set(digits)) == 1:
            raise ValueError("CPF inválido")
        for size in (9, 10):
            digit = sum(int(n) * weight for n, weight in zip(digits[:size], range(size + 1, 1, -1))) * 10 % 11 % 10
            if digit != int(digits[size]):
                raise ValueError("CPF inválido")
        return digits


class Tutor(Pessoa):
    data_nascimento: date
    endereco_id: Id


class Veterinario(Pessoa):
    numero_crmv: str = Field(min_length=1, max_length=20)
    uf_crmv: str = Field(pattern=r"^[A-Z]{2}$")


class NovoVeterinario(Veterinario):
    senha: str = Field(min_length=12, max_length=256)


class Endereco(Dados):
    cep: str = Field(pattern=r"^[0-9]{8}$")
    logradouro: str = Field(min_length=1, max_length=160)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=120)
    bairro: str = Field(min_length=1, max_length=120)
    cidade: str = Field(min_length=1, max_length=120)
    uf: str = Field(pattern=r"^[A-Z]{2}$")
    codigo_ibge: str | None = Field(default=None, pattern=r"^[0-9]{7}$")


class Especie(Dados):
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = None


class Raca(Especie):
    especie_id: Id


class Animal(Dados):
    nome: str = Field(min_length=1, max_length=100)
    data_nascimento: date | None = None
    idade_estimada_meses: int | None = Field(default=None, ge=0)
    sexo: str = Field(min_length=1, max_length=20)
    cor: str = Field(min_length=1, max_length=80)
    peso_atual_kg: Decimal = Field(gt=0, max_digits=8, decimal_places=3)
    tutor_id: Id
    especie_id: Id
    raca_id: Id | None = None

    @model_validator(mode="after")
    def verifica_idade(self):
        if self.data_nascimento is None and self.idade_estimada_meses is None:
            raise ValueError("Informe a data de nascimento ou a idade estimada")
        return self


class NovoAnimal(Animal):
    codigo_rfid: str = Field(min_length=1, max_length=48)


def add_crud(path, table, schema, create_schema, inactive):
    columns = ", ".join(("id", *schema.model_fields, "situacao"))

    def get_one(db, registro_id):
        rows = query(db, f"SELECT {columns} FROM {table} WHERE id = %s", (registro_id,))
        if not rows:
            raise HTTPException(404, "Registro não encontrado")
        return rows[0]

    def require_admin(db, vet):
        if table == "veterinario":
            rows = query(db, "SELECT administrador FROM veterinario WHERE id = %s FOR UPDATE", (vet["id"],))
            if not rows[0]["administrador"]:
                raise HTTPException(403, "Operação restrita a administradores")

    @router.get(path, name=f"listar_{table}")
    def list_records(db=Depends(database)):
        return query(db, f"SELECT {columns} FROM {table} ORDER BY id")

    @router.get(path + "/{registro_id}", name=f"consultar_{table}")
    def get_record(registro_id: Id, db=Depends(database)):
        return get_one(db, registro_id)

    @router.post(path, status_code=201, name=f"criar_{table}")
    def create_record(dados: create_schema, db=Depends(database), vet=Depends(sessao)):
        require_admin(db, vet)
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
        get_one(db, registro_id)
        write(db, f"UPDATE {table} SET situacao = %s WHERE id = %s", (inactive, registro_id))
        if table == "veterinario":
            write(db, "DELETE FROM sessao WHERE veterinario_id = %s", (registro_id,))
        db.commit()
        return Response(status_code=204)


add_crud("/tutores", "tutor", Tutor, Tutor, "INATIVO")
add_crud("/animais", "animal", Animal, NovoAnimal, "INATIVO")
add_crud("/especies", "especie", Especie, Especie, "INATIVA")
add_crud("/racas", "raca", Raca, Raca, "INATIVA")
add_crud("/enderecos", "endereco", Endereco, Endereco, "INATIVO")
add_crud("/veterinarios", "veterinario", Veterinario, NovoVeterinario, "INATIVO")
