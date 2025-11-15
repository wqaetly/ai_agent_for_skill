"""
LangGraph 节点实现
定义 Graph 中的各个节点（generator、validator、fixer 等）
"""

import json
import logging
import time
from typing import Any, Dict, List, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os

from .json_utils import extract_json_from_markdown

logger = logging.getLogger(__name__)


# ==================== State 定义 ====================

class SkillGenerationState(TypedDict):
    """技能生成流程的状态"""
    requirement: str  # 用户需求描述
    similar_skills: List[Dict[str, Any]]  # 检索到的相似技能
    action_schemas: List[Dict[str, Any]]  # 🔥 检索到的Action定义schema
    generated_json: str  # 生成的 JSON
    validation_errors: List[str]  # 验证错误列表
    retry_count: int  # 重试次数
    max_retries: int  # 最大重试次数
    final_result: Dict[str, Any]  # 最终结果
    messages: Annotated[List, "append"]  # 对话历史
    thread_id: str  # 🔥 线程ID (用于流式输出)


# ==================== LLM 初始化 ====================

def get_llm(model: str = "deepseek-reasoner", temperature: float = 1.0):
    """
    获取 LLM 实例（使用 LangChain ChatOpenAI 兼容 DeepSeek）

    Args:
        model: 模型名称（默认使用 deepseek-reasoner 思考模型）
        temperature: 温度参数（deepseek-reasoner 推荐使用 1.0）

    Returns:
        ChatOpenAI 实例
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DEEPSEEK_API_KEY 未设置")

    # 从环境变量读取超时配置（默认 120 秒，因为 reasoner 模型推理时间长）
    timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "120"))
    max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "2"))

    logger.info(f"初始化 LLM: model={model}, timeout={timeout}s, max_retries={max_retries}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        timeout=timeout,  # 请求超时（秒）
        max_retries=max_retries,  # 最大重试次数
    )


# ==================== 节点函数 ====================

def retriever_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    检索相似技能节点

    根据需求描述，从 RAG Core 检索相似技能和相关 Action 定义作为参考。
    """
    from ..tools.rag_tools import search_skills_semantic, search_actions

    requirement = state["requirement"]
    logger.info(f"检索相似技能: {requirement}")

    # 准备消息列表
    messages = []

    # 添加开始检索的消息
    messages.append(AIMessage(content=f"🔍 正在从技能库中检索与「{requirement}」相关的技能和Action定义..."))

    # 🔥 P0改进：添加错误边界
    try:
        # 调用 RAG 工具检索技能（添加性能日志）
        # top_k=2 优化：减少检索数量以提升速度，2个高质量参考已足够
        start_time = time.time()
        results = search_skills_semantic.invoke({"query": requirement, "top_k": 2})
        rag_elapsed = time.time() - start_time
        logger.info(f"⏱️ RAG 技能检索耗时: {rag_elapsed:.2f}s")

        # 🔥 新增：检索相关的 Action 定义
        action_start = time.time()
        action_results = search_actions.invoke({"query": requirement, "top_k": 5})
        action_elapsed = time.time() - action_start
        logger.info(f"⏱️ RAG Action检索耗时: {action_elapsed:.2f}s")
        logger.info(f"📋 检索到 {len(action_results) if isinstance(action_results, list) else 0} 个相关Action")
    except Exception as e:
        # RAG检索失败时返回空结果，允许继续执行
        logger.error(f"❌ RAG检索失败: {e}", exc_info=True)
        results = []
        action_results = []
        messages.append(AIMessage(content=f"⚠️ 检索失败，将直接基于需求生成"))

    # 构建详细的检索结果消息
    if results:
        skills_summary = "\n".join([
            f"• **{skill.get('skill_name', 'Unknown')}** (相似度: {skill.get('similarity', 0):.2%})"
            for skill in results[:3]
        ])
        message = f"📚 **检索到 {len(results)} 个相似技能：**\n\n{skills_summary}\n\n这些技能将作为生成参考。"
    else:
        message = "⚠️ 未检索到相似技能，将基于需求直接生成。"

    # 添加Action检索结果信息
    if isinstance(action_results, list) and action_results:
        action_summary = "\n".join([
            f"• **{action.get('action_name', 'Unknown')}** ({action.get('category', 'N/A')})"
            for action in action_results[:3]
        ])
        message += f"\n\n🎯 **检索到 {len(action_results)} 个相关Action：**\n\n{action_summary}"

    messages.append(AIMessage(content=message))

    return {
        "similar_skills": results,
        "action_schemas": action_results if isinstance(action_results, list) else [],
        "messages": messages
    }


