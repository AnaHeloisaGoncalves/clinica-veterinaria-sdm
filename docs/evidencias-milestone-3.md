# Evidências da Milestone 3

## Fluxo principal

1. Login de veterinário confirmado na tela inicial.
2. `01001000` consultado no ViaCEP; logradouro, bairro, cidade, UF e IBGE são preenchidos automaticamente; número e complemento permanecem para preenchimento manual.
3. Tutor fictício cadastrado.
4. Animal fictício cadastrado com tutor, espécie, raça opcional e RFID.
5. Consulta registrada com data/hora, situação, diagnóstico e tratamento.
6. Vacina registrada localmente com situação, classificação `antirrabica` e próxima dose.
7. Ficha do animal exibe consultas, vacinas e próximas doses.

## Erros cobertos

- `00000000`: ViaCEP informa CEP não encontrado e a edição manual continua disponível.
- RFID já utilizado: conflito de unicidade da API é apresentado em linguagem compreensível.
- Token ausente/expirado: a API responde 401 e a interface solicita novo login.
