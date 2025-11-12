"""
SkillRAG Core Library
纯 RAG 逻辑，无 MCP 依赖，可独立部署

功能:
- 向量嵌入生成（embeddings）
- 向量存储和检索（vector_store）
- 技能索引管理（skill_indexer, action_indexer）
- 结构化查询（structured_query_engine）
- 细粒度索引（fine_grained_indexer）

使用示例:
    from SkillRAG.core import RAGEngine

    rag = RAGEngine(config)
    results = rag.search("治疗技能", top_k=5)
"""

__version__ = "1.0.0"
__all__ = [
    "RAGEngine",
    "EmbeddingGenerator",
    "VectorStore",
    "SkillIndexer",
    "ActionIndexer",
    "StructuredQueryEngine",
    "FineGrainedIndexer",
]

# 延迟导入，避免循环依赖
def __getattr__(name):
    if name == "RAGEngine":
        from .rag_engine import RAGEngine
        return RAGEngine
    elif name == "EmbeddingGenerator":
        from .embeddings import EmbeddingGenerator
        return EmbeddingGenerator
    elif name == "VectorStore":
        from .vector_store import VectorStore
        return VectorStore
    elif name == "SkillIndexer":
        from .skill_indexer import SkillIndexer
        return SkillIndexer
    elif name == "ActionIndexer":
        from .action_indexer import ActionIndexer
        return ActionIndexer
    elif name == "StructuredQueryEngine":
        from .structured_query_engine import StructuredQueryEngine
        return StructuredQueryEngine
    elif name == "FineGrainedIndexer":
        from .fine_grained_indexer import FineGrainedIndexer
        return FineGrainedIndexer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
