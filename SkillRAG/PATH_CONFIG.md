# SkillRAG 路径配置说明

## 路径结构

项目使用**相对路径**配置，所有路径都相对于`config.yaml`所在的目录（`SkillRAG/Python/`）。

```
项目根目录/
├── ai_agent_for_skill/              # Unity项目
│   └── Assets/
│       └── Skills/                  # 技能JSON文件
│
└── SkillRAG/                        # RAG系统
    ├── Data/
    │   ├── Actions/                 # Action JSON文件
    │   ├── models/                  # Qwen3模型
    │   ├── vector_db/               # 向量数据库
    │   ├── skill_index.json         # 技能索引缓存
    │   ├── action_index.json        # Action索引缓存
    │   └── rag_server.log           # 日志文件
    │
    └── Python/
        ├── config.yaml              # ← 配置文件（相对路径基准）
        ├── server.py
        └── ...
```

## config.yaml 路径配置

### 1. 向量数据库
```yaml
vector_store:
  persist_directory: "../Data/vector_db"  # SkillRAG/Data/vector_db
```

### 2. 技能索引
```yaml
skill_indexer:
  skills_directory: "../../ai_agent_for_skill/Assets/Skills"  # Unity技能目录
  index_cache: "../Data/skill_index.json"                      # 缓存文件
```

### 3. Action索引
```yaml
action_indexer:
  actions_directory: "../Data/Actions"            # Action JSON目录
  action_index_cache: "../Data/action_index.json" # 缓存文件
```

### 4. 嵌入模型
```yaml
embedding:
  model_name: "../Data/models/Qwen3-Embedding-0.6B"  # 本地模型路径
```

### 5. 日志
```yaml
logging:
  file: "../Data/rag_server.log"  # 日志文件
```

## Unity端路径配置

### ActionToJsonExporter.cs
```csharp
private const string ExportDirectory = "../SkillRAG/Data/Actions";
```

这个路径相对于Unity项目根目录（`ai_agent_for_skill/`）。

## 路径解析规则

### Python端
Python脚本会自动将相对路径转换为绝对路径：

```python
# config.yaml中：
persist_directory: "../Data/vector_db"

# 实际解析为：
# 工作目录在 SkillRAG/Python/
# 相对路径 ../Data/vector_db
# → 绝对路径 SkillRAG/Data/vector_db
```

### Unity端
Unity的`System.IO.Path.GetFullPath()`会自动处理相对路径：

```csharp
ExportDirectory = "../SkillRAG/Data/Actions"
// Unity项目根目录: ai_agent_for_skill/
// → 绝对路径: 项目根目录/SkillRAG/Data/Actions
```

## 跨平台兼容性

### Windows
```yaml
persist_directory: "../Data/vector_db"  # ✅ 正确
```

### Linux/Mac
```yaml
persist_directory: "../Data/vector_db"  # ✅ 正确
```

相对路径使用`/`作为分隔符，在所有平台上都能正常工作。

## 常见问题

### Q1: 如何确认路径是否正确？

**方法1：查看日志**
```bash
cd SkillRAG/Python
python server.py
# 查看日志输出的实际路径
```

**方法2：Python测试**
```python
import os
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# 打印实际路径
skills_dir = config['skill_indexer']['skills_directory']
abs_path = os.path.abspath(skills_dir)
print(f"技能目录: {abs_path}")
print(f"是否存在: {os.path.exists(abs_path)}")
```

### Q2: 路径找不到怎么办？

**检查工作目录**
```bash
# 确保在正确的目录运行
cd SkillRAG/Python
python server.py  # ✅ 正确

# 不要在其他目录运行
cd SkillRAG
python Python/server.py  # ❌ 错误，相对路径会失效
```

### Q3: 如何修改为其他目录结构？

如果项目结构不同，只需修改`config.yaml`中的相对路径：

```yaml
# 例如：技能文件在其他位置
skill_indexer:
  skills_directory: "../../../OtherProject/Assets/Skills"  # 自定义路径
```

### Q4: 可以使用绝对路径吗？

可以，但**不推荐**：

```yaml
# ❌ 不推荐：绝对路径
skills_directory: "C:/Users/Username/Project/Assets/Skills"

# ✅ 推荐：相对路径
skills_directory: "../../ai_agent_for_skill/Assets/Skills"
```

**理由：**
- 绝对路径在不同电脑上无法使用
- 相对路径可以随项目一起迁移
- 便于团队协作和版本控制

## 最佳实践

1. **始终使用相对路径**
   - 配置文件中使用相对路径
   - 代码中使用相对路径

2. **统一工作目录**
   - 始终在`SkillRAG/Python/`目录下运行脚本
   - 使用`cd`命令切换到正确目录

3. **文档说明**
   - 在README中说明运行位置
   - 提供命令示例

4. **路径验证**
   - 启动时验证关键路径是否存在
   - 打印实际使用的绝对路径供调试

## 启动检查清单

运行服务器前检查：

```bash
# 1. 确认当前目录
pwd  # 应该在 SkillRAG/Python/

# 2. 检查配置文件
ls config.yaml  # 应该存在

# 3. 检查关键目录
ls ../Data/Actions/          # Action目录
ls ../../ai_agent_for_skill/Assets/Skills/  # 技能目录

# 4. 启动服务器
python server.py
```

## 相关文件

- `config.yaml` - 主配置文件
- `ActionToJsonExporter.cs` - Unity导出工具
- `skill_indexer.py` - 技能索引器
- `action_indexer.py` - Action索引器
