# RAG索引错误排查指南

## 🔴 错误信息

```
[RAG] 开始重建索引...
[18:37:22] [RAG异常] An error occurred while sending the request
```

---

## 📋 问题分析

### 错误原因

这个错误表示 **Unity编辑器无法连接到RAG服务器**。具体原因可能是：

1. ❌ **RAG服务器未启动**（最常见）
2. ❌ **服务器端口被占用或配置错误**
3. ❌ **防火墙阻止了连接**
4. ❌ **Python环境或依赖问题**

### 技术细节

- **错误来源**: `EditorRAGClient.TriggerIndexAsync()` 方法
- **请求地址**: `http://127.0.0.1:8765/index`
- **请求方式**: HTTP POST
- **超时时间**: 30秒

---

## ✅ 解决方案

### 方案1: 启动RAG服务器（推荐）

#### 步骤1: 打开RAG查询窗口

1. 在Unity编辑器菜单栏点击：**技能系统 > RAG查询窗口**
2. 窗口会自动打开

#### 步骤2: 启动服务器

在RAG查询窗口中：
- 点击 **🚀 启动服务器** 按钮
- 等待服务器启动（通常需要5-10秒）
- 看到 **✅ 服务器运行中** 状态

#### 步骤3: 验证连接

- 点击 **🔍 健康检查** 按钮
- 如果显示 "✅ 服务器正常"，说明连接成功

#### 步骤4: 重新尝试重建索引

返回描述管理器窗口：
- 点击 **🔨 重建RAG索引** 按钮
- 等待索引完成

---

### 方案2: 手动启动Python服务器

如果Unity内置启动失败，可以手动启动：

#### Windows系统

```powershell
# 1. 打开PowerShell
# 2. 进入Python目录
cd E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Python

# 3. 激活虚拟环境（如果有）
# .venv\Scripts\Activate.ps1

# 4. 启动服务器
python rag_server.py
```

#### 预期输出

```
=== RAG服务器启动 ===
配置文件: config.yaml
监听地址: 127.0.0.1:8765

✅ 服务器启动成功！
访问 http://127.0.0.1:8765/health 检查状态
```

---

### 方案3: 检查端口占用

#### 检查端口是否被占用

```powershell
# Windows
netstat -ano | findstr :8765

# 如果有输出，说明端口被占用
```

#### 解决端口占用

**选项A: 关闭占用端口的程序**
```powershell
# 找到PID（进程ID）
netstat -ano | findstr :8765

# 结束进程（替换<PID>为实际的进程ID）
taskkill /PID <PID> /F
```

**选项B: 修改配置使用其他端口**

编辑 `SkillRAG/Python/config.yaml`:
```yaml
server:
  host: "127.0.0.1"
  port: 8766  # 改为其他端口
```

同时修改Unity中的配置（如果有配置文件）。

---

### 方案4: 检查Python环境

#### 验证Python安装

```powershell
# 检查Python版本（需要3.8+）
python --version

# 检查pip
pip --version
```

#### 安装依赖

```powershell
cd E:/Study/wqaetly/ai_agent_for_skill/SkillRAG/Python

# 安装所有依赖
pip install -r requirements.txt
```

#### 常见依赖问题

如果缺少某些包：
```powershell
pip install fastapi uvicorn chromadb sentence-transformers pyyaml
```

---

## 🔍 诊断工具

### 快速诊断脚本

创建 `test_connection.py`:

```python
import requests
import sys

def test_rag_server():
    """测试RAG服务器连接"""
    url = "http://127.0.0.1:8765/health"
    
    try:
        print(f"正在连接: {url}")
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print("✅ 服务器连接成功！")
            print(f"响应: {response.json()}")
            return True
        else:
            print(f"❌ 服务器返回错误: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器（服务器未启动）")
        return False
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_rag_server()
    sys.exit(0 if success else 1)
```

运行测试：
```powershell
python test_connection.py
```

---

## 🛡️ 预防措施

### 1. 工作流程建议

