export interface DashboardStats {
  agents: { active: number; total: number };
  workflows: { active: number; total: number };
  projects: { active: number; total: number };
  system: { cpu_usage: number; memory_usage: number; disk_usage: number };
}

export interface WorkflowData {
  id: string;
  name: string;
  agents: number;
  progress: number;
  icon: string;
  status: 'running' | 'completed' | 'paused' | 'failed';
  startTime?: string;
  estimatedTime?: string;
  estimatedCompletion?: string;
  description?: string;
}

export interface ActivityItem {
  id: string;
  title: string;
  description: string;
  timestamp: Date;
  type: 'agent' | 'workflow' | 'system';
  status: 'success' | 'warning' | 'error' | 'info';
  icon?: string;
}

export interface SystemMetric {
  name: string;
  value: number;
  color: string;
  label?: string;
  unit?: string;
}

export interface IntegrationStatus {
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  lastCheck: string;
  version?: string;
  url?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  displayName: string;
  type: 'code' | 'chat' | 'specialized';
  size: string;
  status: 'loaded' | 'available' | 'loading' | 'error';
  performance: number;
  memoryUsage?: string;
  tokensPerSecond?: number;
}

export interface AgentInfo {
  id: string;
  name: string;
  type: 'code-generator' | 'debug' | 'testing' | 'deploy' | 'browser' | 'security' | 'documentation' | 'performance-optimizer' | 'architecture-advisor';
  status: 'active' | 'idle' | 'busy' | 'error';
  currentTask?: string;
  performance: number;
  uptime: string;
}

export type TabId =
  | 'dashboard'
  | 'projects'
  | 'workflows'
  | 'analytics'
  | 'code-generator'
  | 'debug-agent'
  | 'testing-agent'
  | 'deploy-agent'
  | 'browser-agent'
  | 'security-agent'
  | 'documentation-agent'
  | 'performance-optimizer'
  | 'architecture-advisor'
  | 'agent-management'
  | 'model-registry'
  | 'settings'
  | 'security'
  | 'monitoring'
  | 'resource-mgmt'
  | 'engine-orchestrator'
  | 'mcp-marketplace'
  | 'enterprise-console'
  | 'configuration'
  | 'realtime-dashboard';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

// Chat types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    provider?: string;
    tokens_used?: number;
    generation_time?: number;
  };
}

export interface ChatResponse {
  content: string;
  provider?: string;
  tokens_used?: number;
  generation_time?: number;
  agentName?: string;
  agentType?: string;
  type?: string;
  metadata?: {
    confidence?: number;
    processingTime?: number;
    tokens?: number;
    cost?: number;
    model?: string;
    temperature?: number;
  };
}

// Engine types
export interface EngineStatus {
  name: string;
  status: 'active' | 'inactive' | 'error';
  metrics: {
    [key: string]: string | number;
  };
}

// Agent execution types
export interface AgentTask {
  id: string;
  agent_type: string;
  parameters: Record<string, any>;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  progress: number;
  result?: any;
  error?: string;
}

export interface AgentExecutionResult {
  success: boolean;
  task_id: string;
  agent_type: string;
  status: string;
  estimated_completion: string;
}