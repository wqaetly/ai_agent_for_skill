# 🎮 AI Agent for Skill - 智能技能配置生成系统

<div align="center">

**为游戏策划提供AI驱动的技能分析、生成和修复能力**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)

[快速开始](#-快速开始) | [主要功能](#-主要功能)  | [技术架构](#-技术架构) | [Roadmap](#-roadmap)

</div>

<img width="3019" height="1484" alt="image" src="https://github.com/user-attachments/assets/e8393a5b-e5bc-47f4-ad4e-6c0417d8a905" />

---

## 📖 项目简介

**AI Agent for Skill** 是一个基于**RAG（检索增强生成）** 和 **LangGraph** 技术的智能技能配置系统，专为游戏策划人员设计。通过本地网页界面，策划可以使用自然语言描述需求，系统自动生成、验证和修复Unity技能配置JSON，大幅提升技能设计效率。

### 🎯 核心价值

- 🚀 **零代码生成**：用自然语言描述，自动生成完整技能配置
- 🔍 **智能分析**：语义搜索技能库，快速找到相似技能参考
- 🛠️**自动修复**：智能验证配置错误，自动修复并重试（最多3次）
- 💻 **本地部署**：完全本地运行，数据安全可控
- 🎨 **友好界面**：现代化Web界面，聊天式交互体验

---

## 🏗️ 项目结构

```
ai_agent_for_skill/
├── skill_agent/           # 核心RAG引擎和LangGraph服务器
?  ├── core/              # 核心RAG模块
?  ├── orchestration/     # LangGraph编排?
?  ├── tools/             # RAG工具
?  └── langgraph_server.py # HTTP API服务器
├── webui/                 # Web用户界面（Next.js?
└── ai_agent_for_skill/    # Unity集成模块
```

## 快速开?

### 1. 环境配置

#### 1.1 Python环境（skill_agent后端?

**必需步骤：配置API密钥**

1. 复制环境变量配置文件?
```bash
cd skill_agent
cp .env.example .env
```

2. 编辑 `.env` 文件，填写必需的API密钥?
```bash
# 必需：DeepSeek API密钥（用于技能生成）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**获取DeepSeek API密钥?*
- 访问 [https://platform.deepseek.com/](https://platform.deepseek.com/)
- 注册账号并创建API密钥
- 新用户通常有免费额度可?

**可选配置：**
```bash
# 可选：服务器端口（默认2024?
LANGGRAPH_PORT=2024

# 可选：LangSmith追踪（生产环境监控）
# LANGSMITH_API_KEY=your_langsmith_key
```

查看 `.env.example` 文件了解所有可配置项?

#### 1.2 WebUI环境

```bash
cd webui
cp .env.example .env
```

编辑 `webui/.env` 文件?
```bash
# LangGraph服务器地址（确保与后端端口一致）
NEXT_PUBLIC_API_URL=http://localhost:2024

# 默认助手（可选值：skill-generation, skill-search, skill-detail, action-search?
NEXT_PUBLIC_ASSISTANT_ID=skill-generation
```

### 2. 安装依赖

#### 2.1 Python依赖

```bash
cd skill_agent
pip install -r requirements.txt  # 如果有requirements.txt
# ?
pip install langchain langchain-community langgraph chromadb sentence-transformers fastapi uvicorn pyyaml
```

#### 2.2 Node.js依赖

```bash
cd webui
npm install
```

### 3. 启动服务

#### 3.1 启动后端服务器

```bash
cd skill_agent
python langgraph_server.py
```

服务器默认运行在 `http://localhost:2024`

**验证服务器状态：**
```bash
curl http://localhost:2024/health
```

#### 3.2 启动Web界面

```bash
cd webui
npm run dev
```

Web界面默认运行?`http://localhost:3000`

## ?主要功能

### 1️⃣ 智能技能生成（已完?✅）

**核心能力?* 基于自然语言描述，自动生成完整的Unity技能配置JSON

**工作流程*
```
用户输入需??RAG检索相似技??LLM生成JSON ?自动验证 ?智能修复 ?返回结果
```

**特性：**
- ?自然语言理解：支持中英文混合描述
- ?RAG增强生成：基于历史技能库提供参?
- ?自动验证：检查必填字段、数据类型、数值范?
- ?智能修复：最多3次自动修复循环，确保配置正确
- ?流式响应：实时查看生成过?

**使用示例?*
```
输入?创建一个火球术技能，造成100点火焰伤害，冷却时间5秒，消?0点魔?
输出：完整的技能配置JSON，包含DamageAction、CostAction?
```

---

### 2️⃣ 技能语义搜索（已完?✅）

**核心能力?* 基于语义理解的技能检索，无需记忆技能ID

**技术实现：**
- 🔍 向量检索：使用Qwen3-Embedding-0.6B本地模型
- 📊 相似度评分：返回匹配度最高的技能列?
- 🎯 细粒度查询：支持类SQL语法（如 "DamageAction where baseDamage > 200"?

**使用示例?*
```
查询?搜索所有范围伤害技?
结果?
  - Flame Shockwave (相似?85%)
  - Fire Storm (相似?78%)
  - Ice Nova (相似?72%)
```

---

### 3️⃣ 技能详情查询（已完?✅）

**核心能力?* 快速查询技能的完整配置和参?

**功能?*
- 📋 完整配置展示：skillName, skillId, actions, cooldown?
- 🔗 Action详情：每个Action的类型和参数
- 📊 参数推荐：基于历史数据的参数范围建议

**使用示例?*
```
查询?查看技?Fireball 的详细配?
返回：技能的完整JSON配置和参数说?
```

---

### 4️⃣ Action智能搜索（已完成 ✅）

**核心能力?* 搜索可用的Action脚本和参数定?

**功能?*
- 🔎 Action类型搜索：查找特定类型的Action（如伤害、治疗、移动）
- 📖 参数定义查询：获取Action的完整参数列?
- 💡 使用频率统计：显示Action在技能库中的使用次数

**使用示例?*
```
查询?有哪些伤害类型的Action?
返回：DamageAction, DOTAction, AOEDamageAction?
```

---

### 5️⃣ 本地Web界面（已完成 ✅）

**核心能力?* 友好的聊天式交互界面

**特性：**
- 💬 聊天式交互：类似ChatGPT的对话体?
- 🔄 流式响应：实时显示生成过?
- 🎨 现代化UI：基于Next.js 15 + React 19
- 🔌 多助手切换：技能生成、搜索、详情、Action查询
- 📱 响应式设计：支持桌面和移动端

**访问地址?* `http://localhost:3000`

---

### 6️⃣ Unity集成（已完成 ✅）

**核心能力?* 与Unity编辑器的双向通信

**功能?*
- 🔗 RPC通信：实时同步技能配置到Unity
- 📤 Action导出：自动扫描Unity C#脚本生成Action定义
- 🪟 Unity窗口：在Unity编辑器中直接使用RAG助手
- 🔄 一键导入：生成的技能配置一键导入Unity项目

**使用场景?*
- 在Unity中直接生成技能，无需切换到浏览器
- 自动同步Action定义，保持数据一致?

## Unity集成

### 前置条件

- Unity 2021.3 或更高版?
- 已安装Odin Inspector插件（用于技能编辑器?

### 集成步骤

1. **导出Action定义**（在Unity中）
   - 打开 Unity 编辑?
   - 菜单：`Tools > RAG > Export Action Definitions`
   - 导出文件保存到：`skill_agent/Data/action_definitions.json`

2. **启动Unity RPC服务?*（可选）
   ```bash
   cd skill_agent/Python
   python unity_rpc_server.py
   ```
   - 默认端口?766
   - 用于Unity与Python的双向通信

3. **在Unity中使用RAG助手**
   - 菜单：`Window > Skill RAG > RAG Assistant`
   - 在窗口中输入需求，生成技能配置
   - 一键导入到Unity项目

详细集成文档请参考：`skill_agent/UNITY集成指南.md`

## 故障排除

### 常见问题

**Q1: 启动服务器时提示 "环境变量 DEEPSEEK_API_KEY 未设?**

A: 确保已创?`.env` 文件并正确配置：
```bash
cd skill_agent
cp .env.example .env
# 编辑 .env，填?DEEPSEEK_API_KEY
```

**Q2: WebUI无法连接到后端服务器**

A: 检查以下几点：
- 后端服务器是否正常运行（访问 `http://localhost:2024/health`?
- `webui/.env` 中的 `NEXT_PUBLIC_API_URL` 是否正确
- 防火墙是否阻止了端口2024

**Q3: 技能生成失败或JSON格式错误**

A: 可能的原因：
- DeepSeek API配额不足或网络问?
- Prompt需要优化（编辑 `skill_agent/orchestration/prompts/prompts.yaml`?
- 验证规则过于严格（检?`orchestration/nodes/skill_nodes.py` 中的 `validator_node`?

**Q4: 向量搜索结果不准?*

A: 可以尝试?
- 重建索引：运?`skill_agent/Python/rebuild_index.py`
- 调整相似度阈值：修改 `skill_agent/core/config.py` 中的阈?
- 增加技能库样本数量（RAG效果依赖数据量）

**Q5: Unity RPC连接失败**

A: 检查：
- RPC服务器是否启动（`python unity_rpc_server.py`?
- 端口8766是否被占?
- Unity编辑器中的RPC地址配置是否正确

## 技术架?

```
用户 ?WebUI (Next.js)
       ?HTTP API
    LangGraph Server (FastAPI)
       ?调用LangGraph?
    Skill Generation Graph
       ?节点流程
    [Retriever] ?[Generator] ?[Validator] ?[Fixer] ?[Finalizer]
       ?使用
    RAG Engine (ChromaDB + Qwen3-Embedding)
       ?检?
    Skills DB + Actions DB
```

### 技术栈

- **后端**: Python + LangGraph + FastAPI + ChromaDB
- **嵌入模型**: Qwen3-Embedding-0.6B（本地部署）
- **LLM**: DeepSeek API
- **前端**: Next.js 15 + React 19 + TypeScript
- **Unity**: C# + Odin Inspector

## 开发指?

### 添加新的助手

1. ?`skill_agent/orchestration/graphs/` 中创建新?
2. ?`langgraph_server.py` 中注册助手ID
3. ?WebUI 中添加到助手列表

### 自定义Prompt

编辑 `skill_agent/orchestration/prompts/prompts.yaml`?
```yaml
your_custom_prompt:
  system: |
    你的系统提示?
  user: |
    你的用户提示词，支持变量 {variable_name}
```

然后在代码中使用?
```python
# ?skill_agent 目录下运?
from orchestration.prompts.prompt_manager import get_prompt_manager

pm = get_prompt_manager()
prompt = pm.get_prompt("your_custom_prompt")
```

### 调整验证规则

修改 `skill_agent/orchestration/nodes/skill_nodes.py` 中的 `validator_node` 函数?

详细开发指南请参考：[完整开发文档](skill_agent/WEBUI_GUIDE.md)

## 🗺?Roadmap

### ?Phase 1: 核心功能（已完成?

- [x] RAG引擎开?
  - [x] 向量嵌入生成（Qwen3-Embedding?
  - [x] 向量存储和检索（ChromaDB?
  - [x] 技能索引管?
  - [x] Action索引管理
- [x] LangGraph工作?
  - [x] 技能生成图（检索→生成→验证→修复?
  - [x] 技能搜索图
  - [x] 技能详情图
  - [x] Action搜索?
- [x] Web界面
  - [x] Next.js前端开?
  - [x] 聊天式交互界?
  - [x] 流式响应支持
  - [x] 多助手切?
- [x] Unity集成
  - [x] RPC服务器
  - [x] Unity编辑器窗?
  - [x] Action定义导出

**完成时间?* 2025?1?

---

### 🚧 Phase 2: 功能增强（进行中?

#### 高优先级

- [ ] **批量技能生?*
  - [ ] 支持一次生成多个技?
  - [ ] 技能模板系?
  - [ ] 批量导出功能

- [ ] **技能对比分?*
  - [ ] 可视化对比两个技能的差异
  - [ ] 参数范围分析
  - [ ] 平衡性建?

- [ ] **历史记录管理**
  - [ ] 保存生成历史
  - [ ] 版本对比
  - [ ] 回滚功能

#### 中优先级

- [ ] **高级搜索功能**
  - [ ] 多条件组合搜?
  - [ ] 搜索结果排序和过?
  - [ ] 保存常用搜索

- [ ] **技能可视化**
  - [ ] 技能效果预?
  - [ ] Action流程
  - [ ] 参数关系?

- [ ] **团队协作**
  - [ ] 多用户支?
  - [ ] 技能评论和标注
  - [ ] 变更追踪

---

### 🔮 Phase 3: 智能化升级（规划中）

#### 高优先级

- [ ] **智能平衡性分?*
  - [ ] 基于历史数据的平衡性评?
  - [ ] 技能强度预?
  - [ ] 自动调参建议

- [ ] **技能组合推?*
  - [ ] 基于技能库推荐技能组?
  - [ ] 职业技能树生成
  - [ ] 技能链路分?

- [ ] **自然语言查询增强**
  - [ ] 支持更复杂的查询语法
  - [ ] 多轮对话上下文理?
  - [ ] 意图识别优化

#### 中优先级

- [ ] **多语言支持**
  - [ ] 界面国际化（???韩）
  - [ ] 多语言技能描?
  - [ ] 跨语言搜索

- [ ] **性能优化**
  - [ ] 向量索引优化
  - [ ] 缓存策略改进
  - [ ] 并发处理优化

- [ ] **数据导入导出**
  - [ ] 支持Excel批量导入
  - [ ] 导出为多种格式（JSON/YAML/XML?
  - [ ] 与其他工具集?

---

### 🌟 Phase 4: 生态扩展（未来?

- [ ] **插件系统**
  - [ ] 自定义验证规则插?
  - [ ] 自定义生成策略插?
  - [ ] 第三方工具集?

- [ ] **云端部署**
  - [ ] Docker容器?
  - [ ] Kubernetes部署方案
  - [ ] 云端协作版本

- [ ] **AI模型升级**
  - [ ] 支持更多LLM（GPT-4, Claude等）
  - [ ] 微调专用技能生成模?
  - [ ] 多模态支持（图片、视频）

- [ ] **跨引擎支?*
  - [ ] Unreal Engine集成
  - [ ] Cocos Creator集成
  - [ ] Godot集成

---

## 📊 项目状?

| 模块 | 状?| 完成?| 备注 |
|------|------|--------|------|
| RAG引擎 | ?已完?| 100% | 核心功能稳定 |
| LangGraph工作?| ?已完?| 100% | 支持4种助?|
| Web界面 | ?已完?| 100% | 生产就绪 |
| Unity集成 | ?已完?| 100% | RPC通信稳定 |
| 文档 | ?已完?| 95% | 持续完善?|
| 测试 | 🚧 进行?| 70% | 需要更多单元测?|

**当前版本?* v1.0.0  
**最后更新：** 2025?1?2?

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request?

### 如何贡献

1. Fork本项?
2. 创建特性分?(`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发规?

- 遵循PEP 8（Python）和ESLint（TypeScript）代码规?
- 添加必要的单元测?
- 更新相关文档

---

## 📄 许可?

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📚 相关文档

- [WebUI快速开始](skill_agent/WEBUI_QUICKSTART.md) - 5分钟快速上?
- [Unity集成指南](skill_agent/UNITY集成指南.md) - Unity编辑器集?
- [完整开发文档](skill_agent/WEBUI_GUIDE.md) - 详细技术文?
- [架构说明](skill_agent/ARCHITECTURE_WEBUI.md) - 系统架构设计

---

## 💬 联系方式

- 提交Issue：[GitHub Issues](https://github.com/yourusername/ai_agent_for_skill/issues)
- 讨论区：[GitHub Discussions](https://github.com/yourusername/ai_agent_for_skill/discussions)

---

<div align="center">

**?如果这个项目对你有帮助，请给个Star支持一下！?*

Made with ❤️ by the AI Agent for Skill Team

</div>
