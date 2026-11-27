"""Cria uma conta fictícia e os catálogos para a apresentação, sem apagar dados."""
import os
from api_clinica.auth import hash_senha
from api_clinica.db import database, query, write
from scripts.catalogos import carregar_catalogos


def main():
    senha = os.getenv("DEMO_PASSWORD", "")
    if len(senha) < 12:
        raise SystemExit("Defina DEMO_PASSWORD com pelo menos 12 caracteres no .env local.")
    gen = database()
    db = next(gen)
    try:
        if not query(db, "SELECT id FROM veterinario WHERE email = 'demo@example.test'"):
            write(db, """INSERT INTO veterinario
                (nome_completo, cpf, numero_crmv, uf_crmv, email, senha_hash, senha_confirmada, administrador)
                VALUES ('Veterinária Demonstração', '52998224725', 'DEMO-001', 'SP',
                        'demo@example.test', %s, TRUE, TRUE)""", (hash_senha(senha),))
        carregar_catalogos(db)
        db.commit()
        print("Conta demo@example.test e catálogos preparados. Senha: valor de DEMO_PASSWORD no .env.")
    finally:
        gen.close()


if __name__ == "__main__":
    main()
