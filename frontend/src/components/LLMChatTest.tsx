import React, { useState, useEffect } from 'react';
import { useLLMChat, Message } from '../hooks/useLLMChat';
import { frontendLLMApi } from '../services/frontend_llm_api';

const LLMChatTest: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  
  const {
    messages,
    loading,
    error,
    send,
    clearMessages,
    currentModel,
    setCurrentModel,
    temperature,
    setTemperature,
    maxTokens,
    setMaxTokens,
    hasStreamingSupport
  } = useLLMChat();

  // Check backend health and get available models on mount
  useEffect(() => {
    const initialize = async () => {
      try {
        // Check health
        const health = await frontendLLMApi.getHealth();
        setBackendStatus('online');
        
        // Get models
        const modelsData = await frontendLLMApi.getAvailableModels();
        setAvailableModels(modelsData.models || []);
      } catch (err) {
        console.error('Backend connection error:', err);
        setBackendStatus('offline');
      }
    };
    
    initialize();
  }, []);
  
  // Handle send message
  const handleSendMessage = () => {
    if (inputText.trim()) {
      send(inputText);
      setInputText('');
    }
  };
  
  // Handle key press to send message on Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-semibold">reVoAgent LLM Chat Test</h1>
          <div className="flex items-center space-x-2">
            <span>Backend:</span>
            <span className={`inline-block w-3 h-3 rounded-full ${
              backendStatus === 'online' ? 'bg-green-500' : 
              backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></span>
            <span>{backendStatus}</span>
          </div>
        </div>
      </div>
      
      {/* Settings */}
      <div className="bg-gray-800 p-4 border-b border-gray-700">
        <div className="flex flex-wrap gap-4">
          {/* Model Selection */}
          <div className="flex items-center space-x-2">
            <label htmlFor="model">Model:</label>
            <select 
              id="model"
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1"
              value={currentModel}
              onChange={(e) => setCurrentModel(e.target.value)}
            >
              {availableModels.length > 0 ? (
                availableModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))
              ) : (
                <option value="deepseek-r1">DeepSeek R1 (Default)</option>
              )}
            </select>
          </div>
          
          {/* Temperature */}
          <div className="flex items-center space-x-2">
            <label htmlFor="temperature">Temperature:</label>
            <input 
              type="number" 
              id="temperature"
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1 w-20"
              value={temperature}
              min={0.1}
              max={1.0}
              step={0.1}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
          </div>
          
          {/* Max Tokens */}
          <div className="flex items-center space-x-2">
            <label htmlFor="maxTokens">Max Tokens:</label>
            <input 
              type="number" 
              id="maxTokens"
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1 w-24"
              value={maxTokens}
              min={100}
              max={4000}
              step={100}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
            />
          </div>
          
          {/* Streaming Status */}
          <div className="flex items-center space-x-2">
            <span>Streaming:</span>
            <span className={`inline-block w-3 h-3 rounded-full ${
              hasStreamingSupport === true ? 'bg-green-500' : 
              hasStreamingSupport === false ? 'bg-red-500' : 'bg-yellow-500'
            }`}></span>
            <span>{hasStreamingSupport === null ? 'Checking...' : 
                  hasStreamingSupport ? 'Enabled' : 'Disabled'}</span>
          </div>
          
          {/* Clear Button */}
          <button
            className="ml-auto bg-red-600 hover:bg-red-700 px-4 py-1 rounded"
            onClick={clearMessages}
          >
            Clear Chat
          </button>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-10">
            <p>No messages yet. Send a message to start the conversation.</p>
          </div>
        ) : (
          messages.map((message: Message) => (
            <div 
              key={message.id} 
              className={`p-4 rounded-lg max-w-[80%] ${
                message.role === 'user' 
                  ? 'bg-blue-600 ml-auto' 
                  : 'bg-gray-700'
              }`}
            >
              <div className="text-sm text-gray-300 mb-1">
                {message.role === 'user' ? 'User' : 'AI'}
                {message.model && ` (${message.model})`}
              </div>
              
              {message.loading ? (
                <div className="flex space-x-2 items-center">
                  <div className="animate-pulse">Thinking</div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
            </div>
          ))
        )}
        
        {/* Loading indicator */}
        {loading && messages.length > 0 && !messages[messages.length - 1].loading && (
          <div className="flex justify-center my-2">
            <div className="animate-spin h-5 w-5 border-2 border-gray-300 rounded-full border-t-transparent"></div>
          </div>
        )}
        
        {/* Error message */}
        {error && (
          <div className="bg-red-700 text-white p-3 rounded-lg my-2">
            <strong>Error:</strong> {error.message}
          </div>
        )}
      </div>
      
      {/* Input */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex space-x-2">
          <textarea
            className="flex-1 bg-gray-700 border border-gray-600 rounded p-3 text-white focus:outline-none focus:border-blue-500"
            rows={3}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            disabled={loading}
          />
          <button
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded self-end"
            onClick={handleSendMessage}
            disabled={loading || !inputText.trim()}
          >
            Send
          </button>
        </div>
        <div className="text-xs text-gray-400 mt-2">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default LLMChatTest;