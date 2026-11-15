# Evidência de funcionamento da Milestone 2

Em 15/11/2026, a suíte de integração passou em Windows com Python 3.14.3, MySQL 8.0.42 e Uvicorn. Foi usado um banco vazio em uma instância local descartável, inicializado com database/banco1.sql. As requisições foram feitas por HTTP à API local.

| Cenário | Resultado observado |
|---|---|
| Verificação de saúde | GET /health retornou 200 |
| Rota privada sem token | GET /tutores retornou 401 |
| Senha incorreta | POST /login retornou 401 |
| Veterinário inativo ou sem confirmação | POST /login retornou 403 |
| Confirmar senha e reutilizar o código | A primeira solicitação retornou 204 e a repetição retornou 400 |
| Login após confirmação | POST /login retornou 200 e emitiu um token |
| Cadastro, consulta, atualização e inativação de tutor | A consulta recuperou os dados persistidos e exibiu o estado INATIVO depois da inativação |
| CPF inválido ou duplicado | O cadastro retornou 422 ou 409, respectivamente |
| Cadastro de endereço, espécies e raça | A API retornou 201 e os registros foram usados nos cadastros seguintes |
| Raça incompatível com a espécie | O cadastro do animal retornou 409 |
| Cadastro de animal com RFID e tentativa de duplicidade | A API retornou 201 no primeiro cadastro e 409 na repetição |
| Logout e uso do mesmo token | POST /logout retornou 204 e a consulta posterior com o token retornou 401 |

A suíte está em tests/entrega2.py. O README descreve como executá-la.
