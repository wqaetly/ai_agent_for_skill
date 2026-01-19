"""
Progressive Skill Generation Nodes (Refactored)
Three-phase generation: Skeleton -> Track-by-Track -> Assembly
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
from pydantic import ValidationError

from .base import get_llm, get_openai_client, prepare_payload_text, safe_int
from .base.streaming import (
    get_writer_safe, emit_skeleton_progress, emit_track_progress, emit_finalize_progress
)
from .json_utils import extract_json_from_markdown
from .validators import validate_skeleton, validate_track, extract_action_type_name
from .constants import infer_track_type, get_default_actions_for_track_type
from .formatters import format_similar_skills
from ..schemas import SkillSkeletonSchema, SkillTrack, OdinSkillSchema
from ..streaming import ProgressEventType
from ..config import get_skill_gen_config
from core.odin_json_parser import serialize_to_odin, odin_json_encode

logger = logging.getLogger(__name__)

# Output directory
_OUTPUT_DIR = Path(__file__).parent.parent.parent / "Data" / "generated_skills"


# ==================== State Definition ====================

class ProgressiveSkillGenerationState(TypedDict):
    """Progressive skill generation state"""
    # Input
    requirement: str
    similar_skills: List[Dict[str, Any]]
    
    # Phase 1: Skeleton
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    skeleton_retry_count: int
    max_skeleton_retries: int
    
    # Phase 2: Track generation
    track_plan: List[Dict[str, Any]]
    current_track_index: int
    current_track_data: Dict[str, Any]
    generated_tracks: List[Dict[str, Any]]
    current_track_errors: List[str]
    track_retry_count: int
    max_track_retries: int
    used_action_types: List[str]
    
    # Action mismatch state
    action_mismatch: bool
    missing_action_types: List[str]
    action_mismatch_details: str
    user_action_mismatch_choice: str  # "continue" or "abort"
    
    # Phase 3: Assembly
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]
    
    # Compatibility
    final_result: Dict[str, Any]
    is_valid: bool
    
    # Common
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str


# ==================== Helper Functions ====================

def _save_generated_json(
    data: Dict[str, Any],
    stage: str,
    skill_name: str = "unknown",
    require_odin_format: bool = True
) -> Tuple[Optional[Path], bool]:
    """Save generated JSON to file"""
    try:
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in skill_name)
        filename = f"{safe_name}_{stage}_{timestamp}.json"
        filepath = _OUTPUT_DIR / filename
        
        is_odin_format = False
        data_to_save = data

        if stage == "final" and "tracks" in data:
            try:
                data_to_save = serialize_to_odin(data)
                is_odin_format = True
            except Exception as e:
                logger.warning(f"Odin serialization failed: {e}")

        with open(filepath, "w", encoding="utf-8") as f:
            if is_odin_format:
                f.write(odin_json_encode(data_to_save, indent=2))
            else:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {stage} JSON: {filepath}")
        return filepath, is_odin_format
    except Exception as e:
        logger.warning(f"Save failed: {e}")
        return None, False


def search_actions_by_track_type(
    track_type: str,
    purpose: str,
    top_k: int = 5,
    suggested_types: Optional[List[str]] = None,
    used_types: Optional[List[str]] = None,
    batch_context: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search actions by track type"""
    from ..tools.rag_tools import search_actions

    type_to_category = {
        "animation": ["Animation"],
        "effect": ["Effect", "Damage", "Buff", "Spawn", "Heal"],
        "audio": ["Audio", "Sound"],
        "movement": ["Movement", "Dash", "Teleport"],
        "camera": ["Camera"],
    }

    query = f"{track_type} {purpose[:50]}"
    if batch_context:
        query = f"{track_type} {batch_context} {purpose[:30]}"

    try:
        results = search_actions.invoke({"query": query, "top_k": top_k * 2})
        if not isinstance(results, list):
            return []

        categories = type_to_category.get(track_type, [])
        if categories:
            filtered = [r for r in results if any(c.lower() in r.get("category", "").lower() for c in categories)]
            if len(filtered) >= top_k // 2:
                results = filtered

        return results[:top_k]
    except Exception as e:
        logger.error(f"Action search failed: {e}")
        return []


