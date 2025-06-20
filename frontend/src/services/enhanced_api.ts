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
    // Use environment variable if available
    if (import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL as string;
    }
    
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
        // Use environment variable for WebSocket URL if available
        let wsURL = '';
        if (import.meta.env.VITE_WS_URL) {
          wsURL = `${import.meta.env.VITE_WS_URL}/ws/chat`;
        } else {
          wsURL = this.baseURL.replace('http', 'ws') + '/ws/chat';
        }
        
        console.log(`Connecting to WebSocket at: ${wsURL}`);
        
        // Close existing connection if any
        if (this.wsConnection) {
          this.wsConnection.close();
          this.wsConnection = null;
        }
        
        this.wsConnection = new WebSocket(wsURL);

        // Set a connection timeout
        const connectionTimeout = setTimeout(() => {
          if (this.wsConnection?.readyState !== WebSocket.OPEN) {
            console.error('WebSocket connection timeout');
            reject(new Error('WebSocket connection timeout'));
            if (this.wsConnection) {
              this.wsConnection.close();
              this.wsConnection = null;
            }
          }
        }, 5000); // 5 second timeout

        this.wsConnection.onopen = () => {
          console.log('WebSocket connected successfully');
          clearTimeout(connectionTimeout);
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

        this.wsConnection.onclose = (event) => {
          console.log(`WebSocket disconnected, code: ${event.code}, reason: ${event.reason}`);
          clearTimeout(connectionTimeout);
          this.wsConnection = null;
        };

        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error);
          clearTimeout(connectionTimeout);
          reject(error);
        };

      } catch (error) {
        console.error('WebSocket initialization error:', error);
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
      // Try multiple endpoints to ensure backend is truly connected
      try {
        // First try health endpoint
        const health = await this.getHealth();
        const latency = Date.now() - startTime;
        
        // Verify LLM status specifically
        if (health.llm_status && health.llm_status.status === 'not_initialized') {
          console.warn('LLM service not fully initialized, but backend is available');
          return { 
            connected: true, 
            latency,
            error: 'LLM service not fully initialized. Some features may be limited.'
          };
        }
        
        return { connected: true, latency };
      } catch (healthError) {
        // If health check fails, try a simpler endpoint
        console.warn('Health check failed, trying fallback endpoint', healthError);
        const response = await fetch(`${this.baseURL}/api/health`);
        if (response.ok) {
          const latency = Date.now() - startTime;
          return { connected: true, latency };
        }
        throw healthError; // Re-throw if both checks fail
      }
    } catch (error) {
      console.error('Connection test failed:', error);
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
  private checkInterval: number = 15000; // 15 seconds (more frequent checks)
  private intervalId: NodeJS.Timeout | null = null;
  private listeners: Set<(status: boolean, details?: any) => void> = new Set();
  private currentStatus: boolean = false;
  private consecutiveFailures: number = 0;
  private maxConsecutiveFailures: number = 3;
  
  constructor() {
    // Check connection immediately on creation
    this.checkConnection();
  }

  async checkConnection() {
    try {
      const result = await enhancedApiService.testConnection();
      const newStatus = result.connected;
      
      // Reset failure count on success
      if (newStatus) {
        this.consecutiveFailures = 0;
      } else {
        this.consecutiveFailures++;
      }
      
      // Only trigger status change if:
      // 1. Status changed from true to false immediately
      // 2. Status changed from false to true immediately
      // 3. For false status, we've had enough consecutive failures
      if (this.currentStatus !== newStatus && 
          (newStatus || this.consecutiveFailures >= this.maxConsecutiveFailures)) {
        this.currentStatus = newStatus;
        this.listeners.forEach(listener => listener(newStatus, result));
      }
      
      return newStatus;
    } catch (error) {
      console.error('Connection check failed:', error);
      this.consecutiveFailures++;
      
      if (this.currentStatus && this.consecutiveFailures >= this.maxConsecutiveFailures) {
        this.currentStatus = false;
        this.listeners.forEach(listener => 
          listener(false, { connected: false, error: 'Connection check failed' }));
      }
      
      return false;
    }
  }

  start() {
    if (this.intervalId) return;

    // Check connection immediately
    this.checkConnection();
    
    this.intervalId = setInterval(() => {
      this.checkConnection();
    }, this.checkInterval);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  addListener(callback: (status: boolean, details?: any) => void) {
    this.listeners.add(callback);
    // Immediately notify with current status
    if (this.listeners.size === 1) {
      this.start();
    }
  }

  removeListener(callback: (status: boolean, details?: any) => void) {
    this.listeners.delete(callback);
    // Stop monitoring if no listeners
    if (this.listeners.size === 0) {
      this.stop();
    }
  }
  
  getCurrentStatus(): boolean {
    return this.currentStatus;
  }
}

export const connectionMonitor = new ConnectionMonitor();

export default enhancedApiService;