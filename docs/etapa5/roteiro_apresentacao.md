# Roteiro da apresentação final — Clínica Veterinária SDM

Entrega em 26/11/2026. A apresentação tem sete slides. A instituição, o professor e a duração devem ser confirmados pela equipe antes da apresentação.

## Integrantes

- Ana Heloísa Henrique Gonçalves — RA 12625122852
- Lucas de Carvalho Pereira — RA 12625119694
- Luiz Felipe Nunes dos Santos — RA 12626126986
- João Manuel Fernandes de Geus — RA 1262316776

## Slides e falas sugeridas

1. **Clínica Veterinária.** Apresentar a equipe e o objetivo do projeto A3 de Sistemas Distribuídos e Mobile.
2. **Fluxo de atendimento.** Explicar o cadastro de tutor e endereço, vínculo de animal com RFID, consulta e vacinação.
3. **Arquitetura da solução.** Mostrar frontend, API privada, MySQL, ViaCEP e API governamental simulada com SQLite separado.
4. **Ficha e histórico clínico.** Mostrar o animal e os procedimentos com veterinário responsável e próxima dose.
5. **Indisponibilidade e reenvio.** Demonstrar a vacinação salva localmente durante uma falha externa, a pendência e a confirmação após o reenvio.
6. **Idempotência e rastreabilidade.** Explicar a chave reutilizada, o protocolo original e o teste de resposta perdida após a gravação externa.
7. **Resultados dos testes.** Mostrar a matriz dos 16 cenários, os 11 métodos aprovados e os logs dos dois fluxos no navegador.

## Preparar a demonstração

Use apenas dados fictícios em ambiente de demonstração. Configure os dois serviços e os bancos conforme o README e docs/milestone-4.md. Antes de começar, confirme /health da clínica na porta 8000 e /health do governo na porta 8001. Entre na interface com a conta de demonstração. Deixe um tutor e um animal com RFID preparados.

Abra o Swagger do governo em http://127.0.0.1:8001/docs e preencha X-API-Key com a chave do ambiente local ao executar a rota de simulação. Mantenha a senha e a chave fora do compartilhamento de tela.

## Demonstração ao vivo

1. Na clínica, abra a ficha do animal e mostre o histórico.
2. No Swagger governamental, execute PUT /api/governo/simulacao com o corpo {"indisponivel": true}.
3. Na clínica, abra Atendimento e registre uma vacina antirrábica APLICADA para o animal. Preencha os dados obrigatórios, incluindo fabricante, lote, via, dose/etapa, validade e data de aplicação.
4. Abra novamente a ficha. Mostre a vacina no histórico e a operação VACINA_ANTIRRABICA como PENDENTE, com tentativa e mensagem de indisponibilidade.
5. No Swagger, execute a mesma rota de simulação com {"indisponivel": false}.
6. Na ficha, clique em Reenviar comunicação. Mostre a mudança para CONFIRMADA e o protocolo retornado.
7. No Swagger da clínica, autenticado com token, consulte GET /clinica/animais/{id}/governo. Mostre a aplicação externa.
8. Execute POST /clinica/integracoes/{id}/reenviar para a integração já confirmada. Consulte o animal externo novamente e confira que o número de vacinações e o protocolo permaneceram iguais.
9. Abra a matriz de testes e os logs para mostrar as verificações de senha incorreta, CPF/RFID duplicados e ausência de envio obrigatório para vacinas de outros tipos.

Para retomar a demonstração, use um novo registro de vacinação, pois uma comunicação já confirmada mantém o protocolo original. Ao finalizar, deixe a simulação em indisponivel=false.

## Evidências de contingência

Se o ViaCEP estiver indisponível, mostre o preenchimento manual e a captura da consulta realizada durante o teste. As capturas m4-pendente.png e m4-confirmada.png documentam o fluxo de integração. Os logs demo_web.txt, demo4_web.txt e revalidacao_unittest.txt registram a reexecução de 25/11/2026.

## Perguntas e respostas

**Por que dois bancos?** A clínica e o governo simulado têm persistência própria e se comunicam por HTTP.

**O que ocorre quando o governo cai?** A aplicação local e a pendência já estão gravadas. Um reenvio manual retoma a comunicação.

**Como evitar duplicidade?** O governo grava o efeito e o resultado com a chave de idempotência na mesma transação e retorna o protocolo original em repetições.

**O que os testes comprovam?** Os 16 cenários de aceitação estão associados às asserções de 11 métodos de teste. Os dois fluxos Chromium registram atendimento e recuperação da pendência na interface.

**Quais limites foram documentados?** Governo acadêmico simulado, reenvio manual, teste de tela móvel emulado e previsões de próximas doses sem baixa automática.
