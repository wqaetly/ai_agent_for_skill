"""
增强版RAG引擎
整合：混合检索、查询理解、重排序、增量索引、上下文感知
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from cachetools import TTLCache

from .embeddings import EmbeddingGenerator
from .vector_store import create_vector_store
from .skill_indexer import SkillIndexer
from .action_indexer import ActionIndexer
from .structured_query_engine import StructuredQueryEngine

# 新增模块
from .hybrid_search import HybridSearchEngine, BM25Index
from .query_understanding import QueryUnderstandingEngine, QueryIntent
from .reranker import (
    RerankerPipeline, SkillReranker, ActionReranker,
    CrossEncoderReranker, RerankResult
)
from .extended_query_parser import ExtendedQueryParser, ExtendedQueryEvaluator
from .incremental_indexer import IncrementalIndexer, FileChangeType
from .context_aware_retriever import ContextAwareRetriever, EditContext

logger = logging.getLogger(__name__)


class EnhancedRAGEngine:
    """增强版RAG引擎"""

    def __init__(self, config: dict):
        """
        初始化增强版RAG引擎

        Args:
            config: 完整配置字典
        """
        self.config = config
        self.rag_config = config.get('rag', {})
        self.top_k = self.rag_config.get('top_k', 5)
        self.similarity_threshold = self.rag_config.get('similarity_threshold', 0.5)

        logger.info("Initializing Enhanced RAG Engine...")

        # ============ 基础组件 ============
        # 1. 嵌入生成器
        self.embedding_generator = EmbeddingGenerator(config.get('embedding', {}))

        # 2. 向量存储（技能）
        self.vector_store = create_vector_store(
            config.get('vector_store', {}),
            embedding_dimension=self.embedding_generator.get_embedding_dimension(),
        )

        # 3. Action向量存储
        action_vector_config = config.get('vector_store', {}).copy()
        action_vector_config['collection_name'] = config.get('action_indexer', {}).get(
            'collection_name', 'action_collection'
        )
        self.action_vector_store = create_vector_store(
            action_vector_config,
            embedding_dimension=self.embedding_generator.get_embedding_dimension(),
        )

        # 4. 索引器
        self.skill_indexer = SkillIndexer(config.get('skill_indexer', {}))
        self.action_indexer = ActionIndexer(config.get('action_indexer', {}))

        # 5. 结构化查询引擎
        skills_dir = config.get('skill_indexer', {}).get(
            'skills_directory', '../Data/Skills'
        )
        self.structured_query_engine = StructuredQueryEngine(
            skills_dir=skills_dir,
            cache_size=self.rag_config.get('structured_query_cache_size', 100)
        )

        # ============ 增强组件 ============
        # 6. 混合检索引擎
        self.hybrid_search = HybridSearchEngine(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_generator,
            bm25_weight=self.rag_config.get('bm25_weight', 0.3),
            vector_weight=self.rag_config.get('vector_weight', 0.7),
            rrf_k=self.rag_config.get('rrf_k', 60)
        )

        # 7. Action混合检索
        self.action_hybrid_search = HybridSearchEngine(
            vector_store=self.action_vector_store,
            embedding_generator=self.embedding_generator,
            bm25_weight=0.4,  # Action更依赖关键词
            vector_weight=0.6
        )

        # 8. 查询理解引擎
        self.query_understanding = QueryUnderstandingEngine()

        # 9. 重排序管道
        self.skill_reranker = RerankerPipeline()
        self.skill_reranker.add_stage(SkillReranker())
        
        self.action_reranker = RerankerPipeline()
        self.action_reranker.add_stage(ActionReranker())

        # 可选：添加Cross-Encoder重排序
        if self.rag_config.get('use_cross_encoder', False):
            self.skill_reranker.add_stage(CrossEncoderReranker())
            self.action_reranker.add_stage(CrossEncoderReranker())

        # 10. 扩展查询解析器
        self.extended_parser = ExtendedQueryParser()
        self.extended_evaluator = ExtendedQueryEvaluator()

        # 11. 增量索引器
        self.incremental_indexer = IncrementalIndexer(
            watch_directory=skills_dir,
            file_pattern="*.json",
            hash_cache_file=config.get('skill_indexer', {}).get(
                'hash_cache', '../Data/skill_hash_cache.json'
            ),
            index_version_file=config.get('skill_indexer', {}).get(
                'version_file', '../Data/skill_index_version.json'
            )
        )
        self._setup_incremental_callbacks()

        # 12. 上下文感知检索器
        self.context_retriever = ContextAwareRetriever(
            rag_engine=self,
            history_file=config.get('rag', {}).get(
                'query_history_file', '../Data/query_history.json'
            )
        )

        # ============ 缓存 ============
        cache_enabled = self.rag_config.get('cache_enabled', True)
        cache_ttl = self.rag_config.get('cache_ttl', 3600)
        if cache_enabled:
            self._query_cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        else:
            self._query_cache = None

        # ============ 统计 ============
        self._stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'hybrid_searches': 0,
            'reranked_queries': 0,
            'total_indexed': 0,
            'last_index_time': None
        }

        logger.info("Enhanced RAG Engine initialized successfully")

    def _setup_incremental_callbacks(self):
        """设置增量索引回调"""
        def on_file_created(file_path: str):
            logger.info(f"New skill file detected: {file_path}")
            self._index_single_skill(file_path)

        def on_file_modified(file_path: str):
            logger.info(f"Skill file modified: {file_path}")
            self._index_single_skill(file_path)

        def on_file_deleted(file_path: str):
            logger.info(f"Skill file deleted: {file_path}")
            self._remove_skill_from_index(file_path)

        self.incremental_indexer.on_file_created(on_file_created)
        self.incremental_indexer.on_file_modified(on_file_modified)
        self.incremental_indexer.on_file_deleted(on_file_deleted)

    def _get_cache_key(self, query: str, top_k: int, filters: Optional[Dict] = None) -> str:
        """生成缓存键"""
        cache_str = f"{query}|{top_k}|{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()

    # ============ 索引方法 ============

    def index_skills(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """索引所有技能（支持增量）"""
        logger.info(f"Starting skill indexing (force_rebuild={force_rebuild})")
        start_time = datetime.now()

        if force_rebuild:
            # 全量索引
            skills = self.skill_indexer.index_all_skills(force_rebuild=True)
            self.hybrid_search.clear()
        else:
            # 增量索引
            result = self.incremental_indexer.incremental_index()
            if not any(result['stats'].values()):
                # 无变更，检查是否需要初始化
                if self.hybrid_search.bm25_index.doc_count == 0:
                    skills = self.skill_indexer.index_all_skills(force_rebuild=False)
                else:
                    return {
                        "status": "no_changes",
                        "version": result['version']
                    }
            else:
                return {
                    "status": "incremental",
                    "stats": result['stats'],
                    "version": result['version']
                }

        if not skills:
            return {"status": "no_skills", "count": 0}

        # 准备数据
        documents, metadatas, ids = [], [], []
        for skill in skills:
            documents.append(skill['search_text'])
            metadatas.append(self._build_skill_metadata(skill))
            ids.append(hashlib.md5(skill['file_path'].encode('utf-8')).hexdigest())

        # 生成嵌入
        embeddings = self.embedding_generator.encode_batch(documents, show_progress=True)

        # 索引到混合检索引擎
        self.hybrid_search.index_documents(
            documents=documents,
            doc_ids=ids,
            metadatas=metadatas,
            embeddings=embeddings
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        self._stats['total_indexed'] = len(skills)
        self._stats['last_index_time'] = datetime.now().isoformat()

        return {
            "status": "success",
            "count": len(skills),
            "elapsed_time": elapsed
        }

    def _build_skill_metadata(self, skill: Dict[str, Any]) -> Dict[str, Any]:
        """构建技能元数据"""
        action_types = self._extract_action_types(skill)
        return {
            'skill_id': skill.get('skillId', ''),
            'skill_name': skill.get('skillName', ''),
            'file_name': skill.get('file_name', ''),
            'file_path': skill.get('file_path', ''),
            'file_hash': skill.get('file_hash', ''),
            'total_duration': skill.get('totalDuration', 0),
            'frame_rate': skill.get('frameRate', 30),
            'num_tracks': len(skill.get('tracks', [])),
            'num_actions': sum(len(t.get('actions', [])) for t in skill.get('tracks', [])),
            'action_type_list': json.dumps(action_types)
        }

    def _extract_action_types(self, skill: Dict[str, Any]) -> List[str]:
        """提取技能中的Action类型"""
        action_types = set()
        for track in skill.get('tracks', []):
            if not track.get('enabled', True):
                continue
            for action in track.get('actions', []):
                action_type = action.get('type', '')
                if action_type:
                    action_types.add(action_type)
        return sorted(list(action_types))

    def _index_single_skill(self, file_path: str):
        """索引单个技能文件"""
        skill_data = self.skill_indexer.parse_skill_file(file_path)
        if not skill_data:
            return

        skill_data['search_text'] = self.skill_indexer.build_search_text(skill_data)
        doc_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        metadata = self._build_skill_metadata(skill_data)
        embedding = self.embedding_generator.encode(skill_data['search_text'])

        self.hybrid_search.index_documents(
            documents=[skill_data['search_text']],
            doc_ids=[doc_id],
            metadatas=[metadata],
            embeddings=[embedding]
        )

    def _remove_skill_from_index(self, file_path: str):
        """从索引中移除技能"""
        doc_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        self.vector_store.delete_documents([doc_id])
        # BM25索引需要重建（简化处理）
        logger.info(f"Removed skill from vector store: {file_path}")

    def index_actions(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """索引所有Action"""
        logger.info(f"Starting action indexing (force_rebuild={force_rebuild})")
        start_time = datetime.now()

        prepared_actions = self.action_indexer.prepare_actions_for_indexing()
        if not prepared_actions:
            return {"status": "no_actions", "count": 0}

        documents = [a['search_text'] for a in prepared_actions]
        metadatas = [a['metadata'] for a in prepared_actions]
        ids = [a['id'] for a in prepared_actions]

        embeddings = self.embedding_generator.encode_batch(documents, show_progress=True)

        if force_rebuild:
            self.action_hybrid_search.clear()

        self.action_hybrid_search.index_documents(
            documents=documents,
            doc_ids=ids,
            metadatas=metadatas,
            embeddings=embeddings
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        return {
            "status": "success",
            "count": len(prepared_actions),
            "elapsed_time": elapsed
        }

    # ============ 搜索方法 ============

    def search_skills(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        use_query_expansion: bool = True,
        return_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        增强版技能搜索

        Args:
            query: 搜索查询
            top_k: 返回数量
            filters: 元数据过滤
            use_hybrid: 是否使用混合检索
            use_rerank: 是否使用重排序
            use_query_expansion: 是否使用查询扩展
            return_details: 是否返回详细信息
        """
        self._stats['total_queries'] += 1
        top_k = top_k or self.top_k

        # 检查缓存
        cache_key = self._get_cache_key(query, top_k, filters)
        if self._query_cache and cache_key in self._query_cache:
            self._stats['cache_hits'] += 1
            return self._query_cache[cache_key]

        # 1. 查询理解
        understanding = self.query_understanding.understand(query)
        search_queries = [query]
        if use_query_expansion:
            search_queries = understanding.expanded_queries or [query]

        # 2. 检索
        all_results = []
        candidate_k = min(top_k * 3, 50)

        for search_query in search_queries[:3]:  # 最多3个扩展查询
            if use_hybrid:
                self._stats['hybrid_searches'] += 1
                results = self.hybrid_search.search(
                    query=search_query,
                    top_k=candidate_k,
                    fusion_method="rrf",
                    filters=filters,
                    return_scores=True
                )
                all_results.extend(results)
            else:
                # 纯向量检索
                query_embedding = self.embedding_generator.encode(
                    search_query, prompt_name="query"
                )
                results = self.vector_store.query(
                    query_embeddings=[query_embedding],
                    top_k=candidate_k,
                    where=filters
                )
                # 转换格式
                if results and results['ids'] and results['ids'][0]:
                    for i in range(len(results['ids'][0])):
                        all_results.append({
                            'doc_id': results['ids'][0][i],
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'score': 1.0 - results['distances'][0][i]
                        })

        # 去重
        seen_ids = set()
        unique_results = []
        for r in all_results:
            doc_id = r.get('doc_id')
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(r)

        # 3. 重排序
        if use_rerank and unique_results:
            self._stats['reranked_queries'] += 1
            reranked = self.skill_reranker.rerank(query, unique_results, top_k=top_k)
            final_results = self._convert_rerank_results(reranked, return_details)
        else:
            final_results = self._convert_search_results(
                unique_results[:top_k], return_details
            )

        # 过滤低分结果
        final_results = [
            r for r in final_results
            if r.get('similarity', r.get('score', 0)) >= self.similarity_threshold
        ]

        # 缓存结果
        if self._query_cache:
            self._query_cache[cache_key] = final_results

        return final_results

    def _convert_rerank_results(
        self,
        results: List[RerankResult],
        return_details: bool
    ) -> List[Dict[str, Any]]:
        """转换重排序结果"""
        converted = []
        for r in results:
            item = {
                'skill_id': r.metadata.get('skill_id', '') if r.metadata else '',
                'skill_name': r.metadata.get('skill_name', '') if r.metadata else '',
                'file_name': r.metadata.get('file_name', '') if r.metadata else '',
                'similarity': round(r.rerank_score, 4),
                'original_rank': r.original_rank,
                'new_rank': r.new_rank
            }
            if return_details and r.metadata:
                item.update({
                    'file_path': r.metadata.get('file_path', ''),
                    'total_duration': r.metadata.get('total_duration', 0),
                    'num_tracks': r.metadata.get('num_tracks', 0),
                    'num_actions': r.metadata.get('num_actions', 0),
                    'action_type_list': r.metadata.get('action_type_list', '[]')
                })
            converted.append(item)
        return converted

    def search_actions(
        self,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        return_details: bool = False
    ) -> List[Dict[str, Any]]:
        """增强版Action搜索"""
        top_k = top_k or self.top_k
        candidate_k = min(top_k * 3, 30)

        # 构建过滤条件
        filters = {"category": category_filter} if category_filter else None

        if use_hybrid:
            results = self.action_hybrid_search.search(
                query=query,
                top_k=candidate_k,
                filters=filters,
                return_scores=True
            )
        else:
            query_embedding = self.embedding_generator.encode(query, prompt_name="query")
            raw_results = self.action_vector_store.query(
                query_embeddings=[query_embedding],
                top_k=candidate_k,
                where=filters
            )
            results = []
            if raw_results and raw_results['ids'] and raw_results['ids'][0]:
                for i in range(len(raw_results['ids'][0])):
                    results.append({
                        'doc_id': raw_results['ids'][0][i],
                        'document': raw_results['documents'][0][i],
                        'metadata': raw_results['metadatas'][0][i],
                        'score': 1.0 - raw_results['distances'][0][i]
                    })

        # 重排序
        if use_rerank and results:
            reranked = self.action_reranker.rerank(query, results, top_k=top_k)
            return self._convert_action_rerank_results(reranked, return_details)

        return self._convert_action_results(results[:top_k], return_details)

    def _convert_action_rerank_results(
        self, results: List[RerankResult], return_details: bool
    ) -> List[Dict[str, Any]]:
        """转换Action重排序结果"""
        converted = []
        for r in results:
            meta = r.metadata or {}
            item = {
                'type_name': meta.get('type_name', ''),
                'display_name': meta.get('display_name', ''),
                'category': meta.get('category', ''),
                'similarity': round(r.rerank_score, 4)
            }
            if return_details:
                action_def = self.action_indexer.get_action_by_type(meta.get('type_name', ''))
                if action_def:
                    item['parameters'] = action_def.get('parameters', [])
                    item['description'] = action_def.get('description', '')
            converted.append(item)
        return converted

    def _convert_action_results(
        self, results: List[Dict], return_details: bool
    ) -> List[Dict[str, Any]]:
        """转换Action搜索结果"""
        converted = []
        for r in results:
            meta = r.get('metadata', {})
            item = {
                'type_name': meta.get('type_name', ''),
                'display_name': meta.get('display_name', ''),
                'category': meta.get('category', ''),
                'similarity': round(r.get('fused_score', r.get('score', 0)), 4)
            }
            if return_details:
                action_def = self.action_indexer.get_action_by_type(meta.get('type_name', ''))
                if action_def:
                    item['parameters'] = action_def.get('parameters', [])
                    item['description'] = action_def.get('description', '')
            converted.append(item)
        return converted

    # ============ 上下文感知方法 ============

    def set_edit_context(self, context: EditContext):
        """设置编辑上下文"""
        self.context_retriever.set_context(context)

    def set_context_from_skill(self, skill_data: Dict[str, Any]):
        """从技能数据设置上下文"""
        self.context_retriever.update_context_from_skill(skill_data)

    def recommend_actions_contextual(
        self,
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """基于上下文推荐Action"""
        recommendations = self.context_retriever.recommend_actions(query, top_k)
        return [
            {
                'action_type': r.item_id,
                'score': round(r.score, 4),
                'reason': r.reason,
                'metadata': r.metadata
            }
            for r in recommendations
        ]

    def get_similar_skills(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """获取相似技能"""
        recommendations = self.context_retriever.get_similar_skills(top_k)
        return [
            {
                'skill_id': r.item_id,
                'skill_name': r.metadata.get('skill_name', ''),
                'score': round(r.score, 4),
                'reason': r.reason
            }
            for r in recommendations
        ]

    # ============ 扩展查询方法 ============

    def query_extended(self, query_str: str, limit: int = 100) -> Dict[str, Any]:
        """执行扩展SQL风格查询"""
        expr = self.extended_parser.parse(query_str)
        
        all_actions = []
        index_data = self.structured_query_engine.indexer.get_index()
        
        for file_index in index_data.get("files", {}).values():
            for track in file_index.get("tracks", []):
                for action in track.get("actions", []):
                    action_data = {**action, "track_name": track["track_name"]}
                    
                    if expr.action_type and action.get("action_type") != expr.action_type:
                        continue
                    
                    if expr.where:
                        if not self.extended_evaluator.evaluate_condition(expr.where, action_data):
                            continue
                    
                    all_actions.append(action_data)
        
        if expr.aggregates:
            results = self.extended_evaluator.aggregate(
                all_actions, expr.aggregates, expr.group_by
            )
        else:
            results = all_actions
        
        if expr.order_by:
            for order in reversed(expr.order_by):
                results.sort(key=lambda x: x.get(order.field, 0), reverse=order.descending)
        
        total = len(results)
        if expr.limit:
            results = results[expr.offset:expr.offset + expr.limit]
        elif limit:
            results = results[:limit]
        
        return {"results": results, "total": total, "returned": len(results)}

    # ============ 文件监听方法 ============

    def start_file_watching(self, use_watchdog: bool = True):
        """启动文件监听"""
        if use_watchdog:
            self.incremental_indexer.start_watching_with_watchdog()
        else:
            self.incremental_indexer.start_watching(poll_interval=5.0)

    def stop_file_watching(self):
        """停止文件监听"""
        self.incremental_indexer.stop_watching()

    # ============ 工具方法 ============

    def get_action_by_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """根据类型名获取Action"""
        return self.action_indexer.get_action_by_type(type_name)

    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取技能"""
        results = self.vector_store.search_by_metadata(where={"skill_id": skill_id}, limit=1)
        if results and results['ids']:
            file_path = results['metadatas'][0].get('file_path', '')
            if file_path:
                return self.skill_indexer.parse_skill_file(file_path)
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'engine_stats': self._stats,
            'hybrid_search': self.hybrid_search.get_statistics(),
            'action_hybrid_search': self.action_hybrid_search.get_statistics(),
            'incremental_indexer': self.incremental_indexer.get_status(),
            'context_retriever': self.context_retriever.get_statistics(),
            'query_cache_size': len(self._query_cache) if self._query_cache else 0
        }

    def clear_cache(self):
        """清空所有缓存"""
        if self._query_cache:
            self._query_cache.clear()
        self.structured_query_engine.clear_cache()
        self.embedding_generator.clear_cache()
