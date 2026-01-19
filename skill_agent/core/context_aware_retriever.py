"""
上下文感知检索模块
支持：编辑上下文推荐、历史查询学习、相似技能关联
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EditContext:
    """编辑上下文"""
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    current_track: Optional[str] = None
    current_action_type: Optional[str] = None
    existing_action_types: List[str] = field(default_factory=list)
    total_duration: int = 0
    frame_rate: int = 30
    current_frame: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryHistoryEntry:
    """查询历史条目"""
    query: str
    timestamp: float
    intent: Optional[str] = None
    result_count: int = 0
    selected_result: Optional[str] = None  # 用户选择的结果
    context: Optional[EditContext] = None


@dataclass
class ContextualRecommendation:
    """上下文推荐结果"""
    item_id: str
    item_type: str  # 'action', 'skill', 'parameter'
    score: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryHistoryManager:
    """查询历史管理器"""
    
    def __init__(
        self,
        max_history: int = 1000,
        history_file: Optional[str] = None
    ):
        self.max_history = max_history
        self.history_file = history_file
        self.history: List[QueryHistoryEntry] = []
        
        # 查询频率统计
        self.query_frequency: Dict[str, int] = defaultdict(int)
        
        # 查询-结果关联
        self.query_result_map: Dict[str, List[str]] = defaultdict(list)
        
        if history_file:
            self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        if self.history_file and Path(self.history_file).exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry_data in data.get('history', []):
                        self.history.append(QueryHistoryEntry(**entry_data))
                    self.query_frequency = defaultdict(int, data.get('frequency', {}))
                    self.query_result_map = defaultdict(list, data.get('result_map', {}))
            except Exception as e:
                logger.warning(f"Failed to load query history: {e}")
    
    def _save_history(self):
        """保存历史记录"""
        if self.history_file:
            try:
                history_dir = Path(self.history_file).parent
                history_dir.mkdir(parents=True, exist_ok=True)
                
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'history': [
                            {
                                'query': e.query,
                                'timestamp': e.timestamp,
                                'intent': e.intent,
                                'result_count': e.result_count,
                                'selected_result': e.selected_result
                            }
                            for e in self.history[-self.max_history:]
                        ],
                        'frequency': dict(self.query_frequency),
                        'result_map': dict(self.query_result_map)
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save query history: {e}")
    
    def add_query(
        self,
        query: str,
        intent: Optional[str] = None,
        result_count: int = 0,
        context: Optional[EditContext] = None
    ):
        """添加查询记录"""
        entry = QueryHistoryEntry(
            query=query,
            timestamp=time.time(),
            intent=intent,
            result_count=result_count,
            context=context
        )
        self.history.append(entry)
        self.query_frequency[query.lower()] += 1
        
        # 限制历史大小
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        self._save_history()
    
    def record_selection(self, query: str, selected_result: str):
        """记录用户选择的结果"""
        # 更新最近的匹配查询
        for entry in reversed(self.history):
            if entry.query.lower() == query.lower():
                entry.selected_result = selected_result
                break
        
        # 更新查询-结果关联
        self.query_result_map[query.lower()].append(selected_result)
        
        self._save_history()
    
    def get_recent_queries(
        self,
        limit: int = 10,
        time_window_hours: int = 24
    ) -> List[QueryHistoryEntry]:
        """获取最近的查询"""
        cutoff = time.time() - (time_window_hours * 3600)
        recent = [e for e in self.history if e.timestamp > cutoff]
        return recent[-limit:]
    
    def get_popular_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取热门查询"""
        sorted_queries = sorted(
            self.query_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]
    
    def get_related_results(self, query: str) -> List[str]:
        """获取查询相关的历史结果"""
        return self.query_result_map.get(query.lower(), [])