def format_action_schemas_for_prompt(actions: List[Dict[str, Any]]) -> str:
    """Format action schemas for prompt"""
    if not actions:
        return "No action reference available"

    lines = []
    for action in actions[:5]:
        name = action.get("action_name", "Unknown")
        action_type = action.get("action_type", "")
        desc = action.get("description", "")[:100]
        params = action.get("parameters", [])
        
        param_lines = []
        for p in params[:5]:
            param_lines.append(f"  - {p.get('name')}: {p.get('type')}")
        
        lines.append(f"Action: {name}\nType: {action_type}\nDesc: {desc}\nParams:\n" + "\n".join(param_lines))

    return "\n\n".join(lines)


# ==================== Phase 1: Skeleton Generation ====================

def skeleton_generator_node(state: ProgressiveSkillGenerationState, writer: StreamWriter) -> Dict[str, Any]:
    """Generate skill skeleton with track plan"""
    from ..prompts.prompt_manager import get_prompt_manager

    requirement = state["requirement"]
    similar_skills = state.get("similar_skills", [])

    logger.info(f"Generating skeleton: {requirement[:50]}...")
    emit_skeleton_progress(ProgressEventType.SKELETON_STARTED, "Generating skeleton...", progress=0.02)

    messages = [AIMessage(content="Phase 1/3: Generating skeleton and track plan...")]
    similar_skills_text = format_similar_skills(similar_skills)

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skeleton_generation")

    api_start_time = time.time()
    thinking_message_id = f"skeleton_thinking_{api_start_time}"
    content_message_id = f"skeleton_content_{api_start_time}"
    full_reasoning, full_content = "", ""

    try:
        client = get_openai_client()
        prompt_value = prompt.invoke({"requirement": requirement, "similar_skills": similar_skills_text or "No reference"})
        
        openai_messages = []
        for msg in prompt_value.to_messages():
            msg_type = msg.__class__.__name__.lower()
            role = "system" if "system" in msg_type else "user" if "human" in msg_type else "assistant"
            openai_messages.append({"role": role, "content": msg.content})

        model_name = get_skill_gen_config().llm.model
        response = client.chat.completions.create(model=model_name, messages=openai_messages, stream=True)

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            if reasoning := getattr(delta, 'reasoning_content', None):
                full_reasoning += reasoning
                if writer:
                    try: writer({"type": "thinking_chunk", "message_id": thinking_message_id, "chunk": reasoning})
                    except: pass
            if content := getattr(delta, 'content', None):
                full_content += content
                if writer:
                    try: writer({"type": "content_chunk", "message_id": content_message_id, "chunk": content})
                    except: pass

        logger.info(f"Skeleton generation took: {time.time() - api_start_time:.2f}s")

        # 提取 JSON 之前的设计分析文本
        design_analysis = ""
        if "```json" in full_content:
            design_analysis = full_content.split("```json")[0].strip()
        elif "```" in full_content:
            design_analysis = full_content.split("```")[0].strip()
        
        json_content = extract_json_from_markdown(full_content)
        skeleton_dict = json.loads(json_content)
        validated = SkillSkeletonSchema.model_validate(skeleton_dict)
        skeleton_dict = validated.model_dump()

        _save_generated_json(skeleton_dict, "skeleton", skeleton_dict.get("skillName", "unknown"), False)
        validation_errors = validate_skeleton(skeleton_dict)

        if validation_errors:
            messages.append(AIMessage(content=f"骨架生成完成，但有 {len(validation_errors)} 个问题需要修复"))
        else:
            messages.append(AIMessage(content=f"骨架生成完成：{skeleton_dict['skillName']}"))

        if full_reasoning:
            messages.append(AIMessage(content=full_reasoning, additional_kwargs={"thinking": True}, id=thinking_message_id))
        
        # 🔥 将 content 输出添加到消息中，使用 content_message_id 确保流式消息被正确替换
        if full_content:
            messages.append(AIMessage(content=full_content, id=content_message_id))

        emit_skeleton_progress(ProgressEventType.SKELETON_COMPLETED, "Skeleton complete", progress=0.1)

        return {
            "skill_skeleton": skeleton_dict,
            "track_plan": skeleton_dict.get("trackPlan", []),
            "skeleton_validation_errors": validation_errors,
            "current_track_index": 0,
            "generated_tracks": [],
            "track_retry_count": 0,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"Skeleton generation failed: {e}")
        messages.append(AIMessage(content=f"Skeleton failed: {str(e)}"))
        emit_skeleton_progress(ProgressEventType.SKELETON_FAILED, str(e), progress=0.1)
        return {
            "skill_skeleton": {},
            "track_plan": [],
            "skeleton_validation_errors": [str(e)],
            "current_track_index": 0,
            "generated_tracks": [],
            "track_retry_count": 0,
            "messages": messages
        }


