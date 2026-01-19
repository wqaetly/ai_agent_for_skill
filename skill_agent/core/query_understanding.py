"""
查询理解增强模块
包含：Query Expansion、意图识别、游戏术语映射
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """查询意图类型"""
    SKILL_SEARCH = "skill_search"           # 搜索技能
    ACTION_RECOMMEND = "action_recommend"   # 推荐Action
    PARAMETER_QUERY = "parameter_query"     # 参数查询
    SIMILAR_SKILL = "similar_skill"         # 相似技能
    SKILL_ANALYSIS = "skill_analysis"       # 技能分析
    UNKNOWN = "unknown"


@dataclass
class QueryUnderstandingResult:
    """查询理解结果"""
    original_query: str
    intent: QueryIntent
    expanded_queries: List[str] = field(default_factory=list)
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    normalized_query: str = ""
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class GameTermMapper:
    """游戏术语映射器 - 处理游戏领域特定词汇"""
    
    def __init__(self):
        # 伤害类型映射
        self.damage_type_mapping = {
            "物理": ["physical", "物理伤害", "物攻", "普攻"],
            "魔法": ["magical", "魔法伤害", "法伤", "魔攻", "法术"],
            "真实": ["true", "真实伤害", "穿透伤害", "无视防御"],
            "火焰": ["fire", "火伤", "燃烧", "灼烧", "火系"],
            "冰霜": ["ice", "frost", "冰伤", "冻结", "冰系", "寒冰"],
            "雷电": ["lightning", "thunder", "雷伤", "电击", "雷系"],
            "毒素": ["poison", "毒伤", "中毒", "剧毒"],
            "暗影": ["shadow", "dark", "暗伤", "黑暗", "暗系"],
            "神圣": ["holy", "light", "圣伤", "光明", "圣系"],
        }
        
        # 控制效果映射
        self.control_effect_mapping = {
            "眩晕": ["stun", "晕眩", "击晕", "昏迷"],
            "沉默": ["silence", "禁言", "封印技能"],
            "定身": ["root", "禁锢", "束缚", "固定"],
            "减速": ["slow", "迟缓", "降速"],
            "击退": ["knockback", "击飞", "推开", "弹开"],
            "击飞": ["knockup", "浮空", "挑飞"],
            "嘲讽": ["taunt", "挑衅", "吸引仇恨"],
            "恐惧": ["fear", "惊吓", "逃跑"],
            "冻结": ["freeze", "冰冻", "冰封"],
            "石化": ["petrify", "石化", "变石"],
            "变形": ["polymorph", "变羊", "变猪"],
            "缴械": ["disarm", "卸武", "无法攻击"],
        }
        
        # Action类型映射
        self.action_type_mapping = {
            "伤害": ["DamageAction", "damage", "攻击", "打击", "造成伤害"],
            "治疗": ["HealAction", "heal", "回血", "恢复生命", "加血"],
            "护盾": ["ShieldAction", "shield", "护甲", "屏障", "保护罩"],
            "移动": ["MovementAction", "move", "位移", "冲刺", "闪现", "突进"],
            "动画": ["AnimationAction", "animation", "播放动画", "动作"],
            "特效": ["VFXAction", "effect", "视觉效果", "粒子"],
            "音效": ["AudioAction", "sound", "声音", "播放音效"],
            "控制": ["ControlAction", "control", "CC", "硬控", "软控"],
            "召唤": ["SummonAction", "summon", "召唤物", "宠物", "分身"],
            "投射物": ["ProjectileAction", "projectile", "弹道", "飞行物", "子弹"],
            "范围": ["AreaOfEffectAction", "aoe", "AOE", "群体", "范围伤害"],
            "Buff": ["BuffAction", "buff", "增益", "加成", "强化"],
            "Debuff": ["DebuffAction", "debuff", "减益", "削弱", "负面效果"],
            "传送": ["TeleportAction", "teleport", "瞬移", "闪烁"],
        }
        
        # 技能类型映射
        self.skill_type_mapping = {
            "主动技能": ["active", "主动", "释放技能"],
            "被动技能": ["passive", "被动", "天赋"],
            "普通攻击": ["basic_attack", "普攻", "平A", "基础攻击"],
            "终极技能": ["ultimate", "大招", "终极", "必杀技"],
            "召唤技能": ["summon", "召唤", "召唤师技能"],
        }
        
        # 构建反向映射（用于快速查找）
        self._build_reverse_mappings()
    
    def _build_reverse_mappings(self):
        """构建反向映射表"""
        self.term_to_category: Dict[str, Tuple[str, str]] = {}
        
        mappings = [
            ("damage_type", self.damage_type_mapping),
            ("control_effect", self.control_effect_mapping),
            ("action_type", self.action_type_mapping),
            ("skill_type", self.skill_type_mapping),
        ]
        
        for category, mapping in mappings:
            for canonical, variants in mapping.items():
                self.term_to_category[canonical.lower()] = (category, canonical)
                for variant in variants:
                    self.term_to_category[variant.lower()] = (category, canonical)
    
    def normalize_term(self, term: str) -> Optional[Tuple[str, str]]:
        """
        标准化术语
        
        Args:
            term: 输入术语
        
        Returns:
            (category, canonical_term) 或 None
        """
        return self.term_to_category.get(term.lower())
    
    def get_synonyms(self, term: str) -> List[str]:
        """获取术语的同义词列表"""
        result = self.normalize_term(term)
        if not result:
            return []
        
        category, canonical = result
        
        # 根据类别获取映射表
        mapping = {
            "damage_type": self.damage_type_mapping,
            "control_effect": self.control_effect_mapping,
            "action_type": self.action_type_mapping,
            "skill_type": self.skill_type_mapping,
        }.get(category, {})
        
        return mapping.get(canonical, [])
    
    def extract_game_entities(self, text: str) -> Dict[str, List[str]]:
        """
        从文本中提取游戏实体
        
        Returns:
            {
                "damage_types": ["火焰", "物理"],
                "control_effects": ["眩晕"],
                "action_types": ["DamageAction"],
                ...
            }
        """
        entities: Dict[str, List[str]] = {
            "damage_types": [],
            "control_effects": [],
            "action_types": [],
            "skill_types": [],
        }
        
        text_lower = text.lower()
        
        for term, (category, canonical) in self.term_to_category.items():
            if term in text_lower:
                key = category + "s"  # damage_type -> damage_types
                if key in entities and canonical not in entities[key]:
                    entities[key].append(canonical)
        
        return entities


class QueryExpander:
    """查询扩展器"""
    
    def __init__(self, term_mapper: Optional[GameTermMapper] = None):
        self.term_mapper = term_mapper or GameTermMapper()
        
        # 通用同义词扩展
        self.general_synonyms = {
            "技能": ["skill", "能力", "招式"],
            "伤害": ["damage", "攻击", "打击"],
            "范围": ["area", "AOE", "群体"],
            "单体": ["single", "单目标"],
            "持续": ["duration", "持续时间", "DOT"],
            "瞬发": ["instant", "立即", "无延迟"],
            "引导": ["channel", "蓄力", "读条"],
            "冷却": ["cooldown", "CD", "冷却时间"],
        }
    
    def expand_query(
        self,
        query: str,
        max_expansions: int = 5
    ) -> List[str]:
        """
        扩展查询
        
        Args:
            query: 原始查询
            max_expansions: 最大扩展数量
        
        Returns:
            扩展后的查询列表（包含原始查询）
        """
        expansions = [query]
        
        # 1. 基于游戏术语的扩展
        entities = self.term_mapper.extract_game_entities(query)
        for category, terms in entities.items():
            for term in terms:
                synonyms = self.term_mapper.get_synonyms(term)
                for syn in synonyms[:2]:  # 每个术语最多2个同义词
                    if syn.lower() not in query.lower():
                        expanded = query + f" {syn}"
                        if expanded not in expansions:
                            expansions.append(expanded)
        
        # 2. 基于通用同义词的扩展
        for term, synonyms in self.general_synonyms.items():
            if term in query:
                for syn in synonyms[:1]:
                    expanded = query.replace(term, syn)
                    if expanded not in expansions:
                        expansions.append(expanded)
        
        # 3. 添加Action类型后缀（如果查询中没有）
        if "action" not in query.lower():
            for action_term in ["伤害", "治疗", "移动", "控制"]:
                if action_term in query:
                    mapping = self.term_mapper.action_type_mapping.get(action_term, [])
                    if mapping:
                        expanded = query + f" {mapping[0]}"
                        if expanded not in expansions:
                            expansions.append(expanded)
        
        return expansions[:max_expansions]


class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        # 意图关键词模式
        self.intent_patterns = {
            QueryIntent.SKILL_SEARCH: [
                r"搜索.*技能", r"查找.*技能", r"找.*技能",
                r"有.*技能", r"哪些技能", r"什么技能",
                r"技能.*搜索", r"skill.*search",
            ],
            QueryIntent.ACTION_RECOMMEND: [
                r"推荐.*action", r"推荐.*动作", r"用什么action",
                r"应该用.*action", r"action.*推荐",
                r"怎么实现", r"如何实现", r"怎么做",
            ],
            QueryIntent.PARAMETER_QUERY: [
                r"参数.*查询", r"查询.*参数", r"参数.*是多少",
                r"baseDamage", r"duration", r"frame",
                r"where.*>", r"where.*<", r"where.*=",
                r"大于", r"小于", r"等于", r"范围",
            ],
            QueryIntent.SIMILAR_SKILL: [
                r"类似.*技能", r"相似.*技能", r"像.*一样",
                r"similar", r"相近", r"差不多",
            ],
            QueryIntent.SKILL_ANALYSIS: [
                r"分析.*技能", r"技能.*分析", r"解析",
                r"结构", r"组成", r"包含哪些",
            ],
        }
    
    def classify(self, query: str) -> Tuple[QueryIntent, float]:
        """
        分类查询意图
        
        Returns:
            (intent, confidence)
        """
        query_lower = query.lower()
        
        intent_scores: Dict[QueryIntent, int] = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            # 默认意图判断
            if any(kw in query_lower for kw in ["action", "动作", "推荐"]):
                return QueryIntent.ACTION_RECOMMEND, 0.5
            elif any(kw in query_lower for kw in ["技能", "skill"]):
                return QueryIntent.SKILL_SEARCH, 0.5
            return QueryIntent.UNKNOWN, 0.3
        
        # 返回得分最高的意图
        best_intent = max(intent_scores, key=intent_scores.get)
        max_score = intent_scores[best_intent]
        confidence = min(0.9, 0.5 + max_score * 0.15)
        
        return best_intent, confidence


class QueryUnderstandingEngine:
    """查询理解引擎 - 整合所有查询理解功能"""
    
    def __init__(self):
        self.term_mapper = GameTermMapper()
        self.query_expander = QueryExpander(self.term_mapper)
        self.intent_classifier = IntentClassifier()
    
    def understand(self, query: str) -> QueryUnderstandingResult:
        """
        理解查询
        
        Args:
            query: 用户查询
        
        Returns:
            QueryUnderstandingResult
        """
        # 1. 意图分类
        intent, confidence = self.intent_classifier.classify(query)
        
        # 2. 实体提取
        entities = self.term_mapper.extract_game_entities(query)
        
        # 3. 查询扩展
        expanded_queries = self.query_expander.expand_query(query)
        
        # 4. 查询标准化
        normalized = self._normalize_query(query, entities)
        
        return QueryUnderstandingResult(
            original_query=query,
            intent=intent,
            expanded_queries=expanded_queries,
            extracted_entities=entities,
            normalized_query=normalized,
            confidence=confidence,
            metadata={
                "has_action_type": bool(entities.get("action_types")),
                "has_damage_type": bool(entities.get("damage_types")),
                "has_control_effect": bool(entities.get("control_effects")),
            }
        )
    
    def _normalize_query(
        self,
        query: str,
        entities: Dict[str, List[str]]
    ) -> str:
        """标准化查询"""
        normalized = query
        
        # 将识别到的术语替换为标准形式
        for action_type in entities.get("action_types", []):
            # 获取Action类型的标准名称
            mapping = self.term_mapper.action_type_mapping.get(action_type, [])
            if mapping and mapping[0].endswith("Action"):
                # 在查询中添加标准Action名称
                if mapping[0] not in normalized:
                    normalized = f"{normalized} {mapping[0]}"
        
        return normalized.strip()
    
    def get_search_queries(
        self,
        query: str,
        include_expansions: bool = True
    ) -> List[str]:
        """
        获取用于搜索的查询列表
        
        Args:
            query: 原始查询
            include_expansions: 是否包含扩展查询
        
        Returns:
            查询列表（按优先级排序）
        """
        result = self.understand(query)
        
        queries = [result.normalized_query or query]
        
        if include_expansions:
            for exp in result.expanded_queries:
                if exp not in queries:
                    queries.append(exp)
        
        return queries
