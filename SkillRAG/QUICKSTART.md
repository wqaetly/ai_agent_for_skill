# SkillRAG 快速启动指南

适用于在新电脑或团队成员第一次运行项目。

## 前置要求

- Python 3.8+
- Unity 2021.3+（如果需要导出技能）
- Git（用于克隆项目）

## 步骤1: 克隆项目

```bash
git clone <repository_url>
cd ai_agent_for_skill
```

## 步骤2: 安装Python依赖

```bash
cd SkillRAG/Python
pip install -r requirements.txt
```

**requirements.txt包含：**
- fastapi
- uvicorn
- chromadb
- sentence-transformers
- torch
- pyyaml
- watchdog
- pydantic
- cachetools

## 步骤3: 下载Qwen3嵌入模型

### 方案A：自动下载（推荐）

```bash
# 运行模型下载脚本（如果提供）
python download_model.py
```

### 方案B：手动下载

1. 从Hugging Face下载 `Qwen3-Embedding-0.6B` 模型
2. 放置到 `SkillRAG/Data/models/Qwen3-Embedding-0.6B/`

目录结构应该是：
```
SkillRAG/Data/models/Qwen3-Embedding-0.6B/
├── config.json
├── model.safetensors
├── tokenizer.json
└── ...
```

## 步骤4: 验证路径配置

```bash
cd SkillRAG/Python
python check_paths.py
```

**预期输出：**
```
✅ 所有关键路径配置正确！
```

如果有错误，按照提示修复。

## 步骤5: 导出Action元数据（首次运行）

1. 打开Unity项目 `ai_agent_for_skill`
2. 菜单栏：`Tools -> Skill RAG -> Export Actions to JSON`
3. 点击"导出所有Actions"
4. 确认导出成功，检查 `SkillRAG/Data/Actions/` 目录

## 步骤6: 构建Action索引

```bash
cd SkillRAG/Python
python build_action_index.py
```

**预期输出：**
```
✅ 索引构建成功！
索引Action数: 21
耗时: 3.45 秒
```

## 步骤7: 启动RAG服务器

```bash
python server.py
```

**预期输出：**
```
SkillRAG Server is ready!
Access API docs at: http://127.0.0.1:8765/docs
```

## 步骤8: 测试功能

### 方法1：访问API文档
打开浏览器：http://127.0.0.1:8765/docs

### 方法2：运行测试脚本
```bash
python test_action_search.py
```

### 方法3：直接调用API
```bash
curl "http://127.0.0.1:8765/search_actions?q=造成伤害&top_k=3"
```

## 常见问题

### Q1: pip install失败

**问题：** 依赖安装失败

**解决：**
```bash
# 更新pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 找不到模型

**问题：** `Model not found: ../Data/models/Qwen3-Embedding-0.6B`

**解决：**
1. 确认模型文件已下载
2. 检查路径：`SkillRAG/Data/models/Qwen3-Embedding-0.6B/`
3. 验证模型文件完整性

### Q3: 路径验证失败

**问题：** `check_paths.py` 报告路径错误

**解决：**
```bash
# 确保在正确目录
cd SkillRAG/Python
pwd  # 应该显示 .../SkillRAG/Python

# 检查项目结构
ls ../Data/  # 应该看到 Actions, models 等目录
```

### Q4: Unity导出失败

**问题：** Unity中找不到导出菜单

**解决：**
1. 确认安装了Odin Inspector插件
2. 重新编译Unity项目
3. 检查 `Assets/Scripts/SkillSystem/Editor/` 目录

### Q5: 服务器启动失败

**问题：** 端口被占用

**解决：**
```yaml
# 修改 config.yaml
server:
  port: 8766  # 改为其他端口
```

## 项目目录结构

```
ai_agent_for_skill/
├── ai_agent_for_skill/          # Unity项目
│   └── Assets/
│       ├── Scripts/
│       │   └── SkillSystem/
│       │       ├── Actions/     # Action脚本
│       │       └── Editor/      # 导出工具
│       └── Skills/              # 技能JSON文件
│
└── SkillRAG/                    # RAG系统
    ├── Data/
    │   ├── Actions/             # Action JSON文件
    │   ├── models/              # Qwen3模型
    │   ├── vector_db/           # 向量数据库
    │   └── *.json               # 缓存文件
    │
    ├── Python/
    │   ├── config.yaml          # 配置文件
    │   ├── server.py            # 服务器
    │   ├── check_paths.py       # 路径验证
    │   └── ...
    │
    └── *.md                     # 文档
```

## 下一步

- 阅读 [ACTION_RAG_README.md](ACTION_RAG_README.md) 了解详细功能
- 阅读 [PATH_CONFIG.md](PATH_CONFIG.md) 了解路径配置
- 在Unity编辑器中集成Action搜索功能

## 需要帮助？

- 查看日志文件：`SkillRAG/Data/rag_server.log`
- 运行诊断脚本：`python check_paths.py`
- 查看API文档：http://127.0.0.1:8765/docs
