"""
重排序模块 (Reranking)
支持Cross-Encoder重排序和基于规则的重排序
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """重排序结果"""
    doc_id: str
    original_rank: int
    new_rank: int
    original_score: float
    rerank_score: float
    document: str = ""
    metadata: Dict[str, Any] = None


class BaseReranker(ABC):
    """重排序器基类"""
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """重排序文档"""
        pass


class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder重排序器
    使用sentence-transformers的CrossEncoder模型
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        max_length: int = 512
    ):
        """
        Args:
            model_name: Cross-Encoder模型名称
            device: 运行设备
            max_length: 最大序列长度
        """
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self._model = None
    
    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder model: {self.model_name}")
                self._model = CrossEncoder(
                    self.model_name,
                    max_length=self.max_length,
                    device=self.device
                )
                logger.info("CrossEncoder model loaded successfully")
            except ImportError:
                logger.warning("sentence-transformers not installed, using fallback")
                self._model = "fallback"
            except Exception as e:
                logger.error(f"Failed to load CrossEncoder: {e}")
                self._model = "fallback"
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        使用Cross-Encoder重排序
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档需包含 'doc_id', 'document', 'score'
            top_k: 返回top_k个结果
        
        Returns:
            重排序后的结果列表
        """
        if not documents:
            return []
        
        self._load_model()
        
        # 准备输入对
        pairs = []
        for doc in documents:
            doc_text = doc.get('document', '') or doc.get('text', '')
            pairs.append([query, doc_text])
        
        # 计算重排序分数
        if self._model == "fallback":
            # 降级：使用原始分数
            scores = [doc.get('score', doc.get('fused_score', 0.0)) for doc in documents]
        else:
            scores = self._model.predict(pairs)
        
        # 构建结果
        results = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            results.append(RerankResult(
                doc_id=doc.get('doc_id', str(i)),
                original_rank=i,
                new_rank=-1,  # 稍后填充
                original_score=doc.get('score', doc.get('fused_score', 0.0)),
                rerank_score=float(score),
                document=doc.get('document', ''),
                metadata=doc.get('metadata', {})
            ))
        
        # 按重排序分数排序
        results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # 更新新排名
        for i, result in enumerate(results):
            result.new_rank = i
        
        # 返回top_k
        if top_k:
            results = results[:top_k]
        
        return results


class RuleBasedReranker(BaseReranker):
    """
    基于规则的重排序器
    适用于不需要额外模型的场景
    """
    
    def __init__(self):
        self.boost_rules: List[Tuple[Callable, float]] = []
        self.penalty_rules: List[Tuple[Callable, float]] = []
    
    def add_boost_rule(
        self,
        condition: Callable[[Dict[str, Any], str], bool],
        boost_factor: float
    ):
        """
        添加加分规则
        
        Args:
            condition: 条件函数 (doc, query) -> bool
            boost_factor: 加分因子 (如 1.2 表示加20%)
        """
        self.boost_rules.append((condition, boost_factor))
    
    def add_penalty_rule(
        self,
        condition: Callable[[Dict[str, Any], str], bool],
        penalty_factor: float
    ):
        """
        添加减分规则
        
        Args:
            condition: 条件函数 (doc, query) -> bool
            penalty_factor: 减分因子 (如 0.8 表示减20%)
        """
        self.penalty_rules.append((condition, penalty_factor))
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """基于规则重排序"""
        if not documents:
            return []
        
        results = []
        
        for i, doc in enumerate(documents):
            original_score = doc.get('score', doc.get('fused_score', 0.0))
            adjusted_score = original_score
            
            # 应用加分规则
            for condition, factor in self.boost_rules:
                try:
                    if condition(doc, query):
                        adjusted_score *= factor
                except Exception:
                    pass
            
            # 应用减分规则
            for condition, factor in self.penalty_rules:
                try:
                    if condition(doc, query):
                        adjusted_score *= factor
                except Exception:
                    pass
            
            results.append(RerankResult(
                doc_id=doc.get('doc_id', str(i)),
                original_rank=i,
                new_rank=-1,
                original_score=original_score,
                rerank_score=adjusted_score,
                document=doc.get('document', ''),
                metadata=doc.get('metadata', {})
            ))
        
        # 排序
        results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(results):
            result.new_rank = i
        
        if top_k:
            results = results[:top_k]
        
        return results


