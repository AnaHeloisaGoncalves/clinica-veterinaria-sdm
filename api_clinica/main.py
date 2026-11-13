from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
import jwt
import mysql.connector
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API da Clínica Veterinária")

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


# Conexão com o banco de dados MySQL
def get_db():
  return mysql.connector.connect(
      host="localhost",
      user="root",
      password=os.getenv("DB_PASSWORD"),  # <-- Substitua pela sua palavra-passe do MySQL root
      database="clinica_vet",
  )


# Schemas Pydantic para os dados enviados na requisição
class LoginSchema(BaseModel):
  email: str
  senha: str


class TutorSchema(BaseModel):
  nome_completo: str
  cpf: str
  email: str
  telefone: str | None = None


# 1. Rota de Health Check
@app.get("/health")
def health():
  return {"status": "ok", "servico": "api-clinica"}


# 2. Rota de Login (Autenticação JWT)
@app.post("/login")
def login(dados: LoginSchema):
  db = get_db()
  cursor = db.cursor(dictionary=True)
  cursor.execute(
      "SELECT * FROM veterinario WHERE email = %s", (dados.email,)
  )
  vet = cursor.fetchone()
  cursor.close()
  db.close()

  if not vet:
    raise HTTPException(status_code=401, detail="Credenciais inválidas")
  if vet["senha_hash"] != dados.senha:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
  expira = datetime.utcnow() + timedelta(hours=8)
  token = jwt.encode(
      {"sub": str(vet["id"]), "email": vet["email"], "exp": expira},
      SECRET_KEY,
      algorithm=ALGORITHM,
  )
  return {"token_acesso": token, "token_type": "bearer"}


# 3. Rota CRUD: Listar Tutores
@app.get("/tutores")
def listar_tutores():
  db = get_db()
  cursor = db.cursor(dictionary=True)
  cursor.execute("SELECT * FROM tutor")
  tutores = cursor.fetchall()
  cursor.close()
  db.close()
  return tutores


# 4. Rota CRUD: Criar Tutor
@app.post("/tutores", status_code=201)
def criar_tutor(tutor: TutorSchema):
  db = get_db()
  cursor = db.cursor()
  sql = "INSERT INTO tutor (nome_completo, cpf, email, telefone) VALUES (%s, %s, %s, %s)"
  valores = (tutor.nome_completo, tutor.cpf, tutor.email, tutor.telefone)

  try:
    cursor.execute(sql, valores)
    db.commit()
    tutor_id = cursor.lastrowid
    cursor.close()
    db.close()
    return {
        "id": tutor_id,
        "mensagem": "Tutor cadastrado com sucesso!",
        **tutor.dict(),
    }
  except Exception as e:
    cursor.close()
    db.close()
    raise HTTPException(
        status_code=400, detail=f"Erro ao inserir no banco: {str(e)}"
    )