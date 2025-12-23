"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import { useStreamContext } from "@/providers/Stream";
import { useQueryState } from "nuqs";
import {
  Activity,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Zap,
  Layers,
  Boxes,
  Search,
  FileText,
} from "lucide-react";

type NodeStatus = "pending" | "running" | "completed" | "error";

interface ProgressEvent {
  event_type: string;
  message: string;
  progress?: number;
  phase?: string;
  track_index?: number;
  track_name?: string;
  total_tracks?: number;
  timestamp?: string;
}

interface GraphNode {
  id: string;
  label: string;
  type: "start" | "end" | "default";
}

interface GraphEdge {
  source: string;
  target: string;
  conditional: boolean;
  label?: string;
}

interface GraphStructure {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphInfo {
  name: string;
  description: string;
}

// 节点中文名称映射
const NODE_LABELS_CN: Record<string, string> = {
  "__start__": "开始",
  "__end__": "结束",
  "skeleton_generator": "骨架生成",
  "skeleton_fixer": "骨架修复",
  "track_action_generator": "Track生成",
  "track_validator": "Track验证",
  "track_fixer": "Track修复",
  "track_saver": "Track保存",
  "skill_assembler": "技能组装",
  "finalize": "完成",
  "retrieve": "RAG检索",
  "generate": "LLM生成",
  "validator": "验证器",
  "batch_action_generator": "批量生成",
  "batch_validator": "批量验证",
  "batch_fixer": "批量修复",
  "batch_saver": "批量保存",
  "track_batch_planner": "批量规划",
  "track_assembler": "Track组装",
};

const GRAPH_ICONS: Record<string, React.ReactNode> = {
  "skill-generation": <Zap className="h-4 w-4" />,
  "progressive-skill-generation": <Layers className="h-4 w-4" />,
  "action-batch-skill-generation": <Boxes className="h-4 w-4" />,
  "skill-search": <Search className="h-4 w-4" />,
  "skill-detail": <FileText className="h-4 w-4" />,
};

const EVENT_TO_NODE_MAP: Record<string, string[]> = {
  skeleton_started: ["skeleton_generator"],
  skeleton_completed: ["skeleton_generator"],
  skeleton_failed: ["skeleton_generator", "skeleton_fixer"],
  track_started: ["track_action_generator"],
  track_completed: ["track_saver"],
  track_failed: ["track_action_generator", "track_fixer"],
  batch_planning: ["track_batch_planner"],
  batch_started: ["batch_action_generator"],
  batch_completed: ["batch_saver"],
  batch_validating: ["batch_validator"],
  batch_fixing: ["batch_fixer"],
  batch_failed: ["batch_action_generator"],
  assembling_track: ["track_assembler"],
  assembling_skill: ["skill_assembler"],
  validating: ["validator", "track_validator", "batch_validator"],
  validation_passed: ["validator", "track_validator"],
  validation_failed: ["validator", "track_validator"],
  generation_started: ["retrieve", "skeleton_generator"],
  generation_completed: ["finalize"],
  generation_failed: ["finalize"],
  rag_searching: ["retrieve"],
  rag_completed: ["retrieve"],
  llm_calling: ["generate", "skeleton_generator", "track_action_generator"],
  llm_completed: ["generate"],
};

// 节点位置计算
interface NodePosition {
  x: number;
  y: number;
}

function calculateNodePositions(
  nodes: GraphNode[],
  edges: GraphEdge[]
): Map<string, NodePosition> {
  const positions = new Map<string, NodePosition>();
  const nodeWidth = 120;
  const nodeHeight = 40;
  const horizontalGap = 60;
  const verticalGap = 50;
  
  // 构建邻接表
  const adjacency = new Map<string, string[]>();
  const inDegree = new Map<string, number>();
  
  nodes.forEach(n => {
    adjacency.set(n.id, []);
    inDegree.set(n.id, 0);
  });
  
  edges.forEach(e => {
    adjacency.get(e.source)?.push(e.target);
    inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1);
  });
  
  // 拓扑排序分层
  const layers: string[][] = [];
  const visited = new Set<string>();
  const queue: string[] = [];
  
  // 找到起始节点
  nodes.forEach(n => {
    if (inDegree.get(n.id) === 0) {
      queue.push(n.id);
    }
  });
  
