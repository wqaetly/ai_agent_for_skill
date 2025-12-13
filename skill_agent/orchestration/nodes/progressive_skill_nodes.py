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

from .skill_nodes import get_llm, _prepare_payload_text
from ..schemas import SkillSkeletonSchema, TrackPlanItem, SkillTrack, OdinSkillSchema
from ..streaming import (
    ProgressEventType,
    emit_progress,
)

logger = logging.getLogger(__name__)

# ==================== JSON 输出配置 ====================

# 输出目录（相对于 skill_agent 目录）
_OUTPUT_DIR = Path(__file__).parent.parent.parent / "Data" / "generated_skills"


def _save_generated_json(data: Dict[str, Any], stage: str, skill_name: str = "unknown") -> Optional[Path]:
    """
    保存生成的 JSON 数据到文件

    Args:
        data: 要保存的数据
        stage: 生成阶段 (skeleton/track/final)
        skill_name: 技能名称

    Returns:
        保存的文件路径，失败返回 None
    """
    try:
        # 确保输出目录存在
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 生成文件名：{skill_name}_{stage}_{timestamp}.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in skill_name)
        filename = f"{safe_name}_{stage}_{timestamp}.json"
        filepath = _OUTPUT_DIR / filename

        # 保存 JSON（格式化输出，支持中文）
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 已保存 {stage} JSON: {filepath}")
        return filepath

    except Exception as e:
        logger.warning(f"⚠️ 保存 JSON 失败: {e}")
        return None


# ==================== 流式输出辅助函数 ====================

def _get_writer_safe() -> Optional[Any]:
    """
    安全获取StreamWriter

    在非流式执行环境中不会报错
    """
    try:
        return get_stream_writer()
    except Exception:
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

    # === 阶段2状态 ===
    track_plan: List[Dict[str, Any]]  # Track 计划列表
    current_track_index: int  # 当前正在生成的 track 索引
    current_track_data: Dict[str, Any]  # 当前生成的 track 数据
    generated_tracks: List[Dict[str, Any]]  # 已生成并验证通过的 tracks
    current_track_errors: List[str]  # 当前 track 的验证错误
    track_retry_count: int  # 当前 track 重试次数
    max_track_retries: int  # 单个 track 最大重试次数（默认 3）

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

def skeleton_generator_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    骨架生成节点（阶段1）- 增强版：支持流式输出

    职责：
    1. 根据用户需求和相似技能，生成技能骨架和 track 计划
    2. 使用 structured output 确保输出符合 SkillSkeletonSchema
    3. 验证骨架数据
    4. 发送进度事件

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

    # 调用 LLM（使用 structured output）
    llm = get_llm(temperature=0.7)

    try:
        # 使用 with_structured_output 确保格式正确
        structured_llm = llm.with_structured_output(
            SkillSkeletonSchema,
            method="json_mode",
            include_raw=False
        )
        logger.info("✅ Skeleton generator 使用 structured output 模式")
    except Exception as e:
        logger.warning(f"⚠️ Structured output 初始化失败，使用普通模式: {e}")
        structured_llm = llm

    chain = prompt | structured_llm

    # 调用 LLM
    api_start_time = time.time()
    logger.info("⏳ 正在调用 DeepSeek API 生成骨架...")

    # 发送LLM调用事件
    _emit_skeleton_progress(
        ProgressEventType.LLM_CALLING,
        "调用LLM生成技能骨架...",
        progress=0.03
    )

    try:
        response = chain.invoke({
            "requirement": requirement,
            "similar_skills": similar_skills_text or "无参考技能"
        })

        api_elapsed = time.time() - api_start_time
        logger.info(f"⏱️ 骨架生成耗时: {api_elapsed:.2f}s")

        # 处理响应：可能是 SkillSkeletonSchema 实例或原始文本
        if isinstance(response, SkillSkeletonSchema):
            # structured output 成功
            skeleton_dict = response.model_dump()
            logger.info(f"✅ 骨架生成成功 (structured output): {response.skillName}")
        else:
            # 需要手动解析
            logger.warning("⚠️ Structured output 返回非预期类型，尝试手动解析")
            payload_text = _prepare_payload_text(response)

            # 尝试解析 JSON
            json_content = extract_json_from_markdown(payload_text)
            skeleton_dict = json.loads(json_content)

            # 使用 Pydantic 验证
            validated = SkillSkeletonSchema.model_validate(skeleton_dict)
            skeleton_dict = validated.model_dump()
            logger.info(f"✅ 骨架手动解析成功: {skeleton_dict.get('skillName')}")

        # 保存骨架 JSON 到文件
        _save_generated_json(
            skeleton_dict,
            stage="skeleton",
            skill_name=skeleton_dict.get("skillName", "unknown")
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


# ==================== 条件判断函数 ====================

def should_continue_to_track_generation(state: ProgressiveSkillGenerationState) -> Literal["generate_tracks", "skeleton_failed"]:
    """
    判断是否继续进入 Track 生成阶段

    条件：
    - 骨架验证无错误 → "generate_tracks"
    - 骨架验证有错误 → "skeleton_failed"
    """
    errors = state.get("skeleton_validation_errors", [])

    if errors:
        logger.warning(f"骨架验证失败，错误数: {len(errors)}")
        return "skeleton_failed"

    return "generate_tracks"


# ==================== Track 类型识别 ====================

# Track类型关键词映射（支持中英文）
TRACK_TYPE_KEYWORDS = {
    "animation": ["animation", "anim", "动画", "動畫"],
    "effect": ["effect", "fx", "vfx", "特效", "效果", "伤害", "傷害", "damage"],
    "audio": ["audio", "sound", "音效", "音频", "音頻", "声音", "聲音"],
    "movement": ["movement", "move", "移动", "移動", "位移", "冲刺", "衝刺"],
    "camera": ["camera", "cam", "镜头", "鏡頭", "相机", "相機"],
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
    5. 所有 action 的结束帧 <= totalDuration

    Args:
        track_data: Track 数据（dict 格式）
        total_duration: 技能总时长（帧数）

    Returns:
        错误列表，空表示验证通过
    """
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

    return errors


# ==================== 阶段2：Track 生成节点 ====================

def track_action_generator_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """
    Track Action 生成节点（阶段2）

    职责：
    1. 为当前 track 生成具体的 actions
    2. 根据 track 类型检索相关 Action 定义
    3. 使用 LLM 生成符合 SkillTrack 格式的数据

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

    # 准备消息列表
    messages = []
    messages.append(AIMessage(
        content=f"🎯 **阶段2/3**: 正在生成 Track [{current_index + 1}/{len(track_plan)}] - **{track_name}**\n"
                f"用途: {purpose}"
    ))

    # RAG 检索：根据 trackName 和 purpose 检索相关 Actions
    track_type = infer_track_type(track_name)
    relevant_actions = search_actions_by_track_type(
        track_type=track_type,
        purpose=purpose,
        top_k=5
    )

    if relevant_actions:
        messages.append(AIMessage(
            content=f"📋 检索到 {len(relevant_actions)} 个相关 Action 定义用于生成"
        ))
    else:
        messages.append(AIMessage(content="⚠️ 未检索到相关 Action，将基于通用知识生成"))

    # 格式化 Action Schema
    action_schemas_text = format_action_schemas_for_prompt(relevant_actions)

    # 获取 Prompt
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("track_action_generation")

    # 调用 LLM（使用 structured output）
    llm = get_llm(temperature=0.5)  # Track 生成使用稍低温度

    try:
        # 尝试使用 structured output（绑定 SkillTrack）
        structured_llm = llm.with_structured_output(
            SkillTrack,
            method="json_mode",
            include_raw=False
        )
        logger.info("✅ Track generator 使用 structured output 模式")
    except Exception as e:
        logger.warning(f"⚠️ Structured output 初始化失败，使用普通模式: {e}")
        structured_llm = llm

    chain = prompt | structured_llm

    # 调用 LLM
    api_start_time = time.time()
    logger.info(f"⏳ 正在为 '{track_name}' 生成 actions...")

    try:
        response = chain.invoke({
            "skillName": skeleton.get("skillName", "Unknown"),
            "totalDuration": skeleton.get("totalDuration", 150),
            "trackName": track_name,
            "purpose": purpose,
            "estimatedActions": estimated_actions,
            "relevant_actions": action_schemas_text or "无特定 Action 参考"
        })

        api_elapsed = time.time() - api_start_time
        logger.info(f"⏱️ Track 生成耗时: {api_elapsed:.2f}s")

        # 处理响应
        if isinstance(response, SkillTrack):
            # structured output 成功
            track_dict = response.model_dump()
            logger.info(f"✅ Track 生成成功 (structured output): {len(track_dict.get('actions', []))} actions")
        else:
            # 需要手动解析
            logger.warning("⚠️ Structured output 返回非预期类型，尝试手动解析")
            payload_text = _prepare_payload_text(response)
            json_content = extract_json_from_markdown(payload_text)
            track_dict = json.loads(json_content)

            # 使用 Pydantic 验证
            validated = SkillTrack.model_validate(track_dict)
            track_dict = validated.model_dump()
            logger.info(f"✅ Track 手动解析成功: {len(track_dict.get('actions', []))} actions")

        # 确保 trackName 正确
        if track_dict.get("trackName") != track_name:
            logger.warning(f"⚠️ LLM 返回的 trackName 不一致，强制修正为 '{track_name}'")
            track_dict["trackName"] = track_name

        messages.append(AIMessage(
            content=f"✅ Track 生成完成：{len(track_dict.get('actions', []))} 个 actions"
        ))

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

        return {
            "current_track_data": {},
            "current_track_errors": [f"Schema 验证失败: {str(e)}"],
            "messages": messages
        }

    except Exception as e:
        # 其他错误
        logger.error(f"❌ Track 生成异常: {e}", exc_info=True)
        messages.append(AIMessage(content=f"❌ Track 生成失败: {str(e)}"))

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
    - generated_tracks: 追加当前 track
    - current_track_index: 递增索引
    - track_retry_count: 重置为 0
    """
    track_data = state.get("current_track_data", {})
    generated_tracks = state.get("generated_tracks", [])
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])

    track_name = track_data.get("trackName", "Unknown")
    actions_count = len(track_data.get("actions", []))

    logger.info(f"💾 保存 Track '{track_name}' ({actions_count} actions)")

    # 保存
    generated_tracks.append(track_data)

    # 准备消息
    messages = []
    progress = f"[{len(generated_tracks)}/{len(track_plan)}]"
    messages.append(AIMessage(
        content=f"💾 Track '{track_name}' 已保存 {progress}"
    ))

    return {
        "generated_tracks": generated_tracks,
        "current_track_index": current_index + 1,
        "track_retry_count": 0,  # 重置重试计数
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

def validate_cross_track_timeline(tracks: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    验证跨Track时间同步

    检查不同Track间的时间协调性，确保：
    1. 动画和音效在相近帧触发
    2. 伤害Action在动画/特效之后
    3. 效果Track不早于动画Track开始

    Args:
        tracks: 已生成的Track列表

    Returns:
        (errors, warnings) 元组
    """
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
                abs(anim_frame - audio_frame) <= 15  # 允许±15帧偏差
                for audio_frame in audio_frames
            )
            if not has_nearby_audio:
                warnings.append(
                    f"动画帧{anim_frame}附近缺少配套音效（±15帧内）"
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

        if max_gap > 60:  # 超过60帧（约2秒）的空白
            warnings.append(
                f"时间轴存在较大空白（最大间隔{max_gap}帧），可能影响技能连贯性"
            )

    return errors, warnings


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
    2. 进行整体验证
    3. 输出符合 OdinSkillSchema 格式的技能数据

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

    # 跨Track时间同步验证（新增）
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
        _save_generated_json(
            assembled_skill,
            stage="final",
            skill_name=assembled_skill.get("skillName", "unknown")
        )

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
