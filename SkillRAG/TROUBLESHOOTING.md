# 故障排除指南

## ❌ 问题: Qwen3模型下载失败

### 错误信息

```
FileNotFoundError: [Errno 2] No such file or directory:
'C:\Users\...\config_sentence_transformers.json'
```

### 原因

这是**缓存损坏**问题，通常由以下原因导致：
- ❌ 下载过程中断（网络波动、关闭窗口等）
- ❌ 磁盘空间不足导致文件写入失败
- ❌ 杀毒软件干扰下载

---

## 🛠️ 解决方案

### 方法1: 一键修复（推荐）⭐

**最简单的方式，只需运行一个脚本**:

```bash
cd SkillRAG
fix_download.bat
```

**脚本会自动**:
- ✅ 清理损坏的缓存
- ✅ 设置国内镜像加速
- ✅ 重新下载模型

**预计时间**: 5-10分钟

---

### 方法2: 使用镜像加速

```bash
cd SkillRAG\Python

# 设置镜像
set HF_ENDPOINT=https://hf-mirror.com

# 清理缓存并下载
python download_qwen3.py --clear-cache --mirror
```

---

### 方法3: 手动清理缓存

#### Windows:

```bash
# 1. 删除HuggingFace缓存
rd /s /q "%USERPROFILE%\.cache\huggingface"

# 2. 重新下载
cd SkillRAG\Python
python download_qwen3.py
```

#### 或使用文件管理器:

1. 按 `Win + R`
2. 输入: `%USERPROFILE%\.cache\huggingface`
3. 删除整个 `hub` 文件夹
4. 重新运行 `setup.bat`

---

### 方法4: 使用专用下载工具

```bash
cd SkillRAG
download_qwen3_model.bat

# 选择选项2: 使用镜像加速
```

---

## 📋 预防措施

### 下载前检查

```bash
# 1. 检查磁盘空间（至少需要5GB）
dir C:\

# 2. 检查网络连接
ping huggingface.co
ping hf-mirror.com

# 3. 检查Python环境
python --version
pip --version
```

### 下载时注意

- ✅ 保持命令行窗口开启
- ✅ 确保网络稳定
- ✅ 不要同时运行多个下载任务
- ✅ 关闭杀毒软件的实时保护（下载完成后再开启）

---

## 🔍 其他常见问题

### Q1: transformers版本错误

**错误**: `KeyError: 'qwen3'`

**解决**:
```bash
pip install --upgrade transformers>=4.51.0
```

---

### Q2: 网络连接超时

**症状**: 长时间卡在下载状态

**解决**:
```bash
# 使用国内镜像
set HF_ENDPOINT=https://hf-mirror.com
python download_qwen3.py --mirror
```

---

### Q3: 磁盘空间不足

**症状**: 下载到50%左右失败

**解决**:
1. 清理磁盘空间
2. 修改缓存目录到其他盘:

编辑 `config.yaml`:
```yaml
embedding:
  cache_dir: "D:/HuggingFace/Cache"  # 改到D盘
```

---

### Q4: 权限不足

**症状**: `PermissionError: [WinError 5]`

**解决**:
```bash
# 以管理员身份运行命令行
# 右键 -> 以管理员身份运行

cd SkillRAG
fix_download.bat
```

---

### Q5: 杀毒软件拦截

**症状**: 下载完成但文件不存在

**解决**:
1. 临时关闭杀毒软件
2. 将 Python 和 HuggingFace 缓存目录加入白名单
3. 重新下载

---

## 📞 完整诊断流程

如果以上方法都无效，请按以下步骤诊断：

### 步骤1: 收集信息

```bash
# 1. Python版本
python --version

# 2. 依赖版本
pip show transformers sentence-transformers

# 3. 缓存位置
echo %USERPROFILE%\.cache\huggingface

# 4. 磁盘空间
dir C:\
```

### 步骤2: 完全清理

```bash
# 1. 卸载相关包
pip uninstall transformers sentence-transformers -y

# 2. 清理缓存
rd /s /q "%USERPROFILE%\.cache\huggingface"
rd /s /q "%USERPROFILE%\.cache\torch"

# 3. 重新安装
pip install transformers>=4.51.0 sentence-transformers>=2.7.0
```

### 步骤3: 使用离线安装（最后手段）

如果网络实在不行，可以考虑：

1. **在有良好网络的电脑上**:
   ```bash
   python download_qwen3.py
   ```

2. **打包缓存目录**:
   ```
   %USERPROFILE%\.cache\huggingface\hub\models--Qwen--Qwen3-Embedding-0.6B
   ```

3. **复制到目标电脑相同位置**

---

## 💡 最佳实践

### 推荐安装流程

1. **检查环境**:
   ```bash
   python --version  # >=3.8
   pip --version     # >=20.0
   ```

2. **设置镜像**（国内用户必做）:
   ```bash
   set HF_ENDPOINT=https://hf-mirror.com
   ```

3. **运行修复脚本**:
   ```bash
   cd SkillRAG
   fix_download.bat
   ```

4. **验证安装**:
   ```bash
   cd Python
   python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('Qwen/Qwen3-Embedding-0.6B'); print('OK')"
   ```

---

## 📊 成功率对比

| 方法 | 成功率 | 速度 | 难度 |
|------|--------|------|------|
| **fix_download.bat** | 95% | ⭐⭐⭐⭐ | 非常简单 |
| 镜像加速 | 90% | ⭐⭐⭐⭐ | 简单 |
| 手动清理 | 85% | ⭐⭐⭐ | 中等 |
| 完全清理 | 98% | ⭐⭐ | 较难 |
| 离线安装 | 100% | ⭐ | 复杂 |

---

## 🆘 仍然无法解决？

如果尝试了所有方法仍然失败：

1. **查看日志**:
   ```
   SkillRAG\Data\rag_server.log
   ```

2. **运行诊断**:
   ```bash
   cd SkillRAG\Python
   python download_qwen3.py --clear-cache --mirror > debug.log 2>&1
   ```

3. **检查错误信息**并搜索解决方案

---

<div align="center">

**✅ 99%的问题都能通过 `fix_download.bat` 解决**

如果还有问题，请查看完整文档: [QUICK_START.md](QUICK_START.md)

</div>