  while (queue.length > 0) {
    const layer: string[] = [];
    const nextQueue: string[] = [];
    
    for (const nodeId of queue) {
      if (!visited.has(nodeId)) {
        visited.add(nodeId);
        layer.push(nodeId);
        
        for (const next of adjacency.get(nodeId) || []) {
          const newDegree = (inDegree.get(next) || 1) - 1;
          inDegree.set(next, newDegree);
          if (newDegree === 0) {
            nextQueue.push(next);
          }
        }
      }
    }
    
    if (layer.length > 0) {
      layers.push(layer);
    }
    queue.length = 0;
    queue.push(...nextQueue);
  }
  
  // 计算位置
  let maxWidth = 0;
  layers.forEach(layer => {
    maxWidth = Math.max(maxWidth, layer.length);
  });
  
  const totalWidth = maxWidth * (nodeWidth + horizontalGap);
  
  layers.forEach((layer, layerIndex) => {
    const layerWidth = layer.length * (nodeWidth + horizontalGap) - horizontalGap;
    const startX = (totalWidth - layerWidth) / 2;
    
    layer.forEach((nodeId, nodeIndex) => {
      positions.set(nodeId, {
        x: startX + nodeIndex * (nodeWidth + horizontalGap) + nodeWidth / 2,
        y: layerIndex * (nodeHeight + verticalGap) + nodeHeight / 2 + 20,
      });
    });
  });
  
  return positions;
}

// 获取节点状态颜色
function getStatusColors(status: NodeStatus) {
  switch (status) {
    case "running":
      return { bg: "#dbeafe", border: "#3b82f6", text: "#1d4ed8" };
    case "completed":
      return { bg: "#dcfce7", border: "#22c55e", text: "#15803d" };
    case "error":
      return { bg: "#fee2e2", border: "#ef4444", text: "#b91c1c" };
    default:
      return { bg: "#f3f4f6", border: "#d1d5db", text: "#6b7280" };
  }
}

