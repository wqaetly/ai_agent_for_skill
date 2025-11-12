# skill_agent - 智能技能检索与推荐系统

<div align="center">

**为Unity技能编辑器提供AI驱动的技能搜索和参数推荐功能**

[快速开始](#快速开始) | [功能特性](#功能特性) | [文档](#文档) | [架构](#架构)

</div>

---

## 📖 简介

skill_agent（Skill Retrieval-Augmented Generation）是一个基于**检索增强生成（RAG）**技术的智能技能辅助系统。它通过向量化技能数据，提供语义搜索和智能推荐，帮助开发者快速找到相似技能、获取参数建议，大幅提升技能设计效率。

### 🎯 核心价值

- **🔍 语义搜索**：用自然语言描述查找相似技能，无需记忆技能ID
- **💡 智能推荐**：根据上下文自动推荐Action类型和参数配置
- **📚 知识沉淀**：将所有技能经验转化为可搜索的知识库
- **🔄 实时同步**：技能文件修改后自动更新索引，始终保持最新

### 🌟 适用场景

- **大规模技能库管理**：技能数量超过100个，难以手动查找
- **团队协作开发**：快速了解他人设计的技能，保持风格统一
- **参数调优**：参考相似技能的参数配置，加速平衡性调整
- **学习与培训**：新成员快速学习现有技能设计模式

---

## 🚀 功能特性

### 1. 语义技能搜索

```
查询：火球 + 范围 + 伤害
结果：Flame Shockwave (相似度85%)
      Fire Storm (相似度78%)
      ...
```

- 支持中英文混合查询
- 基于含义而非关键词匹配
- 返回相似度评分和详细信息

### 2. Action智能推荐

```
上下文：造成伤害并击退敌人
推荐：DamageAction (出现15次)
      - baseDamage: 100, damageType: Magical
      MovementAction (出现8次)
      - movementType: Linear, distance: 5.0
```

- 分析相似技能中的Action使用模式
- 提供实际参数示例
- 一键应用到编辑器

### 3. Unity编辑器集成

- **RAG查询窗口**：独立窗口进行技能搜索和管理
- **智能检查器**：Action Inspector中自动显示参数建议
- **一键应用**：直接将推荐参数填充到Action
- **无缝集成**：与现有技能编辑器完美配合

### 4. 自动化索引

- **实时监听**：技能文件修改后自动更新向量库
- **增量索引**：只更新变化的文件，节省时间
- **后台运行**：不影响Unity编辑器使用

---

## 🚀 快速开始

### 系统要求

| 组件 | 要求 |
|------|------|
| **Python** | 3.8+ |
| **Unity** | 2023.2+ |
| **内存** | 至少2GB可用 |
| **磁盘** | 10GB（模型数据） |

### 安装步骤

#### 1️⃣ 准备Qwen3模型

**重要：系统使用本地模型，需要先手动下载模型文件**

1. 下载 Qwen3-Embedding-0.6B 模型到指定目录：
   ```
   skill_agent/Data/models/Qwen3-Embedding-0.6B/
   ```

2. 模型文件获取方式：
   - 从HuggingFace 下载：https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
   - 使用 `git lfs` 克隆：
     ```bash
     git lfs install
     git clone https://huggingface.co/Qwen/Qwen3-Embedding-0.6B skill_agent/Data/models/Qwen3-Embedding-0.6B
     ```

3. 确保目录结构如下：
   ```
   skill_agent/Data/models/Qwen3-Embedding-0.6B/
   ├── config.json
   ├── model.safetensors
   ├── tokenizer.json
   ├── tokenizer_config.json
   └── ... (其他模型文件)
   ```

#### 2️⃣ 安装Python依赖

```bash
cd skill_agent
setup.bat  # Windows

# 或手动安装
cd Python
pip install -r requirements.txt
```

**注意**：
- 需要transformers>=4.51.0 才能支持Qwen3模型
- 需要sentence-transformers>=3.0.0
- Qwen3支持100+语言，嵌入维度1024，性能优于前代模型

#### 3️⃣ 配置路径

编辑`Python/config.yaml`：

```yaml
# 嵌入模型配置 - 使用本地模型
embedding:
  model_name: "../Data/models/Qwen3-Embedding-0.6B"  # 本地模型路径
  device: "cpu"  # 或"cuda" 如有GPU

# 技能索引配置
skill_indexer:
  skills_directory: "../../ai_agent_for_skill/Assets/Skills"  # 修改为你的技能路径
```

#### 4️⃣ 启动RAG服务器

```bash
start_rag_server.bat  # Windows
```

看到以下信息说明成功：
```
INFO: skill_agent Server is ready!
INFO: Access API docs at: http://127.0.0.1:8765/docs
```

#### 5️⃣ Unity中启用

1. Unity菜单 → **技能系统 / RAG功能 / 启用RAG功能**
2. 菜单 → **Edit / Preferences / 技能系统 / RAG设置**
3. 点击**测试连接**

✅ **安装完成！** 现在可以使用RAG功能了。

---

## 📚 使用示例

### 示例1：搜索相似技能

**场景**：想找一个带位移的伤害技能参考

1. 打开RAG查询窗口（技能系统 → RAG查询窗口）
2. 输入："带冲锋效果的伤害技能"
3. 点击搜索

**结果**：
```
Riven Broken Wings (相似度 87%)
- 文件: RivenBrokenWings.json
- 6轨道, 15动作, 150帧

Tryndamere Spinning Slash (相似度 76%)
- 文件: TryndamereSpinningSlash.json
- 5轨道, 12动作, 120帧
```

4. 点击"打开技能文件"直接在编辑器中查看

### 示例2：获取参数建议

**场景**：正在配置DamageAction，不确定合适的参数值

1. 在技能编辑器中添加DamageAction
2. 选中该Action
3. 查看自动显示的"🤖 AI参数建议"面板

**建议内容**：
```
常见参数配置 (出现12次)

来源: Flame Shockwave
  baseDamage: 100
  damageType: Magical
  damageRadius: 5.0
  [应用]

来源: Sion Soul Furnace
  baseDamage: 80
  damageType: Physical
  maxTargets: 3
  [应用]
```

4. 点击"应用"按钮一键填充参数

---

## 🏗️ 架构

### 系统架构图

```
┌──────────────────────────────────────────────────────────┐
│                   Unity 编辑器                         │
│ ┌────────────────┐ ┌──────────────┐ ┌─────────────┐│
│ │skill_agentWindow│ │ActionInspector│ │SkillEditor ││
│ │ (查询界面)     │ │(智能建议)    │ │ (编辑器)   ││
│ └────────┬───────┘ └──────┬───────┘ └─────────────┘│
│          │                │                           │
│          └────────┬───────┘                           │
│                   │HTTP API                            │
└───────────────────┼──────────────────────────────────┘
                    │
                    │
┌──────────────────────────────────────────────────────────┐
│             Python RAG 服务 (FastAPI)                   │
│ ┌────────────────────────────────────────────────────┐│
│ │                 RAG Engine                         ││
│ │ ┌──────────────┐┌──────────────┐┌───────────┐ ││
│ │ │Embedding    ││Vector Store ││ Skill    │ ││
│ │ │Generator    ││ (ChromaDB)  ││ Indexer  │ ││
│ │ └──────────────┘└──────────────┘└───────────┘ ││
│ └────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
                    │
                    │
┌──────────────────────────────────────────────────────────┐
│               技能JSON文件                              │
│  FlameShockwave.json, RivenBrokenWings.json, ...      │
└──────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **Unity客户端** | C# / UnityWebRequest | 编辑器集成和HTTP通信 |
| **Python服务** | FastAPI / Uvicorn | RESTful API服务器 |
| **嵌入模型** | Qwen3-Embedding-0.6B | 通义千问嵌入模型，1024维向量，支持100+语言 |
| **向量数据库** | ChromaDB | 本地持久化向量存储 |
| **文件监听** | Watchdog | 自动检测文件变化 |

### 核心模块

#### Python后端

- **embeddings.py**：文本向量化，缓存管理
- **vector_store.py**：ChromaDB封装，向量CRUD
- **skill_indexer.py**：技能解析，索引构建
- **rag_engine.py**：RAG核心逻辑，检索排序
- **server.py**：FastAPI服务器，API路由

#### Unity前端

- **RAGClient.cs**：HTTP客户端，API调用封装
- **skill_agentWindow.cs**：查询窗口UI
- **SmartActionInspector.cs**：智能参数推荐
- **RAGEditorIntegration.cs**：编辑器钩子集成

---

## 📁 目录结构

```
skill_agent/
├── Python/                      # Python RAG服务
│  ├── server.py                # FastAPI服务器
│  ├── rag_engine.py            # RAG引擎核心
│  ├── embeddings.py            # 嵌入生成器
│  ├── vector_store.py          # 向量数据库
│  ├── skill_indexer.py         # 技能索引器
│  ├── config.yaml              # 配置文件
│  └── requirements.txt         # Python依赖
│
├── Unity/                       # Unity编辑器集成（实际位于Assets/Scripts/RAGSystem）
│  ├── RAGClient.cs             # HTTP客户端
│  ├── skill_agentWindow.cs        # RAG查询窗口
│  ├── SmartActionInspector.cs  # 智能参数推荐
│  └── RAGEditorIntegration.cs  # 编辑器集成
│
├── Data/                        # 数据存储
│  ├── vector_db/               # ChromaDB数据库
│  ├── embeddings_cache/        # 嵌入模型缓存
│  ├── skill_index.json         # 技能索引缓存
│  └── rag_server.log           # 服务器日志
│
├── Docs/                        # 完整文档
│  ├── UserGuide.md             # 用户指南
│  ├── API.md                   # API文档
│  ├── ActionReference.md       # Action参数详解
│  └── SkillPatterns.md         # 技能设计模式
│
├── start_rag_server.bat         # 启动脚本
├── setup.bat                    # 安装脚本
└── README.md                    # 本文档
```

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| **[用户指南](Docs/UserGuide.md)** | 详细使用教程，从入门到精通 |
| **[API文档](Docs/API.md)** | RESTful API接口说明 |
| **[Action参考](Docs/ActionReference.md)** | 21种Action类型的参数详解 |
| **[技能模式](Docs/SkillPatterns.md)** | 20种常见技能设计模式 |

### 在线文档

启动服务器后访问：
- **Swagger UI**: http://127.0.0.1:8765/docs
- **ReDoc**: http://127.0.0.1:8765/redoc

---

## 🔧 配置说明

### 核心配置项

编辑`Python/config.yaml`：

```yaml
# 服务器配置
server:
  host: "127.0.0.1"
  port: 8765

# 嵌入模型配置 - 使用本地模型
embedding:
  model_name: "../Data/models/Qwen3-Embedding-0.6B"  # 本地模型路径
  device: "cpu"  # 或"cuda" (如有GPU)
  batch_size: 32
  max_length: 8192  # 支持长文本（最多32K）
  use_flash_attention: false  # GPU加速（仅GPU支持）

# 向量数据库配置
vector_store:
  persist_directory: "../Data/vector_db"
  collection_name: "skill_collection"

# 技能索引配置
skill_indexer:
  skills_directory: "../../ai_agent_for_skill/Assets/Skills"  # 修改此路径
  watch_enabled: true  # 启用文件监听

# RAG配置
rag:
  top_k: 5  # 默认返回结果数
  similarity_threshold: 0.5  # 相似度阈值
  cache_enabled: true  # 启用查询缓存
  cache_ttl: 3600  # 缓存1小时
```

---

## 🎓 最佳实践

### 1. 查询技巧

**✅ 推荐做法**：
- 使用描述性语言："带位移的伤害技能"
- 包含关键词：火焰、范围、控制等
- 中英文混合支持更佳

**❌ 避免**：
- 过于模糊："好用的技能"
- 纯技术术语："DamageAction + MovementAction"

### 2. 参数应用

**✅ 推荐做法**：
- 先应用AI推荐，再微调
- 参考多个示例取平均
- 遵循游戏设计规范

**❌ 避免**：
- 完全照搬不测试
- 忽略技能整体平衡

### 3. 索引维护

**定期维护**：
- 每周重建一次索引
- 清理无用的技能文件
- 检查服务器日志

---

## ❓ 常见问题

### Q: 连接失败怎么办？

**A**: 检查以下几点：
1. Python服务器是否正在运行
2. 防火墙是否阻止端口8765
3. Unity Preferences中的服务器地址是否正确

### Q: 搜索结果不相关？

**A**: 尝试：
1. 重建索引（管理 → 重建索引）
2. 使用更具体的查询词
3. 检查技能文件是否有详细描述

### Q: 模型加载失败？

**A**: 请检查：
1. 模型文件是否完整下载到`Data/models/Qwen3-Embedding-0.6B/` 目录
2. 检查config.yaml 中的 model_name 路径是否正确
3. 确保所有必需的模型文件都存在（config.json, model.safetensors 等）

### Q: 遇到 KeyError: 'qwen3' 错误？

**A**: 需要升级transformers 版本：
```bash
pip install --upgrade transformers>=4.51.0
```

### Q: 如何提高搜索精度?

**A**:
- 确保技能有详细的skillDescription
- 使用中文+英文混合描述
- 定期重建索引保持最新

更多问题请查看**[用户指南](Docs/UserGuide.md)**。

---

## 🔍 性能指标

| 指标 | 数值 |
|------|------|
| 索引速度 | ~10技能/秒 |
| 查询延迟 | <500ms (无缓存) |
| 缓存命中率 | 60-80% |
| 内存占用 | ~2GB (含Qwen3模型) |
| 模型大小 | 1.2GB (Qwen3-0.6B) |
| 嵌入维度 | 1024 (支持32-1024自定义) |
| 上下文长度 | 32K tokens |

---

## 🛣️ 未来计划

- [ ] 支持更多嵌入模型（OpenAI、Cohere等）
- [ ] 云端向量数据库支持（Pinecone、Weaviate）
- [ ] 技能自动生成功能
- [ ] 多人协作推荐
- [ ] 技能设计质量评估

---

## 📄 许可证

本项目为内部工具，仅供学习和研究使用。

---

## 🙏 致谢

- **Qwen/Alibaba Cloud**: 提供强大的Qwen3嵌入模型
- **Sentence-Transformers**: 优秀的嵌入模型框架
- **ChromaDB**: 易用的向量数据库
- **FastAPI**: 现代化的Python Web框架
- **Unity**: 强大的游戏引擎

---

## 📮 联系方式

如有问题或建议，请：
1. 查看[用户指南](Docs/UserGuide.md)和[API文档](Docs/API.md)
2. 检查服务器日志：`Data/rag_server.log`
3. 查看Unity Console日志（搜索`[RAG]`前缀）

---

<div align="center">

**🎉 祝你使用愉快！**

Made with ❤️ for Unity Skill Designers

</div>
