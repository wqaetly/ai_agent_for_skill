# RAG 技能查询页面

完整的RAG查询页面，包含技能搜索、Action推荐、参数推荐和索引管理功能。

## 功能模块

### 1. 技能搜索 (Tab 1)
- 向量相似度搜索技能配置
- 高级选项：返回数量、过滤条件
- 实时显示搜索结果和相似度
- 支持查看完整JSON数据

**API**: `POST /rag/search`

### 2. Action推荐 (Tab 2)
- 基于上下文描述推荐合适的Action类型
- 显示相似度评分和使用建议
- 支持自定义推荐数量

**API**: `POST /rag/recommend-actions`

### 3. 参数推荐 (Tab 3)
- 根据Action类型推荐参数配置
- 显示来源技能和完整参数JSON
- 一键复制参数配置

**API**: `POST /rag/recommend-parameters`

### 4. 索引管理 (Tab 4)
- 实时监控服务状态
- 查看索引统计信息
- 重建索引、清空缓存操作
- 操作历史记录

**API**:
- `GET /rag/health`
- `GET /rag/index/stats`
- `POST /rag/index/rebuild`
- `DELETE /rag/cache`

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图标**: lucide-react
- **状态管理**: React Hooks (useState, useEffect, useCallback)

## 文件结构

```
webui/src/app/rag/
├── page.tsx          # 主页面文件（1165行）
└── README.md         # 本文档
```

## 运行要求

1. **后端服务**: 确保RAG服务运行在 `http://localhost:2024`
2. **前端开发服务器**:
   ```bash
   cd webui
   npm install
   npm run dev
   ```
3. **访问地址**: http://localhost:3000/rag

## 主要特性

### UI/UX
- 响应式设计，移动端友好
- 流畅的动画效果（Toast、对话框）
- Loading状态指示
- 错误提示和空状态处理
- 服务健康状态实时监控

### 代码质量
- 完整的TypeScript类型定义
- 组件化设计（10个独立组件）
- 错误处理和边界情况处理
- 代码注释清晰
- 无TypeScript编译错误

### 性能优化
- useCallback优化API调用
- 按需展开详细信息
- 防抖处理（4秒自动关闭Toast）

## 组件列表

1. **RAGPage** - 主容器组件
2. **TabButton** - Tab切换按钮
3. **SearchTab** - 技能搜索功能
4. **ActionsTab** - Action推荐功能
5. **ParametersTab** - 参数推荐功能
6. **IndexTab** - 索引管理功能
7. **StatCard** - 统计卡片
8. **EmptyState** - 空状态提示
9. **Toast** - 消息提示
10. **ConfirmDialog** - 确认对话框

## API端点详情

### 技能搜索
```typescript
POST /rag/search
Body: {
  query: string,
  top_k: number,
  filters?: object
}
Response: {
  results: SearchResult[]
}
```

### Action推荐
```typescript
POST /rag/recommend-actions
Body: {
  context: string,
  top_k: number
}
Response: {
  recommendations: ActionRecommendation[]
}
```

### 参数推荐
```typescript
POST /rag/recommend-parameters
Body: {
  action_type: string,
  skill_context?: string
}
Response: {
  examples: ParameterExample[]
}
```

### 健康检查
```typescript
GET /rag/health
Response: {
  status: 'healthy' | 'unhealthy',
  skill_count: number,
  action_count: number,
  last_updated: string
}
```

### 索引统计
```typescript
GET /rag/index/stats
Response: {
  total_skills: number,
  total_actions: number,
  total_parameters: number,
  index_size_mb: number
}
```

### 重建索引
```typescript
POST /rag/index/rebuild
Response: {
  success: boolean,
  message: string
}
```

### 清空缓存
```typescript
DELETE /rag/cache
Response: {
  success: boolean
}
```

## 使用示例

### 技能搜索
1. 输入查询："AOE伤害技能"
2. 设置返回数量：5
3. （可选）添加过滤条件：`{"skill_type": "attack"}`
4. 点击搜索
5. 查看结果，展开查看完整JSON

### Action推荐
1. 输入描述："造成伤害并击退敌人"
2. 选择推荐数量：3
3. 点击获取推荐
4. 查看推荐的Action类型和使用建议

### 参数推荐
1. 输入Action类型："DamageAction"
2. （可选）输入技能上下文
3. 点击获取参数示例
4. 查看示例，一键复制参数配置

### 索引管理
1. 查看服务状态和索引统计
2. 需要时重建索引（需确认）
3. 清空缓存释放内存
4. 查看操作历史

## 注意事项

1. **服务依赖**: 需要后端RAG服务正常运行
2. **重建索引**: 操作耗时较长，需要确认后执行
3. **错误处理**: 所有API调用都包含错误处理，失败时会显示友好提示
4. **浏览器兼容**: 使用了现代浏览器API（fetch, clipboard），建议使用最新版Chrome/Edge/Firefox

## 维护建议

1. **API地址配置**: `API_BASE_URL` 常量可以提取到环境变量
2. **类型定义**: 考虑提取到独立的types文件
3. **组件拆分**: 如果功能继续增长，可以将各Tab拆分为独立文件
4. **状态管理**: 复杂场景可考虑引入Zustand或Redux
5. **测试**: 建议添加单元测试和集成测试

## 更新日志

- **2025-11-13**: 初始版本创建
  - 实现4个核心Tab功能
  - 完整的API集成
  - 响应式UI设计
  - 错误处理和Loading状态
