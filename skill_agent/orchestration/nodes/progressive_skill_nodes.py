"""
渐进式技能生成节点实现
实现三阶段生成：骨架生成 → 逐Track生成 → 技能组装
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, TypedDict, Annotated, Optional, Literal, Tuple
from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from langgraph.config import get_stream_writer
from pydantic import ValidationError

from .skill_nodes import get_llm, get_openai_client, _prepare_payload_text
from ..schemas import SkillSkeletonSchema, TrackPlanItem, SkillTrack, OdinSkillSchema
from ..streaming import (
    ProgressEventType,
    emit_progress,
)
from core.odin_json_parser import serialize_to_odin

logger = logging.getLogger(__name__)


# ==================== 流式 LLM 调用辅助函数 ====================

# 🔥 注意：原 stream_llm_with_reasoning 函数已废弃
# LangGraph Studio 通过 stream_mode="messages" 自动捕获 LangChain LLM 的流式 token
# 不再需要手动处理流式输出，LangGraph 会自动追踪所有 LLM.invoke() 调用

# ==================== JSON 输出配置 ====================

# 输出目录（相对于 skill_agent 目录）
_OUTPUT_DIR = Path(__file__).parent.parent.parent / "Data" / "generated_skills"


def _save_generated_json(
    data: Dict[str, Any], 
    stage: str, 
    skill_name: str = "unknown",
    require_odin_format: bool = True
) -> Tuple[Optional[Path], bool]:
    """
    保存生成的 JSON 数据到文件

    Args:
        data: 要保存的数据
        stage: 生成阶段 (skeleton/track/final)
        skill_name: 技能名称
        require_odin_format: final 阶段是否强制要求 Odin 格式

    Returns:
        (保存的文件路径, 是否为Odin格式) 元组，路径为None表示失败
    """
    try:
        # 确保输出目录存在
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 生成文件名：{skill_name}_{stage}_{timestamp}.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in skill_name)
        filename = f"{safe_name}_{stage}_{timestamp}.json"
        filepath = _OUTPUT_DIR / filename
        
        is_odin_format = False

        # 如果是 final 阶段，转换为 Odin 序列化格式
        if stage == "final" and "tracks" in data:
            try:
                data_to_save = serialize_to_odin(data)
                is_odin_format = True
                logger.info("✅ 已将技能数据转换为 Odin 序列化格式")
            except Exception as e:
                if require_odin_format:
                    # 强制要求时记录错误但仍保存原始格式（同时保存两个文件）
                    logger.error(f"❌ Odin 序列化失败: {e}")
                    # 保存原始格式作为备份
                    backup_filename = f"{safe_name}_{stage}_raw_{timestamp}.json"
                    backup_filepath = _OUTPUT_DIR / backup_filename
                    with open(backup_filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    logger.warning(f"⚠️ 已保存原始格式备份: {backup_filepath}")
                    
                    # 尝试简化序列化（只处理 _odin_type）
                    data_to_save = _simple_odin_serialize(data)
                    logger.info("✅ 使用简化 Odin 序列化")
                else:
                    logger.warning(f"⚠️ Odin 序列化失败，使用原始格式: {e}")
                    data_to_save = data
        else:
            data_to_save = data

        # 保存 JSON（格式化输出，支持中文）
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 已保存 {stage} JSON: {filepath}")
        return filepath, is_odin_format

    except Exception as e:
        logger.warning(f"⚠️ 保存 JSON 失败: {e}")
        return None, False


def _simple_odin_serialize(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    简化的 Odin 序列化（当完整序列化失败时使用）
    
    只确保 _odin_type 格式正确，不做其他复杂转换
    """
    import copy
    result = copy.deepcopy(data)
    
    # 遍历所有 tracks 和 actions
    for track in result.get("tracks", []):
        for action in track.get("actions", []):
            params = action.get("parameters", {})
            odin_type = params.get("_odin_type", "")
            
            # 确保 _odin_type 有索引前缀
            if odin_type and "|" not in odin_type:
                # 添加默认索引 0
                params["_odin_type"] = f"0|{odin_type}"
    
    return result


# ==================== 流式输出辅助函数 ====================

def _get_writer_safe() -> Optional[Any]:
    """
    安全获取StreamWriter

    在非流式执行环境中不会报错
    """
    try:
        writer = get_stream_writer()
        logger.info(f"✅ 成功获取 StreamWriter: {type(writer)}")
        return writer
    except Exception as e:
        logger.warning(f"⚠️ 无法获取 StreamWriter: {e}")
        return None


def _emit_skeleton_progress(
    event_type: ProgressEventType,
    message: str,
    **kwargs
):
    """
    发送骨架生成进度事件的便捷函数
    """
    writer = _get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    # 骨架阶段进度固定为10%以内
    progress = kwargs.pop("progress", 0.05)

    emit_progress(
        writer,
        event_type,
        message,
        progress=progress,
        phase="skeleton",
        **kwargs
    )


def _emit_finalize_progress(
    event_type: ProgressEventType,
    message: str,
    is_valid: bool = True,
    **kwargs
):
    """
    发送最终化进度事件的便捷函数
    """
    writer = _get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    # 最终化阶段进度为100%
    progress = 1.0 if is_valid else 0.95

    emit_progress(
        writer,
        event_type,
        message,
        progress=progress,
        phase="finalize",
        **kwargs
    )


def _emit_track_progress(
    event_type: ProgressEventType,
    message: str,
    track_index: int,
    total_tracks: int,
    track_name: str = "",
    **kwargs
):
    """
    发送Track生成进度事件的便捷函数
    
    Args:
        event_type: 事件类型
        message: 消息内容
        track_index: 当前Track索引（0-based）
        total_tracks: Track总数
        track_name: Track名称
        **kwargs: 其他参数
    """
    writer = _get_writer_safe()
    if writer is None:
        logger.debug(f"[{event_type.value}] {message}")
        return

    # 计算进度：骨架10% + tracks占80%（按比例分配）
    base_progress = 0.1  # 骨架已完成
    track_weight = 0.8 / max(1, total_tracks)
    
    if event_type == ProgressEventType.TRACK_STARTED:
        progress = base_progress + track_index * track_weight
    elif event_type == ProgressEventType.TRACK_COMPLETED:
        progress = base_progress + (track_index + 1) * track_weight
    else:
        progress = base_progress + (track_index + 0.5) * track_weight

    emit_progress(
        writer,
        event_type,
        message,
        progress=progress,
        phase="track",
        track_index=track_index,
        track_name=track_name,
        total_tracks=total_tracks,
        **kwargs
    )


# ==================== State 定义 ====================

class ProgressiveSkillGenerationState(TypedDict):
    """
    渐进式技能生成状态

    支持三阶段生成：
    1. 骨架生成：生成技能元信息和 track 计划
    2. 逐 Track 生成：为每个 track 生成具体 actions
    3. 技能组装：组装完整技能并进行整体验证
    """

    # === 输入 ===
    requirement: str  # 用户需求描述
    similar_skills: List[Dict[str, Any]]  # RAG 检索的相似技能

    # === 阶段1输出 ===
    skill_skeleton: Dict[str, Any]  # 骨架数据（SkillSkeletonSchema）
    skeleton_validation_errors: List[str]  # 骨架验证错误
    skeleton_retry_count: int  # 骨架重试次数
    max_skeleton_retries: int  # 骨架最大重试次数（默认 2）

    # === 阶段2状态 ===
    track_plan: List[Dict[str, Any]]  # Track 计划列表
    current_track_index: int  # 当前正在生成的 track 索引
    current_track_data: Dict[str, Any]  # 当前生成的 track 数据
    generated_tracks: List[Dict[str, Any]]  # 已生成并验证通过的 tracks
    current_track_errors: List[str]  # 当前 track 的验证错误
    track_retry_count: int  # 当前 track 重试次数
    max_track_retries: int  # 单个 track 最大重试次数（默认 3）
    used_action_types: List[str]  # 已使用的 Action 类型（跨 Track 传递）

    # === 阶段3输出 ===
    assembled_skill: Dict[str, Any]  # 组装后的完整技能（OdinSkillSchema）
    final_validation_errors: List[str]  # 最终验证错误

    # === 兼容旧版 State 的字段 ===
    final_result: Dict[str, Any]  # 最终结果（等同于 assembled_skill，用于兼容旧版API）
    is_valid: bool  # 技能是否通过验证

    # === 通用 ===
    # 使用add_messages reducer确保消息正确累积
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str  # 线程ID（用于追踪会话）


# ==================== 默认 Action 模板 ====================

