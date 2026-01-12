"""
Nodes module - LangGraph workflow nodes for skill generation
"""

# Base utilities
from .base import get_llm, get_openai_client, prepare_payload_text, safe_int
from .base.streaming import get_writer_safe, emit_track_progress, emit_batch_progress, emit_finalize_progress

# Constants
from .constants import (
    DEFAULT_ACTIONS_BY_TRACK_TYPE,
    TRACK_TYPE_KEYWORDS, infer_track_type, get_default_actions_for_track_type,
    SEMANTIC_RULES, TRACK_TYPE_RULES, PHASE_RULES, SEMANTIC_KEYWORD_MAP
)

# Validators
from .validators import (
    validate_skeleton,
    validate_track, validate_track_type_compliance,
    extract_action_type_name, validate_action_matches_track_type, validate_semantic_rules
)

# Context and formatters
from .context import create_initial_context, update_context_after_batch, format_context_for_prompt
from .formatters import format_similar_skills, format_action_schemas_for_prompt

# JSON utilities
from .json_utils import extract_json_from_markdown

# Skill nodes
from .skill_nodes import (
    SkillGenerationState,
    retriever_node,
    generator_node,
    validator_node,
    fixer_node,
    finalize_node,
    should_continue
)

# Progressive skill nodes
from .progressive_skill_nodes import (
    ProgressiveSkillGenerationState,
    skeleton_generator_node,
    skeleton_fixer_node,
    track_generator_node,
    track_validator_node,
    track_accumulator_node,
    skill_assembler_node,
    finalize_progressive_node,
    should_continue_to_track_generation,
    should_continue_track_loop,
    should_finalize_or_fail,
    search_actions_by_track_type,
    format_action_schemas_for_prompt
)

# Action batch skill nodes
from .action_batch_skill_nodes import (
    ActionBatchSkillGenerationState,
    batch_planner_node,
    batch_generator_node,
    batch_accumulator_node,
    track_assembler_node as batch_track_assembler_node,
    should_continue_batch_loop,
    should_continue_track_loop as batch_should_continue_track_loop
)

# Single action skill nodes
from .single_action_skill_nodes import (
    SingleActionProgressiveState,
    action_planner_node,
    single_action_generator_node,
    action_accumulator_node,
    track_assembler_node as single_track_assembler_node,
    should_continue_action_loop,
    should_continue_track_loop as single_should_continue_track_loop
)

# Agentic RAG nodes
from .agentic_rag_nodes import (
    get_skill_retriever_tool,
    generate_query_or_respond,
    grade_documents,
    rewrite_question,
    generate_answer
)

__all__ = [
    # Base
    "get_llm", "get_openai_client", "prepare_payload_text", "safe_int",
    "get_writer_safe", "emit_track_progress", "emit_batch_progress", "emit_finalize_progress",
    # Constants
    "DEFAULT_ACTIONS_BY_TRACK_TYPE", "TRACK_TYPE_KEYWORDS", "infer_track_type",
    "get_default_actions_for_track_type", "SEMANTIC_RULES", "TRACK_TYPE_RULES",
    "PHASE_RULES", "SEMANTIC_KEYWORD_MAP",
    # Validators
    "validate_skeleton", "validate_track", "validate_track_type_compliance",
    "extract_action_type_name", "validate_action_matches_track_type", "validate_semantic_rules",
    # Context/Formatters
    "create_initial_context", "update_context_after_batch", "format_context_for_prompt",
    "format_similar_skills", "format_action_schemas_for_prompt",
    # JSON
    "extract_json_from_markdown",
    # Skill nodes
    "SkillGenerationState", "retriever_node", "generator_node",
    "validator_node", "fixer_node", "finalize_node", "should_continue",
    # Progressive
    "ProgressiveSkillGenerationState", "skeleton_generator_node",
    "skeleton_fixer_node", "track_generator_node", "track_validator_node",
    "track_accumulator_node", "skill_assembler_node", "finalize_progressive_node",
    "should_continue_to_track_generation", "should_continue_track_loop", "should_finalize_or_fail",
    "search_actions_by_track_type", "format_action_schemas_for_prompt",
    # Batch
    "ActionBatchSkillGenerationState", "batch_planner_node", "batch_generator_node",
    "batch_accumulator_node", "batch_track_assembler_node", "should_continue_batch_loop",
    "batch_should_continue_track_loop",
    # Single action
    "SingleActionProgressiveState", "action_planner_node", "single_action_generator_node",
    "action_accumulator_node", "single_track_assembler_node", "should_continue_action_loop",
    "single_should_continue_track_loop",
    # Agentic RAG
    "get_skill_retriever_tool", "generate_query_or_respond", "grade_documents",
    "rewrite_question", "generate_answer",
]
