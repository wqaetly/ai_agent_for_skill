"""
Single Action Skill Generation Nodes (Refactored)
Finest granularity: Skeleton -> Track Plan -> Single Action Loop -> Assembly
"""

import json
import logging
import time
from typing import Any, Dict, List, TypedDict, Annotated, Optional, Literal, Tuple

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from pydantic import ValidationError

from .base import get_llm, get_openai_client, prepare_payload_text
from .base.streaming import get_writer_safe, emit_track_progress
from .json_utils import extract_json_from_markdown
from .validators import extract_action_type_name, validate_track, validate_action_matches_track_type
from .constants import infer_track_type, get_default_actions_for_track_type
from .progressive_skill_nodes import (
    skeleton_generator_node, skeleton_fixer_node,
    should_continue_to_track_generation, skill_assembler_node,
    finalize_progressive_node, should_finalize_or_fail,
    search_actions_by_track_type, format_action_schemas_for_prompt, _save_generated_json
)
from ..schemas import SkillAction
from ..streaming import ProgressEventType
from ..config import get_skill_gen_config

logger = logging.getLogger(__name__)

MAX_CONTEXT_ACTIONS = 5
DEFAULT_ACTION_DURATION = 30


# ==================== State Definition ====================

class SingleActionProgressiveState(TypedDict):
    """Single action progressive generation state"""
    requirement: str
    similar_skills: List[Dict[str, Any]]
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    skeleton_retry_count: int
    max_skeleton_retries: int
    track_plan: List[Dict[str, Any]]
    current_track_index: int
    current_action_plan: List[Dict[str, Any]]
    current_action_index: int
    current_action_data: Dict[str, Any]
    current_track_actions: List[Dict[str, Any]]
    generated_tracks: List[Dict[str, Any]]
    current_track_errors: List[str]
    action_retry_count: int
    max_action_retries: int
    used_action_types: List[str]
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]
    final_result: Dict[str, Any]
    is_valid: bool
    action_mismatch: bool
    missing_action_types: List[str]
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str


# ==================== Action Planning ====================

def plan_track_actions(track_name: str, purpose: str, estimated_actions: int, total_duration: int) -> List[Dict[str, Any]]:
    """Plan individual actions for a track"""
    track_type = infer_track_type(track_name)
    action_duration = total_duration // max(1, estimated_actions)
    
    action_plan = []
    for i in range(estimated_actions):
        start_frame = i * action_duration
        action_plan.append({
            "action_index": i,
            "suggested_frame": start_frame,
            "suggested_duration": min(action_duration, DEFAULT_ACTION_DURATION),
            "track_type": track_type,
            "context": f"Action {i+1}/{estimated_actions} for {purpose[:30]}"
        })
    return action_plan


# ==================== Single Action Nodes ====================

def action_planner_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """Plan actions for current track"""
    track_plan = state.get("track_plan", [])
    current_index = state.get("current_track_index", 0)
    skeleton = state.get("skill_skeleton", {})
    
    if current_index >= len(track_plan):
        return {"messages": [AIMessage(content="All tracks planned")]}
    
    track_item = track_plan[current_index]
    track_name = track_item.get("trackName", f"Track_{current_index}")
    purpose = track_item.get("purpose", "")
    estimated_actions = track_item.get("estimatedActions", 3)
    total_duration = skeleton.get("totalDuration", 180)
    
    action_plan = plan_track_actions(track_name, purpose, estimated_actions, total_duration)
    logger.info(f"Planned {len(action_plan)} actions for track {track_name}")
    
    return {
        "current_action_plan": action_plan,
        "current_action_index": 0,
        "current_track_actions": [],
        "messages": [AIMessage(content=f"Track {track_name}: {len(action_plan)} actions planned")]
    }


