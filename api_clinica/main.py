from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router
from .cadastros import router as cadastro_router
from .clinica import router as clinica_router
from .integracao import router as integracao_router
from .registro import router as registro_router

app = FastAPI(title="API da Clínica Veterinária")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:5500", "http://localhost:5500"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(cadastro_router)
app.include_router(clinica_router)
app.include_router(integracao_router)
app.include_router(registro_router)


@app.get("/health")
def health():
    return {"status": "ok", "servico": "api-clinica"}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="frontend")