def generator_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    生成技能 JSON 节点

    根据需求和参考技能，使用 LLM 生成技能配置 JSON。

    Args:
        state: 技能生成状态
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from langgraph.config import get_stream_writer

    requirement = state["requirement"]
    similar_skills = state.get("similar_skills", [])
    action_schemas = state.get("action_schemas", [])  # 🔥 新增：获取action schemas

    # 🔥 使用 LangGraph 标准的 stream_writer 机制
    try:
        writer = get_stream_writer()
        logger.info(f"✅ Got stream writer")
    except Exception as e:
        logger.warning(f"⚠️ Failed to get stream writer: {e}")
        writer = None

    logger.info(f"生成技能 JSON: {requirement}")

    # 格式化相似技能
    similar_skills_text = "\n\n".join([
        f"技能 {i+1}: {skill.get('skill_name', 'Unknown')}\n{json.dumps(skill.get('skill_data', {}), indent=2, ensure_ascii=False)}"
        for i, skill in enumerate(similar_skills[:2])  # 只取前2个
    ])

    # 🔥 新增：格式化 Action Schema（包含参数定义和约束）
    action_schemas_text = ""
    if action_schemas:
        formatted_actions = []
        for action in action_schemas[:5]:  # 只取前5个相关action
            action_name = action.get('action_name', 'Unknown')
            action_type = action.get('action_type', 'N/A')
            category = action.get('category', 'N/A')
            description = action.get('description', '')[:200]  # 限制描述长度
            parameters = action.get('parameters', [])

            # 格式化参数信息
            params_info = []
            for param in parameters:
                param_name = param.get('name', 'unknown')
                param_type = param.get('type', 'unknown')
                default_val = param.get('defaultValue', '')
                constraints = param.get('constraints', {})
                is_enum = param.get('isEnum', False)
                enum_values = param.get('enumValues', [])

                # 构建参数约束描述
                constraint_desc = []
                if constraints.get('min'):
                    constraint_desc.append(f"min={constraints['min']}")
                if constraints.get('max'):
                    constraint_desc.append(f"max={constraints['max']}")
                if constraints.get('minValue'):
                    constraint_desc.append(f"minValue={constraints['minValue']}")
                if constraints.get('maxValue'):
                    constraint_desc.append(f"maxValue={constraints['maxValue']}")

                param_info = f"  - {param_name}: {param_type}"
                if default_val:
                    param_info += f" = {default_val}"
                if is_enum and enum_values:
                    param_info += f" (枚举值: {', '.join(enum_values)})"
                elif constraint_desc:
                    param_info += f" ({', '.join(constraint_desc)})"

                params_info.append(param_info)

            params_text = "\n".join(params_info) if params_info else "  无参数"

            formatted_action = f"""Action: {action_name} ({action_type})
分类: {category}
描述: {description}
参数定义:
{params_text}"""
            formatted_actions.append(formatted_action)

        action_schemas_text = "\n\n".join(formatted_actions)
        logger.info(f"📋 已格式化 {len(formatted_actions)} 个Action schema用于prompt")

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skill_generation")

    # 准备消息列表
    messages = []

    # 添加开始生成的消息
    messages.append(AIMessage(content="🤖 正在调用 DeepSeek AI 生成技能配置..."))

    # 调用 LLM (使用流式输出)
    llm = get_llm()
    chain = prompt | llm

    logger.info(f"⏳ 正在调用 DeepSeek API (流式输出)...")
    api_start_time = time.time()
    first_chunk_time = None

    # 收集流式输出（分离思考过程和最终输出）
    full_reasoning = ""  # 思考过程
    full_content = ""    # 最终输出

    # 🔥 生成唯一的 message_id 用于跟踪流式消息
    thinking_message_id = f"thinking_{api_start_time}"
    content_message_id = f"content_{api_start_time}"

    # 🔥 P0改进：添加错误边界
    try:
        # 流式调用
        for chunk in chain.stream({
            "requirement": requirement,
            "similar_skills": similar_skills_text or "无参考技能",
            "action_schemas": action_schemas_text or "无Action参考"  # 🔥 新增：传递action schemas
        }):
            # 记录首字节时间（TTFB）
            if first_chunk_time is None:
                first_chunk_time = time.time()
                ttfb = first_chunk_time - api_start_time
                logger.info(f"⚡ 首字节延迟 (TTFB): {ttfb:.2f}s")

            # 尝试提取 reasoning_content (DeepSeek Reasoner 特有)
            # 检查多个可能的位置
            reasoning_chunk = None

            # 方法1: 检查 response_metadata
            if hasattr(chunk, 'response_metadata') and isinstance(chunk.response_metadata, dict):
                reasoning_chunk = chunk.response_metadata.get('reasoning_content')

            # 方法2: 检查 additional_kwargs
            if not reasoning_chunk and hasattr(chunk, 'additional_kwargs') and isinstance(chunk.additional_kwargs, dict):
                reasoning_chunk = chunk.additional_kwargs.get('reasoning_content')

            # 方法3: 直接检查属性
            if not reasoning_chunk and hasattr(chunk, 'reasoning_content'):
                reasoning_chunk = chunk.reasoning_content

            # 累积思考内容
            if reasoning_chunk:
                full_reasoning += reasoning_chunk
                logger.info(f"📝 Reasoning chunk received: {len(reasoning_chunk)} chars")

                # 🔥 使用 LangGraph 标准 writer 实时推送 thinking chunk
                if writer:
                    try:
                        writer({
                            "type": "thinking_chunk",
                            "message_id": thinking_message_id,
                            "chunk": reasoning_chunk
                        })
                        logger.info(f"✅ Sent thinking chunk via writer")
                    except Exception as e:
                        logger.error(f"❌ Failed to send thinking chunk: {e}")

            # 累积最终内容
            if hasattr(chunk, 'content') and chunk.content:
                full_content += chunk.content
                logger.info(f"📝 Content chunk received: {len(chunk.content)} chars, total: {len(full_content)}")

                # 🔥 使用 LangGraph 标准 writer 实时推送 content chunk
                if writer:
                    try:
                        writer({
                            "type": "content_chunk",
                            "message_id": content_message_id,
                            "chunk": chunk.content
                        })
                        logger.info(f"✅ Sent content chunk via writer")
                    except Exception as e:
                        logger.error(f"❌ Failed to send content chunk: {e}")

        # 记录完整响应和性能指标
        api_total_time = time.time() - api_start_time
        logger.info(f"✅ DeepSeek API 响应完成")
        logger.info(f"⏱️ DeepSeek API 总耗时: {api_total_time:.2f}s")
        logger.info(f"🧠 思考内容长度: {len(full_reasoning)} 字符")
        logger.info(f"📝 输出内容长度: {len(full_content)} 字符")

        if full_reasoning:
            logger.info(f"💭 思考过程预览:\n{full_reasoning[:300]}...")
        logger.info(f"📄 DeepSeek 完整输出:\n{full_content}")

        generated_json = full_content

        # 如果有思考过程，作为单独的消息添加（标记为 thinking）
        # 🔥 使用与流式chunk相同的 message_id，确保前端可以正确更新消息
        if full_reasoning:
            messages.append(AIMessage(
                content=full_reasoning,
                additional_kwargs={"thinking": True},
                id=thinking_message_id  # 🔥 使用相同的 ID
            ))

        # 添加 DeepSeek 的最终输出
        # 🔥 使用与流式chunk相同的 message_id
        messages.append(AIMessage(
            content=full_content,
            id=content_message_id  # 🔥 使用相同的 ID
        ))

    except TimeoutError as e:
        # LLM调用超时
        logger.error(f"❌ DeepSeek API 超时: {e}")
        generated_json = ""
        messages.append(AIMessage(content=f"⏱️ 生成超时，请稍后重试"))
        return {
            "generated_json": generated_json,
            "messages": messages,
            "validation_errors": ["timeout"]  # 标记为超时错误
        }
    except Exception as e:
        # 其他错误（网络错误、API错误等）
        logger.error(f"❌ DeepSeek API 调用失败: {e}", exc_info=True)
        generated_json = ""
        messages.append(AIMessage(content=f"❌ 生成失败: {str(e)}"))
        return {
            "generated_json": generated_json,
            "messages": messages,
            "validation_errors": [f"api_error: {str(e)}"]
        }

    return {
        "generated_json": generated_json,
        "messages": messages
    }


