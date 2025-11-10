"""
MCP Server - 结构化查询工具和资源
为REQ-03提供MCP协议支持
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
    import mcp.server.stdio
except ImportError:
    print("警告: mcp库未安装，请运行: pip install mcp")
    Server = None

from structured_query_engine import StructuredQueryEngine
from chunked_json_store import ChunkedJsonStore
from fine_grained_indexer import FineGrainedIndexer


class StructuredQueryMCPServer:
    """MCP Server - 提供结构化查询能力"""

    def __init__(self):
        if Server is None:
            raise ImportError("需要安装mcp库: pip install mcp")

        self.server = Server("skill-structured-query")
        self.query_engine = StructuredQueryEngine()
        self.json_store = ChunkedJsonStore()
        self.indexer = FineGrainedIndexer()

        # 注册处理器
        self._register_handlers()

    def _register_handlers(self):
        """注册MCP处理器"""

        # ==================== Resources ====================

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """列出可用资源"""
            resources = []

            # 1. 细粒度索引资源
            resources.append(Resource(
                uri="skill://index/fine-grained",
                name="Fine-Grained Skill Index",
                mimeType="application/json",
                description="技能细粒度索引，包含所有Action的路径、行号和参数信息"
            ))

            # 2. 每个技能文件的资源
            index_data = self.indexer.get_index()
            for file_path in index_data["files"].keys():
                file_name = Path(file_path).name
                resources.append(Resource(
                    uri=f"skill://file/{file_name}",
                    name=f"Skill: {file_name}",
                    mimeType="application/json",
                    description=f"技能文件: {file_name}"
                ))

            # 3. 每个技能的Action列表资源
            for file_path, file_index in index_data["files"].items():
                file_name = Path(file_path).name
                skill_name = file_index.get("skill_name", "Unknown")

                for track in file_index.get("tracks", []):
                    for action in track.get("actions", []):
                        action_uri = f"skill://action/{file_name}/{action['json_path']}"
                        resources.append(Resource(
                            uri=action_uri,
                            name=f"{skill_name} - {action['action_type']}",
                            mimeType="application/json",
                            description=action['summary']
                        ))

            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """读取资源内容"""

            # 1. 索引资源
            if uri == "skill://index/fine-grained":
                index_data = self.indexer.get_index()
                return json.dumps(index_data, ensure_ascii=False, indent=2)

            # 2. 技能文件资源
            if uri.startswith("skill://file/"):
                file_name = uri.replace("skill://file/", "")
                skills_dir = Path(self.indexer.skills_dir)
                file_path = skills_dir / file_name

                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    return json.dumps({"error": "文件不存在"})

            # 3. Action资源
            if uri.startswith("skill://action/"):
                parts = uri.replace("skill://action/", "").split("/", 1)
                if len(parts) == 2:
                    file_name, json_path = parts
                    chunk = self.query_engine.get_action_detail(file_name, json_path)

                    if chunk:
                        return json.dumps(chunk, ensure_ascii=False, indent=2)
                    else:
                        return json.dumps({"error": "Action不存在"})

            return json.dumps({"error": "未知资源URI"})

        # ==================== Tools ====================

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """列出可用工具"""
            return [
                Tool(
                    name="query_skills_structured",
                    description=(
                        "结构化查询技能Action。"
                        "支持按Action类型、参数条件筛选。"
                        "查询语法示例:\n"
                        "- 'DamageAction where baseDamage > 200'\n"
                        "- 'baseDamage between 100 and 300'\n"
                        "- 'animationClipName contains Attack'\n"
                        "- 'DamageAction where damageType = Magical and baseDamage > 150'"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "结构化查询字符串"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "最大返回结果数（默认100）",
                                "default": 100
                            },
                            "include_context": {
                                "type": "boolean",
                                "description": "是否包含上下文信息（技能名、轨道名）",
                                "default": True
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_action_statistics",
                    description=(
                        "获取Action参数的统计信息。"
                        "可按Action类型、轨道分组统计参数的min/max/avg值。"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "过滤查询（可选），不指定则统计全部"
                            },
                            "group_by": {
                                "type": "string",
                                "description": "分组字段: action_type 或 track_name",
                                "enum": ["action_type", "track_name"],
                                "default": "action_type"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_action_detail",
                    description=(
                        "获取Action的完整详细信息。"
                        "包含原始JSON数据、行号、上下文等。"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "skill_file": {
                                "type": "string",
                                "description": "技能文件名，如 'FlameShockwave.json'"
                            },
                            "json_path": {
                                "type": "string",
                                "description": "Action的JSONPath，如 'tracks.$rcontent[2].actions.$rcontent[0]'"
                            }
                        },
                        "required": ["skill_file", "json_path"]
                    }
                ),
                Tool(
                    name="rebuild_fine_grained_index",
                    description="重建细粒度索引（当技能文件修改后）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "force": {
                                "type": "boolean",
                                "description": "强制重建所有文件（默认只更新修改的文件）",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="get_cache_stats",
                    description="获取查询缓存的统计信息（命中率、大小等）",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """调用工具"""

            if name == "query_skills_structured":
                query = arguments.get("query")
                limit = arguments.get("limit", 100)
                include_context = arguments.get("include_context", True)

                result = self.query_engine.query(
                    query,
                    limit=limit,
                    include_context=include_context
                )

                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            elif name == "get_action_statistics":
                query = arguments.get("query")
                group_by = arguments.get("group_by", "action_type")

                stats = self.query_engine.get_statistics(
                    query_str=query,
                    group_by=group_by
                )

                return [TextContent(
                    type="text",
                    text=json.dumps(stats, ensure_ascii=False, indent=2)
                )]

            elif name == "get_action_detail":
                skill_file = arguments.get("skill_file")
                json_path = arguments.get("json_path")

                detail = self.query_engine.get_action_detail(skill_file, json_path)

                if detail:
                    return [TextContent(
                        type="text",
                        text=json.dumps(detail, ensure_ascii=False, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Action不存在"})
                    )]

            elif name == "rebuild_fine_grained_index":
                force = arguments.get("force", False)
                stats = self.query_engine.rebuild_index(force=force)

                return [TextContent(
                    type="text",
                    text=json.dumps(stats, ensure_ascii=False, indent=2)
                )]

            elif name == "get_cache_stats":
                stats = self.query_engine.get_cache_stats()

                return [TextContent(
                    type="text",
                    text=json.dumps(stats, ensure_ascii=False, indent=2)
                )]

            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"未知工具: {name}"})
                )]

    async def run(self):
        """运行MCP服务器"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# ==================== 主函数 ====================

async def main():
    """启动MCP Server"""
    server = StructuredQueryMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