DEFAULT_ACTIONS_BY_TRACK_TYPE: Dict[str, List[Dict[str, Any]]] = {
    "animation": [
        {
            "action_name": "AnimationAction",
            "action_type": "SkillSystem.Actions.AnimationAction, Assembly-CSharp",
            "description": "播放角色动画",
            "parameters": [
                {"name": "animationClipName", "type": "string", "defaultValue": "Attack01"},
                {"name": "normalizedTime", "type": "float", "defaultValue": "0"},
                {"name": "crossFadeDuration", "type": "float", "defaultValue": "0.2"},
                {"name": "animationLayer", "type": "int", "defaultValue": "0"}
            ]
        }
    ],
    "effect": [
        {
            "action_name": "SpawnEffectAction",
            "action_type": "SkillSystem.Actions.SpawnEffectAction, Assembly-CSharp",
            "description": "生成特效",
            "parameters": [
                {"name": "effectPrefab", "type": "string", "defaultValue": "DefaultEffect"},
                {"name": "position", "type": "Vector3", "defaultValue": "(0,0,0)"},
                {"name": "duration", "type": "float", "defaultValue": "1.0"}
            ]
        },
        {
            "action_name": "DamageAction",
            "action_type": "SkillSystem.Actions.DamageAction, Assembly-CSharp",
            "description": "造成伤害",
            "parameters": [
                {"name": "damageAmount", "type": "float", "defaultValue": "10"},
                {"name": "damageType", "type": "DamageType", "defaultValue": "Physical"},
                {"name": "radius", "type": "float", "defaultValue": "1.0"}
            ]
        }
    ],
    "audio": [
        {
            "action_name": "PlaySoundAction",
            "action_type": "SkillSystem.Actions.PlaySoundAction, Assembly-CSharp",
            "description": "播放音效",
            "parameters": [
                {"name": "soundClip", "type": "string", "defaultValue": "DefaultSound"},
                {"name": "volume", "type": "float", "defaultValue": "1.0"},
                {"name": "pitch", "type": "float", "defaultValue": "1.0"}
            ]
        }
    ],
    "movement": [
        {
            "action_name": "MoveAction",
            "action_type": "SkillSystem.Actions.MoveAction, Assembly-CSharp",
            "description": "角色位移",
            "parameters": [
                {"name": "direction", "type": "Vector3", "defaultValue": "(0,0,1)"},
                {"name": "distance", "type": "float", "defaultValue": "2.0"},
                {"name": "speed", "type": "float", "defaultValue": "5.0"}
            ]
        }
    ],
    "camera": [
        {
            "action_name": "CameraShakeAction",
            "action_type": "SkillSystem.Actions.CameraShakeAction, Assembly-CSharp",
            "description": "镜头震动",
            "parameters": [
                {"name": "intensity", "type": "float", "defaultValue": "0.5"},
                {"name": "duration", "type": "float", "defaultValue": "0.3"}
            ]
        }
    ],
    "other": [
        {
            "action_name": "GenericAction",
            "action_type": "SkillSystem.Actions.GenericAction, Assembly-CSharp",
            "description": "通用Action",
            "parameters": []
        }
    ]
}


def get_default_actions_for_track_type(track_type: str) -> List[Dict[str, Any]]:
    """
    获取指定Track类型的默认Action模板
    
    当RAG检索失败时使用，确保LLM有参考格式
    """
    return DEFAULT_ACTIONS_BY_TRACK_TYPE.get(track_type, DEFAULT_ACTIONS_BY_TRACK_TYPE["other"])


# ==================== 骨架验证函数 ====================

def validate_skeleton(skeleton: Dict[str, Any]) -> List[str]:
    """
    验证技能骨架的合法性

    验证规则：
    1. skillName、skillId 非空
    2. totalDuration >= 30（至少1秒@30fps）
    3. trackPlan 非空数组
    4. 每个 trackPlan 项包含 trackName 和 purpose

    Args:
        skeleton: 骨架数据（dict 格式）

    Returns:
        错误列表，空表示验证通过
    """
    errors = []

    # 验证1：基本字段非空
    if not skeleton.get("skillName"):
        errors.append("skillName 不能为空")

    if not skeleton.get("skillId"):
        errors.append("skillId 不能为空")

    # 验证2：totalDuration 至少 30 帧
    total_duration = skeleton.get("totalDuration", 0)
    if not isinstance(total_duration, int) or total_duration < 30:
        errors.append(f"totalDuration ({total_duration}) 必须是 >= 30 的整数")

    # 验证3：trackPlan 非空
    track_plan = skeleton.get("trackPlan", [])
    if not track_plan or not isinstance(track_plan, list):
        errors.append("trackPlan 不能为空，必须是数组")
        return errors  # 提前返回，后续验证依赖 trackPlan

    # 验证4：每个 trackPlan 项的必填字段
    track_names_seen = set()
    for idx, track_item in enumerate(track_plan):
        if not isinstance(track_item, dict):
            errors.append(f"trackPlan[{idx}] 必须是对象")
            continue

        track_name = track_item.get("trackName")
        purpose = track_item.get("purpose")

        if not track_name:
            errors.append(f"trackPlan[{idx}].trackName 不能为空")
        else:
            # 检查 trackName 唯一性
            if track_name in track_names_seen:
                errors.append(f"trackPlan[{idx}].trackName '{track_name}' 重复")
            track_names_seen.add(track_name)

        if not purpose:
            errors.append(f"trackPlan[{idx}].purpose 不能为空")

        # 验证 estimatedActions 合理性
        estimated_actions = track_item.get("estimatedActions", 1)
        if not isinstance(estimated_actions, int) or estimated_actions < 1 or estimated_actions > 20:
            errors.append(f"trackPlan[{idx}].estimatedActions ({estimated_actions}) 必须在 1-20 之间")

    return errors


# ==================== 阶段1：骨架生成节点 ====================

