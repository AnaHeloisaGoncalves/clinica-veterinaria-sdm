# Revisão por tópico do A3-SDM

Fonte: A3-SDM.pdf fornecido pelo usuário, 12 páginas, entrega indicada em 26/11/2026.
Revisão local de 25/11/2026. O PDF original não foi modificado. Esta matriz documenta
as exigências e sua implementação na cópia local do projeto.

## 1 e 2. Contexto e objetivo

O sistema deve concentrar a gestão veterinária e demonstrar serviços distribuídos.
A interface HTML/CSS/JavaScript consome a API privada FastAPI por HTTP. A clínica
persiste em MySQL 8 e consulta o ViaCEP por HTTPS. A API governamental simulada é
outro processo FastAPI, com SQLite próprio. Não representa um serviço oficial.
Cada animal possui tutor e microchip; os procedimentos registram o veterinário da
sessão. Aplicações antirrábicas geram comunicação após a gravação local.

## 3. Escopo funcional

| Tópico | O que o sistema deve fazer | Como foi implementado e como demonstrar |
|---|---|---|
| 3.1 Autenticação | Login por e-mail/senha; hash; confirmação; bloquear contas inativas ou não confirmadas; logout; endpoints privados protegidos | `auth.py`: scrypt com salt, JWT e sessão revogável em MySQL; código aleatório com hash e validade de uma hora. Login inclui formulário de confirmação. O envio acadêmico é simulado no log da API. Logout remove a sessão; cada requisição confere situação e confirmação. |
| 3.2 Tutores | Incluir, consultar, alterar e inativar; ID, nome, CPF único/validado, nascimento, e-mail, telefone, endereço, cadastro e situação | Tela Tutores com cadastro, consulta/edição preenchida e inativação confirmada. CPF validado por dígitos verificadores e índice único. API devolve data de cadastro. Atualização de tutor e endereço é transacional: CPF duplicado desfaz também o novo endereço. Inativação preserva registros. |
| 3.3 Endereços/CEP | CEP, logradouro, número, complemento, bairro, cidade, UF e IBGE; preenchimento automático e manual; tratar CEP inexistente e falhas | Consulta ViaCEP ao alterar/sair do CEP, também disponível no botão. Timeout de 5 segundos; respostas 404/503/504 com orientação para preenchimento manual. Endereço pode ser editado junto com tutor. Endereços compartilhados não são alterados silenciosamente: a edição vincula novo registro ao tutor. Endereço próprio da clínica é opcional no enunciado e não é utilizado. |
| 3.4 Espécies | Catálogo com ID, nome, descrição e situação | Tela Catálogos permite criar, editar, consultar descrição/situação e inativar. API possui GET/POST/PUT/DELETE lógico. Carga inicial inclui 38 opções de nomes comuns para animais domésticos, exóticos e silvestres. |
| 3.5 Raças | Catálogo com espécie; compatibilidade; sem raça definida | Catálogos permite criar, editar e inativar. Lista do animal é filtrada por espécie e reiniciada quando ela muda. FK composta `(raca_id, especie_id)` garante compatibilidade também na API. Há SRD para cão e gato; raça é opcional para outros animais. |
| 3.6 Veterinários | Manter nome, CPF, CRMV/UF, e-mail, telefone, hash, confirmação/data, cadastro, situação e último acesso | Tela Veterinários exibe os dados e metadados, sem expor hashes. Administrador cria, edita e inativa profissionais e reenvia confirmação. Usuário comum não pode executar essas operações, inclusive pela API. Mudança de e-mail revoga sessões e exige nova confirmação. Contas novas não recebem privilégio de administrador pela interface. |
| 3.7 Animais/RFID | Cadastro/atualização com tutor, espécie, raça aplicável, nascimento ou idade, sexo, cor, peso, situação; RFID único, data e profissional; substituição com histórico | Tela Animais permite criar, editar e inativar; ficha mostra identificação e histórico. `POST /clinica/animais/{id}/microchip` encerra o vínculo vigente e insere outro numa transação com bloqueio do animal. RFID anterior permanece único e não pode ser reutilizado. Ficha mostra todos os vínculos, datas, situação e profissional. Leitura física não é exigida. |
| 3.8 Consultas | Registrar atendimento e consultar histórico com todos os atributos do enunciado | Formulário Atendimento e histórico por animal: motivo, anamnese, sintomas, diagnóstico, tratamento, medicamentos, peso, temperatura, observações e situação. Responsável vem da sessão. Peso é exigido quando realizada. Aceita AGENDADA, REALIZADA, CANCELADA e NAO_COMPARECEU. |
| 3.9 Vacinas | Registrar aplicações, agendamentos, histórico e próximas doses; classificação antirrábica estruturada | Formulário com nome/tipo, checkbox antirrábica, fabricante, lote, aplicação/agendamento, dose, via, próxima dose, validade e observações. API valida campos por situação e datas. Histórico distingue previsão atrasada/futura. Classificação usa booleano, não inferência pelo nome. |
| 3.10 API privada | REST com regras, validações, persistência, autorização e operações aplicáveis | Cadastros possuem criar/consultar/editar/inativar. Consultas e vacinas preservam registros clínicos; não há exclusão física. Rotas efetivas documentadas em `/docs` e `/openapi.json`. Os caminhos `/api/...` do enunciado são sugestões, não obrigatoriedade de prefixo. |
| 3.11 Governo simulado | Cadastrar/consultar/atualizar por microchip, receber antirrábicas, validar, evitar duplicidade, emitir protocolo e simular falhas | Serviço separado na porta 8001 com SQLite. Exige chave compartilhada, valida modelos/UUID, guarda operações e resultados. Endpoint `/api/governo/simulacao` controla indisponibilidade; payload inválido gera erro de validação. Consulta, atualização e protocolo são acessíveis pela API documentada. |

