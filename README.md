# Clínica Veterinária · A3 de SDM

Estrutura inicial da Milestone 1. Contém duas APIs Python que sobem em processos e portas separados. O endpoint de saúde verifica se cada processo responde.

## Stack aprovada

| Componente | Tecnologia | Etapa |
|---|---|---|
| Linguagem e colaboração | Python 3.14, Git e GitHub | Milestone 1 |
| APIs | FastAPI, Pydantic e Uvicorn | Base executável na Milestone 1 |
| Banco e migrações | PostgreSQL, SQLAlchemy e Alembic | A partir da Milestone 2 |
| Interface web | HTML, CSS e JavaScript | Milestone 3 |
| Testes | Pytest e Postman | A partir da Milestone 2 |

### Justificativa das tecnologias

- **Python 3.14, Git e GitHub.** Usar a mesma versão de Python nas duas APIs facilita a configuração do ambiente em cada máquina. Git e GitHub permitem versionar código e documentação, dividir o trabalho em branches e revisar as mudanças em pull requests.
- **FastAPI, Pydantic e Uvicorn.** FastAPI organiza as rotas REST e gera a documentação OpenAPI para a clínica e o governo simulado. Pydantic valida os dados recebidos pelas APIs. Uvicorn permite executar cada serviço em um processo e uma porta próprios.
- **PostgreSQL, SQLAlchemy e Alembic.** PostgreSQL aplica as restrições do modelo relacional, como CPF e RFID únicos, e permite gravar a vacinação e a comunicação pendente na mesma transação. SQLAlchemy organiza o acesso ao banco a partir do código Python. Alembic versiona as alterações do esquema para que o grupo aplique as mesmas migrações em cada ambiente.
- **HTML, CSS e JavaScript.** HTML estrutura as telas, CSS permite adaptá-las a diferentes tamanhos de tela e JavaScript valida os formulários e envia as requisições à API privada.
- **Pytest e Postman.** Pytest permite automatizar testes de regras de negócio e integração. Postman permite compartilhar uma coleção de requisições para reproduzir e demonstrar fluxos como autenticação, vacinação e reenvio de pendências.

O [DER e dicionário de dados](docs/modelo-relacional.md) orientam a implementação das tabelas e das migrações. O [resumo da Milestone 1](docs/milestone-1.md) registra os requisitos e a arquitetura.

## Rodar localmente

Instale o Python 3.14 e execute os comandos na pasta raiz. No Windows, confirme que o primeiro comando mostra Python 3.14.x antes de criar o ambiente virtual.

```powershell
python --version
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Abra dois terminais na raiz e execute um comando em cada:

```powershell
.venv\Scripts\python.exe -m uvicorn api_clinica.main:app --port 8000
.venv\Scripts\python.exe -m uvicorn api_governo.main:app --port 8001
```

No Linux ou macOS, use `python3.14 -m venv .venv` e substitua `.venv\Scripts\python.exe` por `.venv/bin/python` nos demais comandos.

| Serviço | Verificação | Swagger |
|---|---|---|
| Clínica | [GET /health](http://127.0.0.1:8000/health) | [Documentação](http://127.0.0.1:8000/docs) |
| Governo simulado | [GET /health](http://127.0.0.1:8001/health) | [Documentação](http://127.0.0.1:8001/docs) |

## Primeiro envio ao GitHub

Se o grupo já tem um repositório, clone-o, crie a branch `docs/milestone-1`, copie os arquivos pertinentes e abra um pull request. Se este for o repositório inicial, crie um repositório vazio no GitHub e use os comandos abaixo na pasta extraída. Substitua a URL pelo endereço do repositório do grupo.

```bash
git init -b main
git add .
git commit -m "chore: initialize A3 milestone 1"
git remote add origin https://github.com/SEU-GRUPO/SEU-REPOSITORIO.git
git push -u origin main
```

Após o primeiro envio, cada integrante clona o mesmo repositório e cria o próprio ambiente virtual. Para novas tarefas, atualize a `main`, crie uma branch, envie os commits e abra um pull request para revisão.
