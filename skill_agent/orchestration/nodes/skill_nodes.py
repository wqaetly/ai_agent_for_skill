"""
LangGraph 节点实现
定义 Graph 中的各个节点（generator、validator、fixer 等）
"""

import json
import logging
from typing import Any, Dict, List, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os

logger = logging.getLogger(__name__)


# ==================== State 定义 ====================

class SkillGenerationState(TypedDict):
    """技能生成流程的状�?""
    requirement: str  # 用户需求描�?    similar_skills: List[Dict[str, Any]]  # 检索到的相似技�?    generated_json: str  # 生成�?JSON
    validation_errors: List[str]  # 验证错误列表
    retry_count: int  # 重试次数
    max_retries: int  # 最大重试次�?    final_result: Dict[str, Any]  # 最终结�?    messages: Annotated[List, "append"]  # 对话历史


# ==================== LLM 初始�?====================

def get_llm(model: str = "deepseek-chat", temperature: float = 0.7):
    """
    获取 LLM 实例（使�?LangChain ChatOpenAI 兼容 DeepSeek�?
    Args:
        model: 模型名称
        temperature: 温度参数

    Returns:
        ChatOpenAI 实例
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设�?)

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
    )


# ==================== 节点函数 ====================

def retriever_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    检索相似技能节�?
    根据需求描述，�?RAG Core 检索相似技能作为参考�?    """
    from ..tools.rag_tools import search_skills_semantic

    requirement = state["requirement"]
    logger.info(f"检索相似技�? {requirement}")

    # 调用 RAG 工具检�?    results = search_skills_semantic.invoke({"query": requirement, "top_k": 3})

    return {
        "similar_skills": results,
        "messages": [HumanMessage(content=f"检索到 {len(results)} 个相似技�?)]
    }


def generator_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    生成技�?JSON 节点

    根据需求和参考技能，使用 LLM 生成技能配�?JSON�?    """
    from ..prompts.prompt_manager import get_prompt_manager

    requirement = state["requirement"]
    similar_skills = state.get("similar_skills", [])

    logger.info(f"生成技�?JSON: {requirement}")

    # 格式化相似技�?    similar_skills_text = "\n\n".join([
        f"技�?{i+1}: {skill.get('skill_name', 'Unknown')}\n{json.dumps(skill.get('skill_data', {}), indent=2, ensure_ascii=False)}"
        for i, skill in enumerate(similar_skills[:2])  # 只取�?�?    ])

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skill_generation")

    # 调用 LLM
    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke({
        "requirement": requirement,
        "similar_skills": similar_skills_text or "无参考技�?
    })

    generated_json = response.content

    return {
        "generated_json": generated_json,
        "messages": [AIMessage(content=f"已生成技�?JSON (长度: {len(generated_json)} 字符)")]
    }


def validator_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    验证 JSON 节点

    验证生成�?JSON 是否符合 Schema 和业务规则�?    """
    generated_json = state["generated_json"]
    logger.info("验证生成�?JSON")

    errors = []

    try:
        # 解析 JSON
        skill_data = json.loads(generated_json)

        # 基础验证
        required_fields = ["skillName", "skillId", "actions"]
        for field in required_fields:
            if field not in skill_data:
                errors.append(f"缺少必填字段: {field}")

        # Actions 验证
        if "actions" in skill_data:
            actions = skill_data["actions"]
            if not isinstance(actions, list):
                errors.append("actions 字段必须是数�?)
            elif len(actions) == 0:
                errors.append("actions 数组不能为空")
            else:
                # 验证每个 Action
                for i, action in enumerate(actions):
                    if not isinstance(action, dict):
                        errors.append(f"Action[{i}] 必须是对�?)
                    elif "actionType" not in action:
                        errors.append(f"Action[{i}] 缺少 actionType 字段")

        # 数值范围验�?        if "cooldown" in skill_data:
            cooldown = skill_data["cooldown"]
            if not isinstance(cooldown, (int, float)) or cooldown < 0:
                errors.append(f"cooldown 必须是非负数，当前�? {cooldown}")

    except json.JSONDecodeError as e:
        errors.append(f"JSON 解析失败: {str(e)}")
    except Exception as e:
        errors.append(f"验证异常: {str(e)}")

    if errors:
        logger.warning(f"验证失败，发�?{len(errors)} 个错�?)
    else:
        logger.info("验证通过")

    return {
        "validation_errors": errors,
        "messages": [
            HumanMessage(content=f"验证结果: {'失败' if errors else '通过'} ({len(errors)} 个错�?")
        ]
    }


def fixer_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    修复 JSON 节点

    根据验证错误，使�?LLM 修复 JSON�?    """
    from ..prompts.prompt_manager import get_prompt_manager

    generated_json = state["generated_json"]
    errors = state["validation_errors"]

    logger.info(f"修复 JSON，错误数: {len(errors)}")

    # 格式化错误信�?    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("validation_fix")

    # 调用 LLM
    llm = get_llm(temperature=0.3)  # 修复时使用更低温�?    chain = prompt | llm

    response = chain.invoke({
        "errors": errors_text,
        "json": generated_json
    })

    fixed_json = response.content

    return {
        "generated_json": fixed_json,
        "retry_count": state["retry_count"] + 1,
        "messages": [AIMessage(content=f"已修�?JSON (重试 {state['retry_count'] + 1}/{state['max_retries']})")]
    }


