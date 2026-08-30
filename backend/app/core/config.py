from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "IntelliDocs"
    debug: bool = False

    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    openai_api_key: str = ""
    groq_api_key: str = ""
    openai_base_url: str = ""

    embedding_provider: str = "mock"  # mock (default, no downloads) | api (OpenAI-compatible)
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""  # falls back to openai_api_key
    embedding_api_base: str = ""  # falls back to openai_base_url

    database_url: str = "sqlite:///./data/intellidocs.db"
    vector_store: str = "local"  # local (default, dependency-free) | chroma (optional extra)
    vector_path: str = "./data/vectors"
    chroma_path: str = "./data/chroma"  # only used when vector_store=chroma
    upload_dir: str = "./data/uploads"

    max_upload_mb: int = 15
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    retrieval_top_k: int = 5
    chunk_size: int = 900
    chunk_overlap: int = 150

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_dir(self) -> Path:
        path = Path(self.chroma_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def vector_dir(self) -> Path:
        path = Path(self.vector_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_data_dirs(self) -> None:
        Path("data").mkdir(parents=True, exist_ok=True)
        self.upload_path
        self.vector_dir


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_data_dirs()
    return settings
