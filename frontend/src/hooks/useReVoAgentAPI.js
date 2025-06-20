// Updated reVoAgent Frontend API Integration Hooks
// Compatible with the enhanced backend (Phase 2)

import { useState, useEffect, useCallback, useRef } from 'react';

// =============================================================================
// API CLIENT CONFIGURATION WITH IMPROVED URL DETECTION
// =============================================================================

// FIXED: Enhanced URL detection for flexible deployment environments
const isDevelopment = import.meta.env.DEV;
const isRuntimeEnvironment = window.location.hostname.includes('prod-runtime.all-hands.dev');

// Centralized URL configuration that properly handles all environments
const API_BASE_URL = (() => {
  // First priority: Explicit environment variable
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  
  // Second priority: Runtime environment detection
  if (isRuntimeEnvironment) {
    return `https://${window.location.hostname}`;
  }
  
  // Default fallback for local development
  return 'http://localhost:12001';  // FIXED: Using port 12001, the correct backend port
})();

// WebSocket URL derived from API URL
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('revoagent_token');
    
    if (isDevelopment) {
      console.log(`🔗 API Base URL: ${baseURL}`);
    }
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

// =============================================================================
// WEBSOCKET MANAGER WITH IMPROVED RECONNECT LOGIC
// =============================================================================

class WebSocketManager {
  constructor() {
    this.connections = new Map();
    this.reconnectAttempts = new Map();
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(endpoint, sessionId, onMessage, onError) {
    // FIXED: Using the correct WebSocket URL format
    const wsUrl = `${WS_BASE_URL}${endpoint}`;
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

const apiClient = new APIClient();
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
      // FIXED: Using the correct health endpoint
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

// =============================================================================
// LLM SYSTEM HOOKS
// =============================================================================

export const useLLMModels = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true);
      // FIXED: Using the correct models endpoint
      const response = await apiClient.get('/api/models');
      setModels(response.models || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return { models, loading, error, refetch: fetchModels };
};

export const useLLMConfig = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      // FIXED: Using the correct LLM config endpoint
      const data = await apiClient.get('/api/config/llm');
      setConfig(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return { config, loading, error, refetch: fetchConfig };
};

// =============================================================================
// AGENT MANAGEMENT HOOKS - UPDATED FOR ENHANCED BACKEND
// =============================================================================

export const useAgents = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      // FIXED: Using the correct agents endpoint
      const data = await apiClient.get('/api/agents/status');
      setAgents(data.agents || []);
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

  // FIXED: Updated to match the enhanced backend agent task API
  const executeAgentTask = useCallback(async (agentType, taskData) => {
    try {
      return await apiClient.post(`/api/agent`, {
        agent_type: agentType,
        message: taskData.content || taskData.message || taskData.task,
        model: taskData.model,
        temperature: taskData.temperature,
        max_tokens: taskData.max_tokens
      });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return { 
    agents, 
    loading, 
    error, 
    getAgent, 
    executeAgentTask,
    refetch: fetchAgents 
  };
};

// =============================================================================
// CHAT HOOKS - UPDATED FOR ENHANCED BACKEND
// =============================================================================

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // FIXED: Updated to match the enhanced backend chat API
  const sendMessage = useCallback(async (content, options = {}) => {
    try {
      setLoading(true);
      
      // Select the correct endpoint based on options
      const endpoint = options.multiAgent ? '/api/chat/multi-agent' : '/api/chat';
      
      // Format the request body correctly
      const payload = {
        message: content,
        model: options.model || 'deepseek-r1',
        temperature: options.temperature || 0.7,
        max_tokens: options.max_tokens || 1000
      };

      const response = await apiClient.post(endpoint, payload);
      
      // Create user message
      const userMessage = { 
        role: 'user', 
        content, 
        timestamp: new Date().toISOString() 
      };
      
      // Create assistant message based on which endpoint was used
      let assistantMessage;
      if (options.multiAgent) {
        // Multi-agent response
        assistantMessage = {
          role: 'assistant',
          content: response.responses ? response.responses.map(r => 
            `${r.agent}: ${r.response}`
          ).join('\n\n') : 'No response',
          timestamp: new Date().toISOString()
        };
      } else {
        // Single-agent response
        assistantMessage = {
          role: 'assistant',
          content: response.response,
          model: response.model,
          timestamp: response.timestamp
        };
      }

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
    clearMessages 
  };
};

// FIXED: Updated real-time chat hook for enhanced WebSocket API
export const useRealTimeChat = (sessionId = 'default') => {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  // Send a message through WebSocket
  const sendMessage = useCallback((message, options = {}) => {
    if (connected) {
      // FIXED: Match expected format by backend WebSocket handler
      wsManager.send('ws/chat', { 
        message,
        model: options.model || 'deepseek-r1',
        temperature: options.temperature || 0.7, 
        max_tokens: options.max_tokens || 1000
      });
      
      // Add user message immediately
      const userMessage = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);
    } else {
      setError(new Error('WebSocket not connected'));
    }
  }, [connected]);

  // Connect to WebSocket on mount with updated endpoint
  useEffect(() => {
    wsManager.connect(
      '/ws/chat',
      sessionId,
      (data) => {
        if (data.type === 'response') {
          const assistantMessage = {
            role: 'assistant',
            content: data.response,
            model: data.model,
            timestamp: data.timestamp
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else if (data.type === 'error') {
          setError(new Error(data.error));
        }
        setConnected(true);
      },
      (error) => {
        setError(error);
        setConnected(false);
      }
    );

    return () => {
      wsManager.disconnect('ws/chat');
      setConnected(false);
    };
  }, [sessionId]);

  return { messages, connected, error, sendMessage };
};

// =============================================================================
// MEMORY AND KNOWLEDGE HOOKS - UPDATED FOR ENHANCED BACKEND
// =============================================================================

export const useMemory = () => {
  const [memoryStats, setMemoryStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getMemoryStats = useCallback(async () => {
    try {
      setLoading(true);
      // FIXED: Using the correct memory stats endpoint
      const data = await apiClient.get('/api/memory/stats');
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
      // FIXED: Using the correct memory query endpoint
      return await apiClient.post('/api/memory/query', {
        text: query,
        limit: options.limit || 10,
        include_context: options.includeContext !== false
      });
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  useEffect(() => {
    getMemoryStats();
  }, [getMemoryStats]);

  return { 
    memoryStats, 
    loading, 
    error, 
    queryMemory, 
    refetch: getMemoryStats 
  };
};

// =============================================================================
// EXPORT ALL HOOKS AND CLIENTS
// =============================================================================

export {
  apiClient,
  wsManager
};