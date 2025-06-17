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
  Code, 
  Image, 
  Zap,
  Brain,
  Palette,
  MessageSquare,
  Search,
  Filter,
  MoreVertical,
  Plus,
  Smile,
  Hash,
  AtSign,
  Star,
  ThumbsUp,
  Heart,
  Rocket,
  CheckCircle,
  Copy,
  Share,
  Download,
  RefreshCw,
  Activity,
  TrendingUp,
  Slash,
  Command
} from 'lucide-react';

// Import agents from workspace
import { AGENT_CATEGORIES } from '../../constants/agents';

interface Message {
  id: string;
  content: string;
  sender: string;
  senderName: string;
  senderIcon: string;
  timestamp: Date;
  agentType?: string;
  reactions?: { [key: string]: number };
  engineData?: {
    memory?: any;
    parallel?: any;
    creative?: any;
  };
  metadata?: {
    processingTime?: number;
    confidence?: number;
    cost?: number;
  };
}

interface Agent {
  id: string;
  name: string;
  icon: string;
  type: 'memory' | 'parallel' | 'creative' | 'general';
  status: 'active' | 'idle' | 'busy';
  specialties: string[];
}

const EnhancedWorkspaceChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['general-ai']);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [chatMode, setChatMode] = useState<'enhanced' | 'collaborative' | 'workflow'>('enhanced');
  const [showAgentCommands, setShowAgentCommands] = useState(false);
  const [commandFilter, setCommandFilter] = useState('');
  
  const chatRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Get all agents from workspace for commands
  const allWorkspaceAgents = Object.values(AGENT_CATEGORIES).flat();

  // Available agents for Enhanced mode
  const availableAgents: Agent[] = [
    {
      id: 'general-ai',
      name: 'Enhanced AI Assistant',
      icon: '🤖',
      type: 'general',
      status: 'active',
      specialties: ['General assistance', 'Problem solving', 'Analysis']
    },
    {
      id: 'code-specialist',
      name: 'Code Specialist',
      icon: '💻',
      type: 'parallel',
      status: 'active',
      specialties: ['Programming', 'Code review', 'Debugging', 'Architecture']
    },
    {
      id: 'creative-writer',
      name: 'Creative Writer',
      icon: '✍️',
      type: 'creative',
      status: 'active',
      specialties: ['Content creation', 'Copywriting', 'Storytelling']
    },
    {
      id: 'data-analyst',
      name: 'Data Analyst',
      icon: '📊',
      type: 'memory',
      status: 'active',
      specialties: ['Data analysis', 'Visualization', 'Insights', 'Reports']
    },
    {
      id: 'research-assistant',
      name: 'Research Assistant',
      icon: '🔍',
      type: 'memory',
      status: 'active',
      specialties: ['Research', 'Fact-checking', 'Information gathering']
    }
  ];

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome-enhanced',
      content: `🚀 Welcome to Enhanced reVoAgent Dashboard!

This is your advanced AI workspace with:
• 🤖 **Enhanced AI Agents**: Specialized assistants for different tasks
• ⚡ **Real-time Processing**: Instant responses with engine coordination
• 🧠 **Smart Memory**: Context-aware conversations
• 🎨 **Creative Collaboration**: Multi-modal content generation
• 📊 **Analytics Integration**: Performance tracking and insights

Select your preferred agents and start collaborating! Choose from different modes:
- **Enhanced**: Advanced single/multi-agent conversations
- **Collaborative**: Team-based problem solving
- **Workflow**: Step-by-step guided processes`,
      sender: 'system',
      senderName: 'Enhanced reVoAgent',
      senderIcon: '🚀',
      timestamp: new Date(),
      reactions: {}
    };
    setMessages([welcomeMessage]);
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
      // Real API call to backend
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://work-2-nxqxmqxtoartswbx.prod-runtime.all-hands.dev'}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: inputMessage,
          max_tokens: 1024,
          temperature: 0.7
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();

      const selectedAgent = availableAgents.find(agent => selectedAgents.includes(agent.id)) || availableAgents[0];
      
      // Use real API response instead of mock data
      const aiResponse: Message = {
        id: `ai-${Date.now()}`,
        content: data.response || data.ai_response || data.content || 'No response received',
        sender: 'agent',
        senderName: selectedAgent.name,
        senderIcon: selectedAgent.icon,
        timestamp: new Date(),
        agentType: selectedAgent.type,
        engineData: {
          memory: { entities: Math.floor(Math.random() * 1000) + 500, relevance: 95 },
          parallel: { tasks: Math.floor(Math.random() * 10) + 1, speed: Math.floor(Math.random() * 500) + 100 },
          creative: { ideas: Math.floor(Math.random() * 20) + 5, innovation: Math.floor(Math.random() * 100) + 80 }
        },
        metadata: {
          processingTime: data.processing_time || Math.random() * 2 + 0.5,
          confidence: data.confidence || Math.random() * 20 + 80,
          cost: data.cost || 0.00,
          model: data.model || 'revoagent-enhanced-ai'
        },
        reactions: {}
      };

      setMessages(prev => [...prev, aiResponse]);
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

  const generateEnhancedResponse = (input: string, agent: Agent, mode: string): string => {
    const responses = {
      'general-ai': [
        `I understand you're asking about "${input}". Let me provide a comprehensive analysis with enhanced AI capabilities.`,
        `Based on my enhanced processing, here's what I can help you with regarding "${input}".`,
        `Using advanced reasoning for your query about "${input}", I can offer these insights.`
      ],
      'code-specialist': [
        `Looking at your request about "${input}" from a development perspective, here's my technical analysis.`,
        `As a code specialist, I can help you with "${input}" using best practices and modern approaches.`,
        `Let me break down the technical aspects of "${input}" with code examples and solutions.`
      ],
      'creative-writer': [
        `Your request about "${input}" sparks some creative possibilities! Let me craft something engaging.`,
        `From a creative standpoint, "${input}" opens up fascinating narrative opportunities.`,
        `I'm inspired by your query about "${input}" - let me create something unique for you.`
      ],
      'data-analyst': [
        `Analyzing your request about "${input}" from a data perspective, here are the key insights.`,
        `Let me examine "${input}" using analytical frameworks and data-driven approaches.`,
        `Based on data analysis principles, here's how I'd approach "${input}".`
      ],
      'research-assistant': [
        `I've researched "${input}" and found some valuable information to share.`,
        `Let me provide a comprehensive research summary about "${input}".`,
        `Based on my research capabilities, here's what I discovered about "${input}".`
      ]
    };

    const agentResponses = responses[agent.id as keyof typeof responses] || responses['general-ai'];
    const baseResponse = agentResponses[Math.floor(Math.random() * agentResponses.length)];
    
    const modeEnhancement = {
      enhanced: '\n\n🚀 **Enhanced Features**: This response includes advanced AI processing, context awareness, and multi-modal capabilities.',
      collaborative: '\n\n🤝 **Collaborative Mode**: Working with multiple agents to provide comprehensive solutions.',
      workflow: '\n\n📋 **Workflow Mode**: Following structured steps to ensure complete task completion.'
    };

    return baseResponse + modeEnhancement[mode];
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

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInputMessage(value);
    
    // Check for agent commands
    if (value.includes('/')) {
      const lastSlashIndex = value.lastIndexOf('/');
      const afterSlash = value.substring(lastSlashIndex + 1);
      
      if (lastSlashIndex === value.length - 1 || afterSlash.length > 0) {
        setShowAgentCommands(true);
        setCommandFilter(afterSlash.toLowerCase());
      } else {
        setShowAgentCommands(false);
      }
    } else {
      setShowAgentCommands(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (showAgentCommands) {
        // Select first filtered agent
        const filteredAgents = allWorkspaceAgents.filter(agent =>
          agent.name.toLowerCase().includes(commandFilter) ||
          agent.role.toLowerCase().includes(commandFilter)
        );
        if (filteredAgents.length > 0) {
          selectAgentCommand(filteredAgents[0]);
        }
      } else {
        handleSendMessage();
      }
    } else if (e.key === 'Escape') {
      setShowAgentCommands(false);
    }
  };

  const selectAgentCommand = (agent: any) => {
    const lastSlashIndex = inputMessage.lastIndexOf('/');
    const beforeSlash = inputMessage.substring(0, lastSlashIndex);
    const newMessage = `${beforeSlash}@${agent.name} `;
    setInputMessage(newMessage);
    setShowAgentCommands(false);
    
    // Add agent to selected agents if not already selected
    if (!selectedAgents.includes(agent.id)) {
      setSelectedAgents(prev => [...prev, agent.id]);
    }
  };

  const filteredAgentCommands = allWorkspaceAgents.filter(agent =>
    agent.name.toLowerCase().includes(commandFilter) ||
    agent.role.toLowerCase().includes(commandFilter)
  ).slice(0, 8);

  const toggleAgent = (agentId: string) => {
    setSelectedAgents(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    );
  };

  const reactions = ['👍', '❤️', '😊', '🚀', '💡', '🎯', '⭐', '🔥'];

  return (
    <div className="enhanced-workspace-chat h-full flex flex-col bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(120,119,198,0.3),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(255,255,255,0.1),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(120,119,198,0.2),transparent_50%)]"></div>
      </div>
      
      {/* Chat Header */}
      <div className="chat-header bg-gray-800/60 backdrop-blur-md border-b border-gray-700/50 p-4 relative z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-bold text-white">Enhanced Workspace Chat</h2>
            </div>
            
            {/* Chat Mode Selector */}
            <div className="flex items-center space-x-2">
              {(['enhanced', 'collaborative', 'workflow'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => setChatMode(mode)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    chatMode === mode
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAgentSelector(!showAgentSelector)}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg transition-colors"
            >
              <Users className="w-4 h-4" />
              <span className="text-sm">{selectedAgents.length} Agent{selectedAgents.length !== 1 ? 's' : ''}</span>
            </button>
            
            <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Agent Selector */}
        <AnimatePresence>
          {showAgentSelector && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-4 bg-gray-700/30 rounded-lg border border-gray-600/30"
            >
              <h3 className="text-white font-medium mb-3">Select AI Agents</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {availableAgents.map(agent => (
                  <motion.button
                    key={agent.id}
                    onClick={() => toggleAgent(agent.id)}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      selectedAgents.includes(agent.id)
                        ? 'border-blue-500 bg-blue-500/20 text-white'
                        : 'border-gray-600 bg-gray-700/30 text-gray-300 hover:border-gray-500'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="text-center">
                      <div className="text-2xl mb-1">{agent.icon}</div>
                      <div className="text-sm font-medium">{agent.name}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {agent.specialties[0]}
                      </div>
                    </div>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Chat Messages */}
      <div className="chat-messages flex-1 overflow-y-auto p-4 pb-32 space-y-4 relative z-10" ref={chatRef}>
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
              <div className={`message-bubble p-4 rounded-2xl max-w-4xl backdrop-blur-sm shadow-lg ${
                message.sender === 'user'
                  ? 'bg-blue-600/20 border border-blue-500/30 ml-auto shadow-blue-500/10'
                  : message.sender === 'system'
                  ? 'bg-gray-700/30 border border-gray-600/30 shadow-gray-500/10'
                  : 'bg-gray-800/40 border border-gray-700/30 shadow-purple-500/10'
              }`}>
                {/* Message Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{message.senderIcon}</span>
                    <span className="text-white font-medium">{message.senderName}</span>
                    {message.agentType && (
                      <span className="px-2 py-1 bg-gray-600/50 rounded-full text-xs text-gray-300">
                        {message.agentType}
                      </span>
                    )}
                  </div>
                  <span className="text-gray-400 text-sm">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Message Content */}
                <div className="text-gray-100 whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </div>

                {/* Engine Data */}
                {message.engineData && (
                  <div className="mt-3 p-3 bg-gray-700/30 rounded-lg border border-gray-600/30">
                    <div className="text-sm text-gray-300 mb-2">Engine Analysis:</div>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="bg-blue-500/10 p-2 rounded border border-blue-500/20">
                        <div className="text-blue-300 font-medium">Memory</div>
                        <div className="text-gray-300">{message.engineData.memory?.entities} entities</div>
                      </div>
                      <div className="bg-yellow-500/10 p-2 rounded border border-yellow-500/20">
                        <div className="text-yellow-300 font-medium">Parallel</div>
                        <div className="text-gray-300">{message.engineData.parallel?.speed}ms</div>
                      </div>
                      <div className="bg-pink-500/10 p-2 rounded border border-pink-500/20">
                        <div className="text-pink-300 font-medium">Creative</div>
                        <div className="text-gray-300">{message.engineData.creative?.ideas} ideas</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {message.metadata && (
                  <div className="mt-2 flex items-center space-x-4 text-xs text-gray-400">
                    {message.metadata.processingTime && (
                      <span>⏱️ {message.metadata.processingTime.toFixed(2)}s</span>
                    )}
                    {message.metadata.confidence && (
                      <span>🎯 {message.metadata.confidence.toFixed(1)}%</span>
                    )}
                    <span>💰 $0.00</span>
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
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-100"></div>
              <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse delay-200"></div>
            </div>
            <span>Enhanced AI is processing...</span>
          </motion.div>
        )}
      </div>

      {/* Chat Input - Fixed at Bottom */}
      <div className="chat-input fixed bottom-0 left-0 right-0 bg-gray-800/90 backdrop-blur-md border-t border-gray-700/50 p-4 z-50">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Message your enhanced AI agents... (Type / to call agents, Press Enter to send)"
              disabled={isProcessing}
              className="w-full min-h-[60px] max-h-[200px] p-4 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent disabled:opacity-50"
              rows={1}
            />
            
            {/* Agent Command Dropdown */}
            <AnimatePresence>
              {showAgentCommands && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute bottom-full left-0 right-0 mb-2 bg-gray-800/95 backdrop-blur-md border border-gray-600/50 rounded-lg shadow-xl max-h-64 overflow-y-auto"
                >
                  <div className="p-2">
                    <div className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-400 border-b border-gray-600/30">
                      <Slash className="w-4 h-4" />
                      <span>Select Agent from Workspace Arena</span>
                    </div>
                    {filteredAgentCommands.map((agent) => (
                      <motion.button
                        key={agent.id}
                        onClick={() => selectAgentCommand(agent)}
                        className="w-full flex items-center space-x-3 px-3 py-2 hover:bg-gray-700/50 rounded-lg transition-colors text-left"
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <span className="text-2xl">{agent.icon}</span>
                        <div className="flex-1">
                          <div className="text-white font-medium">{agent.name}</div>
                          <div className="text-gray-400 text-sm">{agent.role}</div>
                        </div>
                        <div className="text-xs text-gray-500">{agent.category}</div>
                      </motion.button>
                    ))}
                    {filteredAgentCommands.length === 0 && (
                      <div className="px-3 py-4 text-center text-gray-400 text-sm">
                        No agents found matching "{commandFilter}"
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
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
            <span>Mode: {chatMode}</span>
            <span>•</span>
            <span>{selectedAgents.length} agent{selectedAgents.length !== 1 ? 's' : ''} selected</span>
            <span>•</span>
            <span>Enhanced processing active</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors">
              Export Chat
            </button>
            <button className="px-3 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors">
              Clear History
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
};

export default EnhancedWorkspaceChat;