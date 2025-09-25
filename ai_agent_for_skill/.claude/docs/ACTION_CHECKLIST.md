# Action创建强制检查清单

**每次涉及技能或Action的任务，必须执行此清单**

## 🚨 MANDATORY 检查步骤

### 第1步: 需求分析
```
□ 列出本次任务需要的所有Action类型
□ 写下具体的Action名称（如AudioAction, CameraAction等）
```

### 第2步: 现有Action检查
```
□ 执行: ls "Assets/Scripts/SkillSystem/Actions"
□ 对照需求列表，标记哪些Action已存在
□ 标记哪些Action不存在
```

### 第3步: 缺失Action处理
```
□ 对于每个缺失的Action：
  □ 立即创建对应的Action脚本
  □ 遵循通用性设计原则
  □ 添加完整的字段注释
  □ 编译验证无错误
```

### 第4步: JSON/代码创建
```
□ 只有在所有必要Action都存在后，才开始创建JSON或相关代码
□ 使用正确的Action类型，绝不使用占位方案
```

## 🔥 绝对禁止的行为

❌ 使用LogAction模拟其他功能
❌ 使用任何Action作为占位符
❌ 创建JSON时引用不存在的Action
❌ 绕过检查步骤直接开始编码

## ✅ 检查完成确认

当且仅当以上所有步骤都完成后，才能继续后续工作。

**违反检查清单 = 立即停止工作重新执行**