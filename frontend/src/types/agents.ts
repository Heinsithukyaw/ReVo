export interface Agent {
  id: string;
  name: string;
  type: 'code' | 'workflow' | 'knowledge' | 'integration';
  status: 'active' | 'inactive' | 'busy' | 'error';
  description: string;
  capabilities: string[];
  lastActivity: string;
  metrics: AgentMetrics;
}

export interface AgentMetrics {
  tasksCompleted: number;
  successRate: number;
  averageResponseTime: number;
  resourceUsage: number;
}

export interface AgentTask {
  id: string;
  agentId: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
  updatedAt: string;
  result?: any;
}

export interface AgentConfiguration {
  id: string;
  name: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  tools: string[];
  enabled: boolean;
}