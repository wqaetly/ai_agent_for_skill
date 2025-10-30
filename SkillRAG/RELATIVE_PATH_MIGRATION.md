# 路径配置改为相对路径 - 改动总结

## 改动概述

将SkillRAG系统中的所有绝对路径改为相对路径，使项目可以在不同电脑上直接运行，无需修改配置。

## 修改的文件

### 1. config.yaml（主配置文件）

**修改前：**
```yaml
vector_store:
  persist_directory: "E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/vector_db"

skill_indexer:
  skills_directory: "E:/Study/wqaetly/ai_agent_for_skill/ai_agent_for_skill/Assets/Skills"
  index_cache: "E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/skill_index.json"

action_indexer:
  actions_directory: "E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/Actions"
  action_index_cache: "E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/action_index.json"

logging:
  file: "E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Data/rag_server.log"
```

**修改后：**
```yaml
vector_store:
  persist_directory: "../Data/vector_db"  # 相对于config.yaml

skill_indexer:
  skills_directory: "../../ai_agent_for_skill/Assets/Skills"  # 相对于config.yaml
  index_cache: "../Data/skill_index.json"

action_indexer:
  actions_directory: "../Data/Actions"
  action_index_cache: "../Data/action_index.json"

logging:
  file: "../Data/rag_server.log"
```

### 2. Unity导出工具（已使用相对路径）

**ActionToJsonExporter.cs:**
```csharp
private const string ExportDirectory = "../SkillRAG/Data/Actions";
```
✅ 无需修改，已经是相对路径

### 3. 新增文件

- **PATH_CONFIG.md** - 详细的路径配置说明文档
- **QUICKSTART.md** - 新电脑快速启动指南
- **check_paths.py** - 路径配置验证脚本

### 4. 更新文档

- **ACTION_RAG_README.md** - 更新配置说明部分

## 相对路径基准

所有Python端的相对路径都基于 `config.yaml` 所在目录：`SkillRAG/Python/`

```
SkillRAG/Python/config.yaml  ← 基准目录
    ../Data/vector_db        → SkillRAG/Data/vector_db
    ../Data/Actions          → SkillRAG/Data/Actions
    ../../ai_agent_for_skill/Assets/Skills  → ai_agent_for_skill/Assets/Skills
```

## 使用方式

### 验证路径配置
```bash
cd SkillRAG/Python
python check_paths.py
```

### 启动服务器
```bash
cd SkillRAG/Python
python server.py
```

**重要：** 必须在 `SkillRAG/Python/` 目录下运行Python脚本，否则相对路径会失效。

## 优势

1. **跨平台兼容** - Windows/Linux/Mac都能正常工作
2. **团队协作** - Git克隆后无需修改配置
3. **易于迁移** - 移动项目目录后仍然有效
4. **版本控制** - 配置文件可以直接提交到Git

## 注意事项

### ✅ 正确做法
```bash
cd SkillRAG/Python
python server.py
```

### ❌ 错误做法
```bash
cd SkillRAG
python Python/server.py  # 相对路径会失效
```

### ❌ 错误做法
```bash
cd项目根目录
python SkillRAG/Python/server.py  # 相对路径会失效
```

## 测试结果

运行 `python check_paths.py` 的输出：

```
SkillRAG Path Configuration Check
======================================================================
Current directory: E:\Study\wqaetly\ai_agent_for_skill\SkillRAG\Python
[OK] Config file found: config.yaml

Checking Configuration Paths
======================================================================
[OK] Embedding Model Directory
[OK] Vector Database Directory
[OK] Skill JSON Directory
[OK] Action JSON Directory
[OK] Data Root Directory

Check Results
======================================================================
[OK] All key paths are configured correctly!

File Statistics:
----------------------------------------------------------------------
Skill files: 8
Action files: 1
======================================================================
```

## 相关文档

- [PATH_CONFIG.md](PATH_CONFIG.md) - 详细路径配置说明
- [QUICKSTART.md](QUICKSTART.md) - 快速启动指南
- [ACTION_RAG_README.md](ACTION_RAG_README.md) - Action RAG系统文档
