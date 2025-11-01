# 描述管理器使用指南

## 概述

**描述管理器（DescriptionManagerWindow）**是一个统一的工具，整合了Action和技能描述的完整管理流程：

```
AI生成描述 → 保存数据库 → 导出JSON → 重建RAG索引
```

取代了之前分散的三个工具：
- ❌ ActionDescriptionGeneratorWindow（仅生成描述）
- ❌ ActionToJsonExporter（仅导出JSON）
- ❌ RAG窗口管理标签页（仅重建索引）

### 主要功能

✅ **AI批量生成** - 使用DeepSeek自动生成Action描述
✅ **手动编辑** - 直接在窗口中编辑优化描述
✅ **JSON导出** - 自动导出格式正确的JSON文件
✅ **索引重建** - 一键重建RAG向量索引
✅ **一键发布** - 自动完成整个流程
✅ **操作日志** - 实时查看每步操作状态

## 打开描述管理器

**菜单路径**: `技能系统` → `描述管理器`

**快捷方式**: `Ctrl+Shift+D` (待配置)

## 界面布局

窗口采用标签页设计，包含4个主要标签：

### 1. Actions标签

管理所有Action的描述。

**数据库区域**：
- 显示ActionDescriptionDatabase.asset
- 可点击查看数据库详情

**Action列表**：
- 表格形式显示所有Action
- 列包括：类型、显示名称、分类、描述、状态
- 状态：`AI生成` | `手动` | `待生成`

**统计信息**：
```
Action总数: 20
已生成描述: 18
待生成: 2
```

### 2. Skills标签

（开发中）未来将管理技能描述。

### 3. Workflow标签（自动化工作流）

**一键发布流程**：
```
🚀 一键生成并发布所有Action
```
自动完成全部5个步骤，无需人工干预。

**分步操作**：
```
1️⃣ 扫描Actions        - 扫描所有ISkillAction子类
2️⃣ AI生成缺失描述     - 调用DeepSeek生成
3️⃣ 保存到数据库        - 保存到ScriptableObject
4️⃣ 导出JSON文件        - 导出到SkillRAG/Data/Actions/
5️⃣ 重建RAG索引         - 重建向量数据库
```

### 4. Config标签（配置）

**API配置**：
- DeepSeek API Key（默认已配置）

**导出路径**：
- JSON导出目录：`../SkillRAG/Data/Actions`

**数据库路径**：
- `Assets/Data/ActionDescriptionDatabase.asset`

### 5. Logs标签（操作日志）

实时显示所有操作的详细日志：
```
[12:34:56] [扫描] 完成，找到 20 个Action
[12:34:58] [AI生成] 开始生成 2 个Action的描述...
[12:35:10] [成功] AudioAction - 已生成描述 (350 字符)
[12:35:12] [保存] 完成 - 已保存 20 个Action到数据库
```

## 完整工作流

### 方式1: 一键发布（推荐）

适用于首次使用或批量更新。

**步骤**：
1. 打开描述管理器
2. 切换到 **Workflow** 标签
3. 确保RAG服务器正在运行（在RAG查询窗口中启动）
4. 点击 **🚀 一键生成并发布所有Action**
5. 在确认对话框中点击"继续"
6. 等待完成（约1-3分钟，取决于Action数量）
7. 完成！可以在RAG查询窗口中测试搜索

**特点**：
- ✅ 全自动
- ✅ 无需人工干预
- ✅ 自动跳过已有描述
- ✅ 显示详细进度
- ❌ 需要RAG服务器运行

### 方式2: 分步操作

适用于调试或部分更新。

#### 步骤1: 扫描Actions

**操作**: 点击 **1️⃣ 扫描Actions**

**作用**:
- 扫描所有继承自ISkillAction的类
- 从数据库加载现有描述
- 读取源代码准备AI生成

**日志输出**:
```
[扫描] 完成，找到 20 个Action
```

#### 步骤2: AI生成缺失描述

**操作**: 点击 **2️⃣ AI生成缺失描述**

**作用**:
- 仅生成description为空的Action
- 调用DeepSeek API
- 自动生成描述、关键词等

**进度**:
```
AI生成描述
正在生成 AudioAction 的描述... (1/2)
[进度条: ████████░░ 50%]
```

**耗时**: 约1秒/Action（包含API限流延迟）

**注意事项**:
- ⚠️ 生成后请检查结果质量
- ⚠️ 可以手动修改表格中的描述
- ⚠️ 未保存前可以重新生成

#### 步骤3: 保存到数据库

**操作**: 点击 **3️⃣ 保存到数据库**

**作用**:
- 将Action列表中的数据保存到ActionDescriptionDatabase.asset
- 自动标记修改时间和修改人
- 清理已删除的Action

**确认对话框**:
```
保存成功
已保存 20 个Action的描述到数据库

下一步: 点击【导出JSON文件】
```

#### 步骤4: 导出JSON文件

**操作**: 点击 **4️⃣ 导出JSON文件**

**作用**:
- 读取数据库
- 为每个Action生成独立的JSON文件
- 包含完整的参数信息、约束、默认值等

**导出位置**: `E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/Actions/`

**文件格式**:
```json
AudioAction.json:
{
  "version": "1.0",
  "exportTime": "2025-11-01T14:30:00",
  "action": {
    "typeName": "AudioAction",
    "displayName": "音频效果",
    "category": "Audio",
    "description": "AudioAction是Unity技能系统中专门用于控制音效播放...",
    "searchText": "音频效果\nAudioAction是Unity...\n关键词: 音频效果,音效播放...",
    "parameters": [...]
  }
}
```

**验证方法**:
- 打开JSON文件检查`description`字段是否有完整内容
- 检查`searchText`是否包含description

