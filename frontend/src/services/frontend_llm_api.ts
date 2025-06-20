// reVoAgent Frontend LLM API - Enhanced to work with the new backend LLM integration
// This service connects to the backend_main_enhanced.py endpoints

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  source: string;
  status: string;
  cost_per_token: number;
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
}

export interface AgentRequest {
  agent_type: string;
  message: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface AgentResponse {
  agent: string;
  response: string;
  model: string;
  timestamp: string;
}

export interface MultiAgentResponse {
  responses: {
    agent: string;
    response: string;
    timestamp: string;
    model: string;
  }[];
}

export interface LLMConfig {
  default_model: string;
  available_providers: string[];
  status: {
    status: string;
    providers: number;
    models: string[];
  };
}

// Detect runtime environment and use appropriate URLs
const isRuntimeEnvironment = window.location.hostname.includes('prod-runtime.all-hands.dev');
const API_BASE = import.meta.env.VITE_API_URL || 
  (isRuntimeEnvironment ? 'https://work-2-cikrwnvkyhdgeqtr.prod-runtime.all-hands.dev' : 'http://localhost:12001');
const WS_BASE = import.meta.env.VITE_WS_URL || 
  (isRuntimeEnvironment ? 'wss://work-2-cikrwnvkyhdgeqtr.prod-runtime.all-hands.dev' : 'ws://localhost:12001');

class FrontendLLMApiService {
  private retryAttempts = 3;
  private retryDelay = 1000; // milliseconds

  constructor() {
    if (import.meta.env.DEV) {
      console.log(`🔗 API Base URL: ${API_BASE}`);
      console.log(`🔌 WebSocket URL: ${WS_BASE}`);
    }
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
          },
          ...options,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ error: response.statusText }));
          throw new Error(errorData.detail || errorData.error || response.statusText);
        }

        return await response.json();
      } catch (error) {
        lastError = error as Error;
        
        if (attempt < this.retryAttempts - 1) {
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt)));
        }
      }
    }
    
    throw lastError || new Error(`Failed to fetch from ${endpoint}`);
  }

  // Get available models
  async getAvailableModels(): Promise<{ models: ModelInfo[] }> {
    return this.request<{ models: ModelInfo[] }>('/api/models');
  }

  // Simple chat with LLM
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Chat with specific agent
  async agentChat(request: AgentRequest): Promise<AgentResponse> {
    return this.request<AgentResponse>('/api/agent', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Multi-agent chat
  async multiAgentChat(request: ChatRequest): Promise<MultiAgentResponse> {
    return this.request<MultiAgentResponse>('/api/chat/multi-agent', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get LLM configuration
  async getLLMConfig(): Promise<LLMConfig> {
    return this.request<LLMConfig>('/api/config/llm');
  }

  // Get API health status
  async getHealth(): Promise<{
    status: string;
    timestamp: string;
    version: string;
    uptime: number;
    services: Record<string, string>;
    llm_status: Record<string, any>;
  }> {
    return this.request('/health');
  }
  
  // Create WebSocket connection for streaming chat
  createChatWebSocket(): WebSocket {
    const ws = new WebSocket(`${WS_BASE}/ws/chat`);
    
    if (import.meta.env.DEV) {
      ws.onopen = () => console.log('WebSocket connected');
      ws.onclose = () => console.log('WebSocket disconnected');
      ws.onerror = (error) => console.error('WebSocket error:', error);
    }
    
    return ws;
  }
  
  // Send a message through WebSocket
  sendWebSocketMessage(ws: WebSocket, message: string, model?: string, options?: Partial<ChatRequest>): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        message,
        model: model || 'deepseek-r1',
        temperature: options?.temperature || 0.7,
        max_tokens: options?.max_tokens || 1000
      }));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }
  
  // Simple helper method to stream chat
  async streamChat(
    message: string,
    model: string = 'deepseek-r1',
    onMessage: (content: string) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const ws = this.createChatWebSocket();
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'typing') {
          // Nothing to do for typing indicator
        } else if (data.type === 'response') {
          onComplete({
            response: data.response,
            model: data.model,
            timestamp: data.timestamp,
            tokens_used: data.response?.split(' ')?.length || 0,
            response_time: 0
          });
        } else if (data.type === 'error') {
          onError(new Error(data.error));
        }
      } catch (error) {
        onError(error as Error);
      }
    };
    
    ws.onerror = (event) => {
      onError(new Error('WebSocket error'));
    };
    
    ws.onopen = () => {
      try {
        this.sendWebSocketMessage(ws, message, model);
      } catch (error) {
        onError(error as Error);
      }
    };
    
    ws.onclose = () => {
      // Handle completion if needed
    };
  }
}

// Export singleton instance
export const frontendLLMApi = new FrontendLLMApiService();
export default frontendLLMApi;