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

    # 从环境变量读取超时配置
    # deepseek-reasoner 是深度思考模型，复杂任务可能需要 5 分钟以上
    timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "300"))  # 默认 5 分钟
    max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "2"))

    logger.info(f"初始化 LLM: model={model}, timeout={timeout}s, max_retries={max_retries}")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        timeout=timeout,  # 请求超时（秒）
        max_retries=max_retries,  # 最大重试次数
        # 添加 HTTP 客户端配置，确保超时生效
        http_client=None,  # 使用默认 httpx 客户端
    )


# ==================== Schema 转换辅助函数 ====================

def _prepare_payload_text(payload: Any) -> str:
    """
    将异构的 payload（AIMessage/BaseModel/str/dict）规范化为原始文本

    支持多种输入类型：
    - str: 直接返回
    - AIMessage/有 content 属性的对象: 返回 content
    - Pydantic Model: 转换为 JSON 字符串
    - dict/list: 序列化为 JSON

    Args:
        payload: 任意类型的输入

    Returns:
        规范化后的文本字符串
    """
    if payload is None:
        return ""

    # 字符串直接返回
    if isinstance(payload, str):
        return payload

    # AIMessage 或其他有 content 属性的对象
    if hasattr(payload, "content"):
        content = payload.content
        # 🔥 LangChain 可能存储结构化响应为 List[dict]，需要提取文本部分
        if isinstance(content, list):
            # 尝试提取文本内容
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    # 常见格式：{'type': 'output_text', 'text': '...'}
                    text_parts.append(item.get('text', ''))
                elif isinstance(item, str):
                    text_parts.append(item)
            if text_parts:
                return ''.join(text_parts)
        elif isinstance(content, dict):
            # dict 格式：尝试提取文本字段
            return content.get('text', content.get('content', json.dumps(content, ensure_ascii=False)))
        # 其他情况：转字符串
        return str(content)

    # Pydantic V2 Model
    if hasattr(payload, "model_dump_json"):
        try:
            return payload.model_dump_json()
        except Exception:
            pass

    # Pydantic V1 Model 或其他有 model_dump 的对象
    if hasattr(payload, "model_dump"):
        try:
            return json.dumps(payload.model_dump(), ensure_ascii=False)
        except Exception:
            pass

    # dict 或 list
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, ensure_ascii=False)

    # 其他类型：强制转字符串
    return str(payload)


def _safe_int(value: Any, default: int = 0, min_value: int = 0) -> int:
    """
    安全地将值转换为整数

    支持：str, int, float, Decimal 等类型
    容错：无效值返回 default，负数钳制到 min_value

    Args:
        value: 待转换的值
        default: 转换失败时的默认值
        min_value: 最小值（用于钳制负数）

    Returns:
        整数值
    """
    if value is None:
        return default

    try:
        # 尝试直接转 int
        result = int(value)
    except (ValueError, TypeError):
        try:
            # 尝试先转 float 再转 int（处理 "12.5" 这种情况）
            result = int(float(value))
        except (ValueError, TypeError):
            # 完全无法转换，使用默认值
            logger.debug(f"无法将 {value} (type={type(value)}) 转换为 int，使用默认值 {default}")
            return default

    # 钳制到最小值
    return max(result, min_value)


