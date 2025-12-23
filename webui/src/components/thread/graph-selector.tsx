"use client";

import React, { useState, useEffect } from "react";
import { useQueryState } from "nuqs";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  Zap,
  Layers,
  Boxes,
  Search,
  FileText,
  ChevronDown,
  Check,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Graph 配置
const GRAPHS = [
  {
    id: "smart",
    name: "智能路由",
    description: "根据输入自动选择最合适的生成方式",
    icon: Sparkles,
    default: true,
    color: "text-purple-500",
  },
  {
    id: "skill-generation",
    name: "标准生成",
    description: "一次性生成完整技能，适合简单技能",
    icon: Zap,
    color: "text-yellow-500",
  },
  {
    id: "progressive-skill-generation",
    name: "渐进式生成",
    description: "三阶段渐进生成，推荐用于复杂技能",
    icon: Layers,
    recommended: true,
    color: "text-blue-500",
  },
  {
    id: "action-batch-skill-generation",
    name: "批量式生成",
    description: "最细粒度生成，适合超复杂技能",
    icon: Boxes,
    color: "text-green-500",
  },
  {
    id: "skill-search",
    name: "技能搜索",
    description: "语义搜索技能库",
    icon: Search,
    color: "text-orange-500",
  },
  {
    id: "skill-detail",
    name: "技能详情",
    description: "查询技能详细信息",
    icon: FileText,
    color: "text-gray-500",
  },
];

interface GraphSelectorProps {
  className?: string;
  compact?: boolean;
}

export function GraphSelector({ className, compact = false }: GraphSelectorProps) {
  const [assistantId, setAssistantId] = useQueryState("assistantId", {
    defaultValue: "smart",
  });
  const [isOpen, setIsOpen] = useState(false);

  const selectedGraph = GRAPHS.find((g) => g.id === assistantId) || GRAPHS[0];
  const Icon = selectedGraph.icon;

  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-md text-sm",
                "bg-muted hover:bg-muted/80 transition-colors",
                className
              )}
            >
              <Icon className={cn("size-4", selectedGraph.color)} />
              <span className="hidden sm:inline">{selectedGraph.name}</span>
              <ChevronDown className="size-3 text-muted-foreground" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>{selectedGraph.description}</p>
          </TooltipContent>
        </Tooltip>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 z-50 w-64 bg-background border rounded-lg shadow-lg p-1">
            {GRAPHS.map((graph) => {
              const GraphIcon = graph.icon;
              return (
                <button
                  key={graph.id}
                  onClick={() => {
                    setAssistantId(graph.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm",
                    "hover:bg-muted transition-colors text-left",
                    assistantId === graph.id && "bg-muted"
                  )}
                >
                  <GraphIcon className={cn("size-4", graph.color)} />
                  <div className="flex-1">
                    <div className="flex items-center gap-1">
                      <span>{graph.name}</span>
                      {graph.recommended && (
                        <span className="text-xs text-blue-500">推荐</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {graph.description}
                    </p>
                  </div>
                  {assistantId === graph.id && (
                    <Check className="size-4 text-primary" />
                  )}
                </button>
              );
            })}
          </div>
        )}
      </TooltipProvider>
    );
  }

  // Full selector (for settings or initial screen)
  return (
    <div className={cn("space-y-2", className)}>
      <label className="text-sm font-medium text-muted-foreground">
        生成模式
      </label>
      <div className="grid grid-cols-2 gap-2">
        {GRAPHS.slice(0, 4).map((graph) => {
          const GraphIcon = graph.icon;
          return (
            <button
              key={graph.id}
              onClick={() => setAssistantId(graph.id)}
              className={cn(
                "flex items-center gap-2 p-3 rounded-lg border text-left transition-all",
                "hover:border-primary/50 hover:bg-muted/50",
                assistantId === graph.id
                  ? "border-primary bg-primary/5"
                  : "border-border"
              )}
            >
              <GraphIcon className={cn("size-5", graph.color)} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1">
                  <span className="text-sm font-medium">{graph.name}</span>
                  {graph.default && (
                    <span className="text-xs text-purple-500">默认</span>
                  )}
                  {graph.recommended && (
                    <span className="text-xs text-blue-500">推荐</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground truncate">
                  {graph.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// 路由信息显示组件
interface RoutingInfoProps {
  routingInfo?: {
    graph_id: string;
    confidence: number;
    reason: string;
    complexity?: {
      score: number;
      indicators: string[];
    };
  };
}

export function RoutingInfo({ routingInfo }: RoutingInfoProps) {
  if (!routingInfo) return null;

  const graph = GRAPHS.find((g) => g.id === routingInfo.graph_id);
  if (!graph) return null;

  const Icon = graph.icon;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-md text-xs">
      <Sparkles className="size-3 text-purple-500" />
      <span className="text-muted-foreground">智能路由:</span>
      <Icon className={cn("size-3", graph.color)} />
      <span>{graph.name}</span>
      <span className="text-muted-foreground">
        ({Math.round(routingInfo.confidence * 100)}% 置信度)
      </span>
    </div>
  );
}

export default GraphSelector;