def skeleton_generator_node(state: ProgressiveSkillGenerationState, writer: StreamWriter) -> Dict[str, Any]:
    """
    骨架生成节点（阶段1）- 使用 LangChain LLM 实现流式输出

    职责：
    1. 根据用户需求和相似技能，生成技能骨架和 track 计划
    2. 🔥 使用 OpenAI SDK 直接调用 DeepSeek API，支持 reasoning_content 流式输出
    3. 通过 writer 发送 thinking_chunk/content_chunk 自定义事件
    4. 验证骨架数据
    5. 发送进度事件

    Args:
        state: 渐进式技能生成状态
        writer: LangGraph 注入的 StreamWriter，用于流式输出自定义事件

    输出：
    - skill_skeleton: 骨架数据
    - track_plan: Track 计划列表
    - skeleton_validation_errors: 验证错误
    - current_track_index: 初始化为 0
    - generated_tracks: 初始化为空数组
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown

    requirement = state["requirement"]
    similar_skills = state.get("similar_skills", [])

    logger.info(f"🦴 开始生成技能骨架: {requirement[:50]}...")

    # 发送骨架生成开始事件
    _emit_skeleton_progress(
        ProgressEventType.SKELETON_STARTED,
        f"开始生成技能骨架...",
        progress=0.02,
        data={"requirement": requirement[:50]}
    )

    # 准备消息列表
    messages = []
    messages.append(AIMessage(content=f"🦴 **阶段1/3**: 正在生成技能骨架和 Track 计划..."))

    # 格式化相似技能（简化版，只用于参考结构）
    similar_skills_text = format_similar_skills(similar_skills)

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skeleton_generation")

    # 发送LLM调用事件
    _emit_skeleton_progress(
        ProgressEventType.LLM_CALLING,
        "调用LLM生成技能骨架...",
        progress=0.03
    )

    api_start_time = time.time()
    first_chunk_time = None
    logger.info("⏳ 正在调用 DeepSeek API 生成骨架（OpenAI SDK 流式）...")

    # 🔥 生成唯一的 message_id 用于跟踪流式消息
    thinking_message_id = f"skeleton_thinking_{api_start_time}"
    content_message_id = f"skeleton_content_{api_start_time}"

    # 收集流式输出
    full_reasoning = ""
    full_content = ""

    try:
        # 🔥 使用 OpenAI SDK 直接调用 DeepSeek API
        # LangChain 的 ChatOpenAI 不能正确处理 DeepSeek Reasoner 的 reasoning_content
        client = get_openai_client()

        # 渲染 prompt 模板
        prompt_inputs = {
            "requirement": requirement,
            "similar_skills": similar_skills_text or "无参考技能"
        }
        prompt_value = prompt.invoke(prompt_inputs)

        # 转换为 OpenAI 格式的 messages
        openai_messages = []
        for msg in prompt_value.to_messages():
            msg_type = msg.__class__.__name__.lower()
            if "system" in msg_type:
                openai_messages.append({"role": "system", "content": msg.content})
            elif "human" in msg_type:
                openai_messages.append({"role": "user", "content": msg.content})
            elif "ai" in msg_type:
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                openai_messages.append({"role": "user", "content": msg.content})

        logger.info(f"📤 发送请求到 DeepSeek API，消息数: {len(openai_messages)}")

        # 🔥 发送初始思考提示
        if writer:
            try:
                writer({
                    "type": "thinking_chunk",
                    "message_id": thinking_message_id,
                    "chunk": "🤔 DeepSeek Reasoner 正在分析技能需求...\n"
                })
            except Exception as e:
                logger.warning(f"⚠️ 发送初始 thinking chunk 失败: {e}")

        # 🔥 使用 OpenAI SDK 进行流式调用
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=openai_messages,
            stream=True
        )

        # 流式处理响应
        for chunk in response:
            # 记录首字节时间（TTFB）
            if first_chunk_time is None:
                first_chunk_time = time.time()
                ttfb = first_chunk_time - api_start_time
                logger.info(f"⚡ 首字节延迟 (TTFB): {ttfb:.2f}s")

            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # 提取 reasoning_content（思考过程）
            reasoning_chunk = getattr(delta, 'reasoning_content', None)
            if reasoning_chunk:
                full_reasoning += reasoning_chunk
                # 降低日志频率
                if len(full_reasoning) % 500 < len(reasoning_chunk):
                    logger.debug(f"📝 Reasoning progress: {len(full_reasoning)} chars")

                # 🔥 使用 writer 实时推送 thinking chunk
                if writer:
                    try:
                        writer({
                            "type": "thinking_chunk",
                            "message_id": thinking_message_id,
                            "chunk": reasoning_chunk
                        })
                    except Exception as e:
                        logger.debug(f"发送 thinking chunk 失败: {e}")

            # 提取 content（最终输出）
            content_chunk = getattr(delta, 'content', None)
            if content_chunk:
                full_content += content_chunk
                # 降低日志频率
                if len(full_content) % 200 < len(content_chunk):
                    logger.debug(f"📝 Content progress: {len(full_content)} chars")

                # 🔥 使用 writer 实时推送 content chunk
                if writer:
                    try:
                        writer({
                            "type": "content_chunk",
                            "message_id": content_message_id,
                            "chunk": content_chunk
                        })
                    except Exception as e:
                        logger.debug(f"发送 content chunk 失败: {e}")

        api_elapsed = time.time() - api_start_time
        logger.info(f"⏱️ 骨架生成耗时: {api_elapsed:.2f}s")
        logger.info(f"🧠 思考内容长度: {len(full_reasoning)} 字符")
        logger.info(f"📝 输出内容长度: {len(full_content)} 字符")

        # 解析 JSON 响应
        json_content = extract_json_from_markdown(full_content)
        skeleton_dict = json.loads(json_content)

        # 使用 Pydantic 验证
        validated = SkillSkeletonSchema.model_validate(skeleton_dict)
        skeleton_dict = validated.model_dump()
        logger.info(f"✅ 骨架生成成功: {skeleton_dict.get('skillName')}")

        # 保存骨架 JSON 到文件（skeleton 阶段不涉及 Odin 序列化）
        _save_generated_json(
            skeleton_dict,
            stage="skeleton",
            skill_name=skeleton_dict.get("skillName", "unknown"),
            require_odin_format=False
        )

        # 验证骨架
        validation_errors = validate_skeleton(skeleton_dict)

        if validation_errors:
            logger.warning(f"⚠️ 骨架验证发现 {len(validation_errors)} 个错误")
            messages.append(AIMessage(
                content=f"⚠️ 骨架验证发现 {len(validation_errors)} 个问题:\n" +
                        "\n".join([f"• {e}" for e in validation_errors])
            ))
        else:
            logger.info("✅ 骨架验证通过")
            # 构建成功消息
            track_plan = skeleton_dict.get("trackPlan", [])
            track_summary = "\n".join([
                f"  {i+1}. **{t['trackName']}** - {t['purpose'][:30]}... (预估 {t['estimatedActions']} actions)"
                for i, t in enumerate(track_plan)
            ])
            messages.append(AIMessage(
                content=f"✅ **骨架生成完成**\n\n" +
                        f"**技能名称**: {skeleton_dict['skillName']}\n" +
                        f"**技能ID**: {skeleton_dict['skillId']}\n" +
                        f"**总时长**: {skeleton_dict['totalDuration']} 帧\n\n" +
                        f"**Track 计划** ({len(track_plan)} 个轨道):\n{track_summary}"
            ))

        # 🔥 添加思考过程消息（如果有）
        if full_reasoning:
            messages.append(AIMessage(
                content=full_reasoning,
                additional_kwargs={"thinking": True},
                id=thinking_message_id
            ))

        # 发送骨架生成完成事件
        _emit_skeleton_progress(
            ProgressEventType.SKELETON_COMPLETED,
            f"骨架生成完成: {skeleton_dict.get('skillName', 'Unknown')}",
            progress=0.1,
            data={
                "skill_name": skeleton_dict.get("skillName"),
                "total_duration": skeleton_dict.get("totalDuration"),
                "track_count": len(skeleton_dict.get("trackPlan", []))
            }
        )

        return {
            "skill_skeleton": skeleton_dict,
            "track_plan": skeleton_dict.get("trackPlan", []),
            "skeleton_validation_errors": validation_errors,
            "current_track_index": 0,
            "generated_tracks": [],
            "track_retry_count": 0,
            "messages": messages
        }

    except ValidationError as e:
        # Pydantic 验证失败
        logger.error(f"❌ 骨架 Schema 验证失败: {e}")
        error_details = "\n".join([f"• {err['loc']}: {err['msg']}" for err in e.errors()])
        messages.append(AIMessage(content=f"❌ 骨架生成失败（Schema 验证错误）:\n{error_details}"))

        # 发送骨架生成失败事件
        _emit_skeleton_progress(
            ProgressEventType.SKELETON_FAILED,
            f"骨架Schema验证失败",
            progress=0.1,
            data={"error": str(e)[:100]}
        )

        return {
            "skill_skeleton": {},
            "track_plan": [],
            "skeleton_validation_errors": [f"Schema 验证失败: {str(e)}"],
            "current_track_index": 0,
            "generated_tracks": [],
            "track_retry_count": 0,
            "messages": messages
        }

    except Exception as e:
        # 其他错误
        logger.error(f"❌ 骨架生成异常: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ 骨架生成失败: {str(e)}"))

        # 发送骨架生成失败事件
        _emit_skeleton_progress(
            ProgressEventType.SKELETON_FAILED,
            f"骨架生成异常: {str(e)[:50]}",
            progress=0.1,
            data={"error": str(e)[:100]}
        )

        return {
            "skill_skeleton": {},
            "track_plan": [],
            "skeleton_validation_errors": [f"生成异常: {str(e)}"],
            "current_track_index": 0,
            "generated_tracks": [],
            "track_retry_count": 0,
            "messages": messages
        }


# ==================== 辅助函数 ====================

def format_similar_skills(skills: List[Dict[str, Any]]) -> str:
    """格式化相似技能用于 prompt"""
    if not skills:
        return "无参考技能"

    formatted = []
    for i, skill in enumerate(skills[:3]):
        skill_name = skill.get("skill_name", "Unknown")
        skill_data = skill.get("skill_data", {})

        # 提取 track 结构
        tracks = skill_data.get("tracks", [])
        track_info = []
        for track in tracks[:5]:
            track_name = track.get("trackName", "?")
            actions_count = len(track.get("actions", []))
            track_info.append(f"{track_name} ({actions_count} actions)")

        formatted.append(
            f"参考技能 {i+1}: {skill_name}\n"
            f"  - Tracks: {', '.join(track_info) if track_info else '无'}\n"
            f"  - 总时长: {skill_data.get('totalDuration', '?')} 帧"
        )

    return "\n\n".join(formatted)


# ==================== 骨架修复节点 ====================

def skeleton_fixer_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    骨架修复节点
    
    职责：根据验证错误修复骨架数据
    
    输出：
    - skill_skeleton: 修复后的骨架数据
    - skeleton_validation_errors: 清空（由验证节点重新填充）
    - skeleton_retry_count: 递增重试计数
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown
    
    skeleton = state.get("skill_skeleton", {})
    errors = state.get("skeleton_validation_errors", [])
    requirement = state.get("requirement", "")
    
    logger.info(f"🔧 修复骨架，错误数: {len(errors)}")
    
    # 格式化错误信息
    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])
    
    # 准备消息列表
    messages = []
    messages.append(AIMessage(
        content=f"🔧 骨架验证发现 {len(errors)} 个错误，正在修复...\n{errors_text}"
    ))
    
    # 获取 Prompt（复用修复逻辑）
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skeleton_validation_fix")
    
    # 调用 LLM
    llm = get_llm(temperature=0.3)  # 修复时使用更低温度
    
    try:
        fixer_llm = llm.with_structured_output(
            SkillSkeletonSchema,
            method="json_mode",
            include_raw=False
        )
        logger.info("✅ Skeleton fixer 使用 structured output 模式")
    except Exception as e:
        logger.warning(f"⚠️ Fixer structured output 不可用: {e}")
        fixer_llm = llm
    
    chain = prompt | fixer_llm
    
    try:
        response = chain.invoke({
            "errors": errors_text,
            "skeleton_json": json.dumps(skeleton, ensure_ascii=False, indent=2),
            "requirement": requirement
        })
        
        # 处理响应
        if isinstance(response, SkillSkeletonSchema):
            fixed_skeleton_dict = response.model_dump()
            logger.info("✅ 骨架修复成功 (structured output)")
        else:
            payload_text = _prepare_payload_text(response)
            json_content = extract_json_from_markdown(payload_text)
            fixed_skeleton_dict = json.loads(json_content)
            validated = SkillSkeletonSchema.model_validate(fixed_skeleton_dict)
            fixed_skeleton_dict = validated.model_dump()
            logger.info("✅ 骨架修复成功（手动解析）")
        
        # 重新验证
        new_errors = validate_skeleton(fixed_skeleton_dict)
        
        messages.append(AIMessage(content="✅ 骨架已修复，重新验证中..."))
        
        return {
            "skill_skeleton": fixed_skeleton_dict,
            "track_plan": fixed_skeleton_dict.get("trackPlan", []),
            "skeleton_validation_errors": new_errors,
            "skeleton_retry_count": state.get("skeleton_retry_count", 0) + 1,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"❌ 骨架修复失败: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ 骨架修复失败: {str(e)}"))
        
        # 修复失败时，保留原有错误并添加修复失败信息
        original_errors = state.get("skeleton_validation_errors", [])
        updated_errors = original_errors + [f"修复失败: {str(e)}"]
        
        return {
            "skeleton_validation_errors": updated_errors,
            "skeleton_retry_count": state.get("skeleton_retry_count", 0) + 1,
            "messages": messages
        }


# ==================== 条件判断函数 ====================

def should_continue_to_track_generation(state: ProgressiveSkillGenerationState) -> Literal["generate_tracks", "fix_skeleton", "skeleton_failed"]:
    """
    判断是否继续进入 Track 生成阶段

    条件：
    - 骨架验证无错误 → "generate_tracks"
    - 骨架验证有错误且未达重试上限 → "fix_skeleton"
    - 骨架验证有错误且达到上限 → "skeleton_failed"
    """
    errors = state.get("skeleton_validation_errors", [])
    retry_count = state.get("skeleton_retry_count", 0)
    max_retries = state.get("max_skeleton_retries", 2)

    if not errors:
        return "generate_tracks"
    
    if retry_count < max_retries:
        logger.info(f"骨架需要修复 (重试 {retry_count + 1}/{max_retries})")
        return "fix_skeleton"
    else:
        logger.warning(f"骨架达到最大重试次数 ({max_retries})，生成失败")
        return "skeleton_failed"


# ==================== Track 类型识别 ====================

# Track类型关键词映射（支持中英文，增强版）
TRACK_TYPE_KEYWORDS = {
    "animation": [
        "animation", "anim", "animator", 
        "动画", "動畫", "动作", "動作"
    ],
    "effect": [
        "effect", "fx", "vfx", "visual", "particle",
        "特效", "效果", "伤害", "傷害", "damage", "buff", "debuff",
        "技能效果", "攻击效果", "攻擊效果"
    ],
    "audio": [
        "audio", "sound", "sfx", "music",
        "音效", "音频", "音頻", "声音", "聲音", "音乐", "音樂"
    ],
    "movement": [
        "movement", "move", "position", "translate", "dash", "teleport",
        "移动", "移動", "位移", "冲刺", "衝刺", "传送", "傳送", "位置"
    ],
    "camera": [
        "camera", "cam", "shake", "zoom", "focus",
        "镜头", "鏡頭", "相机", "相機", "震动", "震動", "震屏"
    ],
}


def infer_track_type(track_name: str) -> str:
    """
    根据 track 名称推断类型（支持中英文）

    Args:
        track_name: Track 名称（如 "Animation Track", "动画轨道"）

    Returns:
        Track 类型：animation | effect | audio | movement | camera | other
    """
    track_name_lower = track_name.lower()

    for track_type, keywords in TRACK_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in track_name_lower:
                return track_type

    return "other"


def search_actions_by_track_type(
    track_type: str,
    purpose: str,
    top_k: int = 5,
    suggested_types: Optional[List[str]] = None,
    used_types: Optional[List[str]] = None,
    batch_context: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    根据 track 类型和用途检索相关 Actions（增强版：支持语义上下文）

    策略：
    1. 基于 track_type 过滤 Action 类别
    2. 优先检索 suggested_types 指定的Action类型
    3. 结合 purpose 和 batch_context 进行语义检索
    4. 降权已使用的 used_types（避免重复推荐同类型）
    5. 返回最相关的 top_k 个

    Args:
        track_type: Track 类型（animation/effect/audio/movement/camera/other）
        purpose: Track 用途描述
        top_k: 返回的最大 Action 数量
        suggested_types: 建议使用的Action类型列表（来自语义上下文）
        used_types: 已使用的Action类型列表（避免重复）
        batch_context: 批次上下文描述

    Returns:
        Action 定义列表（按相关性排序）
    """
    from ..tools.rag_tools import search_actions

    # Track 类型 → Action 类别映射
    type_to_category_map = {
        "animation": ["Animation"],
        "effect": ["Effect", "Damage", "Buff", "Debuff", "Spawn", "Heal", "Shield"],
        "audio": ["Audio", "Sound"],
        "movement": ["Movement", "Dash", "Teleport"],
        "camera": ["Camera"],
        "other": []  # 不过滤
    }

    categories = type_to_category_map.get(track_type, [])
    all_results = []

    # 策略1：优先检索建议的Action类型
    if suggested_types:
        for suggested_type in suggested_types[:3]:  # 最多检索3种建议类型
            try:
                query = f"{suggested_type} {purpose[:30]}"
                results = search_actions.invoke({"query": query, "top_k": 3})
                if isinstance(results, list):
                    for r in results:
                        r["_relevance_boost"] = 2.0  # 建议类型加权
                        if r not in all_results:
                            all_results.append(r)
            except Exception as e:
                logger.warning(f"⚠️ 检索建议类型 {suggested_type} 失败: {e}")

    # 策略2：结合purpose和batch_context构建查询
    if batch_context:
        combined_query = f"{track_type} {batch_context} {purpose[:50]}"
    else:
        combined_query = f"{track_type} {purpose}"

    logger.info(f"🔍 检索 {track_type} track: query=\"{combined_query[:60]}...\"")

    try:
        # 主查询
        results = search_actions.invoke({"query": combined_query, "top_k": top_k * 2})

        if isinstance(results, list):
            for r in results:
                if r not in all_results:
                    r["_relevance_boost"] = 1.0
                    all_results.append(r)

    except Exception as e:
        logger.error(f"❌ 主查询失败: {e}")

    # 类别过滤
    if categories:
        filtered_results = []
        for action in all_results:
            action_category = action.get("category", "")
            if any(cat.lower() in action_category.lower() for cat in categories):
                filtered_results.append(action)

        # 如果过滤后结果太少，保留部分原始结果
        if len(filtered_results) < top_k // 2 and all_results:
            logger.warning(f"⚠️ 类别过滤后只剩 {len(filtered_results)} 个，补充原始结果")
            for r in all_results:
                if r not in filtered_results and len(filtered_results) < top_k:
                    filtered_results.append(r)
        all_results = filtered_results

    # 降权已使用的类型
    if used_types:
        for action in all_results:
            action_type = action.get("typeName", "")
            if action_type in used_types:
                action["_relevance_boost"] = action.get("_relevance_boost", 1.0) * 0.5

    # 按加权相关性排序
    all_results.sort(key=lambda x: x.get("_relevance_boost", 1.0), reverse=True)

    # 清理临时字段
    for action in all_results:
        action.pop("_relevance_boost", None)

    final_results = all_results[:top_k]
    logger.info(f"✅ 检索到 {len(final_results)} 个 {track_type} 相关 Actions")

    return final_results