## 4. Comunicação antirrábica obrigatória

O cadastro local da aplicação e a criação da operação PENDENTE ocorrem na mesma
transação. A chamada HTTP só começa depois do commit. Toda vacina classificada
como antirrábica e APLICADA gera uma operação, mesmo sem cadastro externo anterior.
O payload contém microchip, nome/espécie/tutor, ID da aplicação, nome da vacina,
data, fabricante, lote e nome/CRMV/UF do veterinário.

O governo cadastra o animal quando necessário, persiste a aplicação e devolve
protocolo. A clínica registra a confirmação separadamente. Indisponibilidade ou
timeout mantêm o registro local e a pendência. O botão Reenviar comunicação usa
a mesma chave de idempotência e o mesmo snapshot do payload; inclusive a perda
de resposta após o governo gravar não duplica a aplicação. Não antirrábicas e
vacinas agendadas/canceladas não geram essa comunicação obrigatória.

## 5. Controle das integrações

`integracao_governo` registra ID, animal, vacina opcional, operação, protocolo,
chave de idempotência, situação, solicitação/resposta, tentativas, erro e payload.
O envio passa por ENVIADA dentro da transação protegida por bloqueio; termina em
CONFIRMADA, PENDENTE (falha transitória) ou FALHA (rejeição não transitória).
ENVIADA é um estado transitório, não um painel de progresso em tempo real.
A ficha exibe estado, protocolo, tentativas, erro, chave, datas e vínculo da vacina.
Reenvio manual atende ao enunciado, que permite tentativas automáticas ou manuais.

## 6. Modelo de dados

O esquema executável atual é `database/banco1.sql` (MySQL 8). Ele contém as dez
entidades obrigatórias e uma tabela técnica de sessão. O DER está em
`docs/modelo-relacional.md`; o texto PostgreSQL ali é a proposta histórica.

| Tabela atual | Chave primária e relacionamentos | Unicidade/integridade relevante |
|---|---|---|
| endereco | id | Referenciado por tutor |
| tutor | id; endereco_id → endereco | cpf único |
| especie | id | Referenciada por raça/animal |
| raca | id; especie_id → especie | par (id, especie_id) único |
| veterinario | id | cpf, email e (numero_crmv, uf_crmv) únicos; hash scrypt |
| animal | id; tutor_id → tutor; especie_id → especie; (raca_id, especie_id) → raca | nascimento ou idade, peso positivo |
| vinculo_microchip | id; animal_id → animal; veterinario_id → veterinario | RFID único inclusive histórico; coluna gerada única limita a um vínculo vigente por animal |
| consulta | id; animal_id → animal; veterinario_id → veterinario | situações permitidas; realizada exige peso |
| vacina | id; animal_id → animal; veterinario_id → veterinario | situações/datas e dados de lote da aplicação |
| integracao_governo | id; animal_id → animal; vacina_id → vacina | chave de idempotência e vacina_id únicos |
| sessao | id; veterinario_id → veterinario | expiração e revogação |

Cada banco governa sua integridade: o SQLite governamental não depende de FK para
o MySQL. A comunicação entre eles é HTTP. Nenhuma migração destrutiva foi necessária
para esta revisão: as tabelas já tinham campos para histórico e metadados.

## 7 e 8. Requisitos não funcionais e tecnologias

