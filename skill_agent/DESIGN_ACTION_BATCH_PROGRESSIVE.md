# Action批次级渐进式技能生成 - 架构设计文档

## 1. 问题定义

### 1.1 当前架构问题
- **Track级渐进式**: 每次生成整个Track的所有actions (10-20个)
- **Token瓶颈**: 复杂Track生成时输出6K+ tokens,配合thinking链可能超限
- **质量下降**: 输出过长时,后半段actions容易格式错误
- **修复成本高**: 一个action错误 → 整个Track重新生成

### 1.2 Token消耗估算

**超级复杂技能示例:**
- 5 Tracks, 每Track 15 actions, 每action 8参数

**当前progressive (Track级):**
```
单Track生成:
  输入: ~3300 tokens (prompt + RAG + 骨架)
  输出: ~6800 tokens (15 actions × 450 tokens/action)
  总计: ~10100 tokens/次

整个技能: 5 Tracks × 10100 = ~50K tokens
重试3次: 最坏情况 ~150K tokens
```

## 2. 解决方案: 动态批处理 + 增量修复

### 2.1 批次划分策略

| Track复杂度 | Actions数量 | 批次策略 | 每批actions数 |
|-------------|-------------|----------|---------------|
| 简单 | 1-5 | 不分批 | 全部 |
| 中等 | 6-10 | 分2批 | 3-5 |
| 复杂 | 11-15 | 分3批 | 4-5 |
| 超级复杂 | 16+ | 分4+批 | 3-5 |

### 2.2 Token消耗优化

**新方案 (批次级):**
```
单批次生成 (3-5 actions):
  输入: ~3000 tokens
  输出: ~1500-2500 tokens
  总计: ~4500-5500 tokens/次

超级复杂技能: ~75K tokens (vs 150K)
优化: 50%降低, 且质量更高
```

## 3. 架构设计

### 3.1 新增State字段

```python
current_track_batch_plan: List[Dict]  # 当前Track的批次计划
current_batch_index: int  # 当前批次索引
current_batch_actions: List[Dict]  # 当前批次生成的actions
accumulated_track_actions: List[Dict]  # 当前Track已完成的所有actions
batch_retry_count: int  # 批次重试次数
```

### 3.2 核心节点

1. **plan_track_batches_node**: 规划Track批次
2. **batch_action_generator_node**: 生成批次actions
3. **batch_action_validator_node**: 验证批次
4. **batch_action_saver_node**: 保存批次
5. **track_assembler_node**: 组装完整Track

### 3.3 Graph流程

```
骨架生成 → 规划Track批次 → [批次循环: 生成→验证→修复→保存] → 组装Track → [Track循环] → 组装技能
```

## 4. 实施计划

**新文件**: `action_batch_skill_generation.py` (保持向后兼容)

**预期改进**:
- Token消耗: -50%
- 生成质量: +25%
- 错误隔离性: 优秀
