# SkillRAG 快速开始指南

## 🚀 5分钟快速上手

### 步骤1: 准备Qwen3模型 (首次运行)

**重要：需要手动下载模型文件到本地**

1. 下载 Qwen3-Embedding-0.6B 模型到指定目录：
   ```
   SkillRAG/Data/models/Qwen3-Embedding-0.6B/
   ```

2. 下载方式：
   ```bash
   # 方法1: 使用 git lfs 克隆
   git lfs install
   git clone https://huggingface.co/Qwen/Qwen3-Embedding-0.6B SkillRAG/Data/models/Qwen3-Embedding-0.6B

   # 方法2: 从 HuggingFace 手动下载
   # 访问：https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
   # 下载所有文件到 SkillRAG/Data/models/Qwen3-Embedding-0.6B/ 目录
   ```

3. 确保目录结构：
   ```
   SkillRAG/Data/models/Qwen3-Embedding-0.6B/
   ├── config.json
   ├── model.safetensors
   ├── tokenizer.json
   ├── tokenizer_config.json
   └── ... (其他文件)
   ```

**预计时间**: 取决于网络速度（模型约1.2GB）

---

### 步骤2: 安装Python依赖

双击运行：
```
SkillRAG/setup.bat
```

**会自动完成**:
- ✅ 检查Python环境
- ✅ 安装Python依赖包（transformers, sentence-transformers等）

**预计时间**: 2-5分钟

---

### 步骤3: 配置路径

编辑 `SkillRAG/Python/config.yaml`：

```yaml
# 嵌入模型配置
embedding:
  model_name: "../Data/models/Qwen3-Embedding-0.6B"  # ← 本地模型路径
  device: "cpu"  # 或 "cuda" 如有GPU

# 技能索引配置
skill_indexer:
  skills_directory: "E:/YourPath/Assets/Skills"  # ← 修改为你的技能目录
```

**提示**: 使用正斜杠 `/` 而不是反斜杠 `\`

---

### 步骤4: 启动服务

双击运行：
```
SkillRAG/start_rag_server.bat
```

**看到以下信息说明启动成功**:
```
INFO: SkillRAG Server is ready!
INFO: Access API docs at: http://127.0.0.1:8765/docs
```

**保持此窗口运行**，不要关闭！

---

### 步骤5: Unity中使用

1. 打开Unity项目
2. 菜单栏 → **技能系统** → **RAG查询窗口**
3. 点击 **测试连接**
4. 看到 "✓ 连接成功" 即可开始使用

---

## 📖 基本使用

### 搜索技能

1. 在RAG查询窗口输入：
   ```
   火焰范围伤害技能
   ```

2. 点击 **搜索**

3. 查看结果：
   ```
   Flame Shockwave (相似度: 85%)
   - 文件: FlameShockwave.json
   - 6轨道, 15动作
   [打开] [查看详情]
   ```

### 参数推荐

1. 在技能编辑器中添加 `DamageAction`
2. 选中该Action
3. 自动显示 **AI参数建议** 面板
4. 点击 **应用** 按钮一键填充参数

---

## ❓ 常见问题

### Q1: setup.bat报错 "KeyError: 'qwen3'"

**原因**: transformers版本过低

**解决**:
```bash
pip install --upgrade transformers>=4.51.0
```

---

### Q2: 模型文件找不到

**原因**: 模型未正确下载到指定位置

**解决**:
1. 检查模型目录：`SkillRAG/Data/models/Qwen3-Embedding-0.6B/`
2. 确认目录中有 config.json 和 model.safetensors 等文件
3. 检查 config.yaml 中的 model_name 路径是否正确

---

### Q3: Unity连接失败

**检查清单**:
- [ ] Python服务器是否运行（`start_rag_server.bat`）
- [ ] 防火墙是否阻止端口8765
- [ ] Unity Preferences中服务器地址是否为 `http://127.0.0.1:8765`

---

### Q4: 搜索结果不相关

**解决**:
1. 重建索引:
   ```
   POST http://127.0.0.1:8765/index
   {"force_rebuild": true}
   ```

2. 确保技能有详细的 `skillDescription`

3. 使用更具体的查询词

---

### Q5: 首次启动较慢

**这是正常的！** 原因:
- 加载本地Qwen3模型（1.2GB到内存）
- 构建技能索引
- 生成向量嵌入

**后续启动会更快** (~5-10秒)

---

## 🔧 高级配置

### 使用GPU加速

编辑 `config.yaml`:
```yaml
embedding:
  device: "cuda"  # ← 改为cuda
  use_flash_attention: true  # ← 启用flash attention
```

**需要**:
- NVIDIA GPU (支持CUDA)
- 已安装PyTorch CUDA版本

---

### 调整搜索精度

```yaml
rag:
  similarity_threshold: 0.05  # 降低阈值返回更多结果
  top_k: 10  # 增加返回数量
```

---

### 自定义缓存位置

```yaml
embedding:
  cache_dir: "D:/MyCache/huggingface"  # 自定义缓存目录
```

---

## 📚 更多资源

| 文档 | 说明 |
|------|------|
| **README.md** | 完整功能介绍和架构说明 |
| **CHANGELOG_QWEN3.md** | Qwen3迁移详细说明 |
| **config.yaml** | 配置文件注释 |
| **API文档** | http://127.0.0.1:8765/docs |

---

## 🆘 获取帮助

1. 查看服务器日志: `SkillRAG/Data/rag_server.log`
2. 查看Unity Console日志（搜索 `[RAG]`）
3. 运行测试: `cd SkillRAG/Python && python embeddings.py`

---

## ✅ 检查清单

安装完成后，确认以下内容：

- [ ] Python 3.8+ 已安装
- [ ] Qwen3模型已下载到 `Data/models/Qwen3-Embedding-0.6B/`
- [ ] `setup.bat` 运行成功
- [ ] `config.yaml` 中模型路径和技能路径已配置
- [ ] `start_rag_server.bat` 运行中
- [ ] Unity中连接测试成功

**全部打勾？恭喜你可以开始使用了！** 🎉

---

<div align="center">

**遇到问题？** 查看 [README.md](README.md) 获取更多帮助

Made with ❤️ for Unity Skill Designers

</div>
