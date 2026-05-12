"""
用户偏好记忆模块 (借鉴 OpenViking 的 Memory 进化机制)
记录和学习用户的技能配置偏好，让系统越用越智能

特性:
- 记录用户的 Action 选择偏好
- 学习用户常用的参数组合
- 基于历史推荐相似配置
- 支持偏好的导出和导入
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ActionUsage:
    """Action 使用记录"""
    action_type: str
    count: int = 0
    last_used: str = ""
    common_params: Dict[str, List[Any]] = field(default_factory=dict)
    contexts: List[str] = field(default_factory=list)  # 使用场景


@dataclass
class UserPreference:
    """用户偏好配置"""
    user_id: str = "default"
    
    # Action 偏好
    action_usage: Dict[str, ActionUsage] = field(default_factory=dict)
    action_sequences: List[List[str]] = field(default_factory=list)  # 常用 Action 序列
    
    # 参数偏好
    param_defaults: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 技能风格偏好
    preferred_skill_styles: List[str] = field(default_factory=list)
    
    # 元数据
    created_at: str = ""
    updated_at: str = ""
    total_interactions: int = 0


class PreferenceMemory:
    """偏好记忆管理器"""
    
    def __init__(
        self, 
        storage_path: str = "Data/user_preferences",
        user_id: str = "default"
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.user_id = user_id
        
        # 加载或创建偏好
        self._preference = self._load_preference()
        
        # 短期记忆 (会话内)
        self._session_actions: List[str] = []
        self._session_params: Dict[str, Dict[str, Any]] = {}
    
    def _preference_file(self) -> Path:
        return self.storage_path / f"{self.user_id}_preference.json"
    
    def _load_preference(self) -> UserPreference:
        """加载用户偏好"""
        pref_file = self._preference_file()
        if pref_file.exists():
            try:
                with open(pref_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 重建 ActionUsage 对象
                action_usage = {}
                for k, v in data.get('action_usage', {}).items():
                    action_usage[k] = ActionUsage(**v)
                data['action_usage'] = action_usage
                
                return UserPreference(**data)
            except Exception as e:
                logger.warning(f"Failed to load preference: {e}")
        
        return UserPreference(
            user_id=self.user_id,
            created_at=datetime.now().isoformat()
        )
    
    def _save_preference(self):
        """保存用户偏好"""
        self._preference.updated_at = datetime.now().isoformat()
        
        # 转换为可序列化格式
        data = asdict(self._preference)
        data['action_usage'] = {
            k: asdict(v) for k, v in self._preference.action_usage.items()
        }
        
        try:
            with open(self._preference_file(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save preference: {e}")
    
    def record_action_usage(
        self,
        action_type: str,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ):
        """
        记录 Action 使用
        
        Args:
            action_type: Action 类型名
            params: 使用的参数
            context: 使用场景描述
        """
        # 更新 Action 使用统计
        if action_type not in self._preference.action_usage:
            self._preference.action_usage[action_type] = ActionUsage(
                action_type=action_type
            )
        
        usage = self._preference.action_usage[action_type]
        usage.count += 1
        usage.last_used = datetime.now().isoformat()
        
        # 记录常用参数
        if params:
            for k, v in params.items():
                if k not in usage.common_params:
                    usage.common_params[k] = []
                if v not in usage.common_params[k]:
                    usage.common_params[k].append(v)
                # 保留最常用的 5 个值
                usage.common_params[k] = usage.common_params[k][-5:]
        
        # 记录使用场景
        if context and context not in usage.contexts:
            usage.contexts.append(context)
            usage.contexts = usage.contexts[-10:]  # 保留最近 10 个场景
        
        # 记录会话内使用
        self._session_actions.append(action_type)
        
        self._preference.total_interactions += 1
        self._save_preference()
    
    def record_action_sequence(self, actions: List[str]):
        """记录 Action 序列（用于学习常用组合）"""
        if len(actions) >= 2:
            self._preference.action_sequences.append(actions)
            # 保留最近 50 个序列
            self._preference.action_sequences = self._preference.action_sequences[-50:]
            self._save_preference()

    def get_recommended_actions(
        self,
        context: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        基于历史使用推荐 Action

        Args:
            context: 当前场景描述（可选）
            top_k: 返回数量

        Returns:
            [(action_type, score), ...] 推荐列表
        """
        if not self._preference.action_usage:
            return []

        # 计算每个 Action 的推荐分数
        scores: Dict[str, float] = {}

        for action_type, usage in self._preference.action_usage.items():
            # 基础分 = 使用次数
            base_score = usage.count

            # 时间衰减: 最近使用的加分
            recency_bonus = 0.0
            if usage.last_used:
                try:
                    last_dt = datetime.fromisoformat(usage.last_used)
                    days_ago = (datetime.now() - last_dt).days
                    recency_bonus = max(0, 10 - days_ago)  # 10天内有加分
                except:
                    pass

            # 场景匹配加分
            context_bonus = 0.0
            if context and usage.contexts:
                # 简单匹配: 检查是否有相似场景
                context_lower = context.lower()
                for ctx in usage.contexts:
                    if ctx.lower() in context_lower or context_lower in ctx.lower():
                        context_bonus += 5.0
                        break

            scores[action_type] = base_score + recency_bonus + context_bonus

        # 排序并返回 top_k
        sorted_actions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_actions[:top_k]

    def get_param_suggestions(
        self,
        action_type: str,
        param_name: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """
        获取 Action 的参数建议

        Args:
            action_type: Action 类型
            param_name: 特定参数名（可选）

        Returns:
            {param_name: [常用值列表], ...}
        """
        if action_type not in self._preference.action_usage:
            return {}

        usage = self._preference.action_usage[action_type]

        if param_name:
            return {param_name: usage.common_params.get(param_name, [])}

        return dict(usage.common_params)

    def get_common_sequences(
        self,
        min_count: int = 2,
        max_length: int = 5
    ) -> List[Tuple[List[str], int]]:
        """
        获取常用 Action 序列

        Args:
            min_count: 最小出现次数
            max_length: 最大序列长度

        Returns:
            [(序列, 出现次数), ...] 按次数降序
        """
        if not self._preference.action_sequences:
            return []

        # 统计序列出现次数
        sequence_counts: Counter = Counter()
        for seq in self._preference.action_sequences:
            # 截取到最大长度
            truncated = tuple(seq[:max_length])
            sequence_counts[truncated] += 1

        # 过滤并排序
        result = [
            (list(seq), count)
            for seq, count in sequence_counts.most_common()
            if count >= min_count
        ]

        return result

    def get_next_action_prediction(self, current_actions: List[str]) -> List[Tuple[str, float]]:
        """
        预测下一个可能的 Action（基于序列模式）

        Args:
            current_actions: 当前已选的 Action 序列

        Returns:
            [(action_type, probability), ...] 预测列表
        """
        if not current_actions or not self._preference.action_sequences:
            return self.get_recommended_actions(top_k=3)

        # 查找匹配的序列前缀
        next_action_counts: Counter = Counter()
        total_matches = 0

        current_len = len(current_actions)
        for seq in self._preference.action_sequences:
            if len(seq) > current_len:
                # 检查前缀是否匹配
                if seq[:current_len] == current_actions:
                    next_action = seq[current_len]
                    next_action_counts[next_action] += 1
                    total_matches += 1

        if total_matches == 0:
            return self.get_recommended_actions(top_k=3)

        # 计算概率
        return [
            (action, count / total_matches)
            for action, count in next_action_counts.most_common(5)
        ]

    def record_skill_style(self, style: str):
        """记录偏好的技能风格"""
        if style not in self._preference.preferred_skill_styles:
            self._preference.preferred_skill_styles.append(style)
            self._preference.preferred_skill_styles = \
                self._preference.preferred_skill_styles[-10:]
            self._save_preference()

    def get_preference_summary(self) -> Dict[str, Any]:
        """获取偏好摘要"""
        top_actions = sorted(
            self._preference.action_usage.items(),
            key=lambda x: x[1].count,
            reverse=True
        )[:5]

        return {
            'user_id': self.user_id,
            'total_interactions': self._preference.total_interactions,
            'top_actions': [(a, u.count) for a, u in top_actions],
            'preferred_styles': self._preference.preferred_skill_styles,
            'sequence_count': len(self._preference.action_sequences),
            'created_at': self._preference.created_at,
            'updated_at': self._preference.updated_at
        }

    def end_session(self):
        """结束会话，保存会话内的序列"""
        if len(self._session_actions) >= 2:
            self.record_action_sequence(self._session_actions)
        self._session_actions = []
        self._session_params = {}

    def export_preferences(self) -> Dict[str, Any]:
        """导出偏好配置"""
        data = asdict(self._preference)
        data['action_usage'] = {
            k: asdict(v) for k, v in self._preference.action_usage.items()
        }
        return data

    def import_preferences(self, data: Dict[str, Any]):
        """导入偏好配置"""
        try:
            action_usage = {}
            for k, v in data.get('action_usage', {}).items():
                action_usage[k] = ActionUsage(**v)
            data['action_usage'] = action_usage

            self._preference = UserPreference(**data)
            self._save_preference()
            logger.info(f"Imported preferences for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            raise

