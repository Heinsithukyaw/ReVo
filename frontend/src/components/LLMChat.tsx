import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Settings, DollarSign } from 'lucide-react';
import { llmApi, type ChatResponse, type LLMProvider } from '../services/llmApi';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Badge,
  Alert,
  AlertDescription
} from './ui';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  provider?: string;
  cost?: number;
  processing_time?: number;
}

interface LLMChatProps {
  className?: string;
}

const LLMChat: React.FC<LLMChatProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentProvider, setCurrentProvider] = useState<LLMProvider | null>(null);
  const [totalCost, setTotalCost] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCurrentProvider();
    // Add welcome message
    setMessages([{
      id: '1',
      content: 'Hello! I\'m your reVoAgent LLM assistant. I\'m optimized for your 1.1 GHz Quad-Core Intel Core i5 system. How can I help you today?',
      role: 'assistant',
      timestamp: new Date(),
      provider: 'system',
      cost: 0
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadCurrentProvider = async () => {
    try {
      const data = await llmApi.getProviders();
      const current = data.providers.find(p => p.is_current);
      setCurrentProvider(current || null);
    } catch (error) {
      console.error('Failed to load current provider:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response: ChatResponse = await llmApi.sendMessage({
        content: userMessage.content,
        max_tokens: 2048,
        temperature: 0.7
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        provider: response.provider,
        cost: response.cost,
        processing_time: response.processing_time
      };

      setMessages(prev => [...prev, assistantMessage]);
      setTotalCost(prev => prev + response.cost);

    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to send message');
      
      // Add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        role: 'assistant',
        timestamp: new Date(),
        provider: 'error',
        cost: 0
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return 'Free';
    return `$${cost.toFixed(4)}`;
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Bot className="h-5 w-5 mr-2" />
              LLM Chat Interface
            </CardTitle>
            <div className="flex items-center space-x-2">
              {currentProvider && (
                <Badge variant="outline">
                  {currentProvider.name}
                </Badge>
              )}
              <Badge className="bg-green-100 text-green-800">
                <DollarSign className="h-3 w-3 mr-1" />
                Total: {formatCost(totalCost)}
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert className="mb-4 border-red-500">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages */}
      <Card className="flex-1 flex flex-col">
        <CardContent className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.role === 'assistant' && (
                      <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    {message.role === 'user' && (
                      <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Message metadata */}
                      <div className={`mt-2 text-xs ${
                        message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        <div className="flex items-center justify-between">
                          <span>{message.timestamp.toLocaleTimeString()}</span>
                          {message.provider && message.provider !== 'system' && message.provider !== 'error' && (
                            <div className="flex items-center space-x-2">
                              {message.processing_time && (
                                <span>{formatTime(message.processing_time * 1000)}</span>
                              )}
                              {message.cost !== undefined && (
                                <span>{formatCost(message.cost)}</span>
                              )}
                              <span>{message.provider}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4" />
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </CardContent>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex space-x-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              disabled={loading}
              className="flex-1"
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              size="sm"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          
          {/* Quick stats */}
          <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <div className="flex items-center space-x-4">
              {currentProvider && (
                <span>Provider: {currentProvider.name}</span>
              )}
              <span>Messages: {messages.length - 1}</span>
              <span>Total Cost: {formatCost(totalCost)}</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default LLMChat;