def validate_track(track_data: Dict[str, Any], total_duration: int) -> List[str]:
    """
    验证单个 Track 的合法性

    验证规则：
    1. trackName 非空
    2. actions 数组非空
    3. 每个 action 的 frame/duration 合法
    4. 每个 action 的 parameters 包含 _odin_type
    5. _odin_type 格式正确（TypeName, Assembly-CSharp）
    6. 所有 action 的结束帧 <= totalDuration

    Args:
        track_data: Track 数据（dict 格式）
        total_duration: 技能总时长（帧数）

    Returns:
        错误列表，空表示验证通过
    """
    from core.odin_json_parser import validate_odin_type
    
    errors = []

    # 验证1：trackName 非空
    track_name = track_data.get("trackName")
    if not track_name:
        errors.append("trackName 不能为空")
        track_name = "Unknown Track"  # 用于后续错误信息

    # 验证2：actions 数组非空
    actions = track_data.get("actions", [])
    if not actions or not isinstance(actions, list):
        errors.append(f"Track '{track_name}' 的 actions 数组为空")
        return errors  # 提前返回，后续验证依赖 actions

    # 验证3：每个 action 的合法性
    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"Track '{track_name}' 的 action[{idx}] 必须是对象")
            continue

        # 检查 frame
        frame = action.get("frame")
        if not isinstance(frame, int) or frame < 0:
            errors.append(f"Track '{track_name}' action[{idx}].frame 必须是非负整数（当前: {frame}）")

        # 检查 duration
        duration = action.get("duration")
        if not isinstance(duration, int) or duration < 1:
            errors.append(f"Track '{track_name}' action[{idx}].duration 必须是正整数（当前: {duration}）")

        # 检查时间范围
        if isinstance(frame, int) and isinstance(duration, int):
            end_frame = frame + duration
            if end_frame > total_duration:
                errors.append(
                    f"Track '{track_name}' action[{idx}] 结束帧 ({end_frame}) "
                    f"超出技能总时长 ({total_duration})"
                )

        # 检查 parameters 和 _odin_type
        parameters = action.get("parameters")
        if not parameters or not isinstance(parameters, dict):
            errors.append(f"Track '{track_name}' action[{idx}].parameters 缺失或格式错误")
        elif "_odin_type" not in parameters:
            errors.append(f"Track '{track_name}' action[{idx}].parameters 缺少 _odin_type")
        else:
            # 验证 _odin_type 格式
            odin_type = parameters.get("_odin_type", "")
            is_valid, _, error_msg = validate_odin_type(odin_type)
            if not is_valid:
                errors.append(f"Track '{track_name}' action[{idx}]: {error_msg}")

    return errors


