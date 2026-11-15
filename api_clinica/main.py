from fastapi import FastAPI

from .auth import router as auth_router
from .cadastros import router as cadastro_router

app = FastAPI(title="API da Clínica Veterinária")
app.include_router(auth_router)
app.include_router(cadastro_router)


@app.get("/health")
def health():
    return {"status": "ok", "servico": "api-clinica"}
