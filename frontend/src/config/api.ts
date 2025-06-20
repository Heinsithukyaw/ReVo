import { API_CONFIG } from '../utils/constants';

// API Client Configuration
export interface APIConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

export const apiConfig: APIConfig = {
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  retryAttempts: API_CONFIG.RETRY_ATTEMPTS,
  retryDelay: API_CONFIG.RETRY_DELAY,
};

// API Endpoints Mapping
export const API_ENDPOINTS = {
  // Health & Status
  health: '/health',
  healthReady: '/health/ready',
  healthLive: '/health/live',
  
  // Chat & Agents
  chat: '/api/chat',
  multiAgentChat: '/api/chat/multi-agent',
  agent: '/api/agent',
  agentStatus: '/api/agents/status',
  agents: '/api/agents',
  agentTasks: '/api/agents/tasks',
  agentConfigurations: '/api/agents/configurations',
  
  // Models & Configuration
  models: '/api/models',
  llmConfig: '/api/config/llm',
  
  // Memory System
  memoryStats: '/api/memory/stats',
  memoryStore: '/api/memory/store',
  memoryQuery: '/api/memory/query',
  
  // Chat Sessions
  chatSessions: '/api/chat/sessions',
  chatMessages: '/api/chat/messages',
  chatSend: '/api/chat/send',
  
  // System Metrics
  systemMetrics: '/api/system/metrics',
  systemStatus: '/api/system/status',
  
  // Analytics
  analytics: '/api/analytics',
  costOptimization: '/api/analytics/cost',
  performance: '/api/analytics/performance',
  
  // WebSocket Endpoints
  wsDashboard: '/ws/dashboard',
  wsChat: '/ws/chat'
} as const;

// Type-Safe API Response Types
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  services: Record<string, string>;
  llm_status: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  model: string;
  timestamp: string;
  tokens_used: number;
  response_time: number;
}

export interface AgentResponse {
  agent: string;
  response: string;
  model: string;
  timestamp: string;
}

export interface SystemStatusResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  engines: Array<{
    name: string;
    status: 'active' | 'inactive' | 'error';
    load: number;
    lastUpdate: string;
  }>;
  metrics: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    networkActivity: number;
  };
}

// Error Response Type
export interface APIError {
  error: string;
  message: string;
  timestamp: string;
  details?: any;
}

// API Response Wrapper
export interface APIResponse<T = any> {
  data: T;
  status: number;
  message?: string;
  timestamp: string;
}

// Request Types
export interface ChatRequest {
  content: string;
  agentId?: string;
  sessionId?: string;
  timestamp: string;
}

export interface AgentRequest {
  query: string;
  agent: string;
  context?: any;
}

export interface CreateAgentRequest {
  name: string;
  type: 'code' | 'workflow' | 'knowledge' | 'integration';
  description: string;
  capabilities: string[];
  configuration: Record<string, any>;
}
