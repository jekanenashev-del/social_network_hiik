from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Социальная сеть «Круг»", version="1.0.0")
    @app.get("/health", tags=["system"])
    def health():
        return {"status": "ok", "version": "1.0.0"}
    # Роутеры подключаются отдельными PR владельцев модулей.
    return app

app = create_app()
