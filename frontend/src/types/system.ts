export interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkActivity: number;
  timestamp: string;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  lastActivity: string;
  tasksCompleted: number;
  errorCount: number;
}

export interface TaskProgress {
  id: string;
  title: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: string;
  estimatedCompletion?: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export interface EngineStatus {
  name: string;
  status: 'active' | 'inactive' | 'error';
  load: number;
  lastUpdate: string;
  metrics: Record<string, any>;
}