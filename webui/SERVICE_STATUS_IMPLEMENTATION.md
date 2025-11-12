# WebUI 服务状态监控功能实现总结

## 实现概述

本次更新为WebUI添加了RAG服务和Unity连接的实时状态监控功能，用户可以在聊天界面顶部实时查看这两个服务的连接状态。

## 新增文件

### 1. 核心功能文件

#### `src/lib/service-status.ts`
- **功能**: 服务状态类型定义和检查函数
- **内容**:
  - `ServiceStatus` 类型定义（connected/disconnected/checking/error）
  - `ServiceStatusInfo` 接口定义
  - `checkRAGServiceStatus()` - RAG服务健康检查
  - `checkUnityConnectionStatus()` - Unity连接状态检查
  - 工具函数：格式化延迟、获取状态颜色、获取状态文本

#### `src/hooks/use-service-status.tsx`
- **功能**: 服务状态监控的自定义Hooks
- **内容**:
  - `useRAGServiceStatus()` - RAG服务状态Hook
  - `useUnityConnectionStatus()` - Unity连接状态Hook
  - 支持自动定时检查（默认30秒）
  - 支持手动刷新

#### `src/components/ui/status-indicator.tsx`
- **功能**: 状态指示器UI组件
- **特性**:
  - 显示服务名称、状态图标和状态文本
  - 鼠标悬停显示详细信息（延迟、最后检查时间、错误信息）
  - 根据状态自动切换颜色和图标
  - 使用Tooltip组件展示详细信息

#### `src/components/service-status-panel.tsx`
- **功能**: 服务状态面板组件
- **特性**:
  - 集成RAG和Unity状态指示器
  - 自动从Context获取API配置
  - 支持自定义检查间隔

### 2. 文档文件

#### `SERVICE_STATUS_GUIDE.md`
- 完整的功能说明文档
- 包含API要求、配置选项、故障排查、自定义扩展等

#### `SERVICE_STATUS_TEST.md`
- 快速测试指南
- 包含测试步骤、Mock Server示例、常见问题等

## 修改的文件

### 1. `src/providers/Stream.tsx`
**修改内容**:
- 添加 `ApiConfigContext` 用于共享API配置
- 添加 `useApiConfig()` Hook
- 在 `StreamSession` 中提供API配置Context

**关键代码**:
```typescript
interface ApiConfigContextType {
  apiUrl: string;
  apiKey: string | null;
}
const ApiConfigContext = createContext<ApiConfigContextType | undefined>(undefined);

export const useApiConfig = (): ApiConfigContextType => {
  const context = useContext(ApiConfigContext);
  if (context === undefined) {
    throw new Error("useApiConfig must be used within a StreamProvider");
  }
  return context;
};
```

### 2. `src/components/thread/index.tsx`
**修改内容**:
- 导入 `ServiceStatusPanel` 组件
- 在顶部工具栏添加服务状态面板

**位置**: 在聊天开始后的顶部工具栏，位于GitHub图标和"New thread"按钮之前

## 功能特性

### ✅ 已实现的功能

1. **实时状态监控**
   - 自动定时检查服务状态（默认30秒）
   - 显示连接状态、延迟、最后检查时间

2. **多种状态支持**
   - Connected（已连接）- 绿色
   - Disconnected（未连接）- 红色
   - Checking（检查中）- 黄色
   - Error（错误）- 橙色

3. **详细信息展示**
   - 鼠标悬停显示Tooltip
   - 包含状态、延迟、最后检查时间、错误信息

4. **错误处理**
   - 网络超时处理（5秒）
   - 错误信息捕获和显示
   - 优雅降级

5. **性能优化**
   - 使用React Hooks优化渲染
   - 避免不必要的重新检查
   - 组件卸载时清理定时器

## API要求

后端需要实现以下API端点：

### 1. RAG服务健康检查
```
GET /rag/health
Response: { "status": "ok" }
Status Code: 200 (正常) / 503 (不可用)
```

### 2. Unity连接状态
```
GET /unity/status
Response: { "connected": true/false }
Status Code: 200 (正常) / 503 (不可用)
```

## 使用方法

### 1. 启动应用
```bash
cd webui
pnpm install  # 如果是首次运行
pnpm dev
```

### 2. 查看状态
- 打开浏览器访问 `http://localhost:3000`
- 配置API URL和Assistant ID
- 进入聊天界面后，在顶部工具栏查看状态指示器

### 3. 自定义配置
可以通过修改 `ServiceStatusPanel` 的 `checkInterval` 属性调整检查间隔：
```tsx
<ServiceStatusPanel checkInterval={60000} /> // 60秒检查一次
```

## 技术栈

- **React 18** - UI框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式
- **Lucide React** - 图标
- **Radix UI** - Tooltip组件
- **Next.js** - 应用框架

## 架构设计

```
┌─────────────────────────────────────────┐
│         Thread Component (UI)           │
│  ┌───────────────────────────────────┐  │
│  │   ServiceStatusPanel              │  │
│  │  ┌─────────────┐ ┌──────────────┐ │  │
│  │  │ RAG Status  │ │ Unity Status │ │  │
│  │  └─────────────┘ └──────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────┐
│      useRAGServiceStatus Hook           │
│      useUnityConnectionStatus Hook      │
└─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────┐
│    checkRAGServiceStatus()              │
│    checkUnityConnectionStatus()         │
│    (src/lib/service-status.ts)          │
└─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────┐
│         Backend API Endpoints           │
│    GET /rag/health                      │
│    GET /unity/status                    │
└─────────────────────────────────────────┘
```

## 扩展性

### 添加新服务监控

系统设计支持轻松添加新的服务监控：

1. 在 `service-status.ts` 中添加检查函数
2. 在 `use-service-status.tsx` 中添加Hook
3. 在 `ServiceStatusPanel` 中添加状态指示器

详细步骤请参考 `SERVICE_STATUS_GUIDE.md` 的"自定义扩展"章节。

## 测试建议

1. **单元测试**: 测试状态检查函数
2. **集成测试**: 测试Hook和组件交互
3. **E2E测试**: 测试完整的用户流程
4. **性能测试**: 测试大量并发检查的性能

## 已知限制

1. **检查频率**: 默认30秒检查一次，不适合需要实时监控的场景
2. **超时设置**: 固定5秒超时，不可配置
3. **重试机制**: 目前没有自动重试机制
4. **离线检测**: 不支持浏览器离线状态检测

## 未来改进方向

1. **WebSocket支持**: 使用WebSocket实现真正的实时监控
2. **可配置超时**: 允许用户自定义超时时间
3. **重试机制**: 添加智能重试逻辑
4. **历史记录**: 记录状态变化历史
5. **告警通知**: 状态异常时发送通知
6. **性能监控**: 添加更多性能指标（CPU、内存等）

## 相关文档

- [功能说明文档](./SERVICE_STATUS_GUIDE.md)
- [快速测试指南](./SERVICE_STATUS_TEST.md)
- [主README](./README.md)

## 版本信息

- **版本**: v1.0.0
- **日期**: 2025-01-12
- **作者**: AI Assistant
- **状态**: ✅ 已完成

## 反馈与支持

如有问题或建议，请：
1. 查看文档中的故障排查章节
2. 检查浏览器控制台的错误信息
3. 查看后端服务日志
4. 提交Issue或联系开发团队
