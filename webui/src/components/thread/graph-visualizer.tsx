"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Node,
  Edge,
  Position,
  MarkerType,
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

  // 简单的层级布局
  const nodeOrder = [
    "__start__",
    "skeleton_generator",
    "skeleton_fixer",
    "track_action_generator",
    "track_validator",
    "track_fixer",
    "track_saver",
    "skill_assembler",
    "finalize",
    "__end__",
  ];

  const nodes: Node[] = structure.nodes.map((node) => {
    const status = getStatus(node.id);
    const style = getNodeStyle(status);
    const orderIndex = nodeOrder.indexOf(node.id);
    const yPos = orderIndex >= 0 ? orderIndex * 70 : structure.nodes.indexOf(node) * 70;

    return {
      id: node.id,
      position: { x: 100, y: yPos },
      data: {
        label: NODE_LABELS_CN[node.id] || node.label,
      },
      style: {
        ...style,
        borderRadius: node.type === "start" || node.type === "end" ? "50%" : "8px",
        padding: "8px 16px",
        fontSize: "12px",
        fontWeight: status === "running" ? 600 : 400,
        width: node.type === "start" || node.type === "end" ? 60 : 100,
        textAlign: "center" as const,
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
      },
    };
  });

  return { nodes, edges };
}
