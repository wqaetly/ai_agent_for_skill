"""
分层上下文系统 (借鉴 OpenViking)
实现 L0/L1/L2 三层上下文，按需加载减少 Token 消耗

层级说明:
- L0 (Abstract): 一句话摘要 (~50 tokens) - 快速识别相关性
- L1 (Overview): 核心信息 (~200 tokens) - 理解结构和关键点
- L2 (Details): 完整详情 - 按需深度读取
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LayeredContext:
    """分层上下文数据结构"""
    # 标识
    context_id: str
    context_type: str  # "skill" | "action"
    source_path: str = ""
    
    # L0: 一句话摘要
    l0_abstract: str = ""
    
    # L1: 核心信息概览
    l1_overview: str = ""
    l1_key_points: List[str] = field(default_factory=list)
    l1_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # L2: 完整详情 (懒加载)
    l2_details: Optional[Dict[str, Any]] = None
    l2_loaded: bool = False
    
    # 元信息
    created_at: str = ""
    content_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不含 L2 详情以节省空间）"""
        d = asdict(self)
        d.pop('l2_details', None)
        d.pop('l2_loaded', None)
        return d


class SkillContextGenerator:
    """技能上下文生成器 - 生成 L0/L1/L2 分层内容"""
    
    def generate_l0_abstract(self, skill_data: Dict[str, Any]) -> str:
        """
        生成 L0 层摘要 - 一句话描述技能
        目标: ~50 tokens
        """
        name = skill_data.get('skillName', '未命名技能')
        desc = skill_data.get('skillDescription', '')
        
        # 提取关键 Action 类型
        action_types = self._extract_action_types(skill_data)
        main_actions = action_types[:3] if action_types else ['未知动作']
        
        # 统计信息
        num_tracks = len(skill_data.get('tracks', []))
        total_actions = sum(
            len(t.get('actions', [])) 
            for t in skill_data.get('tracks', [])
        )
        
        if desc:
            return f"{name}: {desc[:50]}... ({total_actions}个动作)"
        else:
            return f"{name}: 包含 {', '.join(main_actions)} 等 {total_actions} 个动作"
    
    def generate_l1_overview(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成 L1 层概览 - 核心信息和关键点
        目标: ~200 tokens
        """
        # 基础信息
        overview_text = []
        overview_text.append(f"技能: {skill_data.get('skillName', '未命名')}")
        
        if skill_data.get('skillDescription'):
            overview_text.append(f"描述: {skill_data['skillDescription']}")
        
        overview_text.append(f"ID: {skill_data.get('skillId', 'N/A')}")
        overview_text.append(f"持续时间: {skill_data.get('totalDuration', 0)} 帧")
        overview_text.append(f"帧率: {skill_data.get('frameRate', 30)} FPS")
        
        # 提取关键点
        key_points = []
        action_types = self._extract_action_types(skill_data)
        if action_types:
            key_points.append(f"包含动作类型: {', '.join(action_types)}")
        
        # Track 统计
        tracks = skill_data.get('tracks', [])
        enabled_tracks = [t for t in tracks if t.get('enabled', True)]
        key_points.append(f"轨道数: {len(tracks)} (启用: {len(enabled_tracks)})")
        
        # 动作时间线摘要
        timeline_summary = self._generate_timeline_summary(skill_data)
        if timeline_summary:
            key_points.append(f"时间线: {timeline_summary}")
        
        # 元数据
        metadata = {
            'skill_id': skill_data.get('skillId', ''),
            'skill_name': skill_data.get('skillName', ''),
            'total_duration': skill_data.get('totalDuration', 0),
            'frame_rate': skill_data.get('frameRate', 30),
            'num_tracks': len(tracks),
            'num_actions': sum(len(t.get('actions', [])) for t in tracks),
            'action_types': action_types,
        }
        
        return {
            'overview': '\n'.join(overview_text),
            'key_points': key_points,
            'metadata': metadata
        }
    
    def generate_layered_context(
        self, 
        skill_data: Dict[str, Any],
        source_path: str = ""
    ) -> LayeredContext:
        """生成完整的分层上下文"""
        # 计算内容哈希
        content_str = json.dumps(skill_data, sort_keys=True, ensure_ascii=False)
        content_hash = hashlib.md5(content_str.encode('utf-8')).hexdigest()
        
        # 生成 L0
        l0_abstract = self.generate_l0_abstract(skill_data)
        
        # 生成 L1
        l1_result = self.generate_l1_overview(skill_data)
        
        # L2 为原始数据，懒加载
        return LayeredContext(
            context_id=skill_data.get('skillId', content_hash[:8]),
            context_type="skill",
            source_path=source_path,
            l0_abstract=l0_abstract,
            l1_overview=l1_result['overview'],
            l1_key_points=l1_result['key_points'],
            l1_metadata=l1_result['metadata'],
            l2_details=skill_data,  # 存储但默认不序列化
            l2_loaded=True,
            created_at=datetime.now().isoformat(),
            content_hash=content_hash
        )
    
    def _extract_action_types(self, skill_data: Dict[str, Any]) -> List[str]:
        """提取技能中的 Action 类型"""
        action_types = set()
        for track in skill_data.get('tracks', []):
            if not track.get('enabled', True):
                continue
            for action in track.get('actions', []):
                action_type = action.get('type', '')
                if action_type:
                    action_types.add(action_type)
        return sorted(list(action_types))
    
    def _generate_timeline_summary(self, skill_data: Dict[str, Any]) -> str:
        """生成动作时间线摘要"""
        actions_by_frame = []
        for track in skill_data.get('tracks', []):
            if not track.get('enabled', True):
                continue
            for action in track.get('actions', []):
                frame = action.get('frame', 0)
                action_type = action.get('type', 'Unknown')
                actions_by_frame.append((frame, action_type))

        if not actions_by_frame:
            return ""

        actions_by_frame.sort(key=lambda x: x[0])

        # 只显示前3个和最后1个
        if len(actions_by_frame) <= 4:
            return " → ".join(f"{a[1]}@{a[0]}f" for a in actions_by_frame)
        else:
            first_three = [f"{a[1]}@{a[0]}f" for a in actions_by_frame[:3]]
            last_one = f"{actions_by_frame[-1][1]}@{actions_by_frame[-1][0]}f"
            return f"{' → '.join(first_three)} → ... → {last_one}"


class LayeredContextCache:
    """分层上下文缓存管理器"""

    def __init__(self, cache_dir: str = "Data/context_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存 (L0/L1)
        self._memory_cache: Dict[str, LayeredContext] = {}

        # 缓存索引文件
        self._index_file = self.cache_dir / "context_index.json"
        self._load_index()

    def _load_index(self):
        """加载缓存索引"""
        self._index: Dict[str, Dict[str, Any]] = {}
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
                logger.info(f"Loaded {len(self._index)} cached contexts")
            except Exception as e:
                logger.warning(f"Failed to load context index: {e}")

    def _save_index(self):
        """保存缓存索引"""
        try:
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save context index: {e}")

    def get(
        self,
        context_id: str,
        level: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定层级的上下文

        Args:
            context_id: 上下文ID
            level: 层级 (0=摘要, 1=概览, 2=详情)

        Returns:
            对应层级的上下文数据
        """
        # 先查内存缓存
        if context_id in self._memory_cache:
            ctx = self._memory_cache[context_id]
            return self._extract_level(ctx, level)

        # 从索引获取元数据
        if context_id not in self._index:
            return None

        # L0/L1 直接从索引返回
        if level < 2:
            return self._index[context_id].get(f'l{level}')

        # L2 需要加载详情文件
        detail_file = self.cache_dir / f"{context_id}_l2.json"
        if detail_file.exists():
            try:
                with open(detail_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load L2 details for {context_id}: {e}")

        return None

    def _extract_level(self, ctx: LayeredContext, level: int) -> Dict[str, Any]:
        """从 LayeredContext 提取指定层级数据"""
        if level == 0:
            return {
                'context_id': ctx.context_id,
                'abstract': ctx.l0_abstract,
                'type': ctx.context_type
            }
        elif level == 1:
            return {
                'context_id': ctx.context_id,
                'abstract': ctx.l0_abstract,
                'overview': ctx.l1_overview,
                'key_points': ctx.l1_key_points,
                'metadata': ctx.l1_metadata,
                'type': ctx.context_type
            }
        else:
            return {
                'context_id': ctx.context_id,
                'abstract': ctx.l0_abstract,
                'overview': ctx.l1_overview,
                'key_points': ctx.l1_key_points,
                'metadata': ctx.l1_metadata,
                'details': ctx.l2_details,
                'type': ctx.context_type
            }

    def put(self, ctx: LayeredContext, persist_l2: bool = True):
        """
        存储分层上下文

        Args:
            ctx: 分层上下文对象
            persist_l2: 是否持久化 L2 详情到磁盘
        """
        # 存入内存缓存
        self._memory_cache[ctx.context_id] = ctx

        # 更新索引 (只含 L0/L1)
        self._index[ctx.context_id] = {
            'l0': {'abstract': ctx.l0_abstract, 'type': ctx.context_type},
            'l1': {
                'overview': ctx.l1_overview,
                'key_points': ctx.l1_key_points,
                'metadata': ctx.l1_metadata
            },
            'source_path': ctx.source_path,
            'content_hash': ctx.content_hash,
            'created_at': ctx.created_at
        }
        self._save_index()

        # 持久化 L2 详情
        if persist_l2 and ctx.l2_details:
            detail_file = self.cache_dir / f"{ctx.context_id}_l2.json"
            try:
                with open(detail_file, 'w', encoding='utf-8') as f:
                    json.dump(ctx.l2_details, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Failed to persist L2 details for {ctx.context_id}: {e}")

    def is_valid(self, context_id: str, content_hash: str) -> bool:
        """检查缓存是否有效（通过内容哈希比对）"""
        if context_id not in self._index:
            return False
        return self._index[context_id].get('content_hash') == content_hash

    def get_all_l0(self) -> List[Dict[str, Any]]:
        """获取所有 L0 摘要（用于快速浏览）"""
        return [
            {'context_id': cid, **data.get('l0', {})}
            for cid, data in self._index.items()
        ]

    def clear(self):
        """清空缓存"""
        self._memory_cache.clear()
        self._index.clear()
        self._save_index()

        # 删除 L2 文件
        for f in self.cache_dir.glob("*_l2.json"):
            f.unlink()

        logger.info("Layered context cache cleared")

