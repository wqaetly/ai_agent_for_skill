# Qwen3 嵌入模型自动下载

## 概述

skill_agent 使用 **Qwen3-Embedding-0.6B** 作为 RAG 系统的向量嵌入模型。启动脚本会自动检测模型完整性，并在需要时自动下载。

## 模型信息

- **模型名称**: Qwen3-Embedding-0.6B
- **来源**: HuggingFace - `Qwen/Qwen3-Embedding-0.6B`
- **大小**: 约 1.3 GB
- **下载时间**: 3-10 分钟（取决于网络速度）
- **嵌入维度**: 1024
- **上下文长度**: 32K tokens

## 自动下载流程

### 启动时自动检查

运行 `start_webui_with_logs.bat` 时会自动：

1. **检查模型完整性**
   - 验证 `model.safetensors` 是否存在（>1GB）
   - 验证配置文件和 tokenizer

2. **自动下载**（如果缺失）
   - 显示下载进度
   - 下载完成后验证文件完整性

3. **继续启动服务**
   - 模型验证通过后启动 LangGraph 服务

### 手动下载模型

如果需要单独下载或更新模型：

```bash
# 方式1: 使用批处理脚本（推荐）
skill_agent\download_model.bat

# 方式2: 直接运行 Python 脚本
cd skill_agent
venv\Scripts\activate
python check_and_download_model.py
```

## 模型位置

```
skill_agent/
└── Data/
    └── models/
        └── Qwen3-Embedding-0.6B/
            ├── model.safetensors      # 权重文件 (1.2GB)
            ├── config.json             # 模型配置
            ├── tokenizer.json          # Tokenizer
            ├── tokenizer_config.json
            ├── vocab.json
            └── ...
```

## 配置文件

模型配置在 `core_config.yaml`:

```yaml
embedding:
  model_name: "Data/models/Qwen3-Embedding-0.6B"
  device: "cpu"  # 或 "cuda" (GPU)
  batch_size: 32
  max_length: 8192
```

## 故障排查

### 下载失败

**问题**: 网络连接 HuggingFace 失败

**解决方案**:
1. 检查网络连接
2. 使用代理或镜像站
3. 手动下载：
   ```bash
   # 安装下载工具
   pip install -U huggingface-hub

   # 使用命令行下载
   huggingface-cli download Qwen/Qwen3-Embedding-0.6B --local-dir skill_agent/Data/models/Qwen3-Embedding-0.6B
   ```

### 文件不完整

**问题**: 下载中断或文件损坏

**解决方案**:
```bash
# 删除不完整的文件
del skill_agent\Data\models\Qwen3-Embedding-0.6B\model.safetensors

# 重新运行下载
skill_agent\download_model.bat
```

### 磁盘空间不足

**问题**: 需要至少 2GB 可用空间

**解决方案**:
1. 清理磁盘空间
2. 或更换模型存储位置（修改 `core_config.yaml` 中的 `model_name`）

## 使用其他模型

如需使用其他嵌入模型，修改 `core_config.yaml`:

```yaml
embedding:
  # 使用轻量级多语言模型（自动下载）
  model_name: "paraphrase-multilingual-MiniLM-L12-v2"
  max_length: 512

  # 或使用其他 Qwen3 尺寸
  # model_name: "Qwen/Qwen3-Embedding-4B"  # 更大更准确
```

## 依赖项

模型下载需要以下依赖（已包含在 `requirements_ml.txt`）:

- `torch>=2.0.0` - PyTorch 张量计算
- `sentence-transformers>=2.2.0` - 模型加载框架
- `psycopg[binary]>=3.2.0` - PostgreSQL 向量数据库驱动
- `huggingface-hub>=1.0.0` - 模型下载工具

## 相关文件

- `check_and_download_model.py` - 模型检查和下载脚本
- `download_model.bat` - Windows 批处理下载脚本
- `requirements_ml.txt` - ML 依赖清单
- `core_config.yaml` - 嵌入模型配置
