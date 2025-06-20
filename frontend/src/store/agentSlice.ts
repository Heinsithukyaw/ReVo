import { StateCreator } from 'zustand';
import { Agent, AgentTask, AgentConfiguration } from '../types/agents';

export interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  agentTasks: AgentTask[];
  agentConfigurations: AgentConfiguration[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  setSelectedAgent: (agent: Agent | null) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  removeAgent: (id: string) => void;
  setAgentTasks: (tasks: AgentTask[]) => void;
  addAgentTask: (task: AgentTask) => void;
  updateAgentTask: (id: string, updates: Partial<AgentTask>) => void;
  setAgentConfigurations: (configs: AgentConfiguration[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const createAgentSlice: StateCreator<AgentState> = (set, get) => ({
  agents: [],
  selectedAgent: null,
  agentTasks: [],
  agentConfigurations: [],
  isLoading: false,
  error: null,

  setAgents: (agents) => set({ agents }),
  
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  
  addAgent: (agent) => set((state) => ({
    agents: [...state.agents, agent]
  })),
  
  updateAgent: (id, updates) => set((state) => ({
    agents: state.agents.map(agent => 
      agent.id === id ? { ...agent, ...updates } : agent
    )
  })),
  
  removeAgent: (id) => set((state) => ({
    agents: state.agents.filter(agent => agent.id !== id)
  })),
  
  setAgentTasks: (tasks) => set({ agentTasks: tasks }),
  
  addAgentTask: (task) => set((state) => ({
    agentTasks: [...state.agentTasks, task]
  })),
  
  updateAgentTask: (id, updates) => set((state) => ({
    agentTasks: state.agentTasks.map(task => 
      task.id === id ? { ...task, ...updates } : task
    )
  })),
  
  setAgentConfigurations: (configs) => set({ agentConfigurations: configs }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
});