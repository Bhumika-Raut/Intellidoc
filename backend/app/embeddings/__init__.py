"""Embedding provider abstraction: EmbeddingProvider -> MockEmbeddingProvider | APIEmbeddingProvider."""

from app.embeddings.api import APIEmbeddingProvider
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.embeddings.mock import MockEmbeddingProvider

__all__ = ["EmbeddingProvider", "MockEmbeddingProvider", "APIEmbeddingProvider", "get_embedding_provider"]

