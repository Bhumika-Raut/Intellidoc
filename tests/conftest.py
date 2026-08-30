import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["VECTOR_STORE"] = "local"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(ROOT / 'data' / 'test.db').as_posix()}")
os.environ.setdefault("VECTOR_PATH", str(ROOT / "data" / "vectors-test"))
os.environ.setdefault("UPLOAD_DIR", str(ROOT / "data" / "uploads-test"))
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