# ==================== 阶段2：Track 生成节点 ====================

def track_action_generator_node(state: ProgressiveSkillGenerationState, writer: StreamWriter) -> Dict[str, Any]:
    """
    Track Action 生成节点（阶段2）

    职责：
    1. 为当前 track 生成具体的 actions
    2. 根据 track 类型检索相关 Action 定义
    3. 🔥 使用 OpenAI SDK 直接调用 DeepSeek API，支持 reasoning_content 流式输出
    4. 通过 writer 发送 thinking_chunk/content_chunk 自定义事件

    输出：
    - current_track_data: 当前生成的 track 数据
    - current_track_errors: 初始为空（由 validator 填充）
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown

    skeleton = state["skill_skeleton"]
    track_plan = state["track_plan"]
    current_index = state["current_track_index"]

    if current_index >= len(track_plan):
        logger.error(f"❌ current_track_index ({current_index}) 超出 track_plan 长度 ({len(track_plan)})")
        return {
            "current_track_data": {},
            "current_track_errors": ["索引越界"],
            "messages": [AIMessage(content="❌ Track 索引错误")]
        }

    current_track_plan = track_plan[current_index]
    track_name = current_track_plan.get("trackName", "Unknown Track")
    purpose = current_track_plan.get("purpose", "")
    estimated_actions = current_track_plan.get("estimatedActions", 1)

    logger.info(
        f"🎯 开始生成 Track [{current_index + 1}/{len(track_plan)}]: "
        f"{track_name} (预估 {estimated_actions} actions)"
    )

    # 发送Track生成开始事件
    _emit_track_progress(
        ProgressEventType.TRACK_STARTED,
        f"开始生成 Track: {track_name}",
        track_index=current_index,
        total_tracks=len(track_plan),
        track_name=track_name,
        data={"purpose": purpose[:50], "estimated_actions": estimated_actions}
    )

    # 准备消息列表
    messages = []
    messages.append(AIMessage(
        content=f"🎯 **阶段2/3**: 正在生成 Track [{current_index + 1}/{len(track_plan)}] - **{track_name}**\n"
                f"用途: {purpose}"
    ))

    # RAG 检索：根据 trackName 和 purpose 检索相关 Actions
    track_type = infer_track_type(track_name)
    used_action_types = state.get("used_action_types", [])
    
    relevant_actions = search_actions_by_track_type(
        track_type=track_type,
        purpose=purpose,
        top_k=5,
        used_types=used_action_types
    )

    # RAG 检索容错：无结果时使用默认模板
    if not relevant_actions:
        logger.warning(f"⚠️ RAG 检索无结果，使用 {track_type} 类型默认模板")
        relevant_actions = get_default_actions_for_track_type(track_type)
        messages.append(AIMessage(
            content=f"⚠️ 未检索到相关 Action，使用 {track_type} 类型默认模板生成"
        ))
    else:
        messages.append(AIMessage(
            content=f"📋 检索到 {len(relevant_actions)} 个相关 Action 定义用于生成"
        ))

    # 格式化 Action Schema
    action_schemas_text = format_action_schemas_for_prompt(relevant_actions)

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("track_action_generation")

    # 🔥 使用 OpenAI SDK 进行流式调用
    api_start_time = time.time()
    first_chunk_time = None
    logger.info(f"⏳ 正在为 '{track_name}' 生成 actions（OpenAI SDK 流式）...")

    # 🔥 生成唯一的 message_id 用于跟踪流式消息
    thinking_message_id = f"track_{current_index}_thinking_{api_start_time}"
    content_message_id = f"track_{current_index}_content_{api_start_time}"

    # 收集流式输出
    full_reasoning = ""
    full_content = ""

    try:
        # 🔥 使用 OpenAI SDK 直接调用 DeepSeek API
        client = get_openai_client()

        # 渲染 prompt 模板
        prompt_inputs = {
            "skillName": skeleton.get("skillName", "Unknown"),
            "totalDuration": skeleton.get("totalDuration", 150),
            "trackName": track_name,
            "purpose": purpose,
            "estimatedActions": estimated_actions,
            "relevant_actions": action_schemas_text or "无特定 Action 参考"
        }
        prompt_value = prompt.invoke(prompt_inputs)

        # 转换为 OpenAI 格式的 messages
        openai_messages = []
        for msg in prompt_value.to_messages():
            msg_type = msg.__class__.__name__.lower()
            if "system" in msg_type:
                openai_messages.append({"role": "system", "content": msg.content})
            elif "human" in msg_type:
                openai_messages.append({"role": "user", "content": msg.content})
            elif "ai" in msg_type:
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                openai_messages.append({"role": "user", "content": msg.content})

        logger.info(f"📤 发送请求到 DeepSeek API，消息数: {len(openai_messages)}")

        # 🔥 发送初始思考提示
        if writer:
            try:
                writer({
                    "type": "thinking_chunk",
                    "message_id": thinking_message_id,
                    "chunk": f"🤔 正在思考 Track '{track_name}' 的 actions 结构...\n"
                })
            except Exception as e:
                logger.warning(f"⚠️ 发送初始 thinking chunk 失败: {e}")

        # 🔥 使用 OpenAI SDK 进行流式调用
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=openai_messages,
            stream=True
        )

        # 流式处理响应
        for chunk in response:
            # 记录首字节时间（TTFB）
            if first_chunk_time is None:
                first_chunk_time = time.time()
                ttfb = first_chunk_time - api_start_time
                logger.info(f"⚡ Track '{track_name}' 首字节延迟 (TTFB): {ttfb:.2f}s")

            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # 提取 reasoning_content（思考过程）
            reasoning_chunk = getattr(delta, 'reasoning_content', None)
            if reasoning_chunk:
                full_reasoning += reasoning_chunk
                # 降低日志频率
                if len(full_reasoning) % 500 < len(reasoning_chunk):
                    logger.debug(f"📝 Track reasoning progress: {len(full_reasoning)} chars")

                # 🔥 使用 writer 实时推送 thinking chunk
                if writer:
                    try:
                        writer({
                            "type": "thinking_chunk",
                            "message_id": thinking_message_id,
                            "chunk": reasoning_chunk
                        })
                    except Exception as e:
                        logger.debug(f"发送 thinking chunk 失败: {e}")

            # 提取 content（最终输出）
            content_chunk = getattr(delta, 'content', None)
            if content_chunk:
                full_content += content_chunk
                # 降低日志频率
                if len(full_content) % 200 < len(content_chunk):
                    logger.debug(f"📝 Track content progress: {len(full_content)} chars")

                # 🔥 使用 writer 实时推送 content chunk
                if writer:
                    try:
                        writer({
                            "type": "content_chunk",
                            "message_id": content_message_id,
                            "chunk": content_chunk
                        })
                    except Exception as e:
                        logger.debug(f"发送 content chunk 失败: {e}")

        api_elapsed = time.time() - api_start_time
        logger.info(f"⏱️ Track '{track_name}' 生成耗时: {api_elapsed:.2f}s")
        logger.info(f"🧠 思考内容长度: {len(full_reasoning)} 字符")
        logger.info(f"📝 输出内容长度: {len(full_content)} 字符")

        # 解析 JSON 响应
        json_content = extract_json_from_markdown(full_content)
        track_dict = json.loads(json_content)

        # 使用 Pydantic 验证
        validated = SkillTrack.model_validate(track_dict)
        track_dict = validated.model_dump()
        logger.info(f"✅ Track 生成成功: {len(track_dict.get('actions', []))} actions")

        # 确保 trackName 正确
        if track_dict.get("trackName") != track_name:
            logger.warning(f"⚠️ LLM 返回的 trackName 不一致，强制修正为 '{track_name}'")
            track_dict["trackName"] = track_name

        messages.append(AIMessage(
            content=f"✅ Track 生成完成：{len(track_dict.get('actions', []))} 个 actions"
        ))

        # 🔥 添加思考过程消息（如果有）
        if full_reasoning:
            messages.append(AIMessage(
                content=full_reasoning,
                additional_kwargs={"thinking": True},
                id=thinking_message_id
            ))

        # 发送Track生成完成事件（注意：这里只是LLM生成完成，还需要验证）
        _emit_track_progress(
            ProgressEventType.LLM_COMPLETED,
            f"Track {track_name} LLM生成完成，待验证",
            track_index=current_index,
            total_tracks=len(track_plan),
            track_name=track_name,
            data={"actions_count": len(track_dict.get('actions', []))}
        )

        return {
            "current_track_data": track_dict,
            "current_track_errors": [],  # 初始为空，由 validator 填充
            "messages": messages
        }

    except ValidationError as e:
        # Pydantic 验证失败
        logger.error(f"❌ Track Schema 验证失败: {e}")
        error_details = "\n".join([f"• {err['loc']}: {err['msg']}" for err in e.errors()])
        messages.append(AIMessage(content=f"❌ Track 生成失败（Schema 验证错误）:\n{error_details}"))

        # 发送Track生成失败事件
        _emit_track_progress(
            ProgressEventType.TRACK_FAILED,
            f"Track {track_name} Schema验证失败",
            track_index=current_index,
            total_tracks=len(track_plan),
            track_name=track_name,
            data={"error": str(e)[:100]}
        )

        return {
            "current_track_data": {},
            "current_track_errors": [f"Schema 验证失败: {str(e)}"],
            "messages": messages
        }

    except Exception as e:
        # 其他错误
        logger.error(f"❌ Track 生成异常: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ Track 生成失败: {str(e)}"))

        # 发送Track生成失败事件
        _emit_track_progress(
            ProgressEventType.TRACK_FAILED,
            f"Track {track_name} 生成异常",
            track_index=current_index,
            total_tracks=len(track_plan),
            track_name=track_name,
            data={"error": str(e)[:100]}
        )

        return {
            "current_track_data": {},
            "current_track_errors": [f"生成异常: {str(e)}"],
            "messages": messages
        }


def track_validator_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    Track 验证节点

    职责：验证当前生成的 track 是否符合规范

    输出：
    - current_track_errors: 更新验证错误列表
    """
    track_data = state.get("current_track_data", {})
    total_duration = state["skill_skeleton"].get("totalDuration", 150)

    logger.info("🔍 验证当前 Track...")

    # 准备消息列表
    messages = []

    # 验证
    errors = validate_track(track_data, total_duration)

    if errors:
        logger.warning(f"⚠️ Track 验证发现 {len(errors)} 个错误")
        errors_list = "\n".join([f"• {err}" for err in errors])
        messages.append(AIMessage(
            content=f"⚠️ Track 验证失败，发现 {len(errors)} 个问题:\n{errors_list}"
        ))
    else:
        track_name = track_data.get("trackName", "Unknown")
        actions_count = len(track_data.get("actions", []))
        logger.info(f"✅ Track '{track_name}' 验证通过")
        messages.append(AIMessage(
            content=f"✅ Track 验证通过！（{actions_count} actions）"
        ))

    return {
        "current_track_errors": errors,
        "messages": messages
    }


