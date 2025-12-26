"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  Position,
  MarkerType,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useStreamContext } from "@/providers/Stream";
import { useQueryState } from "nuqs";
import {
  Activity,
  Loader2,
  Zap,
  Layers,
  Boxes,
  Search,
  FileText,
} from "lucide-react";

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
};

const GRAPH_ICONS: Record<string, React.ReactNode> = {
  "skill-generation": <Zap className="h-4 w-4" />,
  "progressive-skill-generation": <Layers className="h-4 w-4" />,
  "action-batch-skill-generation": <Boxes className="h-4 w-4" />,
  "skill-search": <Search className="h-4 w-4" />,
  "skill-detail": <FileText className="h-4 w-4" />,
};

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

// 节点样式
const getNodeStyle = (status: string) => {
  switch (status) {
    case "running":
      return {
        background: "#dbeafe",
        border: "2px solid #3b82f6",
        color: "#1d4ed8",
      };
    case "completed":
      return {
        background: "#dcfce7",
        border: "2px solid #22c55e",
        color: "#15803d",
      };
    case "error":
      return {
        background: "#fee2e2",
        border: "2px solid #ef4444",
        color: "#b91c1c",
      };
    default:
      return {
        background: "#f3f4f6",
        border: "2px solid #d1d5db",
        color: "#6b7280",
      };
  }
};

// 改进的图布局算法 - 支持循环边的可视化
function calculateGraphLayout(structure: GraphStructure): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  
  if (!structure.nodes.length) return positions;
  
  const nodeSet = new Set(structure.nodes.map(n => n.id));
  
  // 构建邻接表
  const successors = new Map<string, Set<string>>();
  const predecessors = new Map<string, Set<string>>();
  
  structure.nodes.forEach(n => {
    successors.set(n.id, new Set());
    predecessors.set(n.id, new Set());
  });
  
  // 分类边：前向边和回边
  const forwardEdges: GraphEdge[] = [];
  const backEdges: GraphEdge[] = [];
  
  structure.edges.forEach(e => {
    if (!nodeSet.has(e.source) || !nodeSet.has(e.target)) return;
    if (e.source === e.target) return;
    successors.get(e.source)!.add(e.target);
    predecessors.get(e.target)!.add(e.source);
  });
  
  // 使用 DFS 检测回边并分层
  const layers = new Map<string, number>();
  const visited = new Set<string>();
  const inStack = new Set<string>();
  
  function dfs(nodeId: string, depth: number): void {
    if (inStack.has(nodeId)) return; // 检测到回边，跳过
    if (visited.has(nodeId)) {
      // 已访问但不在栈中，更新层级为更深的值
      layers.set(nodeId, Math.max(layers.get(nodeId) || 0, depth));
      return;
    }
    
    visited.add(nodeId);
    inStack.add(nodeId);
    layers.set(nodeId, depth);
    
    for (const succ of successors.get(nodeId) || []) {
      if (inStack.has(succ)) {
        // 这是一条回边
        backEdges.push({ source: nodeId, target: succ, conditional: false });
      } else {
        forwardEdges.push({ source: nodeId, target: succ, conditional: false });
        dfs(succ, depth + 1);
      }
    }
    
    inStack.delete(nodeId);
  }
  
  // 从 start 节点或入度为0的节点开始 DFS
  const startNode = structure.nodes.find(n => n.type === "start");
  if (startNode) {
    dfs(startNode.id, 0);
  }
  
  // 处理未访问的节点
  structure.nodes.forEach(n => {
    if (!visited.has(n.id)) {
      dfs(n.id, 0);
    }
  });
  
  // 按层分组
  const layerGroups = new Map<number, string[]>();
  layers.forEach((layer, nodeId) => {
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer)!.push(nodeId);
  });
  
  // 优化层内顺序以减少边交叉
  const nodeOrder = new Map<string, number>();
  const sortedLayers = Array.from(layerGroups.keys()).sort((a, b) => a - b);
  
  sortedLayers.forEach((layerIdx, i) => {
    const nodesInLayer = layerGroups.get(layerIdx)!;
    
    if (i === 0) {
      // 第一层：start 节点居中
      nodesInLayer.sort((a, b) => {
        const nodeA = structure.nodes.find(n => n.id === a);
        if (nodeA?.type === "start") return -1;
        return 0;
      });
    } else {
      // 后续层：按前驱节点的重心排序
      nodesInLayer.sort((a, b) => {
        const predsA = Array.from(predecessors.get(a) || []);
        const predsB = Array.from(predecessors.get(b) || []);
        
        const avgA = predsA.length > 0 
          ? predsA.reduce((sum, p) => sum + (nodeOrder.get(p) ?? 0), 0) / predsA.length 
          : 0;
        const avgB = predsB.length > 0 
          ? predsB.reduce((sum, p) => sum + (nodeOrder.get(p) ?? 0), 0) / predsB.length 
          : 0;
        
        return avgA - avgB;
      });
    }
    
    nodesInLayer.forEach((nodeId, idx) => {
      nodeOrder.set(nodeId, idx);
    });
  });
  
  // 计算坐标 - 使用更大的间距来容纳回边
  const horizontalSpacing = 160;
  const verticalSpacing = 110;
  
  let maxLayerWidth = 1;
  layerGroups.forEach((nodes) => {
    maxLayerWidth = Math.max(maxLayerWidth, nodes.length);
  });
  
  const canvasWidth = Math.max(maxLayerWidth * horizontalSpacing, horizontalSpacing * 2);
  
  layerGroups.forEach((nodesInLayer, layer) => {
    const layerWidth = nodesInLayer.length * horizontalSpacing;
    const startX = (canvasWidth - layerWidth) / 2 + horizontalSpacing / 2;
    
    nodesInLayer.forEach((nodeId, idx) => {
      positions.set(nodeId, {
        x: startX + idx * horizontalSpacing,
        y: layer * verticalSpacing + 40
      });
    });
  });
  
  return positions;
}

