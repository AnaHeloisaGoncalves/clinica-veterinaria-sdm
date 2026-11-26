# Matriz de testes obrigatórios — Milestone 5

## Reexecução local de 25/11/2026

As suítes abaixo foram reexecutadas junto com as regressões da revisão A3:
**17 métodos aprovados em 4,011 segundos**. Veja o [log atual](evidencias/revisao-a3/testes.txt).
Os 16 cenários continuam distribuídos pelos métodos das entregas 2, 3 e 4.
As seis verificações adicionais são quatro métodos em `tests.requisitos_a3`, um
em `tests.edicao_animal_web` e um em `tests.gestao_web`. Cobrem atualização,
rollback, RFID/histórico/concorrência, autorização, confirmação e telas novas.
ViaCEP válido/inexistente também foi conferido contra o serviço real no Mac após
reiniciar a aplicação. As referências de 11 testes abaixo são evidências históricas.

**Fonte:** seção 9, “Testes obrigatórios”, do enunciado acadêmico fornecido pela equipe. Os 16 cenários estão na ordem original.  
**Execução automatizada:** [11 testes aprovados em 8,102 segundos](evidencias/testes_automatizados.txt), resultado `OK`.

> Os 16 cenários representam verificações de aceitação, não 16 métodos de teste individuais. Um método automatizado pode verificar mais de um cenário. As capturas complementam os testes.

| ID | Cenário obrigatório do enunciado | Teste ou evidência existente | Resultado |
|---|---|---|---|
| CT-01 | Login de veterinário ativo e com senha confirmada. | `test_autenticacao_e_cadastros`; [log](evidencias/testes_automatizados.txt); [painel](evidencias/01-painel.png) | Aprovado |
| CT-02 | Bloqueio de veterinário inativo. | `test_autenticacao_e_cadastros`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-03 | Bloqueio de veterinário com senha não confirmada. | `test_autenticacao_e_cadastros`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-04 | Rejeição de senha incorreta. | `test_autenticacao_e_cadastros`; [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-05 | Cadastro de tutor e validação de CPF duplicado. | `test_autenticacao_e_cadastros` e `test_tutor_duplicado_nao_deixa_endereco`; [log](evidencias/testes_automatizados.txt); [tutor](evidencias/03-tutor-cep.png) | Aprovado |
| CT-06 | Consulta de CEP válido e tratamento de CEP inexistente. | `test_cep_inexistente_timeout_indisponivel`; [CEP válido](evidencias/03-tutor-cep.png); [CEP inexistente](evidencias/02-cep-inexistente.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-07 | Cadastro de animal e vínculo de microchip. | `test_fluxo_clinico_e_rfid`; [log](evidencias/testes_automatizados.txt); [resumo manual](evidencias/testes_manuais_resumo.txt) | Aprovado |
| CT-08 | Rejeição de microchip já utilizado. | `test_fluxo_clinico_e_rfid`; [RFID duplicado](evidencias/04-rfid-duplicado.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-09 | Registro de consulta e consulta ao histórico clínico. | `test_fluxo_clinico_e_rfid` e `test_campos_clinicos_obrigatorios`; [histórico](evidencias/05-historicos.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-10 | Registro de vacina e consulta às próximas doses. | `test_fluxo_clinico_e_rfid` e `test_campos_clinicos_obrigatorios`; [histórico e doses](evidencias/05-historicos.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-11 | Cadastro e atualização de animal na API governamental simulada. | `test_sincronizacao_cadastro_atualizacao`; [log](evidencias/testes_automatizados.txt); [detalhes M4](../evidencias-milestone-4.md) | Aprovado |
| CT-12 | Envio obrigatório de vacina antirrábica. | `test_integracao_falha_reenvio_idempotencia` e `test_rejeicao_corrigida_e_vacinas_sem_comunicacao`; [log](evidencias/testes_automatizados.txt); [confirmação](evidencias/m4-confirmada.png) | Aprovado |
| CT-13 | Ausência de comunicação obrigatória para vacina não antirrábica. | `test_integracao_falha_reenvio_idempotencia` (aplicação com `antirrabica=False` mantém a contagem de integrações); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-14 | Indisponibilidade da API governamental e registro de pendência. | `test_integracao_falha_reenvio_idempotencia`; [pendência](evidencias/m4-pendente.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-15 | Reenvio de comunicação pendente e confirmação posterior. | `test_integracao_falha_reenvio_idempotencia`; [pendente](evidencias/m4-pendente.png); [confirmada](evidencias/m4-confirmada.png); [log](evidencias/testes_automatizados.txt) | Aprovado |
| CT-16 | Repetição de solicitação sem duplicidade de vacinação no serviço externo. | `test_integracao_falha_reenvio_idempotencia`; [log](evidencias/testes_automatizados.txt); [detalhes de idempotência M4](../evidencias-milestone-4.md) | Aprovado |

## Evidências publicadas

- [Log completo dos testes automatizados](evidencias/testes_automatizados.txt): 11 métodos aprovados em 8,102 segundos.
- [Resumo dos testes manuais](evidencias/testes_manuais_resumo.txt).
- Imagens da interface: [painel](evidencias/01-painel.png), [CEP inexistente](evidencias/02-cep-inexistente.png), [cadastro de tutor e CEP](evidencias/03-tutor-cep.png), [RFID duplicado](evidencias/04-rfid-duplicado.png), [históricos](evidencias/05-historicos.png), [interface móvel](evidencias/06-celular.png).
- Integração: [pendente](evidencias/m4-pendente.png) e [confirmada](evidencias/m4-confirmada.png).

**Critério de leitura:** as linhas aprovadas correspondem à suíte de testes executada e às evidências registradas. As imagens comprovam estados da interface; bloqueios, validações e idempotência são demonstrados sobretudo pelas asserções automatizadas.
