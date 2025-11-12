"use client";

import { useState, useEffect, useCallback } from "react";
import {
  ServiceStatusInfo,
  checkRAGServiceStatus,
  checkUnityConnectionStatus,
} from "@/lib/service-status";

interface UseServiceStatusOptions {
  apiUrl: string;
  apiKey?: string | null;
  checkInterval?: number; // 检查间隔（毫秒），默认30秒
  enabled?: boolean; // 是否启用自动检查
}

export function useRAGServiceStatus({
  apiUrl,
  apiKey,
  checkInterval = 30000,
  enabled = true,
}: UseServiceStatusOptions) {
  const [status, setStatus] = useState<ServiceStatusInfo>({
    status: "checking",
  });

  const checkStatus = useCallback(async () => {
    if (!enabled || !apiUrl) return;
    const result = await checkRAGServiceStatus(apiUrl, apiKey);
    setStatus(result);
  }, [apiUrl, apiKey, enabled]);

  useEffect(() => {
    if (!enabled || !apiUrl) return;

    // 立即检查一次
    checkStatus();

    // 设置定时检查
    const interval = setInterval(checkStatus, checkInterval);

    return () => clearInterval(interval);
  }, [checkStatus, checkInterval, enabled, apiUrl]);

  return { status, refresh: checkStatus };
}

export function useUnityConnectionStatus({
  apiUrl,
  apiKey,
  checkInterval = 30000,
  enabled = true,
}: UseServiceStatusOptions) {
  const [status, setStatus] = useState<ServiceStatusInfo>({
    status: "checking",
  });

  const checkStatus = useCallback(async () => {
    if (!enabled || !apiUrl) return;
    const result = await checkUnityConnectionStatus(apiUrl, apiKey);
    setStatus(result);
  }, [apiUrl, apiKey, enabled]);

  useEffect(() => {
    if (!enabled || !apiUrl) return;

    // 立即检查一次
    checkStatus();

    // 设置定时检查
    const interval = setInterval(checkStatus, checkInterval);

    return () => clearInterval(interval);
  }, [checkStatus, checkInterval, enabled, apiUrl]);

  return { status, refresh: checkStatus };
}
