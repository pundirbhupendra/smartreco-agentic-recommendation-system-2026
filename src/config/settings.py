import os 
from dotenv import load_dotenv


load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MESH_API_KEY: str = os.getenv("MESH_API_KEY", "")
    MESH_BASE_URL: str = os.getenv("MESH_BASE_URL", "https://api.meshapi.ai/v1")
   # PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
   # PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "smartreco-products")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./.smartreco/qdrant")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "my_reco_db")
    MESH_EMBEDDING_MODEL: str = os.getenv(
        "MESH_EMBEDDING_MODEL", "openai/text-embedding-3-small"
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./Data/smartreco.db")
    
    # LangSmith Settings
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "smartreco-build-challenge-2026")

    # Email Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")

    
settings = Settings()