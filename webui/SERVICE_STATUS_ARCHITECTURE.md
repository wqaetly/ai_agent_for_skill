# 服务状态监控 - 架构图

## 系统架构图

```mermaid
graph TB
    subgraph "前端 WebUI"
        A[Thread Component] --> B[ServiceStatusPanel]
        B --> C[StatusIndicator - RAG]
        B --> D[StatusIndicator - Unity]
        
        C --> E[useRAGServiceStatus Hook]
        D --> F[useUnityConnectionStatus Hook]
        
        E --> G[checkRAGServiceStatus]
        F --> H[checkUnityConnectionStatus]
        
        I[ApiConfigContext] -.提供配置.-> B
        J[StreamProvider] --> I
    end
    
    subgraph "网络层"
        G --> K[HTTP GET /rag/health]
        H --> L[HTTP GET /unity/status]
    end
    
    subgraph "后端服务"
        K --> M[RAG Service]
        L --> N[Unity Connection Manager]
    end
    
    style A fill:#e1f5ff
    style B fill:#fff4e6
    style C fill:#e8f5e9
    style D fill:#e8f5e9
    style M fill:#fce4ec
    style N fill:#fce4ec
```

## 数据流图

```mermaid
sequenceDiagram
    participant UI as Thread UI
    participant Panel as ServiceStatusPanel
    participant Hook as useServiceStatus Hook
    participant Lib as service-status.ts
    participant API as Backend API
    
    UI->>Panel: 渲染组件
    Panel->>Hook: 初始化Hook
    Hook->>Lib: 调用检查函数
    Lib->>API: GET /rag/health
    API-->>Lib: 返回状态
    Lib-->>Hook: 返回ServiceStatusInfo
    Hook-->>Panel: 更新状态
    Panel-->>UI: 显示状态指示器
    
    Note over Hook,Lib: 每30秒自动重复
```

## 组件层次结构

```mermaid
graph LR
    A[Thread] --> B[ServiceStatusPanel]
    B --> C[StatusIndicator RAG]
    B --> D[StatusIndicator Unity]
    C --> E[Tooltip]
    D --> F[Tooltip]
    
    style A fill:#bbdefb
    style B fill:#c8e6c9
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#ffccbc
    style F fill:#ffccbc
```

## 状态机图

```mermaid
stateDiagram-v2
    [*] --> Checking: 初始化
    Checking --> Connected: API返回200
    Checking --> Disconnected: 网络错误/超时
    Checking --> Error: API返回非200
    
    Connected --> Checking: 定时检查
    Disconnected --> Checking: 定时检查
    Error --> Checking: 定时检查
    
    Connected --> [*]: 组件卸载
    Disconnected --> [*]: 组件卸载
    Error --> [*]: 组件卸载
```

## 文件依赖关系

```mermaid
graph TD
    A[index.tsx] --> B[service-status-panel.tsx]
    B --> C[status-indicator.tsx]
    B --> D[use-service-status.tsx]
    B --> E[Stream.tsx - useApiConfig]
    
    D --> F[service-status.ts]
    C --> G[ui/tooltip]
    C --> H[lucide-react icons]
    
    F --> I[fetch API]
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#e8f5e9
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#e0f2f1
```

## 时序图 - 完整流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant UI as Thread UI
    participant Panel as ServiceStatusPanel
    participant Hook as Hook
    participant Check as Check Function
    participant API as Backend
    
    User->>UI: 打开聊天界面
    UI->>Panel: 渲染状态面板
    Panel->>Hook: useRAGServiceStatus()
    Panel->>Hook: useUnityConnectionStatus()
    
    Note over Hook: 初始状态: checking
    
    Hook->>Check: checkRAGServiceStatus()
    Check->>API: GET /rag/health
    
    alt 成功响应
        API-->>Check: 200 OK
        Check-->>Hook: {status: "connected", latency: 50ms}
        Hook-->>Panel: 更新状态
        Panel-->>UI: 显示绿色✓
    else 网络错误
        API-->>Check: Network Error
        Check-->>Hook: {status: "disconnected", error: "..."}
        Hook-->>Panel: 更新状态
        Panel-->>UI: 显示红色✗
    else 服务错误
        API-->>Check: 503 Service Unavailable
        Check-->>Hook: {status: "error", error: "HTTP 503"}
        Hook-->>Panel: 更新状态
        Panel-->>UI: 显示橙色⚠
    end
    
    User->>UI: 鼠标悬停
    UI->>Panel: 显示Tooltip
    Panel-->>User: 显示详细信息
    
    Note over Hook: 30秒后
    Hook->>Check: 自动重新检查
```

## 错误处理流程

```mermaid
flowchart TD
    A[开始检查] --> B{发送请求}
    B --> C{5秒内响应?}
    
    C -->|是| D{状态码200?}
    C -->|否| E[超时错误]
    
    D -->|是| F[返回Connected]
    D -->|否| G[返回Error]
    
    E --> H[返回Disconnected]
    
    B -->|网络错误| I[捕获异常]
    I --> H
    
    F --> J[更新UI]
    G --> J
    H --> J
    
    J --> K[等待30秒]
    K --> A
    
    style F fill:#c8e6c9
    style G fill:#ffccbc
    style H fill:#ffcdd2
```

## 配置流程

```mermaid
flowchart LR
    A[环境变量] --> B[StreamProvider]
    C[URL参数] --> B
    D[LocalStorage] --> B
    
    B --> E[ApiConfigContext]
    E --> F[useApiConfig Hook]
    F --> G[ServiceStatusPanel]
    
    G --> H[useRAGServiceStatus]
    G --> I[useUnityConnectionStatus]
    
    style B fill:#e1bee7
    style E fill:#c5cae9
    style F fill:#b2dfdb
    style G fill:#fff9c4
```

## 性能优化策略

```mermaid
mindmap
  root((性能优化))
    React优化
      useCallback
      useMemo
      避免不必要渲染
    网络优化
      请求超时控制
      并发请求限制
      错误重试机制
    状态管理
      Context优化
      状态更新批处理
      组件卸载清理
    UI优化
      懒加载
      虚拟滚动
      防抖节流
```

## 扩展点

```mermaid
graph TB
    A[当前系统] --> B[扩展点1: 新服务监控]
    A --> C[扩展点2: WebSocket支持]
    A --> D[扩展点3: 历史记录]
    A --> E[扩展点4: 告警通知]
    
    B --> F[添加检查函数]
    B --> G[添加Hook]
    B --> H[添加UI组件]
    
    C --> I[建立WebSocket连接]
    C --> J[实时推送状态]
    
    D --> K[状态变化记录]
    D --> L[历史数据可视化]
    
    E --> M[浏览器通知]
    E --> N[邮件/短信通知]
    
    style A fill:#e3f2fd
    style B fill:#c8e6c9
    style C fill:#fff9c4
    style D fill:#ffccbc
    style E fill:#f8bbd0
```

## 说明

以上架构图使用Mermaid语法编写，可以在支持Mermaid的Markdown查看器中渲染，例如：
- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Typora
- 在线Mermaid编辑器: https://mermaid.live/

如果您的查看器不支持Mermaid，可以将代码复制到 https://mermaid.live/ 查看渲染效果。
