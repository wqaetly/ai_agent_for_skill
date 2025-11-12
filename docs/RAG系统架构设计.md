# RAG 系统架构设计文档

## 系统概览

RAG (Retrieval-Augmented Generation) 系统是一个基于Unity的AI辅助技能设计系统，通过向量检索和语义分析为策划人员提供智能的Action推荐和约束验证。

### 核心指标

- **代码规模**: ~8,318 行
- **核心文件**: 16 个
- **通信端口**: 127.0.0.1:8765
- **主要语言**: C# (Unity)
- **AI服务**: Python RAG + DeepSeek LLM

---

## 四层架构设计

### 1. 通信层 (Transport Layer)

负责与Python RAG服务的通信，提供运行时和编辑器双模式支持。

#### 核心组件

| 组件 | 类型 | 特性 | 代码行数 |
|------|------|------|---------|
| `RAGClient` | Runtime | 协程 + WWW | 353 |
| `EditorRAGClient` | Editor | UniTask + HttpClient | 382 |

#### API端点

```
GET  /health          - 健康检查
POST /search          - 向量语义检索
POST /recommend       - Action推荐
POST /index           - 文档索引
GET  /stats           - 统计信息
POST /clear-cache     - 清除缓存
```

#### 通信特性

- **异步处理**: 不阻塞Unity主线程
- **连接监控**: 1秒间隔Ping检测
- **错误处理**: 超时和异常捕获
- **缓存策略**: 本地缓存优化性能

---

### 2. 编辑器集成层 (Editor Integration Layer)

提供策划友好的可视化界面和工作流程。

#### 主要窗口

##### **SkillRAGWindow** (1,132行)
三标签查询界面：

- **Tab 0: 技能搜索** - 向量检索查询
- **Tab 1: Action推荐** - 语义相似度 + 增强处理
- **Tab 2: 索引管理** - 文档索引控制

##### **DescriptionManagerWindow** (1,476行)
六步完整工作流：

```
1. 扫描    → 自动发现所有Action类型
2. 生成    → DeepSeek AI自动生成描述
3. 编辑    → 策划手动优化描述
4. 保存    → ScriptableObject持久化
5. 导出    → JSON格式导出
6. 索引    → 提交到RAG服务
```

##### **SmartActionInspector**
在Action编辑器中直接集成推荐建议，实现编辑流程无缝衔接。

#### 自动初始化

```csharp
[InitializeOnLoad]
public class RAGEditorIntegration
{
    static RAGEditorIntegration()
    {
        // 编辑器启动时自动初始化
        EditorApplication.delayCall += Initialize;
    }
}
```

---

### 3. 语义处理层 (Semantic Processing Layer)

核心的语义分析和约束验证引擎。

#### 三层语义结构 (PED模型)

```csharp
ActionSemanticInfo {
    // Purpose - 使用意图
    intents: string[]        // 使用场景
    scenarios: string[]      // 应用情境
    keywords: string[]       // 关键词标签

    // Effect - 实际效果
    primaryEffect: string    // 主要效果类型
    targetType: string       // 作用目标
    rangeType: string        // 作用范围

    // Dependency - 逻辑约束
    prerequisites: string[]   // 前置依赖
    incompatibles: string[]   // 互斥关系
    synergies: string[]       // 协同增强
    followUps: string[]       // 后续推荐
}
```

#### 核心组件职责

##### **ActionSemanticRegistry** (417行)
- **模式**: Singleton
- **职责**: 全局语义配置管理
- **特性**: 支持JSON热加载
- **默认配置**:
  - 4个内置Action (Damage/Heal/Shield/Movement)
  - 5条内置规则 (互斥/前置/协同)

##### **ActionConstraintValidator** (多维度验证)
```csharp
ValidateConstraints() {
    1. 检查互斥关系 (incompatibles)
    2. 检查前置依赖 (prerequisites)
    3. 匹配意图关键词 (intents/keywords)
    → ValidationResult { is_valid, issues[] }
}
```

