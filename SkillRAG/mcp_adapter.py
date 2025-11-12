"""
MCP Adapter（极简版）
薄适配层，负责 MCP 协议 ↔ LangGraph 的桥接

职责：
1. 监听 MCP Stdio 协议
2. 解析工具调用请求
3. 路由到对应的 LangGraph 图
4. 返回结果

代码量：约 100 行
"""

import asyncio
import json
import logging
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 导入 LangGraph 图
from SkillRAG.orchestration import (
    get_skill_generation_graph,
    get_skill_search_graph,
    get_skill_detail_graph,
    get_skill_validation_graph,
    get_parameter_inference_graph,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MCP Server 初始化 ====================

app = Server("skillrag-server")

# ==================== 工具定义 ====================

TOOLS = [
    Tool(
        name="generate_skill",
        description="生成技能配置（支持自动验证和循环修复）",
        inputSchema={
            "type": "object",
            "properties": {
                "requirement": {"type": "string", "description": "技能需求描述"},
                "max_retries": {"type": "integer", "default": 3, "description": "最大重试次数"}
            },
            "required": ["requirement"]
        }
    ),
    Tool(
        name="search_skills",
        description="语义搜索技能配置",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"},
                "filters": {"type": "object", "description": "过滤条件（可选）"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="validate_skill",
        description="验证并修复技能配置 JSON",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_json": {"type": "string", "description": "技能配置 JSON 字符串"},
                "max_retries": {"type": "integer", "default": 3, "description": "最大修复次数"}
            },
            "required": ["skill_json"]
        }
    ),
    Tool(
        name="infer_parameters",
        description="推理技能参数值",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "技能名称"},
                "skill_type": {"type": "string", "description": "技能类型（Attack/Heal/Buff/Debuff）"},
                "action_list": {"type": "array", "items": {"type": "string"}, "description": "Action 列表"}
            },
            "required": ["skill_name", "skill_type", "action_list"]
        }
    ),
    Tool(
        name="get_skill_detail",
        description="获取技能详细配置",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id": {"type": "string", "description": "技能 ID"}
            },
            "required": ["skill_id"]
        }
    )
]

# ==================== MCP 协议处理 ====================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """
    调用工具（路由到 LangGraph 图）

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        MCP TextContent 列表
    """
    logger.info(f"调用工具: {name}, 参数: {arguments}")

    try:
        # 路由到对应的 LangGraph 图
        if name == "generate_skill":
            graph = get_skill_generation_graph()
            initial_state = {
                "requirement": arguments["requirement"],
                "max_retries": arguments.get("max_retries", 3),
                "similar_skills": [],
                "generated_json": "",
                "validation_errors": [],
                "retry_count": 0,
                "final_result": {},
                "messages": [],
            }
            result = await graph.ainvoke(initial_state)
            output = result["final_result"]

        elif name == "search_skills":
            graph = get_skill_search_graph()
            initial_state = {
                "query": arguments["query"],
                "top_k": arguments.get("top_k", 5),
                "filters": arguments.get("filters"),
                "results": []
            }
            result = await graph.ainvoke(initial_state)
            output = result["results"]

        elif name == "validate_skill":
            graph = get_skill_validation_graph()
            initial_state = {
                "skill_json": arguments["skill_json"],
                "validation_errors": [],
                "fixed_json": "",
                "retry_count": 0,
                "max_retries": arguments.get("max_retries", 3),
                "final_result": {}
            }
            result = await graph.ainvoke(initial_state)
            output = {
                "validation_errors": result.get("validation_errors", []),
                "fixed_json": result.get("fixed_json", result["skill_json"]),
                "retry_count": result.get("retry_count", 0)
            }

        elif name == "infer_parameters":
            graph = get_parameter_inference_graph()
            initial_state = {
                "skill_name": arguments["skill_name"],
                "skill_type": arguments["skill_type"],
                "action_list": arguments["action_list"],
                "result": {}
            }
            result = await graph.ainvoke(initial_state)
            output = result["result"]

        elif name == "get_skill_detail":
            graph = get_skill_detail_graph()
            initial_state = {
                "skill_id": arguments["skill_id"],
                "result": {}
            }
            result = await graph.ainvoke(initial_state)
            output = result["result"]

        else:
            output = {"error": f"Unknown tool: {name}"}

        # 返回 MCP 格式结果
        return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]

    except Exception as e:
        logger.error(f"工具调用失败: {e}", exc_info=True)
        error_output = {"error": str(e)}
        return [TextContent(type="text", text=json.dumps(error_output))]


# ==================== 主函数 ====================

async def main():
    """启动 MCP Server"""
    logger.info("启动 SkillRAG MCP Adapter...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
