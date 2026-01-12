"""
LangGraph 节点实现 - 基础技能生成
定义 Graph 中的各个节点（generator、validator、fixer 等）
"""

import json
import logging
import time
from typing import Any, Dict, List, TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage
from pydantic import ValidationError

from .base import get_llm, get_openai_client, prepare_payload_text, safe_int
from .json_utils import extract_json_from_markdown
from ..config import get_skill_gen_config

logger = logging.getLogger(__name__)

# Default action type when missing
DEFAULT_ACTION_TYPE = "SkillSystem.Actions.BaseAction, Assembly-CSharp"


# ==================== State Definition ====================

class SkillGenerationState(TypedDict):
    """Skill generation workflow state"""
    requirement: str
    similar_skills: List[Dict[str, Any]]
    action_schemas: List[Dict[str, Any]]
    generated_json: str
    validation_errors: List[str]
    retry_count: int
    max_retries: int
    final_result: Dict[str, Any]
    messages: Annotated[List, "append"]
    thread_id: str


# ==================== Odin Structure Enforcement ====================

def _normalize_existing_tracks(payload_dict: Dict[str, Any], source: str):
    """Normalize existing tracks structure"""
    from ..schemas import OdinSkillSchema

    max_end_frame = 0
    normalized_tracks = []

    for track_dict in payload_dict.get("tracks", []):
        track_name = track_dict.get("trackName") or track_dict.get("track_name") or "Unknown Track"
        enabled = bool(track_dict.get("enabled", True))
        actions = track_dict.get("actions", [])

        normalized_actions = []
        for action in actions:
            frame = safe_int(action.get("frame"), default=0, min_value=0)
            duration = safe_int(action.get("duration"), default=1, min_value=1)
            action_enabled = bool(action.get("enabled", True))
            parameters = action.get("parameters") or {}

            if "_odin_type" not in parameters:
                fallback_type = (
                    parameters.get("odinType") or
                    action.get("_odin_type") or
                    action.get("odinType") or
                    DEFAULT_ACTION_TYPE
                )
                parameters = {**parameters, "_odin_type": fallback_type}

            normalized_actions.append({
                "frame": frame,
                "duration": duration,
                "enabled": action_enabled,
                "parameters": parameters
            })
            max_end_frame = max(max_end_frame, frame + duration)

        normalized_tracks.append({
            "trackName": track_name,
            "enabled": enabled,
            "actions": normalized_actions
        })

    normalized_dict = {
        "skillName": payload_dict.get("skillName") or "Unnamed Skill",
        "skillId": payload_dict.get("skillId") or "unnamed-skill-001",
        "skillDescription": payload_dict.get("skillDescription") or "",
        "totalDuration": max(
            safe_int(payload_dict.get("totalDuration"), default=0, min_value=1),
            max_end_frame or 1
        ),
        "frameRate": safe_int(payload_dict.get("frameRate"), default=30, min_value=1),
        "tracks": normalized_tracks
    }

    try:
        final_skill = OdinSkillSchema.model_validate(normalized_dict)
        logger.info(f"Normalized {source} tracks: {len(normalized_tracks)} tracks")
        return final_skill
    except ValidationError as e:
        logger.error(f"Normalization failed: {e}")
        raise ValueError(f"{source} tracks normalization failed") from e


