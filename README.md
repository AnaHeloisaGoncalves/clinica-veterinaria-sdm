# Clínica Veterinária · A3 de SDM

A API privada usa Python 3.14, FastAPI, Pydantic, Uvicorn e MySQL 8. O MySQL aplica as restrições do modelo, como CPF e RFID únicos. A API usa MySQL Connector/Python para executar consultas parametrizadas. Os scripts SQL ficam no diretório database.

A [documentação da Milestone 1](docs/milestone-1.md) descreve os requisitos e a arquitetura. O [modelo relacional](docs/modelo-relacional.md) registra o desenho original em PostgreSQL. A implementação da Milestone 2 usa MySQL e mantém o modelo como referência.

## Instalação no Windows

Na raiz do repositório, crie o ambiente e instale as dependências.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Use Python 3.14.x. No Linux ou macOS, crie o ambiente com `python3.14 -m venv .venv` e use `.venv/bin/python` nos comandos seguintes.

### Banco de dados

Com MySQL 8 em execução, abra o cliente MySQL como um usuário autorizado a criar bancos e usuários. A partir da raiz do repositório, rode `mysql -u root -p` e execute no cliente:

```sql
SOURCE database/banco1.sql;
CREATE USER 'clinica_app'@'localhost' IDENTIFIED BY 'SUBSTITUA_POR_UMA_SENHA_FORTE';
GRANT SELECT, INSERT, UPDATE, DELETE ON clinica_vet.* TO 'clinica_app'@'localhost';
```

Use um banco vazio para a primeira instalação. O script preserva bancos existentes e não altera tabelas já criadas. Quem tiver dados na estrutura anterior deve preservá-los e migrar o esquema separadamente antes de usar esta API. Senhas antigas em texto puro precisam ser redefinidas.

Preencha `DB_USER` e `DB_PASSWORD` no `.env` com o usuário e a senha escolhidos. Ajuste endereço e porta se necessário e gere um valor próprio para `JWT_SECRET`, por exemplo com `python -c "import secrets; print(secrets.token_urlsafe(48))"`. O arquivo `.env` deve ficar local.

### Acesso inicial e execução

Crie o primeiro veterinário administrador no terminal:

```powershell
.\.venv\Scripts\python.exe -m api_clinica.criar_administrador
```

O comando solicita a senha sem exibi-la e imprime um código de confirmação para a demonstração. Inicie os serviços em terminais separados:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_clinica.main:app --port 8000
.\.venv\Scripts\python.exe -m uvicorn api_governo.main:app --port 8001
```

Abra o [Swagger da clínica](http://127.0.0.1:8000/docs). Envie o código em `POST /confirmar-senha` no campo `codigo` e faça login com e-mail e senha em `POST /login`. No Swagger, use **Authorize** para informar o token retornado. O logout revoga a sessão do token apresentado.

As rotas privadas cobrem endereços, tutores, animais, espécies, raças e veterinários. Para cadastrar um animal, cadastre antes as entidades referenciadas e informe o RFID no cadastro. Somente um administrador pode criar, atualizar ou inativar veterinários. O terminal da API exibe o código de confirmação como simulação do envio por e-mail para novos veterinários. O [governo simulado](http://127.0.0.1:8001/docs) mantém sua rota de saúde.

## Testes da Milestone 2

Em um banco descartável com o esquema aplicado, deixe a API da clínica rodando com a mesma configuração de banco e execute em outro terminal:

```powershell
$env:ALLOW_TEST_DATA = '1'
.\.venv\Scripts\python.exe -m tests.entrega2
```

Use `TEST_API_URL` para informar outra porta. O teste grava dados fictícios e verifica confirmação de senha, login autorizado, senha incorreta, conta inativa, conta sem confirmação, acesso sem token, logout, cadastro e consulta de tutor, atualização, inativação, CPF inválido e duplicado, raça incompatível e RFID duplicado. Use somente um banco de testes, pois os registros de demonstração permanecem gravados.

Consulte as [evidências da execução local](docs/evidencias-milestone-2.md).
