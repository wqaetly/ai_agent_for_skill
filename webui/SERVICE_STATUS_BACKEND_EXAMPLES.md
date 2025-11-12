# 后端API实现示例

本文档提供RAG服务和Unity连接状态API的实现示例。

## Python (FastAPI) 实现

### 完整示例

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio

app = FastAPI(title="Service Status API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # WebUI地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态（实际应用中应使用数据库或缓存）
class ServiceState:
    def __init__(self):
        self.rag_available = True
        self.unity_connected = False
        
service_state = ServiceState()

# 响应模型
class HealthResponse(BaseModel):
    status: str

class UnityStatusResponse(BaseModel):
    connected: bool
    client_info: Optional[dict] = None

# RAG服务健康检查
@app.get("/rag/health", response_model=HealthResponse)
async def rag_health_check():
    """
    RAG服务健康检查端点
    
    Returns:
        - 200: 服务正常
        - 503: 服务不可用
    """
    if service_state.rag_available:
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=503, detail="RAG service unavailable")

# Unity连接状态
@app.get("/unity/status", response_model=UnityStatusResponse)
async def unity_connection_status():
    """
    Unity连接状态端点
    
    Returns:
        - connected: Unity客户端是否已连接
        - client_info: Unity客户端信息（可选）
    """
    return {
        "connected": service_state.unity_connected,
        "client_info": {
            "version": "2022.3.0f1",
            "platform": "Windows",
            "last_heartbeat": "2025-01-12T12:00:00Z"
        } if service_state.unity_connected else None
    }

# 管理端点（用于测试）
@app.post("/admin/rag/toggle")
async def toggle_rag_status():
    """切换RAG服务状态（仅用于测试）"""
    service_state.rag_available = not service_state.rag_available
    return {"rag_available": service_state.rag_available}

@app.post("/admin/unity/toggle")
async def toggle_unity_status():
    """切换Unity连接状态（仅用于测试）"""
    service_state.unity_connected = not service_state.unity_connected
    return {"unity_connected": service_state.unity_connected}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2024)
```

### 运行方式

```bash
# 安装依赖
pip install fastapi uvicorn

# 运行服务
python main.py
```

### 测试API

```bash
# 测试RAG健康检查
curl http://localhost:2024/rag/health

# 测试Unity状态
curl http://localhost:2024/unity/status

# 切换RAG状态（测试用）
curl -X POST http://localhost:2024/admin/rag/toggle

# 切换Unity状态（测试用）
curl -X POST http://localhost:2024/admin/unity/toggle
```

## Node.js (Express) 实现

### 完整示例

```javascript
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 2024;

// 配置CORS
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true
}));

app.use(express.json());

// 全局状态
const serviceState = {
  ragAvailable: true,
  unityConnected: false,
  unityClientInfo: null
};

// RAG服务健康检查
app.get('/rag/health', (req, res) => {
  if (serviceState.ragAvailable) {
    res.json({ status: 'ok' });
  } else {
    res.status(503).json({ 
      status: 'error',
      message: 'RAG service unavailable' 
    });
  }
});

// Unity连接状态
app.get('/unity/status', (req, res) => {
  res.json({
    connected: serviceState.unityConnected,
    client_info: serviceState.unityConnected ? {
      version: '2022.3.0f1',
      platform: 'Windows',
      last_heartbeat: new Date().toISOString()
    } : null
  });
});

// 管理端点（用于测试）
app.post('/admin/rag/toggle', (req, res) => {
  serviceState.ragAvailable = !serviceState.ragAvailable;
  res.json({ rag_available: serviceState.ragAvailable });
});

app.post('/admin/unity/toggle', (req, res) => {
  serviceState.unityConnected = !serviceState.unityConnected;
  res.json({ unity_connected: serviceState.unityConnected });
});

app.listen(PORT, () => {
  console.log(`Service Status API running on http://localhost:${PORT}`);
  console.log(`RAG Health: http://localhost:${PORT}/rag/health`);
  console.log(`Unity Status: http://localhost:${PORT}/unity/status`);
});
```

### 运行方式

```bash
# 安装依赖
npm install express cors

# 运行服务
node server.js
```

## 集成到现有LangGraph服务

如果您已经有LangGraph服务，可以添加这些端点：

### Python (LangGraph) 集成

```python
from langgraph.graph import StateGraph
from fastapi import FastAPI

# 假设您已有的LangGraph应用
app = FastAPI()

# 添加RAG健康检查
@app.get("/rag/health")
async def rag_health():
    try:
        # 检查RAG服务是否可用
        # 例如：检查向量数据库连接
        # vector_db.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 503