def enforce_odin_structure(payload: Any, source: str):
    """Force convert any payload to OdinSkillSchema structure"""
    from ..schemas import OdinSkillSchema, SimplifiedSkillSchema

    if isinstance(payload, OdinSkillSchema):
        return payload

    payload_text = prepare_payload_text(payload)
    if not payload_text:
        raise ValueError(f"{source} payload is empty")

    json_blob = extract_json_from_markdown(payload_text)

    try:
        validated_skill = OdinSkillSchema.model_validate_json(json_blob)
        logger.info(f"{source} validated as OdinSkillSchema")
        return validated_skill
    except ValidationError:
        pass

    try:
        payload_dict = json.loads(json_blob)
    except json.JSONDecodeError as e:
        raise ValueError(f"{source} is not valid JSON") from e

    has_tracks = "tracks" in payload_dict and isinstance(payload_dict["tracks"], list)
    has_actions = "actions" in payload_dict and isinstance(payload_dict["actions"], list)

    if not has_tracks and not has_actions:
        raise ValueError(f"{source} has neither tracks nor actions field")

    if has_tracks:
        return _normalize_existing_tracks(payload_dict, source)

    # Handle flat actions structure
    try:
        simplified = SimplifiedSkillSchema.model_validate(payload_dict)
    except ValidationError as e:
        raise ValueError(f"{source} cannot be validated as SimplifiedSkillSchema") from e

    grouped_actions: Dict[str, List[Dict[str, Any]]] = {}
    for action in simplified.actions:
        track_name = action.get("trackName") or action.get("track_name") or "Animation Track"
        grouped_actions.setdefault(track_name, []).append(action)

    if not grouped_actions:
        grouped_actions["Animation Track"] = [{
            "frame": 0, "duration": 1, "enabled": True,
            "parameters": {"_odin_type": DEFAULT_ACTION_TYPE}
        }]

    tracks: List[Dict[str, Any]] = []
    max_end_frame = 0

    for track_name, actions in grouped_actions.items():
        odin_actions = []
        for action in actions:
            frame = safe_int(action.get("frame"), default=0, min_value=0)
            duration = safe_int(action.get("duration"), default=1, min_value=1)
            enabled = bool(action.get("enabled", True))
            parameters = action.get("parameters") or {}

            if "_odin_type" not in parameters:
                fallback_type = (
                    parameters.get("odinType") or
                    action.get("_odin_type") or
                    action.get("odinType") or
                    DEFAULT_ACTION_TYPE
                )
                parameters = {**parameters, "_odin_type": fallback_type}

            odin_actions.append({
                "frame": frame, "duration": duration,
                "enabled": enabled, "parameters": parameters
            })
            max_end_frame = max(max_end_frame, frame + duration)

        tracks.append({"trackName": track_name, "enabled": True, "actions": odin_actions})

    normalized_dict = {
        "skillName": simplified.skillName,
        "skillId": simplified.skillId,
        "skillDescription": payload_dict.get("skillDescription") or "",
        "totalDuration": max(
            safe_int(payload_dict.get("totalDuration"), default=0, min_value=1),
            max_end_frame or 1
        ),
        "frameRate": safe_int(payload_dict.get("frameRate"), default=30, min_value=1),
        "tracks": tracks
    }

    try:
        final_skill = OdinSkillSchema.model_validate(normalized_dict)
        logger.info(f"{source} converted to OdinSkillSchema: {len(tracks)} tracks")
        return final_skill
    except ValidationError as e:
        raise ValueError(f"{source} normalization failed") from e


# ==================== Node Functions ====================

def retriever_node(state: SkillGenerationState) -> Dict[str, Any]:
    """Retrieve similar skills and action schemas from RAG"""
    from ..tools.rag_tools import search_skills_semantic, search_actions

    requirement = state["requirement"]
    logger.info(f"Retrieving similar skills: {requirement}")

    messages = [AIMessage(content=f"Searching for skills related to: {requirement}...")]

    try:
        start_time = time.time()
        results = search_skills_semantic.invoke({"query": requirement, "top_k": 2})
        logger.info(f"Skill search took: {time.time() - start_time:.2f}s")

        action_start = time.time()
        action_results = search_actions.invoke({"query": requirement, "top_k": 5})
        logger.info(f"Action search took: {time.time() - action_start:.2f}s")
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        results, action_results = [], []
        messages.append(AIMessage(content="Search failed, generating from scratch"))

    if results:
        skills_summary = "\n".join([
            f"- {skill.get('skill_name', 'Unknown')} ({skill.get('similarity', 0):.0%})"
            for skill in results[:3]
        ])
        messages.append(AIMessage(content=f"Found {len(results)} similar skills:\n{skills_summary}"))
    else:
        messages.append(AIMessage(content="No similar skills found"))

    return {
        "similar_skills": results,
        "action_schemas": action_results if isinstance(action_results, list) else [],
        "messages": messages
    }


