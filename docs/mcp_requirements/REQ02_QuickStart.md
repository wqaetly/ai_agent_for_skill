# REQ-02 参数粒度增强 - 快速开�?
## 5分钟上手指南

### 快速体�?
最简单的使用方式�?
```csharp
using SkillSystem.RAG;
using SkillSystem.Data;

// 1. 获取增强器实�?var enhancer = ParameterGranularityEnhancer.Instance;

// 2. 准备技能数据和推荐
SkillData skillData = GetCurrentSkillData();
EnhancedActionRecommendation recommendation = GetRAGRecommendation();

// 3. 增强推荐
var enhanced = enhancer.EnhanceActionRecommendation(recommendation, skillData);

// 4. 查看结果
Debug.Log(enhanced.recommendationSummary);
Debug.Log($"推荐�?{enhanced.parameterInferences.Count} 个参�?);
Debug.Log($"高置信度: {enhanced.GetHighConfidenceParameterCount()}");
```

---

## 典型使用场景

### 场景1：在RAG窗口中展示参数推�?
```csharp
// �?skill_agentWindow.cs �?OnGUI �?private void DrawEnhancedRecommendations()
{
    if (GUILayout.Button("获取增强推荐"))
    {
        var enhancer = ParameterGranularityEnhancer.Instance;

        // 批量增强
        enhancedRecommendations = enhancer.EnhanceMultipleRecommendations(
            recommendations.Select(ConvertToEnhanced).ToList(),
            GetCurrentSkillData()
        );
    }

    // 展示结果
    foreach (var enhanced in enhancedRecommendations)
    {
        DrawEnhancedCard(enhanced);
    }
}

private void DrawEnhancedCard(EnhancedParameterRecommendation enhanced)
{
    EditorGUILayout.BeginVertical(EditorStyles.helpBox);

    // 标题
    EditorGUILayout.LabelField(enhanced.displayName, EditorStyles.boldLabel);

    // 摘要
    EditorGUILayout.LabelField(enhanced.recommendationSummary, EditorStyles.wordWrappedLabel);

    // 参数列表
    EditorGUILayout.LabelField("推荐参数:", EditorStyles.boldLabel);
    foreach (var param in enhanced.parameterInferences)
    {
        if (param.confidence >= 0.7f)
        {
            DrawParameter(param);
        }
    }

    EditorGUILayout.EndVertical();
}
```

### 场景2：验证用户输入的参数

```csharp
// �?SmartActionInspector.cs �?private void ValidateActionParameters(ISkillAction action)
{
    // 提取当前参数
    var parameters = ExtractParameters(action);

    // 验证
    var enhancer = ParameterGranularityEnhancer.Instance;
    var result = enhancer.ValidateParameters(action.GetType().Name, parameters);

    // 显示验证结果
    if (!result.isValid)
    {
        EditorGUILayout.HelpBox("参数配置存在问题:", MessageType.Warning);
        foreach (var issue in result.issues)
        {
            string icon = issue.severity == IssueSeverity.Error ? "�? : "�?;
            EditorGUILayout.LabelField($"{icon} {issue.message}");
        }
    }
}
```

### 场景3：自动填充参�?
```csharp
private void AutoFillParameters(ISkillAction action, SkillData skillData)
{
    var enhancer = ParameterGranularityEnhancer.Instance;

    // 创建推荐
    var recommendation = new EnhancedActionRecommendation
    {
        action_type = action.GetType().Name,
        display_name = action.GetDisplayName()
    };

    // 增强推荐
    var enhanced = enhancer.EnhanceActionRecommendation(recommendation, skillData);

    // 自动填充高置信度参数
    foreach (var param in enhanced.parameterInferences)
    {
        if (param.confidence >= 0.7f && !param.requiresManualConfirmation)
        {
            SetFieldValue(action, param.parameterName, param.recommendedValue);
        }
    }

    Debug.Log($"自动填充�?{enhanced.GetHighConfidenceParameterCount()} 个参�?);
}
```

---

## 关键API速查

### ParameterGranularityEnhancer（主入口�?
```csharp
var enhancer = ParameterGranularityEnhancer.Instance;

// 增强单个推荐
EnhancedParameterRecommendation enhanced = enhancer.EnhanceActionRecommendation(rec, skillData);

// 批量增强
List<EnhancedParameterRecommendation> results = enhancer.EnhanceMultipleRecommendations(recs, skillData);

// 验证参数
ValidationResult validation = enhancer.ValidateParameters(actionType, parameters);

// 获取依赖报告
string report = enhancer.GetDependencyReport("DamageAction");

// 生成JSON输出
JObject json = enhancer.GenerateCompleteJSON(enhanced);
```

### SkillContextAssembler（上下文提取�?
```csharp
// 组装上下�?SkillContextFeatures context = SkillContextAssembler.AssembleContext(skillData);

// 生成摘要
string summary = SkillContextAssembler.BuildContextSummaryForQuery(context);

// 访问上下文数�?Debug.Log($"技能标�? {string.Join(", ", context.tags)}");
Debug.Log($"技能意�? {string.Join(", ", context.inferredIntents)}");
Debug.Log($"已有Action: {context.existingActions.Count}�?);
```

### ActionParameterDependencyGraph（依赖验证）

