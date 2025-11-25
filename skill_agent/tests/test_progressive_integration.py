"""
渐进式技能生成集成测试（使用真实 LLM API）
测试完整的三阶段生成流程，收集性能指标

运行前确保：
1. DEEPSEEK_API_KEY 已设置
2. RAG 索引已初始化
"""

import pytest
import sys
import os
import time
import json
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from orchestration.graphs.progressive_skill_generation import (
    get_progressive_skill_generation_graph,
    generate_skill_progressive_sync,
)


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="需要 DEEPSEEK_API_KEY 环境变量"
)
class TestProgressiveIntegration:
    """集成测试：真实 LLM 调用"""

    def test_simple_skill_generation(self):
        """测试简单技能生成（1-2 tracks）"""
        requirement = "生成一个简单的近战攻击技能，只需要动画和伤害效果"

        start_time = time.time()

        # 调用渐进式生成
        result = generate_skill_progressive_sync(
            requirement=requirement,
            similar_skills=[],
            max_track_retries=3
        )

        elapsed = time.time() - start_time

        # 打印测试结果
        print(f"\n{'='*60}")
        print(f"简单技能生成测试")
        print(f"{'='*60}")
        print(f"需求：{requirement}")
        print(f"生成耗时：{elapsed:.2f}s")

        # 验证结果
        assert "final_result" in result
        final_skill = result["final_result"]

        print(f"技能名称：{final_skill.get('skillName', 'N/A')}")
        print(f"技能ID：{final_skill.get('skillId', 'N/A')}")
        print(f"轨道数：{len(final_skill.get('tracks', []))}")

        total_actions = sum(
            len(track.get("actions", []))
            for track in final_skill.get("tracks", [])
        )
        print(f"总 Actions：{total_actions}")

        # 打印消息历史（查看阶段进度）
        messages = result.get("messages", [])
        print(f"\n阶段进度消息数：{len(messages)}")
        for i, msg in enumerate(messages[-5:], 1):  # 只显示最后5条
            content = msg.content if hasattr(msg, 'content') else str(msg)
            content_preview = content[:100] if len(content) > 100 else content
            print(f"  {i}. {content_preview}...")

        # 断言验证
        assert final_skill.get("skillName"), "技能名称不能为空"
        assert final_skill.get("skillId"), "技能ID不能为空"
        assert len(final_skill.get("tracks", [])) >= 1, "至少需要1个轨道"
        assert total_actions >= 1, "至少需要1个 action"

        # 性能验证（考虑到 LLM API 延迟，放宽至 180s）
        assert elapsed < 180, f"生成时间 {elapsed:.2f}s 超过 180s 上限"

        print(f"{'='*60}\n")

    @pytest.mark.skip(reason="复杂技能测试耗时较长，默认跳过")
    def test_complex_skill_generation(self):
        """测试复杂技能生成（3+ tracks）"""
        requirement = (
            "生成一个大招技能，包含以下效果："
            "1. 动画：施法动画和技能动画"
            "2. 特效：火焰冲击波和爆炸效果"
            "3. 音效：施法音效、爆炸音效"
            "4. 伤害：范围伤害和持续灼烧"
        )

        start_time = time.time()

        result = generate_skill_progressive_sync(
            requirement=requirement,
            similar_skills=[],
            max_track_retries=3
        )

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"复杂技能生成测试")
        print(f"{'='*60}")
        print(f"需求：{requirement}")
        print(f"生成耗时：{elapsed:.2f}s")

        final_skill = result["final_result"]
        print(f"技能名称：{final_skill.get('skillName', 'N/A')}")
        print(f"轨道数：{len(final_skill.get('tracks', []))}")

        total_actions = sum(
            len(track.get("actions", []))
            for track in final_skill.get("tracks", [])
        )
        print(f"总 Actions：{total_actions}")

        # 轨道详情
        print("\n轨道详情：")
        for track in final_skill.get("tracks", []):
            track_name = track.get("trackName", "Unknown")
            actions_count = len(track.get("actions", []))
            print(f"  - {track_name}: {actions_count} actions")

        # 验证
        assert len(final_skill.get("tracks", [])) >= 3, "复杂技能至少需要3个轨道"
        assert total_actions >= 4, "复杂技能至少需要4个 actions"
        assert elapsed < 180, f"复杂技能生成时间 {elapsed:.2f}s 超过 180s"

        print(f"{'='*60}\n")


class TestCompareGenerationMethods:
    """对比测试：一次性生成 vs 渐进式生成"""

    @pytest.mark.skip(reason="对比测试需要两个生成器都运行，耗时较长")
    def test_compare_generation_quality(self):
        """对比生成质量和性能"""
        from orchestration.graphs.skill_generation import generate_skill_sync

        requirement = "生成一个火焰弹技能，包含动画、特效和伤害"

        # 一次性生成
        print("\n开始一次性生成...")
        start1 = time.time()
        result_legacy = generate_skill_sync(requirement, max_retries=3)
        time1 = time.time() - start1

        # 渐进式生成
        print("开始渐进式生成...")
        start2 = time.time()
        result_progressive = generate_skill_progressive_sync(
            requirement, max_track_retries=3
        )
        time2 = time.time() - start2

        # 对比结果
        print(f"\n{'='*60}")
        print("生成方法对比")
        print(f"{'='*60}")
        print(f"一次性生成耗时：{time1:.2f}s")
        print(f"渐进式生成耗时：{time2:.2f}s")
        print(f"耗时差异：{time2 - time1:.2f}s ({(time2/time1 - 1)*100:+.1f}%)")

        # 对比轨道数和 action 数
        legacy_skill = result_legacy["final_result"]
        progressive_skill = result_progressive["final_result"]

        legacy_tracks = len(legacy_skill.get("tracks", []))
        progressive_tracks = len(progressive_skill.get("tracks", []))

        legacy_actions = sum(
            len(t.get("actions", [])) for t in legacy_skill.get("tracks", [])
        )
        progressive_actions = sum(
            len(t.get("actions", [])) for t in progressive_skill.get("tracks", [])
        )

        print(f"\n一次性生成：{legacy_tracks} tracks, {legacy_actions} actions")
        print(f"渐进式生成：{progressive_tracks} tracks, {progressive_actions} actions")

        print(f"{'='*60}\n")


class TestGraphCheckpoint:
    """测试 checkpoint 持久化和恢复"""

    def test_checkpoint_persistence(self):
        """测试状态持久化"""
        graph = get_progressive_skill_generation_graph()

        # 检查 checkpoint 是否配置
        assert graph.checkpointer is not None, "Graph 应该配置 checkpointer"

        print("\n✅ Checkpoint 持久化已配置")
        print(f"   Checkpointer 类型: {type(graph.checkpointer).__name__}")

    @pytest.mark.skip(reason="中断恢复测试需要手动操作")
    def test_interrupt_and_resume(self):
        """测试中断和恢复（需要手动测试）"""
        # 这个测试需要在 Graph 中设置 interrupt_after 或 interrupt_before
        # 然后手动恢复执行
        pass


if __name__ == "__main__":
    # 运行简单技能测试
    pytest.main([__file__, "-v", "-s", "-k", "test_simple"])
