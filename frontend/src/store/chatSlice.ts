import { StateCreator } from 'zustand';
import { ChatMessage, ChatSession, TypingIndicator, AgentActivity } from '../types/chat';

export interface ChatState {
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  typingIndicators: TypingIndicator[];
  agentActivities: AgentActivity[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  removeMessage: (id: string) => void;
  setSessions: (sessions: ChatSession[]) => void;
  setCurrentSession: (session: ChatSession | null) => void;
  addSession: (session: ChatSession) => void;
  updateSession: (id: string, updates: Partial<ChatSession>) => void;
  setTypingIndicators: (indicators: TypingIndicator[]) => void;
  addTypingIndicator: (indicator: TypingIndicator) => void;
  removeTypingIndicator: (userId: string) => void;
  setAgentActivities: (activities: AgentActivity[]) => void;
  updateAgentActivity: (agentId: string, activity: AgentActivity['activity']) => void;
  setConnected: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const createChatSlice: StateCreator<ChatState> = (set, get) => ({
  messages: [],
  sessions: [],
  currentSession: null,
  typingIndicators: [],
  agentActivities: [],
  isConnected: false,
  isLoading: false,
  error: null,

  setMessages: (messages) => set({ messages }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    )
  })),
  
  removeMessage: (id) => set((state) => ({
    messages: state.messages.filter(msg => msg.id !== id)
  })),
  
  setSessions: (sessions) => set({ sessions }),
  
  setCurrentSession: (session) => set({ currentSession: session }),
  
  addSession: (session) => set((state) => ({
    sessions: [...state.sessions, session]
  })),
  
  updateSession: (id, updates) => set((state) => ({
    sessions: state.sessions.map(session => 
      session.id === id ? { ...session, ...updates } : session
    )
  })),
  
  setTypingIndicators: (indicators) => set({ typingIndicators: indicators }),
  
  addTypingIndicator: (indicator) => set((state) => ({
    typingIndicators: [...state.typingIndicators.filter(i => i.userId !== indicator.userId), indicator]
  })),
  
  removeTypingIndicator: (userId) => set((state) => ({
    typingIndicators: state.typingIndicators.filter(i => i.userId !== userId)
  })),
  
  setAgentActivities: (activities) => set({ agentActivities: activities }),
  
  updateAgentActivity: (agentId, activity) => set((state) => ({
    agentActivities: [
      ...state.agentActivities.filter(a => a.agentId !== agentId),
      { agentId, activity, timestamp: new Date().toISOString() }
    ]
  })),
  
  setConnected: (connected) => set({ isConnected: connected }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
});