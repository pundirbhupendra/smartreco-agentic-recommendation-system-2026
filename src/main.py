from fastapi import FastAPI

from logging_config.config import configure_logging
from middleware.request_logging import RequestLoggingMiddleware




def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="SmartReco Agentic Recommendation System",
        version="0.1.0",
        description="Backend API for the agentic recommendation platform.",
    )

    app.add_middleware(RequestLoggingMiddleware)

    return app


app = create_app()



#conda activate smartreco-py312
#uvicorn src.main:app --reload