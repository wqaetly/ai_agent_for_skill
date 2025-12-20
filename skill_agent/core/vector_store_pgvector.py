"""pgvector-based vector store.

This implementation targets Postgres with the pgvector extension.

Schema is created automatically on startup:
- One table per "collection" to mirror the existing Chroma usage.
- Metadata is stored as JSONB.

Distance metric mapping:
- cosine: uses 1 - (embedding <=> query) similarity; we return "distance" compatible with existing code.
- l2: uses <->
- ip: uses <#>
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


@dataclass
class _PgConfig:
    dsn: str
    table_prefix: str
    distance_metric: str


class PgVectorStore:
    """Vector store backed by Postgres + pgvector."""

    def __init__(self, config: dict, embedding_dimension: int = 768):
        self.config = config
        self.embedding_dimension = embedding_dimension
        self.collection_name = config.get("collection_name", "skill_collection")
        self.distance_metric = (config.get("distance_metric", "cosine") or "cosine").lower()
        self._pg = _PgConfig(
            dsn=config.get("pg_dsn")
            or config.get("dsn")
            or "postgresql://postgres:postgres@localhost:5432/skill_agent",
            table_prefix=config.get("table_prefix", "vs"),
            distance_metric=self.distance_metric,
        )

        self._psycopg = None
        self._sql = None

        self._ensure_driver()
        self._ensure_schema()

    def _ensure_driver(self) -> None:
        try:
            import psycopg  # type: ignore
            from psycopg import sql  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "pgvector store requires psycopg. Install with: pip install psycopg[binary]"
            ) from e

        self._psycopg = psycopg
        self._sql = sql

    def _table_name(self) -> str:
        """Return the raw table name string."""
        return f"{self._pg.table_prefix}__{self.collection_name}".replace("-", "_")

    def _table_ident(self):
        # table name: <prefix>__<collection>
        return self._sql.Identifier(self._table_name())

    def _connect(self):
        return self._psycopg.connect(self._pg.dsn)

    def _ensure_schema(self) -> None:
        table = self._table_ident()
        table_name = self._table_name()
        with self._connect() as conn:
            with conn.cursor() as cur:
                # Ensure pgvector extension is available.
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cur.execute(
                    self._sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {table} (
                          id TEXT PRIMARY KEY,
                          document TEXT,
                          embedding vector({dim}),
                          metadata JSONB DEFAULT '{{}}'::jsonb
                        )
                        """
                    ).format(table=table, dim=self._sql.Literal(self.embedding_dimension)),
                )
                # Basic indexes for metadata filtering and vector search.
                cur.execute(
                    self._sql.SQL(
                        "CREATE INDEX IF NOT EXISTS {idx} ON {table} USING GIN (metadata)"
                    ).format(
                        idx=self._sql.Identifier(f"{table_name}_meta_gin"),
                        table=table,
                    )
                )
                # IVFFlat index needs lists; keep it optional to avoid errors.
                # Users can create a better index later; we create a generic one if possible.
                try:
                    cur.execute(
                        self._sql.SQL(
                            "CREATE INDEX IF NOT EXISTS {idx} ON {table} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
                        ).format(
                            idx=self._sql.Identifier(f"{table_name}_emb_ivfflat"),
                            table=table,
                        )
                    )
                except Exception as e:
                    logger.debug(f"Skipping ivfflat index creation: {e}")

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}
        for key, value in (metadata or {}).items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[key] = value
            else:
                cleaned[key] = json.dumps(value, ensure_ascii=False)
        return cleaned

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> bool:
        table = self._table_ident()
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    for doc_id, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
                        cur.execute(
                            self._sql.SQL(
                                """
                                INSERT INTO {table} (id, document, embedding, metadata)
                                VALUES (%s, %s, %s, %s::jsonb)
                                ON CONFLICT (id) DO UPDATE SET
                                  document = EXCLUDED.document,
                                  embedding = EXCLUDED.embedding,
                                  metadata = EXCLUDED.metadata
                                """
                            ).format(table=table),
                            (doc_id, doc, emb, json.dumps(self._clean_metadata(meta), ensure_ascii=False)),
                        )
            logger.info(f"Upserted {len(documents)} documents into {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to pgvector: {e}")
            return False

    def update_document(
        self,
        document_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        table = self._table_ident()
        fields = []
        values = []

        if document is not None:
            fields.append(self._sql.SQL("document = %s"))
            values.append(document)
        if embedding is not None:
            fields.append(self._sql.SQL("embedding = %s"))
            values.append(embedding)
        if metadata is not None:
            fields.append(self._sql.SQL("metadata = %s::jsonb"))
            values.append(json.dumps(self._clean_metadata(metadata), ensure_ascii=False))

        if not fields:
            return True

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        self._sql.SQL("UPDATE {table} SET ").format(table=table)
                        + self._sql.SQL(", ").join(fields)
                        + self._sql.SQL(" WHERE id = %s"),
                        (*values, document_id),
                    )
            return True
        except Exception as e:
            logger.error(f"Error updating document in pgvector: {e}")
            return False

    def delete_documents(self, ids: List[str]) -> bool:
        table = self._table_ident()
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        self._sql.SQL("DELETE FROM {table} WHERE id = ANY(%s)").format(
                            table=table
                        ),
                        (ids,),
                    )
            return True
        except Exception as e:
            logger.error(f"Error deleting documents in pgvector: {e}")
            return False

    def _distance_expr(self) -> str:
        # Return a SQL snippet for distance.
        if self.distance_metric in ("cosine", "cos"):
            return "embedding <=> %s"
        if self.distance_metric in ("l2", "euclidean"):
            return "embedding <-> %s"
        if self.distance_metric in ("ip", "inner_product"):
            return "embedding <#> %s"
        return "embedding <=> %s"

    def query(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # We keep the return shape compatible with Chroma usage in rag_engine.
        table = self._table_ident()
        embedding = query_embeddings[0] if query_embeddings else None
        if embedding is None:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        filters_sql = []
        params: List[Any] = []

        # Metadata filtering: exact match for simple key/value pairs.
        if where:
            for k, v in where.items():
                filters_sql.append("metadata ->> %s = %s")
                params.extend([k, str(v)])

        # Document filtering: best-effort ILIKE contains.
        if where_document and "$contains" in where_document:
            filters_sql.append("document ILIKE %s")
            params.append(f"%{where_document['$contains']}%")

        where_clause = ""
        if filters_sql:
            where_clause = "WHERE " + " AND ".join(filters_sql)

        distance_expr = self._distance_expr()
        query_sql = f"""
            SELECT id, document, metadata, {distance_expr} AS distance
            FROM {{table}}
            {where_clause}
            ORDER BY distance ASC
            LIMIT %s
        """

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        self._sql.SQL(query_sql).format(table=table),
                        (*params, embedding, top_k)
                        if "%s AS distance" in query_sql
                        else (*params, top_k),
                    )
                    rows = cur.fetchall()

            ids = [r[0] for r in rows]
            docs = [r[1] for r in rows]
            metas = [r[2] for r in rows]
            dists = [float(r[3]) for r in rows]
            return {"ids": [ids], "documents": [docs], "metadatas": [metas], "distances": [dists]}
        except Exception as e:
            logger.error(f"Error querying pgvector: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        table = self._table_ident()
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        self._sql.SQL(
                            "SELECT id, document, metadata, embedding FROM {table} WHERE id = ANY(%s)"
                        ).format(table=table),
                        (ids,),
                    )
                    rows = cur.fetchall()
            return {
                "ids": [r[0] for r in rows],
                "documents": [r[1] for r in rows],
                "metadatas": [r[2] for r in rows],
                "embeddings": [r[3] for r in rows],
            }
        except Exception as e:
            logger.error(f"Error getting docs by ids in pgvector: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def count(self) -> int:
        table = self._table_ident()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(self._sql.SQL("SELECT COUNT(*) FROM {table}").format(table=table))
                return int(cur.fetchone()[0])

    def clear(self) -> bool:
        table = self._table_ident()
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._sql.SQL("TRUNCATE {table}").format(table=table))
            return True
        except Exception as e:
            logger.error(f"Error clearing pgvector table: {e}")
            return False

    def get_all_ids(self) -> List[str]:
        table = self._table_ident()
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(self._sql.SQL("SELECT id FROM {table}").format(table=table))
                    return [r[0] for r in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all ids from pgvector: {e}")
            return []

    def search_by_metadata(self, where: Dict[str, Any], limit: Optional[int] = None) -> Dict[str, Any]:
        table = self._table_ident()
        filters_sql = []
        params: List[Any] = []
        for k, v in (where or {}).items():
            filters_sql.append("metadata ->> %s = %s")
            params.extend([k, str(v)])
        where_clause = ""
        if filters_sql:
            where_clause = "WHERE " + " AND ".join(filters_sql)
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT %s"
            params.append(limit)

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        self._sql.SQL(
                            f"SELECT id, document, metadata FROM {{table}} {where_clause} {limit_clause}"
                        ).format(table=table),
                        tuple(params),
                    )
                    rows = cur.fetchall()
            return {
                "ids": [r[0] for r in rows],
                "documents": [r[1] for r in rows],
                "metadatas": [r[2] for r in rows],
            }
        except Exception as e:
            logger.error(f"Error searching by metadata in pgvector: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "type": "pgvector",
            "collection_name": self.collection_name,
            "total_documents": self.count(),
            "distance_metric": self.distance_metric,
            "embedding_dimension": self.embedding_dimension,
            "pg_dsn": self._pg.dsn,
        }
