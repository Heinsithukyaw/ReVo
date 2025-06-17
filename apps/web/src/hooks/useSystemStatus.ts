import { useState, useEffect } from 'react';

interface SystemStatusHookReturn {
  systemStatus: any;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export const useSystemStatus = (): SystemStatusHookReturn => {
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSystemStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/system/status');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSystemStatus(data);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      
      // Set mock data for development
      setSystemStatus({
        status: 'operational',
        uptime: '24h 15m 32s',
        version: '3.2.0-glassmorphism',
        available_providers: ['deepseek_r1', 'llama_local', 'mock_fallback'],
        active_agents: {
          code_generator: { status: 'active', last_used: new Date().toISOString() },
          debug_agent: { status: 'active', last_used: new Date().toISOString() },
          testing_agent: { status: 'active', last_used: new Date().toISOString() },
          security_agent: { status: 'idle', last_used: null },
          documentation_agent: { status: 'idle', last_used: null }
        },
        performance_metrics: {
          cpu_usage: 24,
          memory_usage: 67,
          gpu_usage: 45,
          total_requests: 1248,
          successful_requests: 1231,
          uptime_start: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
        },
        cost_savings: {
          total_savings: 5420,
          percentage: 100,
          monthly_projection: 162600
        },
        active_connections: 3,
        active_tasks: 2
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refresh = () => {
    fetchSystemStatus();
  };

  useEffect(() => {
    fetchSystemStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    systemStatus,
    isLoading,
    error,
    refresh
  };
};