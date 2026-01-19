"""
SkillRAG Core Library
纯 RAG 逻辑，无 MCP 依赖，可独立部署

功能:
- 向量嵌入生成（embeddings）
- 向量存储和检索（vector_store）
- 技能索引管理（skill_indexer, action_indexer）
- 结构化查询（structured_query_engine）
- 细粒度索引（fine_grained_indexer）
- 混合检索（hybrid_search）
- 查询理解（query_understanding）
- 重排序（reranker）
- 增量索引（incremental_indexer）
- 上下文感知检索（context_aware_retriever）

使用示例:
    from core import EnhancedRAGEngine

    rag = EnhancedRAGEngine(config)
    results = rag.search_skills("治疗技能", top_k=5, use_hybrid=True)
"""

__version__ = "2.0.0"
__all__ = [
    # 原有模块
    "RAGEngine",
    "EmbeddingGenerator",
    "create_vector_store",
    "SkillIndexer",
    "ActionIndexer",
    "StructuredQueryEngine",
    "FineGrainedIndexer",
    # 增强模块
    "EnhancedRAGEngine",
    "HybridSearchEngine",
    "BM25Index",
    "QueryUnderstandingEngine",
    "QueryIntent",
    "RerankerPipeline",
    "SkillReranker",
    "ActionReranker",
    "ExtendedQueryParser",
    "IncrementalIndexer",
    "ContextAwareRetriever",
    "EditContext",
]

# 延迟导入，避免循环依赖
def __getattr__(name):
    if name == "RAGEngine":
        from .rag_engine import RAGEngine
        return RAGEngine
    elif name == "EnhancedRAGEngine":
        from .enhanced_rag_engine import EnhancedRAGEngine
        return EnhancedRAGEngine
    elif name == "EmbeddingGenerator":
        from .embeddings import EmbeddingGenerator
        return EmbeddingGenerator
    elif name == "create_vector_store":
        from .vector_store import create_vector_store
        return create_vector_store
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
    # 增强模块
    elif name == "HybridSearchEngine":
        from .hybrid_search import HybridSearchEngine
        return HybridSearchEngine
    elif name == "BM25Index":
        from .hybrid_search import BM25Index
        return BM25Index
    elif name == "QueryUnderstandingEngine":
        from .query_understanding import QueryUnderstandingEngine
        return QueryUnderstandingEngine
    elif name == "QueryIntent":
        from .query_understanding import QueryIntent
        return QueryIntent
    elif name == "RerankerPipeline":
        from .reranker import RerankerPipeline
        return RerankerPipeline
    elif name == "SkillReranker":
        from .reranker import SkillReranker
        return SkillReranker
    elif name == "ActionReranker":
        from .reranker import ActionReranker
        return ActionReranker
    elif name == "ExtendedQueryParser":
        from .extended_query_parser import ExtendedQueryParser
        return ExtendedQueryParser
    elif name == "IncrementalIndexer":
        from .incremental_indexer import IncrementalIndexer
        return IncrementalIndexer
    elif name == "ContextAwareRetriever":
        from .context_aware_retriever import ContextAwareRetriever
        return ContextAwareRetriever
    elif name == "EditContext":
        from .context_aware_retriever import EditContext
        return EditContext
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
