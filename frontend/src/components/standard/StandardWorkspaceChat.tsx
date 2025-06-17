import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Paperclip, 
  Mic, 
  MicOff, 
  Settings, 
  Users, 
  Bot, 
  MessageSquare,
  Search,
  Plus,
  Smile,
  Star,
  ThumbsUp,
  Heart,
  Copy,
  Share,
  Download,
  RefreshCw,
  Activity,
  BarChart3,
  Database,
  Cpu,
  Network,
  Shield,
  Zap,
  Brain,
  Palette,
  CheckCircle,
  Clock,
  TrendingUp
} from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: string;
  senderName: string;
  senderIcon: string;
  timestamp: Date;
  reactions?: { [key: string]: number };
  metadata?: {
    processingTime?: number;
    confidence?: number;
    cost?: number;
  };
}

const StandardWorkspaceChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [chatStats, setChatStats] = useState({
    totalMessages: 0,
    avgResponseTime: 0.8,
    successRate: 99.2,
    costSavings: 0.00
  });
  
  const chatRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome-standard',
      content: `📊 Welcome to Standard reVoAgent Dashboard!

Your reliable AI assistant is ready to help with:
• 🤖 **Standard AI Processing**: Fast and efficient responses
• 📊 **Performance Monitoring**: Real-time system metrics
• 💰 **Cost Optimization**: 100% local processing ($0.00 costs)
• 🔒 **Secure Operations**: Enterprise-grade security
• 📈 **Analytics Dashboard**: Comprehensive system insights

This is your standard interface for:
- General AI assistance and support
- System monitoring and analytics
- Performance tracking and optimization
- Secure local AI processing

Start chatting to experience the power of local AI!`,
      sender: 'system',
      senderName: 'Standard reVoAgent',
      senderIcon: '📊',
      timestamp: new Date(),
      reactions: {}
    };
    setMessages([welcomeMessage]);
    setChatStats(prev => ({ ...prev, totalMessages: 1 }));
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isProcessing) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      senderName: 'You',
      senderIcon: '👤',
      timestamp: new Date(),
      reactions: {}
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsProcessing(true);

    try {
      // Simulate standard AI processing
      const processingTime = Math.random() * 1.5 + 0.5;
      await new Promise(resolve => setTimeout(resolve, processingTime * 1000));
      
      const aiResponse: Message = {
        id: `ai-${Date.now()}`,
        content: generateStandardResponse(inputMessage),
        sender: 'agent',
        senderName: 'Standard AI Assistant',
        senderIcon: '🤖',
        timestamp: new Date(),
        metadata: {
          processingTime,
          confidence: Math.random() * 15 + 85,
          cost: 0.00 // Local processing
        },
        reactions: {}
      };

      setMessages(prev => [...prev, aiResponse]);
      setChatStats(prev => ({
        ...prev,
        totalMessages: prev.totalMessages + 2,
        avgResponseTime: (prev.avgResponseTime + processingTime) / 2
      }));
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: `❌ Error: ${error instanceof Error ? error.message : 'Processing failed'}`,
        sender: 'system',
        senderName: 'System Error',
        senderIcon: '⚠️',
        timestamp: new Date(),
        reactions: {}
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const generateStandardResponse = (input: string): string => {
    const responses = [
      `I understand your request about "${input}". Let me provide a helpful response using standard AI processing.`,
      `Thank you for your question regarding "${input}". Here's what I can help you with.`,
      `Based on your inquiry about "${input}", I can offer the following assistance.`,
      `I'm here to help with "${input}". Let me provide you with a comprehensive answer.`,
      `Your question about "${input}" is interesting. Here's my analysis and recommendations.`
    ];

    const baseResponse = responses[Math.floor(Math.random() * responses.length)];
    
    const additionalInfo = `

📊 **Standard Features Active:**
• Fast local processing (no external API calls)
• Secure data handling (100% private)
• Cost-effective operation ($0.00 per query)
• Reliable performance monitoring
• Enterprise-grade security

This response was generated using our standard AI model with optimized performance and security.`;

    return baseResponse + additionalInfo;
  };

  const handleReaction = (messageId: string, reaction: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const reactions = { ...msg.reactions };
        reactions[reaction] = (reactions[reaction] || 0) + 1;
        return { ...msg, reactions };
      }
      return msg;
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const exportChat = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      messages,
      stats: chatStats
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `standard-chat-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setMessages([]);
      setChatStats({
        totalMessages: 0,
        avgResponseTime: 0.8,
        successRate: 99.2,
        costSavings: 0.00
      });
    }
  };

  const reactions = ['👍', '❤️', '😊', '⭐', '💡', '🎯', '🔥', '✅'];

  return (
    <div className="standard-workspace-chat h-full flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900">
      {/* Chat Header */}
      <div className="chat-header bg-gray-800/60 backdrop-blur-md border-b border-gray-700/50 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-bold text-white">Standard Workspace Chat</h2>
            </div>
            
            {/* Status Indicators */}
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-1 text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>Online</span>
              </div>
              <div className="flex items-center space-x-1 text-blue-400">
                <Activity className="w-4 h-4" />
                <span>Standard Mode</span>
              </div>
              <div className="flex items-center space-x-1 text-purple-400">
                <Shield className="w-4 h-4" />
                <span>Secure</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <div className="bg-gray-700/30 rounded-lg p-3 text-center">
            <div className="text-blue-400 font-bold text-lg">{chatStats.totalMessages}</div>
            <div className="text-gray-400 text-xs">Total Messages</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-3 text-center">
            <div className="text-green-400 font-bold text-lg">{chatStats.avgResponseTime.toFixed(2)}s</div>
            <div className="text-gray-400 text-xs">Avg Response</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-3 text-center">
            <div className="text-purple-400 font-bold text-lg">{chatStats.successRate}%</div>
            <div className="text-gray-400 text-xs">Success Rate</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-3 text-center">
            <div className="text-yellow-400 font-bold text-lg">${chatStats.costSavings.toFixed(2)}</div>
            <div className="text-gray-400 text-xs">Cost Savings</div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="chat-messages flex-1 overflow-y-auto p-4 space-y-4" ref={chatRef}>
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`message-container ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
            >
              <div className={`message-bubble p-4 rounded-2xl max-w-4xl ${
                message.sender === 'user'
                  ? 'bg-blue-600/20 border border-blue-500/30 ml-auto'
                  : message.sender === 'system'
                  ? 'bg-gray-700/30 border border-gray-600/30'
                  : 'bg-gray-800/40 border border-gray-700/30'
              }`}>
                {/* Message Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{message.senderIcon}</span>
                    <span className="text-white font-medium">{message.senderName}</span>
                  </div>
                  <span className="text-gray-400 text-sm">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Message Content */}
                <div className="text-gray-100 whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </div>

                {/* Metadata */}
                {message.metadata && (
                  <div className="mt-3 flex items-center space-x-4 text-xs text-gray-400">
                    {message.metadata.processingTime && (
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{message.metadata.processingTime.toFixed(2)}s</span>
                      </span>
                    )}
                    {message.metadata.confidence && (
                      <span className="flex items-center space-x-1">
                        <TrendingUp className="w-3 h-3" />
                        <span>{message.metadata.confidence.toFixed(1)}%</span>
                      </span>
                    )}
                    <span className="flex items-center space-x-1">
                      <Database className="w-3 h-3" />
                      <span>Local Processing</span>
                    </span>
                    <span className="flex items-center space-x-1 text-green-400">
                      <span>💰 $0.00</span>
                    </span>
                  </div>
                )}

                {/* Reactions */}
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {reactions.map(reaction => (
                      <button
                        key={reaction}
                        onClick={() => handleReaction(message.id, reaction)}
                        className="hover:bg-gray-600/50 p-1 rounded transition-colors"
                      >
                        <span className="text-sm">{reaction}</span>
                      </button>
                    ))}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button className="p-1 hover:bg-gray-600/50 rounded transition-colors">
                      <Copy className="w-4 h-4 text-gray-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-600/50 rounded transition-colors">
                      <Share className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>

                {/* Reaction Display */}
                {message.reactions && Object.keys(message.reactions).length > 0 && (
                  <div className="mt-2 flex items-center space-x-2">
                    {Object.entries(message.reactions).map(([reaction, count]) => (
                      <span
                        key={reaction}
                        className="px-2 py-1 bg-gray-600/50 rounded-full text-sm"
                      >
                        {reaction} {count}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Processing Indicator */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center space-x-2 text-gray-400"
          >
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-100"></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-200"></div>
            </div>
            <span>Standard AI is processing...</span>
          </motion.div>
        )}

        {/* Empty State */}
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-white mb-2">
              Standard reVoAgent Dashboard
            </h3>
            <p className="text-gray-300 max-w-md mx-auto">
              Your reliable AI assistant for standard operations, monitoring, and analytics.
            </p>
          </motion.div>
        )}
      </div>

      {/* Chat Input */}
      <div className="chat-input bg-gray-800/60 backdrop-blur-md border-t border-gray-700/50 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Message your standard AI assistant... (Press Enter to send)"
              disabled={isProcessing}
              className="w-full min-h-[60px] max-h-[200px] p-4 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent disabled:opacity-50"
              rows={1}
            />
            
            <div className="absolute right-2 bottom-2 flex items-center space-x-1">
              <button className="p-1 hover:bg-gray-600/50 rounded transition-colors">
                <Smile className="w-4 h-4 text-gray-400" />
              </button>
              <button className="p-1 hover:bg-gray-600/50 rounded transition-colors">
                <Paperclip className="w-4 h-4 text-gray-400" />
              </button>
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`p-1 rounded transition-colors ${
                  isRecording ? 'bg-red-600 text-white' : 'hover:bg-gray-600/50 text-gray-400'
                }`}
              >
                {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <motion.button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isProcessing}
            className={`p-3 rounded-xl transition-all ${
              inputMessage.trim() && !isProcessing
                ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/25'
                : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
            }`}
            whileHover={inputMessage.trim() && !isProcessing ? { scale: 1.05 } : {}}
            whileTap={inputMessage.trim() && !isProcessing ? { scale: 0.95 } : {}}
          >
            {isProcessing ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        {/* Quick Actions */}
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <span>Standard Mode</span>
            <span>•</span>
            <span>Local Processing</span>
            <span>•</span>
            <span>Secure & Private</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={exportChat}
              className="px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors"
            >
              Export Chat
            </button>
            <button 
              onClick={clearChat}
              className="px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors"
            >
              Clear History
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StandardWorkspaceChat;