def skeleton_fixer_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """Fix skeleton based on validation errors"""
    from ..prompts.prompt_manager import get_prompt_manager

    skeleton = state.get("skill_skeleton", {})
    errors = state.get("skeleton_validation_errors", [])
    requirement = state.get("requirement", "")

    logger.info(f"Fixing skeleton, {len(errors)} errors")
    messages = [AIMessage(content=f"Fixing {len(errors)} skeleton errors...")]

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skeleton_validation_fix")
    llm = get_llm(temperature=0.3)

    try:
        fixer_llm = llm.with_structured_output(SkillSkeletonSchema, method="json_mode", include_raw=False)
        chain = prompt | fixer_llm
        response = chain.invoke({
            "errors": "\n".join(errors),
            "skeleton_json": json.dumps(skeleton, ensure_ascii=False),
            "requirement": requirement
        })

        if isinstance(response, SkillSkeletonSchema):
            fixed = response.model_dump()
        else:
            json_content = extract_json_from_markdown(prepare_payload_text(response))
            fixed = SkillSkeletonSchema.model_validate(json.loads(json_content)).model_dump()

        new_errors = validate_skeleton(fixed)
        messages.append(AIMessage(content="Skeleton fixed, re-validating..."))

        return {
            "skill_skeleton": fixed,
            "track_plan": fixed.get("trackPlan", []),
            "skeleton_validation_errors": new_errors,
            "skeleton_retry_count": state.get("skeleton_retry_count", 0) + 1,
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Skeleton fix failed: {e}")
        return {
            "skeleton_validation_errors": errors + [str(e)],
            "skeleton_retry_count": state.get("skeleton_retry_count", 0) + 1,
            "messages": [AIMessage(content=f"Fix failed: {str(e)}")]
        }


# ==================== Phase 2: Track Generation ====================

def track_generator_node(state: ProgressiveSkillGenerationState, writer: StreamWriter) -> Dict[str, Any]:
    """Generate a single track"""
    from ..prompts.prompt_manager import get_prompt_manager

    track_plan = state.get("track_plan", [])
    current_index = state.get("current_track_index", 0)
    skeleton = state.get("skill_skeleton", {})
    used_action_types = state.get("used_action_types", [])

    if current_index >= len(track_plan):
        return {"messages": [AIMessage(content="All tracks generated")]}

    track_item = track_plan[current_index]
    track_name = track_item.get("trackName", f"Track_{current_index}")
    purpose = track_item.get("purpose", "")
    total_duration = skeleton.get("totalDuration", 180)

    logger.info(f"Generating track {current_index + 1}/{len(track_plan)}: {track_name}")
    emit_track_progress(ProgressEventType.TRACK_STARTED, f"Generating {track_name}", current_index, len(track_plan), track_name)

    messages = [AIMessage(content=f"Phase 2: Generating track {current_index + 1}/{len(track_plan)}: {track_name}")]

    track_type = infer_track_type(track_name)
    action_schemas = search_actions_by_track_type(track_type, purpose, top_k=5, used_types=used_action_types)

    if not action_schemas:
        action_schemas = get_default_actions_for_track_type(track_type)
        logger.warning(f"Using default actions for {track_type}")

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("track_action_generation")

    api_start_time = time.time()
    thinking_message_id = f"track_{current_index}_thinking_{api_start_time}"
    content_message_id = f"track_{current_index}_content_{api_start_time}"
    full_reasoning, full_content = "", ""

    try:
        client = get_openai_client()
        skill_name = skeleton.get("skillName", "未命名技能")
        estimated_actions = track_item.get("estimatedActions", 3)
        prompt_inputs = {
            "skillName": skill_name,
            "totalDuration": total_duration,
            "trackName": track_name,
            "purpose": purpose,
            "estimatedActions": estimated_actions,
            "relevant_actions": format_action_schemas_for_prompt(action_schemas),
        }
        prompt_value = prompt.invoke(prompt_inputs)

        openai_messages = []
        for msg in prompt_value.to_messages():
            msg_type = msg.__class__.__name__.lower()
            role = "system" if "system" in msg_type else "user" if "human" in msg_type else "assistant"
            openai_messages.append({"role": role, "content": msg.content})

        model_name = get_skill_gen_config().llm.model
        response = client.chat.completions.create(model=model_name, messages=openai_messages, stream=True)

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            if reasoning := getattr(delta, 'reasoning_content', None):
                full_reasoning += reasoning
                if writer:
                    try: writer({"type": "thinking_chunk", "message_id": thinking_message_id, "chunk": reasoning})
                    except: pass
            if content := getattr(delta, 'content', None):
                full_content += content
                if writer:
                    try: writer({"type": "content_chunk", "message_id": content_message_id, "chunk": content})
                    except: pass

        logger.info(f"Track generation took: {time.time() - api_start_time:.2f}s")

        # 提取 JSON 之前的设计思路文本
        design_analysis = ""
        if "```json" in full_content:
            design_analysis = full_content.split("```json")[0].strip()
        elif "```" in full_content:
            design_analysis = full_content.split("```")[0].strip()

        json_content = extract_json_from_markdown(full_content)
        track_dict = json.loads(json_content)
        validated = SkillTrack.model_validate(track_dict)
        track_dict = validated.model_dump()

        if track_dict.get("trackName") != track_name:
            track_dict["trackName"] = track_name

        messages.append(AIMessage(content=f"轨道生成完成：{track_name}，包含 {len(track_dict.get('actions', []))} 个动作"))

        if full_reasoning:
            messages.append(AIMessage(content=full_reasoning, additional_kwargs={"thinking": True}, id=thinking_message_id))
        
        # 🔥 将 content 输出添加到消息中，使用 content_message_id 确保流式消息被正确替换
        if full_content:
            messages.append(AIMessage(content=full_content, id=content_message_id))

        return {
            "current_track_data": track_dict,
            "current_track_errors": [],
            "messages": messages
        }

    except Exception as e:
        logger.error(f"Track generation failed: {e}")
        return {
            "current_track_data": {},
            "current_track_errors": [str(e)],
            "messages": [AIMessage(content=f"Track generation failed: {str(e)}")]
        }


def track_validator_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """Validate generated track, including action type existence check"""
    from .validators import validate_track_action_types
    
    track_data = state.get("current_track_data", {})
    skeleton = state.get("skill_skeleton", {})
    total_duration = skeleton.get("totalDuration", 180)

    errors = validate_track(track_data, total_duration)
    
    # 验证 Action 类型是否存在
    missing_types, type_errors = validate_track_action_types(track_data)
    
    if missing_types:
        logger.warning(f"Track contains invalid action types: {missing_types}")
        track_name = track_data.get("trackName", "Unknown")
        details = f"Track '{track_name}' 使用了不存在的 Action 类型: {', '.join(missing_types)}"
        
        return {
            "current_track_errors": errors + type_errors,
            "action_mismatch": True,
            "missing_action_types": missing_types,
            "action_mismatch_details": details,
            "messages": [AIMessage(content=f"[需要确认] {details}")]
        }

    if errors:
        logger.warning(f"Track validation: {len(errors)} errors")
        return {"current_track_errors": errors, "messages": [AIMessage(content=f"轨道验证发现 {len(errors)} 个问题")]}
    
    logger.info("Track validation passed")
    return {"current_track_errors": [], "messages": [AIMessage(content="轨道验证通过")]}


def track_accumulator_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """Accumulate validated track and move to next"""
    track_data = state.get("current_track_data", {})
    generated_tracks = list(state.get("generated_tracks", []))
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])
    used_action_types = list(state.get("used_action_types", []))

    generated_tracks.append(track_data)

    for action in track_data.get("actions", []):
        action_type = extract_action_type_name(action.get("parameters", {}).get("_odin_type", ""))
        if action_type and action_type not in used_action_types:
            used_action_types.append(action_type)

    next_index = current_index + 1
    track_name = track_data.get("trackName", "")

    emit_track_progress(ProgressEventType.TRACK_COMPLETED, f"Track {track_name} complete", current_index, len(track_plan), track_name)

    return {
        "generated_tracks": generated_tracks,
        "current_track_index": next_index,
        "track_retry_count": 0,
        "used_action_types": used_action_types,
        "messages": [AIMessage(content=f"Track {current_index + 1}/{len(track_plan)} saved")]
    }


