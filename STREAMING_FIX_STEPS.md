# LangGraph 实时流式输出修复步骤

本文记录了让前端实时展示 LangGraph LLM 输出所需的改动步骤，分为后端 SSE 流事件修复与前端流消息渲染两部分，并附带测试验证方法。

---

## 1. 问题背景与根因

- LangGraph 服务器在 `skill_agent/langgraph_server.py` 中通过 SSE 推送更新，但目前只发送标准 `event: values` 事件；节点内部的 LLM chunk 仅写入自定义队列，却用 `event: content_chunk` 等非标准事件名直接推送。
- LangGraph React SDK 只会触发 `onCustomEvent` 钩子来处理以 `custom|` 为前缀的事件。因此前端 `StreamProvider` 永远收不到这些 chunk，表现为页面“卡住”，直到节点执行结束才一次性更新。
- 现有前端为了补救，尝试用本地 buffer 拼接字符串，但由于 `onCustomEvent` 未触发，这段逻辑根本不会运行。

---

## 2. 后端：规范自定义 SSE 事件

目标：保证所有 chunk 事件都以 `custom|<event_name>` 形式发送，这样前端才能通过 `onCustomEvent` 及时消费。

步骤：

1. 打开 `skill_agent/langgraph_server.py`，定位到 `stream_graph_updates` 协程内两处 `while not chunk_queue.empty()` 循环（一个在主循环内，另一个在流结束后的清空逻辑）。
2. 将原本 `yield f"event: {event_type}\n..."` 的写法改为：
   ```python
   custom_event = (
       event_type
       if str(event_type).startswith("custom|")
       else f"custom|{event_type}"
   )
   yield f"event: {custom_event}\ndata: {chunk_json}\n\n"
   ```
   如此即可兼容已有的 `custom|...` 事件，并为 `thinking_chunk`/`content_chunk` 自动加前缀。
3. 保持 `chunk_json` 原样（包含 `type`, `message_id`, `chunk` 等字段），日志输出也更新为记录 `custom_event`，方便排查。

---

## 3. 前端：消费 chunk 并渲染流式消息

文件：`webui/src/providers/Stream.tsx`

### 3.1 数据结构准备

- 在组件顶部维护 `chunkBuffers`：`Record<string, { text: string; thinking: boolean; createdFrom?: Message }>`，用来累计某条消息的流式文本，同时标记该消息是否是思考流。
- 根据 `message_id`（来自服务端 chunk 事件）对 buffer 进行分组，可直接用 `useRef` 或 `useState`。示例：
  ```ts
  const chunkBuffersRef = useRef<Record<string, ChunkBuffer>>({});
  const updateChunkBuffer = (id: string, updater: (prev?: ChunkBuffer) => ChunkBuffer) => {
    chunkBuffersRef.current[id] = updater(chunkBuffersRef.current[id]);
  };
  ```

### 3.2 onCustomEvent 处理逻辑

1. 在 `useTypedStream` 调用中设置：
   ```ts
   onCustomEvent: (event, options) => {
     if (!event || typeof event !== "object") return;
     const { type, message_id, chunk } = event;
     if (!message_id || typeof chunk !== "string") return;
     const isThinking = type === "thinking_chunk";

     updateChunkBuffer(message_id, (prev) => ({
       text: (prev?.text ?? "") + chunk,
       thinking: prev?.thinking || isThinking,
     }));

     options.mutate((prev) => upsertStreamingMessage(prev, message_id, chunkBuffersRef.current[message_id]));
   }
   ```
2. `upsertStreamingMessage`：确保 `prev.messages` 中存在对应 ID 的 AI 消息；若无则创建 `{ id, type: "ai", content: [{ type: "text", text: buffer.text }], streaming: true, thinking }`。
3. 如果 chunk 类型是 `content_chunk` 且同一消息之前标记为 thinking，可在 `thinking === false` 时复用同一条消息，也可以区分 `thinking_message_id`/`content_message_id` 来对应两条消息，这取决于后端的 `message_id` 生成方式。
4. 当 LangGraph `values` 事件里的正式 AI message 抵达时（`options.mutate` 运行在 `values` 更新里），可检测 `message.streaming` 并清理对应 buffer，避免重复渲染：
   ```ts
   useEffect(() => {
     streamValue.messages.forEach((msg) => {
       if (!msg.streaming) delete chunkBuffersRef.current[msg.id ?? ""];
     });
   }, [streamValue.messages]);
   ```

### 3.3 UI 展示

文件：`webui/src/components/thread/messages/ai.tsx`

1. 新增 Streaming Badge：当 `message.streaming` 为 true 时，显示一个打字光标或 `...` 动画。
2. 若 `message.thinking` 为 true，则调用已有的 `<ThinkingMessage>`，并将 `contentString` 设为 `message.content ?? ""`。
3. 其余 AI 消息维持 Markdown 渲染；当 `message.streaming` 为 true 且 `contentString` 为空，可显示占位文本“Streaming response...”，避免界面空白。

### 3.4 取消/刷新逻辑

- 复用现有 `stream.stop()`，保证 `chunkBuffersRef` 在 `useEffect` 中监听 `streamValue.isLoading` → false 后清空，防止旧 buffer 污染下一次对话。

---

## 4. 验证步骤

1. **后端测试**
   - 启动 LangGraph 服务器。
   - 手动调用一个长回复任务（例如 `/threads/<id>/runs/stream`）。使用 `curl` 观察 SSE：`event: custom|thinking_chunk` / `event: custom|content_chunk` 应持续出现。
   - 确认 `values` 事件仍能完整返回最终状态。
2. **前端测试**
   - 运行 `pnpm dev` 启动 webui。
   - 打开对话页面，发起请求，应该能看到思考过程和内容逐字出现。
   - 切换网络节流 (Chrome DevTools → Slow 3G) 验证在高延迟下依旧持续渲染。
   - 点击“Cancel”确认 `stream.stop()` 会终止流并停止 UI 更新。
3. **回归检查**
   - 刷新页面，确认历史消息仍正常展示。
   - 确认工具调用 / interrupt 信息不受影响（`hideToolCalls` 等开关仍生效）。

---

## 5. 进一步改进建议

- 在服务端为每条 chunk 补充 `created_at` 时间戳，前端可用来做节流（例如 100 ms 才真正 setState 一次），减少渲染压力。
- 如果未来需要多模型并发，可在 chunk 事件里增加 `run_id`，前端即可精确定位同一条回复的多个流。
- 可以考虑在 `ThreadHistory` 里展示“(Streaming)”状态，提示用户当前线程正在生成内容。

---

完成以上步骤，即可让对话界面实时展示 LangGraph 节点内部的 LLM 输出，消除“卡死”错觉，并显著提升用户体验。祝调试顺利！
