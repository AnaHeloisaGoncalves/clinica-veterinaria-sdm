# Milestone 4 — API governamental simulada e integração

O governo simulado executa em processo independente, com banco SQLite próprio, criado automaticamente em GOVERNO_DB. A clínica continua com MySQL. O SQLite permite demonstrar persistência e transações do segundo serviço sem compartilhar tabelas ou conexão com a clínica. Este serviço é uma simulação acadêmica.

## Configuração

Atualize as dependências conforme o README. No arquivo .env local, configure:

```dotenv
GOVERNO_URL=http://127.0.0.1:8001
GOVERNO_API_KEY=
GOVERNO_DB=governo.sqlite3
```

Gere uma chave com pelo menos 32 caracteres com `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Coloque o valor em GOVERNO_API_KEY. As duas APIs precisam usar a mesma chave. Se rodarem em diretórios ou computadores diferentes, configure a chave em ambos os ambientes. O arquivo SQLite e o .env ficam fora do Git.

Para uma instalação nova, siga database/banco1.sql. Para um banco da Milestone 3, execute também `SOURCE database/milestone4.sql;` no cliente MySQL. Ajuste o USE se o banco tiver outro nome. O script acrescenta uma restrição única por aplicação de vacina no controle das integrações e pode ser reaplicado.

Inicie os serviços em dois terminais na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_clinica.main:app --port 8000
.\.venv\Scripts\python.exe -m uvicorn api_governo.main:app --port 8001
```

Abra http://127.0.0.1:8000 para usar a clínica e http://127.0.0.1:8001/docs para o Swagger do governo. Os endpoints governamentais exigem o cabeçalho X-API-Key. As operações de escrita também exigem Idempotency-Key, com UUID próprio para cada nova operação.

## Operações do governo

| Método e caminho | Finalidade |
|---|---|
| POST /api/governo/animais | Cadastrar animal identificado por microchip |
| GET /api/governo/animais/{microchip} | Consultar animal e vacinações externas |
| PUT /api/governo/animais/{microchip} | Atualizar cadastro |
| POST /api/governo/vacinacoes-antirrabicas | Receber vacinação antirrábica e cadastrar o animal se necessário |
| GET /api/governo/operacoes/{protocolo} | Recuperar resultado processado |
| PUT /api/governo/simulacao | Ativar ou desativar indisponibilidade com o corpo {"indisponivel": true} |

O Swagger descreve os campos. Uma vacinação deve incluir animal com microchip, nome, espécie e tutor, identificador local da aplicação, nome da vacina, indicador antirrábico verdadeiro, fabricante, lote, data da aplicação e identificação do veterinário.

O banco externo guarda a operação e o efeito clínico na mesma transação. Uma repetição com a mesma chave e conteúdo retorna o protocolo original. A mesma chave com conteúdo diferente retorna 409. Uma segunda chave para o mesmo identificador de aplicação também retorna 409. Os identificadores de vacina pertencem a esta clínica de demonstração.

## Fluxo na clínica

Ao registrar uma vacina antirrábica APLICADA, a API cria a aplicação e a integração PENDENTE na mesma transação MySQL. Depois do commit, tenta o HTTP com timeout de 5 segundos. Vacinas de outros tipos, agendadas ou canceladas não geram a comunicação obrigatória.

O payload é uma cópia dos dados no momento do registro, incluindo o RFID vigente. Novas tentativas usam a mesma linha e a mesma chave, mesmo se o cadastro mudar. O reenvio tem bloqueio transacional para serializar tentativas simultâneas. ENVIADA é um estado transitório dentro da tentativa. Se o processo cair, o MySQL desfaz essa transação e a pendência anterior permanece recuperável.

A operação termina como CONFIRMADA com protocolo, PENDENTE quando há timeout, erro de comunicação ou indisponibilidade, ou FALHA para rejeição de dados ou autenticação. Reenvios confirmados retornam o resultado sem outra chamada externa. O reenvio é manual pela ficha ou por POST /clinica/integracoes/{id}/reenviar.

Na ficha do animal estão a lista de comunicações, as tentativas, o erro e o protocolo. O botão de sincronização cadastra ou atualiza o animal externo. A consulta prévia necessária à sincronização devolve erro ao usuário quando o governo está indisponível. As vacinações continuam sendo registradas como pendentes nesse cenário.

| Rota privada da clínica | Finalidade |
|---|---|
| GET /clinica/integracoes?animal_id=1 | Consultar o controle de integrações |
| POST /clinica/integracoes/{id}/reenviar | Tentar novamente uma comunicação |
| POST /clinica/animais/{id}/sincronizar | Cadastrar ou atualizar animal externo |
| GET /clinica/animais/{id}/governo | Consultar dados e vacinações no governo |

## Demonstração e testes

Use exclusivamente bancos descartáveis, prepare a conta com scripts.demo e configure ALLOW_TEST_DATA=1, DEMO_PASSWORD e GOVERNO_API_KEY nos terminais de testes. As duas APIs devem estar ligadas. TEST_API_URL e GOVERNO_URL permitem escolher portas diferentes.

```powershell
.\.venv\Scripts\python.exe -m unittest tests.entrega2 tests.entrega3 tests.entrega4 -v
.\.venv\Scripts\python.exe -m tests.demo_web
.\.venv\Scripts\python.exe -m tests.demo4_web
```

O teste web requer requirements-dev.txt e o Chromium do Playwright conforme o README. tests/demo4_web.py cria dados fictícios, simula indisponibilidade, registra a aplicação, mostra a pendência e realiza o reenvio na interface. A simulação é desligada ao final. As capturas ficam em docs/evidencias/m4-pendente.png e m4-confirmada.png.

Para demonstrar manualmente, ative a indisponibilidade pelo Swagger governamental, registre uma vacina antirrábica aplicada na clínica e abra a ficha. A vacina fica no histórico e a integração fica pendente. Desative a indisponibilidade e clique em Reenviar comunicação. Confira o protocolo e consulte o animal no governo. Repita o envio para conferir que a quantidade de vacinações externas permanece igual.

Também é possível desligar o processo do governo durante o registro da vacinação e reiniciá-lo antes do reenvio. A chave e os dados persistidos permitem retomar a operação.
