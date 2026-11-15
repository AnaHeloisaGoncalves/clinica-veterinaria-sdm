from getpass import getpass

from .auth import cria_confirmacao, hash_senha
from .cadastros import NovoVeterinario
from .db import database, write


def main():
    dados = NovoVeterinario(
        nome_completo=input("Nome completo: "),
        cpf=input("CPF: "),
        email=input("E-mail: "),
        numero_crmv=input("CRMV: "),
        uf_crmv=input("UF do CRMV: ").upper(),
        senha=getpass("Senha (mínimo 12 caracteres): "),
    )
    with_database = database()
    db = next(with_database)
    try:
        vet_id, _ = write(db, """
            INSERT INTO veterinario
                (nome_completo, cpf, email, numero_crmv, uf_crmv, senha_hash, administrador)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """, (dados.nome_completo, dados.cpf, dados.email, dados.numero_crmv, dados.uf_crmv, hash_senha(dados.senha)))
        codigo = cria_confirmacao(db, vet_id)
        db.commit()
    finally:
        with_database.close()
    print("Use o código de confirmação exibido a seguir em POST /confirmar-senha.")
    print(codigo)


if __name__ == "__main__":
    main()