# 添加Unity状态检查
@app.get("/unity/status")
async def unity_status():
    # 检查Unity WebSocket连接
    # 或检查最近的心跳时间
    unity_manager = get_unity_connection_manager()
    return {
        "connected": unity_manager.is_connected(),
        "client_info": unity_manager.get_client_info()
    }
```

## 实际生产环境建议

### 1. RAG服务健康检查

```python
@app.get("/rag/health")
async def rag_health_check():
    """
    实际的RAG健康检查应该包括：
    1. 向量数据库连接检查
    2. 嵌入模型可用性检查
    3. 检索服务响应时间检查
    """
    try:
        # 检查向量数据库
        await vector_db.ping()
        
        # 检查嵌入模型
        test_embedding = await embedding_model.embed("test")
        
        # 检查检索服务
        start_time = time.time()
        await retriever.search("test", k=1)
        latency = time.time() - start_time
        
        if latency > 5.0:  # 如果延迟超过5秒
            return {"status": "degraded", "latency": latency}, 200
            
        return {"status": "ok", "latency": latency}
        
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
```

### 2. Unity连接状态

```python
class UnityConnectionManager:
    def __init__(self):
        self.connections = {}
        self.heartbeat_timeout = 30  # 30秒无心跳视为断开
    
    def is_connected(self) -> bool:
        """检查是否有活跃的Unity连接"""
        now = time.time()
        active_connections = [
            conn for conn in self.connections.values()
            if now - conn.last_heartbeat < self.heartbeat_timeout
        ]
        return len(active_connections) > 0
    
    def get_client_info(self) -> Optional[dict]:
        """获取Unity客户端信息"""
        if not self.is_connected():
            return None
        
        # 返回最近活跃的连接信息
        latest_conn = max(
            self.connections.values(),
            key=lambda x: x.last_heartbeat
        )
        
        return {
            "version": latest_conn.unity_version,
            "platform": latest_conn.platform,
            "last_heartbeat": latest_conn.last_heartbeat,
            "session_id": latest_conn.session_id
        }

unity_manager = UnityConnectionManager()

@app.get("/unity/status")
async def unity_status():
    return {
        "connected": unity_manager.is_connected(),
        "client_info": unity_manager.get_client_info()
    }
```

## 监控和日志

### 添加日志记录

```python
import logging

logger = logging.getLogger(__name__)

@app.get("/rag/health")
async def rag_health_check():
    logger.info("RAG health check requested")
    try:
        # 健康检查逻辑
        result = await check_rag_service()
        logger.info(f"RAG health check result: {result}")
        return result
    except Exception as e:
        logger.error(f"RAG health check failed: {e}", exc_info=True)
        raise
```

### 添加指标收集

```python
from prometheus_client import Counter, Histogram

# 定义指标
health_check_counter = Counter(
    'health_check_total',
    'Total health check requests',
    ['service', 'status']
)

health_check_duration = Histogram(
    'health_check_duration_seconds',
    'Health check duration',
    ['service']
)

@app.get("/rag/health")
async def rag_health_check():
    with health_check_duration.labels(service='rag').time():
        try:
            result = await check_rag_service()
            health_check_counter.labels(service='rag', status='success').inc()
            return result
        except Exception as e:
            health_check_counter.labels(service='rag', status='error').inc()
            raise
```

## 安全考虑

### 1. API Key验证

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

@app.get("/rag/health", dependencies=[Depends(verify_api_key)])
async def rag_health_check():
    return {"status": "ok"}
```

### 2. 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/rag/health")
@limiter.limit("10/minute")
async def rag_health_check(request: Request):
    return {"status": "ok"}
```

## 测试脚本

### Python测试脚本

```python
import requests
import time

def test_service_status():
    base_url = "http://localhost:2024"
    
    # 测试RAG健康检查
    print("Testing RAG health check...")
    response = requests.get(f"{base_url}/rag/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 测试Unity状态
    print("\nTesting Unity status...")
    response = requests.get(f"{base_url}/unity/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 测试响应时间
    print("\nTesting response time...")
    start = time.time()
    requests.get(f"{base_url}/rag/health")
    latency = (time.time() - start) * 1000
    print(f"Latency: {latency:.2f}ms")

if __name__ == "__main__":
    test_service_status()
```

## 部署建议

1. **使用反向代理**: 通过Nginx或Traefik代理API请求
2. **启用HTTPS**: 生产环境必须使用HTTPS
3. **配置监控**: 使用Prometheus + Grafana监控API性能
4. **设置告警**: 当服务不可用时发送告警
5. **负载均衡**: 使用负载均衡器分发请求

## 相关文档

- [功能说明文档](./SERVICE_STATUS_GUIDE.md)
- [实现总结](./SERVICE_STATUS_IMPLEMENTATION.md)
- [架构图](./SERVICE_STATUS_ARCHITECTURE.md)
