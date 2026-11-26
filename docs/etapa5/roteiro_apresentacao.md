# Roteiro da apresentação final — Clínica Veterinária SDM

## Complemento da revisão A3 no Mac

1. Em Tutores, abrir Consultar / editar, alterar telefone/endereço e salvar.
2. Em Animais, editar dados e mostrar que trocar espécie limpa a seleção de raça.
3. Na ficha, substituir o RFID e mostrar os vínculos antigo/novo com data e profissional.
4. Em Catálogos, mostrar descrição, espécie da raça, edição e inativação.
5. Em Veterinários, cadastrar um profissional como administrador; mostrar confirmação
   pendente e o código no e-mail simulado em `.local-run/clinica.log`.
6. Na tela de login, abrir Confirmar minha senha e enviar o código. Demonstrar
   bloqueio antes da confirmação e após a inativação do profissional.
7. Mostrar o log de testes da revisão, separado das evidências históricas abaixo.

Para a parte distribuída, registrar antirrábica com o governo simulado indisponível,
mostrar vacina local + operação pendente, reativar o governo e reenviar. Mostrar
protocolo e chave de idempotência na ficha. Não usar dados pessoais reais.

**Sugestão:** 7 slides, aproximadamente 6–9 minutos (ajustar ao tempo estipulado pelo professor).

## Slide 1 — Identificação
**Título:** Clínica Veterinária SDM — Milestone 5: entrega final  
Conteúdo: equipe, disciplina, instituição e data.  
**Fala:** "Apresentaremos o sistema desenvolvido, sua arquitetura, os fluxos principais e os testes realizados."

## Slide 2 — Problema e objetivo
Conteúdo: organização de tutores/animais, agendamento, registros clínicos, vacinas e integração governamental.  
**Fala:** "O objetivo é concentrar os cadastros e os registros clínicos em uma aplicação com validações e rastreabilidade."

## Slide 3 — Arquitetura
Conteúdo: frontend web → API da clínica (FastAPI) → MySQL; API da clínica ↔ API do governo simulado → SQLite; consulta CEP → ViaCEP.  
**Fala:** "Separamos o sistema clínico da simulação governamental para exercitar integração e recuperação de falhas."

## Slide 4 — Demonstração funcional
Conteúdo: login → tutores/CEP → animal/RFID → consulta/vacina → ficha/histórico.  
**Fala:** "Mostraremos o fluxo de atendimento com dados fictícios."

## Slide 5 — Integração governamental
Conteúdo: envio de vacinação antirrábica, status de pendência, protocolo de confirmação e reenvio sem duplicidade.  
**Fala:** "A integração registra respostas e permite demonstrar contingência quando o governo simulado está indisponível."

## Slide 6 — Validação e problemas resolvidos
Conteúdo: testes manuais concluídos; suítes `tests.entrega2`, `tests.entrega3` e `tests.entrega4` com OK; Playwright `tests.demo_web` e `tests.demo4_web` sem erros, conforme relato; correção das portas e isolamento do banco de testes.  
**Fala:** "A falha inicial de integração veio da execução da API da clínica na porta destinada ao governo; a divergência do login nos testes veio do uso de bancos diferentes. Corrigimos a configuração e repetimos os testes."  
**Nota:** mostrar log real e não inventar quantidade de testes.

## Slide 7 — Conclusão
Conteúdo: objetivos alcançados no ambiente de teste; documentação e evidências; limites: ambiente local, testes sem carga ou auditoria de produção.  
**Fala:** "A entrega demonstra o funcionamento integrado das funcionalidades e o processo de validação aplicado durante a etapa final."

## Demonstração ao vivo — ordem recomendada
1. Confirmar os dois serviços em `/health` antes de iniciar.
2. Fazer login usando a conta de demonstração.
3. Mostrar tutor e animal já cadastrados (evita depender de digitação ao vivo).
4. Mostrar histórico de consulta/vacina.
5. Mostrar confirmação governamental/protocolo; manter screenshots de contingência como plano B.

## Perguntas prováveis
- **Por que dois bancos?** MySQL armazena a clínica; SQLite mantém o estado do governo simulado.
- **Como tratam falhas de conexão?** Registro de pendências e reenvio conforme fluxo da Milestone 4.
- **Como evitar duplicidade?** Idempotência na comunicação governamental.
- **Por que banco separado de testes?** Para não alterar a base de demonstração durante testes que gravam registros.
- **O que foi corrigido na Milestone 5?** Inicialização das APIs nas portas corretas e alinhamento do banco usado pela API e pelos testes.