class SkillReranker(RuleBasedReranker):
    """
    技能专用重排序器
    内置游戏技能相关的重排序规则
    """
    
    def __init__(self):
        super().__init__()
        self._setup_skill_rules()
    
    def _setup_skill_rules(self):
        """设置技能相关的重排序规则"""
        
        # 规则1: 技能名称完全匹配加分
        def name_exact_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            skill_name = metadata.get('skill_name', '').lower()
            return skill_name and skill_name in query.lower()
        
        self.add_boost_rule(name_exact_match, 1.5)
        
        # 规则2: Action类型匹配加分
        def action_type_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            action_types = metadata.get('action_type_list', '[]')
            query_lower = query.lower()
            
            # 检查常见Action关键词
            action_keywords = {
                'damage': ['伤害', 'damage', '攻击'],
                'heal': ['治疗', 'heal', '回血'],
                'movement': ['移动', 'move', '位移', '冲刺'],
                'control': ['控制', 'control', '眩晕', '定身'],
            }
            
            for action_type, keywords in action_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    if action_type.lower() in action_types.lower():
                        return True
            return False
        
        self.add_boost_rule(action_type_match, 1.3)
        
        # 规则3: 文档过短减分
        def doc_too_short(doc: Dict, query: str) -> bool:
            document = doc.get('document', '')
            return len(document) < 50
        
        self.add_penalty_rule(doc_too_short, 0.7)
        
        # 规则4: 包含查询中数值的加分
        def contains_query_numbers(doc: Dict, query: str) -> bool:
            import re
            numbers_in_query = re.findall(r'\d+', query)
            if not numbers_in_query:
                return False
            
            document = doc.get('document', '')
            for num in numbers_in_query:
                if num in document:
                    return True
            return False
        
        self.add_boost_rule(contains_query_numbers, 1.2)

        # 规则5: 技能描述与查询的关键词重叠加分
        def keyword_overlap(doc: Dict, query: str) -> bool:
            document = doc.get('document', '').lower()
            query_words = set(query.lower().split())
            # 移除停用词
            stopwords = {'的', '是', '在', '和', '与', '或', '一个', '这个', 'the', 'a', 'an', 'is', 'are'}
            query_words = query_words - stopwords
            if not query_words:
                return False
            overlap_count = sum(1 for word in query_words if word in document)
            return overlap_count >= len(query_words) * 0.5

        self.add_boost_rule(keyword_overlap, 1.25)

        # 规则6: 技能复杂度匹配（根据查询推断）
        def complexity_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            num_actions = metadata.get('num_actions', 0)
            query_lower = query.lower()

            # 简单技能关键词
            simple_keywords = ['简单', '基础', '普通', 'simple', 'basic']
            # 复杂技能关键词
            complex_keywords = ['复杂', '高级', '连招', '组合', 'complex', 'advanced', 'combo']

            is_simple_query = any(kw in query_lower for kw in simple_keywords)
            is_complex_query = any(kw in query_lower for kw in complex_keywords)

            if is_simple_query and num_actions <= 3:
                return True
            if is_complex_query and num_actions >= 5:
                return True
            return False

        self.add_boost_rule(complexity_match, 1.2)