class ActionCooccurrenceAnalyzer:
    """Action共现分析器 - 分析哪些Action经常一起使用"""
    
    def __init__(self):
        # 共现矩阵: action_type -> {co_action_type: count}
        self.cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 轨道内共现
        self.track_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Action序列模式
        self.sequence_patterns: Dict[str, List[str]] = defaultdict(list)
    
    def analyze_skill(self, skill_data: Dict[str, Any]):
        """分析技能中的Action共现关系"""
        all_actions = []
        
        for track in skill_data.get('tracks', []):
            track_actions = []
            
            for action in track.get('actions', []):
                action_type = action.get('type', '')
                if action_type:
                    track_actions.append(action_type)
                    all_actions.append(action_type)
            
            # 分析轨道内共现
            for i, action_type in enumerate(track_actions):
                for j, other_type in enumerate(track_actions):
                    if i != j:
                        self.track_cooccurrence[action_type][other_type] += 1
        
        # 分析技能级共现
        unique_actions = list(set(all_actions))
        for i, action_type in enumerate(unique_actions):
            for j, other_type in enumerate(unique_actions):
                if i != j:
                    self.cooccurrence[action_type][other_type] += 1
    
    def get_related_actions(
        self,
        action_type: str,
        top_k: int = 5,
        use_track_level: bool = True
    ) -> List[Tuple[str, float]]:
        """获取相关的Action类型"""
        if use_track_level:
            cooc = self.track_cooccurrence.get(action_type, {})
        else:
            cooc = self.cooccurrence.get(action_type, {})
        
        if not cooc:
            return []
        
        # 计算关联强度
        total = sum(cooc.values())
        related = [
            (other, count / total)
            for other, count in cooc.items()
        ]
        
        # 排序返回
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:top_k]