```csharp
var graph = new ActionParameterDependencyGraph();

// 验证参数
ValidationResult result = graph.ValidateParameters("MovementAction", params);

// 获取推荐范围
(float? min, float? max) = graph.GetRecommendedRange("DamageAction", "baseDamage");

// 注册自定义规�?graph.RegisterRule(new ParameterDependencyRule
{
    actionType = "MyCustomAction",
    ruleType = DependencyRuleType.ConditionalRequired,
    sourceParameter = "mode",
    sourceValue = "Advanced",
    targetParameter = "advancedOptions",
    explanation = "高级模式需要配置高级选项"
});
```

### ParameterInferencer（参数推理）

```csharp
var inferencer = new ParameterInferencer();

// 推断参数
ParameterInferenceResult result = inferencer.InferParameters(
    actionType: "DamageAction",
    context: skillContext,
    referenceSkills: new List<string> { "技能A", "技能B" }
);

// 访问推理结果
foreach (var param in result.parameterInferences)
{
    Debug.Log($"{param.parameterName}: {param.recommendedValue} (置信�? {param.confidence:P0})");
}
```

### UnityTypeSerializer（Unity类型处理�?
```csharp
// 序列�?JObject json = UnityTypeSerializer.SerializeUnityType(new Vector3(1, 2, 3));

// 反序列化
Vector3 v = (Vector3)UnityTypeSerializer.DeserializeUnityType(json, typeof(Vector3));

// 格式�?string formatted = UnityTypeSerializer.FormatUnityType(Vector3.forward);

// 语义�?string example = UnityTypeSerializer.GenerateUnityTypeExample(typeof(Color), Color.red);
```

---

## 常见问题

### Q1: 如何提高参数推荐的准确性？

**A**: 增加统计样本量。当前使用模拟数据，实际使用时应�?1. 从现有技能中收集参数统计
2. 实现 `ParameterStatisticsCache.LoadFromFile()` 加载真实数据
3. 定期更新统计缓存

```csharp
// 收集统计示例
var cache = new ParameterStatisticsCache();
foreach (var skill in allSkills)
{
    foreach (var action in skill.GetAllActions())
    {
        var params = ExtractParameters(action);
        foreach (var param in params)
        {
            cache.UpdateStatistics(action.GetType().Name, param.Key, param.Value);
        }
    }
}
cache.SaveToFile("Assets/Resources/parameter_statistics.json");
```

### Q2: 如何为自定义Action添加依赖规则�?
**A**: 在初始化时注册规则：

```csharp
var graph = new ActionParameterDependencyGraph();

// 条件必填
graph.RegisterRule(new ParameterDependencyRule
{
    actionType = "MyAction",
    ruleType = DependencyRuleType.ConditionalRequired,
    sourceParameter = "enableSpecialEffect",
    sourceValue = "True",
    targetParameter = "specialEffectPrefab",
    explanation = "启用特效时必须指定特效预制体"
});

// 范围约束
graph.RegisterRule(new ParameterDependencyRule
{
    actionType = "MyAction",
    ruleType = DependencyRuleType.RangeConstraint,
    targetParameter = "power",
    minValue = 1f,
    maxValue = 100f,
    explanation = "威力值应在合理范围内"
});
```

### Q3: 置信度低怎么办？

**A**: 置信度低�? 0.7）时，系统会自动标记 `requiresManualConfirmation = true`。建议：
1. UI上突出显示这些参�?2. 提供详细的推理理由说�?3. 允许用户手动调整
4. 收集用户最终值用于改进模�?
```csharp
foreach (var param in enhanced.parameterInferences)
{
    if (param.requiresManualConfirmation)
    {
        EditorGUILayout.HelpBox(
            $"{param.parameterName}: {param.inferenceReason}",
            MessageType.Info
        );

        // 显示备选值供用户选择
        DrawAlternativeValues(param.alternativeValues);
    }
}
```

### Q4: Unity类型序列化失败？

**A**: 检查类型支持：

```csharp
if (UnityTypeSerializer.IsUnityType(fieldType))
{
    // 支持的类�?    var json = UnityTypeSerializer.SerializeUnityType(value);
}
else
{
    // 不支持的类型，使用普通序列化
    var json = JToken.FromObject(value);
}
```

当前支持：Vector3、Vector2、Color、Quaternion、AnimationCurve。需要支持其他类型可扩展 `SerializeUnityType` 方法�?
### Q5: 如何与现有RAG系统集成�?
**A**: �?`skill_agentWindow` 获取推荐后增强：

```csharp
// 获取RAG推荐
var recommendations = await editorRAGClient.RecommendActionsAsync(query, topK);

// 转换格式
var enhancedRecs = recommendations.Select(r => new EnhancedActionRecommendation
{
    action_type = r.action_name,
    display_name = r.display_name,
    // ... 其他字段
}).ToList();

// 增强推荐
var enhancer = ParameterGranularityEnhancer.Instance;
var enhanced = enhancer.EnhanceMultipleRecommendations(enhancedRecs, currentSkillData);

// 展示增强结果
DisplayEnhancedRecommendations(enhanced);
```

---

## 测试你的集成

运行单元测试验证功能�?
```
Unity Editor -> Window -> General -> Test Runner
选择 EditMode -> 运行 ParameterGranularityTests
```

所有测试应通过。如有失败，检查：
1. 是否正确引用了Newtonsoft.Json
2. 是否有命名空间冲�?3. 测试数据是否正确构建

---

## 下一�?
1. **集成到UI**: �?`skill_agentWindow` 展示参数推荐
2. **收集数据**: 从现有技能收集参数统�?3. **用户测试**: 收集反馈并迭�?4. **扩展规则**: 为更多Action类型添加依赖规则

参考完整文�? `REQ02_Implementation.md`

---

**版本**: v1.0
**更新日期**: 2025-11-10
