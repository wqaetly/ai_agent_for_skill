"use client";

import React from "react";
import { StatusIndicator } from "@/components/ui/status-indicator";
import {
  useRAGServiceStatus,
  useUnityConnectionStatus,
} from "@/hooks/use-service-status";
import { useApiConfig } from "@/providers/Stream";
import { cn } from "@/lib/utils";

interface ServiceStatusPanelProps {
  className?: string;
  checkInterval?: number;
}

export function ServiceStatusPanel({
  className,
  checkInterval = 30000,
}: ServiceStatusPanelProps) {
  const { apiUrl, apiKey } = useApiConfig();

  const { status: ragStatus } = useRAGServiceStatus({
    apiUrl,
    apiKey,
    checkInterval,
    enabled: !!apiUrl,
  });

  const { status: unityStatus } = useUnityConnectionStatus({
    apiUrl,
    apiKey,
    checkInterval,
    enabled: !!apiUrl,
  });

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <StatusIndicator
        label="RAG"
        status={ragStatus.status}
        latency={ragStatus.latency}
        error={ragStatus.error}
        lastChecked={ragStatus.lastChecked}
      />
      <StatusIndicator
        label="Unity"
        status={unityStatus.status}
        latency={unityStatus.latency}
        error={unityStatus.error}
        lastChecked={unityStatus.lastChecked}
      />
    </div>
  );
}
