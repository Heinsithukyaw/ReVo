// Enhanced LLM API Service for reVoAgent
// Connects to the Enhanced LLM Integration backend (Option B + Option C)

export interface LLMModel {
  id: string;
  name: string;
  type: 'api' | 'local' | 'template';
  enabled: boolean;
  available: boolean;
  current: boolean;
  priority: number;
  cost_per_1k_tokens: number;
  cost_per_request: number;
  max_tokens: number;
  has_api_key: boolean;
  status: string;
}

export interface LLMModelsResponse {
  models: LLMModel[];
  current_model: string;
  total_models: number;
  available_models: number;
  cost_savings: string;
  local_models_active: boolean;
  api_models_active: boolean;
  api_llm_enabled: boolean;
  fallback_enabled: boolean;
}

export interface LLMGenerateRequest {
  prompt: string;
  model_id?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  system_prompt?: string;
}

export interface LLMGenerateResponse {
  success: boolean;
  content: string;
  model: string;
  model_type: string;
  tokens_used: number;
  cost: number;
  response_time: number;
  confidence: number;
  provider: string;
  timestamp: number;
}

export interface ChatRequest {
  content: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  system_prompt?: string;
}

export interface ChatResponse {
  response: string;
  model: string;
  real_ai: boolean;
  cost: number;
  processing_time: number;
  confidence: number;
  timestamp: string;
}

export interface HardwareInfo {
  hardware: {
    cpu_cores: number;
    cpu_frequency_ghz: number;
    ram_gb: number;
    has_gpu: boolean;
    optimization_level: string;
  };
  optimization_status: string;
  recommendations: string[];
}

export interface LLMStatus {
  status: string;
  api_llm_enabled: boolean;
  enhanced_llm_enabled: boolean;
  current_model: string;
  available_models: string[];
  total_models: number;
  fallback_enabled: boolean;
  cost_optimization: boolean;
  performance_monitoring: boolean;
  metrics: {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    total_cost: number;
    total_tokens: number;
    average_response_time: number;
    model_usage: Record<string, number>;
    cost_savings: number;
  };
  model_configs: Record<string, {
    enabled: boolean;
    priority: number;
    cost_per_1k_tokens: number;
    has_api_key: boolean;
  }>;
}

export interface ModelSwitchRequest {
  model_id: string;
}

export interface LLMHealthResponse {
  overall_status: string;
  models: Record<string, {
    status: string;
    response_time?: number;
    last_check?: string;
  }>;
}

// Detect runtime environment and use appropriate URLs
const isRuntimeEnvironment = window.location.hostname.includes('prod-runtime.all-hands.dev');
const API_BASE = import.meta.env.VITE_LLM_API_URL || 
  (isRuntimeEnvironment ? 'https://work-2-tsfupefgvoybdkiz.prod-runtime.all-hands.dev' : 'http://localhost:12001');

class LLMApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
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
      console.error(`LLM API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.request('/health');
  }

  // Get available LLM models (Enhanced LLM Integration)
  async getModels(): Promise<LLMModelsResponse> {
    return this.request('/api/models');
  }

  // Get LLM status and metrics
  async getLLMStatus(): Promise<LLMStatus> {
    return this.request('/api/llm/status');
  }

  // Generate AI response (Enhanced LLM Integration)
  async generateResponse(request: LLMGenerateRequest): Promise<LLMGenerateResponse> {
    return this.request('/api/llm/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Send chat message (legacy endpoint)
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Switch LLM model (Enhanced LLM Integration)
  async switchModel(request: ModelSwitchRequest): Promise<{ success: boolean; message: string; current_model: string }> {
    return this.request('/api/llm/set-model', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Check LLM health
  async getLLMHealth(): Promise<LLMHealthResponse> {
    return this.request('/api/llm/health');
  }

  // Test model connection
  async testModel(modelId: string): Promise<{ success: boolean; message: string; response_time: number }> {
    return this.request(`/api/llm/test/${modelId}`, {
      method: 'POST',
    });
  }

  // Get cost analysis
  async getCostAnalysis(): Promise<{
    current_costs: Record<string, number>;
    projected_monthly: number;
    savings_potential: number;
    recommendations: string[];
  }> {
    return this.request('/api/llm/costs');
  }

  // Stream chat (for real-time responses)
  createChatStream(request: LLMGenerateRequest): EventSource {
    const params = new URLSearchParams({
      prompt: request.prompt,
      ...(request.model_id && { model_id: request.model_id }),
      ...(request.max_tokens && { max_tokens: request.max_tokens.toString() }),
      ...(request.temperature && { temperature: request.temperature.toString() }),
      ...(request.system_prompt && { system_prompt: request.system_prompt }),
    });

    return new EventSource(`${this.baseUrl}/api/llm/stream?${params}`);
  }

  // WebSocket for real-time updates
  createWebSocket(): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/llm';
    return new WebSocket(wsUrl);
  }

  // Convenience methods for common operations
  
  // Quick chat with current model
  async quickChat(message: string): Promise<LLMGenerateResponse> {
    return this.generateResponse({
      prompt: message,
      max_tokens: 500,
      temperature: 0.7
    });
  }

  // Get current model info
  async getCurrentModel(): Promise<LLMModel | null> {
    const models = await this.getModels();
    return models.models.find(m => m.current) || null;
  }

  // Get available models only
  async getAvailableModels(): Promise<LLMModel[]> {
    const models = await this.getModels();
    return models.models.filter(m => m.available);
  }

  // Switch to cheapest available model
  async switchToCheapest(): Promise<{ success: boolean; message: string; current_model: string }> {
    const models = await this.getAvailableModels();
    const cheapest = models.sort((a, b) => a.cost_per_1k_tokens - b.cost_per_1k_tokens)[0];
    
    if (cheapest) {
      return this.switchModel({ model_id: cheapest.id });
    }
    
    throw new Error('No available models found');
  }
}

// Export singleton instance
export const llmApi = new LLMApiService();
export default llmApi;