import React, {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
  useRef,
} from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { type Message } from "@langchain/langgraph-sdk";
import {
  uiMessageReducer,
  isUIMessage,
  isRemoveUIMessage,
  type UIMessage,
  type RemoveUIMessage,
} from "@langchain/langgraph-sdk/react-ui";
import { useQueryState } from "nuqs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LangGraphLogoSVG } from "@/components/icons/langgraph";
import { Label } from "@/components/ui/label";
import { ArrowRight } from "lucide-react";
import { PasswordInput } from "@/components/ui/password-input";
import { getApiKey } from "@/lib/api-key";
import { useThreads } from "./Thread";
import { toast } from "sonner";

export type StateType = { messages: Message[]; ui?: UIMessage[] };

const useTypedStream = useStream<
  StateType,
  {
    UpdateType: {
      messages?: Message[] | Message | string;
      ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
      context?: Record<string, unknown>;
    };
    CustomEventType: UIMessage | RemoveUIMessage;
  }
>;

type StreamContextType = ReturnType<typeof useTypedStream>;
const StreamContext = createContext<StreamContextType | undefined>(undefined);

async function sleep(ms = 4000) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkGraphStatus(
  apiUrl: string,
  apiKey: string | null,
): Promise<boolean> {
  try {
    const res = await fetch(`${apiUrl}/info`, {
      ...(apiKey && {
        headers: {
          "X-Api-Key": apiKey,
        },
      }),
    });

    return res.ok;
  } catch (e) {
    console.error(e);
    return false;
  }
}