// SVG 图形组件
function GraphSVG({
  nodes,
  edges,
  getNodeStatus,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  getNodeStatus: (id: string) => NodeStatus;
}) {
  const positions = useMemo(() => calculateNodePositions(nodes, edges), [nodes, edges]);
  
  const nodeWidth = 120;
  const nodeHeight = 36;
  
  // 计算SVG尺寸
  let maxX = 0, maxY = 0;
  positions.forEach(pos => {
    maxX = Math.max(maxX, pos.x + nodeWidth / 2 + 20);
    maxY = Math.max(maxY, pos.y + nodeHeight / 2 + 20);
  });
  
  return (
    <svg width="100%" height={maxY} viewBox={`0 0 ${maxX} ${maxY}`} className="overflow-visible">
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
        </marker>
        <marker
          id="arrowhead-active"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" />
        </marker>
      </defs>
      
      {/* 绘制边 */}
      {edges.map((edge, i) => {
        const from = positions.get(edge.source);
        const to = positions.get(edge.target);
        if (!from || !to) return null;
        
        const sourceStatus = getNodeStatus(edge.source);
        const isActive = sourceStatus === "completed" || sourceStatus === "running";
        
        return (
          <g key={i}>
            <line
              x1={from.x}
              y1={from.y + nodeHeight / 2}
              x2={to.x}
              y2={to.y - nodeHeight / 2 - 5}
              stroke={isActive ? "#3b82f6" : "#d1d5db"}
              strokeWidth={edge.conditional ? 1 : 2}
              strokeDasharray={edge.conditional ? "4,4" : "none"}
              markerEnd={isActive ? "url(#arrowhead-active)" : "url(#arrowhead)"}
            />
          </g>
        );
      })}
      
      {/* 绘制节点 */}
      {nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return null;
        
        const status = getNodeStatus(node.id);
        const colors = getStatusColors(status);
        const label = NODE_LABELS_CN[node.id] || node.label;
        const isStartEnd = node.type === "start" || node.type === "end";
        
        return (
          <g key={node.id}>
            {isStartEnd ? (
              <ellipse
                cx={pos.x}
                cy={pos.y}
                rx={30}
                ry={16}
                fill={colors.bg}
                stroke={colors.border}
                strokeWidth={2}
              />
            ) : (
              <rect
                x={pos.x - nodeWidth / 2}
                y={pos.y - nodeHeight / 2}
                width={nodeWidth}
                height={nodeHeight}
                rx={6}
                fill={colors.bg}
                stroke={colors.border}
                strokeWidth={2}
              />
            )}
            
            {/* 状态图标 */}
            {status === "running" && !isStartEnd && (
              <circle
                cx={pos.x - nodeWidth / 2 + 14}
                cy={pos.y}
                r={6}
                fill="#3b82f6"
                className="animate-pulse"
              />
            )}
            {status === "completed" && !isStartEnd && (
              <circle
                cx={pos.x - nodeWidth / 2 + 14}
                cy={pos.y}
                r={6}
                fill="#22c55e"
              />
            )}
            {status === "error" && !isStartEnd && (
              <circle
                cx={pos.x - nodeWidth / 2 + 14}
                cy={pos.y}
                r={6}
                fill="#ef4444"
              />
            )}
            
            <text
              x={pos.x + (status !== "pending" && !isStartEnd ? 8 : 0)}
              y={pos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={colors.text}
              fontSize={isStartEnd ? 11 : 12}
              fontWeight={status === "running" ? 600 : 400}
            >
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// 进度条组件
function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="px-3 py-2 border-b">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>进度</span>
        <span>{Math.round(progress * 100)}%</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, progress * 100)}%` }}
        />
      </div>
    </div>
  );
}

// 事件日志项
function EventLogItem({ event }: { event: ProgressEvent }) {
  const getIcon = (t: string) => {
    if (t.includes("completed") || t.includes("passed")) return <CheckCircle2 className="h-3 w-3 text-green-500" />;
    if (t.includes("failed") || t.includes("error")) return <AlertCircle className="h-3 w-3 text-red-500" />;
    if (t.includes("started") || t.includes("calling")) return <Loader2 className="h-3 w-3 text-blue-500" />;
    return <Activity className="h-3 w-3 text-gray-400" />;
  };
  return (
    <div className="flex items-start gap-2 text-xs py-1.5 px-3 border-b border-gray-100 last:border-0">
      <div className="mt-0.5 flex-shrink-0">{getIcon(event.event_type)}</div>
      <p className="text-gray-600 break-words">{event.message}</p>
    </div>
  );
}

// 主组件
export function GraphVisualizer() {
  const [graphStructure, setGraphStructure] = useState<GraphStructure | null>(null);
  const [graphInfo, setGraphInfo] = useState<GraphInfo | null>(null);
  const [progressEvents, setProgressEvents] = useState<ProgressEvent[]>([]);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());
  const [errorNodes, setErrorNodes] = useState<Set<string>>(new Set());

  const [assistantId] = useQueryState("assistantId", { defaultValue: "smart" });
  const stream = useStreamContext();
  const isLoading = stream.isLoading;

  // 处理进度事件
  const handleProgressEvent = useCallback((event: ProgressEvent) => {
    setProgressEvents((prev) => [...prev.slice(-19), event]);
    if (event.progress !== undefined) setCurrentProgress(event.progress);

    const eventType = event.event_type;
    const relatedNodes = EVENT_TO_NODE_MAP[eventType] || [];

    if (eventType.includes("started") || eventType.includes("calling") || eventType.includes("searching")) {
      setActiveNodes((prev) => {
        const next = new Set(prev);
        relatedNodes.forEach((n) => next.add(n));
        return next;
      });
    } else if (eventType.includes("completed") || eventType.includes("passed")) {
      setActiveNodes((prev) => {
        const next = new Set(prev);
        relatedNodes.forEach((n) => next.delete(n));
        return next;
      });
      setCompletedNodes((prev) => {
        const next = new Set(prev);
        relatedNodes.forEach((n) => next.add(n));
        return next;
      });
    } else if (eventType.includes("failed") || eventType.includes("error")) {
      setActiveNodes((prev) => {
        const next = new Set(prev);
        relatedNodes.forEach((n) => next.delete(n));
        return next;
      });
      setErrorNodes((prev) => {
        const next = new Set(prev);
        relatedNodes.forEach((n) => next.add(n));
        return next;
      });
    }
  }, []);

  // 监听进度事件
  useEffect(() => {
    const handler = (e: CustomEvent<ProgressEvent>) => handleProgressEvent(e.detail);
    window.addEventListener("langgraph-progress", handler as EventListener);
    return () => window.removeEventListener("langgraph-progress", handler as EventListener);
  }, [handleProgressEvent]);

  // 获取实际 graph ID
  const streamValues = (stream as any).values;
  const effectiveGraphId = useMemo(() => {
    const routingInfo = streamValues?.routing_info;
    if (routingInfo?.graph_id) return routingInfo.graph_id;
    return assistantId === "smart" ? "progressive-skill-generation" : assistantId;
  }, [assistantId, streamValues?.routing_info]);

  // 获取图结构
  useEffect(() => {
    const fetchGraphStructure = async () => {
      try {
        const apiUrl = "http://localhost:2024";
        const response = await fetch(`${apiUrl}/graphs/${effectiveGraphId}/structure`);
        if (response.ok) {
          const data = await response.json();
          setGraphStructure(data.structure);
          setGraphInfo(data.info);
        }
      } catch (error) {
        console.error("Failed to fetch graph structure:", error);
      }
    };
    if (effectiveGraphId && effectiveGraphId !== "smart") fetchGraphStructure();
  }, [effectiveGraphId]);

  // 重置状态
  useEffect(() => {
    if (isLoading) {
      setProgressEvents([]);
      setCurrentProgress(0);
      setActiveNodes(new Set());
      setCompletedNodes(new Set());
      setErrorNodes(new Set());
    }
  }, [isLoading]);

  // 从 stream values 推断节点状态（始终执行，作为主要状态来源）
  useEffect(() => {
    if (!streamValues) return;
    
    const newCompleted = new Set<string>();
    const newActive = new Set<string>();
    
    // 检查骨架生成状态
    if (streamValues.skill_skeleton && Object.keys(streamValues.skill_skeleton).length > 0) {
      newCompleted.add("skeleton_generator");
    } else if (isLoading && !streamValues.skill_skeleton) {
      // 如果正在加载且还没有骨架，说明正在生成骨架
      newActive.add("skeleton_generator");
    }
    
    // 检查当前 track 状态
    const currentTrackData = streamValues.current_track_data;
    const generatedTracks = streamValues.generated_tracks || [];
    const trackPlan = streamValues.track_plan || [];
    
    if (trackPlan.length > 0 && newCompleted.has("skeleton_generator")) {
      // 骨架完成后，检查 track 生成状态
      if (currentTrackData && Object.keys(currentTrackData).length > 0) {
        // 当前有 track 数据，说明正在处理
        if (streamValues.current_track_errors?.length > 0) {
          newActive.add("track_fixer");
        } else {
          newActive.add("track_validator");
        }
        newCompleted.add("track_action_generator");
      } else if (generatedTracks.length < trackPlan.length && isLoading) {
        // 还有 track 需要生成
        newActive.add("track_action_generator");
      }
      
      // 已保存的 tracks
      if (generatedTracks.length > 0) {
        newCompleted.add("track_action_generator");
        newCompleted.add("track_validator");
        newCompleted.add("track_saver");
      }
    }
    
    // 检查组装状态
    if (streamValues.assembled_skill && Object.keys(streamValues.assembled_skill).length > 0) {
      newCompleted.add("skill_assembler");
    } else if (generatedTracks.length === trackPlan.length && trackPlan.length > 0 && isLoading) {
      newActive.add("skill_assembler");
    }
    
    // 检查最终结果
    if (streamValues.final_result && Object.keys(streamValues.final_result).length > 0) {
      newCompleted.add("finalize");
      newCompleted.add("skill_assembler");
    }
    
    setCompletedNodes(newCompleted);
    setActiveNodes(newActive);
    
  }, [streamValues, isLoading]);

  const getNodeStatus = (nodeId: string): NodeStatus => {
    if (errorNodes.has(nodeId)) return "error";
    if (activeNodes.has(nodeId)) return "running";
    if (completedNodes.has(nodeId)) return "completed";
    return "pending";
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 头部 */}
      <div className="flex items-center gap-2 px-4 py-3 border-b">
        {GRAPH_ICONS[effectiveGraphId] || <Activity className="h-4 w-4 text-gray-500" />}
        <span className="font-medium text-sm text-gray-700">
          {graphInfo?.name || "执行流程"}
        </span>
        {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500 ml-auto" />}
      </div>

      {/* 进度条 */}
      {currentProgress > 0 && <ProgressBar progress={currentProgress} />}

      {/* 图形区域 */}
      <div className="flex-1 overflow-auto p-3">
        {graphStructure ? (
          <GraphSVG
            nodes={graphStructure.nodes}
            edges={graphStructure.edges}
            getNodeStatus={getNodeStatus}
          />
        ) : (
          <div className="flex items-center gap-2 text-sm text-gray-500 p-3">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>加载图结构中...</span>
          </div>
        )}
      </div>

      {/* 事件日志 */}
      {progressEvents.length > 0 && (
        <div className="border-t">
          <p className="text-xs font-medium text-gray-500 px-3 py-2 border-b bg-gray-50">执行日志</p>
          <div className="max-h-32 overflow-y-auto">
            {progressEvents.slice(-5).map((event, i) => (
              <EventLogItem key={i} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphVisualizer;
