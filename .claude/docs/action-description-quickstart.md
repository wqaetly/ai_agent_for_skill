# Action描述AI生成 - 快速开始

## 5分钟快速上手

### 步骤1: 打开管理器（30秒）

```
Unity菜单 → 技能系统 → Action描述管理器
```

### 步骤2: 扫描Action（10秒）

点击按钮：**"扫描所有Action"**

会看到所有Action列表。

### 步骤3: AI生成描述（2-3分钟）

点击按钮：**"AI生成所有缺失的描述"**

等待进度条完成。DeepSeek会自动分析源代码生成描述。

### 步骤4: 保存到数据库（5秒）

点击按钮：**"保存到数据库"**

数据会保存到`Assets/Data/ActionDescriptionDatabase.asset`。

### 步骤5: 导出JSON（10秒）

```
Unity菜单 → Tools → Skill RAG → Export Actions to JSON
点击："导出所有Actions"
```

### 步骤6: 重建索引（1-2分钟）

```
Unity菜单 → 技能系统 → RAG查询窗口
管理标签页 → 点击："重建索引"
```

### 步骤7: 测试（10秒）

```
RAG查询窗口 → Action推荐标签页
输入："位移"
点击："获取推荐"
```

应该看到MovementAction排第一！

---

## 界面速览

### Action描述管理器

```
┌────────────────────────────────────────────────────────┐
│ Action描述管理器                                   [X]  │
├────────────────────────────────────────────────────────┤
│ ┌─ 数据库 ─────────────────────────────────────────┐  │
│ │ ActionDescriptionDatabase.asset                   │  │
│ │ 18个Action | AI生成: 15 | 手动编辑: 3            │  │
│ └──────────────────────────────────────────────────┘  │
│                                                        │
│ ┌─ 配置 ───────────────────────────────────────────┐  │
│ │ DeepSeek API Key: sk-e8ec7e0c860d4b7d...          │  │
│ └──────────────────────────────────────────────────┘  │
│                                                        │
│ ┌─ Action列表 ─────────────────────────────────────┐  │
│ │ Action类型 │显示名称│分类    │功能描述    │状态  │  │
│ │────────────┼────────┼────────┼───────────┼──────│  │
│ │MovementAction│位移  │Movement│控制角色位移│AI生成│  │
│ │ControlAction │控制效果│Control│对目标施加控制│AI生成│  │
│ │ DamageAction │伤害  │Damage  │对目标造成伤害│AI生成│  │
│ │ AudioAction  │音频  │Audio   │           │待生成│  │
│ └──────────────────────────────────────────────────┘  │
│                                                        │
│ ┌─ 批量操作 ───────────────────────────────────────┐  │
│ │ [扫描所有Action] [AI生成所有缺失] [保存到数据库]  │  │
│ └──────────────────────────────────────────────────┘  │
│                                                        │
│ ┌─ 统计信息 ───────────────────────────────────────┐  │
│ │ Action总数: 18 | 已生成: 15 | 待生成: 3          │  │
│ └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 常见问题

### Q: AI生成的描述不满意怎么办？

**A**: 直接在表格中编辑！

1. 双击"功能描述"列的单元格
2. 修改文本
3. 点击"保存到数据库"

### Q: 想重新生成某个Action的描述？

**A**: 单独生成！

1. 找到对应的Action行
2. 清空"功能描述"
3. 点击该行的"AI生成描述"按钮

### Q: 新增Action后如何更新？

**A**: 重新扫描！

1. 点击"扫描所有Action"
2. 新Action会自动出现在列表
3. 点击"AI生成描述"
4. 保存 → 导出 → 重建索引

### Q: API调用失败怎么办？

**A**: 检查以下内容：

1. API Key是否正确
2. 网络连接是否正常
3. 查看Console的详细错误信息
4. DeepSeek服务是否正常

### Q: 推荐结果依然不准确？

**A**: 优化关键词！

1. 打开Action描述管理器
2. 编辑对应Action的描述
3. 增加用户常用的搜索词
4. 更新searchKeywords字段
5. 保存 → 导出 → 重建索引

---

## 高级技巧

### 技巧1: 批量优化描述

如果AI生成的质量不满意：

1. 修改`DeepSeekClient.cs`中的提示词
2. 在管理器中删除所有描述（清空description列）
3. 重新批量生成
4. 策划审阅优化

### 技巧2: 版本控制

ScriptableObject资产可以纳入Git：

```bash
git add Assets/Data/ActionDescriptionDatabase.asset
git commit -m "优化MovementAction的描述，增加关键词"
```

### 技巧3: 多人协作

策划团队可以分工维护：

- 策划A负责Movement/Control类
- 策划B负责Damage/Buff类
- 每次修改后提交Git
- 解决冲突时，保留描述更详细的版本

### 技巧4: 监控推荐质量

定期测试常用搜索词：

```
测试清单：
- 位移 → MovementAction ✓
- 击飞 → ControlAction ✓
- 伤害 → DamageAction ✓
- 治疗 → HealAction ✓
- 音效 → AudioAction ✓
```

如果某个测试失败，说明对应Action的描述需要优化。

---

## 文件清单

### 新增文件

```
Assets/Scripts/SkillSystem/Editor/
├── Data/
│   └── ActionDescriptionData.cs           # SO数据结构
├── DeepSeekClient.cs                      # DeepSeek API客户端
└── ActionDescriptionGeneratorWindow.cs    # Odin编辑器窗口

Assets/Data/
└── ActionDescriptionDatabase.asset        # SO资产（自动创建）

.claude/docs/
├── action-description-ai-workflow.md      # 完整文档
└── action-description-quickstart.md       # 本文件
```

### 修改文件

```
Assets/Scripts/SkillSystem/Editor/
└── ActionToJsonExporter.cs                # 修改为从SO读取数据
```

---

## 依赖检查

确保项目已安装：

- ✅ **Odin Inspector** - 可视化编辑器界面
- ✅ **UniTask** - 异步API调用
- ✅ **UnityWebRequest** - HTTP请求（Unity内置）

如果缺少UniTask：

```
1. Unity Package Manager
2. Add package from git URL
3. 输入: https://github.com/Cysharp/UniTask.git?path=src/UniTask/Assets/Plugins/UniTask
```

---

## 下一步

完成快速开始后，建议：

1. **阅读完整文档** - `.claude/docs/action-description-ai-workflow.md`
2. **优化AI生成的描述** - 策划审阅并手动优化
3. **测试推荐质量** - 收集常用搜索词，验证推荐结果
4. **建立维护流程** - 新增Action后及时更新描述

---

## 获取帮助

遇到问题时：

1. **查看Console** - Unity控制台有详细错误信息
2. **阅读完整文档** - 查看"故障排查"章节
3. **检查网络** - DeepSeek API需要网络连接
4. **查看源码** - 代码有详细注释

---

## 总结

**5个步骤完成AI生成**：
1. 打开管理器
2. 扫描Action
3. AI批量生成
4. 保存数据库
5. 导出JSON + 重建索引

**核心理念**：
- 数据与代码分离
- AI辅助生成，人工优化
- 策划可视化维护

**开始吧！** 🚀
