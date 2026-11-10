from fastapi import FastAPI

app = FastAPI(title="API da Clínica Veterinária")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "servico": "api-clinica"}
