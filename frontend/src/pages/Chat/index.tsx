import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, Paperclip, Mic, Image, Code, Users, Settings, 
  MessageSquare, Phone, Video, Share, Download, Copy,
  Bot, User, Brain, Zap, Sparkles, Clock, CheckCircle
} from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import { useAgents } from '../../hooks/useAgents';

const Chat: React.FC = () => {
  const { messages, sendMessage, sendToAgent, isConnected, typingIndicators } = useChat();
  const { agents } = useAgents();
  const [newMessage, setNewMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mock messages for demonstration
  const mockMessages = [
    {
      id: '1',
      role: 'system' as const,
      content: 'Welcome to the reVoAgent Chat Hub! All agents are online and ready to assist.',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      agentName: 'System'
    },
    {
      id: '2',
      role: 'user' as const,
      content: 'Can you help me optimize the React components in our dashboard?',
      timestamp: new Date(Date.now() - 240000).toISOString()
    },
    {
      id: '3',
      role: 'assistant' as const,
      content: 'I\'ll analyze your React components and suggest optimizations. Let me examine the component structure and identify performance bottlenecks.',
      timestamp: new Date(Date.now() - 200000).toISOString(),
      agentId: 'frontend-dev',
      agentName: 'Frontend Developer'
    },
    {
      id: '4',
      role: 'assistant' as const,
      content: 'I\'ve identified several optimization opportunities:\n\n1. Memoize expensive calculations with useMemo\n2. Use React.memo for pure components\n3. Implement virtual scrolling for large lists\n4. Optimize re-renders with useCallback',
      timestamp: new Date(Date.now() - 180000).toISOString(),
      agentId: 'frontend-dev',
      agentName: 'Frontend Developer'
    }
  ];

  const currentMessages = messages.length > 0 ? messages : mockMessages;

  // Active agents for sidebar
  const activeAgents = [
    { id: 'frontend-dev', name: 'Frontend Developer', status: 'active', avatar: '💻' },
    { id: 'backend-eng', name: 'Backend Engineer', status: 'active', avatar: '⚙️' },
    { id: 'devops', name: 'DevOps Specialist', status: 'busy', avatar: '🚀' },
    { id: 'memory-manager', name: 'Memory Manager', status: 'active', avatar: '🧠' },
    { id: 'creative-agent', name: 'Creative Agent', status: 'active', avatar: '✨' }
  ];

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const messageContent = newMessage.trim();
    setNewMessage('');

    try {
      if (selectedAgent) {
        await sendToAgent(messageContent, selectedAgent);
      } else {
        await sendMessage(messageContent);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getAgentIcon = (agentName?: string) => {
    if (!agentName) return <User className="w-5 h-5" />;
    
    const iconMap: Record<string, React.ReactNode> = {
      'Frontend Developer': <Code className="w-5 h-5 text-blue-400" />,
      'Backend Engineer': <Brain className="w-5 h-5 text-green-400" />,
      'DevOps Specialist': <Zap className="w-5 h-5 text-purple-400" />,
      'Memory Manager': <Brain className="w-5 h-5 text-orange-400" />,
      'Creative Agent': <Sparkles className="w-5 h-5 text-pink-400" />,
      'System': <Bot className="w-5 h-5 text-gray-400" />
    };
    
    return iconMap[agentName] || <Bot className="w-5 h-5 text-blue-400" />;
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages]);

  return (
    <div className="flex h-[calc(100vh-12rem)]">
      {/* Main Chat Interface (75%) */}
      <div className="flex-1 flex flex-col glass-panel mr-6">
        {/* Chat Header */}
        <div className="flex justify-between items-center p-4 border-b border-white/10">
          <div className="flex items-center space-x-3">
            <div className="flex -space-x-2">
              {activeAgents.slice(0, 3).map((agent, index) => (
                <div
                  key={agent.id}
                  className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-sm"
                  style={{ zIndex: 10 - index }}
                >
                  {agent.avatar}
                </div>
              ))}
            </div>
            <div>
              <h2 className="text-white font-medium">Multi-Agent Collaboration</h2>
              <p className="text-sm text-gray-400">
                {activeAgents.filter(a => a.status === 'active').length} agents active
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
              isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-xs">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            
            <button className="glass-button p-2">
              <Phone className="w-4 h-4" />
            </button>
            <button className="glass-button p-2">
              <Video className="w-4 h-4" />
            </button>
            <button className="glass-button p-2">
              <Share className="w-4 h-4" />
            </button>
            <button className="glass-button p-2">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {currentMessages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-start space-x-3 ${
                  message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}
              >
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-blue-500' 
                    : message.role === 'system'
                    ? 'bg-gray-600'
                    : 'bg-gradient-to-r from-purple-500 to-pink-500'
                }`}>
                  {message.role === 'user' ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    getAgentIcon(message.agentName)
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 max-w-3xl ${
                  message.role === 'user' ? 'text-right' : ''
                }`}>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm font-medium text-white">
                      {message.role === 'user' ? 'You' : message.agentName || 'Agent'}
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(message.timestamp)}
                    </span>
                    {message.role === 'assistant' && (
                      <CheckCircle className="w-3 h-3 text-green-400" />
                    )}
                  </div>
                  
                  <div className={`rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500/20 text-white ml-8'
                      : message.role === 'system'
                      ? 'bg-gray-500/20 text-gray-300 mr-8'
                      : 'bg-white/10 text-white mr-8'
                  }`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {/* Message Actions */}
                    <div className="flex items-center space-x-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="text-xs text-gray-400 hover:text-white">
                        <Copy className="w-3 h-3" />
                      </button>
                      <button className="text-xs text-gray-400 hover:text-white">
                        <Download className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing Indicators */}
          {typingIndicators.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center space-x-2 text-gray-400"
            >
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-sm">Agent is typing...</span>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-white/10">
          {/* Agent Selector */}
          {showAgentSelector && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-3"
            >
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => { setSelectedAgent(''); setShowAgentSelector(false); }}
                  className={`glass-button text-xs ${!selectedAgent ? 'bg-white/20' : ''}`}
                >
                  All Agents
                </button>
                {activeAgents.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => { setSelectedAgent(agent.id); setShowAgentSelector(false); }}
                    className={`glass-button text-xs ${selectedAgent === agent.id ? 'bg-white/20' : ''}`}
                  >
                    {agent.avatar} {agent.name}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          <div className="flex items-end space-x-3">
            {/* Attachment Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="glass-button p-2 flex-shrink-0"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            {/* Message Input */}
            <div className="flex-1 relative">
              <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message... (Press Shift+Enter for new line)"
                className="glass-input w-full resize-none min-h-[44px] max-h-32 pr-12"
                rows={1}
              />
              
              {/* Quick Actions */}
              <div className="absolute right-2 top-2 flex space-x-1">
                <button
                  onClick={() => setShowAgentSelector(!showAgentSelector)}
                  className="text-gray-400 hover:text-white p-1"
                  title="Select Agent"
                >
                  <Users className="w-4 h-4" />
                </button>
                <button
                  className="text-gray-400 hover:text-white p-1"
                  title="Insert Code Block"
                >
                  <Code className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Voice Input */}
            <button
              className={`glass-button p-2 flex-shrink-0 ${isRecording ? 'bg-red-500/20 text-red-400' : ''}`}
              onClick={() => setIsRecording(!isRecording)}
            >
              <Mic className="w-4 h-4" />
            </button>

            {/* Send Button */}
            <button
              onClick={handleSendMessage}
              disabled={!newMessage.trim()}
              className="glass-button p-2 flex-shrink-0 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Selected Agent Indicator */}
          {selectedAgent && (
            <div className="mt-2 text-xs text-gray-400">
              Sending to: {activeAgents.find(a => a.id === selectedAgent)?.name}
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            // Handle file uploads
            console.log('Files selected:', e.target.files);
          }}
        />
      </div>

      {/* Sidebar (25%) */}
      <div className="w-80 flex flex-col space-y-4">
        {/* Active Agents Panel */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-3 flex items-center">
            <Users className="w-4 h-4 mr-2" />
            Active Agents
          </h3>
          <div className="space-y-2">
            {activeAgents.map(agent => (
              <div key={agent.id} className="flex items-center justify-between p-2 hover:bg-white/5 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="text-lg">{agent.avatar}</div>
                  <div>
                    <div className="text-white text-sm font-medium">{agent.name}</div>
                    <div className="text-xs text-gray-400">{agent.status}</div>
                  </div>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  agent.status === 'active' ? 'bg-green-400' : 
                  agent.status === 'busy' ? 'bg-yellow-400' : 'bg-gray-400'
                }`}></div>
              </div>
            ))}
          </div>
        </div>

        {/* Session Management */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-3 flex items-center">
            <MessageSquare className="w-4 h-4 mr-2" />
            Chat Sessions
          </h3>
          <div className="space-y-2">
            <div className="p-2 bg-white/10 rounded-lg">
              <div className="text-white text-sm font-medium">Current Session</div>
              <div className="text-xs text-gray-400">Started 2 hours ago</div>
            </div>
            <button className="w-full text-left p-2 hover:bg-white/5 rounded-lg">
              <div className="text-white text-sm">Previous Session</div>
              <div className="text-xs text-gray-400">Yesterday</div>
            </button>
          </div>
          <button className="w-full glass-button mt-3 text-sm">
            New Session
          </button>
        </div>

        {/* Quick Actions */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-3">Quick Actions</h3>
          <div className="space-y-2">
            <button className="w-full glass-button text-sm text-left">
              <Code className="w-4 h-4 inline mr-2" />
              Code Review
            </button>
            <button className="w-full glass-button text-sm text-left">
              <Brain className="w-4 h-4 inline mr-2" />
              Knowledge Query
            </button>
            <button className="w-full glass-button text-sm text-left">
              <Zap className="w-4 h-4 inline mr-2" />
              Task Automation
            </button>
            <button className="w-full glass-button text-sm text-left">
              <Sparkles className="w-4 h-4 inline mr-2" />
              Creative Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;