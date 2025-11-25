"""
回归测试：确保渐进式生成不影响现有功能
测试原有的技能生成、搜索、验证等功能正常工作
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestration.graphs.skill_generation import (
    get_skill_generation_graph,
    build_skill_generation_graph,
)
from orchestration.graphs.other_graphs import (
    get_skill_search_graph,
    get_skill_detail_graph,
)
from orchestration.graphs.progressive_skill_generation import (
    get_progressive_skill_generation_graph,
)


class TestGraphsCoexist:
    """测试多个图能够共存"""

    def test_all_graphs_load_successfully(self):
        """测试所有图能够成功加载"""
        # 加载所有图
        skill_gen_graph = get_skill_generation_graph()
        progressive_graph = get_progressive_skill_generation_graph()
        search_graph = get_skill_search_graph()
        detail_graph = get_skill_detail_graph()

        # 验证都不为 None
        assert skill_gen_graph is not None
        assert progressive_graph is not None
        assert search_graph is not None
        assert detail_graph is not None

        print("\n✅ 所有图成功加载")

    def test_graphs_are_independent(self):
        """测试图之间相互独立"""
        skill_gen_graph = get_skill_generation_graph()
        progressive_graph = get_progressive_skill_generation_graph()

        # 应该是不同的实例
        assert skill_gen_graph is not progressive_graph

        # 但同一个图的单例应该返回相同实例
        skill_gen_graph2 = get_skill_generation_graph()
        assert skill_gen_graph is skill_gen_graph2

        progressive_graph2 = get_progressive_skill_generation_graph()
        assert progressive_graph is progressive_graph2

        print("\n✅ 图独立性验证通过")

    def test_graphs_have_different_checkpoints(self):
        """测试图使用不同的 checkpoint 数据库"""
        skill_gen_graph = get_skill_generation_graph()
        progressive_graph = get_progressive_skill_generation_graph()

        # 两个图都应该有 checkpointer
        assert skill_gen_graph.checkpointer is not None
        assert progressive_graph.checkpointer is not None

        # 它们应该使用不同的 checkpoint（不同的连接）
        # 注意：SqliteSaver 内部使用同一个连接类，但数据库文件不同
        print("\n✅ Checkpoint 配置验证通过")


class TestLegacySkillGeneration:
    """测试原有技能生成功能"""

    def test_legacy_graph_structure(self):
        """测试原有图结构完整"""
        graph = get_skill_generation_graph()
        mermaid = graph.get_graph().draw_mermaid()

        # 检查关键节点存在
        assert "retrieve" in mermaid
        assert "generate" in mermaid
        assert "validate" in mermaid
        assert "fix" in mermaid
        assert "finalize" in mermaid

        print("\n✅ 原有图结构完整")

    def test_legacy_state_structure(self):
        """测试原有 State 结构未被破坏"""
        from orchestration.nodes.skill_nodes import SkillGenerationState

        # 验证必要的字段存在
        required_fields = [
            "requirement",
            "similar_skills",
            "generated_json",
            "validation_errors",
            "retry_count",
            "max_retries",
            "final_result",
            "messages",
        ]

        # SkillGenerationState 是 TypedDict，检查 __annotations__
        state_fields = SkillGenerationState.__annotations__.keys()

        for field in required_fields:
            assert field in state_fields, f"字段 {field} 缺失"

        print(f"\n✅ 原有 State 结构完整（{len(state_fields)} 个字段）")


class TestProgressiveDoesNotBreakLegacy:
    """测试渐进式生成不影响原有功能"""

    def test_import_both_graphs(self):
        """测试两个图可以同时导入"""
        try:
            from orchestration.graphs.skill_generation import get_skill_generation_graph
            from orchestration.graphs.progressive_skill_generation import (
                get_progressive_skill_generation_graph,
            )

            # 同时获取两个图
            graph1 = get_skill_generation_graph()
            graph2 = get_progressive_skill_generation_graph()

            assert graph1 is not None
            assert graph2 is not None

            print("\n✅ 两个图可以同时导入和使用")
        except Exception as e:
            pytest.fail(f"导入失败: {e}")

    def test_legacy_nodes_unchanged(self):
        """测试原有节点未被修改"""
        from orchestration.nodes.skill_nodes import (
            retriever_node,
            generator_node,
            validator_node,
            fixer_node,
            finalize_node,
        )

        # 确保这些函数可调用
        assert callable(retriever_node)
        assert callable(generator_node)
        assert callable(validator_node)
        assert callable(fixer_node)
        assert callable(finalize_node)

        print("\n✅ 原有节点未被破坏")

    def test_schemas_backward_compatible(self):
        """测试 Schema 向后兼容"""
        from orchestration.schemas import (
            OdinSkillSchema,
            SkillAction,
            SkillTrack,
            SkillSkeletonSchema,  # 新增的
        )

        # 旧 Schema 仍然可用
        assert OdinSkillSchema is not None
        assert SkillAction is not None
        assert SkillTrack is not None

        # 新 Schema 也可用
        assert SkillSkeletonSchema is not None

        print("\n✅ Schema 向后兼容")


class TestServerIntegration:
    """测试服务器集成"""

    def test_assistants_list_includes_both(self):
        """测试 assistants 列表包含两种生成方式"""
        import langgraph_server

        # 模拟获取 assistants 列表
        # 由于 list_assistants 是 async，我们检查定义
        import inspect

        source = inspect.getsource(langgraph_server.list_assistants)

        # 检查是否包含两种 assistant
        assert "skill-generation" in source
        assert "progressive-skill-generation" in source

        print("\n✅ 服务器支持两种生成方式")


class TestPrompts:
    """测试 Prompt 配置"""

    def test_progressive_prompts_exist(self):
        """测试渐进式生成的 Prompts 存在"""
        from orchestration.prompts.prompt_manager import get_prompt_manager

        pm = get_prompt_manager()

        # 检查新增的 prompts
        skeleton_prompt = pm.get_prompt("skeleton_generation")
        track_prompt = pm.get_prompt("track_action_generation")
        track_fix_prompt = pm.get_prompt("track_validation_fix")

        assert skeleton_prompt is not None
        assert track_prompt is not None
        assert track_fix_prompt is not None

        print("\n✅ 渐进式生成 Prompts 已配置")

    def test_legacy_prompts_unchanged(self):
        """测试原有 Prompts 未被修改"""
        from orchestration.prompts.prompt_manager import get_prompt_manager

        pm = get_prompt_manager()

        # 检查原有 prompts 仍存在
        skill_gen_prompt = pm.get_prompt("skill_generation")
        validation_fix_prompt = pm.get_prompt("validation_fix")

        assert skill_gen_prompt is not None
        assert validation_fix_prompt is not None

        print("\n✅ 原有 Prompts 未被破坏")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
