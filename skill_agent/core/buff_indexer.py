"""
Buff 索引器模块
用于索引和检索 Buff 效果、触发器数据
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class BuffEffectEntry:
    """Buff 效果条目"""
    type_name: str
    full_type_name: str
    namespace_name: str
    assembly_name: str
    display_name: str
    description: str
    category: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    search_text: str = ""
    
    def __post_init__(self):
        """生成搜索文本"""
        parts = [
            self.display_name,
            self.description,
            self.type_name,
            self.category
        ]
        # 添加参数信息
        for param in self.parameters:
            parts.append(param.get('label', ''))
            parts.append(param.get('infoBox', ''))
        self.search_text = '\n'.join(filter(None, parts))


@dataclass
class BuffTriggerEntry:
    """Buff 触发器条目"""
    type_name: str
    full_type_name: str
    namespace_name: str
    assembly_name: str
    display_name: str
    description: str
    category: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    search_text: str = ""
    
    def __post_init__(self):
        """生成搜索文本"""
        parts = [
            self.display_name,
            self.description,
            self.type_name,
            self.category
        ]
        for param in self.parameters:
            parts.append(param.get('label', ''))
            parts.append(param.get('infoBox', ''))
        self.search_text = '\n'.join(filter(None, parts))


class BuffIndexer:
    """Buff 索引器 - 管理 Buff 效果和触发器的索引"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化 Buff 索引器
        
        Args:
            data_dir: 数据目录路径，默认为 Data/Buffs
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "Data" / "Buffs"
        self.data_dir = Path(data_dir)
        
        self.effects: Dict[str, BuffEffectEntry] = {}
        self.triggers: Dict[str, BuffTriggerEntry] = {}
        self.enums: Dict[str, List[Dict[str, Any]]] = {}
        
        self._loaded = False
    
    def load_index(self) -> Tuple[int, int]:
        """
        加载 Buff 索引
        
        Returns:
            (效果数量, 触发器数量)
        """
        effect_count = self._load_effects()
        trigger_count = self._load_triggers()
        self._load_enums()
        
        self._loaded = True
        logger.info(f"Loaded {effect_count} buff effects, {trigger_count} buff triggers")
        
        return effect_count, trigger_count
    
    def _load_effects(self) -> int:
        """加载 Buff 效果数据"""
        effects_dir = self.data_dir / "Effects"
        if not effects_dir.exists():
            logger.warning(f"Effects directory not found: {effects_dir}")
            return 0
        
        count = 0
        for json_file in effects_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                effect_data = data.get('effect', {})
                entry = BuffEffectEntry(
                    type_name=effect_data.get('typeName', ''),
                    full_type_name=effect_data.get('fullTypeName', ''),
                    namespace_name=effect_data.get('namespaceName', ''),
                    assembly_name=effect_data.get('assemblyName', ''),
                    display_name=effect_data.get('displayName', ''),
                    description=effect_data.get('description', ''),
                    category=effect_data.get('category', ''),
                    parameters=effect_data.get('parameters', [])
                )
                
                self.effects[entry.type_name] = entry
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to load effect {json_file}: {e}")
        
        return count
    
    def _load_triggers(self) -> int:
        """加载 Buff 触发器数据"""
        triggers_dir = self.data_dir / "Triggers"
        if not triggers_dir.exists():
            logger.warning(f"Triggers directory not found: {triggers_dir}")
            return 0
        
        count = 0
        for json_file in triggers_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                trigger_data = data.get('trigger', {})
                entry = BuffTriggerEntry(
                    type_name=trigger_data.get('typeName', ''),
                    full_type_name=trigger_data.get('fullTypeName', ''),
                    namespace_name=trigger_data.get('namespaceName', ''),
                    assembly_name=trigger_data.get('assemblyName', ''),
                    display_name=trigger_data.get('displayName', ''),
                    description=trigger_data.get('description', ''),
                    category=trigger_data.get('category', ''),
                    parameters=trigger_data.get('parameters', [])
                )
                
                self.triggers[entry.type_name] = entry
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to load trigger {json_file}: {e}")

        return count

    def _load_enums(self):
        """加载 Buff 枚举数据"""
        enum_file = self.data_dir / "BuffEnums.json"
        if not enum_file.exists():
            logger.warning(f"Enum file not found: {enum_file}")
            return

        try:
            with open(enum_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载所有枚举
            for key, values in data.items():
                if key not in ('version', 'exportTime') and isinstance(values, list):
                    self.enums[key] = values

            logger.info(f"Loaded {len(self.enums)} enum types")

        except Exception as e:
            logger.error(f"Failed to load enums: {e}")

    def search_effects(self, query: str, top_k: int = 5) -> List[BuffEffectEntry]:
        """
        搜索 Buff 效果

        Args:
            query: 搜索查询
            top_k: 返回数量

        Returns:
            匹配的效果列表
        """
        if not self._loaded:
            self.load_index()

        query_lower = query.lower()
        results = []

        for effect in self.effects.values():
            score = self._calculate_match_score(query_lower, effect.search_text.lower())
            if score > 0:
                results.append((effect, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        return [r[0] for r in results[:top_k]]

    def search_triggers(self, query: str, top_k: int = 5) -> List[BuffTriggerEntry]:
        """
        搜索 Buff 触发器

        Args:
            query: 搜索查询
            top_k: 返回数量

        Returns:
            匹配的触发器列表
        """
        if not self._loaded:
            self.load_index()

        query_lower = query.lower()
        results = []

        for trigger in self.triggers.values():
            score = self._calculate_match_score(query_lower, trigger.search_text.lower())
            if score > 0:
                results.append((trigger, score))

        results.sort(key=lambda x: x[1], reverse=True)

        return [r[0] for r in results[:top_k]]

    def get_effect_by_name(self, type_name: str) -> Optional[BuffEffectEntry]:
        """根据类型名获取效果"""
        if not self._loaded:
            self.load_index()
        return self.effects.get(type_name)

    def get_trigger_by_name(self, type_name: str) -> Optional[BuffTriggerEntry]:
        """根据类型名获取触发器"""
        if not self._loaded:
            self.load_index()
        return self.triggers.get(type_name)

    def get_all_effects(self) -> List[BuffEffectEntry]:
        """获取所有效果"""
        if not self._loaded:
            self.load_index()
        return list(self.effects.values())

    def get_all_triggers(self) -> List[BuffTriggerEntry]:
        """获取所有触发器"""
        if not self._loaded:
            self.load_index()
        return list(self.triggers.values())

    def get_enum_values(self, enum_name: str) -> List[Dict[str, Any]]:
        """获取枚举值列表"""
        if not self._loaded:
            self.load_index()
        return self.enums.get(enum_name, [])

    def _calculate_match_score(self, query: str, text: str) -> float:
        """计算匹配分数"""
        if not query or not text:
            return 0.0

        # 完全匹配
        if query in text:
            return 1.0

        # 词语匹配
        query_words = query.split()
        matched_words = sum(1 for word in query_words if word in text)

        if matched_words > 0:
            return matched_words / len(query_words) * 0.8

        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于 API 响应）"""
        return {
            'effects': {k: self._entry_to_dict(v) for k, v in self.effects.items()},
            'triggers': {k: self._entry_to_dict(v) for k, v in self.triggers.items()},
            'enums': self.enums,
            'stats': {
                'effect_count': len(self.effects),
                'trigger_count': len(self.triggers),
                'enum_count': len(self.enums)
            }
        }

    def _entry_to_dict(self, entry) -> Dict[str, Any]:
        """将条目转换为字典"""
        return {
            'typeName': entry.type_name,
            'fullTypeName': entry.full_type_name,
            'namespaceName': entry.namespace_name,
            'assemblyName': entry.assembly_name,
            'displayName': entry.display_name,
            'description': entry.description,
            'category': entry.category,
            'parameters': entry.parameters
        }


# 全局单例
_buff_indexer: Optional[BuffIndexer] = None


def get_buff_indexer() -> BuffIndexer:
    """获取全局 Buff 索引器实例"""
    global _buff_indexer
    if _buff_indexer is None:
        _buff_indexer = BuffIndexer()
        _buff_indexer.load_index()
    return _buff_indexer


def reload_buff_index() -> Tuple[int, int]:
    """重新加载 Buff 索引"""
    global _buff_indexer
    _buff_indexer = BuffIndexer()
    return _buff_indexer.load_index()