def single_action_generator_node(state: SingleActionProgressiveState, writer: StreamWriter) -> Dict[str, Any]:
    """Generate a single action"""
    from ..prompts.prompt_manager import get_prompt_manager
    
    action_plan = state.get("current_action_plan", [])
    action_index = state.get("current_action_index", 0)
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)
    skeleton = state.get("skill_skeleton", {})
    track_actions = state.get("current_track_actions", [])
    used_action_types = state.get("used_action_types", [])
    
    if action_index >= len(action_plan):
        return {"messages": [AIMessage(content="All actions generated")]}
    
    action_item = action_plan[action_index]
    track_item = track_plan[current_track_idx] if current_track_idx < len(track_plan) else {}
    track_name = track_item.get("trackName", "Unknown")
    purpose = track_item.get("purpose", "")
    track_type = action_item.get("track_type", "effect")
    
    logger.info(f"Generating action {action_index + 1}/{len(action_plan)} for {track_name}")
    
    action_schemas = search_actions_by_track_type(track_type, purpose, top_k=3, used_types=used_action_types)
    if not action_schemas:
        action_schemas = get_default_actions_for_track_type(track_type)
    
    context_actions = track_actions[-MAX_CONTEXT_ACTIONS:] if track_actions else []
    context_text = ""
    if context_actions:
        context_lines = [f"Frame {a.get('frame')}: {extract_action_type_name(a.get('parameters', {}).get('_odin_type', ''))}" for a in context_actions]
        context_text = "Previous actions:\n" + "\n".join(context_lines)
    
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("single_action_generation")
    
    prompt_inputs = {
        "track_name": track_name,
        "action_index": action_index + 1,
        "total_actions": len(action_plan),
        "suggested_frame": action_item.get("suggested_frame", 0),
        "suggested_duration": action_item.get("suggested_duration", 30),
        "context": context_text or "First action in track",
        "action_schemas": format_action_schemas_for_prompt(action_schemas),
        "total_duration": skeleton.get("totalDuration", 180)
    }
    
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
        response = client.chat.completions.create(model=model_name, messages=openai_messages, stream=True)
        
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and (content := getattr(delta, 'content', None)):
                full_content += content
        
        json_content = extract_json_from_markdown(full_content)
        action_data = json.loads(json_content)
        
        is_valid, error_msg = validate_action_matches_track_type(action_data, track_type)
        if not is_valid:
            logger.warning(f"Action type mismatch: {error_msg}")
        
        return {"current_action_data": action_data, "messages": [AIMessage(content=f"Action {action_index + 1} generated")]}
    except Exception as e:
        logger.error(f"Action generation failed: {e}")
        return {"current_action_data": {}, "messages": [AIMessage(content=f"Action generation failed: {str(e)}")]}


def action_accumulator_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """Accumulate action and move to next"""
    action_data = state.get("current_action_data", {})
    track_actions = list(state.get("current_track_actions", []))
    action_index = state.get("current_action_index", 0)
    
    if action_data:
        track_actions.append(action_data)
    
    return {"current_track_actions": track_actions, "current_action_index": action_index + 1, "action_retry_count": 0, "messages": [AIMessage(content=f"Action {action_index + 1} accumulated")]}


def track_assembler_node(state: SingleActionProgressiveState) -> Dict[str, Any]:
    """Assemble track from all actions"""
    track_actions = state.get("current_track_actions", [])
    track_plan = state.get("track_plan", [])
    current_index = state.get("current_track_index", 0)
    generated_tracks = list(state.get("generated_tracks", []))
    used_action_types = list(state.get("used_action_types", []))
    skeleton = state.get("skill_skeleton", {})
    
    track_item = track_plan[current_index] if current_index < len(track_plan) else {}
    track_name = track_item.get("trackName", f"Track_{current_index}")
    
    track_data = {"trackName": track_name, "enabled": True, "actions": track_actions}
    errors = validate_track(track_data, skeleton.get("totalDuration", 180))
    
    if not errors:
        generated_tracks.append(track_data)
        for action in track_actions:
            action_type = extract_action_type_name(action.get("parameters", {}).get("_odin_type", ""))
            if action_type and action_type not in used_action_types:
                used_action_types.append(action_type)
    
    emit_track_progress(ProgressEventType.TRACK_COMPLETED, f"Track {track_name} complete", current_index, len(track_plan), track_name)
    
    return {"generated_tracks": generated_tracks, "current_track_index": current_index + 1, "current_track_errors": errors, "used_action_types": used_action_types, "messages": [AIMessage(content=f"Track {track_name} assembled: {len(track_actions)} actions")]}


# ==================== Conditional Functions ====================

def should_continue_action_loop(state: SingleActionProgressiveState) -> Literal["next_action", "assemble_track"]:
    action_index = state.get("current_action_index", 0)
    action_plan = state.get("current_action_plan", [])
    return "assemble_track" if action_index >= len(action_plan) else "next_action"


def should_continue_track_loop(state: SingleActionProgressiveState) -> Literal["next_track", "assemble_skill"]:
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])
    return "assemble_skill" if current_index >= len(track_plan) else "next_track"


__all__ = [
    "SingleActionProgressiveState", "plan_track_actions", "action_planner_node",
    "single_action_generator_node", "action_accumulator_node", "track_assembler_node",
    "should_continue_action_loop", "should_continue_track_loop",
    "skeleton_generator_node", "skeleton_fixer_node", "should_continue_to_track_generation",
    "skill_assembler_node", "finalize_progressive_node", "should_finalize_or_fail",
]
