'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import axiosInstance from '@/lib/axiosInstance';

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    total: number;
    used: number;
    free: number;
  };
  storage: {
    total: number;
    used: number;
    free: number;
  };
}

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function HostMonitoring() {
  const { data: session, status } = useSession();
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (status === 'authenticated') {
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
        if (!token) throw new Error('Access token is not available');

        const response = await axiosInstance.get('/system-metrics', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setMetrics(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching metrics:', err);
        setError('Failed to fetch system metrics');
      } finally {
        setIsLoading(false);
      }
    }
  }, [session, status]);

  useEffect(() => {
    if (status === 'authenticated') {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, 5000);
      return () => clearInterval(interval);
    }
  }, [status, fetchMetrics]);

  if (status === 'loading' || isLoading) {
    return (
      <div className="container mx-auto py-8 text-center">
        Loading system metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 text-center text-red-500">
        Error: {error}
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="container mx-auto py-8 text-center">
        No metrics available
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let value = bytes;
    let unitIndex = 0;
    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024;
      unitIndex++;
    }
    return `${value.toFixed(2)} ${units[unitIndex]}`;
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">System Metrics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* CPU Usage */}
        <div className="bg-white border border-gray-200 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">CPU Usage</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Usage</span>
              <span className="font-medium">{metrics.cpu.usage.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full"
                style={{ width: `${metrics.cpu.usage}%` }}
              ></div>
            </div>
            <div className="text-sm text-gray-500">
              Cores: {metrics.cpu.cores}
            </div>
          </div>
        </div>

        {/* Memory Usage */}
        <div className="bg-white border border-gray-200 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Memory Usage</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Used</span>
              <span className="font-medium">{formatBytes(metrics.memory.used)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-green-600 h-2.5 rounded-full"
                style={{ width: `${(metrics.memory.used / metrics.memory.total) * 100}%` }}
              ></div>
            </div>
            <div className="text-sm text-gray-500">
              Total: {formatBytes(metrics.memory.total)}
            </div>
          </div>
        </div>

        {/* Storage Usage */}
        <div className="bg-white border border-gray-200 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Storage Usage</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Used</span>
              <span className="font-medium">{formatBytes(metrics.storage.used)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-purple-600 h-2.5 rounded-full"
                style={{ width: `${(metrics.storage.used / metrics.storage.total) * 100}%` }}
              ></div>
            </div>
            <div className="text-sm text-gray-500">
              Total: {formatBytes(metrics.storage.total)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