const StreamSession = ({
  children,
  apiKey,
  apiUrl,
  assistantId,
}: {
  children: ReactNode;
  apiKey: string | null;
  apiUrl: string;
  assistantId: string;
}) => {
  const [threadId, setThreadId] = useQueryState("threadId");
  const { getThreads, setThreads } = useThreads();

  // 🔥 存储流式 chunk 的累积缓冲区 (使用 useRef 避免闭包问题)
  type ChunkBuffer = { text: string; thinking: boolean };
  const chunkBuffersRef = useRef<Record<string, ChunkBuffer>>({});
  // 🔥 防抖定时器，减少频繁的 React 重渲染
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingMutateRef = useRef<((options: any) => void) | null>(null);

  const updateChunkBuffer = (id: string, updater: (prev?: ChunkBuffer) => ChunkBuffer) => {
    chunkBuffersRef.current[id] = updater(chunkBuffersRef.current[id]);
  };

  // 🔥 防抖更新 UI，将多个 chunk 合并成一次更新
  // 🔥 跟踪已创建的流式消息ID，避免重复创建
  const createdStreamingIdsRef = useRef<Set<string>>(new Set());
  
  const debouncedMutate = (options: any) => {
    pendingMutateRef.current = options.mutate;
    
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    debounceTimerRef.current = setTimeout(() => {
      if (pendingMutateRef.current) {
        pendingMutateRef.current((prev: any) => {
          const messages = prev.messages || [];
          const updatedMessages = [...messages];
          let hasChanges = false;
          
          // 批量更新所有 buffer 中的消息
          for (const [msgId, buffer] of Object.entries(chunkBuffersRef.current)) {
            // 🔥 检查是否已存在非流式的完整消息（后端返回的最终消息）
            const existingIndex = updatedMessages.findIndex((m: any) => m.id === msgId);
            
            if (existingIndex >= 0) {
              const existingMsg = updatedMessages[existingIndex];
              // 🔥 如果已存在非流式消息，说明后端已返回完整消息，跳过更新
              if (!existingMsg.streaming) {
                continue;
              }
              if (existingMsg.content !== buffer.text) {
                updatedMessages[existingIndex] = {
                  ...existingMsg,
                  content: buffer.text,
                  streaming: true,
                  thinking: buffer.thinking,
                };
                hasChanges = true;
              }
            } else {
              // 🔥 只有当该ID未被创建过时才添加新消息
              if (!createdStreamingIdsRef.current.has(msgId)) {
                createdStreamingIdsRef.current.add(msgId);
                updatedMessages.push({
                  id: msgId,
                  type: "ai",
                  content: buffer.text,
                  streaming: true,
                  thinking: buffer.thinking,
                });
                hasChanges = true;
              }
            }
          }
          
          return hasChanges ? { ...prev, messages: updatedMessages } : prev;
        });
      }
      debounceTimerRef.current = null;
    }, 50); // 50ms 防抖延迟
  };

  const streamValue = useTypedStream({
    apiUrl,
    apiKey: apiKey ?? undefined,
    assistantId,
    threadId: threadId ?? null,
    messagesKey: "messages",  // 🔥 关键：告诉 hook 从 values 事件中提取 messages
    fetchStateHistory: true,
    onCustomEvent: (event: any, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
        return;
      }

      // 🔥 处理进度事件（来自后端 streaming.py 的 emit_progress）
      if (event && typeof event === "object" && event.event_type) {
        // 这是一个进度事件，通过 window 事件分发给 GraphVisualizer
        window.dispatchEvent(new CustomEvent("langgraph-progress", { detail: event }));
        return;
      }

      // 🔥 处理 thinking_chunk 和 content_chunk 事件
      if (!event || typeof event !== "object") return;
      const { type, message_id, chunk } = event;

      if (!message_id || typeof chunk !== "string") return;

      // 只处理流式 chunk 事件
      if (type !== "thinking_chunk" && type !== "content_chunk") return;

      const isThinking = type === "thinking_chunk";

      // 累积 chunk 到 buffer
      updateChunkBuffer(message_id, (prev) => ({
        text: (prev?.text ?? "") + chunk,
        thinking: prev?.thinking || isThinking,
      }));

      // 🔥 使用防抖更新 UI
      debouncedMutate(options);
    },
    onThreadId: (id) => {
      setThreadId(id);
      // Refetch threads list when thread ID changes.
      // Wait for some seconds before fetching so we're able to get the new thread that was created.
      sleep().then(() => getThreads().then(setThreads).catch(console.error));
    },
  });



  // 🔥 清理已完成的流式消息 buffer
  useEffect(() => {
    if (!streamValue.isLoading) {
      // 流结束时清空所有 buffer 和已创建ID记录
      const bufferIds = Object.keys(chunkBuffersRef.current);
      if (bufferIds.length > 0) {
        chunkBuffersRef.current = {};
      }
      // 🔥 清空已创建的流式消息ID记录，为下次流做准备
      createdStreamingIdsRef.current.clear();
    }
  }, [streamValue.isLoading]);
  
  // 🔥 单独处理消息状态变化，清理对应的 buffer
  useEffect(() => {
    // 🔥 调试日志：打印消息状态变化
    console.log("📨 Messages updated:", streamValue.messages.length, "messages");
    streamValue.messages.forEach((msg: any, i: number) => {
      const contentPreview = typeof msg.content === 'string' 
        ? msg.content.substring(0, 50) 
        : JSON.stringify(msg.content).substring(0, 50);
      console.log(`  [${i}] id=${msg.id}, type=${msg.type}, thinking=${msg.thinking}, content=${contentPreview}...`);
    });
    
    streamValue.messages.forEach((msg: any) => {
      if (!msg.streaming && msg.id && chunkBuffersRef.current[msg.id]) {
        delete chunkBuffersRef.current[msg.id];
      }
    });
  }, [streamValue.messages]);

  useEffect(() => {
    checkGraphStatus(apiUrl, apiKey).then((ok) => {
      if (!ok) {
        toast.error("Failed to connect to LangGraph server", {
          description: () => (
            <p>
              Please ensure your graph is running at <code>{apiUrl}</code> and
              your API key is correctly set (if connecting to a deployed graph).
            </p>
          ),
          duration: 10000,
          richColors: true,
          closeButton: true,
        });
      }
    });
  }, [apiKey, apiUrl]);

  // 🔥 对消息进行去重处理，优先保留非流式消息
  const deduplicatedMessages = React.useMemo(() => {
    const messageMap = new Map<string, Message>();
    const noIdMessages: Message[] = [];
    
    for (const msg of streamValue.messages) {
      if (!msg.id) {
        noIdMessages.push(msg);
        continue;
      }
      
      const existing = messageMap.get(msg.id);
      if (!existing) {
        messageMap.set(msg.id, msg);
      } else {
        // 🔥 优先保留非流式消息（后端返回的完整消息）
        const existingIsStreaming = (existing as any).streaming === true;
        const currentIsStreaming = (msg as any).streaming === true;
        
        if (existingIsStreaming && !currentIsStreaming) {
          // 用完整消息替换流式消息
          messageMap.set(msg.id, msg);
        } else if (!existingIsStreaming && currentIsStreaming) {
          // 保留完整消息，忽略流式消息
          // do nothing
        } else {
          // 两者状态相同，保留后来的（内容更完整）
          messageMap.set(msg.id, msg);
        }
      }
    }
    
    return [...messageMap.values(), ...noIdMessages];
  }, [streamValue.messages]);

  // 🔥 创建包装后的 streamValue，使用去重后的消息
  const wrappedStreamValue = React.useMemo(() => ({
    ...streamValue,
    messages: deduplicatedMessages,
  }), [streamValue, deduplicatedMessages]);

  return (
    <StreamContext.Provider value={wrappedStreamValue}>
      {children}
    </StreamContext.Provider>
  );
};

