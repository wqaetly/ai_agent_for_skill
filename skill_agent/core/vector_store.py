"""
向量数据库存储模�?
使用ChromaDB进行向量存储和检�?
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import json

logger = logging.getLogger(__name__)


class VectorStore:
    """向量数据库存储类，封装ChromaDB操作"""

    def __init__(self, config: dict, embedding_dimension: int = 768):
        """
        初始化向量存�?

        Args:
            config: 向量存储配置
            embedding_dimension: 嵌入向量维度
        """
        self.config = config
        self.persist_directory = config.get("persist_directory", "../Data/vector_db")
        self.collection_name = config.get("collection_name", "skill_collection")
        self.distance_metric = config.get("distance_metric", "cosine")
        self.embedding_dimension = embedding_dimension

        # 创建持久化目�?
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory, exist_ok=True)

        # 初始化ChromaDB客户�?
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 获取或创建集�?
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except Exception:
            # 集合不存在，创建新集�?
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_metric}
            )
            logger.info(f"Created new collection: {self.collection_name}")

        logger.info(f"Collection contains {self.collection.count()} documents")

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> bool:
        """
        添加文档到向量数据库

        Args:
            documents: 文档文本列表
            embeddings: 嵌入向量列表
            metadatas: 元数据列�?
            ids: 文档ID列表

        Returns:
            是否成功
        """
        try:
            # ChromaDB要求metadata中的值必须是简单类�?
            cleaned_metadatas = []
            for meta in metadatas:
                cleaned_meta = {}
                for key, value in meta.items():
                    if isinstance(value, (str, int, float, bool)):
                        cleaned_meta[key] = value
                    elif value is None:
                        cleaned_meta[key] = ""
                    else:
                        # 复杂类型转为JSON字符�?
                        cleaned_meta[key] = json.dumps(value, ensure_ascii=False)
                cleaned_metadatas.append(cleaned_meta)

            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=cleaned_metadatas,
                ids=ids
            )

            logger.info(f"Added {len(documents)} documents to collection")
            return True

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def update_document(
        self,
        document_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新单个文档

        Args:
            document_id: 文档ID
            document: 新的文档文本（可选）
            embedding: 新的嵌入向量（可选）
            metadata: 新的元数据（可选）

        Returns:
            是否成功
        """
        try:
            update_params = {"ids": [document_id]}

            if document is not None:
                update_params["documents"] = [document]
            if embedding is not None:
                update_params["embeddings"] = [embedding]
            if metadata is not None:
                # 清理metadata
                cleaned_meta = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        cleaned_meta[key] = value
                    elif value is None:
                        cleaned_meta[key] = ""
                    else:
                        cleaned_meta[key] = json.dumps(value, ensure_ascii=False)
                update_params["metadatas"] = [cleaned_meta]

            self.collection.update(**update_params)
            logger.info(f"Updated document: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            return False

    def delete_documents(self, ids: List[str]) -> bool:
        """
        删除文档

        Args:
            ids: 要删除的文档ID列表

        Returns:
            是否成功
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False

    def query(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        查询相似文档

        Args:
            query_embeddings: 查询向量列表
            top_k: 返回结果数量
            where: 元数据过滤条�?
            where_document: 文档内容过滤条件

        Returns:
            查询结果字典
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )

            logger.debug(f"Query returned {len(results['ids'][0])} results")
            return results

        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        根据ID获取文档

        Args:
            ids: 文档ID列表

        Returns:
            文档数据字典
        """
        try:
            results = self.collection.get(
                ids=ids,
                include=["documents", "metadatas", "embeddings"]
            )
            return results
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def count(self) -> int:
        """获取集合中的文档数量"""
        return self.collection.count()

    def clear(self) -> bool:
        """清空集合中的所有文�?""
        try:
            # ChromaDB没有直接的clear方法，需要删除并重建集合
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.distance_metric}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def get_all_ids(self) -> List[str]:
        """获取所有文档ID"""
        try:
            # 获取所有文档（分批处理，避免内存问题）
            all_data = self.collection.get(include=[])
            return all_data.get("ids", [])
        except Exception as e:
            logger.error(f"Error getting all IDs: {e}")
            return []

    def search_by_metadata(
        self,
        where: Dict[str, Any],
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        根据元数据搜索文�?

        Args:
            where: 元数据过滤条�?
            limit: 结果数量限制

        Returns:
            匹配的文�?
        """
        try:
            results = self.collection.get(
                where=where,
                limit=limit,
                include=["documents", "metadatas"]
            )
            return results
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def get_statistics(self) -> Dict[str, Any]:
        """获取向量库统计信�?""
        return {
            "collection_name": self.collection_name,
            "total_documents": self.count(),
            "distance_metric": self.distance_metric,
            "embedding_dimension": self.embedding_dimension,
            "persist_directory": self.persist_directory
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    config = {
        "persist_directory": "../Data/vector_db_test",
        "collection_name": "test_collection",
        "distance_metric": "cosine"
    }

    # 创建向量存储
    store = VectorStore(config, embedding_dimension=768)

    # 测试添加文档
    test_docs = [
        "火焰冲击波技�?,
        "冰霜新星技�?,
        "雷电链技�?
    ]
    test_embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
    test_metadatas = [
        {"skill_id": "skill_001", "type": "damage"},
        {"skill_id": "skill_002", "type": "control"},
        {"skill_id": "skill_003", "type": "damage"}
    ]
    test_ids = ["doc_001", "doc_002", "doc_003"]

    store.add_documents(test_docs, test_embeddings, test_metadatas, test_ids)

    # 测试查询
    query_embedding = [[0.15] * 768]
    results = store.query(query_embedding, top_k=2)
    print(f"\nQuery results: {results['ids']}")

    # 测试统计
    stats = store.get_statistics()
    print(f"\nStatistics: {stats}")

    # 清理测试数据
    store.clear()