// 转换后端数据为React Flow格式
function convertToReactFlowData(
  structure: GraphStructure,
  completedNodes: Set<string>,
  activeNodes: Set<string>,
  errorNodes: Set<string>
): { nodes: Node[]; edges: Edge[] } {
  const getStatus = (id: string) => {
    if (errorNodes.has(id)) return "error";
    if (activeNodes.has(id)) return "running";
    if (completedNodes.has(id)) return "completed";
    return "pending";
  };

  // 使用图布局算法计算位置
  const nodePositions = calculateGraphLayout(structure);
  const nodeWidth = 100;

  const nodes: Node[] = structure.nodes.map((node) => {
    const status = getStatus(node.id);
    const style = getNodeStyle(status);
    const pos = nodePositions.get(node.id) || { x: 0, y: 0 };
    const isTerminal = node.type === "start" || node.type === "end";

    return {
      id: node.id,
      position: pos,
      data: { label: NODE_LABELS_CN[node.id] || node.label },
      style: {
        ...style,
        borderRadius: isTerminal ? "50%" : "8px",
        padding: isTerminal ? "8px" : "8px 12px",
        fontSize: "11px",
        fontWeight: status === "running" ? 600 : 400,
        width: isTerminal ? 45 : nodeWidth,
        height: isTerminal ? 45 : "auto",
        minHeight: isTerminal ? 45 : 36,
        textAlign: "center" as const,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: status === "running" ? "0 0 8px rgba(59, 130, 246, 0.5)" : "none",
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    };
  });

  const edges: Edge[] = structure.edges.map((edge, i) => {
    const sourceStatus = getStatus(edge.source);
    const isActive = sourceStatus === "completed" || sourceStatus === "running";

    return {
      id: `e${i}`,
      source: edge.source,
      target: edge.target,
      animated: isActive,
      style: {
        stroke: isActive ? "#3b82f6" : "#d1d5db",
        strokeWidth: edge.conditional ? 1 : 2,
        strokeDasharray: edge.conditional ? "5,5" : undefined,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isActive ? "#3b82f6" : "#d1d5db",
        width: 15,
        height: 15,
      },
    };
  });

  return { nodes, edges };
}

// 内部流程图组件
function GraphVisualizerInner() {
  const [graphStructure, setGraphStructure] = useState<GraphStructure | null>(null);
  const [graphInfo, setGraphInfo] = useState<GraphInfo | null>(null);
  const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());
  const [activeNodes, setActiveNodes] = useState<Set<string>>(new Set());
  const [errorNodes] = useState<Set<string>>(new Set());

  const [assistantId] = useQueryState("assistantId", { defaultValue: "smart" });
  const stream = useStreamContext();
  const isLoading = stream.isLoading;
  const streamValues = (stream as any).values;
  
  const reactFlowInstance = useReactFlow();

  // 获取实际 graph ID
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

  // 从 stream values 推断节点状态
  useEffect(() => {
    if (!streamValues) return;
    
    const newCompleted = new Set<string>();
    const newActive = new Set<string>();
    
    // 开始节点
    if (isLoading || streamValues.skill_skeleton) {
      newCompleted.add("__start__");
    }
    
    // 骨架生成
    if (streamValues.skill_skeleton && Object.keys(streamValues.skill_skeleton).length > 0) {
      newCompleted.add("skeleton_generator");
    } else if (isLoading) {
      newActive.add("skeleton_generator");
    }
    
    // Track 状态
    const generatedTracks = streamValues.generated_tracks || [];
    const trackPlan = streamValues.track_plan || [];
    
    if (newCompleted.has("skeleton_generator")) {
      if (generatedTracks.length > 0) {
        newCompleted.add("track_action_generator");
        newCompleted.add("track_validator");
        newCompleted.add("track_saver");
      }
      if (generatedTracks.length < trackPlan.length && isLoading) {
        newActive.add("track_action_generator");
      }
    }
    
    // 组装状态
    if (streamValues.assembled_skill && Object.keys(streamValues.assembled_skill).length > 0) {
      newCompleted.add("skill_assembler");
    } else if (generatedTracks.length === trackPlan.length && trackPlan.length > 0 && isLoading) {
      newActive.add("skill_assembler");
    }
    
    // 最终结果
    if (streamValues.final_result && Object.keys(streamValues.final_result).length > 0) {
      newCompleted.add("finalize");
      newCompleted.add("skill_assembler");
      newCompleted.add("__end__");
    } else if (newCompleted.has("skill_assembler") && isLoading) {
      newActive.add("finalize");
    }
    
    setCompletedNodes(newCompleted);
    setActiveNodes(newActive);
  }, [streamValues, isLoading]);

  // 转换为React Flow数据
  const { nodes, edges } = useMemo(() => {
    if (!graphStructure) return { nodes: [], edges: [] };
    return convertToReactFlowData(graphStructure, completedNodes, activeNodes, errorNodes);
  }, [graphStructure, completedNodes, activeNodes, errorNodes]);

  // 当图结构变化时自动适应视图
  useEffect(() => {
    if (nodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
      }, 200);
    }
  }, [graphStructure, reactFlowInstance, nodes.length]);

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="flex items-center gap-2 px-4 py-3 border-b flex-shrink-0">
        {GRAPH_ICONS[effectiveGraphId] || <Activity className="h-4 w-4 text-gray-500" />}
        <span className="font-medium text-sm text-gray-700 truncate">
          {graphInfo?.name || "执行流程"}
        </span>
        {isLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500 ml-auto flex-shrink-0" />}
      </div>

      <div className="flex-1 relative" style={{ minHeight: 300 }}>
        {graphStructure ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ padding: 0.2, maxZoom: 1.5, minZoom: 0.3 }}
            nodesDraggable={true}
            nodesConnectable={false}
            elementsSelectable={true}
            panOnDrag={true}
            zoomOnScroll={true}
            zoomOnPinch={true}
            zoomOnDoubleClick={true}
            preventScrolling={true}
            minZoom={0.2}
            maxZoom={2}
            defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
          >
            <Background color="#e5e7eb" gap={20} size={1} />
            <Controls 
              showZoom={true}
              showFitView={true}
              showInteractive={false}
              position="bottom-right"
              style={{ 
                display: 'flex', 
                flexDirection: 'column',
                gap: '4px',
                background: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                padding: '4px'
              }}
            />
          </ReactFlow>
        ) : (
          <div className="flex items-center justify-center h-full gap-2 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>加载图结构中...</span>
          </div>
        )}
      </div>
    </div>
  );
}

// 主组件（包装 ReactFlowProvider）
export function GraphVisualizer() {
  return (
    <ReactFlowProvider>
      <GraphVisualizerInner />
    </ReactFlowProvider>
  );
}
