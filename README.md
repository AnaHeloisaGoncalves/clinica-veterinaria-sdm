# Clínica Veterinária · A3 de SDM

## Revisão local dos requisitos A3 — 25/11/2026

Veja a [matriz por tópico do PDF](docs/requisitos-a3-revisados.md), com as exigências,
implementação, modelo MySQL atual e instruções de teste. Esta revisão inclui edição
e inativação de tutores, manutenção de veterinários/catálogos, confirmação de senha
na tela e substituição de microchip com histórico. Testes isolados:
`.venv/bin/python -m scripts.testes_isolados` (dependências de desenvolvimento e
Chromium do Playwright necessários). No Mac configurado, abra `iniciar-mac.command`
e mantenha a janela do Terminal aberta durante a demonstração.

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

Na tela de login, o botão **Criar minha conta de veterinário** permite o cadastro público do profissional (nome, CPF, e-mail, CRMV e senha). A conta é gravada diretamente no MySQL com senha protegida por scrypt, fica ativa e confirmada para o primeiro acesso e nunca recebe privilégios de administrador. Não há envio de e-mail nesse fluxo. Os campos de senha possuem o botão **Mostrar senha/Ocultar senha**.

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
e os catálogos de cães e gatos com 40 e 20 opções de raça, respectivamente,
incluindo a opção de cadastro Sem raça definida (SRD). Não apaga nem redefine cadastros existentes.
Para carregar apenas esses catálogos, sem criar a conta demo, execute
`.venv/bin/python -m scripts.catalogos` no macOS. A carga pode ser repetida sem
duplicar os nomes já cadastrados e preserva registros inativos.

O catálogo também inclui animais domésticos, silvestres e exóticos, como coelhos,
roedores, furões, aves, quelônios, lagartos e serpentes. Os nomes são opções de
identificação no cadastro clínico; nomes comuns abrangentes devem ser detalhados
na ficha. Para espécies sem catálogo de raças, deixe o campo opcional de raça vazio.
Use somente um banco local de demonstração. Para contas normais, siga o fluxo de
criação e confirmação da Milestone 2.

O fluxo demonstrativo é: login → Tutores → consulte `01001000` → complete número/complemento e cadastre → Animais → selecione tutor/espécie/raça opcional e informe RFID → Atendimento → registre consulta e vacina → Animais → **Ficha de [nome]**.

Para atualizar um animal, acesse **Animais → Editar [nome]**, altere os dados e
clique em **Salvar alterações**. É possível editar nome, tutor, espécie, raça,
sexo, cor, peso, nascimento e idade estimada. A troca de espécie limpa a raça
selecionada e mostra apenas opções compatíveis. O RFID e os históricos são
preservados. **Cancelar edição** descarta as alterações não salvas.

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

Em Atendimento, toda consulta exige um motivo e toda vacinação exige a dose ou etapa (por exemplo, primeira dose ou reforço). A vacina aplicada exige
data de aplicação, fabricante, lote, via de aplicação e validade do lote; a agendada
exige data de agendamento. Próxima dose e validade do lote são conferidas quando
informadas. Consultas realizadas exigem o peso registrado; a situação também permite
`NAO_COMPARECEU`. A ficha mostra os detalhes e diferencia
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

## Milestone 4

A clínica comunica aplicações antirrábicas ao governo simulado e mostra pendências e protocolos na ficha do animal. Siga a [configuração e demonstração da Milestone 4](docs/milestone-4.md) para configurar a chave compartilhada, aplicar a atualização do banco e executar os testes.

## Milestone 5 — entrega final

A documentação está em **[docs/etapa5](docs/etapa5/README.md)**, incluindo o [relatório](docs/etapa5/relatorio_final.md), a [matriz de 16 cenários](docs/etapa5/matriz_testes.md), oito capturas de tela e o log de **11 testes automatizados aprovados em 8,102 segundos**.

A revalidação de 25/11/2026 está em [revalidacao_unittest.txt](docs/etapa5/evidencias/revalidacao_unittest.txt). Os fluxos de navegador têm logs próprios em [demo_web.txt](docs/etapa5/evidencias/demo_web.txt) e [demo4_web.txt](docs/etapa5/evidencias/demo4_web.txt). A identificação da equipe e o roteiro da demonstração estão na documentação da Etapa 5.

Para preparar também `gestor@clinica.test`, defina `DEMO_PASSWORD` no `.env` local e execute `python -m scripts.demo` em um banco de demonstração.