def _normalize_existing_tracks(payload_dict: Dict[str, Any], source: str):
    """
    规范化已有 tracks 结构的 payload

    处理场景：DeepSeek 已经生成了 tracks，但可能存在：
    - 某些 action 缺少 _odin_type
    - totalDuration 计算错误
    - frame/duration 为字符串或浮点数

    Args:
        payload_dict: 已解析的 dict，包含 tracks 字段
        source: 来源描述

    Returns:
        验证通过的 OdinSkillSchema 实例
    """
    from pydantic import ValidationError
    from ..schemas import OdinSkillSchema

    # 规范化 tracks
    max_end_frame = 0
    normalized_tracks = []

    for track_dict in payload_dict.get("tracks", []):
        track_name = track_dict.get("trackName") or track_dict.get("track_name") or "Unknown Track"
        enabled = bool(track_dict.get("enabled", True))
        actions = track_dict.get("actions", [])

        normalized_actions = []
        for action in actions:
            # 🔥 使用 _safe_int 容错转换
            frame = _safe_int(action.get("frame"), default=0, min_value=0)
            duration = _safe_int(action.get("duration"), default=1, min_value=1)
            action_enabled = bool(action.get("enabled", True))
            parameters = action.get("parameters") or {}

            # 🔥 确保 _odin_type 存在
            if "_odin_type" not in parameters:
                fallback_type = (
                    parameters.get("odinType") or
                    action.get("_odin_type") or
                    action.get("odinType") or
                    "4|SkillSystem.Actions.GenericAction, Assembly-CSharp"
                )
                parameters = {**parameters, "_odin_type": fallback_type}
                logger.debug(f"为 track[{track_name}].action (frame={frame}) 补充 _odin_type")

            normalized_actions.append({
                "frame": frame,
                "duration": duration,
                "enabled": action_enabled,
                "parameters": parameters
            })

            # 更新最大结束帧
            max_end_frame = max(max_end_frame, frame + duration)

        normalized_tracks.append({
            "trackName": track_name,
            "enabled": enabled,
            "actions": normalized_actions
        })

    # 构建规范化的 dict
    normalized_dict = {
        "skillName": payload_dict.get("skillName") or "Unnamed Skill",
        "skillId": payload_dict.get("skillId") or "unnamed-skill-001",
        "skillDescription": payload_dict.get("skillDescription") or "",
        "totalDuration": max(
            _safe_int(payload_dict.get("totalDuration"), default=0, min_value=1),
            max_end_frame or 1
        ),
        "frameRate": _safe_int(payload_dict.get("frameRate"), default=30, min_value=1),
        "tracks": normalized_tracks
    }

    # 最终验证
    try:
        final_skill = OdinSkillSchema.model_validate(normalized_dict)
        logger.info(
            f"✅ {source} tracks 结构规范化成功 "
            f"({len(normalized_tracks)} tracks, "
            f"{sum(len(t['actions']) for t in normalized_tracks)} actions)"
        )
        return final_skill
    except ValidationError as e:
        logger.error(f"❌ 规范化后的 tracks 仍然无法验证: {e}")
        raise ValueError(f"{source} tracks 规范化失败") from e


