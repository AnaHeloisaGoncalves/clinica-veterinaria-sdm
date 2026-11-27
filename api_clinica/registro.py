from fastapi import APIRouter, Depends

from .auth import hash_senha
from .cadastros import NovoVeterinario
from .db import database, query, write

router = APIRouter()


@router.post("/cadastro-veterinario", status_code=201)
def cadastro_veterinario(dados: NovoVeterinario, db=Depends(database)):
    """Cria uma conta de veterinário pronta para o primeiro login.

    O cadastro público não envia e-mail: a senha já fica confirmada, mas a
    conta nunca recebe privilégios de administrador.
    """
    valores = dados.model_dump()
    valores["senha_hash"] = hash_senha(valores.pop("senha"))
    valores["senha_confirmada"] = True
    valores["administrador"] = False
    valores["situacao"] = "ATIVO"
    campos = ", ".join(valores)
    placeholders = ", ".join(["%s"] * len(valores))
    registro_id, _ = write(
        db,
        f"INSERT INTO veterinario ({campos}) VALUES ({placeholders})",
        tuple(valores.values()),
    )
    db.commit()
    registro = query(
        db,
        "SELECT id, nome_completo, cpf, email, telefone, numero_crmv, uf_crmv, situacao, senha_confirmada, administrador "
        "FROM veterinario WHERE id = %s",
        (registro_id,),
    )[0]
    return {"mensagem": "Conta criada com sucesso. Entre com seu e-mail e senha.", **registro}
