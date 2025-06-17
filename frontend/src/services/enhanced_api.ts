// Enhanced Frontend API Service - Properly integrates with the enhanced backend LLM endpoints

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  model?: string;
  tokens_used?: number;
  response_time?: number;
}

export interface ChatRequest {
  message: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatResponse {
  response: string;
  model: string;
  timestamp: string;
  tokens_used: number;
  response_time: number;
  provider: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  status: string;
  cost_per_token: number;
  max_tokens: number;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  services: Record<string, string>;
  llm_status: {
    status: string;
    providers: number;
    models: string[];
    default_model: string;
  };
}

export interface AgentResponse {
  agent: string;
  response: string;
  timestamp: string;
  model: string;
}

class EnhancedAPIService {
  private baseURL: string;
  private wsConnection: WebSocket | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();

  constructor() {
    // Auto-detect backend URL based on environment
    this.baseURL = this.detectBackendURL();
    console.log(`Enhanced API Service initialized with backend: ${this.baseURL}`);
  }

  private detectBackendURL(): string {
    // Development detection
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:12001';
    }
    
    // Production detection - same host, different port
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:12001`;
  }

  // Health and Status Methods
  async getHealth(): Promise<HealthStatus> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Backend service unavailable');
    }
  }

  async checkConnection(): Promise<boolean> {
    try {
      const health = await this.getHealth();
      return health.status === 'healthy';
    } catch {
      return false;
    }
  }

  // Model Management
  async getAvailableModels(): Promise<ModelInfo[]> {
    try {
      const response = await fetch(`${this.baseURL}/api/models`);
      if (!response.ok) {
        throw new Error(`Failed to get models: ${response.status}`);
      }
      const data = await response.json();
      return data.models || [];
    } catch (error) {
      console.error('Failed to get models:', error);
      return [];
    }
  }

  // Chat Methods
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseURL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `Chat request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat request failed:', error);
      throw error;
    }
  }

  async sendMultiAgentChat(request: ChatRequest): Promise<{ responses: AgentResponse[] }> {
    try {
      const response = await fetch(`${this.baseURL}/api/chat/multi-agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `Multi-agent chat failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Multi-agent chat failed:', error);
      throw error;
    }
  }

  // WebSocket Chat for Streaming
  connectWebSocket(): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      try {
        const wsURL = this.baseURL.replace('http', 'ws') + '/ws/chat';
        this.wsConnection = new WebSocket(wsURL);

        this.wsConnection.onopen = () => {
          console.log('WebSocket connected');
          resolve(this.wsConnection!);
        };

        this.wsConnection.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.wsConnection.onclose = () => {
          console.log('WebSocket disconnected');
          this.wsConnection = null;
        };

        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleWebSocketMessage(data: any) {
    const handler = this.messageHandlers.get(data.type);
    if (handler) {
      handler(data);
    }
  }

  onWebSocketMessage(type: string, handler: (data: any) => void) {
    this.messageHandlers.set(type, handler);
  }

  async sendWebSocketMessage(message: any): Promise<void> {
    if (!this.wsConnection || this.wsConnection.readyState !== WebSocket.OPEN) {
      await this.connectWebSocket();
    }

    if (this.wsConnection) {
      this.wsConnection.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket connection failed');
    }
  }

  closeWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // Configuration Methods
  async getLLMConfig(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/config/llm`);
      if (!response.ok) {
        throw new Error(`Failed to get LLM config: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get LLM config:', error);
      throw error;
    }
  }

  async updateLLMConfig(config: any): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/config/llm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to update LLM config: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update LLM config:', error);
      throw error;
    }
  }

  // Utility Methods
  async testConnection(): Promise<{ connected: boolean; latency?: number; error?: string }> {
    const startTime = Date.now();
    try {
      await this.getHealth();
      const latency = Date.now() - startTime;
      return { connected: true, latency };
    } catch (error) {
      return { 
        connected: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  // Error handling utility
  private handleAPIError(error: any, context: string): never {
    const message = error?.message || error?.error || 'Unknown error occurred';
    console.error(`API Error in ${context}:`, error);
    throw new Error(`${context}: ${message}`);
  }
}

// Create singleton instance
export const enhancedApiService = new EnhancedAPIService();

// React hooks for common operations
export const useEnhancedAPI = () => {
  return {
    enhancedApiService,
    
    // Health check hook
    useHealthCheck: async () => {
      try {
        return await enhancedApiService.getHealth();
      } catch (error) {
        console.error('Health check failed:', error);
        return null;
      }
    },

    // Models hook
    useModels: async () => {
      try {
        return await enhancedApiService.getAvailableModels();
      } catch (error) {
        console.error('Failed to get models:', error);
        return [];
      }
    },

    // Chat hook
    useChat: () => ({
      sendMessage: enhancedApiService.sendChatMessage.bind(enhancedApiService),
      sendMultiAgentMessage: enhancedApiService.sendMultiAgentChat.bind(enhancedApiService),
      connectWebSocket: enhancedApiService.connectWebSocket.bind(enhancedApiService),
      sendWebSocketMessage: enhancedApiService.sendWebSocketMessage.bind(enhancedApiService),
      onWebSocketMessage: enhancedApiService.onWebSocketMessage.bind(enhancedApiService),
      closeWebSocket: enhancedApiService.closeWebSocket.bind(enhancedApiService),
    }),
  };
};

// Utility functions
export const formatChatMessage = (response: ChatResponse, userMessage: string): ChatMessage[] => {
  return [
    {
      id: `user-${Date.now()}`,
      content: userMessage,
      role: 'user',
      timestamp: new Date().toISOString(),
    },
    {
      id: `assistant-${Date.now()}`,
      content: response.response,
      role: 'assistant',
      timestamp: response.timestamp,
      model: response.model,
      tokens_used: response.tokens_used,
      response_time: response.response_time,
    },
  ];
};

export const validateChatRequest = (request: ChatRequest): string[] => {
  const errors: string[] = [];
  
  if (!request.message || request.message.trim().length === 0) {
    errors.push('Message cannot be empty');
  }
  
  if (request.message && request.message.length > 4000) {
    errors.push('Message too long (max 4000 characters)');
  }
  
  if (request.temperature !== undefined && (request.temperature < 0 || request.temperature > 2)) {
    errors.push('Temperature must be between 0 and 2');
  }
  
  if (request.max_tokens !== undefined && (request.max_tokens < 1 || request.max_tokens > 4096)) {
    errors.push('Max tokens must be between 1 and 4096');
  }
  
  return errors;
};

// Connection status monitoring
export class ConnectionMonitor {
  private checkInterval: number = 30000; // 30 seconds
  private intervalId: NodeJS.Timeout | null = null;
  private listeners: Set<(status: boolean) => void> = new Set();

  start() {
    if (this.intervalId) return;

    this.intervalId = setInterval(async () => {
      const connected = await enhancedApiService.checkConnection();
      this.listeners.forEach(listener => listener(connected));
    }, this.checkInterval);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  addListener(callback: (status: boolean) => void) {
    this.listeners.add(callback);
  }

  removeListener(callback: (status: boolean) => void) {
    this.listeners.delete(callback);
  }
}

export const connectionMonitor = new ConnectionMonitor();

export default enhancedApiService;