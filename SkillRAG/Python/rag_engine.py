"""
RAG引擎核心模块
整合嵌入生成、向量存储和技能索引，提供统一的RAG接口
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from cachetools import TTLCache
import hashlib
import json

from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from skill_indexer import SkillIndexer
from action_indexer import ActionIndexer

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG引擎，提供技能检索和推荐功能"""

    def __init__(self, config: dict):
        """
        初始化RAG引擎

        Args:
            config: 完整配置字典
        """
        self.config = config
        self.rag_config = config.get('rag', {})
        self.top_k = self.rag_config.get('top_k', 5)
        self.similarity_threshold = self.rag_config.get('similarity_threshold', 0.5)

        # 初始化各个组件
        logger.info("Initializing RAG Engine components...")

        # 1. 嵌入生成器
        self.embedding_generator = EmbeddingGenerator(config.get('embedding', {}))

        # 2. 向量存储（用于技能）
        self.vector_store = VectorStore(
            config.get('vector_store', {}),
            embedding_dimension=self.embedding_generator.get_embedding_dimension()
        )

        # 3. 技能索引器
        self.skill_indexer = SkillIndexer(config.get('skill_indexer', {}))

        # 4. Action索引器
        self.action_indexer = ActionIndexer(config.get('action_indexer', {}))

        # 5. Action向量存储（独立collection）
        action_vector_config = config.get('vector_store', {}).copy()
        action_vector_config['collection_name'] = config.get('action_indexer', {}).get('collection_name', 'action_collection')
        self.action_vector_store = VectorStore(
            action_vector_config,
            embedding_dimension=self.embedding_generator.get_embedding_dimension()
        )

        # 查询缓存（TTL缓存，默认1小时）
        cache_enabled = self.rag_config.get('cache_enabled', True)
        cache_ttl = self.rag_config.get('cache_ttl', 3600)

        if cache_enabled:
            self._query_cache = TTLCache(maxsize=1000, ttl=cache_ttl)
            logger.info(f"Query cache enabled with TTL={cache_ttl}s")
        else:
            self._query_cache = None

        # 统计信息
        self._stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'total_indexed': 0,
            'last_index_time': None
        }

        logger.info("RAG Engine initialized successfully")

    def _get_cache_key(self, query: str, top_k: int, filters: Optional[Dict] = None) -> str:
        """生成缓存键"""
        cache_str = f"{query}|{top_k}|{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()

    def index_skills(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        索引所有技能到向量数据库

        Args:
            force_rebuild: 是否强制重建索引

        Returns:
            索引结果统计
        """
        logger.info(f"Starting skill indexing (force_rebuild={force_rebuild})")
        start_time = datetime.now()

        # 1. 扫描并解析技能文件
        skills = self.skill_indexer.index_all_skills(force_rebuild=force_rebuild)

        if not skills:
            logger.warning("No skills found to index")
            return {"status": "no_skills", "count": 0}

        # 2. 准备数据
        documents = []
        metadatas = []
        ids = []

        for skill in skills:
            # 文档文本（用于搜索）
            documents.append(skill['search_text'])

            # 元数据
            metadata = {
                'skill_id': skill.get('skillId', ''),
                'skill_name': skill.get('skillName', ''),
                'file_name': skill.get('file_name', ''),
                'file_path': skill.get('file_path', ''),
                'file_hash': skill.get('file_hash', ''),
                'last_modified': skill.get('last_modified', ''),
                'total_duration': skill.get('totalDuration', 0),
                'frame_rate': skill.get('frameRate', 30),
                'num_tracks': len(skill.get('tracks', [])),
                'num_actions': sum(len(track.get('actions', [])) for track in skill.get('tracks', []))
            }
            metadatas.append(metadata)

            # 文档ID（使用文件路径的哈希）
            doc_id = hashlib.md5(skill['file_path'].encode('utf-8')).hexdigest()
            ids.append(doc_id)

        # 3. 生成嵌入向量
        logger.info(f"Generating embeddings for {len(documents)} skills...")
        embeddings = self.embedding_generator.encode_batch(
            documents,
            show_progress=True
        )

        # 4. 存储到向量数据库
        logger.info("Storing embeddings to vector database...")

        # 如果是强制重建，先清空
        if force_rebuild:
            self.vector_store.clear()

        # 添加文档
        success = self.vector_store.add_documents(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        # 5. 统计
        elapsed_time = (datetime.now() - start_time).total_seconds()

        if success:
            self._stats['total_indexed'] = len(skills)
            self._stats['last_index_time'] = datetime.now().isoformat()

            result = {
                "status": "success",
                "count": len(skills),
                "elapsed_time": elapsed_time,
                "vector_dimension": self.embedding_generator.get_embedding_dimension()
            }

            logger.info(f"Indexing completed: {len(skills)} skills in {elapsed_time:.2f}s")
        else:
            result = {
                "status": "error",
                "count": 0,
                "message": "Failed to add documents to vector store"
            }
            logger.error("Indexing failed")

        return result

    def search_skills(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        return_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜索相似技能

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filters: 元数据过滤条件
            return_details: 是否返回详细信息

        Returns:
            匹配的技能列表
        """
        self._stats['total_queries'] += 1

        # 使用默认值
        top_k = top_k or self.top_k

        # 检查缓存
        cache_key = None
        if self._query_cache is not None:
            cache_key = self._get_cache_key(query, top_k, filters)
            if cache_key in self._query_cache:
                self._stats['cache_hits'] += 1
                logger.debug(f"Cache hit for query: {query[:50]}")
                return self._query_cache[cache_key]

        # 1. 生成查询向量（使用query prompt优化Qwen3等模型性能）
        query_embedding = self.embedding_generator.encode(
            query,
            use_cache=True,
            prompt_name="query"
        )

        # 2. 向量检索
        results = self.vector_store.query(
            query_embeddings=[query_embedding],
            top_k=top_k,
            where=filters
        )

        # 3. 处理结果
        matched_skills = []

        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                doc_id = results['ids'][0][i]
                distance = results['distances'][0][i]
                metadata = results['metadatas'][0][i]
                document = results['documents'][0][i]

                # 转换距离为相似度（cosine distance -> cosine similarity）
                similarity = 1.0 - distance

                # 过滤低相似度结果
                if similarity < self.similarity_threshold:
                    continue

                skill_result = {
                    'skill_id': metadata.get('skill_id', ''),
                    'skill_name': metadata.get('skill_name', ''),
                    'file_name': metadata.get('file_name', ''),
                    'similarity': round(similarity, 4),
                    'distance': round(distance, 4)
                }

                # 如果需要详细信息
                if return_details:
                    skill_result.update({
                        'file_path': metadata.get('file_path', ''),
                        'total_duration': metadata.get('total_duration', 0),
                        'frame_rate': metadata.get('frame_rate', 30),
                        'num_tracks': metadata.get('num_tracks', 0),
                        'num_actions': metadata.get('num_actions', 0),
                        'last_modified': metadata.get('last_modified', ''),
                        'search_text_preview': document[:200]
                    })

                matched_skills.append(skill_result)

        # 4. 更新缓存
        if self._query_cache is not None and cache_key:
            self._query_cache[cache_key] = matched_skills

        logger.info(f"Search query '{query[:50]}' returned {len(matched_skills)} results")
        return matched_skills

    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        根据skill_id获取技能详细信息

        Args:
            skill_id: 技能ID

        Returns:
            技能详细信息，未找到返回None
        """
        # 通过元数据查询
        results = self.vector_store.search_by_metadata(
            where={"skill_id": skill_id},
            limit=1
        )

        if results and results['ids']:
            metadata = results['metadatas'][0]
            file_path = metadata.get('file_path', '')

            # 重新解析文件以获取完整数据
            if file_path:
                skill_data = self.skill_indexer.parse_skill_file(file_path)
                return skill_data

        return None

    def recommend_actions(
        self,
        context: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        根据上下文推荐Action类型

        Args:
            context: 上下文描述（如"造成伤害"、"移动角色"等）
            top_k: 推荐数量

        Returns:
            推荐的Action列表
        """
        # 搜索包含相关Action的技能
        matching_skills = self.search_skills(
            query=context,
            top_k=top_k * 2,
            return_details=True
        )

        # 提取Action统计
        action_stats = {}

        for skill in matching_skills:
            # 获取完整技能数据
            skill_data = self.get_skill_by_id(skill['skill_id'])
            if not skill_data:
                continue

            # 统计Action类型
            for track in skill_data.get('tracks', []):
                for action in track.get('actions', []):
                    action_type = action.get('type', '')
                    if action_type:
                        if action_type not in action_stats:
                            action_stats[action_type] = {
                                'count': 0,
                                'examples': []
                            }
                        action_stats[action_type]['count'] += 1

                        # 保存参数示例
                        if len(action_stats[action_type]['examples']) < 2:
                            action_stats[action_type]['examples'].append({
                                'skill_name': skill_data.get('skillName', ''),
                                'parameters': action.get('parameters', {})
                            })

        # 按出现频率排序
        recommended_actions = []
        for action_type, stats in sorted(
            action_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:top_k]:
            recommended_actions.append({
                'action_type': action_type,
                'frequency': stats['count'],
                'examples': stats['examples']
            })

        logger.info(f"Recommended {len(recommended_actions)} actions for context: {context}")
        return recommended_actions

    def update_skill(self, file_path: str) -> bool:
        """
        更新单个技能的索引

        Args:
            file_path: 技能文件路径

        Returns:
            是否成功
        """
        try:
            # 解析技能
            skill_data = self.skill_indexer.parse_skill_file(file_path)
            if not skill_data:
                return False

            # 生成文档ID
            doc_id = hashlib.md5(file_path.encode('utf-8')).hexdigest()

            # 构建搜索文本
            search_text = self.skill_indexer.build_search_text(skill_data)

            # 生成嵌入
            embedding = self.embedding_generator.encode(search_text)

            # 准备元数据
            metadata = {
                'skill_id': skill_data.get('skillId', ''),
                'skill_name': skill_data.get('skillName', ''),
                'file_name': skill_data.get('file_name', ''),
                'file_path': file_path,
                'file_hash': skill_data.get('file_hash', ''),
                'last_modified': skill_data.get('last_modified', ''),
                'total_duration': skill_data.get('totalDuration', 0),
                'frame_rate': skill_data.get('frameRate', 30),
                'num_tracks': len(skill_data.get('tracks', [])),
                'num_actions': sum(len(track.get('actions', [])) for track in skill_data.get('tracks', []))
            }

            # 更新向量数据库
            success = self.vector_store.update_document(
                document_id=doc_id,
                document=search_text,
                embedding=embedding,
                metadata=metadata
            )

            if success:
                logger.info(f"Updated skill: {file_path}")
                # 清空缓存
                if self._query_cache is not None:
                    self._query_cache.clear()

            return success

        except Exception as e:
            logger.error(f"Error updating skill {file_path}: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取RAG引擎统计信息"""
        vector_stats = self.vector_store.get_statistics()
        embedding_cache = self.embedding_generator.get_cache_info()
        action_stats = self.action_indexer.get_statistics()

        return {
            'engine_stats': self._stats,
            'vector_store': vector_stats,
            'embedding_cache': embedding_cache,
            'query_cache_size': len(self._query_cache) if self._query_cache else 0,
            'action_stats': action_stats
        }

    # ============ Action相关方法 ============

    def index_actions(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        索引所有Action到向量数据库

        Args:
            force_rebuild: 是否强制重建索引

        Returns:
            索引结果统计
        """
        logger.info(f"Starting action indexing (force_rebuild={force_rebuild})")
        start_time = datetime.now()

        # 1. 准备Action数据
        prepared_actions = self.action_indexer.prepare_actions_for_indexing()

        if not prepared_actions:
            logger.warning("No actions found to index")
            return {"status": "no_actions", "count": 0}

        # 2. 提取数据
        documents = []
        metadatas = []
        ids = []

        for action in prepared_actions:
            documents.append(action['search_text'])
            metadatas.append(action['metadata'])
            ids.append(action['id'])

        # 3. 生成嵌入向量
        logger.info(f"Generating embeddings for {len(documents)} actions...")
        embeddings = self.embedding_generator.encode_batch(
            documents,
            show_progress=True
        )

        # 4. 存储到向量数据库
        logger.info("Storing action embeddings to vector database...")

        # 如果是强制重建，先清空
        if force_rebuild:
            self.action_vector_store.clear()

        # 添加文档
        success = self.action_vector_store.add_documents(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        # 5. 统计
        elapsed_time = (datetime.now() - start_time).total_seconds()

        if success:
            result = {
                "status": "success",
                "count": len(prepared_actions),
                "elapsed_time": elapsed_time
            }
            logger.info(f"Action indexing completed: {len(prepared_actions)} actions in {elapsed_time:.2f}s")
        else:
            result = {
                "status": "error",
                "count": 0,
                "message": "Failed to add action documents to vector store"
            }
            logger.error("Action indexing failed")

        return result

    def search_actions(
        self,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
        return_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜索Action类型

        Args:
            query: 搜索查询（如"造成伤害"、"移动角色"）
            top_k: 返回结果数量
            category_filter: 按分类过滤（如"Damage"、"Movement"）
            return_details: 是否返回详细参数信息

        Returns:
            匹配的Action列表
        """
        top_k = top_k or self.top_k

        # 1. 生成查询向量
        query_embedding = self.embedding_generator.encode(
            query,
            use_cache=True,
            prompt_name="query"
        )

        # 2. 构建过滤条件
        where_filter = None
        if category_filter:
            where_filter = {"category": category_filter}

        # 3. 向量检索
        results = self.action_vector_store.query(
            query_embeddings=[query_embedding],
            top_k=top_k,
            where=where_filter
        )

        # 4. 处理结果
        matched_actions = []

        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                action_id = results['ids'][0][i]
                distance = results['distances'][0][i]
                metadata = results['metadatas'][0][i]

                # 转换距离为相似度
                similarity = 1.0 - distance

                # 过滤低相似度结果
                if similarity < self.similarity_threshold:
                    continue

                action_result = {
                    'type_name': metadata.get('type_name', ''),
                    'display_name': metadata.get('display_name', ''),
                    'category': metadata.get('category', ''),
                    'similarity': round(similarity, 4)
                }

                # 如果需要详细信息，从action_indexer获取完整定义
                if return_details:
                    type_name = metadata.get('type_name', '')
                    action_def = self.action_indexer.get_action_by_type(type_name)
                    if action_def:
                        action_result['parameters'] = action_def.get('parameters', [])
                        action_result['description'] = action_def.get('description', '')
                        action_result['full_type_name'] = action_def.get('fullTypeName', '')

                matched_actions.append(action_result)

        logger.info(f"Action search query '{query[:50]}' returned {len(matched_actions)} results")
        return matched_actions

    def get_action_by_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        根据类型名获取Action详细信息

        Args:
            type_name: Action类型名（如"DamageAction"）

        Returns:
            Action详细信息，未找到返回None
        """
        return self.action_indexer.get_action_by_type(type_name)

    def get_actions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取指定分类的所有Action

        Args:
            category: Action分类

        Returns:
            Action列表
        """
        return self.action_indexer.get_actions_by_category(category)

    def get_action_categories(self) -> List[str]:
        """
        获取所有Action分类

        Returns:
            分类列表
        """
        actions = self.action_indexer.get_all_actions()
        categories = set(action.get('category', 'Other') for action in actions)
        return sorted(list(categories))


if __name__ == "__main__":
    # 测试代码
    import yaml
    logging.basicConfig(level=logging.INFO)

    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 创建RAG引擎
    engine = RAGEngine(config)

    # 索引技能
    print("\n=== Indexing Skills ===")
    index_result = engine.index_skills(force_rebuild=True)
    print(f"Index result: {index_result}")

    # 搜索技能
    print("\n=== Searching Skills ===")
    results = engine.search_skills("火焰伤害技能", top_k=3, return_details=True)
    for i, skill in enumerate(results, 1):
        print(f"\n{i}. {skill['skill_name']} (相似度: {skill['similarity']:.3f})")
        print(f"   文件: {skill['file_name']}")

    # 推荐Action
    print("\n=== Recommending Actions ===")
    actions = engine.recommend_actions("造成伤害并击退敌人", top_k=3)
    for i, action in enumerate(actions, 1):
        print(f"\n{i}. {action['action_type']} (频率: {action['frequency']})")

    # 统计信息
    print("\n=== Statistics ===")
    stats = engine.get_statistics()
    print(f"Total indexed: {stats['engine_stats']['total_indexed']}")
    print(f"Total queries: {stats['engine_stats']['total_queries']}")