class ActionReranker(RuleBasedReranker):
    """
    Action专用重排序器
    """
    
    def __init__(self):
        super().__init__()
        self._setup_action_rules()
    
    def _setup_action_rules(self):
        """设置Action相关的重排序规则"""
        
        # 规则1: 类型名称匹配加分
        def type_name_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            type_name = metadata.get('type_name', '').lower()
            display_name = metadata.get('display_name', '').lower()
            query_lower = query.lower()
            return type_name in query_lower or display_name in query_lower
        
        self.add_boost_rule(type_name_match, 1.5)
        
        # 规则2: 分类匹配加分
        def category_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            category = metadata.get('category', '').lower()
            query_lower = query.lower()
            
            category_keywords = {
                'damage': ['伤害', 'damage', '攻击'],
                'heal': ['治疗', 'heal'],
                'movement': ['移动', 'move'],
                'control': ['控制', 'control'],
                'buff': ['buff', '增益'],
                'debuff': ['debuff', '减益'],
            }
            
            for cat, keywords in category_keywords.items():
                if cat in category:
                    if any(kw in query_lower for kw in keywords):
                        return True
            return False
        
        self.add_boost_rule(category_match, 1.3)
        
        # 规则3: 参数数量适中加分（3-8个参数）
        def reasonable_param_count(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            param_count = metadata.get('param_count', 0)
            return 3 <= param_count <= 8

        self.add_boost_rule(reasonable_param_count, 1.1)

        # 规则4: 参数名称匹配加分
        def param_name_match(doc: Dict, query: str) -> bool:
            metadata = doc.get('metadata', {})
            param_names = metadata.get('param_names', '').lower()
            query_lower = query.lower()

            # 常见参数关键词映射
            param_keywords = {
                'damage': ['伤害', 'damage', '攻击力'],
                'duration': ['持续', 'duration', '时间'],
                'range': ['范围', 'range', '距离'],
                'speed': ['速度', 'speed', '快'],
                'target': ['目标', 'target', '敌人'],
            }

            for param, keywords in param_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    if param in param_names:
                        return True
            return False

        self.add_boost_rule(param_name_match, 1.2)

        # 规则5: 描述相关性加分
        def description_relevance(doc: Dict, query: str) -> bool:
            document = doc.get('document', '').lower()
            query_lower = query.lower()

            # 计算查询词在描述中的出现次数
            query_words = [w for w in query_lower.split() if len(w) > 1]
            if not query_words:
                return False

            match_count = sum(1 for word in query_words if word in document)
            return match_count >= 2

        self.add_boost_rule(description_relevance, 1.15)


class SemanticReranker(BaseReranker):
    """
    语义重排序器
    基于查询和文档的语义相似度进行重排序
    """

    def __init__(self, embedding_generator=None, weight: float = 0.3):
        """
        Args:
            embedding_generator: 嵌入生成器实例（可选）
            weight: 语义分数权重（与原始分数融合）
        """
        self.embedding_generator = embedding_generator
        self.weight = weight

    def set_embedding_generator(self, generator):
        """设置嵌入生成器"""
        self.embedding_generator = generator

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        基于语义相似度重排序
        """
        if not documents:
            return []

        # 如果没有嵌入生成器，降级为原始分数
        if self.embedding_generator is None:
            return self._fallback_rerank(documents, top_k)

        try:
            # 获取查询向量
            query_embedding = self.embedding_generator.encode(query, prompt_name="query")

            results = []
            for i, doc in enumerate(documents):
                original_score = doc.get('score', doc.get('fused_score', 0.0))

                # 获取文档向量（如果有缓存的话会很快）
                doc_text = doc.get('document', '') or doc.get('text', '')
                if doc_text:
                    doc_embedding = self.embedding_generator.encode(doc_text)
                    # 计算余弦相似度
                    semantic_score = self._cosine_similarity(query_embedding, doc_embedding)
                else:
                    semantic_score = 0.0

                # 融合分数
                combined_score = (1 - self.weight) * original_score + self.weight * semantic_score

                results.append(RerankResult(
                    doc_id=doc.get('doc_id', str(i)),
                    original_rank=i,
                    new_rank=-1,
                    original_score=original_score,
                    rerank_score=combined_score,
                    document=doc_text,
                    metadata=doc.get('metadata', {})
                ))

            # 排序
            results.sort(key=lambda x: x.rerank_score, reverse=True)
            for i, result in enumerate(results):
                result.new_rank = i

            if top_k:
                results = results[:top_k]

            return results

        except Exception as e:
            logger.warning(f"Semantic reranking failed, falling back: {e}")
            return self._fallback_rerank(documents, top_k)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _fallback_rerank(self, documents: List[Dict], top_k: Optional[int]) -> List[RerankResult]:
        """降级重排序（使用原始分数）"""
        results = []
        for i, doc in enumerate(documents):
            results.append(RerankResult(
                doc_id=doc.get('doc_id', str(i)),
                original_rank=i,
                new_rank=i,
                original_score=doc.get('score', doc.get('fused_score', 0.0)),
                rerank_score=doc.get('score', doc.get('fused_score', 0.0)),
                document=doc.get('document', ''),
                metadata=doc.get('metadata', {})
            ))

        if top_k:
            results = results[:top_k]

        return results


class RerankerPipeline:
    """重排序管道 - 支持多阶段重排序"""
    
    def __init__(self):
        self.stages: List[BaseReranker] = []
    
    def add_stage(self, reranker: BaseReranker):
        """添加重排序阶段"""
        self.stages.append(reranker)
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        执行多阶段重排序
        
        每个阶段的输出作为下一阶段的输入
        """
        if not documents:
            return []
        
        current_docs = documents
        
        for i, stage in enumerate(self.stages):
            # 转换为阶段输入格式
            stage_input = []
            for j, doc in enumerate(current_docs):
                if isinstance(doc, RerankResult):
                    stage_input.append({
                        'doc_id': doc.doc_id,
                        'document': doc.document,
                        'score': doc.rerank_score,
                        'metadata': doc.metadata
                    })
                else:
                    stage_input.append(doc)
            
            # 执行重排序
            results = stage.rerank(query, stage_input, top_k=None)
            current_docs = results
            
            logger.debug(f"Rerank stage {i+1} completed, {len(results)} documents")
        
        # 最终截断
        if top_k and isinstance(current_docs[0], RerankResult):
            current_docs = current_docs[:top_k]
        
        return current_docs


def create_skill_reranker_pipeline(
    use_cross_encoder: bool = False,
    use_semantic: bool = False,
    embedding_generator=None
) -> RerankerPipeline:
    """
    创建技能检索的重排序管道

    Args:
        use_cross_encoder: 是否使用Cross-Encoder（需要额外模型）
        use_semantic: 是否使用语义重排序
        embedding_generator: 嵌入生成器（语义重排序需要）
    """
    pipeline = RerankerPipeline()

    # 阶段1: 规则重排序
    pipeline.add_stage(SkillReranker())

    # 阶段2: 语义重排序（可选）
    if use_semantic and embedding_generator:
        pipeline.add_stage(SemanticReranker(embedding_generator))

    # 阶段3: Cross-Encoder（可选）
    if use_cross_encoder:
        pipeline.add_stage(CrossEncoderReranker())

    return pipeline


def create_action_reranker_pipeline(
    use_cross_encoder: bool = False,
    use_semantic: bool = False,
    embedding_generator=None
) -> RerankerPipeline:
    """
    创建Action检索的重排序管道

    Args:
        use_cross_encoder: 是否使用Cross-Encoder（需要额外模型）
        use_semantic: 是否使用语义重排序
        embedding_generator: 嵌入生成器（语义重排序需要）
    """
    pipeline = RerankerPipeline()

    # 阶段1: 规则重排序
    pipeline.add_stage(ActionReranker())

    # 阶段2: 语义重排序（可选）
    if use_semantic and embedding_generator:
        pipeline.add_stage(SemanticReranker(embedding_generator))

    # 阶段3: Cross-Encoder（可选）
    if use_cross_encoder:
        pipeline.add_stage(CrossEncoderReranker())

    return pipeline
