// WebSocket Connection Manager
class WebSocketManager {
  private connections: Map<string, WebSocket>;
  private reconnectAttempts: number;
  private heartbeatInterval: NodeJS.Timeout;
  
  // Connection Management
  connect(endpoint: string, callbacks: WebSocketCallbacks): void
  disconnect(endpoint: string): void
  reconnect(endpoint: string): void
  
  // Message Handling
  sendMessage(endpoint: string, message: any): void
  broadcastMessage(message: any): void
  
  // Health Monitoring
  startHeartbeat(): void
  stopHeartbeat(): void
  checkConnectionHealth(): boolean
}

// Real-time Data Streams
interface WebSocketStreams {
  dashboard: {
    systemMetrics: SystemMetrics;
    agentStatus: AgentStatus[];
    taskProgress: TaskProgress[];
    notifications: Notification[];
  };
  
  chat: {
    messages: ChatMessage[];
    typingIndicators: TypingIndicator[];
    agentActivity: AgentActivity[];
  };
}