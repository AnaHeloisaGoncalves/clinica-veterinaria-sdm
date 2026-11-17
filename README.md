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

## Milestone 3 — interface e funcionalidades clínicas

Além da API, esta entrega inclui uma interface web responsiva em `frontend/`. Ela usa o token retornado pelo login em todas as operações privadas, permite logout, consulta de CEP via ViaCEP com preenchimento manual de contingência, cadastro de tutor e animal/RFID, registro local de consultas e vacinas e consulta da ficha/históricos.

### Executar a interface

As telas são servidas pela própria API. Na raiz do repositório, execute:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_clinica.main:app --host 127.0.0.1 --port 8000
```

Abra <http://127.0.0.1:8000>. Não é necessário Node, npm ou um servidor separado
para usar o frontend. A interface usa o mesmo endereço da API.

Para testar em um celular da mesma rede, inicie com `--host 0.0.0.0` e abra
`http://IP_DO_COMPUTADOR:8000`. Isso depende da rede e do firewall. A configuração
padrão fica restrita ao próprio computador.

### Dados fictícios para demonstração

Após criar o banco, inclua `DEMO_PASSWORD` no .env com uma senha de pelo menos 12
caracteres e execute `python -m scripts.demo` usando o Python da .venv.
O script cria o veterinário `demo@example.test`, já confirmado para a demonstração,
e os catálogos Cão/Labrador e Gato/Siamês. Não apaga nem redefine cadastros existentes.
Use somente um banco local de demonstração. Para contas normais, siga o fluxo de
criação e confirmação da Milestone 2.

O fluxo demonstrativo é: login → Tutores → consulte `01001000` → complete número/complemento e cadastre → Animais → selecione tutor/espécie/raça opcional e informe RFID → Atendimento → registre consulta e vacina → Animais → **Ficha de [nome]**.

### Casos de erro demonstráveis

- CEP `00000000` ou serviço indisponível: a interface informa o problema e mantém os campos editáveis para preenchimento manual.
- RFID já cadastrado: a API retorna conflito e a interface mostra “RFID já está em uso...”.
- Raça de outra espécie: a lista é reconstruída ao trocar a espécie e a seleção anterior é limpa. A API mantém a validação por chave estrangeira composta.
- Acesso sem login: a API retorna 401 e a interface volta ao formulário de login.

As rotas clínicas privadas são `POST /clinica/consultas`, `POST /clinica/vacinas` e `GET /clinica/animais/{animal_id}/historico`. O envio ao governo simulado continua fora desta milestone.

A consulta de CEP usa `GET /clinica/cep/{cep}`: a API chama o ViaCEP com timeout de
5 segundos. `POST /clinica/tutores` grava tutor e endereço na mesma transação.
Consultas e vacinas recebem o veterinário da sessão. As datas e horas de consulta
são informadas no horário local da clínica, sem conversão de fuso.

Em Atendimento estão todos os campos clínicos do modelo. A vacina aplicada exige
data de aplicação; a agendada exige data de agendamento. Próxima dose e validade do
lote são conferidas quando informadas. A ficha mostra os detalhes e diferencia
previsões futuras de datas que já passaram. Não há baixa automática de uma previsão
ao registrar uma nova aplicação: confira o histórico.

### Repetir os testes

Com o banco descartável configurado, a conta de demonstração criada e a API ligada:

```powershell
$env:ALLOW_TEST_DATA = '1'
.\.venv\Scripts\python.exe -m unittest tests.entrega2 tests.entrega3 -v
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m tests.demo_web
```

Os testes deixam dados fictícios no banco. O teste web consulta o ViaCEP real e
atualiza as capturas em `docs/evidencias/`. Timeout e indisponibilidade são simulados
nos testes da API para permitir reprodução. A prova de execução e os limites estão
em [Testes da Milestone 3](docs/evidencias-milestone-3.md).