def finalize_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    最终化节点

    将生成的 JSON 解析为最终结果�?    """
    generated_json = state["generated_json"]

    try:
        final_result = json.loads(generated_json)
        logger.info("技能生成成�?)
    except json.JSONDecodeError:
        final_result = {
            "error": "JSON 解析失败",
            "raw_json": generated_json
        }
        logger.error("最�?JSON 解析失败")

    return {
        "final_result": final_result,
        "messages": [HumanMessage(content="技能生成完�?)]
    }


# ==================== 条件判断函数 ====================

def should_continue(state: SkillGenerationState) -> str:
    """
    判断是否继续修复循环

    Returns:
        "fix" - 继续修复
        "finalize" - 结束，返回结�?    """
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # 如果没有错误，结�?    if not errors:
        return "finalize"

    # 如果达到最大重试次数，结束
    if retry_count >= max_retries:
        logger.warning(f"达到最大重试次�?{max_retries}，停止修�?)
        return "finalize"

    # 继续修复
    return "fix"


# ==================== Action 搜索节点 ====================

def action_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Action 搜索节点

    根据自然语言描述搜索相关�?Action 脚本�?
    Args:
        state: 包含 requirement (搜索查询) �?messages 的状态字�?
    Returns:
        更新后的状态，包含搜索结果和消�?    """
    from ..tools.rag_tools import search_actions

    requirement = state.get("requirement", "")
    top_k = state.get("top_k", 5)

    logger.info(f"搜索 Action: {requirement}")

    # 调用 RAG 工具搜索 Action
    results = search_actions.invoke({"query": requirement, "top_k": top_k})

    # 检查是否有错误
    if isinstance(results, dict) and "error" in results:
        logger.error(f"Action 搜索失败: {results['error']}")
        return {
            "search_results": [],
            "error": results["error"],
            "messages": [AIMessage(content=f"�?搜索失败: {results['error']}")]
        }

    # 格式化搜索结果为可读文本
    if results:
        result_summary = f"找到 {len(results)} 个相�?Action:\n\n"
        for i, action in enumerate(results[:5], 1):  # 只显示前5�?            action_name = action.get('action_name', 'Unknown')
            action_type = action.get('action_type', 'N/A')
            similarity = action.get('similarity_score', 0)
            parameters = action.get('parameters', [])

            result_summary += f"{i}. **{action_name}** (类型: {action_type}, 相似�? {similarity:.2f})\n"

            # 显示参数信息
            if parameters:
                result_summary += f"   参数 ({len(parameters)} �?:\n"
                for param in parameters[:3]:  # 只显示前3个参�?                    param_name = param.get('name', 'unknown')
                    param_type = param.get('type', 'unknown')
                    default_value = param.get('defaultValue', 'N/A')
                    result_summary += f"   - `{param_name}` ({param_type}, 默认: {default_value})\n"

                if len(parameters) > 3:
                    result_summary += f"   - ... 还有 {len(parameters) - 3} 个参数\n"
            result_summary += "\n"

        message_content = result_summary
    else:
        message_content = "未找到匹配的 Action，请尝试其他描述�?

    logger.info(f"Action 搜索完成，找�?{len(results)} 个结�?)

    return {
        "search_results": results,
        "messages": [AIMessage(content=message_content)]
    }