def track_fixer_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    Track 修复节点

    职责：根据验证错误修复当前 track

    输出：
    - current_track_data: 修复后的 track 数据
    - track_retry_count: 递增重试计数
    """
    from ..prompts.prompt_manager import get_prompt_manager
    from .json_utils import extract_json_from_markdown

    track_data = state.get("current_track_data", {})
    errors = state.get("current_track_errors", [])
    skeleton = state["skill_skeleton"]

    logger.info(f"🔧 修复 Track，错误数: {len(errors)}")

    # 格式化错误信息
    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])

    # 准备消息列表
    messages = []
    messages.append(AIMessage(
        content=f"🔧 发现 {len(errors)} 个错误，正在修复...\n{errors_text}"
    ))

    # 获取 Prompt（复用 validation_fix，针对单个 track）
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("track_validation_fix")

    # 调用 LLM
    llm = get_llm(temperature=0.3)  # 修复时使用更低温度

    try:
        fixer_llm = llm.with_structured_output(
            SkillTrack,
            method="json_mode",
            include_raw=False
        )
        logger.info("✅ Track fixer 使用 structured output 模式")
    except Exception as e:
        logger.warning(f"⚠️ Fixer structured output 不可用: {e}")
        fixer_llm = llm

    chain = prompt | fixer_llm

    try:
        response = chain.invoke({
            "errors": errors_text,
            "track_json": json.dumps(track_data, ensure_ascii=False, indent=2),
            "total_duration": skeleton.get("totalDuration", 150)
        })

        # 处理响应
        if isinstance(response, SkillTrack):
            fixed_track_dict = response.model_dump()
            logger.info("✅ Track 修复成功 (structured output)")
        else:
            payload_text = _prepare_payload_text(response)
            json_content = extract_json_from_markdown(payload_text)
            fixed_track_dict = json.loads(json_content)
            validated = SkillTrack.model_validate(fixed_track_dict)
            fixed_track_dict = validated.model_dump()
            logger.info("✅ Track 修复成功（手动解析）")

        messages.append(AIMessage(content="✅ Track 已修复，重新验证中..."))

        return {
            "current_track_data": fixed_track_dict,
            "track_retry_count": state.get("track_retry_count", 0) + 1,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"❌ Track 修复失败: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ Track 修复失败: {str(e)}"))

        return {
            "track_retry_count": state.get("track_retry_count", 0) + 1,
            "messages": messages
        }


def track_saver_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    Track 保存节点

    职责：保存验证通过的 track，并移动到下一个 track

    输出：
    - generated_tracks: 追加当前 track（跳过空 track）
    - current_track_index: 递增索引
    - track_retry_count: 重置为 0
    - used_action_types: 更新已使用的 Action 类型
    """
    from core.odin_json_parser import extract_type_name_from_odin_type
    
    track_data = state.get("current_track_data", {})
    generated_tracks = list(state.get("generated_tracks", []))  # 创建副本避免修改原列表
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])
    used_action_types = list(state.get("used_action_types", []))

    track_name = track_data.get("trackName", "Unknown")
    actions = track_data.get("actions", [])
    actions_count = len(actions)

    # 准备消息
    messages = []
    
    # 检查是否为空 Track（跳过保存）
    if not track_data or not actions:
        logger.warning(f"⚠️ 跳过空 Track '{track_name}'（无有效 actions）")
        messages.append(AIMessage(
            content=f"⚠️ Track '{track_name}' 为空或无效，已跳过"
        ))
        return {
            "generated_tracks": generated_tracks,  # 不追加
            "current_track_index": current_index + 1,
            "track_retry_count": 0,
            "used_action_types": used_action_types,
            "messages": messages
        }

    logger.info(f"💾 保存 Track '{track_name}' ({actions_count} actions)")

    # 保存有效 Track
    generated_tracks.append(track_data)
    
    # 收集已使用的 Action 类型（用于后续 Track 避免重复）
    # 使用 set 提高查找效率
    used_types_set = set(used_action_types)
    for action in actions:
        params = action.get("parameters", {})
        odin_type = params.get("_odin_type", "")
        if odin_type:
            type_name = extract_type_name_from_odin_type(odin_type)
            if type_name:
                used_types_set.add(type_name)
    used_action_types = list(used_types_set)

    progress = f"[{len(generated_tracks)}/{len(track_plan)}]"
    messages.append(AIMessage(
        content=f"💾 Track '{track_name}' 已保存 {progress}"
    ))

    # 发送Track完成事件
    _emit_track_progress(
        ProgressEventType.TRACK_COMPLETED,
        f"Track {track_name} 已保存 {progress}",
        track_index=current_index,
        total_tracks=len(track_plan),
        track_name=track_name,
        data={"actions_count": actions_count, "saved_tracks": len(generated_tracks)}
    )

    return {
        "generated_tracks": generated_tracks,
        "current_track_index": current_index + 1,
        "track_retry_count": 0,  # 重置重试计数
        "used_action_types": used_action_types,
        "messages": messages
    }


# ==================== 辅助函数 ====================

def format_action_schemas_for_prompt(actions: List[Dict[str, Any]]) -> str:
    """格式化 Action Schema 用于 prompt"""
    if not actions:
        return "无特定 Action 参考"

    formatted = []
    for action in actions[:5]:  # 最多5个
        action_name = action.get("action_name", "Unknown")
        action_type = action.get("action_type", "N/A")
        description = action.get("description", "")[:150]  # 限制长度
        parameters = action.get("parameters", [])

        # 格式化参数
        params_info = []
        for param in parameters[:8]:  # 最多显示8个参数
            param_name = param.get("name", "unknown")
            param_type = param.get("type", "unknown")
            default_val = param.get("defaultValue", "")

            param_info = f"  - {param_name}: {param_type}"
            if default_val:
                param_info += f" = {default_val}"
            params_info.append(param_info)

        params_text = "\n".join(params_info) if params_info else "  无参数"

        formatted.append(
            f"**{action_name}** ({action_type})\n"
            f"描述: {description}\n"
            f"参数:\n{params_text}"
        )

    return "\n\n".join(formatted)