// Default values for the form and fallbacks
const DEFAULT_API_URL = "http://localhost:2024";
const DEFAULT_ASSISTANT_ID = "smart";  // 🔥 默认使用智能路由

export const StreamProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  // Get environment variables
  const envApiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL;
  const envAssistantId: string | undefined =
    process.env.NEXT_PUBLIC_ASSISTANT_ID;

  // Use URL params with env var fallbacks
  const [apiUrl, setApiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || "",
  });
  const [assistantId, setAssistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });

  // For API key, use localStorage with env var fallback
  const [apiKey, _setApiKey] = useState(() => {
    const storedKey = getApiKey();
    return storedKey || "";
  });

  const setApiKey = (key: string) => {
    window.localStorage.setItem("lg:chat:apiKey", key);
    _setApiKey(key);
  };

  // Determine final values to use, prioritizing URL params then env vars then defaults
  // Use .trim() to handle whitespace-only values
  const finalApiUrl = apiUrl?.trim() || envApiUrl?.trim() || DEFAULT_API_URL;
  const finalAssistantId = assistantId?.trim() || envAssistantId?.trim() || DEFAULT_ASSISTANT_ID;

  // Show the form if we: don't have an API URL, or don't have an assistant ID
  if (!finalApiUrl || !finalAssistantId) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center p-4">
        <div className="animate-in fade-in-0 zoom-in-95 bg-background flex max-w-3xl flex-col rounded-lg border shadow-lg">
          <div className="mt-14 flex flex-col gap-2 border-b p-6">
            <div className="flex flex-col items-start gap-2">
              <LangGraphLogoSVG className="h-7" />
              <h1 className="text-xl font-semibold tracking-tight">
                Agent Chat
              </h1>
            </div>
            <p className="text-muted-foreground">
              Welcome to Agent Chat! Before you get started, you need to enter
              the URL of the deployment and the assistant / graph ID.
            </p>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();

              const form = e.target as HTMLFormElement;
              const formData = new FormData(form);
              const apiUrl = formData.get("apiUrl") as string;
              const assistantId = formData.get("assistantId") as string;
              const apiKey = formData.get("apiKey") as string;

              setApiUrl(apiUrl);
              setApiKey(apiKey);
              setAssistantId(assistantId);

              form.reset();
            }}
            className="bg-muted/50 flex flex-col gap-6 p-6"
          >
            <div className="flex flex-col gap-2">
              <Label htmlFor="apiUrl">
                Deployment URL<span className="text-rose-500">*</span>
              </Label>
              <p className="text-muted-foreground text-sm">
                This is the URL of your LangGraph deployment. Can be a local, or
                production deployment.
              </p>
              <Input
                id="apiUrl"
                name="apiUrl"
                className="bg-background"
                defaultValue={apiUrl || DEFAULT_API_URL}
                required
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="assistantId">
                Assistant / Graph ID<span className="text-rose-500">*</span>
              </Label>
              <p className="text-muted-foreground text-sm">
                This is the ID of the graph (can be the graph name), or
                assistant to fetch threads from, and invoke when actions are
                taken.
              </p>
              <Input
                id="assistantId"
                name="assistantId"
                className="bg-background"
                defaultValue={assistantId || DEFAULT_ASSISTANT_ID}
                required
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="apiKey">LangSmith API Key</Label>
              <p className="text-muted-foreground text-sm">
                This is <strong>NOT</strong> required if using a local LangGraph
                server. This value is stored in your browser's local storage and
                is only used to authenticate requests sent to your LangGraph
                server.
              </p>
              <PasswordInput
                id="apiKey"
                name="apiKey"
                defaultValue={apiKey ?? ""}
                className="bg-background"
                placeholder="lsv2_pt_..."
              />
            </div>

            <div className="mt-2 flex justify-end">
              <Button
                type="submit"
                size="lg"
              >
                Continue
                <ArrowRight className="size-5" />
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <StreamSession
      apiKey={apiKey}
      apiUrl={finalApiUrl}
      assistantId={finalAssistantId}
    >
      {children}
    </StreamSession>
  );
};

// Create a custom hook to use the context
export const useStreamContext = (): StreamContextType => {
  const context = useContext(StreamContext);
  if (context === undefined) {
    throw new Error("useStreamContext must be used within a StreamProvider");
  }
  return context;
};

export default StreamContext;