#### 步骤5: 重建RAG索引

**操作**: 点击 **5️⃣ 重建RAG索引**

**前置条件**:
- ✅ RAG服务器必须正在运行
- ✅ JSON文件已导出

**作用**:
- 调用RAG服务器的`/rebuild_index`端点
- 重新构建Action和技能的向量索引
- 清除旧索引数据

**进度**:
```
重建RAG索引
正在重建Action和技能索引...
[进度条不确定]
```

**完成提示**:
```
索引重建成功

RAG索引已更新:

Action: 20 个
技能: 15 个

✅ 现在可以在RAG查询窗口中测试搜索了！
```

## 常见问题

### Q1: "AI生成失败"

**可能原因**:
1. DeepSeek API Key失效或配额用完
2. 网络连接问题
3. 源代码读取失败

**解决方法**:
1. 检查Config标签中的API Key
2. 查看Logs标签中的详细错误
3. 确保Action脚本文件存在且可读
4. 单独测试失败的Action（在Action列表中点击"AI生成描述"按钮）

### Q2: "JSON导出后description仍为空"

**可能原因**:
- 忘记执行步骤3（保存到数据库）

**解决方法**:
1. 检查Action列表中描述是否已填充
2. 确保已点击"保存到数据库"
3. 查看Assets/Data/ActionDescriptionDatabase.asset是否已更新
4. 重新执行步骤4（导出JSON）

### Q3: "重建索引失败"

**可能原因**:
1. RAG服务器未运行
2. 服务器端口冲突
3. JSON文件格式错误

**解决方法**:
1. 打开RAG查询窗口，点击"启动服务器"
2. 确认服务器状态为绿色"● 服务器运行中"
3. 检查Logs标签中的错误信息
4. 验证JSON文件格式（用JSON验证器）

### Q4: "一键发布卡在某个步骤"

**排查步骤**:
1. 查看Logs标签中最后一条日志
2. 检查Unity Console是否有错误
3. 检查RAG服务器日志（如果卡在重建索引）
4. 按Esc键取消操作
5. 改用分步操作逐步调试

## 最佳实践

### 1. 首次使用

```
Step 1: 确保RAG服务器运行
Step 2: 使用"一键发布"
Step 3: 在RAG查询窗口测试搜索
Step 4: 根据搜索结果质量调整描述
```

### 2. 新增Action后

```
Step 1: 打开描述管理器
Step 2: 点击"扫描Actions"（会自动检测新Action）
Step 3: 点击"AI生成缺失描述"（仅生成新Action）
Step 4: 检查生成质量，手动优化
Step 5: 点击"保存到数据库"
Step 6: 点击"导出JSON文件"
Step 7: 点击"重建RAG索引"
```

### 3. 优化现有描述

```
Step 1: 在Actions标签的列表中直接编辑描述
Step 2: 点击"保存到数据库"
Step 3: 点击"导出JSON文件"
Step 4: 点击"重建RAG索引"
```

### 4. 批量修改后

使用"一键发布"确保所有步骤都执行。

## 与旧工具的对比

| 功能 | 旧方式 | 新方式（描述管理器） |
|------|-------|-------------------|
| 生成描述 | ActionDescriptionGeneratorWindow | 集成在Actions标签 |
| 导出JSON | Tools > Skill RAG > Export Actions | Workflow标签，步骤4 |
| 重建索引 | RAG查询窗口 > 管理标签页 | Workflow标签，步骤5 |
| 完整流程 | 需要打开3个窗口，6次点击 | 一键发布，1次点击 |
| 日志查看 | Unity Console | Logs标签，持久化显示 |
| 状态跟踪 | 无 | 实时统计，状态列 |

## 快捷操作

### 键盘快捷键（待实现）

- `Ctrl+R` - 扫描Actions
- `Ctrl+G` - AI生成
- `Ctrl+S` - 保存数据库
- `Ctrl+E` - 导出JSON
- `Ctrl+I` - 重建索引
- `Ctrl+Shift+P` - 一键发布

### 右键菜单（待实现）

在Action列表中：
- 右键 > "重新生成描述"
- 右键 > "复制描述"
- 右键 > "查看源代码"

## 高级用法

### 自定义导出路径

1. 切换到Config标签
2. 修改"JSON导出目录"
3. 确保Python RAG服务器的config.yaml中的路径一致

### 批量替换关键词

直接在数据库资产中：
1. 选择ActionDescriptionDatabase.asset
2. 在Inspector中批量编辑

### 集成到CI/CD

创建Unity Editor脚本：
```csharp
[MenuItem("Tools/CI/Update Action Descriptions")]
public static void UpdateActionDescriptions()
{
    var window = EditorWindow.GetWindow<DescriptionManagerWindow>(false, null, false);
    window.OneClickPublishAllAsync().Forget();
}
```

## 故障排除清单

如果遇到问题，请依次检查：

- [ ] Unity编辑器无报错
- [ ] ActionDescriptionDatabase.asset存在
- [ ] DeepSeek API Key有效
- [ ] RAG服务器运行中
- [ ] JSON文件导出成功（检查文件大小 >0）
- [ ] JSON格式正确（用验证器检查）
- [ ] Python依赖已安装（transformers, chromadb等）
- [ ] 向量数据库路径可访问

## 相关文档

- [RAG推荐逻辑修复](.claude/docs/rag-action-recommendation-fix.md)
- [Action描述AI工作流](.claude/docs/action-description-ai-workflow.md)
- [RAG服务器管理](.claude/docs/rag-server-management.md)

---

**版本**: 1.0.0
**最后更新**: 2025-11-01
**维护者**: Claude Code
