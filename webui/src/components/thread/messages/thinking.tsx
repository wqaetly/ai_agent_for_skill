import { useState, useEffect, useRef, useCallback } from "react";
import { ChevronDown, ChevronRight, Brain, Clock, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownText } from "../markdown-text";

interface ThinkingMessageProps {
  content: string;
  isStreaming?: boolean;
  isContentOutput?: boolean; // 🔥 新增：标记是否为 content 输出（deepseek-chat）
}

export function ThinkingMessage({
  content,
  isStreaming = false,
  isContentOutput = false
}: ThinkingMessageProps) {
  // 🔥 isContentOutput 内容默认展开且保持展开
  const [isExpanded, setIsExpanded] = useState(isContentOutput);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  // 检测用户是否在底部附近（允许10px误差）
  const isNearBottom = useCallback(() => {
    if (!contentRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
    return scrollHeight - scrollTop - clientHeight < 10;
  }, []);

  // 处理滚动事件
  const handleScroll = useCallback(() => {
    setShouldAutoScroll(isNearBottom());
  }, [isNearBottom]);

  // 流式输出时自动展开
  useEffect(() => {
    if (isStreaming || isContentOutput) {
      setIsExpanded(true);
      setShouldAutoScroll(true);
    }
  }, [isStreaming, isContentOutput]);

  // 流式输出时自动滚动到底部（仅当用户未手动滚动时）
  useEffect(() => {
    if (isStreaming && isExpanded && shouldAutoScroll && contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [content, isStreaming, isExpanded, shouldAutoScroll]);

  // 计时器 - 显示已思考时间
  useEffect(() => {
    if (isStreaming) {
      const startTime = Date.now();
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      return () => clearInterval(timer);
    } else {
      setElapsedTime(0);
    }
  }, [isStreaming]);

  // 输出完成后自动收起（仅对思考内容，不对 content 输出）
  // 🔥 修复：当 isContentOutput 为 true 时，永远不要自动收起
  // 🔥 使用 useRef 记录是否为 content 输出，避免 props 变化导致的问题
  const isContentOutputRef = useRef(isContentOutput);
  
  // 🔥 更新 ref，确保始终使用最新的 isContentOutput 值
  useEffect(() => {
    if (isContentOutput) {
      isContentOutputRef.current = true;
    }
  }, [isContentOutput]);
  
  useEffect(() => {
    // 如果是 content 输出（包括 JSON、设计思路等），永远保持展开
    // 🔥 使用 ref 来确保即使 props 变化也能保持正确状态
    if (isContentOutput || isContentOutputRef.current) {
      setIsExpanded(true);
      return;
    }
    
    // 只有纯思考内容才会自动收起
    if (!isStreaming && isExpanded) {
      const timer = setTimeout(() => {
        setIsExpanded(false);
      }, 1000); // 1秒后自动收起

      return () => clearTimeout(timer);
    }
  }, [isStreaming, isContentOutput]);

  return (
    <div className={cn(
      "my-2 rounded-lg border overflow-hidden",
      isContentOutput 
        ? "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950"
        : "border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950"
    )}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-full flex items-center gap-2 p-3 transition-colors",
          isContentOutput
            ? "hover:bg-blue-100 dark:hover:bg-blue-900"
            : "hover:bg-purple-100 dark:hover:bg-purple-900"
        )}
      >
        {isContentOutput ? (
          <Sparkles className={cn(
            "h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0",
            isStreaming && "animate-pulse"
          )} />
        ) : (
          <Brain className={cn(
            "h-4 w-4 text-purple-600 dark:text-purple-400 flex-shrink-0",
            isStreaming && "animate-pulse"
          )} />
        )}
        <div className="flex-1 text-left">
          <span className={cn(
            "text-sm font-medium",
            isContentOutput
              ? "text-blue-900 dark:text-blue-100"
              : "text-purple-900 dark:text-purple-100"
          )}>
            {isStreaming 
              ? (isContentOutput ? "AI 正在生成..." : "DeepSeek 正在深度思考...") 
              : (isContentOutput ? "AI 输出" : "思考过程")}
          </span>
          {isStreaming && (
            <div className={cn(
              "flex items-center gap-2 mt-1 text-xs",
              isContentOutput
                ? "text-blue-600 dark:text-blue-400"
                : "text-purple-600 dark:text-purple-400"
            )}>
              <Clock className="h-3 w-3" />
              <span>
                {isContentOutput 
                  ? `已生成 ${elapsedTime}s`
                  : `已思考 ${elapsedTime}s ${elapsedTime < 30 ? "(推理中，预计 30-60s)" : "(即将完成)"}`}
              </span>
            </div>
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className={cn(
            "h-4 w-4 ml-auto flex-shrink-0",
            isContentOutput
              ? "text-blue-600 dark:text-blue-400"
              : "text-purple-600 dark:text-purple-400"
          )} />
        ) : (
          <ChevronRight className={cn(
            "h-4 w-4 ml-auto flex-shrink-0",
            isContentOutput
              ? "text-blue-600 dark:text-blue-400"
              : "text-purple-600 dark:text-purple-400"
          )} />
        )}
      </button>

      <div
        className={cn(
          "overflow-hidden transition-all duration-300",
          isExpanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className={cn(
          "p-3 pt-0 border-t",
          isContentOutput
            ? "border-blue-200 dark:border-blue-800"
            : "border-purple-200 dark:border-purple-800"
        )}>
          <div 
            ref={contentRef}
            onScroll={handleScroll}
            className={cn(
              "text-sm max-h-[500px] overflow-y-auto",
              isContentOutput
                ? "text-blue-800 dark:text-blue-200"
                : "text-purple-800 dark:text-purple-200"
            )}
          >
            <MarkdownText>{content}</MarkdownText>
          </div>
        </div>
      </div>
    </div>
  );
}