# ==================== 条件判断函数 ====================

def should_fix_track(state: ProgressiveSkillGenerationState) -> str:
    """
    判断是否需要修复 track

    条件：
    - 无错误 → "save"
    - 有错误且未达重试上限 → "fix"
    - 有错误且达到上限 → "skip"
    """
    errors = state.get("current_track_errors", [])
    retry_count = state.get("track_retry_count", 0)
    max_retries = state.get("max_track_retries", 3)

    if not errors:
        return "save"

    if retry_count < max_retries:
        logger.info(f"Track 需要修复 (重试 {retry_count + 1}/{max_retries})")
        return "fix"
    else:
        logger.warning(f"Track 达到最大重试次数 ({max_retries})，跳过")
        return "skip"


def should_continue_tracks(state: ProgressiveSkillGenerationState) -> str:
    """
    判断是否继续生成下一个 track

    条件：
    - 还有未生成的 track → "continue"
    - 所有 track 已生成 → "assemble"
    """
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])

    if current_index < len(track_plan):
        logger.info(f"继续生成下一个 Track ({current_index + 1}/{len(track_plan)})")
        return "continue"
    else:
        logger.info(f"所有 {len(track_plan)} 个 Tracks 已生成，进入组装阶段")
        return "assemble"


# ==================== 阶段3：技能组装节点 ====================

# 时间线验证配置常量
TIMELINE_VALIDATION_CONFIG = {
    "audio_sync_tolerance": 15,      # 动画和音效同步容差（帧）
    "max_timeline_gap": 60,          # 时间轴最大空白警告阈值（帧）
    "damage_after_visual_delay": 5,  # 伤害在视觉效果后的延迟（帧）
    "effect_after_anim_delay": 3,    # 特效在动画后的延迟（帧）
}


def validate_cross_track_timeline(
    tracks: List[Dict[str, Any]], 
    config: Optional[Dict[str, int]] = None
) -> Tuple[List[str], List[str]]:
    """
    验证跨Track时间同步

    检查不同Track间的时间协调性，确保：
    1. 动画和音效在相近帧触发
    2. 伤害Action在动画/特效之后
    3. 效果Track不早于动画Track开始

    Args:
        tracks: 已生成的Track列表
        config: 可选的验证配置，覆盖默认值

    Returns:
        (errors, warnings) 元组
    """
    # 合并配置
    cfg = {**TIMELINE_VALIDATION_CONFIG, **(config or {})}
    audio_sync_tolerance = cfg["audio_sync_tolerance"]
    max_timeline_gap = cfg["max_timeline_gap"]
    
    errors = []
    warnings = []

    # 收集各类型Track的帧信息
    animation_frames: List[int] = []  # 动画开始帧
    audio_frames: List[int] = []       # 音效开始帧
    damage_frames: List[int] = []      # 伤害开始帧
    effect_frames: List[int] = []      # 特效开始帧

    track_start_frames: Dict[str, int] = {}  # Track类型 -> 最早开始帧

    for track in tracks:
        track_name = track.get("trackName", "")
        actions = track.get("actions", [])

        if not actions:
            continue

        # 使用增强的Track类型识别（支持中英文）
        track_type = infer_track_type(track_name)

        # 记录Track最早开始帧
        min_frame = min(a.get("frame", 999) for a in actions)

        if track_type == "animation":
            track_start_frames["animation"] = min(
                track_start_frames.get("animation", 999), min_frame
            )
            for action in actions:
                animation_frames.append(action.get("frame", 0))

        elif track_type == "audio":
            track_start_frames["audio"] = min(
                track_start_frames.get("audio", 999), min_frame
            )
            for action in actions:
                audio_frames.append(action.get("frame", 0))

        elif track_type == "effect":
            track_start_frames["effect"] = min(
                track_start_frames.get("effect", 999), min_frame
            )
            for action in actions:
                params = action.get("parameters", {})
                odin_type = params.get("_odin_type", "")

                if "Damage" in odin_type:
                    damage_frames.append(action.get("frame", 0))
                elif "Effect" in odin_type or "Spawn" in odin_type:
                    effect_frames.append(action.get("frame", 0))

    # === 验证1：动画和音效时间同步 ===
    if animation_frames and audio_frames:
        for anim_frame in animation_frames[:3]:  # 检查前3个动画帧
            has_nearby_audio = any(
                abs(anim_frame - audio_frame) <= audio_sync_tolerance
                for audio_frame in audio_frames
            )
            if not has_nearby_audio:
                warnings.append(
                    f"动画帧{anim_frame}附近缺少配套音效（±{audio_sync_tolerance}帧内）"
                )

    # === 验证2：伤害应在动画/特效之后 ===
    if damage_frames and (animation_frames or effect_frames):
        earliest_visual = min(
            animation_frames + effect_frames if animation_frames or effect_frames else [0]
        )
        for damage_frame in damage_frames:
            if damage_frame < earliest_visual:
                warnings.append(
                    f"伤害(帧{damage_frame})出现在动画/特效(帧{earliest_visual})之前"
                )

    # === 验证3：效果Track不应早于动画Track ===
    anim_start = track_start_frames.get("animation", 0)
    effect_start = track_start_frames.get("effect", 999)

    if effect_start < anim_start and anim_start != 999:
        warnings.append(
            f"效果Track(帧{effect_start})早于动画Track(帧{anim_start})开始"
        )

    # === 验证4：检查时间轴空白（可选，仅警告） ===
    all_frames = animation_frames + audio_frames + damage_frames + effect_frames
    if all_frames:
        all_frames.sort()
        max_gap = 0
        for i in range(1, len(all_frames)):
            gap = all_frames[i] - all_frames[i-1]
            if gap > max_gap:
                max_gap = gap

        if max_gap > max_timeline_gap:
            warnings.append(
                f"时间轴存在较大空白（最大间隔{max_gap}帧），可能影响技能连贯性"
            )

    return errors, warnings