def validator_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    验证 JSON 节点

    验证生成的 JSON 是否符合 Schema 和业务规则。
    """
    generated_json = state["generated_json"]
    logger.info("验证生成的 JSON")

    # 准备消息列表
    messages = []

    # 添加开始验证的消息
    messages.append(AIMessage(content="🔍 正在验证技能配置的合法性..."))

    errors = []

    try:
        # 从 Markdown 中提取 JSON
        json_content = extract_json_from_markdown(generated_json)
        logger.info(f"提取的 JSON 长度: {len(json_content)}")
        logger.debug(f"提取的 JSON 内容预览: {json_content[:500]}...")  # 只记录前500字符

        # 解析 JSON
        skill_data = json.loads(json_content)

        # 基础验证
        required_fields = ["skillName", "skillId", "actions"]
        for field in required_fields:
            if field not in skill_data:
                errors.append(f"缺少必填字段: {field}")

        # Actions 验证
        if "actions" in skill_data:
            actions = skill_data["actions"]
            if not isinstance(actions, list):
                errors.append("actions 字段必须是数组")
            elif len(actions) == 0:
                errors.append("actions 数组不能为空")
            else:
                # 验证每个 Action
                for i, action in enumerate(actions):
                    if not isinstance(action, dict):
                        errors.append(f"Action[{i}] 必须是对象")
                    elif "actionType" not in action:
                        errors.append(f"Action[{i}] 缺少 actionType 字段")

        # 数值范围验证
        if "cooldown" in skill_data:
            cooldown = skill_data["cooldown"]
            if not isinstance(cooldown, (int, float)) or cooldown < 0:
                errors.append(f"cooldown 必须是非负数，当前值: {cooldown}")

    except json.JSONDecodeError as e:
        errors.append(f"JSON 解析失败: {str(e)}")
    except Exception as e:
        errors.append(f"验证异常: {str(e)}")

    if errors:
        logger.warning(f"验证失败，发现 {len(errors)} 个错误")
        errors_list = "\n".join([f"• {err}" for err in errors])
        message = f"⚠️ **验证失败**，发现 {len(errors)} 个错误：\n\n{errors_list}"
    else:
        logger.info("验证通过")
        message = "✅ **验证通过！** 技能配置符合规范。"

    messages.append(AIMessage(content=message))

    return {
        "validation_errors": errors,
        "messages": messages
    }


def fixer_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    修复 JSON 节点

    根据验证错误，使用 LLM 修复 JSON。
    """
    from ..prompts.prompt_manager import get_prompt_manager

    generated_json = state["generated_json"]
    errors = state["validation_errors"]

    logger.info(f"修复 JSON，错误数: {len(errors)}")

    # 格式化错误信息
    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])

    # 准备消息列表
    messages = []

    # 添加开始修复的消息
    messages.append(AIMessage(content=f"🔍 发现 {len(errors)} 个错误，正在调用 DeepSeek AI 进行修复...\n\n错误列表：\n{errors_text}"))

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("validation_fix")

    # 调用 LLM
    llm = get_llm(temperature=0.3)  # 修复时使用更低温度
    chain = prompt | llm

    response = chain.invoke({
        "errors": errors_text,
        "json": generated_json
    })

    fixed_json = response.content

    # 添加 DeepSeek 修复回应
    messages.append(AIMessage(content=f"💬 **DeepSeek 回应：**\n\n已针对 {len(errors)} 个错误进行修复 (尝试 {state['retry_count'] + 1}/{state['max_retries']})。"))

    # 显示修复后的JSON
    display_message = f"🔧 **已修复技能配置：**\n\n```json\n{fixed_json}\n```"
    messages.append(AIMessage(content=display_message))

    return {
        "generated_json": fixed_json,
        "retry_count": state["retry_count"] + 1,
        "messages": messages
    }


