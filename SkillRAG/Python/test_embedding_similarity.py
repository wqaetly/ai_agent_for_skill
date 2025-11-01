"""
测试嵌入模型对中文关键词的相似度计算
验证为什么"位移"会推荐AudioAction
"""

import yaml
import logging
from embeddings import EmbeddingGenerator
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def test_similarity():
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 初始化嵌入生成器
    embedding_gen = EmbeddingGenerator(config.get('embedding', {}))

    # 测试查询
    query = "位移"

    # 模拟Action的searchText
    audio_search_text = """Action类型: AudioAction
显示名称: 音频效果
分类: Other
参数: frame, duration, enabled, audioClipName, volume, pitch, loop, is3D, positionOffset"""

    movement_search_text = """Action类型: MovementAction
显示名称: 位移
分类: Other
参数: movementType, movementSpeed, targetPosition, useRelativePosition, arcHeight"""

    control_search_text = """Action类型: ControlAction
显示名称: 控制效果
分类: Other
参数: controlType, controlDuration, controlStrength"""

    print("="*80)
    print(f"查询: \"{query}\"")
    print("="*80)

    # 生成嵌入
    query_emb = embedding_gen.encode(query, use_cache=False, prompt_name="query")
    audio_emb = embedding_gen.encode(audio_search_text, use_cache=False)
    movement_emb = embedding_gen.encode(movement_search_text, use_cache=False)
    control_emb = embedding_gen.encode(control_search_text, use_cache=False)

    # 计算相似度
    audio_sim = cosine_similarity(query_emb, audio_emb)
    movement_sim = cosine_similarity(query_emb, movement_emb)
    control_sim = cosine_similarity(query_emb, control_emb)

    # 打印结果
    results = [
        ("AudioAction (音频效果)", audio_sim),
        ("MovementAction (位移)", movement_sim),
        ("ControlAction (控制效果)", control_sim),
    ]

    # 排序
    results.sort(key=lambda x: x[1], reverse=True)

    print("\n语义相似度排名:")
    print("-"*80)
    for i, (name, sim) in enumerate(results, 1):
        print(f"{i}. {name:40s} 相似度: {sim:.4f}")

    # 测试更多查询
    print("\n\n" + "="*80)
    print("测试更多查询")
    print("="*80)

    test_queries = [
        "移动",
        "冲刺",
        "音效",
        "播放声音",
        "控制",
        "眩晕"
    ]

    for test_query in test_queries:
        q_emb = embedding_gen.encode(test_query, use_cache=False, prompt_name="query")

        audio_s = cosine_similarity(q_emb, audio_emb)
        movement_s = cosine_similarity(q_emb, movement_emb)
        control_s = cosine_similarity(q_emb, control_emb)

        results = [
            ("Audio", audio_s),
            ("Movement", movement_s),
            ("Control", control_s),
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        print(f"\n查询: \"{test_query}\"")
        print(f"  排名: {results[0][0]} ({results[0][1]:.3f}) > {results[1][0]} ({results[1][1]:.3f}) > {results[2][0]} ({results[2][1]:.3f})")


if __name__ == "__main__":
    test_similarity()
