from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from logging_config.config import configure_logging
from middleware.request_logging import RequestLoggingMiddleware
from src.database.db import init_db
from src.routes import auth, events, frontend, products, recommendations


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    app = FastAPI(
        title="SmartReco Agentic Recommendation System",
        version="0.1.0",
        description="Backend API for the agentic recommendation platform.",
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

    app.include_router(frontend.router)

    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(events.router)
    app.include_router(recommendations.router)

    app.include_router(auth.router, prefix="/api")
    app.include_router(products.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(recommendations.router, prefix="/api")

    return app


app = create_app()


# conda activate smartreco-py312
# uvicorn src.main:app --reload 
#& 'C:\Users\win-10\miniconda3\envs\smartreco-py312\python.exe' -m uvicorn src.main:app --reload