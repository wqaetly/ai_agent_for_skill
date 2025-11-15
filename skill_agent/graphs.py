"""
LangGraph CLI 入口点
为 langgraph dev 提供编译后的 graph 实例
"""

# 加载 .env 文件中的环境变量（必须在导入其他模块之前）
from dotenv import load_dotenv
import os
# 确保从正确的路径加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path, override=True)

# 验证关键环境变量是否加载
if not os.getenv("DEEPSEEK_API_KEY"):
    raise ValueError(f"DEEPSEEK_API_KEY 环境变量未设置！请检查 .env 文件: {env_path}")

from orchestration import (
    get_skill_generation_graph,
    get_skill_search_graph,
    get_skill_detail_graph,
    get_skill_validation_graph,
    get_parameter_inference_graph,
)

# 导出编译后的 graph 实例
skill_generation = get_skill_generation_graph()
skill_search = get_skill_search_graph()
skill_detail = get_skill_detail_graph()
skill_validation = get_skill_validation_graph()
parameter_inference = get_parameter_inference_graph()