def finalize_node(state: SkillGenerationState) -> Dict[str, Any]:
    """
    最终化节点

    将生成的 JSON 解析为最终结果。
    """
    generated_json = state["generated_json"]

    try:
        # 从 Markdown 中提取 JSON
        json_content = extract_json_from_markdown(generated_json)
        logger.info(f"最终化：提取的 JSON 长度: {len(json_content)}")

        final_result = json.loads(json_content)
        logger.info("技能生成成功")
    except json.JSONDecodeError as e:
        final_result = {
            "error": f"JSON 解析失败: {str(e)}",
            "raw_json": generated_json
        }
        logger.error(f"最终 JSON 解析失败: {e}")

    return {
        "final_result": final_result,
        "messages": [HumanMessage(content="技能生成完成")]
    }


# ==================== 条件判断函数 ====================

def should_continue(state: SkillGenerationState) -> str:
    """
    判断是否继续修复循环

    Returns:
        "fix" - 继续修复
        "finalize" - 结束，返回结果
    """
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    # 如果没有错误，结束
    if not errors:
        return "finalize"

    # 如果达到最大重试次数，结束
    if retry_count >= max_retries:
        logger.warning(f"达到最大重试次数 {max_retries}，停止修复")
        return "finalize"

    # 继续修复
    return "fix"
