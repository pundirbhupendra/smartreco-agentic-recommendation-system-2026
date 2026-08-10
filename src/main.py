from fastapi import FastAPI

app = FastAPI(
    title="SmartReco Agentic Recommendation System",
    version="0.1.0",
    description="Backend API for the agentic recommendation platform.",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "SmartReco API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


#conda activate smartreco-py312
#uvicorn src.main:app --reload