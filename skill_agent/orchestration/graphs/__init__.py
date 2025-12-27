"""
LangGraph orchestration graphs
"""

# 基础技能生成图
from .skill_generation import (
    build_skill_generation_graph,
    get_skill_generation_graph,
    generate_skill,
    generate_skill_sync,
)

# Track 式渐进技能生成图
from .progressive_skill_generation import (
    build_progressive_skill_generation_graph,
    get_progressive_skill_generation_graph,
    generate_skill_progressive,
    generate_skill_progressive_sync,
)

# Action 批量式技能生成图
from .action_batch_skill_generation import (
    build_action_batch_skill_generation_graph,
    get_action_batch_skill_generation_graph,
    generate_skill_action_batch,
    generate_skill_action_batch_sync,
)

# 并行渐进式技能生成图 - 使用 Send API 实现 Track 并行生成
from .parallel_progressive_skill_generation import (
    build_parallel_progressive_graph,
    get_parallel_progressive_graph,
    generate_skill_parallel,
    generate_skill_parallel_sync,
    visualize_parallel_graph,
)

# 通用修复子图 - 可复用的验证-修复循环
from .fix_subgraph import (
    create_fix_subgraph,
    get_skeleton_fix_subgraph,
    get_track_fix_subgraph,
)

# Human-in-the-loop 技能生成图
from .hitl_skill_generation import (
    get_hitl_skill_generation_graph,
    start_skill_generation_hitl,
    approve_and_continue,
    get_current_state,
)

# Agentic RAG 图 - 智能检索增强生成
from .agentic_rag import (
    build_agentic_rag_graph,
    get_agentic_rag_graph,
    agentic_rag_query,
    agentic_rag_query_sync,
    agentic_rag_stream,
)

__all__ = [
    # 基础生成
    "build_skill_generation_graph",
    "get_skill_generation_graph",
    "generate_skill",
    "generate_skill_sync",
    # Track 式
    "build_progressive_skill_generation_graph",
    "get_progressive_skill_generation_graph",
    "generate_skill_progressive",
    "generate_skill_progressive_sync",
    # Action 批量式生成图
    "build_action_batch_skill_generation_graph",
    "get_action_batch_skill_generation_graph",
    "generate_skill_action_batch",
    "generate_skill_action_batch_sync",
    # 并行渐进式生成图
    "build_parallel_progressive_graph",
    "get_parallel_progressive_graph",
    "generate_skill_parallel",
    "generate_skill_parallel_sync",
    "visualize_parallel_graph",
    # 通用修复子图
    "create_fix_subgraph",
    "get_skeleton_fix_subgraph",
    "get_track_fix_subgraph",
    # Human-in-the-loop
    "get_hitl_skill_generation_graph",
    "start_skill_generation_hitl",
    "approve_and_continue",
    "get_current_state",
    # Agentic RAG
    "build_agentic_rag_graph",
    "get_agentic_rag_graph",
    "agentic_rag_query",
    "agentic_rag_query_sync",
    "agentic_rag_stream",
]
