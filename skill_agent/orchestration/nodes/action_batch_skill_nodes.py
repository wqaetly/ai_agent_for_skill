"""
Action Batch Skill Generation Nodes (Refactored)
Batch-level generation: Skeleton -> Batch Planning -> Batch Generation -> Assembly
"""

import json
import logging
import time
from typing import Any, Dict, List, TypedDict, Annotated, Optional, Literal

from langchain_core.messages import AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter
from pydantic import ValidationError

from .base import get_llm, get_openai_client, prepare_payload_text, safe_int
from .base.streaming import get_writer_safe, emit_batch_progress
from .json_utils import extract_json_from_markdown
from .validators import extract_action_type_name, validate_track, validate_semantic_rules
from .constants import infer_track_type, get_default_actions_for_track_type, SEMANTIC_RULES, TRACK_TYPE_RULES
from .context import (
    create_initial_context, update_context_after_batch, format_context_for_prompt,
    merge_frame_intervals, extract_key_params
)
from .progressive_skill_nodes import (
    skeleton_generator_node, skeleton_fixer_node,
    should_continue_to_track_generation, skill_assembler_node,
    finalize_progressive_node, should_finalize_or_fail,
    search_actions_by_track_type, format_action_schemas_for_prompt, _save_generated_json
)
from ..schemas import SkillTrack, BatchPhase, BatchContextState
from ..streaming import ProgressEventType
from ..config import get_skill_gen_config

logger = logging.getLogger(__name__)

# Batch configuration
MAX_ACTIONS_PER_BATCH = 5
MIN_ACTIONS_PER_BATCH = 2


# ==================== State Definition ====================

class ActionBatchSkillGenerationState(TypedDict):
    """Action batch skill generation state"""
    # Input
    requirement: str
    similar_skills: List[Dict[str, Any]]
    
    # Phase 1: Skeleton (reuse from progressive)
    skill_skeleton: Dict[str, Any]
    skeleton_validation_errors: List[str]
    skeleton_retry_count: int
    max_skeleton_retries: int
    
    # Phase 2: Track and Batch
    track_plan: List[Dict[str, Any]]
    current_track_index: int
    current_track_batch_plan: List[Dict[str, Any]]
    current_batch_index: int
    current_batch_actions: List[Dict[str, Any]]
    current_track_actions: List[Dict[str, Any]]
    batch_context: BatchContextState
    
    # Generated data
    generated_tracks: List[Dict[str, Any]]
    current_track_errors: List[str]
    track_retry_count: int
    max_track_retries: int
    used_action_types: List[str]
    
    # Phase 3: Assembly
    assembled_skill: Dict[str, Any]
    final_validation_errors: List[str]
    
    # Compatibility
    final_result: Dict[str, Any]
    is_valid: bool
    action_mismatch: bool
    missing_action_types: List[str]
    
    # Common
    messages: Annotated[List[AnyMessage], add_messages]
    thread_id: str


# ==================== Batch Planning ====================

