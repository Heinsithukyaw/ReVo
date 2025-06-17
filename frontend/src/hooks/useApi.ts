import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import type { DashboardStats, WorkflowData, ActivityItem, SystemMetric, IntegrationStatus, ModelInfo } from '../types';

// Generic API hook
export function useApi<T>(
  endpoint: string,
  options?: {
    immediate?: boolean;
    interval?: number;
    fallback?: T;
  }
) {
  const [data, setData] = useState<T | null>(options?.fallback || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.get<T>(endpoint);
      setData(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      if (options?.fallback) {
        setData(options.fallback);
      }
    } finally {
      setLoading(false);
    }
  }, [endpoint, options?.fallback]);

  useEffect(() => {
    if (options?.immediate !== false) {
      fetchData();
    }
  }, [fetchData, options?.immediate]);

  useEffect(() => {
    if (options?.interval) {
      const intervalId = setInterval(fetchData, options.interval);
      return () => clearInterval(intervalId);
    }
  }, [fetchData, options?.interval]);

  return { data, loading, error, refetch: fetchData };
}

// Dashboard stats hook
export function useDashboardStats() {
  const [stats, setStats] = useState<DashboardStats>({
    agents: { active: 8, total: 25 },
    workflows: { active: 3, total: 12 },
    projects: { active: 2, total: 8 },
    system: { cpu_usage: 67.8, memory_usage: 89.2, disk_usage: 45.3 }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}

// Agents hook
export function useAgents() {
  const [agents, setAgents] = useState<Record<string, any>>({});
  const [activeTasks, setActiveTasks] = useState(12);
  const [totalAgents, setTotalAgents] = useState(25);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.getAgents();
      setAgents(data.agents);
      setActiveTasks(data.active_tasks);
      setTotalAgents(data.total_agents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 15000); // Update every 15 seconds
    return () => clearInterval(interval);
  }, [fetchAgents]);

  return { agents, activeTasks, totalAgents, loading, error, refetch: fetchAgents };
}

// System metrics hook
export function useSystemMetrics() {
  const [metrics, setMetrics] = useState<{ [key: string]: SystemMetric }>({
    cpu: { name: 'CPU', value: 67.8, color: 'blue' },
    memory: { name: 'Memory', value: 89.2, color: 'green' },
    disk: { name: 'Disk', value: 45.3, color: 'yellow' }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.getSystemMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch system metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return { metrics, loading, error, refetch: fetchMetrics };
}

// Health check hook
export function useHealthCheck() {
  const [health, setHealth] = useState<{ status: string; version?: string; services?: any }>({ 
    status: 'healthy',
    version: '1.0.0',
    services: {
      memory_engine: 'active',
      parallel_engine: 'active', 
      creative_engine: 'active'
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.healthCheck();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Health check failed');
      setHealth({ status: 'offline' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { health, loading, error, refetch: checkHealth };
}

// Chat hook
export function useChat() {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string, options?: any) => {
    setLoading(true);
    setError(null);
    
    const userMessage = {
      id: Date.now().toString(),
      content,
      role: 'user' as const,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      const response = await apiService.sendChatMessage(content, options);
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        role: 'assistant' as const,
        timestamp: new Date(),
        metadata: {
          provider: response.provider,
          tokens_used: response.tokens_used,
          generation_time: response.generation_time
        }
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearMessages };
}

// Connection status hook
export function useConnectionStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const checkConnection = () => {
      setIsOnline(apiService.getConnectionStatus());
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  return isOnline;
}