**正确的操作顺序**：
```
1. 启动Unity编辑器
2. 打开RAG查询窗口
3. 启动RAG服务器
4. 使用描述管理器
5. 重建索引
```

### 2. 自动启动配置

可以配置Unity在启动时自动检查并启动RAG服务器。

### 3. 服务器状态监控

在描述管理器中添加服务器状态指示器：
- 🟢 绿色：服务器运行中
- 🔴 红色：服务器未连接
- 🟡 黄色：连接中

---

## 📊 常见问题FAQ

### Q1: 为什么每次都要手动启动服务器？

**A**: RAG服务器是一个独立的Python进程，不会随Unity自动启动。建议：
- 在开始工作前先启动服务器
- 或者配置自动启动脚本

### Q2: 服务器启动后多久会自动关闭？

**A**: 服务器会一直运行，直到：
- 手动点击"停止服务器"
- 关闭Unity编辑器
- 系统重启

### Q3: 可以在没有服务器的情况下使用描述管理器吗？

**A**: 可以！描述管理器的大部分功能不需要服务器：
- ✅ 扫描Actions
- ✅ AI生成描述
- ✅ 编辑描述
- ✅ 保存到数据库
- ✅ 导出JSON
- ❌ 重建RAG索引（需要服务器）

### Q4: 索引重建失败会影响其他功能吗？

**A**: 不会！索引重建只影响RAG搜索功能：
- 描述管理器的其他功能正常
- 已有的索引数据不会丢失
- 可以稍后重试

### Q5: 如何确认索引是否成功？

**A**: 在RAG查询窗口中：
1. 点击"获取统计信息"
2. 查看索引数量
3. 尝试搜索测试

---

## 🔧 高级故障排查

### 查看详细日志

#### Unity日志
- 位置: `Unity编辑器 > Console窗口`
- 筛选: 搜索 "RAG"

#### Python服务器日志
- 如果手动启动: 查看终端输出
- 日志文件: `SkillRAG/Python/logs/server.log`（如果配置了）

### 网络抓包

使用Fiddler或Wireshark查看HTTP请求：
- 目标地址: `127.0.0.1:8765`
- 请求路径: `/index`
- 请求方法: POST

### 防火墙检查

```powershell
# Windows防火墙规则
netsh advfirewall firewall show rule name=all | findstr 8765
```

---

## 📞 获取帮助

如果以上方法都无法解决问题：

1. **收集信息**：
   - Unity版本
   - Python版本
   - 错误日志（完整）
   - 操作系统版本

2. **检查配置文件**：
   - `SkillRAG/Python/config.yaml`
   - 服务器配置

3. **尝试最小化测试**：
   - 单独运行Python服务器
   - 使用浏览器访问 `http://127.0.0.1:8765/health`
   - 使用Postman测试API

---

## ✨ 改进建议

### 对描述管理器的改进

我建议在描述管理器中添加以下功能：

1. **服务器状态指示器**
   ```
   🟢 RAG服务器: 运行中 (127.0.0.1:8765)
   ```

2. **自动连接测试**
   - 在点击"重建索引"前自动检查连接
   - 如果失败，提示用户启动服务器

3. **快捷启动按钮**
   ```
   [🚀 启动RAG服务器] [🔍 测试连接]
   ```

4. **更详细的错误信息**
   ```
   ❌ 无法连接到RAG服务器
   
   可能原因:
   - 服务器未启动
   - 端口8765被占用
   
   解决方法:
   1. 打开 技能系统 > RAG查询窗口
   2. 点击 启动服务器
   3. 重试
   ```

---

## 📝 总结

**最常见的解决方案（90%的情况）**：

```
1. 打开 技能系统 > RAG查询窗口
2. 点击 🚀 启动服务器
3. 等待启动完成
4. 返回描述管理器
5. 点击 🔨 重建RAG索引
```

**记住**：RAG索引重建需要服务器运行，但描述管理器的其他功能都可以独立使用！

---

*最后更新: 2025-11-01*