# ==================== Phase 3: Assembly ====================

def skill_assembler_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """Assemble all tracks into final skill"""
    skeleton = state.get("skill_skeleton", {})
    tracks = state.get("generated_tracks", [])

    logger.info(f"Assembling skill: {len(tracks)} tracks")

    max_end_frame = 0
    for track in tracks:
        for action in track.get("actions", []):
            end_frame = action.get("frame", 0) + action.get("duration", 0)
            max_end_frame = max(max_end_frame, end_frame)

    assembled = {
        "skillName": skeleton.get("skillName", "Unknown"),
        "skillId": skeleton.get("skillId", "unknown-001"),
        "skillDescription": skeleton.get("skillDescription", ""),
        "totalDuration": max(skeleton.get("totalDuration", 180), max_end_frame),
        "frameRate": skeleton.get("frameRate", 30),
        "tracks": tracks
    }

    errors = []
    try:
        OdinSkillSchema.model_validate(assembled)
    except ValidationError as e:
        for err in e.errors():
            errors.append(f"{err['loc']}: {err['msg']}")

    return {
        "assembled_skill": assembled,
        "final_validation_errors": errors,
        "messages": [AIMessage(content=f"Skill assembled: {len(tracks)} tracks, {len(errors)} issues")]
    }


def finalize_progressive_node(state: ProgressiveSkillGenerationState) -> Dict[str, Any]:
    """Finalize and save the skill"""
    assembled_skill = state.get("assembled_skill", {})
    final_errors = state.get("final_validation_errors", [])
    action_mismatch = state.get("action_mismatch", False)

    messages = []

    if action_mismatch:
        emit_finalize_progress(ProgressEventType.GENERATION_FAILED, "Action mismatch", is_valid=False)
        return {
            "final_result": {},
            "is_valid": False,
            "messages": [AIMessage(content="Generation interrupted: missing action types")]
        }

    is_valid = len(final_errors) == 0

    if assembled_skill:
        filepath, is_odin = _save_generated_json(assembled_skill, "final", assembled_skill.get("skillName", "unknown"))
        if filepath and not is_odin:
            messages.append(AIMessage(content="Warning: Odin serialization failed"))

    if is_valid:
        messages.append(AIMessage(content=f"Skill {assembled_skill.get('skillName')} generated successfully!"))
        emit_finalize_progress(ProgressEventType.GENERATION_COMPLETED, "Success", is_valid=True)
    else:
        messages.append(AIMessage(content=f"Skill generated with {len(final_errors)} warnings"))
        emit_finalize_progress(ProgressEventType.GENERATION_COMPLETED, "With warnings", is_valid=False)

    return {"final_result": assembled_skill, "is_valid": is_valid, "messages": messages}


