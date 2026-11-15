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
            raise HTTPException(409, "Registro duplicado ou referência inválida") from error
        return cursor.lastrowid, cursor.rowcount
