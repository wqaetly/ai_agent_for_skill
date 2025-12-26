"""
通用验证-修复子图（Validation-Fix Subgraph）

抽取骨架修复和Track修复的共同逻辑，
提供可复用的验证-修复循环子图。

使用场景：
1. 骨架验证修复
2. Track验证修复
3. 最终技能验证修复
"""

from langgraph.graph import StateGraph, END
from typing import Any, Dict, List, TypedDict, Callable, Optional, Type
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class FixableState(TypedDict):
    """可修复状态的基础接口"""
    data: Dict[str, Any]  # 待验证/修复的数据
    validation_errors: List[str]  # 验证错误列表
    retry_count: int  # 当前重试次数
    max_retries: int  # 最大重试次数
    context: Dict[str, Any]  # 额外上下文（如 requirement, total_duration）


def create_fix_subgraph(
    name: str,
    validator_fn: Callable[[Dict[str, Any], Dict[str, Any]], List[str]],
    fixer_fn: Callable[[Dict[str, Any], List[str], Dict[str, Any]], Dict[str, Any]],
    schema_class: Optional[Type[BaseModel]] = None,
):
    """
    创建通用的验证-修复子图
    
    Args:
        name: 子图名称（用于日志）
        validator_fn: 验证函数，签名 (data, context) -> List[str]
        fixer_fn: 修复函数，签名 (data, errors, context) -> Dict[str, Any]
        schema_class: 可选的 Pydantic Schema 用于结构验证
    
    Returns:
        编译后的子图
    """
    
    def validate_node(state: FixableState) -> Dict[str, Any]:
        """验证节点"""
        data = state.get("data", {})
        context = state.get("context", {})
        
        errors = []
        
        # Pydantic Schema 验证
        if schema_class:
            try:
                schema_class.model_validate(data)
            except Exception as e:
                errors.append(f"Schema validation failed: {str(e)}")
        
        # 自定义验证
        custom_errors = validator_fn(data, context)
        errors.extend(custom_errors)
        
        logger.info(f"[{name}] Validation: {len(errors)} errors")
        
        return {"validation_errors": errors}
    
    def fix_node(state: FixableState) -> Dict[str, Any]:
        """修复节点"""
        data = state.get("data", {})
        errors = state.get("validation_errors", [])
        context = state.get("context", {})
        retry_count = state.get("retry_count", 0)
        
        logger.info(f"[{name}] Fixing {len(errors)} errors (retry {retry_count + 1})")
        
        try:
            fixed_data = fixer_fn(data, errors, context)
            return {
                "data": fixed_data,
                "retry_count": retry_count + 1
            }
        except Exception as e:
            logger.error(f"[{name}] Fix failed: {e}")
            return {
                "retry_count": retry_count + 1,
                "validation_errors": errors + [f"Fix failed: {str(e)}"]
            }
    
    def should_continue(state: FixableState) -> str:
        """判断是否继续修复"""
        errors = state.get("validation_errors", [])
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        
        if not errors:
            return "done"
        if retry_count >= max_retries:
            logger.warning(f"[{name}] Max retries ({max_retries}) reached")
            return "done"
        return "fix"
    
    # 构建子图
    workflow = StateGraph(FixableState)
    workflow.add_node("validate", validate_node)
    workflow.add_node("fix", fix_node)
    
    workflow.set_entry_point("validate")
    
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {"fix": "fix", "done": END}
    )
    
    workflow.add_edge("fix", "validate")
    
    return workflow.compile()


# ==================== 预定义的验证/修复函数 ====================

def skeleton_validator(data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """骨架验证函数"""
    from ..nodes.progressive_skill_nodes import validate_skeleton
    return validate_skeleton(data)


def track_validator(data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
    """Track验证函数"""
    from ..nodes.progressive_skill_nodes import validate_track
    total_duration = context.get("total_duration", 150)
    return validate_track(data, total_duration)


def create_llm_fixer(prompt_name: str):
    """
    创建基于LLM的修复函数工厂
    
    Args:
        prompt_name: Prompt模板名称
    
    Returns:
        修复函数
    """
    def fixer(data: Dict[str, Any], errors: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        import json
        from ..prompts.prompt_manager import get_prompt_manager
        from ..nodes.skill_nodes import get_llm
        from ..nodes.json_utils import extract_json_from_markdown
        
        prompt_mgr = get_prompt_manager()
        prompt = prompt_mgr.get_prompt(prompt_name)
        llm = get_llm(temperature=0.3)
        
        errors_text = "\n".join([f"{i+1}. {e}" for i, e in enumerate(errors)])
        
        chain = prompt | llm
        response = chain.invoke({
            "errors": errors_text,
            "json": json.dumps(data, ensure_ascii=False, indent=2),
            **context
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        json_content = extract_json_from_markdown(content)
        return json.loads(json_content)
    
    return fixer


# ==================== 预构建的子图 ====================

def get_skeleton_fix_subgraph():
    """获取骨架修复子图"""
    from ..schemas import SkillSkeletonSchema
    return create_fix_subgraph(
        name="SkeletonFix",
        validator_fn=skeleton_validator,
        fixer_fn=create_llm_fixer("skeleton_validation_fix"),
        schema_class=SkillSkeletonSchema
    )


def get_track_fix_subgraph():
    """获取Track修复子图"""
    from ..schemas import SkillTrack
    return create_fix_subgraph(
        name="TrackFix",
        validator_fn=track_validator,
        fixer_fn=create_llm_fixer("track_validation_fix"),
        schema_class=SkillTrack
    )


__all__ = [
    "FixableState",
    "create_fix_subgraph",
    "skeleton_validator",
    "track_validator",
    "create_llm_fixer",
    "get_skeleton_fix_subgraph",
    "get_track_fix_subgraph",
]
