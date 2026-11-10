from fastapi import FastAPI

app = FastAPI(title="API Governamental Simulada")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "servico": "api-governo"}
