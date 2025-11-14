import { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, Brain, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownText } from "../markdown-text";

interface ThinkingMessageProps {
  content: string;
  isStreaming?: boolean;
}

export function ThinkingMessage({
  content,
  isStreaming = false
}: ThinkingMessageProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);

  // 流式输出时自动展开
  useEffect(() => {
    if (isStreaming) {
      setIsExpanded(true);
    }
  }, [isStreaming]);

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

  // 输出完成后自动收起
  useEffect(() => {
    if (!isStreaming && isExpanded) {
      const timer = setTimeout(() => {
        setIsExpanded(false);
      }, 1000); // 1秒后自动收起

      return () => clearTimeout(timer);
    }
  }, [isStreaming, isExpanded]);

  return (
    <div className="my-2 rounded-lg border border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 p-3 hover:bg-purple-100 dark:hover:bg-purple-900 transition-colors"
      >
        <Brain className={cn(
          "h-4 w-4 text-purple-600 dark:text-purple-400 flex-shrink-0",
          isStreaming && "animate-pulse"
        )} />
        <div className="flex-1 text-left">
          <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
            {isStreaming ? "DeepSeek 正在深度思考..." : "思考过程"}
          </span>
          {isStreaming && (
            <div className="flex items-center gap-2 mt-1 text-xs text-purple-600 dark:text-purple-400">
              <Clock className="h-3 w-3" />
              <span>已思考 {elapsedTime}s {elapsedTime < 30 ? "(推理中，预计 30-60s)" : "(即将完成)"}</span>
            </div>
          )}
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 ml-auto text-purple-600 dark:text-purple-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 ml-auto text-purple-600 dark:text-purple-400 flex-shrink-0" />
        )}
      </button>

      <div
        className={cn(
          "overflow-hidden transition-all duration-300",
          isExpanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="p-3 pt-0 border-t border-purple-200 dark:border-purple-800">
          <div className="text-sm text-purple-800 dark:text-purple-200 max-h-[500px] overflow-y-auto">
            <MarkdownText>{content}</MarkdownText>
          </div>
        </div>
      </div>
    </div>
  );
}
