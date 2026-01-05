"""LanceDB-based vector store.

This implementation uses LanceDB as a lightweight, embedded vector database.
No Docker or external services required - data is stored locally in Lance format.

Features:
- Zero configuration, embedded database
- High performance (Rust core)
- Supports cosine, L2, and dot product distance metrics
- Automatic persistence to local directory
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import pyarrow as pa

logger = logging.getLogger(__name__)


class LanceDBVectorStore:
    """Vector store backed by LanceDB."""

    def __init__(self, config: dict, embedding_dimension: int = 768):
        self.config = config
        self.embedding_dimension = embedding_dimension
        self.collection_name = config.get("collection_name", "skill_collection")
        self.distance_metric = (config.get("distance_metric", "cosine") or "cosine").lower()
        
        # LanceDB storage path
        self.db_path = config.get("lancedb_path") or config.get("path") or "Data/lancedb"
        
        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        self._db = None
        self._table = None
        self._ensure_driver()
        self._ensure_schema()

    def _ensure_driver(self) -> None:
        try:
            import lancedb
            self._lancedb = lancedb
        except ImportError as e:
            raise RuntimeError(
                "LanceDB store requires lancedb. Install with: pip install lancedb"
            ) from e

    def _table_name(self) -> str:
        """Return the table name."""
        return self.collection_name.replace("-", "_")

    def _connect(self):
        """Get or create database connection."""
        if self._db is None:
            self._db = self._lancedb.connect(self.db_path)
        return self._db

    def _get_table(self):
        """Get or create the table."""
        if self._table is not None:
            return self._table
        
        db = self._connect()
        table_name = self._table_name()
        
        if table_name in db.table_names():
            self._table = db.open_table(table_name)
        else:
            self._table = None
        
        return self._table

    def _ensure_schema(self) -> None:
        """Ensure table exists with correct schema."""
        db = self._connect()
        table_name = self._table_name()
        
        if table_name not in db.table_names():
            # Create empty table with schema
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("document", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), self.embedding_dimension)),
                pa.field("metadata", pa.string()),  # JSON string
            ])
            # Create with empty data matching schema
            self._table = db.create_table(table_name, schema=schema)
            logger.info(f"Created LanceDB table: {table_name}")
        else:
            self._table = db.open_table(table_name)
            logger.info(f"Opened existing LanceDB table: {table_name}")

    def _clean_metadata(self, metadata: Dict[str, Any]) -> str:
        """Convert metadata dict to JSON string."""
        cleaned: Dict[str, Any] = {}
        for key, value in (metadata or {}).items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[key] = value
            else:
                cleaned[key] = json.dumps(value, ensure_ascii=False)
        return json.dumps(cleaned, ensure_ascii=False)

    def _parse_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Parse metadata JSON string back to dict."""
        if not metadata_str:
            return {}
        try:
            return json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool:
        """Add or update documents in the store."""
        try:
            table = self._get_table()
            
            # Prepare data
            data = []
            for doc_id, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
                data.append({
                    "id": doc_id,
                    "document": doc,
                    "vector": emb,
                    "metadata": self._clean_metadata(meta),
                })
            
            if table is None:
                # Create table with initial data
                db = self._connect()
                self._table = db.create_table(self._table_name(), data)
            else:
                # Delete existing docs with same IDs first (upsert behavior)
                existing_ids = set(self.get_all_ids())
                ids_to_delete = [doc_id for doc_id in ids if doc_id in existing_ids]
                if ids_to_delete:
                    self.delete_documents(ids_to_delete)
                
                # Add new data
                table = self._get_table()
                if table is not None:
                    table.add(data)
                else:
                    db = self._connect()
                    self._table = db.create_table(self._table_name(), data)
            
            logger.info(f"Upserted {len(documents)} documents into {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to LanceDB: {e}")
            return False

    def update_document(
        self,
        document_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a single document."""
        try:
            table = self._get_table()
            if table is None:
                return False
            
            # Get existing document
            existing = table.search().where(f"id = '{document_id}'").limit(1).to_list()
            if not existing:
                return False
            
            existing_doc = existing[0]
            
            # Prepare updated data
            updated = {
                "id": document_id,
                "document": document if document is not None else existing_doc.get("document", ""),
                "vector": embedding if embedding is not None else existing_doc.get("vector", []),
                "metadata": self._clean_metadata(metadata) if metadata is not None else existing_doc.get("metadata", "{}"),
            }
            
            # Delete and re-add (LanceDB doesn't have native update)
            self.delete_documents([document_id])
            table = self._get_table()
            if table is not None:
                table.add([updated])
            
            return True
        except Exception as e:
            logger.error(f"Error updating document in LanceDB: {e}")
            return False

    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            table = self._get_table()
            if table is None:
                return True
            
            # Build filter for deletion
            if len(ids) == 1:
                filter_expr = f"id = '{ids[0]}'"
            else:
                ids_str = ", ".join(f"'{id}'" for id in ids)
                filter_expr = f"id IN ({ids_str})"
            
            table.delete(filter_expr)
            return True
        except Exception as e:
            logger.error(f"Error deleting documents in LanceDB: {e}")
            return False

    def _get_metric_type(self) -> str:
        """Map distance metric to LanceDB metric type."""
        if self.distance_metric in ("cosine", "cos"):
            return "cosine"
        if self.distance_metric in ("l2", "euclidean"):
            return "L2"
        if self.distance_metric in ("ip", "inner_product", "dot"):
            return "dot"
        return "cosine"

    def query(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query for similar documents."""
        table = self._get_table()
        embedding = query_embeddings[0] if query_embeddings else None
        
        if embedding is None or table is None:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            # Build search query
            search = table.search(embedding, vector_column_name="vector")
            search = search.metric(self._get_metric_type())
            search = search.limit(top_k)
            
            # Apply metadata filter if provided
            filter_parts = []
            if where:
                for k, v in where.items():
                    # LanceDB filter on JSON field requires parsing
                    filter_parts.append(f"json_extract(metadata, '$.{k}') = '{v}'")
            
            if where_document and "$contains" in where_document:
                search_term = where_document["$contains"]
                filter_parts.append(f"document LIKE '%{search_term}%'")
            
            if filter_parts:
                filter_expr = " AND ".join(filter_parts)
                search = search.where(filter_expr)
            
            results = search.to_list()
            
            ids = [r["id"] for r in results]
            docs = [r["document"] for r in results]
            metas = [self._parse_metadata(r.get("metadata", "{}")) for r in results]
            dists = [float(r.get("_distance", 0.0)) for r in results]
            
            return {"ids": [ids], "documents": [docs], "metadatas": [metas], "distances": [dists]}
        except Exception as e:
            logger.error(f"Error querying LanceDB: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """Get documents by their IDs."""
        table = self._get_table()
        if table is None:
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
        
        try:
            if len(ids) == 1:
                filter_expr = f"id = '{ids[0]}'"
            else:
                ids_str = ", ".join(f"'{id}'" for id in ids)
                filter_expr = f"id IN ({ids_str})"
            
            results = table.search().where(filter_expr).limit(len(ids)).to_list()
            
            return {
                "ids": [r["id"] for r in results],
                "documents": [r["document"] for r in results],
                "metadatas": [self._parse_metadata(r.get("metadata", "{}")) for r in results],
                "embeddings": [r["vector"] for r in results],
            }
        except Exception as e:
            logger.error(f"Error getting docs by ids in LanceDB: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def count(self) -> int:
        """Return total document count."""
        table = self._get_table()
        if table is None:
            return 0
        try:
            return table.count_rows()
        except Exception:
            return 0

    def clear(self) -> bool:
        """Clear all documents from the table."""
        try:
            db = self._connect()
            table_name = self._table_name()
            if table_name in db.table_names():
                db.drop_table(table_name)
                self._table = None
                self._ensure_schema()
            return True
        except Exception as e:
            logger.error(f"Error clearing LanceDB table: {e}")
            return False

    def get_all_ids(self) -> List[str]:
        """Get all document IDs."""
        table = self._get_table()
        if table is None:
            return []
        try:
            results = table.to_pandas()
            return results["id"].tolist() if "id" in results.columns else []
        except Exception as e:
            logger.error(f"Error getting all ids from LanceDB: {e}")
            return []

    def search_by_metadata(self, where: Dict[str, Any], limit: Optional[int] = None) -> Dict[str, Any]:
        """Search documents by metadata filters."""
        table = self._get_table()
        if table is None:
            return {"ids": [], "documents": [], "metadatas": []}
        
        try:
            filter_parts = []
            for k, v in (where or {}).items():
                filter_parts.append(f"json_extract(metadata, '$.{k}') = '{v}'")
            
            if not filter_parts:
                return {"ids": [], "documents": [], "metadatas": []}
            
            filter_expr = " AND ".join(filter_parts)
            search = table.search().where(filter_expr)
            
            if limit:
                search = search.limit(limit)
            
            results = search.to_list()
            
            return {
                "ids": [r["id"] for r in results],
                "documents": [r["document"] for r in results],
                "metadatas": [self._parse_metadata(r.get("metadata", "{}")) for r in results],
            }
        except Exception as e:
            logger.error(f"Error searching by metadata in LanceDB: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def get_statistics(self) -> Dict[str, Any]:
        """Return store statistics."""
        return {
            "type": "lancedb",
            "collection_name": self.collection_name,
            "total_documents": self.count(),
            "distance_metric": self.distance_metric,
            "embedding_dimension": self.embedding_dimension,
            "db_path": self.db_path,
        }
