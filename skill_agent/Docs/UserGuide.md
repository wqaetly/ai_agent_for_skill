# skill_agent 使用指南

欢迎使用skill_agent！本指南将帮助你快速上手技能RAG系统。

## 目录

- [什么是skill_agent](#什么是skillrag)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [高级功能](#高级功能)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 什么是skill_agent？

skill_agent是一个基于**检索增强生成（RAG）**技术的智能技能辅助系统，专为Unity技能编辑器设计。它能够：

- 🔍 **语义搜索**：用自然语言描述查找相似技能
- 💡 **智能推荐**：根据上下文推荐Action类型和参数
- 📚 **知识库**：索引所有技能文件，建立可搜索的知识库
- ⚡ **实时更新**：技能文件修改后自动更新索引

### 核心概念

- **向量化**: 将技能描述转换为数学向量
- **语义搜索**: 基于含义而非关键词的搜索
- **嵌入模型**: 使用多语言BERT模型支持中英文
- **向量数据库**: LanceDB 嵌入式向量存储（本地文件）

---

## 快速开始

### 系统要求

**Python环境**:
- Python 3.8+
- 至少2GB可用内存
- 10GB磁盘空间（模型+数据）

**Unity环境**:
- Unity 2023.2+
- .NET Framework 4.x
- 现有的技能编辑器系统

### 安装步骤

#### 1. 安装Python依赖

打开命令行，进入`skill_agent/Python`目录：

```bash
cd skill_agent/Python
```

运行安装脚本（首次运行）：

```bash
# Windows
..\setup.bat

# 或手动安装
pip install -r requirements.txt
```

**注意**: 首次安装会下载约500MB的嵌入模型，请确保网络畅通。

#### 2. 配置服务器

编辑`config.yaml`文件，配置技能文件路径：

```yaml
skill_indexer:
  skills_directory: "../../ai_agent_for_skill/Assets/Skills"  # 修改为你的技能目录
```

#### 3. 启动RAG服务器

```bash
# Windows
python server.py

# 或使用启动脚本
..\start_rag_server.bat
```

看到以下信息说明启动成功：

```
INFO: skill_agent Server is ready!
INFO: Access API docs at: http://127.0.0.1:8765/docs
```

#### 4. 在Unity中启用RAG

1. 打开Unity项目
2. 菜单 → **技能系统 / RAG功能 / 启用RAG功能**
3. 菜单 → **Edit / Preferences / 技能系统 / RAG设置**
4. 点击**测试连接**确认连接成功

---

## 使用方法

### 1. RAG查询窗口

#### 打开窗口

菜单 → **技能系统 / RAG查询窗口**

#### 技能搜索

**Tab: 技能搜索**

1. 输入查询文本（例如："火焰伤害技能"）
2. 调整返回数量（1-20）
3. 勾选"返回详细信息"查看更多数据
4. 点击"搜索"

**搜索示例**:
- "造成范围伤害的火焰技能"
- "带有冲锋效果的突进技能"
- "治疗友军并增加移速"
- "召唤单位攻击敌人"

**结果操作**:
- **打开技能文件**: 在技能编辑器中打开该技能
- **复制ID**: 复制skill_id到剪贴板
- **相似度**: 0.8+高度相似，0.6-0.8中度相似，<0.6低相似

---

#### Action推荐

**Tab: Action推荐**

1. 描述你想要的效果（例如："造成伤害并击退敌人"）
2. 调整推荐数量
3. 点击"获取推荐"

**推荐结果包含**:
- Action类型名称
- 出现频率（在相似技能中）
- 参数示例（来自实际技能）
- 可直接应用到编辑器

**推荐示例**:
- "对敌人造成持续伤害" → DamageAction + AreaOfEffectAction
- "快速移动到目标位置" → MovementAction + TeleportAction
- "眩晕并减速敌人" → ControlAction + BuffAction

---

#### 管理功能

**Tab: 管理**

- **更新索引**: 扫描新增/修改的技能文件
- **重建索引**: 清空并重新索引所有技能（慎用）
- **清空缓存**: 清除查询缓存，强制重新计算
- **获取统计信息**: 查看查询次数、缓存命中率等

**何时需要重建索引**:
- 批量修改技能文件后
- 索引数据损坏
- 更换嵌入模型后

---

### 2. 智能Action检查器

**自动启用**（如果在Preferences中启用"自动显示参数建议"）

在技能编辑器中选中任何Action时，会自动显示"🤖 AI参数建议"面板：

#### 功能说明

1. **参数示例**: 显示相似技能中的实际参数配置
2. **来源技能**: 参数来自哪个技能
3. **一键应用**: 点击"应用"按钮直接填充参数
4. **批量应用**: 应用整套参数配置

#### 使用场景

**示例1: 配置DamageAction**

1. 添加DamageAction到轨道
2. 选中该Action
3. 查看AI建议的baseDamage、damageType等参数
4. 点击"应用"按钮快速配置

**示例2: 学习参数组合**

- 查看其他技能如何配置MovementAction
- 了解常用的movementSpeed值范围
- 学习参数之间的配合关系

---

### 3. 编辑器集成

#### 首选项设置

**Edit / Preferences / 技能系统 / RAG设置**

- **启用RAG功能**: 总开关
- **自动显示参数建议**: 是否在ActionInspector中显示AI建议
- **服务器地址**: RAG服务器IP（默认127.0.0.1）
- **服务器端口**: RAG服务器端口（默认8765）

#### 菜单快捷方式

**技能系统 / RAG功能**:
- 打开RAG查询窗口
- 启用/禁用RAG功能
- 自动显示参数建议
- 重建索引

---

## 高级功能

### 1. API调用

#### 在脚本中使用RAG

```csharp
using SkillSystem.RAG;

// 创建客户端
var ragClient = new RAGClient();

// 搜索技能
StartCoroutine(ragClient.SearchSkills(
    "火焰伤害",
    topK: 5,
    returnDetails: true,
    (success, response, error) => {
        if (success) {
            foreach (var result in response.results) {
                Debug.Log($"找到: {result.skill_name} (相似度: {result.similarity})");
            }
        }
    }
));

// 推荐Action
StartCoroutine(ragClient.RecommendActions(
    "造成伤害并击退",
    topK: 3,
    (success, response, error) => {
        if (success) {
            foreach (var rec in response.recommendations) {
                Debug.Log($"推荐: {rec.action_type}");
            }
        }
    }
));
```

#### 自定义集成

参考`RAGEditorIntegration.cs`了解如何将RAG功能集成到自定义编辑器。

---

### 2. 配置优化

#### 调整搜索精度

编辑`config.yaml`:

```yaml
rag:
  top_k: 5  # 增加返回更多结果
  similarity_threshold: 0.5  # 降低阈值返回更多结果（可能不相关）
```

#### 启用/禁用文件监听

```yaml
skill_indexer:
  watch_enabled: true  # false则需手动触发索引
```

#### 调整缓存时间

```yaml
rag:
  cache_enabled: true
  cache_ttl: 3600  # 缓存生存时间（秒）
```

---

### 3. 性能优化

#### 减少内存占用

```yaml
embedding:
  batch_size: 16  # 降低批量大小
  cache_dir: "../Data/embeddings_cache"  # 使用磁盘缓存
```

#### 加速查询

- 使用缓存（默认启用）
- 限制top_k数量
- 避免频繁重建索引

#### 并发处理

RAG服务器支持异步处理，Unity客户端可并发发送多个请求。

---

## 常见问题

### Q1: 连接失败，显示"Connection error"

**原因**:
- Python服务器未启动
- 端口被占用
- 防火墙阻止

**解决方案**:
1. 确认Python服务器正在运行
2. 检查`config.yaml`中的端口配置
3. 在Unity Preferences中测试连接

---

### Q2: 搜索结果不相关

**原因**:
- 索引数据不完整
- 相似度阈值过低
- 技能描述不够详细

**解决方案**:
1. 重建索引（管理 → 重建索引）
2. 提高相似度阈值
3. 使用更具体的查询词

---

### Q3: 首次启动很慢

**原因**: 需要下载嵌入模型（约500MB）

**解决方案**:
- 耐心等待首次下载
- 后续启动会快很多
- 模型缓存在`Data/embeddings_cache`

---

### Q4: 推荐的Action参数无法应用

**原因**:
- 字段名称不匹配
- 类型转换失败
- Action版本不一致

**解决方案**:
- 查看Console日志了解详情
- 手动复制参数值
- 更新技能定义

---

### Q5: 索引后技能数量为0

**原因**:
- 技能目录路径错误
- JSON文件格式错误
- 权限问题

**解决方案**:
1. 检查`config.yaml`中的`skills_directory`路径
2. 确认Skills文件夹中有.json文件
3. 查看服务器日志了解错误详情

---

## 最佳实践

### 1. 技能命名规范

**推荐做法**:
- 使用描述性的`skillName`和`skillDescription`
- 中英文混合支持更好
- 包含关键效果词汇（伤害、治疗、控制等）

**示例**:
```json
{
  "skillName": "Flame Shockwave",
  "skillDescription": "释放一道火焰冲击波，对路径上的敌人造成魔法伤害并击退",
  "skillId": "flame-shockwave-001"
}
```

---

### 2. 查询技巧

**精确查询**:
- "火焰 + 范围 + 伤害"
- "单体 + 高爆发 + 物理伤害"

**模糊查询**:
- "类似瑞文Q技能"
- "带位移的伤害技能"

**效果导向**:
- "想要一个控制技能"
- "需要AOE清兵能力"

---

### 3. 参数调优

**参考AI建议后微调**:
1. 先应用AI推荐的参数
2. 在编辑器中测试效果
3. 根据实际需求微调数值
4. 保存并重新索引

**平衡性考虑**:
- 不要完全照搬，考虑技能整体平衡
- 参考多个示例取平均值
- 遵循游戏设计规范

---

### 4. 团队协作

**共享索引**:
- 定期重建索引并提交
- 使用统一的技能命名规范
- 文档化特殊技能设计

**版本控制**:
- 技能JSON文件纳入Git
- 索引缓存不纳入版本控制
- 每次pull后重新索引

---

### 5. 维护建议

**定期维护**:
- 每周重建一次索引
- 清理无用的技能文件
- 检查RAG服务器日志

**监控性能**:
- 查看统计信息了解使用情况
- 监控查询响应时间
- 注意缓存命中率

---

## 快捷键参考

| 操作 | 快捷键/路径 |
|------|-------------|
| 打开RAG窗口 | 技能系统 → RAG查询窗口 |
| 技能搜索 | RAG窗口 → 技能搜索Tab |
| Action推荐 | RAG窗口 → Action推荐Tab |
| 设置 | Edit → Preferences → 技能系统 |
| 重建索引 | 技能系统 → RAG功能 → 重建索引 |

---

## 进阶阅读

- **API文档**: 查看完整的REST API接口说明
- **Action参考**: 了解所有Action类型的参数
- **技能模式**: 学习常见的技能设计模式
- **在线文档**: 访问 http://127.0.0.1:8765/docs

---

## 技术支持

### 查看日志

**Python服务器日志**:
```
skill_agent/Data/rag_server.log
```

**Unity Console**:
- 搜索`[RAG]`或`[SmartActionInspector]`前缀

### 报告问题

遇到问题时，请提供：
1. 错误信息（截图或日志）
2. 操作步骤
3. Unity版本和Python版本
4. config.yaml配置

---

## 版本历史

- **v1.0.0** (2025-01-29): 初始发布
  - 技能语义搜索
  - Action智能推荐
  - Unity编辑器集成
  - 实时文件监听

---

## 下一步

1. ✅ 启动RAG服务器
2. ✅ 在Unity中测试连接
3. ✅ 尝试搜索你的第一个技能
4. ✅ 使用AI推荐配置Action
5. 📚 阅读进阶文档了解更多功能

**祝你使用愉快！** 🎉

如有问题，请查阅[常见问题](#常见问题)或查看详细日志。