class ContextAwareRetriever:
    """上下文感知检索器"""
    
    def __init__(
        self,
        rag_engine=None,
        history_file: Optional[str] = None
    ):
        """
        Args:
            rag_engine: RAG引擎实例（可选，用于实际检索）
            history_file: 查询历史文件路径
        """
        self.rag_engine = rag_engine
        self.history_manager = QueryHistoryManager(history_file=history_file)
        self.cooccurrence_analyzer = ActionCooccurrenceAnalyzer()
        
        # 当前编辑上下文
        self.current_context: Optional[EditContext] = None
        
        # 上下文权重配置
        self.context_weights = {
            'existing_actions': 0.3,      # 已有Action的关联推荐
            'track_context': 0.2,         # 当前轨道上下文
            'history_preference': 0.2,    # 历史偏好
            'semantic_similarity': 0.3,   # 语义相似度
        }
    
    def set_context(self, context: EditContext):
        """设置当前编辑上下文"""
        self.current_context = context
        logger.debug(f"Context set: skill={context.skill_name}, track={context.current_track}")
    
    def clear_context(self):
        """清除上下文"""
        self.current_context = None
    
    def update_context_from_skill(self, skill_data: Dict[str, Any]):
        """从技能数据更新上下文"""
        action_types = []
        for track in skill_data.get('tracks', []):
            for action in track.get('actions', []):
                action_type = action.get('type', '')
                if action_type:
                    action_types.append(action_type)
        
        self.current_context = EditContext(
            skill_id=skill_data.get('skillId'),
            skill_name=skill_data.get('skillName'),
            existing_action_types=action_types,
            total_duration=skill_data.get('totalDuration', 0),
            frame_rate=skill_data.get('frameRate', 30)
        )
        
        # 分析共现关系
        self.cooccurrence_analyzer.analyze_skill(skill_data)
    
    def recommend_actions(
        self,
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[ContextualRecommendation]:
        """
        基于上下文推荐Action
        
        Args:
            query: 可选的查询文本
            top_k: 返回数量
        
        Returns:
            推荐列表
        """
        recommendations: Dict[str, ContextualRecommendation] = {}
        
        # 1. 基于已有Action的共现推荐
        if self.current_context and self.current_context.existing_action_types:
            for existing_action in self.current_context.existing_action_types:
                related = self.cooccurrence_analyzer.get_related_actions(
                    existing_action, top_k=3
                )
                for action_type, score in related:
                    if action_type not in self.current_context.existing_action_types:
                        weight = self.context_weights['existing_actions']
                        if action_type not in recommendations:
                            recommendations[action_type] = ContextualRecommendation(
                                item_id=action_type,
                                item_type='action',
                                score=score * weight,
                                reason=f"常与 {existing_action} 一起使用"
                            )
                        else:
                            recommendations[action_type].score += score * weight
        
        # 2. 基于历史偏好的推荐
        popular_queries = self.history_manager.get_popular_queries(limit=5)
        for hist_query, freq in popular_queries:
            related_results = self.history_manager.get_related_results(hist_query)
            for result in related_results[:2]:
                weight = self.context_weights['history_preference']
                score = (freq / 10) * weight  # 归一化频率
                if result not in recommendations:
                    recommendations[result] = ContextualRecommendation(
                        item_id=result,
                        item_type='action',
                        score=score,
                        reason=f"历史常用 (查询: {hist_query})"
                    )
        
        # 3. 基于语义查询的推荐（如果有RAG引擎和查询）
        if query and self.rag_engine:
            try:
                semantic_results = self.rag_engine.search_actions(
                    query=query,
                    top_k=top_k
                )
                weight = self.context_weights['semantic_similarity']
                for result in semantic_results:
                    action_type = result.get('type_name', '')
                    similarity = result.get('similarity', 0.5)
                    
                    if action_type not in recommendations:
                        recommendations[action_type] = ContextualRecommendation(
                            item_id=action_type,
                            item_type='action',
                            score=similarity * weight,
                            reason=f"语义匹配: {query}",
                            metadata=result
                        )
                    else:
                        recommendations[action_type].score += similarity * weight
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")
        
        # 记录查询
        if query:
            self.history_manager.add_query(
                query=query,
                result_count=len(recommendations),
                context=self.current_context
            )
        
        # 排序返回
        sorted_recs = sorted(
            recommendations.values(),
            key=lambda x: x.score,
            reverse=True
        )
        return sorted_recs[:top_k]
    
    def recommend_parameters(
        self,
        action_type: str,
        current_params: Optional[Dict[str, Any]] = None
    ) -> List[ContextualRecommendation]:
        """
        推荐Action参数值
        
        基于：
        - 同类型Action的历史参数值
        - 当前技能的上下文（如总时长、帧率）
        """
        recommendations = []
        
        # 基于上下文推荐帧相关参数
        if self.current_context:
            if action_type in ['AnimationAction', 'MovementAction']:
                # 推荐duration基于技能总时长
                total_duration = self.current_context.total_duration
                if total_duration > 0:
                    suggested_duration = min(30, total_duration // 3)
                    recommendations.append(ContextualRecommendation(
                        item_id='duration',
                        item_type='parameter',
                        score=0.8,
                        reason=f"基于技能总时长 {total_duration} 帧",
                        metadata={'suggested_value': suggested_duration}
                    ))
        
        return recommendations
    
    def get_similar_skills(
        self,
        top_k: int = 5
    ) -> List[ContextualRecommendation]:
        """获取相似技能推荐"""
        if not self.current_context or not self.rag_engine:
            return []
        
        recommendations = []
        
        # 基于当前技能的Action组合搜索相似技能
        if self.current_context.existing_action_types:
            action_str = " ".join(self.current_context.existing_action_types[:5])
            
            try:
                results = self.rag_engine.search_skills(
                    query=action_str,
                    top_k=top_k + 1,  # +1 排除自身
                    return_details=True
                )
                
                for result in results:
                    # 排除当前技能
                    if result.get('skill_id') == self.current_context.skill_id:
                        continue
                    
                    recommendations.append(ContextualRecommendation(
                        item_id=result.get('skill_id', ''),
                        item_type='skill',
                        score=result.get('similarity', 0.0),
                        reason="Action组合相似",
                        metadata={
                            'skill_name': result.get('skill_name'),
                            'file_name': result.get('file_name')
                        }
                    ))
            except Exception as e:
                logger.warning(f"Similar skill search failed: {e}")
        
        return recommendations[:top_k]
    
    def record_user_selection(self, query: str, selected_item: str):
        """记录用户选择，用于学习偏好"""
        self.history_manager.record_selection(query, selected_item)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'history_count': len(self.history_manager.history),
            'popular_queries': self.history_manager.get_popular_queries(5),
            'has_context': self.current_context is not None,
            'context_skill': self.current_context.skill_name if self.current_context else None,
            'cooccurrence_actions': len(self.cooccurrence_analyzer.cooccurrence)
        }
