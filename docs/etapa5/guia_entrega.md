# Guia de finalização e entrega no GitHub

## 1. Conferir evidências (sem repetir testes apenas por fotos)
No VS Code, abra a pasta `docs/evidencias/` existente no projeto. Consulte as capturas que os scripts Playwright geraram. Acrescente em `docs/etapa5/evidencias/` apenas os registros relevantes, com dados fictícios. Adicione o log final real `unittest.txt` quando disponível. Não fabrique resultados ou números.

Para registrar uma nova execução, se realmente necessário, **somente com ambiente descartável confirmado**, execute no terminal com `DB_NAME=clinica_vet_testes`:

```powershell
$env:ALLOW_TEST_DATA = "1"
$env:DB_NAME = "clinica_vet_testes"
$env:GOVERNO_DB = "governo_testes.sqlite3"
.\.venv\Scripts\python.exe -m unittest tests.entrega2 tests.entrega3 tests.entrega4 -v 2>&1 | Tee-Object -FilePath "docs\etapa5\evidencias\unittest.txt"
```

**Atenção:** executar a suíte novamente grava dados fictícios adicionais. Se já existe uma saída anterior, prefira salvá-la sem repetir a execução.

## 2. Restaurar o ambiente principal após os testes
1. Interrompa as duas APIs com `Ctrl + C`.
2. Restaure o `.env` original, se preservou cópia: `Copy-Item ..\clinica-sdm-env-backup.local .env -Force`.
3. No terminal PowerShell, remova variáveis temporárias que possam sobrescrever o `.env`:

```powershell
Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
Remove-Item Env:GOVERNO_DB -ErrorAction SilentlyContinue
Remove-Item Env:ALLOW_TEST_DATA -ErrorAction SilentlyContinue
```

4. Confirme `DB_NAME=clinica_vet` no `.env` e verifique a conexão antes de iniciar servidores novamente.
5. Reinicie as APIs nas portas 8000 e 8001.

## 3. Verificar o que será publicado
**Incluir:** documentação da Milestone 5, scripts do projeto, testes existentes, evidências apropriadas e README atualizado com link para `docs/etapa5/README.md`.

**Não incluir:** `.env`, cópia de backup do `.env`, `.venv/`, credenciais, tokens, banco real, SQLite com dados pessoais, dumps de produção. Confira `.gitignore` e também os arquivos já rastreados antes de publicar.

## 4. Atualizar o repositório compartilhado
Para não sobrescrever trabalho do grupo, recomendação simples:
1. Copie `docs/etapa5/` para o projeto.
2. Faça backup local da pasta do projeto.
3. Se tiver acesso de escrita ao repositório, envie **somente os arquivos novos** pela interface do GitHub (Add file → Upload files) ou por um branch/PR. Preserve os demais arquivos.
4. Escreva uma mensagem de alteração, por exemplo: `docs: adiciona relatório, matriz e roteiro da Milestone 5`.
5. Confirme no GitHub que os arquivos aparecem em `docs/etapa5/`.

Se você ainda não tiver acesso de escrita ao repositório do grupo, envie o pacote a um integrante responsável pela publicação ou solicite inclusão como colaborador. Não publique cópias com segredos.

## 5. Checklist final
- [ ] Logs e capturas reais anexados.
- [ ] Relatório revisado pelo grupo; nenhuma contagem inventada.
- [ ] Nomes e responsabilidades dos integrantes preenchidos na apresentação.
- [ ] Links para documentação incluídos no README principal.
- [ ] Ambiente principal restaurado após os testes.
- [ ] Arquivos enviados ao GitHub compartilhado e conferidos.
- [ ] Demonstração ensaiada antes da data de entrega.
