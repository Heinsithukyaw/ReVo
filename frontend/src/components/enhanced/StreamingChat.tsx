import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, RefreshCw, Zap, Brain, Cpu } from 'lucide-react';

interface StreamChunk {
  type: string;
  content?: string;
  delay?: number;
  progress?: number;
  word_index?: number;
  total_words?: number;
  is_complete?: boolean;
  timestamp?: string;
}

interface StreamingMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  isStreaming?: boolean;
  isComplete?: boolean;
  model?: string;
}

const StreamingChat: React.FC = () => {
  const [messages, setMessages] = useState<StreamingMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [streamingProgress, setStreamingProgress] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentStreamingMessageRef = useRef<string>('');

  // WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const connectWebSocket = () => {
    const isRuntimeEnvironment = window.location.hostname.includes('prod-runtime.all-hands.dev');
    const wsUrl = isRuntimeEnvironment 
      ? 'wss://work-2-nxqxmqxtoartswbx.prod-runtime.all-hands.dev/ws/chat/stream'
      : 'ws://localhost:12001/ws/chat/stream';

    setConnectionStatus('connecting');
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('🔌 Streaming WebSocket connected');
      setConnectionStatus('connected');
    };

    wsRef.current.onmessage = (event) => {
      const data: StreamChunk = JSON.parse(event.data);
      handleStreamChunk(data);
    };

    wsRef.current.onclose = () => {
      console.log('🔌 Streaming WebSocket disconnected');
      setConnectionStatus('disconnected');
      setIsStreaming(false);
    };

    wsRef.current.onerror = (error) => {
      console.error('🔌 Streaming WebSocket error:', error);
      setConnectionStatus('disconnected');
      setIsStreaming(false);
    };
  };

  const handleStreamChunk = (chunk: StreamChunk) => {
    switch (chunk.type) {
      case 'stream_start':
        // Start new streaming message
        const newMessageId = `ai-${Date.now()}`;
        currentStreamingMessageRef.current = newMessageId;
        
        setMessages(prev => [...prev, {
          id: newMessageId,
          content: '',
          sender: 'ai',
          timestamp: new Date(),
          isStreaming: true,
          isComplete: false,
          model: chunk.model || 'revoagent-enhanced-ai-stream'
        }]);
        setStreamingProgress(0);
        break;

      case 'stream_chunk':
        // Add word to current streaming message
        if (chunk.content && currentStreamingMessageRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.id === currentStreamingMessageRef.current
              ? { ...msg, content: msg.content + chunk.content }
              : msg
          ));
          
          if (chunk.progress) {
            setStreamingProgress(chunk.progress * 100);
          }
        }
        break;

      case 'stream_complete':
        // Mark streaming as complete
        if (currentStreamingMessageRef.current) {
          setMessages(prev => prev.map(msg => 
            msg.id === currentStreamingMessageRef.current
              ? { ...msg, isStreaming: false, isComplete: true }
              : msg
          ));
        }
        setIsStreaming(false);
        setStreamingProgress(100);
        currentStreamingMessageRef.current = '';
        break;

      case 'stream_error':
        console.error('Streaming error:', chunk.error);
        setIsStreaming(false);
        setStreamingProgress(0);
        break;
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isStreaming || connectionStatus !== 'connected') return;

    // Add user message
    const userMessage: StreamingMessage = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsStreaming(true);

    // Send to WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: inputMessage,
        session_id: `stream_${Date.now()}`
      }));
    }

    setInputMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400';
      case 'connecting': return 'text-yellow-400';
      default: return 'text-red-400';
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <Zap className="w-4 h-4" />;
      case 'connecting': return <RefreshCw className="w-4 h-4 animate-spin" />;
      default: return <Brain className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-bold">Real-Time AI Streaming</h2>
          </div>
          <div className="text-sm text-gray-400">
            DeepSeek R1 Enhanced
          </div>
        </div>
        
        <div className={`flex items-center space-x-2 ${getConnectionStatusColor()}`}>
          {getConnectionStatusIcon()}
          <span className="text-sm font-medium capitalize">{connectionStatus}</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-3xl p-4 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100 border border-gray-700'
              }`}>
                {message.sender === 'ai' && (
                  <div className="flex items-center space-x-2 mb-2 text-sm text-gray-400">
                    <Brain className="w-4 h-4" />
                    <span>{message.model || 'AI Assistant'}</span>
                    {message.isStreaming && (
                      <div className="flex items-center space-x-2">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>Streaming... {Math.round(streamingProgress)}%</span>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="prose prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {message.content}
                    {message.isStreaming && (
                      <motion.span
                        animate={{ opacity: [1, 0] }}
                        transition={{ duration: 0.8, repeat: Infinity }}
                        className="inline-block w-2 h-5 bg-blue-400 ml-1"
                      />
                    )}
                  </pre>
                </div>

                {message.isStreaming && (
                  <div className="mt-2">
                    <div className="w-full bg-gray-700 rounded-full h-1">
                      <motion.div
                        className="bg-blue-400 h-1 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${streamingProgress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message for real-time AI streaming..."
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
              disabled={isStreaming || connectionStatus !== 'connected'}
            />
          </div>
          
          <motion.button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isStreaming || connectionStatus !== 'connected'}
            className={`p-3 rounded-lg transition-all ${
              inputMessage.trim() && !isStreaming && connectionStatus === 'connected'
                ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/25'
                : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
            }`}
            whileHover={inputMessage.trim() && !isStreaming && connectionStatus === 'connected' ? { scale: 1.05 } : {}}
            whileTap={inputMessage.trim() && !isStreaming && connectionStatus === 'connected' ? { scale: 0.95 } : {}}
          >
            {isStreaming ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
          <div>
            Real-time streaming • $0.00 per message • Enhanced AI
          </div>
          <div>
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamingChat;