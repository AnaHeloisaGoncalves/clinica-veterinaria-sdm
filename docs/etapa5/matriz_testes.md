# Matriz de testes e rastreabilidade — Milestone 5

**Legenda:** `APROVADO (relato)` = confirmação verbal do executor; `ANEXAR EVIDÊNCIA` = falta o artefato para comprovação.

| ID | Categoria | Cenário | Resultado esperado | Status | Evidência sugerida |
|---|---|---|---|---|---|
| CT-01 | Autenticação | Login válido | Sessão autenticada | Aprovado (relato) | `evidencias/login.png` |
| CT-02 | Cadastro | Tutor | Tutor gravado no MySQL | Aprovado (relato) | `evidencias/tutor.png` |
| CT-03 | Integração externa | CEP | Endereço preenchido/contingência | Aprovado (relato) | `evidencias/cep.png` |
| CT-04 | Cadastro | Animal com tutor, espécie e RFID | Animal gravado e vinculado | Aprovado (relato) | `evidencias/animal.png` |
| CT-05 | Clínica | Consulta | Atendimento gravado | Aprovado (relato) | `evidencias/consulta.png` |
| CT-06 | Clínica | Vacina | Aplicação gravada | Aprovado (relato) | `evidencias/vacina.png` |
| CT-07 | Clínica | Histórico | Consulta e vacina apresentados | Aprovado (relato) | `evidencias/historico.png` |
| CT-08 | Integração | Governo disponível | Confirmação/protocolo | Aprovado (relato) | `evidencias/integracao.png` |
| CT-09 | Automação API | `tests.entrega2` | Testes de autenticação/cadastros OK | Aprovado (relato) | `evidencias/unittest.txt` |
| CT-10 | Automação API | `tests.entrega3` | Testes clínicos OK | Aprovado (relato) | `evidencias/unittest.txt` |
| CT-11 | Automação API | `tests.entrega4` | Integração, pendência e idempotência OK | Aprovado (relato) | `evidencias/unittest.txt` |
| CT-12 | Automação E2E | `tests.demo_web` | Fluxo web termina sem erros | Aprovado (relato) | `evidencias/demo_web.txt` + imagens |
| CT-13 | Automação E2E | `tests.demo4_web` | Fluxo web governo termina sem erros | Aprovado (relato) | `evidencias/demo4_web.txt` + imagens |

## Critérios de aceite
- Suítes automatizadas sem falhas, com logs identificados por data e ambiente.
- Fluxos de navegador demonstráveis com dados fictícios.
- APIs iniciadas separadamente nas portas 8000 e 8001.
- Banco de testes separado do banco principal.
- Nenhuma senha ou token exposto na documentação ou no GitHub.

## Evidências pendentes de anexação
- [ ] Log completo da suíte `unittest`, com total e duração reais.
- [ ] Saída de `tests.demo_web` e `tests.demo4_web`, se disponível.
- [ ] Capturas do Playwright em `docs/evidencias/` copiadas para a entrega ou referenciadas por caminho.
- [ ] Prints dos fluxos básicos, se exigidos pelo professor.