def calculate_batch_plan(
    track_name: str,
    estimated_actions: int,
    total_duration: int,
    purpose: str
) -> List[Dict[str, Any]]:
    """Calculate batch plan for a track"""
    num_batches = max(1, (estimated_actions + MAX_ACTIONS_PER_BATCH - 1) // MAX_ACTIONS_PER_BATCH)
    actions_per_batch = max(MIN_ACTIONS_PER_BATCH, estimated_actions // num_batches)
    
    batch_plan = []
    remaining = estimated_actions
    frame_per_batch = total_duration // num_batches if num_batches > 0 else total_duration
    
    for i in range(num_batches):
        batch_actions = min(actions_per_batch, remaining)
        if batch_actions <= 0:
            break
            
        start_frame = i * frame_per_batch
        end_frame = min((i + 1) * frame_per_batch, total_duration)
        
        # Determine phase
        if i < num_batches * 0.3:
            phase = BatchPhase.SETUP.value
        elif i < num_batches * 0.7:
            phase = BatchPhase.MAIN.value
        else:
            phase = BatchPhase.CLEANUP.value
        
        batch_plan.append({
            "batch_index": i,
            "action_count": batch_actions,
            "frame_start": start_frame,
            "frame_end": end_frame,
            "phase": phase,
            "context": f"Batch {i+1}: {purpose[:30]}..."
        })
        remaining -= batch_actions
    
    return batch_plan


# ==================== Batch Generation Nodes ====================

def batch_planner_node(state: ActionBatchSkillGenerationState) -> Dict[str, Any]:
    """Plan batches for current track"""
    track_plan = state.get("track_plan", [])
    current_index = state.get("current_track_index", 0)
    skeleton = state.get("skill_skeleton", {})
    
    if current_index >= len(track_plan):
        return {"messages": [AIMessage(content="All tracks planned")]}
    
    track_item = track_plan[current_index]
    track_name = track_item.get("trackName", f"Track_{current_index}")
    purpose = track_item.get("purpose", "")
    estimated_actions = track_item.get("estimatedActions", 5)
    total_duration = skeleton.get("totalDuration", 180)
    
    batch_plan = calculate_batch_plan(track_name, estimated_actions, total_duration, purpose)
    initial_context = create_initial_context(track_item, skeleton, batch_plan)
    
    logger.info(f"Planned {len(batch_plan)} batches for track {track_name}")
    
    return {
        "current_track_batch_plan": batch_plan,
        "current_batch_index": 0,
        "current_track_actions": [],
        "batch_context": initial_context,
        "messages": [AIMessage(content=f"Track {track_name}: {len(batch_plan)} batches planned")]
    }


def batch_generator_node(state: ActionBatchSkillGenerationState, writer: StreamWriter) -> Dict[str, Any]:
    """Generate actions for current batch"""
    from ..prompts.prompt_manager import get_prompt_manager
    
    batch_plan = state.get("current_track_batch_plan", [])
    batch_index = state.get("current_batch_index", 0)
    track_plan = state.get("track_plan", [])
    current_track_idx = state.get("current_track_index", 0)
    skeleton = state.get("skill_skeleton", {})
    context = state.get("batch_context", {})
    used_action_types = state.get("used_action_types", [])
    
    if batch_index >= len(batch_plan):
        return {"messages": [AIMessage(content="All batches generated")]}
    
    batch_item = batch_plan[batch_index]
    track_item = track_plan[current_track_idx] if current_track_idx < len(track_plan) else {}
    track_name = track_item.get("trackName", "Unknown")
    purpose = track_item.get("purpose", "")
    
    logger.info(f"Generating batch {batch_index + 1}/{len(batch_plan)} for {track_name}")
    emit_batch_progress(ProgressEventType.BATCH_STARTED, f"Batch {batch_index + 1}", state)
    
    track_type = infer_track_type(track_name)
    action_schemas = search_actions_by_track_type(
        track_type, purpose, top_k=5,
        suggested_types=context.get("suggested_types"),
        used_types=used_action_types,
        batch_context=batch_item.get("context")
    )
    
    if not action_schemas:
        action_schemas = get_default_actions_for_track_type(track_type)
    
    prompt_mgr = get_prompt_manager()
    prompt = prompt_mgr.get_prompt("batch_generation")
    
    context_text = format_context_for_prompt(context)
    
    prompt_inputs = {
        "track_name": track_name,
        "batch_index": batch_index + 1,
        "total_batches": len(batch_plan),
        "action_count": batch_item.get("action_count", 3),
        "frame_start": batch_item.get("frame_start", 0),
        "frame_end": batch_item.get("frame_end", 60),
        "phase": batch_item.get("phase", "main"),
        "context": context_text,
        "action_schemas": format_action_schemas_for_prompt(action_schemas),
        "total_duration": skeleton.get("totalDuration", 180)
    }
    
    api_start_time = time.time()
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
        
        logger.info(f"Batch generation took: {time.time() - api_start_time:.2f}s")
        
        json_content = extract_json_from_markdown(full_content)
        batch_data = json.loads(json_content)
        
        actions = batch_data.get("actions", batch_data if isinstance(batch_data, list) else [])
        
        emit_batch_progress(ProgressEventType.BATCH_COMPLETED, f"Batch {batch_index + 1} done", state)
        
        return {
            "current_batch_actions": actions,
            "messages": [AIMessage(content=f"Batch {batch_index + 1}: {len(actions)} actions generated")]
        }
        
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        return {
            "current_batch_actions": [],
            "messages": [AIMessage(content=f"Batch generation failed: {str(e)}")]
        }


def batch_accumulator_node(state: ActionBatchSkillGenerationState) -> Dict[str, Any]:
    """Accumulate batch actions and update context"""
    batch_actions = state.get("current_batch_actions", [])
    track_actions = list(state.get("current_track_actions", []))
    batch_plan = state.get("current_track_batch_plan", [])
    batch_index = state.get("current_batch_index", 0)
    context = state.get("batch_context", {})
    
    track_actions.extend(batch_actions)
    new_context = update_context_after_batch(context, batch_actions, batch_plan, batch_index + 1)
    
    return {
        "current_track_actions": track_actions,
        "current_batch_index": batch_index + 1,
        "batch_context": new_context,
        "messages": [AIMessage(content=f"Batch {batch_index + 1} accumulated: {len(batch_actions)} actions")]
    }


def track_assembler_node(state: ActionBatchSkillGenerationState) -> Dict[str, Any]:
    """Assemble track from all batches"""
    track_actions = state.get("current_track_actions", [])
    track_plan = state.get("track_plan", [])
    current_index = state.get("current_track_index", 0)
    generated_tracks = list(state.get("generated_tracks", []))
    used_action_types = list(state.get("used_action_types", []))
    skeleton = state.get("skill_skeleton", {})
    
    track_item = track_plan[current_index] if current_index < len(track_plan) else {}
    track_name = track_item.get("trackName", f"Track_{current_index}")
    
    track_data = {
        "trackName": track_name,
        "enabled": True,
        "actions": track_actions
    }
    
    errors = validate_track(track_data, skeleton.get("totalDuration", 180))
    
    if not errors:
        generated_tracks.append(track_data)
        for action in track_actions:
            action_type = extract_action_type_name(action.get("parameters", {}).get("_odin_type", ""))
            if action_type and action_type not in used_action_types:
                used_action_types.append(action_type)
    
    return {
        "generated_tracks": generated_tracks,
        "current_track_index": current_index + 1,
        "current_track_errors": errors,
        "used_action_types": used_action_types,
        "messages": [AIMessage(content=f"Track {track_name} assembled: {len(track_actions)} actions")]
    }


# ==================== Conditional Functions ====================

def should_continue_batch_loop(state: ActionBatchSkillGenerationState) -> Literal["next_batch", "assemble_track"]:
    """Determine next step in batch loop"""
    batch_index = state.get("current_batch_index", 0)
    batch_plan = state.get("current_track_batch_plan", [])
    
    if batch_index >= len(batch_plan):
        return "assemble_track"
    return "next_batch"


def should_continue_track_loop(state: ActionBatchSkillGenerationState) -> Literal["next_track", "assemble_skill"]:
    """Determine next step in track loop"""
    current_index = state.get("current_track_index", 0)
    track_plan = state.get("track_plan", [])
    
    if current_index >= len(track_plan):
        return "assemble_skill"
    return "next_track"


# Re-export from progressive for compatibility
__all__ = [
    "ActionBatchSkillGenerationState",
    "calculate_batch_plan",
    "batch_planner_node",
    "batch_generator_node",
    "batch_accumulator_node",
    "track_assembler_node",
    "should_continue_batch_loop",
    "should_continue_track_loop",
    # Re-exported from progressive
    "skeleton_generator_node",
    "skeleton_fixer_node",
    "should_continue_to_track_generation",
    "skill_assembler_node",
    "finalize_progressive_node",
    "should_finalize_or_fail",
    "extract_action_type_name",
]