##### **ActionRecommendationScorer** (综合评分)
```csharp
CalculateFinalScore() {
    similarity_score  // 从RAG服务获取
    frequency_penalty // 使用频率惩罚
    business_priority // 业务优先级

    finalScore = similarity × (1 - penalty) × sWeight
                 + priority × bWeight
}
```

##### **ActionRecommendationExplainer** (365行)
生成人类可读的推荐解释：

- **理由** (reasons): 为什么推荐
- **警告** (warnings): 潜在问题
- **建议** (suggestions): 使用建议
- **参考** (references): 相关案例

##### **ActionRecommendationEnhancer** (Facade门面)
整合完整推荐流程：

```
原始推荐
  → 评分 (Scorer)
  → 验证 (Validator)
  → 解释 (Explainer)
  → 排序和过滤
  → 增强推荐
```

---

### 4. 数据管理层 (Data Management Layer)

#### ScriptableObject持久化

```csharp
ActionDescriptionDatabase : ScriptableObject
  ├─ descriptions: List<ActionDescriptionData>
  ├─ version: string
  └─ lastModified: DateTime
```

#### JSON导出格式

```json
{
  "actions": [
    {
      "action_name": "Damage",
      "category": "Combat",
      "description": "造成伤害",
      "usage_scenarios": ["战斗", "技能"],
      "keywords": ["攻击", "伤害"]
    }
  ]
}
```

---

## 关键设计模式

### 模式应用总览

| 设计模式 | 应用组件 | 解决问题 |
|---------|---------|---------|
| **Singleton** | ActionSemanticRegistry<br>ActionRecommendationEnhancer | 全局配置管理<br>统一服务入口 |
| **Facade** | ActionRecommendationEnhancer | 简化复杂推荐流程 |
| **InitializeOnLoad** | RAGEditorIntegration | 自动初始化服务 |
| **Chain of Responsibility** | 约束验证流程 | 多级验证链 |
| **Strategy** | 评分算法 | 可配置权重策略 |
| **Repository** | ActionDescriptionDatabase | 数据持久化抽象 |

### Singleton实现细节

```csharp
public class ActionSemanticRegistry
{
    private static ActionSemanticRegistry _instance;
    public static ActionSemanticRegistry Instance
    {
        get
        {
            if (_instance == null)
                _instance = LoadOrCreateDefault();
            return _instance;
        }
    }

    // 支持热加载
    public void ReloadFromFile() { ... }
}
```

---

## 完整数据流

### Action推荐流程

```
┌──────────────────────────────────────────────────────────────┐
│ 1. 用户输入上下文 (SkillRAGWindow)                            │
│    "需要一个群体治疗技能"                                      │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ 2. EditorRAGClient → Python RAG服务                          │
│    POST /recommend { query, top_k, context }                 │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ 3. 向量检索 + 语义相似度计算                                  │
│    返回原始推荐: [                                            │
│      { action_name, similarity: 0.85 },                       │
│      { action_name, similarity: 0.72 },                       │
│      ...                                                      │
│    ]                                                          │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ 4. ActionRecommendationEnhancer.Enhance()                    │
│                                                               │
│    ┌─────────────────────────────────────┐                  │
│    │ 4.1 Scorer: 计算综合得分            │                  │
│    │   - 语义相似度 × 权重               │                  │
│    │   - 业务优先级 × 权重               │                  │
│    │   → finalScore                      │                  │
│    └─────────────────────────────────────┘                  │
│                 │                                             │
│    ┌─────────────────────────────────────┐                  │
│    │ 4.2 Validator: 约束验证             │                  │
│    │   - 检查互斥关系                    │                  │
│    │   - 检查前置依赖                    │                  │
│    │   - 匹配意图关键词                  │                  │
│    │   → is_valid + validation_issues    │                  │
│    └─────────────────────────────────────┘                  │
│                 │                                             │
│    ┌─────────────────────────────────────┐                  │
│    │ 4.3 Explainer: 生成解释             │                  │
│    │   - reasons: 推荐理由               │                  │
│    │   - warnings: 潜在问题              │                  │
│    │   - suggestions: 使用建议           │                  │
│    │   - references: 参考案例            │                  │
│    └─────────────────────────────────────┘                  │
│                 │                                             │
│    ┌─────────────────────────────────────┐                  │
│    │ 4.4 排序和过滤                      │                  │
│    │   - 按finalScore排序                │                  │
│    │   - 过滤无效推荐                    │                  │
│    └─────────────────────────────────────┘                  │
│                                                               │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ 5. 增强推荐结果                                               │
│    [                                                          │
│      EnhancedActionRecommendation {                           │
│        action_name: "GroupHeal",                              │
│        original_similarity: 0.85,                             │
│        final_score: 0.92,                                     │
│        is_valid: true,                                        │
│        reasons: ["匹配群体治疗场景", "高相似度"],             │
│        warnings: ["需要消耗大量魔法值"],                      │
│        suggestions: ["搭配魔法回复技能使用"],                 │
│        validation_issues: []                                  │
│      },                                                       │
│      ...                                                      │
│    ]                                                          │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────────┐
│ 6. UI展示 (SkillRAGWindow)                                   │
│    - 推荐卡片展示                                             │
│    - 得分、理由、警告可视化                                   │
│    - 一键应用到技能配置                                       │
└──────────────────────────────────────────────────────────────┘
```

### 描述管理工作流

```
扫描 → 生成 → 编辑 → 保存 → 导出 → 索引
 │      │      │      │      │      │
 │      │      │      │      │      └─→ POST /index
 │      │      │      │      └────────→ JSON文件
 │      │      │      └───────────────→ ScriptableObject
 │      │      └──────────────────────→ 策划手动优化
 │      └─────────────────────────────→ DeepSeek AI生成
 └────────────────────────────────────→ 反射扫描Action类型
```

---

## 性能优化策略

### 查询优化
- **HashMap索引**: O(1) 复杂度查找语义信息
- **本地缓存**: 频繁访问数据缓存在内存
- **延迟加载**: 按需加载大型配置文件

### 异步处理
```csharp
// 编辑器模式：UniTask不阻塞
async UniTask<SearchResult> SearchAsync(string query)

// 运行时模式：协程支持
IEnumerator SearchCoroutine(string query, Action<SearchResult> callback)
```

### 连接池管理
- 1秒间隔Ping检测服务可用性
- 连接失败自动重试机制
- 超时限制防止长时间阻塞

---

## 技术栈

### Unity端
- **C# 语言**: .NET Framework
- **异步框架**: UniTask (编辑器) + Coroutine (运行时)
- **HTTP客户端**: HttpClient + UnityWebRequest
- **数据序列化**: JsonUtility (考虑迁移Newtonsoft.Json)
- **持久化**: ScriptableObject

### Python端 (RAG服务)
- **向量数据库**: (未明确，推测Chroma/Pinecone)
- **LLM服务**: DeepSeek API
- **Web框架**: (推测Flask/FastAPI)
- **端口**: 127.0.0.1:8765

---

## 核心优势

### 1. 架构清晰
- **四层分离**: 通信、集成、语义、数据各司其职
- **单一职责**: 每个组件职责明确
- **低耦合**: 通过接口和门面解耦

### 2. 语义完整
- **PED三层模型**: Purpose-Effect-Dependency覆盖全方位
- **多维约束**: 互斥、前置、协同、后续全面验证
- **可解释性**: 不只推荐结果，还有推荐理由

### 3. 用户友好
- **六步工作流**: 从扫描到索引一站式完成
- **可视化界面**: 三标签窗口直观操作
- **Inspector集成**: 编辑流程无缝衔接

### 4. 扩展性强
- **JSON配置**: 热加载支持动态调整
- **Strategy模式**: 评分算法可插拔
- **API标准化**: RESTful接口易于扩展

---

## 技术债务与改进建议

### 当前技术债务

