"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
  ServiceStatus,
  getStatusColor,
  getStatusText,
  formatLatency,
} from "@/lib/service-status";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Circle, AlertCircle, CheckCircle, XCircle } from "lucide-react";

interface StatusIndicatorProps {
  label: string;
  status: ServiceStatus;
  latency?: number;
  error?: string;
  lastChecked?: Date;
  className?: string;
}

function getStatusIcon(status: ServiceStatus) {
  switch (status) {
    case "connected":
      return <CheckCircle className="h-4 w-4" />;
    case "disconnected":
      return <XCircle className="h-4 w-4" />;
    case "checking":
      return <Circle className="h-4 w-4 animate-pulse" />;
    case "error":
      return <AlertCircle className="h-4 w-4" />;
    default:
      return <Circle className="h-4 w-4" />;
  }
}

export function StatusIndicator({
  label,
  status,
  latency,
  error,
  lastChecked,
  className,
}: StatusIndicatorProps) {
  const statusColor = getStatusColor(status);
  const statusText = getStatusText(status);

  const tooltipContent = (
    <div className="flex flex-col gap-1 text-xs">
      <div>
        <strong>Status:</strong> {statusText}
      </div>
      {latency !== undefined && (
        <div>
          <strong>Latency:</strong> {formatLatency(latency)}
        </div>
      )}
      {lastChecked && (
        <div>
          <strong>Last Checked:</strong> {lastChecked.toLocaleTimeString()}
        </div>
      )}
      {error && (
        <div className="text-red-400">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-gray-100",
              className,
            )}
          >
            <div className={cn(statusColor)}>{getStatusIcon(status)}</div>
            <span className="font-medium">{label}</span>
            <span className={cn("text-xs", statusColor)}>{statusText}</span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom">{tooltipContent}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
