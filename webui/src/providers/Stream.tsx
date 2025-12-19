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

  const updateChunkBuffer = (id: string, updater: (prev?: ChunkBuffer) => ChunkBuffer) => {
    chunkBuffersRef.current[id] = updater(chunkBuffersRef.current[id]);
  };

  const streamValue = useTypedStream({
    apiUrl,
    apiKey: apiKey ?? undefined,
    assistantId,
    threadId: threadId ?? null,
    fetchStateHistory: true,
    onCustomEvent: (event: any, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
        return;
      }

      // 🔥 处理 thinking_chunk 和 content_chunk 事件
      if (!event || typeof event !== "object") return;
      const { type, message_id, chunk } = event;

      if (!message_id || typeof chunk !== "string") return;

      // 只处理流式 chunk 事件
      if (type !== "thinking_chunk" && type !== "content_chunk") return;

      const isThinking = type === "thinking_chunk";

      console.log(`[Stream] Received ${type}:`, {
        message_id,
        chunk: chunk.substring(0, 50),
        isThinking,
      });

      // 累积 chunk 到 buffer
      updateChunkBuffer(message_id, (prev) => ({
        text: (prev?.text ?? "") + chunk,
        thinking: prev?.thinking || isThinking,
      }));

      // 实时更新到 messages
      options.mutate((prev) => {
        const messages = prev.messages || [];
        const buffer = chunkBuffersRef.current[message_id];
        if (!buffer) return prev;

        const existingIndex = messages.findIndex((m: any) => m.id === message_id);

        if (existingIndex >= 0) {
          // 更新现有消息
          const updatedMessages = [...messages];
          const existingMsg = updatedMessages[existingIndex];
          updatedMessages[existingIndex] = {
            ...existingMsg,
            content: buffer.text,
            streaming: true,
            thinking: buffer.thinking,
          };
          return { ...prev, messages: updatedMessages };
        } else {
          // 创建新消息
          const newMessage: any = {
            id: message_id,
            type: "ai",
            content: buffer.text,
            streaming: true,
            thinking: buffer.thinking,
          };
          return { ...prev, messages: [...messages, newMessage] };
        }
      });
    },
    onThreadId: (id) => {
      setThreadId(id);
      // Refetch threads list when thread ID changes.
      // Wait for some seconds before fetching so we're able to get the new thread that was created.
      sleep().then(() => getThreads().then(setThreads).catch(console.error));
    },
  });

  // 调试日志
  useEffect(() => {
    console.log('[StreamProvider Debug] messages:', streamValue.messages);
    console.log('[StreamProvider Debug] values:', streamValue.values);
    console.log('[StreamProvider Debug] isLoading:', streamValue.isLoading);

    // 🔍 检查 thinking 字段
    streamValue.messages.forEach((msg: any) => {
      if (msg.thinking || (msg.content && typeof msg.content === 'string' && msg.content.includes('思考'))) {
        console.log(`[StreamProvider Debug] Message with thinking field:`, {
          id: msg.id,
          thinking: msg.thinking,
          streaming: msg.streaming,
          content_preview: msg.content?.substring(0, 100)
        });
      }
    });
  }, [streamValue.messages, streamValue.values, streamValue.isLoading]);

  // 🔥 清理已完成的流式消息 buffer
  useEffect(() => {
    if (!streamValue.isLoading) {
      // 流结束时清空所有 buffer
      const bufferIds = Object.keys(chunkBuffersRef.current);
      if (bufferIds.length > 0) {
        console.log(`[Stream] Clearing ${bufferIds.length} chunk buffers`);
        chunkBuffersRef.current = {};
      }
    }

    // 检查每个消息,如果不再是 streaming 状态,清理对应的 buffer
    streamValue.messages.forEach((msg: any) => {
      if (!msg.streaming && msg.id && chunkBuffersRef.current[msg.id]) {
        console.log(`[Stream] Clearing buffer for completed message: ${msg.id}`);
        delete chunkBuffersRef.current[msg.id];
      }
    });
  }, [streamValue.isLoading, streamValue.messages]);

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

  return (
    <StreamContext.Provider value={streamValue}>
      {children}
    </StreamContext.Provider>
  );
};

// Default values for the form and fallbacks
const DEFAULT_API_URL = "http://localhost:2024";
const DEFAULT_ASSISTANT_ID = "skill-generation";

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