#### 1. 代码重复 (Critical)
```csharp
// RAGClient.cs 和 EditorRAGClient.cs 重复定义
[Serializable]
public class SearchResult { ... }

// 建议：提取到共享的 RAGDataModels.cs
```

#### 2. JSON序列化限制 (High)
```csharp
// Unity JsonUtility 不支持多态和复杂类型
// 建议：迁移到 Newtonsoft.Json
using Newtonsoft.Json;
```

#### 3. 服务发现硬编码 (Medium)
```csharp
// 当前硬编码
private const string serverUrl = "http://127.0.0.1:8765";

// 建议：配置化或服务发现
public class RAGServerConfig : ScriptableObject
{
    public string serverUrl;
    public int timeout;
}
```

#### 4. 测试覆盖不足 (High)
- 缺少单元测试
- 缺少集成测试
- 缺少语义约束验证的测试用例

#### 5. 日志系统不完善 (Low)
```csharp
// 建议：统一日志系统
public static class RAGLogger
{
    public static void LogQuery(string query, float latency);
    public static void LogError(string operation, Exception ex);
}
```

### 改进优先级

| 优先级 | 改进项 | 预期收益 |
|--------|--------|----------|
| P0 | 提取共享数据模型基类 | 减少50%代码重复 |
| P0 | 完整单元测试覆盖 | 提升稳定性 |
| P1 | 迁移Newtonsoft.Json | 支持复杂类型 |
| P1 | 服务发现机制 | 提升部署灵活性 |
| P2 | 统一日志系统 | 改善可维护性 |
| P2 | 性能监控埋点 | 识别性能瓶颈 |

---

## 核心文件清单

```
总计：16个文件，~8,318行代码
绝对路径：E:\Study\wqaetly\ai_agent_for_skill\ai_agent_for_skill\Assets\Scripts\RAGSystem\

按重要性排序：

【编辑器窗口】
1. DescriptionManagerWindow.cs               (1,476行) - 六步工作流主窗口
2. SkillRAGWindow.cs                          (1,132行) - 三标签查询UI
3. SmartActionInspector.cs                    (行数未明) - Inspector集成

【语义处理】
4. ActionRecommendationExplainer.cs           (365行)   - 解释生成
5. ActionSemanticRegistry.cs                  (417行)   - 配置管理Singleton
6. ActionConstraintValidator.cs               (新文件)  - 约束验证
7. ActionSemanticModels.cs                    (新文件)  - 语义数据模型
8. ActionRecommendationEnhancer.cs            (行数未明) - Facade门面

【通信客户端】
9. RAGClient.cs                               (353行)   - 运行时HTTP客户端
10. EditorRAGClient.cs                        (382行)   - 编辑器异步客户端

【数据管理】
11. ActionDescriptionDatabase.cs              (行数未明) - ScriptableObject持久化
12. ActionDescriptionData.cs                  (行数未明) - 单个描述数据项
13. ActionExportModels.cs                     (行数未明) - JSON导出格式

【编辑器集成】
14. RAGEditorIntegration.cs                   (行数未明) - InitializeOnLoad入口

【工具类】
15. DescriptionManagerWindow相关支持文件      (多个)    - UI辅助和数据处理
```

---

## 总结

RAG系统是一个**架构清晰、设计完善**的AI辅助技能设计系统。其核心价值在于：

1. **三层语义结构 (PED模型)** - 全面覆盖使用意图、实际效果和逻辑约束
2. **多维度约束验证** - 互斥、前置、协同、后续关系完整验证
3. **可解释推荐** - 不仅推荐结果，更有理由、警告和建议
4. **完整工作流** - 从扫描到索引一站式完成

当前主要改进空间在于**代码复用**（提取共享基类）和**测试覆盖**（补充单元测试）。整体设计具备良好的**扩展性**和**可维护性**，架构决策合理，值得在此基础上持续迭代优化。

---

**文档版本**: v1.0
**最后更新**: 2025-11-10
**维护者**: RAG System Team
