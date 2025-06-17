import React, { useState, useEffect } from 'react';
import { Brain, MessageSquare, Settings, Send, Bot, User, Loader2, CheckCircle, AlertCircle, DollarSign } from 'lucide-react';

// API service
const API_BASE = 'http://localhost:12001';

interface Model {
  id: string;
  name: string;
  type: string;
  available: boolean;
  current: boolean;
  cost_per_1k_tokens: number;
}

interface LLMStatus {
  api_llm_enabled: boolean;
  current_model: string;
  metrics: {
    total_requests: number;
    total_cost: number;
    total_tokens: number;
  };
}

interface ChatResponse {
  content: string;
  cost: number;
  model: string;
  tokens: number;
}

const apiCall = async (endpoint: string, options: any = {}) => {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
    {children}
  </div>
);

const CardHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="px-6 py-4 border-b border-gray-200">{children}</div>
);

const CardTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <h3 className="text-lg font-semibold text-gray-900">{children}</h3>
);

const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 ${className}`}>{children}</div>
);

const Button: React.FC<{ 
  children: React.ReactNode; 
  onClick: () => void; 
  disabled?: boolean; 
  className?: string 
}> = ({ children, onClick, disabled = false, className = '' }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none bg-blue-600 text-white hover:bg-blue-700 ${className}`}
  >
    {children}
  </button>
);

const Badge: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 ${className}`}>
    {children}
  </span>
);

export const EnhancedLLMDashboard: React.FC = () => {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [message, setMessage] = useState('Tell me about artificial intelligence in 2 sentences.');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastCost, setLastCost] = useState(0);

  useEffect(() => {
    checkHealth();
    loadModels();
    loadLLMStatus();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await apiCall('/health');
      setStatus(health.status === 'healthy' ? 'online' : 'offline');
    } catch (error) {
      setStatus('offline');
    }
  };

  const loadModels = async () => {
    try {
      const data = await apiCall('/api/models');
      setModels(data.models || []);
      setCurrentModel(data.current_model);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const loadLLMStatus = async () => {
    try {
      const data = await apiCall('/api/llm/status');
      setLlmStatus(data);
    } catch (error) {
      console.error('Failed to load LLM status:', error);
    }
  };

  const sendMessage = async () => {
    if (!message.trim() || loading) return;
    
    setLoading(true);
    try {
      const result: ChatResponse = await apiCall('/api/llm/generate', {
        method: 'POST',
        body: JSON.stringify({ 
          prompt: message,
          max_tokens: 500,
          temperature: 0.7
        })
      });
      setResponse(result.content);
      setLastCost(result.cost);
      // Refresh status after generation
      loadLLMStatus();
    } catch (error: any) {
      setResponse('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const switchModel = async (modelId: string) => {
    try {
      await apiCall('/api/llm/set-model', {
        method: 'POST',
        body: JSON.stringify({ model_id: modelId })
      });
      loadModels();
      loadLLMStatus();
    } catch (error) {
      console.error('Failed to switch model:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center mb-2">
            <Brain className="h-8 w-8 mr-3 text-blue-600" />
            Enhanced LLM Integration (Option B + C)
          </h1>
          <div className="flex items-center space-x-4 flex-wrap">
            <Badge className={status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
              {status === 'online' ? (
                <>
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Backend Online
                </>
              ) : (
                <>
                  <AlertCircle className="h-3 w-3 mr-1" />
                  Backend Offline
                </>
              )}
            </Badge>
            {currentModel && (
              <Badge>Current: {currentModel}</Badge>
            )}
            {llmStatus && (
              <>
                <Badge className="bg-purple-100 text-purple-800">
                  API Models: {llmStatus.api_llm_enabled ? 'Active' : 'Inactive'}
                </Badge>
                <Badge className="bg-orange-100 text-orange-800">
                  Total Cost: ${llmStatus.metrics?.total_cost?.toFixed(4) || '0.0000'}
                </Badge>
                <Badge className="bg-green-100 text-green-800">
                  Requests: {llmStatus.metrics?.total_requests || 0}
                </Badge>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Models */}
          <Card>
            <CardHeader>
              <CardTitle>Available Models</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {models.map((model) => (
                  <div key={model.id} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <span className="font-medium">{model.name}</span>
                      <div className="text-sm text-gray-500">
                        ${model.cost_per_1k_tokens?.toFixed(4) || '0.0000'}/1k tokens
                        <span className="ml-2 text-xs">
                          ({model.type})
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={model.available ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                        {model.available ? 'Available' : 'Unavailable'}
                      </Badge>
                      {model.current && (
                        <Badge className="bg-blue-100 text-blue-800">Current</Badge>
                      )}
                      {model.available && !model.current && (
                        <Button 
                          onClick={() => switchModel(model.id)}
                          className="text-xs px-2 py-1 h-auto"
                        >
                          Switch
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Chat Test */}
          <Card>
            <CardHeader>
              <CardTitle>AI Chat Test</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Test Message
                  </label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Enter a test message..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                  />
                </div>
                
                <Button 
                  onClick={sendMessage} 
                  disabled={!message.trim() || loading}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Send Message
                    </>
                  )}
                </Button>

                {response && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Response
                      </label>
                      {lastCost > 0 && (
                        <Badge className="bg-green-100 text-green-800">
                          <DollarSign className="h-3 w-3 mr-1" />
                          ${lastCost.toFixed(4)}
                        </Badge>
                      )}
                    </div>
                    <div className="p-3 bg-gray-50 border rounded-md">
                      <pre className="whitespace-pre-wrap text-sm">{response}</pre>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Metrics Dashboard */}
        {llmStatus && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>LLM Metrics Dashboard</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {llmStatus.metrics?.total_requests || 0}
                  </div>
                  <div className="text-sm text-gray-500">Total Requests</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    ${llmStatus.metrics?.total_cost?.toFixed(4) || '0.0000'}
                  </div>
                  <div className="text-sm text-gray-500">Total Cost</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {llmStatus.metrics?.total_tokens || 0}
                  </div>
                  <div className="text-sm text-gray-500">Total Tokens</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default EnhancedLLMDashboard;