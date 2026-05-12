"""
OpenViking 启发特性的单元测试

测试模块:
- layered_context: 分层上下文系统
- retrieval_trace: 检索轨迹可视化
- user_preference: 用户偏好记忆
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 测试模块导入
from core.layered_context import (
    LayeredContext, 
    SkillContextGenerator, 
    LayeredContextCache
)
from core.retrieval_trace import (
    RetrievalTracer, 
    RetrievalStage, 
    RetrievalTrace,
    TraceStorage,
    format_trace_for_display
)
from core.user_preference import (
    PreferenceMemory, 
    UserPreference, 
    ActionUsage
)


class TestRetrievalTrace:
    """检索轨迹测试"""
    
    def test_tracer_basic_flow(self):
        """测试基本的轨迹记录流程"""
        tracer = RetrievalTracer(query="测试查询")
        
        # 记录查询理解阶段
        tracer.start_stage(RetrievalStage.QUERY_UNDERSTANDING, {'query': '测试查询'})
        tracer.end_stage({'expanded': ['测试', '查询']}, {'intent': 'search'})
        
        # 记录向量检索阶段
        tracer.start_stage(RetrievalStage.VECTOR_SEARCH)
        tracer.end_stage({'results': ['r1', 'r2', 'r3']}, {'count': 3})
        
        # 完成轨迹
        trace = tracer.finalize(results_count=3)
        
        assert trace.original_query == "测试查询"
        assert len(trace.stages) == 2
        assert trace.final_results_count == 3
        assert trace.total_duration_ms > 0
    
    def test_tracer_record_stage(self):
        """测试直接记录阶段"""
        tracer = RetrievalTracer(query="直接记录测试")
        
        tracer.record_stage(
            stage=RetrievalStage.HYBRID_FUSION,
            input_data={'vector_results': 10, 'bm25_results': 8},
            output_data={'results': ['r1', 'r2']},
            duration_ms=15.5
        )
        
        trace = tracer.get_trace()
        assert len(trace.stages) == 1
        assert trace.stages[0].stage == "hybrid_fusion"
        assert trace.stages[0].duration_ms == 15.5
    
    def test_trace_to_mermaid(self):
        """测试 Mermaid 图生成"""
        tracer = RetrievalTracer(query="Mermaid测试")
        tracer.start_stage(RetrievalStage.QUERY_UNDERSTANDING)
        tracer.end_stage({'expanded': ['test']})
        tracer.start_stage(RetrievalStage.VECTOR_SEARCH)
        tracer.end_stage({'results': ['r1']})
        trace = tracer.finalize(1)
        
        mermaid = trace.to_mermaid()
        
        assert "flowchart TD" in mermaid
        assert "query_understanding" in mermaid
        assert "vector_search" in mermaid
    
    def test_trace_storage(self):
        """测试轨迹存储"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = TraceStorage(storage_path=tmpdir, max_traces=5)
            
            # 添加多个轨迹
            for i in range(7):
                tracer = RetrievalTracer(query=f"查询{i}")
                tracer.start_stage(RetrievalStage.VECTOR_SEARCH)
                tracer.end_stage({'results': []})
                trace = tracer.finalize(0)
                storage.save(trace)
            
            # 检查最大数量限制
            recent = storage.get_recent(10)
            assert len(recent) == 5  # max_traces=5
            
            # 检查统计
            stats = storage.get_statistics()
            assert stats['count'] == 5


class TestUserPreference:
    """用户偏好测试"""
    
    @pytest.fixture
    def temp_storage(self):
        """创建临时存储目录"""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir)
    
    def test_record_action_usage(self, temp_storage):
        """测试记录 Action 使用"""
        memory = PreferenceMemory(storage_path=temp_storage, user_id="test_user")
        
        memory.record_action_usage(
            action_type="PlayAnimationAction",
            params={"animationName": "attack", "speed": 1.0},
            context="近战攻击技能"
        )
        
        summary = memory.get_preference_summary()
        assert summary['total_interactions'] == 1
        assert len(summary['top_actions']) == 1
        assert summary['top_actions'][0][0] == "PlayAnimationAction"
    
    def test_get_recommended_actions(self, temp_storage):
        """测试 Action 推荐"""
        memory = PreferenceMemory(storage_path=temp_storage, user_id="test_user")
        
        # 记录多次使用
        for _ in range(5):
            memory.record_action_usage("PlayAnimationAction", context="攻击")
        for _ in range(3):
            memory.record_action_usage("CreateVFXAction", context="特效")
        memory.record_action_usage("PlaySoundAction", context="音效")
        
        # 获取推荐
        recommendations = memory.get_recommended_actions(top_k=3)
        
        assert len(recommendations) == 3
        # 使用次数最多的应该排在前面
        assert recommendations[0][0] == "PlayAnimationAction"
        assert recommendations[1][0] == "CreateVFXAction"
    
    def test_action_sequence_prediction(self, temp_storage):
        """测试 Action 序列预测"""
        memory = PreferenceMemory(storage_path=temp_storage, user_id="test_user")
        
        # 记录多个序列
        for _ in range(3):
            memory.record_action_sequence(["A", "B", "C"])
        for _ in range(2):
            memory.record_action_sequence(["A", "B", "D"])
        memory.record_action_sequence(["A", "X", "Y"])
        
        # 预测下一个 Action
        predictions = memory.get_next_action_prediction(["A", "B"])
        
        assert len(predictions) > 0
        # C 出现 3 次，D 出现 2 次，所以 C 的概率更高
        assert predictions[0][0] == "C"


class TestLayeredContext:
    """分层上下文测试"""
    
    def test_skill_context_generator(self):
        """测试技能上下文生成"""
        generator = SkillContextGenerator()
        
        # 模拟技能数据
        skill_data = {
            'id': 'skill_001',
            'name': '火球术',
            'total_duration': 60,
            'tracks': [
                {
                    'name': 'Main',
                    'enabled': True,
                    'actions': [
                        {'frame': 0, 'type': 'PlayAnimationAction'},
                        {'frame': 10, 'type': 'CreateVFXAction'},
                        {'frame': 20, 'type': 'DamageAction'},
                    ]
                }
            ]
        }
        
        # 生成 L0 摘要
        l0 = generator.generate_l0_abstract(skill_data)
        assert len(l0) > 0
        assert '火球术' in l0 or 'skill' in l0.lower()
        
        # 生成 L1 概览
        l1 = generator.generate_l1_overview(skill_data)
        assert 'overview' in l1 or '概' in l1 or len(l1) > len(l0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

