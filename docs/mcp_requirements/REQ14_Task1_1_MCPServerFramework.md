# REQ-14 任务1.1 MCP Server框架搭建

## 工作范围
- 安装mcp-sdk-python，搭建主入口、Tool注册与会话管理。
- 建立目录结构（tools/core/rag_integration/config/tests）。
- 接入现有RAG Engine的客户端封装。

## 实施步骤
1. 初始化Python项目、配置poetry/pip requirements与基础脚本。
2. 实现main.py：处理MCP握手、tool registry、日志与健康检查。
3. 编写rag_client适配器，统一search/lookup接口与超时策略。
4. 配置测试骨架（pytest + tox），确保基本工具调用可mock。

## 依赖
- Python 3.9+、mcp-server-sdk、现有RAG服务地址、Chroma连接凭据。

## 验收标准
- 能在本地通过MCP handshake并列出占位工具。
- 日志/配置可通过settings.yaml调整。

## 风险
- SDK版本变更 → 锁定版本并在CI中做兼容性测试。

## 里程碑
- 预计2天完成，输出可运行的最小骨架 + 接入文档。

## 交付物
- 完整目录结构、主入口、集成测试样例、运行说明。
