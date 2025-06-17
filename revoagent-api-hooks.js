// /src/hooks/useReVoAgentAPI.js
/**
 * reVoAgent Frontend API Integration Hooks
 * Complete integration with Three-Engine Backend
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// =============================================================================
// API CLIENT CONFIGURATION
// =============================================================================

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:12000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:12000';

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('revoagent_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('revoagent_token', token);
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

const apiClient = new APIClient();

// =============================================================================
// WEBSOCKET MANAGER
// =============================================================================

class WebSocketManager {
  constructor() {
    this.connections = new Map();
    this.reconnectAttempts = new Map();
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(endpoint, sessionId, onMessage, onError) {
    const wsUrl = `${WS_BASE_URL}/ws/${endpoint}/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log(`WebSocket connected: ${endpoint}`);
      this.reconnectAttempts.set(endpoint, 0);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };
    
    ws.onclose = () => {
      console.log(`WebSocket disconnected: ${endpoint}`);
      this.handleReconnect(endpoint, sessionId, onMessage, onError);
    };
    
    ws.onerror = (error) => {
      console.error(`WebSocket error: ${endpoint}`, error);
      if (onError) onError(error);
    };
    
    this.connections.set(endpoint, ws);
    return ws;
  }

  handleReconnect(endpoint, sessionId, onMessage, onError) {
    const attempts = this.reconnectAttempts.get(endpoint) || 0;
    
    if (attempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        console.log(`Reconnecting WebSocket: ${endpoint} (attempt ${attempts + 1})`);
        this.reconnectAttempts.set(endpoint, attempts + 1);
        this.connect(endpoint, sessionId, onMessage, onError);
      }, this.reconnectDelay * Math.pow(2, attempts));
    }
  }

  disconnect(endpoint) {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close();
      this.connections.delete(endpoint);
      this.reconnectAttempts.delete(endpoint);
    }
  }

  send(endpoint, data) {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }
}

const wsManager = new WebSocketManager();

// =============================================================================
// SYSTEM STATUS HOOKS
// =============================================================================

export const useSystemHealth = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/health');
      setHealth(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return { health, loading, error, refetch: fetchHealth };
};

export const useEngineStatus = () => {
  const [engines, setEngines] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEngines = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/engines/status');
      setEngines(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEngines();
    const interval = setInterval(fetchEngines, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [fetchEngines]);

  return { engines, loading, error, refetch: fetchEngines };
};

export const useSystemMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [realTime, setRealTime] = useState(false);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/system/metrics');
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const enableRealTime = useCallback((sessionId = 'default') => {
    setRealTime(true);
    wsManager.connect(
      'system',
      sessionId,
      (data) => {
        if (data.type === 'system_metrics') {
          setMetrics(data.data);
        }
      },
      (error) => setError(error.message)
    );
  }, []);

  const disableRealTime = useCallback(() => {
    setRealTime(false);
    wsManager.disconnect('system');
  }, []);

  useEffect(() => {
    if (!realTime) {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, 10000); // Update every 10 seconds
      return () => clearInterval(interval);
    }
  }, [fetchMetrics, realTime]);

  return { 
    metrics, 
    loading, 
    error, 
    realTime,
    enableRealTime,
    disableRealTime,
    refetch: fetchMetrics 
  };
};

// =============================================================================
// AGENT MANAGEMENT HOOKS
// =============================================================================

export const useAgents = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/agents');
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const getAgent = useCallback(async (agentId) => {
    try {
      return await apiClient.get(`/api/agents/${agentId}`);
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, []);

  const createTask = useCallback(async (agentId, taskData) => {
    try {
      return await apiClient.post(`/api/agents/${agentId}/tasks`, taskData);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const updateAgentStatus = useCallback(async (agentId, status) => {
    try {
      await apiClient.put(`/api/agents/${agentId}/status`, { status });
      await fetchAgents(); // Refresh the list
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchAgents]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return { 
    agents, 
    loading, 
    error, 
    getAgent, 
    createTask, 
    updateAgentStatus,
    refetch: fetchAgents 
  };
};

// =============================================================================
// CHAT HOOKS
// =============================================================================

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (content, options = {}) => {
    try {
      setLoading(true);
      const endpoint = options.multiAgent ? '/api/chat/multi-agent' : '/api/chat';
      const payload = options.multiAgent 
        ? { content, agents: options.agents || [] }
        : { content, role: 'user' };

      const response = await apiClient.post(endpoint, payload);
      
      const userMessage = { 
        role: 'user', 
        content, 
        timestamp: new Date().toISOString() 
      };
      
      const assistantMessage = {
        role: 'assistant',
        content: options.multiAgent ? response.results : response.content,
        provider: response.provider,
        cost: response.cost || response.total_cost,
        timestamp: response.timestamp
      };

      setMessages(prev => [...prev, userMessage, assistantMessage]);
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMemoryEnabledMessage = useCallback(async (content, sessionId) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/api/chat/memory-enabled', {
        content,
        role: 'user',
        session_id: sessionId,
        memory_enabled: true
      });

      const userMessage = { 
        role: 'user', 
        content, 
        timestamp: new Date().toISOString() 
      };
      
      const assistantMessage = {
        role: 'assistant',
        content: response.content,
        provider: response.provider,
        cost: response.cost,
        memory_context: response.memory_context,
        timestamp: response.timestamp
      };

      setMessages(prev => [...prev, userMessage, assistantMessage]);
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { 
    messages, 
    loading, 
    error, 
    sendMessage, 
    sendMemoryEnabledMessage,
    clearMessages 
  };
};

export const useRealTimeChat = (sessionId) => {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback((content) => {
    if (connected) {
      wsManager.send('chat', { content, session_id: sessionId });
      
      // Add user message immediately
      const userMessage = {
        role: 'user',
        content,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);
    }
  }, [connected, sessionId]);

  useEffect(() => {
    if (sessionId) {
      wsManager.connect(
        'chat',
        sessionId,
        (data) => {
          if (data.type === 'ai_response') {
            const assistantMessage = {
              role: 'assistant',
              content: data.content,
              provider: data.provider,
              cost: data.cost,
              timestamp: data.timestamp
            };
            setMessages(prev => [...prev, assistantMessage]);
          }
          setConnected(true);
        },
        (error) => {
          setError(error.message);
          setConnected(false);
        }
      );

      return () => {
        wsManager.disconnect('chat');
        setConnected(false);
      };
    }
  }, [sessionId]);

  return { messages, connected, error, sendMessage };
};

// =============================================================================
// MEMORY AND KNOWLEDGE HOOKS
// =============================================================================

export const useMemory = () => {
  const [memoryStats, setMemoryStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getMemoryStats = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/engines/memory/stats');
      setMemoryStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const queryMemory = useCallback(async (query, options = {}) => {
    try {
      return await apiClient.post('/api/engines/memory/query', {
        query,
        agent_id: options.agentId,
        limit: options.limit || 10,
        include_context: options.includeContext !== false
      });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const enableRealTimeMemory = useCallback((sessionId = 'default') => {
    wsManager.connect(
      'memory',
      sessionId,
      (data) => {
        if (data.type === 'memory_update') {
          setMemoryStats(data.data);
        }
      },
      (error) => setError(error.message)
    );
  }, []);

  useEffect(() => {
    getMemoryStats();
  }, [getMemoryStats]);

  return { 
    memoryStats, 
    loading, 
    error, 
    queryMemory, 
    enableRealTimeMemory,
    refetch: getMemoryStats 
  };
};

// =============================================================================
// WORKFLOW HOOKS
// =============================================================================

export const useWorkflows = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchWorkflows = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/workflows');
      setWorkflows(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const createWorkflow = useCallback(async (workflowData) => {
    try {
      const response = await apiClient.post('/api/workflows', workflowData);
      await fetchWorkflows(); // Refresh the list
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchWorkflows]);

  const executeWorkflow = useCallback(async (workflowId, parameters = {}) => {
    try {
      return await apiClient.post(`/api/workflows/${workflowId}/execute`, parameters);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  return { 
    workflows, 
    loading, 
    error, 
    createWorkflow, 
    executeWorkflow,
    refetch: fetchWorkflows 
  };
};

// =============================================================================
// ANALYTICS HOOKS
// =============================================================================

export const useAnalytics = () => {
  const [costAnalytics, setCostAnalytics] = useState(null);
  const [performanceAnalytics, setPerformanceAnalytics] = useState(null);
  const [agentAnalytics, setAgentAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCostAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/analytics/costs');
      setCostAnalytics(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const fetchPerformanceAnalytics = useCallback(async () => {
    try {
      const data = await apiClient.get('/api/analytics/performance');
      setPerformanceAnalytics(data);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const fetchAgentAnalytics = useCallback(async () => {
    try {
      const data = await apiClient.get('/api/analytics/agents');
      setAgentAnalytics(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAllAnalytics = useCallback(async () => {
    await Promise.all([
      fetchCostAnalytics(),
      fetchPerformanceAnalytics(),
      fetchAgentAnalytics()
    ]);
  }, [fetchCostAnalytics, fetchPerformanceAnalytics, fetchAgentAnalytics]);

  useEffect(() => {
    fetchAllAnalytics();
  }, [fetchAllAnalytics]);

  return { 
    costAnalytics,
    performanceAnalytics,
    agentAnalytics,
    loading, 
    error,
    refetch: fetchAllAnalytics 
  };
};

// =============================================================================
// EXTERNAL INTEGRATIONS HOOKS
// =============================================================================

export const useIntegrations = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const executeGitHubAction = useCallback(async (action, parameters) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/api/integrations/github', {
        service: 'github',
        action,
        parameters
      });
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const executeSlackAction = useCallback(async (action, parameters) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/api/integrations/slack', {
        service: 'slack',
        action,
        parameters
      });
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const executeJiraAction = useCallback(async (action, parameters) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/api/integrations/jira', {
        service: 'jira',
        action,
        parameters
      });
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { 
    loading, 
    error,
    executeGitHubAction,
    executeSlackAction,
    executeJiraAction
  };
};

// =============================================================================
// MCP STORE HOOKS
// =============================================================================

export const useMCPStore = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMCPAgents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/mcp/agents');
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const installAgent = useCallback(async (agentId) => {
    try {
      const response = await apiClient.post('/api/mcp/agents/install', {
        agent_id: agentId
      });
      await fetchMCPAgents(); // Refresh the list
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchMCPAgents]);

  useEffect(() => {
    fetchMCPAgents();
  }, [fetchMCPAgents]);

  return { 
    agents, 
    loading, 
    error, 
    installAgent,
    refetch: fetchMCPAgents 
  };
};

// =============================================================================
// THREE-ENGINE DEMO HOOK
// =============================================================================

export const useThreeEngineDemo = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runShowcase = useCallback(async (task, complexity = 'medium') => {
    try {
      setLoading(true);
      const response = await apiClient.post('/api/engines/demo/three-engine-showcase', {
        task,
        complexity
      });
      setError(null);
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, runShowcase };
};

// =============================================================================
// CONFIGURATION HOOK
// =============================================================================

export const useConfiguration = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/config');
      setConfig(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (newConfig) => {
    try {
      const response = await apiClient.put('/api/config', newConfig);
      await fetchConfig(); // Refresh the config
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [fetchConfig]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return { 
    config, 
    loading, 
    error, 
    updateConfig,
    refetch: fetchConfig 
  };
};

// =============================================================================
// EXPORT ALL HOOKS
// =============================================================================

export {
  apiClient,
  wsManager
};