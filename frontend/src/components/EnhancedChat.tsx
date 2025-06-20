import React, { useState, useEffect, useRef } from 'react';
import { enhancedApiService, ChatMessage, ModelInfo, HealthStatus } from '../services/enhanced_api';

interface ConnectionStatus {
  connected: boolean;
  latency?: number;
  error?: string;
}

const EnhancedChat: React.FC = () => {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('deepseek-r1');
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ connected: false });
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [useWebSocket, setUseWebSocket] = useState(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize connection and load data
  useEffect(() => {
    // Initialize immediately
    initializeApp();
    
    // Set up periodic checking every 15 seconds
    const intervalId = setInterval(() => {
      checkConnection();
    }, 15000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);
  
  // Separate connection check function for periodic health checks
  const checkConnection = async () => {
    try {
      const connStatus = await enhancedApiService.testConnection();
      
      // Only update if status changed to avoid unnecessary re-renders
      if (connStatus.connected !== connectionStatus.connected) {
        setConnectionStatus(connStatus);
        
        if (connStatus.connected && !connectionStatus.connected) {
          console.log('Connection restored, reloading data...');
          await loadData();
        }
      }
    } catch (error) {
      console.error('Connection check failed:', error);
      if (connectionStatus.connected) {
        setConnectionStatus({ 
          connected: false, 
          error: error instanceof Error ? error.message : 'Connection check failed' 
        });
      }
    }
  };

  // Separate function to load data after connection is established
  const loadData = async () => {
    try {
      // Load health status
      const health = await enhancedApiService.getHealth();
      setHealthStatus(health);

      // Load available models with retries
      let retries = 0;
      let models: ModelInfo[] = [];
      
      while (retries < 3 && models.length === 0) {
        try {
          models = await enhancedApiService.getAvailableModels();
          if (models.length === 0) {
            console.log(`No models found, retrying (${retries + 1}/3)...`);
            await new Promise(resolve => setTimeout(resolve, 1000));
            retries++;
          }
        } catch (e) {
          console.error(`Error loading models (attempt ${retries + 1}/3):`, e);
          retries++;
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
      
      setAvailableModels(models);

      // Set default model if available
      if (models.length > 0 && !models.find(m => m.id === selectedModel)) {
        setSelectedModel(models[0].id);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const initializeApp = async () => {
    try {
      // Test connection first
      const connStatus = await enhancedApiService.testConnection();
      setConnectionStatus(connStatus);

      if (connStatus.connected) {
        await loadData();
      } else {
        console.warn('Backend disconnected, cannot load data');
      }
    } catch (error) {
      console.error('Failed to initialize app:', error);
      setConnectionStatus({ 
        connected: false, 
        error: error instanceof Error ? error.message : 'Initialization failed' 
      });
    }
  };

  // WebSocket management
  const setupWebSocket = React.useCallback(async () => {
    if (!useWebSocket) return;

    try {
      const ws = await enhancedApiService.connectWebSocket();
      wsRef.current = ws;

      enhancedApiService.onWebSocketMessage('response', (data) => {
        const newMessage: ChatMessage = {
          id: `ws-${Date.now()}`,
          content: data.response,
          role: 'assistant',
          timestamp: data.timestamp,
          model: data.model,
        };
        setMessages(prev => [...prev, newMessage]);
        setIsLoading(false);
      });

      enhancedApiService.onWebSocketMessage('error', (data) => {
        console.error('WebSocket error:', data.error);
        setIsLoading(false);
      });

      enhancedApiService.onWebSocketMessage('typing', (data) => {
        if (data.status === 'thinking') {
          // Show typing indicator
        }
      });

    } catch (error) {
      console.error('WebSocket setup failed:', error);
      setUseWebSocket(false);
    }
  }, [useWebSocket]);

  useEffect(() => {
    setupWebSocket();
    return () => {
      enhancedApiService.closeWebSocket();
    };
  }, [setupWebSocket]);

  // Send message handler
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      if (useWebSocket && wsRef.current) {
        // Send via WebSocket
        await enhancedApiService.sendWebSocketMessage({
          message: inputMessage,
          model: selectedModel,
          temperature,
          max_tokens: maxTokens,
        });
      } else {
        // Send via HTTP
        const response = await enhancedApiService.sendChatMessage({
          message: inputMessage,
          model: selectedModel,
          temperature,
          max_tokens: maxTokens,
        });
        
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          content: response.response,
          role: 'assistant',
          timestamp: response.timestamp,
          model: response.model,
          tokens_used: response.tokens_used,
          response_time: response.response_time,
        };

        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      if (!useWebSocket) {
        setIsLoading(false);
      }
    }
  };

  // Multi-agent chat handler
  const handleMultiAgentChat = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await enhancedApiService.sendMultiAgentChat({
        message: inputMessage,
        model: selectedModel,
        temperature,
        max_tokens: maxTokens,
      });
      
      // Add each agent response
      response.responses.forEach((agentResponse, index) => {
        const assistantMessage: ChatMessage = {
          id: `agent-${Date.now()}-${index}`,
          content: `**${agentResponse.agent.replace('_', ' ').toUpperCase()}**: ${agentResponse.response}`,
          role: 'assistant',
          timestamp: agentResponse.timestamp,
          model: agentResponse.model,
        };

        setMessages(prev => [...prev, assistantMessage]);
      });
    } catch (error) {
      console.error('Multi-agent chat failed:', error);
      
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        content: `Error: ${error instanceof Error ? error.message : 'Multi-agent chat failed'}`,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear chat
  const handleClearChat = () => {
    setMessages([]);
  };

  // Refresh connection
  const handleRefreshConnection = () => {
    initializeApp();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">reVoAgent Enhanced</h1>
            <p className="text-sm text-gray-400">AI Platform with Real LLM Integration</p>
          </div>
          
          {/* Connection Status */}
          <div className="flex items-center space-x-4">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
              connectionStatus.connected 
                ? 'bg-green-900 text-green-300' 
                : 'bg-red-900 text-red-300'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                connectionStatus.connected ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <span>
                {connectionStatus.connected 
                  ? `Connected ${connectionStatus.latency ? `(${connectionStatus.latency}ms)` : ''}` 
                  : 'Disconnected'
                }
              </span>
            </div>
            
            <button
              onClick={handleRefreshConnection}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
            >
              Refresh
            </button>
            
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm"
            >
              Settings
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-700 rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2"
                >
                  {availableModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name} ({model.provider})
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Temperature: {temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Tokens: {maxTokens}
                </label>
                <input
                  type="range"
                  min="100"
                  max="4000"
                  step="100"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
            
            <div className="mt-4 flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={useWebSocket}
                  onChange={(e) => setUseWebSocket(e.target.checked)}
                  className="rounded"
                />
                <span>Use WebSocket (Streaming)</span>
              </label>
            </div>

            {/* LLM Status Display */}
            {healthStatus?.llm_status && (
              <div className="mt-4 text-sm bg-gray-800 p-3 rounded">
                <h4 className="font-medium text-blue-400 mb-2">LLM Status</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>Status: <span className="text-green-400">{healthStatus.llm_status.status}</span></div>
                  <div>Providers: <span className="text-blue-400">{healthStatus.llm_status.providers}</span></div>
                  <div>Default: <span className="text-yellow-400">{healthStatus.llm_status.default_model}</span></div>
                  <div>Models: <span className="text-purple-400">{healthStatus.llm_status.models?.join(', ')}</span></div>
                </div>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-8">
            <h3 className="text-lg font-medium mb-2">Welcome to reVoAgent Enhanced</h3>
            <p>Real LLM integration with multiple AI providers</p>
            {healthStatus?.llm_status && (
              <div className="mt-4 text-sm">
                <p>Available Models: {healthStatus.llm_status.models?.join(', ')}</p>
                <p>Default Model: {healthStatus.llm_status.default_model}</p>
                <p>Providers Active: {healthStatus.llm_status.providers}</p>
              </div>
            )}
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
              
              {message.role === 'assistant' && (
                <div className="text-xs text-gray-400 mt-2 space-y-1">
                  {message.model && <div>Model: {message.model}</div>}
                  {message.tokens_used && <div>Tokens: {message.tokens_used}</div>}
                  {message.response_time && <div>Time: {message.response_time.toFixed(2)}s</div>}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span>AI is processing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask the AI anything..."
            disabled={!connectionStatus.connected || isLoading}
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          
          <button
            onClick={handleSendMessage}
            disabled={!connectionStatus.connected || isLoading || !inputMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-6 py-2 rounded-lg font-medium"
          >
            Send
          </button>
          
          <button
            onClick={handleMultiAgentChat}
            disabled={!connectionStatus.connected || isLoading || !inputMessage.trim()}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg font-medium"
          >
            Multi-Agent
          </button>
          
          <button
            onClick={handleClearChat}
            className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded-lg font-medium"
          >
            Clear
          </button>
        </div>
        
        {connectionStatus.error && (
          <div className="mt-2 text-red-400 text-sm">
            Error: {connectionStatus.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedChat;