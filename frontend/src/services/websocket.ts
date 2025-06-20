import { SystemMetrics, AgentStatus, TaskProgress, Notification } from '../types/system';
import { ChatMessage, TypingIndicator, AgentActivity } from '../types/chat';

export interface WebSocketCallbacks {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (data: any) => void;
}

export interface WebSocketStreams {
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

class WebSocketManager {
  private connections: Map<string, WebSocket> = new Map();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private heartbeatInterval?: NodeJS.Timeout;
  private baseUrl: string;

  constructor(baseUrl: string = 'ws://localhost:12001') {
    this.baseUrl = baseUrl;
  }

  connect(endpoint: string, callbacks: WebSocketCallbacks): void {
    const url = `${this.baseUrl}${endpoint}`;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log(`WebSocket connected to ${endpoint}`);
      this.reconnectAttempts = 0;
      callbacks.onOpen?.();
      this.startHeartbeat();
    };

    ws.onclose = () => {
      console.log(`WebSocket disconnected from ${endpoint}`);
      callbacks.onClose?.();
      this.connections.delete(endpoint);
      this.reconnect(endpoint, callbacks);
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${endpoint}:`, error);
      callbacks.onError?.(error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callbacks.onMessage?.(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.connections.set(endpoint, ws);
  }

  disconnect(endpoint: string): void {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close();
      this.connections.delete(endpoint);
    }
  }

  private reconnect(endpoint: string, callbacks: WebSocketCallbacks): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      setTimeout(() => {
        console.log(`Attempting to reconnect to ${endpoint} (attempt ${this.reconnectAttempts})`);
        this.connect(endpoint, callbacks);
      }, delay);
    }
  }

  sendMessage(endpoint: string, message: any): void {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    } else {
      console.warn(`Cannot send message: WebSocket for ${endpoint} is not connected`);
    }
  }

  broadcastMessage(message: any): void {
    this.connections.forEach((ws, endpoint) => {
      this.sendMessage(endpoint, message);
    });
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.connections.forEach((ws, endpoint) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      });
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }

  checkConnectionHealth(): boolean {
    let allHealthy = true;
    this.connections.forEach((ws) => {
      if (ws.readyState !== WebSocket.OPEN) {
        allHealthy = false;
      }
    });
    return allHealthy;
  }

  disconnectAll(): void {
    this.stopHeartbeat();
    this.connections.forEach((ws, endpoint) => {
      this.disconnect(endpoint);
    });
  }
}

export const webSocketManager = new WebSocketManager();