def _enforce_odin_structure(payload: Any, source: str):
    """
    强制将任意格式的 payload 转换为符合 OdinSkillSchema 的结构

    这个函数实现了确定性转换层，确保即使 DeepSeek 生成了不规范的格式
    （如扁平的 actions 数组），也能自动转换为正确的 tracks 嵌套结构。

    转换策略：
    1. 首先尝试直接验证为 OdinSkillSchema
    2. 如果失败，尝试解析为 SimplifiedSkillSchema（扁平结构）
    3. 将扁平结构转换为嵌套的 tracks 结构
    4. 补充缺失的必填字段（如 _odin_type）
    5. 重新计算 totalDuration

    Args:
        payload: 可以是 AIMessage、字符串、dict 等
        source: payload 来源描述（用于日志）

    Returns:
        验证通过的 OdinSkillSchema 实例

    Raises:
        ValueError: 如果 payload 无法转换为有效的 OdinSkillSchema
    """
    from pydantic import ValidationError
    from ..schemas import OdinSkillSchema, SimplifiedSkillSchema

    # 如果已经是 OdinSkillSchema，直接返回
    if isinstance(payload, OdinSkillSchema):
        logger.info(f"{source} payload 已经是 OdinSkillSchema，直接使用")
        return payload

    # 步骤1：规范化为文本
    payload_text = _prepare_payload_text(payload)
    if not payload_text:
        raise ValueError(f"{source} payload 为空，无法转换")

    # 步骤2：提取 JSON（处理 Markdown 代码块）
    json_blob = extract_json_from_markdown(payload_text)

    # 步骤3：尝试直接验证为 OdinSkillSchema
    try:
        validated_skill = OdinSkillSchema.model_validate_json(json_blob)
        logger.info(f"✅ {source} payload 直接验证为 OdinSkillSchema 成功")
        return validated_skill
    except ValidationError as schema_error:
        logger.debug(
            f"⚠️ {source} payload 无法直接验证为 OdinSkillSchema，尝试规范化转换",
            exc_info=True
        )

    # 步骤4：解析为 dict，准备转换
    try:
        payload_dict = json.loads(json_blob)
    except json.JSONDecodeError as decode_err:
        raise ValueError(f"{source} payload 不是有效的 JSON") from decode_err

    # 步骤5：检查格式类型
    has_tracks = "tracks" in payload_dict and isinstance(payload_dict["tracks"], list)
    has_actions = "actions" in payload_dict and isinstance(payload_dict["actions"], list)

    if not has_tracks and not has_actions:
        # 既不是 OdinSkillSchema 也不是 SimplifiedSkillSchema，无法转换
        raise ValueError(
            f"{source} payload 既没有 tracks 字段也没有 actions 字段，无法识别格式"
        )

    # 🔥 分支处理：tracks 已存在（但可能有字段缺失）vs 扁平 actions
    if has_tracks:
        logger.info(f"🔄 检测到 tracks 嵌套结构，进行规范化修复...")
        return _normalize_existing_tracks(payload_dict, source)

    # 否则处理扁平 actions 格式
    logger.info(f"🔄 检测到扁平 actions 结构，转换为 tracks 嵌套结构...")

    # 步骤6：验证为 SimplifiedSkillSchema
    try:
        simplified = SimplifiedSkillSchema.model_validate(payload_dict)
    except ValidationError as e:
        raise ValueError(f"{source} payload 也无法验证为 SimplifiedSkillSchema") from e

    logger.info(f"🔄 检测到扁平 actions 结构，开始转换为 tracks 嵌套结构...")

    # 步骤7：按 trackName 分组 actions
    grouped_actions: Dict[str, List[Dict[str, Any]]] = {}
    for action in simplified.actions:
        # 获取 trackName（支持多种字段名）
        track_name = (
            action.get("trackName") or
            action.get("track_name") or
            "Animation Track"  # 默认轨道
        )
        grouped_actions.setdefault(track_name, []).append(action)

    # 步骤8：如果没有任何 actions，创建一个默认 action
    if not grouped_actions:
        logger.warning(f"{source} 没有任何 actions，创建默认 action")
        grouped_actions["Animation Track"] = [{
            "frame": 0,
            "duration": 1,
            "enabled": True,
            "parameters": {
                "_odin_type": "4|SkillSystem.Actions.GenericAction, Assembly-CSharp"
            }
        }]

    # 步骤9：构建 tracks 数组并规范化 actions
    tracks: List[Dict[str, Any]] = []
    max_end_frame = 0

    for track_name, actions in grouped_actions.items():
        odin_actions = []

        for action in actions:
            # 🔥 提取并规范化字段（使用 _safe_int 容错转换）
            frame = _safe_int(action.get("frame"), default=0, min_value=0)
            duration = _safe_int(action.get("duration"), default=1, min_value=1)
            enabled = bool(action.get("enabled", True))
            parameters = action.get("parameters") or {}

            # 🔥 关键修复：确保 _odin_type 存在
            if "_odin_type" not in parameters:
                # 尝试从多个可能的位置获取
                fallback_type = (
                    parameters.get("odinType") or
                    action.get("_odin_type") or
                    action.get("odinType") or
                    "4|SkillSystem.Actions.GenericAction, Assembly-CSharp"  # 终极默认值
                )
                parameters = {**parameters, "_odin_type": fallback_type}
                logger.debug(f"为 action (frame={frame}) 补充 _odin_type: {fallback_type}")

            odin_actions.append({
                "frame": frame,
                "duration": duration,
                "enabled": enabled,
                "parameters": parameters
            })

            # 更新最大结束帧
            max_end_frame = max(max_end_frame, frame + duration)

        # 添加到 tracks
        tracks.append({
            "trackName": track_name,
            "enabled": True,
            "actions": odin_actions
        })

    # 步骤10：构建规范化的 dict
    normalized_dict = {
        "skillName": simplified.skillName,
        "skillId": simplified.skillId,
        "skillDescription": (
            simplified.skillDescription or
            payload_dict.get("skillDescription") or
            ""
        ),
        "totalDuration": max(
            _safe_int(payload_dict.get("totalDuration"), default=0, min_value=1),
            max_end_frame or 1
        ),
        "frameRate": _safe_int(payload_dict.get("frameRate"), default=30, min_value=1),
        "tracks": tracks
    }

    # 步骤11：最终验证
    try:
        final_skill = OdinSkillSchema.model_validate(normalized_dict)
        logger.info(
            f"✅ {source} payload 成功转换为 OdinSkillSchema "
            f"({len(tracks)} tracks, {sum(len(t['actions']) for t in tracks)} actions)"
        )
        return final_skill
    except ValidationError as e:
        logger.error(f"❌ 规范化后的 dict 仍然无法验证为 OdinSkillSchema: {e}")
        raise ValueError(f"{source} 规范化失败") from e


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
    🔥 使用 structured output 确保符合 Odin 格式

    Args:
        state: 技能生成状态
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from langgraph.config import get_stream_writer
    from ..schemas import OdinSkillSchema  # 🔥 导入 Schema

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

    # 🔥 调用 LLM 使用 structured output
    llm = get_llm()

    # 🔥 关键改动：绑定 Pydantic Schema，强制 DeepSeek 按格式输出
    # 注意：deepseek-reasoner 可能不完全支持 structured output，这里使用 method="json_mode"
    try:
        structured_llm = llm.with_structured_output(
            OdinSkillSchema,
            method="json_mode",  # 使用 JSON mode（兼容性更好）
            include_raw=False
        )
    except Exception as e:
        logger.warning(f"⚠️ Structured output 初始化失败，降级使用普通模式: {e}")
        structured_llm = llm

    chain = prompt | structured_llm

    logger.info(f"⏳ 正在调用 DeepSeek API (structured output + 流式)...")
    api_start_time = time.time()
    first_chunk_time = None

    # 收集流式输出（分离思考过程和最终输出）
    full_reasoning = ""  # 思考过程
    full_content = ""    # 最终输出
    structured_result = None  # 🔥 结构化结果

    # 🔥 生成唯一的 message_id 用于跟踪流式消息
    thinking_message_id = f"thinking_{api_start_time}"
    content_message_id = f"content_{api_start_time}"

    # 🔥 P0改进：添加错误边界
    try:
        # 🔥 策略调整：先用普通LLM流式生成（保留thinking体验），然后验证Schema
        # 因为 structured_output 可能不支持流式 + reasoning
        llm_for_stream = get_llm()  # 使用普通LLM进行流式输出
        stream_chain = prompt | llm_for_stream

        # 准备 prompt 输入（用于流式和可能的 structured fallback）
        prompt_inputs = {
            "requirement": requirement,
            "similar_skills": similar_skills_text or "无参考技能",
            "action_schemas": action_schemas_text or "无Action参考"  # 🔥 新增：传递action schemas
        }

        # 流式调用
        for chunk in stream_chain.stream(prompt_inputs):
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

        # 🔥 强制转换：使用确定性转换层保证格式正确
        logger.info("🔍 使用 _enforce_odin_structure 强制转换为 OdinSkillSchema...")

        normalized_skill = None
        structured_fallback_used = False

        # 步骤1：尝试从流式输出强制转换
        try:
            normalized_skill = _enforce_odin_structure(full_content, "stream_output")
            logger.info("✅ 流式输出成功转换为 OdinSkillSchema")
        except Exception as e:
            logger.warning(f"⚠️ 流式输出无法转换为 Odin schema: {e}")

        # 步骤2：如果流式输出转换失败且 structured LLM 可用，触发 structured fallback
        if normalized_skill is None and structured_llm is not llm:
            logger.info("🔄 触发 structured fallback：使用非流式 structured LLM 重新生成...")
            try:
                # 使用 structured LLM 进行非流式调用
                structured_response = chain.invoke(prompt_inputs)

                # 尝试强制转换 structured 响应
                normalized_skill = _enforce_odin_structure(
                    structured_response,
                    "structured_fallback"
                )
                structured_fallback_used = True
                logger.info("✅ Structured fallback 成功生成符合 Schema 的配置")
            except Exception as e:
                logger.error(f"❌ Structured fallback 也失败了: {e}", exc_info=True)

        # 步骤3：根据转换结果设置 generated_json 和提示消息
        if normalized_skill is not None:
            # 成功转换，使用规范化的 JSON
            generated_json = normalized_skill.model_dump_json(indent=2)

            # 根据转换来源生成不同的提示
            if structured_fallback_used:
                origin_hint = "Structured Fallback 成功生成"
            else:
                origin_hint = "流式输出成功转换"

            messages.append(AIMessage(
                content=f"✅ **Schema 验证通过**：{origin_hint}，技能配置符合完整的 tracks/actions 嵌套结构"
            ))
        else:
            # 所有转换尝试都失败，返回原始输出（让 validator/fixer 继续处理）
            logger.warning("⚠️ 所有转换尝试均失败，返回原始流式输出")
            generated_json = full_content
            messages.append(AIMessage(
                content="⚠️ **Schema 验证警告**：格式转换失败，原始输出将交由 validator/fixer 继续处理"
            ))

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

    验证生成的 JSON 是否符合 Odin Schema 和业务规则。
    🔥 更新：支持tracks嵌套结构验证
    """
    from ..schemas import OdinSkillSchema  # 🔥 导入 Schema
    from pydantic import ValidationError

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

        # 🔥 使用 Pydantic Schema 验证（Pydantic V2 API）
        try:
            skill_data = OdinSkillSchema.model_validate_json(json_content)
            logger.info("✅ Pydantic Schema 验证通过")

            # 🔥 业务规则验证（超出 Pydantic 的额外检查）
            # 1. 检查 totalDuration 是否覆盖所有 actions
            max_action_end_frame = 0
            for track in skill_data.tracks:
                for action in track.actions:
                    action_end = action.frame + action.duration
                    if action_end > max_action_end_frame:
                        max_action_end_frame = action_end

            if skill_data.totalDuration < max_action_end_frame:
                errors.append(
                    f"totalDuration ({skill_data.totalDuration}) 小于最大action结束帧 ({max_action_end_frame})"
                )

            # 2. 检查每个 action 的 parameters 是否包含 _odin_type
            for track_idx, track in enumerate(skill_data.tracks):
                for action_idx, action in enumerate(track.actions):
                    if "_odin_type" not in action.parameters:
                        errors.append(
                            f"Track[{track_idx}].Action[{action_idx}] 的 parameters 缺少 _odin_type 字段"
                        )

        except ValidationError as e:
            # Pydantic 验证失败，提取错误信息
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = error["msg"]
                errors.append(f"{field_path}: {error_msg}")

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
    🔥 使用 structured output + 强制转换确保修复后符合 Schema
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from ..schemas import OdinSkillSchema

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

    # 🔥 调用 LLM 并尝试使用 structured output
    llm = get_llm(temperature=0.3)  # 修复时使用更低温度

    # 尝试初始化 structured LLM
    try:
        fixer_llm = llm.with_structured_output(
            OdinSkillSchema,
            method="json_mode",
            include_raw=False
        )
        logger.info("✅ Fixer 使用 structured output 模式")
    except Exception as e:
        logger.warning(f"⚠️ Fixer structured output 不可用，使用普通模式: {e}")
        fixer_llm = llm

    chain = prompt | fixer_llm

    # 准备 prompt 输入
    prompt_inputs = {
        "errors": errors_text,
        "json": generated_json
    }

    # 调用 LLM
    response = chain.invoke(prompt_inputs)

    # 🔥 使用强制转换确保修复后的格式正确
    normalized_skill = None
    try:
        normalized_skill = _enforce_odin_structure(
            response,
            "fixer_structured" if fixer_llm is not llm else "fixer_raw"
        )
        fixed_json = normalized_skill.model_dump_json(indent=2)
        logger.info("✅ Fixer 成功转换为 OdinSkillSchema")

        # 添加成功的提示
        messages.append(AIMessage(
            content=f"💬 **DeepSeek 回应：**\n\n已针对 {len(errors)} 个错误进行修复 (尝试 {state['retry_count'] + 1}/{state['max_retries']})。"
        ))
        messages.append(AIMessage(
            content="✅ **Schema 验证通过**：修复后的配置符合完整的 tracks/actions 嵌套结构"
        ))

    except Exception as e:
        # 强制转换失败，返回原始响应内容
        logger.error(f"❌ Fixer 规范化失败，返回原始内容: {e}", exc_info=True)
        fixed_json = _prepare_payload_text(response)

        # 添加警告提示
        messages.append(AIMessage(
            content=f"💬 **DeepSeek 回应：**\n\n已尝试修复 {len(errors)} 个错误 (尝试 {state['retry_count'] + 1}/{state['max_retries']})。"
        ))
        messages.append(AIMessage(
            content=f"⚠️ **Schema 验证警告**：修复后仍无法完全符合格式，将继续重试"
        ))

    # 显示修复后的JSON（截取预览）
    preview_json = fixed_json if len(fixed_json) <= 1000 else f"{fixed_json[:1000]}...\n(已截断，完整内容见最终结果)"
    display_message = f"🔧 **已修复技能配置：**\n\n```json\n{preview_json}\n```"
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