def generator_node(state: SkillGenerationState, writer: Any = None) -> Dict[str, Any]:
    """Generate skill JSON using LLM with streaming"""
    from ..prompts.prompt_manager import get_prompt_manager
    from ..schemas import OdinSkillSchema
    from .formatters import format_similar_skills, format_action_schemas_for_prompt

    requirement = state["requirement"]
    similar_skills = state.get("similar_skills", [])
    action_schemas = state.get("action_schemas", [])

    logger.info(f"Generating skill: {requirement}")
    messages = [AIMessage(content="Calling DeepSeek AI to generate skill...")]

    # Format inputs
    similar_skills_text = format_similar_skills(similar_skills)
    action_schemas_text = format_action_schemas_for_prompt(action_schemas)

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("skill_generation")

    prompt_inputs = {
        "requirement": requirement,
        "similar_skills": similar_skills_text or "No reference skills",
        "action_schemas": action_schemas_text or "No action reference"
    }

    api_start_time = time.time()
    thinking_message_id = f"thinking_{api_start_time}"
    content_message_id = f"content_{api_start_time}"

    full_reasoning = ""
    full_content = ""

    try:
        client = get_openai_client()
        prompt_value = prompt.invoke(prompt_inputs)

        openai_messages = []
        for msg in prompt_value.to_messages():
            msg_type = msg.__class__.__name__.lower()
            role = "system" if "system" in msg_type else "user" if "human" in msg_type else "assistant"
            openai_messages.append({"role": role, "content": msg.content})

        model_name = get_skill_gen_config().llm.model
        response = client.chat.completions.create(
            model=model_name, messages=openai_messages, stream=True
        )

        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            reasoning_chunk = getattr(delta, 'reasoning_content', None)
            if reasoning_chunk:
                full_reasoning += reasoning_chunk
                if writer:
                    try:
                        writer({"type": "thinking_chunk", "message_id": thinking_message_id, "chunk": reasoning_chunk})
                    except Exception:
                        pass

            content_chunk = getattr(delta, 'content', None)
            if content_chunk:
                full_content += content_chunk
                if writer:
                    try:
                        writer({"type": "content_chunk", "message_id": content_message_id, "chunk": content_chunk})
                    except Exception:
                        pass

        logger.info(f"Generation took: {time.time() - api_start_time:.2f}s")

        # Try to normalize output
        normalized_skill = None
        try:
            normalized_skill = enforce_odin_structure(full_content, "stream_output")
            generated_json = normalized_skill.model_dump_json(indent=2)
            messages.append(AIMessage(content="Schema validation passed"))
        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
            generated_json = full_content
            messages.append(AIMessage(content="Schema validation warning, will retry"))

        if full_reasoning:
            messages.append(AIMessage(content=full_reasoning, additional_kwargs={"thinking": True}, id=thinking_message_id))
        
        # 🔥 修复：将 content 输出也添加到消息中，避免流式结束后 JSON 内容丢失
        if full_content:
            messages.append(AIMessage(content=full_content, id=content_message_id))

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        generated_json = ""
        messages.append(AIMessage(content=f"Generation failed: {str(e)}"))
        return {"generated_json": generated_json, "messages": messages, "validation_errors": [f"api_error: {str(e)}"]}

    return {"generated_json": generated_json, "messages": messages}


