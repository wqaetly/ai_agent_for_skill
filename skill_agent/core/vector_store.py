"""Vector store abstraction - LanceDB.

This module provides a vector store implementation using LanceDB embedded database.
No external services or Docker required - data is stored locally.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from typing import Protocol

logger = logging.getLogger(__name__)


class VectorStore(Protocol):
    """Vector store interface used by RAGEngine."""

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool: ...

    def update_document(
        self,
        document_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool: ...

    def delete_documents(self, ids: List[str]) -> bool: ...

    def query(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]: ...

    def count(self) -> int: ...

    def clear(self) -> bool: ...

    def get_all_ids(self) -> List[str]: ...

    def search_by_metadata(self, where: Dict[str, Any], limit: Optional[int] = None) -> Dict[str, Any]: ...

    def get_statistics(self) -> Dict[str, Any]: ...


def create_vector_store(config: dict, embedding_dimension: int = 768) -> VectorStore:
    """Factory that creates a LanceDB vector store.
    
    Args:
        config: Configuration dictionary with 'lancedb_path' or 'path'.
        embedding_dimension: Dimension of embedding vectors (default: 768 for Qwen3).
    
    Returns:
        A LanceDBVectorStore instance.
    
    Raises:
        RuntimeError: If lancedb is not installed.
    """
    from .vector_store_lancedb import LanceDBVectorStore
    return LanceDBVectorStore(config, embedding_dimension=embedding_dimension)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    store = create_vector_store(
        {
            "collection_name": "test_collection",
            "distance_metric": "cosine",
            "lancedb_path": "Data/lancedb_test",
        },
        embedding_dimension=3,
    )
    store.add_documents(
        documents=["a", "b", "c"],
        embeddings=[[0.1, 0.1, 0.1], [0.2, 0.2, 0.2], [0.3, 0.3, 0.3]],
        metadatas=[{"k": "v"}, {"k": "v2"}, {"k": "v3"}],
        ids=["a", "b", "c"],
    )
    print(store.query([[0.15, 0.15, 0.15]], top_k=2))