def auto_fix_timeline_issues(
    tracks: List[Dict[str, Any]], 
    config: Optional[Dict[str, int]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    自动修复跨Track时间线问题
    
    修复策略：
    1. 伤害Action早于动画 → 将伤害帧后移至动画帧+延迟
    2. 效果Track早于动画Track → 将效果Track的起始帧后移
    
    Args:
        tracks: 已生成的Track列表
        config: 可选的修复配置，覆盖默认值
        
    Returns:
        (修复后的tracks, 修复日志列表)
    """
    import copy
    
    # 合并配置
    cfg = {**TIMELINE_VALIDATION_CONFIG, **(config or {})}
    damage_delay = cfg["damage_after_visual_delay"]
    effect_delay = cfg["effect_after_anim_delay"]
    
    fixed_tracks = copy.deepcopy(tracks)
    fix_logs = []
    
    # 收集动画帧信息
    animation_min_frame = 999
    for track in fixed_tracks:
        track_type = infer_track_type(track.get("trackName", ""))
        if track_type == "animation":
            for action in track.get("actions", []):
                frame = action.get("frame", 999)
                if frame < animation_min_frame:
                    animation_min_frame = frame
    
    if animation_min_frame == 999:
        animation_min_frame = 0  # 没有动画Track时使用0
    
    # 遍历修复
    for track in fixed_tracks:
        track_name = track.get("trackName", "")
        track_type = infer_track_type(track_name)
        actions = track.get("actions", [])
        
        for action in actions:
            frame = action.get("frame", 0)
            params = action.get("parameters", {})
            odin_type = params.get("_odin_type", "")
            
            # 修复1：伤害Action早于动画
            if "Damage" in odin_type and frame < animation_min_frame:
                new_frame = animation_min_frame + damage_delay
                fix_logs.append(
                    f"修复: {track_name} 伤害帧 {frame} → {new_frame}（动画后触发）"
                )
                action["frame"] = new_frame
            
            # 修复2：效果Track早于动画Track
            elif track_type == "effect" and frame < animation_min_frame:
                # 只修复特效生成类（不修复伤害，上面已处理）
                if "Effect" in odin_type or "Spawn" in odin_type:
                    new_frame = animation_min_frame + effect_delay
                    fix_logs.append(
                        f"修复: {track_name} 特效帧 {frame} → {new_frame}（与动画同步）"
                    )
                    action["frame"] = new_frame
    
    return fixed_tracks, fix_logs


def validate_complete_skill(skill_data: Dict[str, Any]) -> List[str]:
    """
    验证完整技能的合法性

    验证规则：
    1. 基本字段非空（skillName, skillId, totalDuration）
    2. 至少有一个 track
    3. 所有 track 的最大结束帧 <= totalDuration
    4. 必须有 Animation Track（可配置为可选）
    5. 各 track 的时间轴逻辑合理

    Args:
        skill_data: 完整技能数据（dict 格式）

    Returns:
        错误列表，空表示验证通过
    """
    errors = []

    # 验证1：基本字段
    if not skill_data.get("skillName"):
        errors.append("skillName 不能为空")

    if not skill_data.get("skillId"):
        errors.append("skillId 不能为空")

    total_duration = skill_data.get("totalDuration", 0)
    if not isinstance(total_duration, int) or total_duration < 30:
        errors.append(f"totalDuration ({total_duration}) 必须是 >= 30 的整数")

    # 验证2：至少有一个 track
    tracks = skill_data.get("tracks", [])
    if not tracks:
        errors.append("tracks 不能为空，至少需要一个轨道")
        return errors  # 提前返回

    # 验证3：检查所有 action 的时间范围
    max_end_frame = 0
    for track in tracks:
        track_name = track.get("trackName", "Unknown")
        actions = track.get("actions", [])

        for idx, action in enumerate(actions):
            frame = action.get("frame", 0)
            duration = action.get("duration", 0)
            end_frame = frame + duration

            if end_frame > max_end_frame:
                max_end_frame = end_frame

            if end_frame > total_duration:
                errors.append(
                    f"Track '{track_name}' action[{idx}] 结束帧 ({end_frame}) "
                    f"超出技能总时长 ({total_duration})"
                )

    # 验证4：检查是否有 Animation Track（可选验证）
    has_animation_track = any(
        "animation" in track.get("trackName", "").lower()
        for track in tracks
    )
    if not has_animation_track:
        # 这只是警告，不作为错误
        logger.warning("⚠️ 技能没有 Animation Track，可能缺少动画表现")

    return errors


def skill_assembler_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    技能组装节点（阶段3）

    职责：
    1. 将骨架和所有生成的 tracks 组装成完整技能
    2. 自动修复跨Track时间线问题
    3. 进行整体验证
    4. 输出符合 OdinSkillSchema 格式的技能数据

    输出：
    - assembled_skill: 组装后的完整技能
    - final_validation_errors: 最终验证错误
    """
    skeleton = state.get("skill_skeleton", {})
    tracks = state.get("generated_tracks", [])

    logger.info(f"🔧 开始组装技能: {skeleton.get('skillName', 'Unknown')}")
    logger.info(f"   - 骨架信息: totalDuration={skeleton.get('totalDuration')}, frameRate={skeleton.get('frameRate')}")
    logger.info(f"   - 已生成 {len(tracks)} 个 Tracks")

    # 准备消息列表
    messages = []
    messages.append(AIMessage(
        content=f"🔧 **阶段3/3**: 正在组装完整技能...\n"
                f"共 {len(tracks)} 个轨道待组装"
    ))

    # 跨Track时间线自动修复
    fixed_tracks, fix_logs = auto_fix_timeline_issues(tracks)
    if fix_logs:
        logger.info(f"🔧 自动修复了 {len(fix_logs)} 个时间线问题")
        for log in fix_logs:
            logger.info(f"   - {log}")
        messages.append(AIMessage(
            content=f"🔧 自动修复了 {len(fix_logs)} 个时间线问题:\n" +
                    "\n".join([f"• {log}" for log in fix_logs])
        ))
    
    # 使用修复后的 tracks
    tracks = fixed_tracks

    # 组装完整技能
    assembled_skill = {
        "skillName": skeleton.get("skillName", "Unnamed Skill"),
        "skillId": skeleton.get("skillId", "unknown-skill-001"),
        "skillDescription": skeleton.get("skillDescription", ""),
        "totalDuration": skeleton.get("totalDuration", 150),
        "frameRate": skeleton.get("frameRate", 30),
        "tracks": tracks
    }

    # 整体验证
    errors = validate_complete_skill(assembled_skill)

    # 跨Track时间同步验证（修复后再验证）
    timeline_errors, timeline_warnings = validate_cross_track_timeline(tracks)
    errors.extend(timeline_errors)

    if errors:
        logger.warning(f"⚠️ 技能组装后验证发现 {len(errors)} 个问题")
        errors_list = "\n".join([f"• {err}" for err in errors])
        messages.append(AIMessage(
            content=f"⚠️ 技能验证发现 {len(errors)} 个问题:\n{errors_list}"
        ))
    else:
        logger.info("✅ 技能组装验证通过")

        # 统计信息
        total_actions = sum(len(track.get("actions", [])) for track in tracks)
        track_summary = ", ".join([
            f"{track.get('trackName', '?')}({len(track.get('actions', []))})"
            for track in tracks
        ])

        result_msg = (
            f"✅ **技能组装完成**\n\n"
            f"**技能名称**: {assembled_skill['skillName']}\n"
            f"**技能ID**: {assembled_skill['skillId']}\n"
            f"**总时长**: {assembled_skill['totalDuration']} 帧\n"
            f"**轨道数**: {len(tracks)}\n"
            f"**总Actions**: {total_actions}\n\n"
            f"**轨道详情**: {track_summary}"
        )

        # 添加跨Track时间同步警告
        if timeline_warnings:
            warnings_text = "\n".join([f"  • {w}" for w in timeline_warnings[:5]])
            result_msg += f"\n\n⚠️ **时间同步建议**:\n{warnings_text}"
            logger.warning(f"⚠️ 跨Track时间同步有 {len(timeline_warnings)} 个建议")

        messages.append(AIMessage(content=result_msg))

    return {
        "assembled_skill": assembled_skill,
        "final_validation_errors": errors,
        "messages": messages
    }


def finalize_progressive_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    渐进式生成最终化节点 - 增强版：支持流式输出

    职责：
    1. 输出最终结果
    2. 生成摘要消息
    3. 发送生成完成/失败事件

    输出：
    - final_result: 最终技能配置（与旧版 SkillGenerationState 兼容）
    """
    assembled_skill = state.get("assembled_skill", {})
    final_errors = state.get("final_validation_errors", [])
    tracks = assembled_skill.get("tracks", [])

    logger.info(f"🏁 渐进式技能生成完成: {assembled_skill.get('skillName', 'Unknown')}")

    # 准备消息
    messages = []

    if final_errors:
        # 有错误但仍输出结果（标记为不完整）
        messages.append(AIMessage(
            content=f"[WARN] 技能生成完成，但存在 {len(final_errors)} 个验证问题\n"
                    f"建议手动检查后使用"
        ))
        is_valid = False

        # 发送生成完成事件（带警告）
        _emit_finalize_progress(
            ProgressEventType.GENERATION_COMPLETED,
            f"技能生成完成（有 {len(final_errors)} 个警告）",
            is_valid=False,
            data={
                "skill_name": assembled_skill.get("skillName"),
                "track_count": len(tracks),
                "error_count": len(final_errors)
            }
        )
    else:
        messages.append(AIMessage(
            content="[SUCCESS] **技能生成成功！**\n\n"
                    f"技能 `{assembled_skill.get('skillName')}` 已就绪，可直接导入 Unity 使用"
        ))
        is_valid = True

        # 发送生成完成事件（成功）
        total_actions = sum(len(t.get("actions", [])) for t in tracks)
        _emit_finalize_progress(
            ProgressEventType.GENERATION_COMPLETED,
            f"技能 {assembled_skill.get('skillName')} 生成成功！",
            is_valid=True,
            data={
                "skill_name": assembled_skill.get("skillName"),
                "track_count": len(tracks),
                "total_actions": total_actions,
                "total_duration": assembled_skill.get("totalDuration")
            }
        )

    # 保存最终技能 JSON 到文件
    if assembled_skill:
        filepath, is_odin_format = _save_generated_json(
            assembled_skill,
            stage="final",
            skill_name=assembled_skill.get("skillName", "unknown")
        )
        if filepath and not is_odin_format:
            messages.append(AIMessage(
                content="⚠️ 注意：Odin 序列化失败，已保存原始格式。可能需要手动转换后导入 Unity。"
            ))

    # 兼容旧版 State 的 final_result 字段
    return {
        "final_result": assembled_skill,
        "is_valid": is_valid,
        "messages": messages
    }


def should_finalize_or_fail(state: ProgressiveSkillGenerationState) -> Literal["finalize", "failed"]:
    """
    判断是否进入最终化或失败状态

    条件：
    - 无最终验证错误 → "finalize"
    - 有错误但有组装结果 → "finalize"（带警告）
    - 无组装结果 → "failed"
    """
    assembled_skill = state.get("assembled_skill", {})
    final_errors = state.get("final_validation_errors", [])

    if not assembled_skill or not assembled_skill.get("tracks"):
        logger.error("❌ 技能组装失败，无有效结果")
        return "failed"

    if final_errors:
        logger.warning(f"⚠️ 技能有 {len(final_errors)} 个验证问题，但仍输出结果")

    return "finalize"
