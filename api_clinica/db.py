import os
from collections.abc import Iterator

import mysql.connector
from dotenv import load_dotenv
from fastapi import HTTPException
from mysql.connector.errors import IntegrityError

load_dotenv()


def database() -> Iterator:
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "clinica_vet"),
    )
    try:
        yield connection
    finally:
        connection.close()


def query(connection, sql, values=()):
    with connection.cursor(dictionary=True, buffered=True) as cursor:
        cursor.execute(sql, values)
        return cursor.fetchall()


def write(connection, sql, values=()):
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql, values)
        except IntegrityError as error:
            connection.rollback()
            mensagem = "Registro duplicado ou referência inválida"
            if error.errno == 1062 and "vinculo_microchip" in sql:
                mensagem = "RFID já está em uso. Informe outro código."
            elif error.errno == 1062 and "tutor" in sql:
                mensagem = "Já existe um tutor com este CPF."
            elif error.errno == 1452 and "animal" in sql:
                mensagem = "Confira tutor, espécie e raça. A raça precisa pertencer à espécie escolhida."
            raise HTTPException(409, mensagem) from error
        return cursor.lastrowid, cursor.rowcount
