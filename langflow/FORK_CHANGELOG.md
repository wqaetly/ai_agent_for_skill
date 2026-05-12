# Fork 与上游差异变更日志（FORK_CHANGELOG）

> 本文件记录 [wqaetly/langflow @ dev](https://github.com/wqaetly/langflow/tree/dev) 相对官方 [langflow-ai/langflow](https://github.com/langflow-ai/langflow) 主干的关键改动，作为本项目编写 Custom Component 与 flow 时**唯一可信的差异说明**。  
> 任何 Custom Component / flow 配置如果依赖 fork 内的非上游行为，**必须**先在本文件记录该依赖。

---

## 锁定版本

| 项目 | 值 |
|------|-----|
| Fork 锁定 commit SHA | `0a3f184750cf...` (`0a3f18475`) |
| 上一次锁定 SHA | `ee567b98c0f50065b0e270e06c47326e08913eb5` |
| 上游对照基准 | _待维护者补齐：fork 当前基于上游哪个 tag/commit rebase_ |

> 本轮 fork bump（2026-05-12）新增 3 个 commit：(1) `2e7782b7e` Local dev tooling — 引入 `restart_langflow.bat` / `LOCAL_DEV_GUIDELINES.md` / `setup_defender_exclusions.ps1`，刷新 starter projects、custom_proxy 与 frontend node-class normalization 测试；(2) `62babbc88` Auto-format from langflow run；(3) `0a3f18475` docs: add upstream sync workflow as guideline 4。

---

## fork 关键改动（待维护者填写）

> 由维护者根据 fork 实际改动补齐下表。AI 助手与新成员**只能依赖本表中已声明的 fork 特性**。

### 1. 自定义 Endpoint

| Endpoint | 路径 | 用途 | 上游是否存在 |
|----------|------|------|--------------|
| _示例：flow dump 增强_ | `POST /api/v1/flows/dump_enhanced` | _待补充_ | 否 |
| _待补充_ | _待补充_ | _待补充_ | _待补充_ |

### 2. 自定义节点 / Component

| 节点名 | 类型 | 用途 | 上游是否存在 |
|--------|------|------|--------------|
| _待补充_ | _待补充_ | _待补充_ | _待补充_ |

### 3. UI / 调度增强

| 模块 | 改动 | 影响 |
|------|------|------|
| _示例：flow dump 优化_ | _见 commit ee567b98c_ | _需要利用 dump 增强能力的 flow 必须依赖此特性_ |
| _待补充_ | _待补充_ | _待补充_ |

### 4. 与上游不兼容的 API 变更

| API | 变更类型 | 上游行为 | fork 行为 | 影响 |
|-----|----------|----------|-----------|------|
| _待补充_ | _待补充_ | _待补充_ | _待补充_ | _待补充_ |

---

## Component 对 fork 的依赖声明

> 编写 `langflow/components/*.py` 时，如该 Component 依赖 fork 特定行为，**必须**在此处登记，便于后续 rebase 时识别破坏性影响。

| Component | 依赖的 fork 特性 | 上游替代方案（若 fork 升级丢失该特性）|
|-----------|------------------|------------------------------------|
| _待补充_ | _待补充_ | _待补充_ |

---

## 升级 fork 的注意事项

1. 升级前先在本文件登记目标 SHA 与上游对照基准
2. `git submodule update --remote external/langflow` 拉取最新 dev 分支
3. 下一次 `launch.bat → [1]` 会自动重跑 `uv sync`（首次 5–10 分钟）
4. 在 Lobe Chat 桌面端上手动跑一轮 8 张 flow 的验收用例（火球术 / 技能搜索 / 智能路由），验收要点见 [`MIGRATION.md § 待维护者补齐`](../MIGRATION.md)
5. 若发现破坏性变更，回滚到上一个锁定 SHA 并在本文件记录已知问题
