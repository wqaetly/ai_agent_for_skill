"""
智能路由模块
根据用户输入自动选择最合适的 Graph

路由策略：
1. skill-search: 搜索、查找相关技能
2. skill-detail: 查看技能详情
3. skill-generation: 简单技能生成（单track或简单效果）
4. progressive-skill-generation: 复杂技能生成（多track、多阶段）
5. action-batch-skill-generation: 超复杂技能（大量action、精细控制）
"""

import re
import logging
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

# Graph ID 常量
GRAPH_SKILL_SEARCH = "skill-search"
GRAPH_SKILL_DETAIL = "skill-detail"
GRAPH_SKILL_GENERATION = "skill-generation"
GRAPH_PROGRESSIVE = "progressive-skill-generation"
GRAPH_ACTION_BATCH = "action-batch-skill-generation"

# 路由规则配置
ROUTING_RULES = {
    GRAPH_SKILL_SEARCH: {
        "keywords": [
            "搜索", "查找", "找一下", "有没有", "有什么", "哪些",
            "search", "find", "look for", "any", "which"
        ],
        "patterns": [
            r"搜.*技能",
            r"找.*技能",
            r"有.*技能吗",
            r"查.*技能",
        ],
        "priority": 10,
        "description": "技能搜索"
    },
    GRAPH_SKILL_DETAIL: {
        "keywords": [
            "详情", "详细", "具体", "查看", "看看", "展示",
            "detail", "show", "display", "view"
        ],
        "patterns": [
            r"(查看|看看|展示).*详情",
            r".*的详细信息",
            r".*技能是什么样",
        ],
        "priority": 9,
        "description": "技能详情查询"
    },
    GRAPH_ACTION_BATCH: {
        "keywords": [
            "超复杂", "非常复杂", "大量action", "精细控制", "批量生成",
            "very complex", "batch", "fine-grained"
        ],
        "patterns": [
            r"(超|非常|特别)(复杂|精细)",
            r"大量.*action",
            r"\d{2,}.*action",  # 10+ actions
        ],
        "priority": 8,
        "description": "Action批量式生成（超复杂技能）"
    },
    GRAPH_PROGRESSIVE: {
        "keywords": [
            "复杂", "多阶段", "多track", "渐进", "分步",
            "complex", "multi-stage", "progressive", "multiple tracks"
        ],
        "patterns": [
            r"(复杂|多阶段|多track)",
            r"\d+.*track",
            r"(蓄力|释放|持续|结束).*阶段",
            r"(前摇|后摇|持续时间)",
        ],
        "complexity_indicators": [
            "蓄力", "释放", "持续", "结束", "前摇", "后摇",
            "多段", "连击", "combo", "阶段", "phase",
            "buff", "debuff", "dot", "hot", "aoe", "范围",
            "弹道", "投射物", "projectile", "召唤", "summon"
        ],
        "priority": 7,
        "description": "渐进式生成（复杂技能）"
    },
    GRAPH_SKILL_GENERATION: {
        "keywords": [],  # 默认选项，不需要关键词
        "patterns": [],
        "priority": 1,
        "description": "标准技能生成（简单技能）"
    }
}


def analyze_complexity(text: str) -> Dict[str, Any]:
    """
    分析用户输入的复杂度
    
    Returns:
        {
            "score": int,  # 复杂度分数 0-100
            "indicators": List[str],  # 检测到的复杂度指标
            "estimated_tracks": int,  # 预估track数量
            "estimated_actions": int  # 预估action数量
        }
    """
    text_lower = text.lower()
    indicators = []
    score = 0
    
    # 检测复杂度指标
    complexity_keywords = ROUTING_RULES[GRAPH_PROGRESSIVE].get("complexity_indicators", [])
    for keyword in complexity_keywords:
        if keyword.lower() in text_lower:
            indicators.append(keyword)
            score += 10
    
    # 检测数字（可能表示多个track或action）
    numbers = re.findall(r'\d+', text)
    for num in numbers:
        n = int(num)
        if n >= 3:
            score += n * 2
    
    # 检测"和"、"以及"等连接词（表示多个效果）
    connectors = ["和", "以及", "同时", "并且", "然后", "接着", "之后"]
    for conn in connectors:
        count = text.count(conn)
        score += count * 5
    
    # 预估track数量
    track_keywords = ["track", "轨道", "阶段", "phase"]
    estimated_tracks = 1
    for kw in track_keywords:
        if kw in text_lower:
            # 尝试提取数字
            match = re.search(rf'(\d+)\s*{kw}', text_lower)
            if match:
                estimated_tracks = max(estimated_tracks, int(match.group(1)))
    
    # 根据复杂度指标估算track
    if len(indicators) >= 4:
        estimated_tracks = max(estimated_tracks, 3)
    elif len(indicators) >= 2:
        estimated_tracks = max(estimated_tracks, 2)
    
    # 预估action数量
    estimated_actions = len(indicators) * 2 + estimated_tracks * 3
    
    return {
        "score": min(score, 100),
        "indicators": indicators,
        "estimated_tracks": estimated_tracks,
        "estimated_actions": estimated_actions
    }


