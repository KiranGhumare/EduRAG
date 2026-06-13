from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key:str = ""
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-this"
    environment: str = "development"
    chunk_size: int = 500
    chunk_overlap: int = 50
    qdrant_collection: str = "edurag_chunks"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()
