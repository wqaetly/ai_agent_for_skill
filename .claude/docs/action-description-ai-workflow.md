# Action描述AI生成工作流

## 概述

**新架构**：数据与代码分离，使用DeepSeek AI自动生成高质量的Action描述，策划可视化编辑优化。

### 设计原则

> **"Data and code should be separated. Data should be editable without recompiling."**

- ✅ **数据与代码分离** - 描述信息存储在ScriptableObject中，不硬编码在C#
- ✅ **AI自动生成** - DeepSeek分析源代码，生成高质量语义描述
- ✅ **策划可编辑** - Odin Inspector可视化界面，策划可手动优化AI生成的内容
- ✅ **版本管理友好** - SO资产可纳入Git版本控制

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Unity Editor (Odin)                        │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Action描述管理器窗口                                 │   │
│  │  (ActionDescriptionGeneratorWindow)                   │   │
│  │                                                        │   │
│  │  1. 扫描所有Action类 (反射)                           │   │
│  │  2. 读取源代码                                        │   │
│  │  3. 调用DeepSeek API生成描述                         │   │
│  │  4. 策划可视化编辑                                    │   │
│  │  5. 保存到ScriptableObject                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ActionDescriptionDatabase.asset (SO)                │   │
│  │  - MovementAction: "控制角色位移。支持4种..."        │   │
│  │  - ControlAction: "对目标施加控制效果..."            │   │
│  │  - DamageAction: "对目标造成伤害..."                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ActionToJsonExporter                                 │   │
│  │  - 从SO读取description                               │   │
│  │  - 构建优化的searchText                              │   │
│  │  - 导出JSON文件                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               SkillRAG/Data/Actions/*.json                   │
│  {                                                            │
│    "description": "控制角色位移。支持4种移动类型...",        │
│    "searchText": "位移\n控制角色位移...\n关键词: 移动,冲刺..." │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                 Python RAG System                            │
│  - action_indexer.py 读取JSON                               │
│  - 向量模型嵌入searchText                                   │
│  - 存储到Chroma向量数据库                                   │
│  - 语义搜索推荐Action                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 完整工作流程

### 步骤1: 打开Action描述管理器

```
Unity菜单 → 技能系统 → Action描述管理器
```

窗口界面说明：
- **数据库区域** - 显示当前SO资产，可内联编辑
- **Action列表** - 表格形式显示所有Action及其状态
- **批量操作** - 扫描、AI生成、保存按钮
- **统计信息** - 总数、已生成、待生成计数

### 步骤2: 扫描所有Action

点击 **"扫描所有Action"** 按钮

系统会：
1. 反射获取所有`ISkillAction`子类
2. 读取每个Action的源代码（`.cs`文件）
3. 从数据库加载现有描述（如果有）
4. 显示在表格中

**表格列说明**：
- **Action类型** - 类名（只读）
- **显示名称** - 可编辑（2-4个中文字）
- **分类** - 可编辑（Movement/Control/Damage等）
- **功能描述** - 可编辑（多行文本，150-300字）
- **状态** - AI生成 / 手动编写 / 待生成

### 步骤3: AI生成描述

#### 方式1: 批量生成（推荐首次使用）

点击 **"AI生成所有缺失的描述"** 按钮

系统会：
1. 遍历所有没有描述的Action
2. 为每个Action调用DeepSeek API
3. 传入源代码和提示词
4. 自动填充生成的描述
5. 每个API调用间隔1秒（避免限流）

**注意**：
- 生成过程可能需要几分钟（取决于Action数量）
- 会显示进度条和当前处理的Action
- 失败的会在Console中显示错误

#### 方式2: 单个生成

在表格中，点击某个Action行的 **"AI生成描述"** 按钮

适用场景：
- 单独更新某个Action的描述
- AI生成失败后重试
- 新增Action后单独生成

### 步骤4: 策划手动优化（可选但推荐）

AI生成的描述可能需要优化：

**优化建议**：
1. **增强关键词** - 确保用户常用搜索词都包含
   - 例：MovementAction应包含"位移、移动、冲刺、闪现、跳跃、突进"

2. **强调区别** - 避免与其他Action混淆
   - 例：AnimationAction应强调"纯视觉，不涉及游戏逻辑"

3. **列举场景** - 增加典型使用场景
   - 例："常用于闪现技能、冲锋突进、跳斩等"

4. **中英混合** - 关键术语中英文都写
   - 例："线性移动(Linear)"、"眩晕(Stun)"

**编辑方式**：
- 直接在表格的"功能描述"列编辑（多行文本框）
- 或点击数据库区域，在Inspector中详细编辑

### 步骤5: 保存到数据库

点击 **"保存到数据库"** 按钮

系统会：
1. 将所有Action的描述保存到SO
2. 更新元数据（总数、AI生成数、编辑数）
3. 记录修改时间和修改人
4. 标记资产为Dirty，自动保存

**数据库文件位置**：
```
Assets/Data/ActionDescriptionDatabase.asset
```

### 步骤6: 导出Action JSON

```
Unity菜单 → Tools → Skill RAG → Export Actions to JSON
```

导出器会：
1. 检查数据库是否存在
2. 从SO读取每个Action的描述
3. 构建优化的searchText（displayName + description + keywords）
4. 导出到`SkillRAG/Data/Actions/*.json`

**Console输出示例**：
```
[导出] ✅ MovementAction: 使用数据库描述 (长度: 245)
[导出] ✅ ControlAction: 使用数据库描述 (长度: 312)
[导出] ℹ️ AudioAction: 使用Attribute描述 (Fallback)
✅ 导出完成: 成功 18 个，失败 0 个
```

### 步骤7: 重建RAG索引

```
Unity菜单 → 技能系统 → RAG查询窗口
管理标签页 → 重建索引
```

系统会：
1. Python读取所有Action JSON
2. 提取searchText字段
3. 使用Qwen3生成向量嵌入
4. 存储到Chroma向量数据库

### 步骤8: 测试推荐结果

```
RAG查询窗口 → Action推荐标签页
输入查询词 → 获取推荐
```

**测试案例**：
- 输入"位移" → 应推荐MovementAction第一
- 输入"击飞" → 应推荐ControlAction第一
- 输入"伤害" → 应推荐DamageAction第一

---

## DeepSeek提示词设计

### 提示词结构

系统向DeepSeek发送的提示词包含：

1. **角色定义** - "你是Unity技能系统专家"
2. **任务说明** - 分析源代码，生成结构化描述
3. **源代码** - 完整的Action类C#代码
4. **输出格式** - JSON格式要求
5. **字段规范** - 每个字段的详细编写规范

### description字段规范

```
1. 核心功能（1-2句话）
   - 概括Action的主要功能

2. 详细说明（3-5句话）
   - 支持的参数、模式、配置项
   - 关键enum值和选项

3. 使用场景（1句话）
   - 列举3-5个典型技能示例

4. 关键区别（1句话）
   - 强调与其他Action的不同
   - 例："纯粹位移，不包含伤害和控制效果"

5. 中英混合
   - 关键术语：线性移动(Linear)、眩晕(Stun)
   - 提高搜索匹配率
```

### searchKeywords字段规范

```
包含5-10个关键词，逗号分隔：
- 功能中文词：位移、移动、冲刺、闪现
- 英文术语：movement、teleport、dash
- 典型技能：闪现、跳斩、冲锋
- DOTA2/LOL技能名
```

### 输出示例

```json
{
  "displayName": "位移",
  "category": "Movement",
  "description": "控制角色位移。支持4种移动类型：线性移动(Linear)直线前进、弧线移动(Arc)跳跃式移动、曲线移动(Curve)自定义轨迹、瞬移(Instant)瞬间传送。可配置移动速度、目标位置、相对/绝对坐标、面向方向等。常用于冲刺技能、闪现、跳跃攻击、位移突进等需要改变角色位置的技能。纯粹位移，不包含伤害和控制效果。",
  "searchKeywords": "位移,移动,冲刺,闪现,跳跃,突进,movement,dash,blink,leap,teleport"
}
```

---

## ScriptableObject数据结构

### ActionDescriptionData

单个Action的描述数据：

```csharp
public class ActionDescriptionData
{
    public string typeName;          // Action类名（只读）
    public string namespaceName;     // 命名空间（只读）
    public string displayName;       // 显示名称（可编辑）
    public string category;          // 分类（可编辑）
    public string description;       // 功能描述（可编辑）
    public string searchKeywords;    // 搜索关键词（可编辑）
    public bool isAIGenerated;       // 是否AI生成
    public string aiGeneratedTime;   // AI生成时间
    public string lastModifiedTime;  // 最后修改时间
    public string lastModifiedBy;    // 最后修改人
}
```

### ActionDescriptionDatabase

数据库SO资产：

```csharp
public class ActionDescriptionDatabase : ScriptableObject
{
    public List<ActionDescriptionData> actions;  // 所有Action描述

    // 元数据
    public int totalActions;
    public int aiGeneratedCount;
    public int manuallyEditedCount;
    public string lastUpdateTime;

    // API
    public ActionDescriptionData GetDescriptionByType(string typeName);
    public void AddOrUpdateAction(ActionDescriptionData data);
    public void UpdateMetadata();
    public void CleanupMissingActions(List<string> validTypeNames);
}
```

---

## 数据流对比

### 旧方案（硬编码Attribute）

❌ **问题**：
- 描述硬编码在C#代码中
- 修改需要重新编译
- 策划无法参与编辑
- 没有版本历史

```csharp
[ActionDescription("控制角色位移...")]
public class MovementAction : ISkillAction
{
    // 修改描述 → 修改C#代码 → 重新编译 → 测试
}
```

### 新方案（ScriptableObject + AI）

✅ **优势**：
- 数据与代码分离
- 无需重新编译
- 策划可视化编辑
- Git版本控制
- AI自动生成

```
Action C#源码
    ↓
DeepSeek AI分析
    ↓
生成结构化描述
    ↓
保存到SO资产
    ↓
策划优化编辑
    ↓
导出JSON
    ↓
RAG索引
```

---

## 维护工作流

### 日常场景

#### 场景1: 新增Action

1. 程序创建新Action类（C#代码）
2. 打开Action描述管理器
3. 点击"扫描所有Action"
4. 找到新Action，点击"AI生成描述"
5. 策划审阅优化描述
6. 保存到数据库
7. 导出JSON → 重建索引

#### 场景2: 优化现有描述

1. 打开Action描述管理器
2. 直接编辑表格中的描述
3. 或在数据库Inspector中详细编辑
4. 保存到数据库
5. 导出JSON → 重建索引

#### 场景3: 批量更新

1. 修改DeepSeek提示词（更好的规范）
2. 打开Action描述管理器
3. 删除旧描述（或清空SO）
4. 批量AI生成
5. 策划审阅优化
6. 保存 → 导出 → 重建索引

#### 场景4: 搜索效果不佳

1. 分析用户搜索词
2. 检查对应Action的description
3. 增加缺失的关键词
4. 更新searchKeywords字段
5. 保存 → 导出 → 重建索引

---

## API配置

### DeepSeek API Key

**当前配置**：
```csharp
private const string DEEPSEEK_API_KEY = "sk-e8ec7e0c860d4b7d98ffc4212ab2c138";
```

**修改方式**：
1. 打开`ActionDescriptionGeneratorWindow.cs`
2. 修改常量`DEEPSEEK_API_KEY`
3. 或在窗口界面的"配置"区域修改（Inspector中）

### API调用参数

```csharp
var requestBody = new
{
    model = "deepseek-chat",
    messages = new[] { ... },
    temperature = 0.3,  // 较低温度，保证输出稳定
    max_tokens = 1000
};
```

**参数说明**：
- `model`: DeepSeek Chat模型
- `temperature`: 0.3（低温度，输出更确定性）
- `max_tokens`: 1000（足够生成完整描述）

---

## 故障排查

### 问题1: API调用失败

**症状**：
```
DeepSeek API调用失败: Unauthorized
```

**解决**：
1. 检查API Key是否正确
2. 检查API Key是否过期
3. 检查网络连接
4. 查看Console详细错误信息

### 问题2: 解析响应失败

**症状**：
```
解析DeepSeek响应失败: JSON parse error
```

**解决**：
1. 查看Console中的原始响应
2. 检查DeepSeek是否返回了非JSON内容
3. 可能是提示词导致模型输出格式错误
4. 优化提示词，明确要求JSON格式

### 问题3: 数据库未找到

**症状**：
```
⚠️ 未找到Action描述数据库！
```

**解决**：
1. 首次使用会自动创建
2. 检查路径：`Assets/Data/ActionDescriptionDatabase.asset`
3. 如果误删，重新打开窗口会自动创建

### 问题4: 导出后推荐依然错误

**原因**：
1. 没有重建RAG索引
2. Python缓存了旧数据

**解决**：
```
Unity RAG窗口 → 管理 → 重建索引
```

---

## 最佳实践

### 1. description编写规范

**✅ 好的描述**：
```
控制角色位移。支持4种移动类型：线性移动(Linear)直线前进、弧线移动(Arc)跳跃式移动、曲线移动(Curve)自定义轨迹、瞬移(Instant)瞬间传送。可配置移动速度、目标位置、相对/绝对坐标、面向方向等。常用于冲刺技能、闪现、跳跃攻击、位移突进等需要改变角色位置的技能。纯粹位移，不包含伤害和控制效果。
```

**特点**：
- ✅ 包含核心功能说明
- ✅ 列举所有子类型
- ✅ 中英文混合
- ✅ 典型使用场景
- ✅ 强调区别性

**❌ 差的描述**：
```
用于移动角色。
```

**问题**：
- ❌ 过于简短，信息量不足
- ❌ 没有关键词
- ❌ 无法区分其他Action

### 2. searchKeywords编写规范

**✅ 好的关键词**：
```
位移,移动,冲刺,闪现,跳跃,突进,位移技能,movement,dash,blink,leap,teleport,charge
```

**✅ 好的关键词**：
```
击飞,眩晕,控制,定身,沉默,减速,放逐,banish,stun,silence,root,slow,控制技能,硬控,软控
```

**❌ 差的关键词**：
```
action,skill
```

### 3. 策划优化checklist

策划审阅AI生成的描述时，检查：

- [ ] displayName是否简洁准确（2-4个字）
- [ ] category分类是否合理
- [ ] description是否包含常用搜索词
- [ ] 是否列举了所有子类型/模式
- [ ] 是否有典型使用场景
- [ ] 是否强调了区别性
- [ ] searchKeywords是否包含同义词
- [ ] 中英文关键术语是否都有

---

## 总结

### 核心优势

1. **数据与代码分离** - 策划可独立维护描述
2. **AI自动生成** - 节省人工编写时间
3. **可视化编辑** - Odin Inspector友好界面
4. **版本管理** - SO资产纳入Git
5. **质量保证** - AI + 人工优化

### 工作流总结

```
新增/修改Action
    ↓
扫描Action
    ↓
AI生成描述
    ↓
策划优化编辑
    ↓
保存到数据库
    ↓
导出JSON
    ↓
重建RAG索引
    ↓
测试推荐效果
```

### Linus式点评

> **"This is the right way to do it."**
>
> 数据与代码分离是基本原则。
> 硬编码描述在Attribute里是业余的做法。
> ScriptableObject + AI生成 + 策划编辑 = 专业架构。
>
> **"Tools should be built for the people who use them."**
>
> 程序员写代码，策划写描述，AI辅助生成。
> 各司其职，这才是正确的工具设计。
