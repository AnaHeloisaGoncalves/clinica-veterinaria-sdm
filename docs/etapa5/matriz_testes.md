# Matriz de testes e rastreabilidade — Milestone 5

**Atualização:** 25/11/2026 · **Execução:** [11 testes aprovados em 8,102 segundos](evidencias/testes_automatizados.txt) (`OK`).

**Origem dos 16 cenários:** consolidação dos requisitos RF01–RF10 descritos em [Milestone 1](../milestone-1.md), dos testes das entregas 2–4 e dos fluxos visuais. O enunciado acadêmico integral não está presente neste repositório; os 16 itens abaixo são a rastreabilidade consolidada, **não uma transcrição literal** de uma lista externa indisponível.

| ID | Requisito | Cenário | Teste ou evidência verificável | Status |
|---|---|---|---|---|
| CT-01 | RF01 | Login válido e confirmação | `test_autenticacao_e_cadastros`; [log](evidencias/testes_automatizados.txt); [painel](evidencias/01-painel.png) | Aprovado |
| CT-02 | RF01 | Senha errada, conta não confirmada/inativa, token ausente, logout | `test_autenticacao_e_cadastros`; `test_sem_token_e_logout`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-03 | RF02 | Cadastro, atualização e inativação de tutor; CPF duplicado | `test_autenticacao_e_cadastros`; `test_tutor_duplicado_nao_deixa_endereco`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-04 | RF03 | ViaCEP válido e preenchimento | `tests.demo_web`; [cadastro e CEP](evidencias/03-tutor-cep.png); [resumo manual](evidencias/testes_manuais_resumo.txt) | Aprovado |
| CT-05 | RF03 | CEP inexistente, timeout e indisponibilidade | `test_cep_inexistente_timeout_indisponivel`; [log](evidencias/testes_automatizados.txt); [CEP](evidencias/02-cep-inexistente.png) | Aprovado |
| CT-06 | RF04 | Espécies, raças e compatibilidade | `test_autenticacao_e_cadastros`; `test_fluxo_clinico_e_rfid`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-07 | RF05 | Animal vinculado ao tutor e RFID único | `test_fluxo_clinico_e_rfid`; [log](evidencias/testes_automatizados.txt); [RFID repetido](evidencias/04-rfid-duplicado.png) | Aprovado |
| CT-08 | RF05 | Identificação e sincronização de microchip | `test_sincronizacao_cadastro_atualizacao`; [log](evidencias/testes_automatizados.txt); [M4](../evidencias-milestone-4.md) | Aprovado na suíte |
| CT-09 | RF06 | Consulta e campos clínicos obrigatórios | `test_campos_clinicos_obrigatorios`; `test_datas_situacao_e_responsavel`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-10 | RF06 | Agendamento, cancelamento, atraso, ausência | `test_agendamento_cancelamento_e_atraso`; [log](evidencias/testes_automatizados.txt); [M3](../evidencias-milestone-3.md) | Aprovado |
| CT-11 | RF07 | Vacina: dados obrigatórios e antirrábica | `test_campos_clinicos_obrigatorios`; `test_fluxo_clinico_e_rfid`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-12 | RF06–RF07 | Histórico, próximas doses e layout responsivo | `test_fluxo_clinico_e_rfid`; [histórico](evidencias/05-historicos.png); [celular](evidencias/06-celular.png) | Aprovado |
| CT-13 | RF08 | Cadastro, atualização e consulta no governo simulado | `test_sincronizacao_cadastro_atualizacao`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-14 | RF09 | Envio da antirrábica aplicada; exclusões previstas | `test_rejeicao_corrigida_e_vacinas_sem_comunicacao`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-15 | RF10 | Indisponibilidade, pendência, reenvio e protocolo | `test_integracao_falha_reenvio_idempotencia`; [pendente](evidencias/m4-pendente.png); [confirmada](evidencias/m4-confirmada.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-16 | RF08–RF10 | Idempotência, resposta perdida, concorrência e conflito 409 | `test_integracao_falha_reenvio_idempotencia`; [log](evidencias/testes_automatizados.txt); [M4](../evidencias-milestone-4.md) | Aprovado |

## Evidências publicadas

- [Log de testes automatizados](evidencias/testes_automatizados.txt): **11 aprovados**, **8,102 segundos**, resultado `OK`.
- [Resumo manual](evidencias/testes_manuais_resumo.txt).
- Playwright clínico: [01-painel.png](evidencias/01-painel.png), [02-cep-inexistente.png](evidencias/02-cep-inexistente.png), [03-tutor-cep.png](evidencias/03-tutor-cep.png), [04-rfid-duplicado.png](evidencias/04-rfid-duplicado.png), [05-historicos.png](evidencias/05-historicos.png) e [06-celular.png](evidencias/06-celular.png).
- Playwright governamental: [m4-pendente.png](evidencias/m4-pendente.png) e [m4-confirmada.png](evidencias/m4-confirmada.png).

**Interpretação:** os 11 métodos da suíte automatizada cobrem diversos cenários. Os 16 itens da matriz não representam 16 métodos de teste distintos. As imagens complementam as verificações; não substituem as asserções da suíte.