- Interface responsiva HTML/CSS/JS; teste de edição em largura de 390 px.
- FastAPI/Pydantic separam modelos, autenticação, cadastros, clínica e integração.
- MySQL 8 aplica FKs, índices únicos e checks; queries usam parâmetros.
- Validação HTML/JS e validação no servidor, com tratamento de erros HTTP e rede.
- Senhas de profissionais somente em hash; segredos de serviço no `.env` ignorado pelo Git.
- Swagger/OpenAPI documenta as APIs; Git preserva alterações locais para revisão.
- Governo simulado com persistência SQLite e API key; dados de teste são fictícios.
- Python 3.14 e dependências fixadas nos arquivos requirements do repositório.

## 9. Testes obrigatórios e adicionais

Os 16 cenários do enunciado estão mapeados em `docs/etapa5/matriz_testes.md`.
A revisão executa novamente `tests.entrega2`, `tests.entrega3` e `tests.entrega4`.
As novas suítes `tests.requisitos_a3`, `tests.edicao_animal_web` e `tests.gestao_web`
cobrem adicionalmente atualização de animal, compatibilidade em PUT, edição de
tutor/endereço e rollback, metadados, permissões, confirmação, substituição de
RFID com concorrência, cancelamento/erro de edição e os novos fluxos no navegador.

Execute `.venv/bin/python -m scripts.testes_isolados`. O executor cria um banco
MySQL com nome aleatório, inicia duas APIs em portas livres e um SQLite separado,
carrega dados fictícios, executa testes e encerra os processos. Só o banco de teste
criado nessa execução é removido ao final. Logs e capturas ficam em `.local-run/`.
O usuário de testes deve poder criar/remover bancos; use TEST_DB_ADMIN_USER e
TEST_DB_ADMIN_PASSWORD quando necessário. A base `clinica_vet` não é usada nos testes.

Resultado da revisão: **17 métodos aprovados em 4,011 segundos**. O log foi salvo
em `docs/etapa5/evidencias/revisao-a3/testes.txt`, junto com quatro capturas dos
novos fluxos. Na aplicação reiniciada, login e saúde dos serviços retornaram 200.
ViaCEP real: `01001000` retornou 200 e endereço da Praça da Sé; `00000000` retornou
404 com orientação para preenchimento manual. Os testes de timeout e
indisponibilidade foram executados com respostas controladas.

## 10. Entregáveis e execução no Mac

| Exigência | Artefato |
|---|---|
| Requisitos/arquitetura | Este documento, `docs/milestone-1.md` e README |
| DER/modelo relacional | `docs/modelo-relacional.md`, tabela acima e `database/banco1.sql` |
| Frontend e APIs | `frontend/`, `api_clinica/`, `api_governo/` |
| Inicialização | `database/banco1.sql`, `scripts.demo`, `scripts.catalogos`, `.env.example` |
| Documentação de endpoints | `/docs` e `/openapi.json` de cada serviço |
| Testes/evidências | `tests/`, executor isolado e logs/capturas desta revisão |
| Relatório | Este documento e adendo à matriz/relatório da etapa 5 |
| Instalação | README e scripts `iniciar-mac.command` / `parar-mac.command` |
| Demonstração | `docs/etapa5/roteiro_apresentacao.md` com adendo desta revisão |

No Mac já configurado, abrir `iniciar-mac.command` e manter o Terminal aberto.
O script inicia o MySQL local e as APIs. A interface fica em http://127.0.0.1:8000,
a documentação clínica em /docs e o governo em http://127.0.0.1:8001/docs.
Os códigos de confirmação simulados aparecem em `.local-run/clinica.log`.
Depois de mudanças em Python, reiniciar os serviços; mudanças nas telas exigem
recarregar a página. Os scripts de inicialização locais dependem da pasta irmã
`mysql-runtime`; uma nova máquina deve seguir a instalação do README.

## 11 e 12. Avaliação e resultado esperado

A avaliação do professor distribui pesos de 15% para modelagem, 20% API privada,
10% CEP, 20% governo/sincronização, 10% autenticação, 10% interface e 15% testes,
documentação e demonstração. Esses pesos orientam a revisão; não são uma nota
atribuída ao projeto nem garantia de aprovação.

O fluxo demonstrável é login confirmado → tutor/CEP → animal/RFID → consulta →
vacina → histórico → integração/protocolo. Demonstrar indisponibilidade, pendência
e reenvio sem duplicidade é essencial. Complementar com edição de tutor/animal,
troca de microchip, manutenção dos catálogos e bloqueio de profissional inativo.

Limites explícitos: e-mail e governo são simulados; ViaCEP exige internet; testes
automatizados de falha usam respostas controladas; previsões de próximas doses
não são baixadas automaticamente por uma aplicação posterior; o projeto é uma
demonstração local e não passou por homologação de produção.
