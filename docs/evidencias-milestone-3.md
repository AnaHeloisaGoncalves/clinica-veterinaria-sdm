# Testes da Milestone 3

Execução em 16/11/2026, no Windows, com Python 3.14.10 e MySQL 8.4.13 local.
Os cadastros usados são fictícios. As capturas não contêm senha ou token.

## API e banco

Comando: `python -m unittest tests.entrega2 tests.entrega3 -v`, com `ALLOW_TEST_DATA=1`.
Resultado: **7 testes passaram** (1 da Milestone 2 e 6 da Milestone 3).

- Autenticação, confirmação de senha, conta inativa, CRUD, CPF e raça incompatível: regressão da Milestone 2.
- Consulta e vacinação persistidas no MySQL, com veterinário da sessão.
- Animal sem raça e sem nascimento, usando idade estimada.
- RFID duplicado retorna 409 e mensagem específica.
- Vacina com e sem próxima dose; classificação antirrábica preservada.
- Vacina aplicada exige fabricante, lote, via e validade; consulta realizada exige peso.
- Datas incoerentes, situação inválida e tentativa de escolher outro veterinário rejeitadas com 422.
- Consulta com `NAO_COMPARECEU` registrada e apresentada no histórico.
- Agendamento atrasado identificado; vacina cancelada excluída das previsões.
- CEP inexistente, timeout e serviço indisponível: respostas externas simuladas nos testes automatizados.
- Acesso sem token e token revogado rejeitados.
- CPF repetido não deixa endereço órfão.

## Fluxo no navegador

Comando: `python -m tests.demo_web`, com `ALLOW_TEST_DATA=1`.
Resultado: **fluxo completo passou**, sem erros JavaScript não tratados.

A demonstração usa Chromium, API local e MySQL reais. As consultas aos CEPs
01001000 e 00000000 foram feitas no ViaCEP real. O teste de sessão expirada
simula uma resposta 401 no navegador; a revogação real é verificada na API.

| Etapa | Captura |
|---|---|
| Login e painel | [01-painel.png](evidencias/01-painel.png) |
| CEP inexistente e campos editáveis | [02-cep-inexistente.png](evidencias/02-cep-inexistente.png) |
| Endereço retornado pelo ViaCEP | [03-tutor-cep.png](evidencias/03-tutor-cep.png) |
| Rejeição do RFID repetido | [04-rfid-duplicado.png](evidencias/04-rfid-duplicado.png) |
| Consulta, vacinas e próximas doses | [05-historicos.png](evidencias/05-historicos.png) |
| Ficha em viewport de celular (390 × 844) | [06-celular.png](evidencias/06-celular.png) |

Também foram verificados: troca de espécie limpa a raça, datas opcionais em branco,
logout e retorno ao login quando a sessão deixa de ser válida. O teste de celular
usa emulação de tamanho no Chromium, não um aparelho físico.

## Limites desta etapa

O registro de vacinação é local. A comunicação com o governo fica para a Milestone 4.
As próximas doses são previsões informadas pelo veterinário. Uma nova aplicação
não encerra automaticamente uma previsão anterior; a ficha orienta conferir o histórico.