def validator_node(state: SkillGenerationState) -> Dict[str, Any]:
    """Validate generated JSON against OdinSkillSchema"""
    from ..schemas import OdinSkillSchema

    generated_json = state["generated_json"]
    logger.info("Validating generated JSON")

    messages = [AIMessage(content="Validating skill configuration...")]
    errors = []

    try:
        json_content = extract_json_from_markdown(generated_json)

        try:
            skill_data = OdinSkillSchema.model_validate_json(json_content)
            logger.info("Pydantic validation passed")

            # Business rule validation
            max_action_end_frame = 0
            for track in skill_data.tracks:
                for action in track.actions:
                    action_end = action.frame + action.duration
                    max_action_end_frame = max(max_action_end_frame, action_end)

            if skill_data.totalDuration < max_action_end_frame:
                errors.append(f"totalDuration ({skill_data.totalDuration}) < max action end ({max_action_end_frame})")

            for track_idx, track in enumerate(skill_data.tracks):
                for action_idx, action in enumerate(track.actions):
                    if "_odin_type" not in action.parameters:
                        errors.append(f"Track[{track_idx}].Action[{action_idx}] missing _odin_type")

        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")

    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {str(e)}")
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    if errors:
        logger.warning(f"Validation failed: {len(errors)} errors")
        messages.append(AIMessage(content=f"Validation failed: {len(errors)} errors\n" + "\n".join(f"- {e}" for e in errors)))
    else:
        logger.info("Validation passed")
        messages.append(AIMessage(content="Validation passed!"))

    return {"validation_errors": errors, "messages": messages}


def fixer_node(state: SkillGenerationState) -> Dict[str, Any]:
    """Fix JSON based on validation errors"""
    from ..prompts.prompt_manager import get_prompt_manager
    from ..schemas import OdinSkillSchema

    generated_json = state["generated_json"]
    errors = state["validation_errors"]

    logger.info(f"Fixing JSON, {len(errors)} errors")
    errors_text = "\n".join([f"{i+1}. {err}" for i, err in enumerate(errors)])

    messages = [AIMessage(content=f"Fixing {len(errors)} errors...\n{errors_text}")]

    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("validation_fix")

    llm = get_llm(temperature=0.3)

    try:
        fixer_llm = llm.with_structured_output(OdinSkillSchema, method="json_mode", include_raw=False)
    except Exception:
        fixer_llm = llm

    chain = prompt | fixer_llm
    response = chain.invoke({"errors": errors_text, "json": generated_json})

    try:
        normalized_skill = enforce_odin_structure(response, "fixer")
        fixed_json = normalized_skill.model_dump_json(indent=2)
        messages.append(AIMessage(content="Fix successful"))
    except Exception as e:
        logger.error(f"Fix normalization failed: {e}")
        fixed_json = prepare_payload_text(response)
        messages.append(AIMessage(content="Fix attempted, will retry validation"))

    return {
        "generated_json": fixed_json,
        "retry_count": state["retry_count"] + 1,
        "messages": messages
    }


def finalize_node(state: SkillGenerationState) -> Dict[str, Any]:
    """Finalize and parse the generated JSON"""
    generated_json = state["generated_json"]

    try:
        json_content = extract_json_from_markdown(generated_json)
        final_result = json.loads(json_content)
        logger.info("Skill generation completed")
    except json.JSONDecodeError as e:
        final_result = {"error": f"JSON parse failed: {str(e)}", "raw_json": generated_json}
        logger.error(f"Final JSON parse failed: {e}")

    return {"final_result": final_result, "messages": [HumanMessage(content="Generation complete")]}


# ==================== Conditional Functions ====================

def should_continue(state: SkillGenerationState) -> str:
    """Determine whether to continue fixing or finalize"""
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if not errors:
        return "finalize"

    if retry_count >= max_retries:
        logger.warning(f"Max retries ({max_retries}) reached")
        return "finalize"

    return "fix"


# Backward compatibility aliases
_prepare_payload_text = prepare_payload_text
_safe_int = safe_int
_enforce_odin_structure = enforce_odin_structure
