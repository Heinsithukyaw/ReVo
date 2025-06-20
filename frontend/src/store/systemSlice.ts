import { StateCreator } from 'zustand';
import { SystemMetrics, AgentStatus, TaskProgress, Notification, EngineStatus } from '../types/system';

export interface SystemState {
  systemMetrics: SystemMetrics | null;
  agentStatuses: AgentStatus[];
  taskProgress: TaskProgress[];
  notifications: Notification[];
  engineStatuses: EngineStatus[];
  isHealthy: boolean;
  uptime: number;
  lastUpdate: string | null;
  
  // Actions
  setSystemMetrics: (metrics: SystemMetrics) => void;
  setAgentStatuses: (statuses: AgentStatus[]) => void;
  updateAgentStatus: (id: string, status: Partial<AgentStatus>) => void;
  setTaskProgress: (tasks: TaskProgress[]) => void;
  updateTaskProgress: (id: string, progress: Partial<TaskProgress>) => void;
  setNotifications: (notifications: Notification[]) => void;
  addNotification: (notification: Notification) => void;
  markNotificationRead: (id: string) => void;
  removeNotification: (id: string) => void;
  setEngineStatuses: (statuses: EngineStatus[]) => void;
  updateEngineStatus: (name: string, status: Partial<EngineStatus>) => void;
  setHealthy: (healthy: boolean) => void;
  setUptime: (uptime: number) => void;
  setLastUpdate: (timestamp: string) => void;
}

export const createSystemSlice: StateCreator<SystemState> = (set, get) => ({
  systemMetrics: null,
  agentStatuses: [],
  taskProgress: [],
  notifications: [],
  engineStatuses: [],
  isHealthy: true,
  uptime: 0,
  lastUpdate: null,

  setSystemMetrics: (metrics) => set({ 
    systemMetrics: metrics,
    lastUpdate: new Date().toISOString()
  }),
  
  setAgentStatuses: (statuses) => set({ agentStatuses: statuses }),
  
  updateAgentStatus: (id, status) => set((state) => ({
    agentStatuses: state.agentStatuses.map(agent => 
      agent.id === id ? { ...agent, ...status } : agent
    )
  })),
  
  setTaskProgress: (tasks) => set({ taskProgress: tasks }),
  
  updateTaskProgress: (id, progress) => set((state) => ({
    taskProgress: state.taskProgress.map(task => 
      task.id === id ? { ...task, ...progress } : task
    )
  })),
  
  setNotifications: (notifications) => set({ notifications }),
  
  addNotification: (notification) => set((state) => ({
    notifications: [notification, ...state.notifications]
  })),
  
  markNotificationRead: (id) => set((state) => ({
    notifications: state.notifications.map(notif => 
      notif.id === id ? { ...notif, read: true } : notif
    )
  })),
  
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(notif => notif.id !== id)
  })),
  
  setEngineStatuses: (statuses) => set({ engineStatuses: statuses }),
  
  updateEngineStatus: (name, status) => set((state) => ({
    engineStatuses: state.engineStatuses.map(engine => 
      engine.name === name ? { ...engine, ...status } : engine
    )
  })),
  
  setHealthy: (healthy) => set({ isHealthy: healthy }),
  
  setUptime: (uptime) => set({ uptime }),
  
  setLastUpdate: (timestamp) => set({ lastUpdate: timestamp }),
});