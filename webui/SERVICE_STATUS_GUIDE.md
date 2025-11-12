# 服务状态监控功能说明

本文档说明如何使用WebUI中新增的RAG服务和Unity连接状态监控功能。

## 功能概述

WebUI现在支持实时监控以下服务的连接状态：

1. **RAG服务状态** - 显示RAG（检索增强生成）服务的连接状态
2. **Unity连接状态** - 显示Unity客户端的连接状态

## 界面展示

状态指示器显示在聊天界面的顶部工具栏中，位于GitHub图标和"New thread"按钮之前。

每个状态指示器包含：
- 服务名称（RAG / Unity）
- 状态图标和文本
- 鼠标悬停时显示详细信息（延迟、最后检查时间、错误信息等）

## 状态类型

每个服务可能处于以下状态之一：

| 状态 | 图标 | 颜色 | 说明 |
|------|------|------|------|
| Connected | ✓ | 绿色 | 服务正常连接 |
| Disconnected | ✗ | 红色 | 服务未连接或无法访问 |
| Checking | ○ | 黄色 | 正在检查连接状态 |
| Error | ⚠ | 橙色 | 连接时发生错误 |

## 后端API要求

为了使状态监控正常工作，后端服务需要提供以下API端点：

### 1. RAG服务健康检查

**端点**: `GET /rag/health`

**响应示例**:
```json
{
  "status": "ok"
}
```

**HTTP状态码**:
- `200 OK` - 服务正常
- `503 Service Unavailable` - 服务不可用

### 2. Unity连接状态

**端点**: `GET /unity/status`

**响应示例**:
```json
{
  "connected": true
}
```

**字段说明**:
- `connected` (boolean): Unity客户端是否已连接

**HTTP状态码**:
- `200 OK` - 请求成功
- `503 Service Unavailable` - 服务不可用

## 配置选项

### 检查间隔

默认情况下，系统每30秒自动检查一次服务状态。可以通过修改`ServiceStatusPanel`组件的`checkInterval`属性来调整：

```tsx
<ServiceStatusPanel checkInterval={60000} /> // 60秒检查一次
```

### 超时设置

每次状态检查的超时时间为5秒。如果在5秒内没有收到响应，将标记为"Disconnected"状态。

## 技术实现

### 核心文件

1. **类型定义和工具函数**
   - `src/lib/service-status.ts` - 服务状态类型定义和检查函数

2. **自定义Hooks**
   - `src/hooks/use-service-status.tsx` - 状态监控Hooks

3. **UI组件**
   - `src/components/ui/status-indicator.tsx` - 状态指示器组件
   - `src/components/service-status-panel.tsx` - 服务状态面板

4. **集成**
   - `src/providers/Stream.tsx` - 添加API配置Context
   - `src/components/thread/index.tsx` - 集成到主界面

### 工作原理

1. **自动检查**: 使用React Hooks实现定时轮询，每隔指定时间自动检查服务状态
2. **状态管理**: 使用React State管理每个服务的状态信息
3. **错误处理**: 捕获网络错误和超时，并显示相应的错误信息
4. **性能优化**: 使用`useCallback`和`useEffect`优化性能，避免不必要的重新渲染

## 故障排查

### 状态一直显示"Checking"

**可能原因**:
- API端点未正确配置
- 后端服务未启动
- 网络连接问题

**解决方法**:
1. 检查环境变量`NEXT_PUBLIC_API_URL`是否正确配置
2. 确认后端服务已启动并可访问
3. 检查浏览器控制台是否有网络错误

### 状态显示"Error"

**可能原因**:
- API端点返回非200状态码
- 响应格式不正确
- 服务内部错误

**解决方法**:
1. 查看状态指示器的tooltip中的错误信息
2. 检查后端日志
3. 使用浏览器开发者工具查看网络请求详情

### 状态显示"Disconnected"

**可能原因**:
- 服务未启动
- 网络超时（超过5秒）
- API端点不存在

**解决方法**:
1. 确认相应的服务已启动
2. 检查网络连接
3. 验证API端点路径是否正确

## 自定义扩展

### 添加新的服务状态监控

如果需要监控其他服务，可以按照以下步骤：

1. 在`src/lib/service-status.ts`中添加新的检查函数：

```typescript
export async function checkNewServiceStatus(
  apiUrl: string,
  apiKey?: string | null,
): Promise<ServiceStatusInfo> {
  const startTime = Date.now();
  try {
    const res = await fetch(`${apiUrl}/new-service/health`, {
      method: "GET",
      headers: {
        ...(apiKey && { "X-Api-Key": apiKey }),
      },
      signal: AbortSignal.timeout(5000),
    });

    const latency = Date.now() - startTime;

    if (res.ok) {
      return {
        status: "connected",
        lastChecked: new Date(),
        latency,
      };
    } else {
      return {
        status: "error",
        lastChecked: new Date(),
        error: `HTTP ${res.status}: ${res.statusText}`,
        latency,
      };
    }
  } catch (e) {
    const latency = Date.now() - startTime;
    return {
      status: "disconnected",
      lastChecked: new Date(),
      error: e instanceof Error ? e.message : "Unknown error",
      latency,
    };
  }
}
```

2. 在`src/hooks/use-service-status.tsx`中添加新的Hook：

```typescript
export function useNewServiceStatus({
  apiUrl,
  apiKey,
  checkInterval = 30000,
  enabled = true,
}: UseServiceStatusOptions) {
  const [status, setStatus] = useState<ServiceStatusInfo>({
    status: "checking",
  });

  const checkStatus = useCallback(async () => {
    if (!enabled || !apiUrl) return;
    const result = await checkNewServiceStatus(apiUrl, apiKey);
    setStatus(result);
  }, [apiUrl, apiKey, enabled]);

  useEffect(() => {
    if (!enabled || !apiUrl) return;
    checkStatus();
    const interval = setInterval(checkStatus, checkInterval);
    return () => clearInterval(interval);
  }, [checkStatus, checkInterval, enabled, apiUrl]);

  return { status, refresh: checkStatus };
}
```

3. 在`ServiceStatusPanel`组件中添加新的状态指示器：

```tsx
const { status: newServiceStatus } = useNewServiceStatus({
  apiUrl,
  apiKey,
  checkInterval,
  enabled: !!apiUrl,
});

// 在返回的JSX中添加
<StatusIndicator
  label="New Service"
  status={newServiceStatus.status}
  latency={newServiceStatus.latency}
  error={newServiceStatus.error}
  lastChecked={newServiceStatus.lastChecked}
/>
```

## 注意事项

1. **性能考虑**: 频繁的状态检查可能增加服务器负载，建议根据实际需求调整检查间隔
2. **错误处理**: 确保后端API有适当的错误处理和超时设置
3. **CORS配置**: 如果前后端分离部署，确保后端正确配置CORS
4. **安全性**: 如果使用API Key，确保通过HTTPS传输

## 更新日志

### v1.0.0 (2025-01-12)
- ✨ 新增RAG服务状态监控
- ✨ 新增Unity连接状态监控
- ✨ 实现自动定时检查机制
- ✨ 添加状态指示器UI组件
- ✨ 集成到主界面顶部工具栏