def route_by_keywords(text: str) -> Tuple[str, float]:
    """
    基于关键词匹配路由
    
    Returns:
        (graph_id, confidence)
    """
    text_lower = text.lower()
    best_match = (GRAPH_SKILL_GENERATION, 0.0)
    
    for graph_id, rules in ROUTING_RULES.items():
        if graph_id == GRAPH_SKILL_GENERATION:
            continue  # 跳过默认选项
            
        keywords = rules.get("keywords", [])
        patterns = rules.get("patterns", [])
        priority = rules.get("priority", 0)
        
        # 关键词匹配
        keyword_matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        
        # 正则匹配
        pattern_matches = sum(1 for p in patterns if re.search(p, text_lower))
        
        # 计算置信度
        total_matches = keyword_matches + pattern_matches * 2
        if total_matches > 0:
            confidence = min(total_matches * 0.2 + priority * 0.05, 1.0)
            if confidence > best_match[1]:
                best_match = (graph_id, confidence)
    
    return best_match


def smart_route(
    user_input: str,
    prefer_progressive: bool = True,
    complexity_threshold: int = 30
) -> Dict[str, Any]:
    """
    智能路由主函数
    
    Args:
        user_input: 用户输入文本
        prefer_progressive: 是否偏好渐进式生成（推荐开启）
        complexity_threshold: 复杂度阈值，超过则使用渐进式
        
    Returns:
        {
            "graph_id": str,  # 推荐的 graph ID
            "confidence": float,  # 置信度 0-1
            "reason": str,  # 路由原因
            "complexity": Dict,  # 复杂度分析结果
            "alternatives": List[Dict]  # 备选方案
        }
    """
    # 1. 关键词路由
    keyword_graph, keyword_confidence = route_by_keywords(user_input)
    
    # 2. 复杂度分析
    complexity = analyze_complexity(user_input)
    
    # 3. 决策逻辑
    result = {
        "graph_id": GRAPH_SKILL_GENERATION,
        "confidence": 0.5,
        "reason": "默认使用标准技能生成",
        "complexity": complexity,
        "alternatives": []
    }
    
    # 如果关键词匹配到搜索或详情，优先使用
    if keyword_graph in [GRAPH_SKILL_SEARCH, GRAPH_SKILL_DETAIL]:
        result["graph_id"] = keyword_graph
        result["confidence"] = keyword_confidence
        result["reason"] = f"检测到{ROUTING_RULES[keyword_graph]['description']}意图"
        return result
    
    # 如果关键词匹配到批量生成
    if keyword_graph == GRAPH_ACTION_BATCH:
        result["graph_id"] = GRAPH_ACTION_BATCH
        result["confidence"] = keyword_confidence
        result["reason"] = "检测到超复杂技能需求，使用Action批量式生成"
        result["alternatives"].append({
            "graph_id": GRAPH_PROGRESSIVE,
            "reason": "也可使用渐进式生成"
        })
        return result
    
    # 根据复杂度决定
    if complexity["score"] >= 60:
        # 超高复杂度 → Action批量式
        result["graph_id"] = GRAPH_ACTION_BATCH
        result["confidence"] = 0.8
        result["reason"] = f"复杂度评分 {complexity['score']}，检测到 {len(complexity['indicators'])} 个复杂度指标"
        result["alternatives"].append({
            "graph_id": GRAPH_PROGRESSIVE,
            "reason": "渐进式生成也可处理"
        })
    elif complexity["score"] >= complexity_threshold or (prefer_progressive and complexity["score"] >= 20):
        # 中等复杂度 → 渐进式
        result["graph_id"] = GRAPH_PROGRESSIVE
        result["confidence"] = 0.7
        result["reason"] = f"复杂度评分 {complexity['score']}，推荐使用渐进式生成"
        result["alternatives"].append({
            "graph_id": GRAPH_SKILL_GENERATION,
            "reason": "简单技能也可使用标准生成"
        })
    else:
        # 低复杂度 → 标准生成
        result["graph_id"] = GRAPH_SKILL_GENERATION
        result["confidence"] = 0.6
        result["reason"] = "简单技能需求，使用标准生成"
        if prefer_progressive:
            result["alternatives"].append({
                "graph_id": GRAPH_PROGRESSIVE,
                "reason": "渐进式生成质量更高但速度较慢"
            })
    
    logger.info(f"Smart route: '{user_input[:50]}...' -> {result['graph_id']} (confidence: {result['confidence']:.2f})")
    return result


def get_available_graphs() -> List[Dict[str, Any]]:
    """
    获取所有可用的 Graph 列表
    
    Returns:
        Graph 信息列表
    """
    return [
        {
            "id": GRAPH_SKILL_GENERATION,
            "name": "标准技能生成",
            "description": "一次性生成完整技能，适合简单技能",
            "recommended_for": "简单技能、快速原型",
            "icon": "zap"
        },
        {
            "id": GRAPH_PROGRESSIVE,
            "name": "渐进式技能生成",
            "description": "三阶段渐进生成：骨架→Track→组装，质量更高",
            "recommended_for": "复杂技能、多阶段技能",
            "recommended": True,
            "icon": "layers"
        },
        {
            "id": GRAPH_ACTION_BATCH,
            "name": "Action批量式生成",
            "description": "最细粒度的渐进式生成，适合超复杂技能",
            "recommended_for": "超复杂技能、大量Action",
            "icon": "boxes"
        },
        {
            "id": GRAPH_SKILL_SEARCH,
            "name": "技能搜索",
            "description": "语义搜索技能库中的相似技能",
            "recommended_for": "查找参考、搜索示例",
            "icon": "search"
        },
        {
            "id": GRAPH_SKILL_DETAIL,
            "name": "技能详情",
            "description": "查看技能的详细配置信息",
            "recommended_for": "查看具体技能配置",
            "icon": "file-text"
        },
        {
            "id": "smart",
            "name": "智能路由",
            "description": "根据输入自动选择最合适的生成方式",
            "recommended_for": "不确定使用哪种方式时",
            "default": True,
            "icon": "sparkles"
        }
    ]
