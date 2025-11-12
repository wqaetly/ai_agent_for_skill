# 服务状态监控 - 快速测试指南

## 测试前准备

1. 确保WebUI已启动：
```bash
cd webui
pnpm dev
```

2. 确保后端服务已启动（默认端口2024）

## 测试步骤

### 1. 查看状态指示器

打开浏览器访问 `http://localhost:3000`，在聊天界面顶部工具栏应该能看到两个状态指示器：
- **RAG** - RAG服务状态
- **Unity** - Unity连接状态

### 2. 测试状态显示

将鼠标悬停在状态指示器上，应该显示详细信息：
- Status: 当前状态
- Latency: 响应延迟
- Last Checked: 最后检查时间
- Error: 错误信息（如果有）

### 3. 测试不同状态

#### 测试"Connected"状态
- 确保后端服务正常运行
- 状态指示器应显示绿色的✓图标
- 状态文本显示"Connected"

#### 测试"Disconnected"状态
- 停止后端服务
- 等待30秒（或下一次检查周期）
- 状态指示器应显示红色的✗图标
- 状态文本显示"Disconnected"

#### 测试"Error"状态
- 修改后端API返回非200状态码
- 状态指示器应显示橙色的⚠图标
- 状态文本显示"Error"
- Tooltip中应显示具体错误信息

### 4. 测试自动刷新

- 观察状态指示器
- 每30秒应自动检查一次服务状态
- "Last Checked"时间应自动更新

## 后端API模拟

如果后端还未实现相应的API，可以使用以下方法进行测试：

### 方法1: 使用Mock Server

创建一个简单的Express服务器来模拟API：

```javascript
// mock-server.js
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());

// RAG健康检查
app.get('/rag/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Unity状态
app.get('/unity/status', (req, res) => {
  res.json({ connected: true });
});

app.listen(2024, () => {
  console.log('Mock server running on http://localhost:2024');
});
```

运行：
```bash
node mock-server.js
```

### 方法2: 修改检查函数（临时测试）

临时修改 `src/lib/service-status.ts` 中的检查函数，返回模拟数据：

```typescript
export async function checkRAGServiceStatus(
  apiUrl: string,
  apiKey?: string | null,
): Promise<ServiceStatusInfo> {
  // 临时返回模拟数据
  return {
    status: "connected",
    lastChecked: new Date(),
    latency: 50,
  };
}
```

## 常见问题

### Q: 状态一直显示"Checking"
**A**: 检查：
1. 后端服务是否启动
2. API URL是否正确（默认：http://localhost:2024）
3. 浏览器控制台是否有CORS错误

### Q: 看不到状态指示器
**A**: 检查：
1. 是否已进入聊天界面（需要先配置API URL和Assistant ID）
2. 浏览器窗口是否足够宽（状态指示器在顶部工具栏）

### Q: 状态更新不及时
**A**: 
- 默认检查间隔为30秒
- 可以刷新页面立即重新检查
- 或修改`checkInterval`参数调整检查频率

## 验证清单

- [ ] 状态指示器正确显示在顶部工具栏
- [ ] RAG服务状态正确显示
- [ ] Unity连接状态正确显示
- [ ] 鼠标悬停显示详细信息
- [ ] 状态图标和颜色正确
- [ ] 自动刷新功能正常
- [ ] 错误信息正确显示
- [ ] 延迟时间正确显示

## 下一步

测试通过后，可以：
1. 在后端实现真实的API端点
2. 根据实际需求调整检查间隔
3. 添加更多服务状态监控
4. 自定义状态指示器样式