# ==================== Conditional Functions ====================

def should_continue_to_track_generation(state: ProgressiveSkillGenerationState) -> Literal["generate_tracks", "fix_skeleton", "skeleton_failed"]:
    """Determine next step after skeleton generation"""
    errors = state.get("skeleton_validation_errors", [])
    retry_count = state.get("skeleton_retry_count", 0)
    max_retries = state.get("max_skeleton_retries", 2)

    if not errors:
        return "generate_tracks"
    if retry_count < max_retries:
        return "fix_skeleton"
    return "skeleton_failed"


def should_continue_track_loop(state: ProgressiveSkillGenerationState) -> Literal["next_track", "assemble", "fix_track", "action_mismatch_interrupt"]:
    """Determine next step in track generation loop"""
    # 检查是否有无效 Action 类型
    action_mismatch = state.get("action_mismatch", False)
    if action_mismatch:
        return "action_mismatch_interrupt"
    
    errors = state.get("current_track_errors", [])
    retry_count = state.get("track_retry_count", 0)
    max_retries = state.get("max_track_retries", 3)
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])

    if errors and retry_count < max_retries:
        return "fix_track"

    if current_index >= len(track_plan) - 1:
        return "assemble"

    return "next_track"


def should_finalize_or_fail(state: ProgressiveSkillGenerationState) -> Literal["finalize", "failed"]:
    """Determine if we should finalize or fail"""
    assembled = state.get("assembled_skill", {})
    if not assembled or not assembled.get("tracks"):
        return "failed"
    return "finalize"
