import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  MessageSquare, Send, Paperclip, Mic, MicOff, Settings, 
  Users, Bot, Code, Image, FileText, Download, Copy, 
  ThumbsUp, ThumbsDown, RotateCcw, Zap, Brain, Palette,
  ChevronDown, ChevronUp, Search, Filter, MoreVertical,
  X, Plus, Minimize2, Maximize2, Volume2, VolumeX,
  Clock, CheckCircle, AlertCircle, Loader, Star,
  Hash, AtSign, Smile, Bookmark, Share, Edit3,
  Eye, EyeOff, Trash2, Archive, Pin, Flag,
  Camera, Video, Phone, ScreenShare, Calendar,
  Globe, Lock, Unlock, Shield, Cpu, Database,
  Activity, TrendingUp, BarChart3, PieChart,
  RefreshCw, PlayCircle, PauseCircle, StopCircle,
  FastForward, Rewind, SkipBack, SkipForward
} from 'lucide-react';

// Import our existing hooks
import { useChat } from '../hooks/useApi';
import { useChatWebSocket } from '../hooks/useWebSocket';

// Types for our enhanced chat interface
interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agentName?: string;
  agentType?: 'memory' | 'parallel' | 'creative' | 'code' | 'general';
  timestamp: Date;
  type: 'text' | 'code' | 'image' | 'file' | 'system';
  metadata?: {
    language?: string;
    fileName?: string;
    fileSize?: number;
    codeExecuted?: boolean;
    executionResult?: string;
    confidence?: number;
    processingTime?: number;
    tokens?: number;
    cost?: number;
  };
  reactions?: { [emoji: string]: number };
  isEdited?: boolean;
  isBookmarked?: boolean;
  isPinned?: boolean;
  threadId?: string;
  replyTo?: string;
  attachments?: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
    url: string;
  }>;
}

interface Agent {
  id: string;
  name: string;
  type: 'memory' | 'parallel' | 'creative' | 'code' | 'general';
  status: 'online' | 'busy' | 'offline';
  avatar: string;
  description: string;
  capabilities: string[];
  isActive: boolean;
  responseTime: number;
  accuracy: number;
  totalInteractions: number;
}

const EnhancedAIChatInterface = () => {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['general-assistant']);
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [chatMode, setChatMode] = useState<'single' | 'multi' | 'collaborative'>('single');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'text' | 'code' | 'files'>('all');
  const [isMinimized, setIsMinimized] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [fontSize, setFontSize] = useState('medium');
  const [currentThread, setCurrentThread] = useState<string | null>(null);
  const [showAgentMetrics, setShowAgentMetrics] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Custom hooks
  const { sendMessage, loading: chatLoading } = useChat();
  const { 
    isConnected, 
    messages: wsMessages, 
    sendChatMessage,
    connectionStatus 
  } = useChatWebSocket();

  // Available agents with enhanced metadata
  const availableAgents: Agent[] = [
    {
      id: 'general-assistant',
      name: 'General Assistant',
      type: 'general',
      status: 'online',
      avatar: '🤖',
      description: 'General purpose AI assistant for various tasks',
      capabilities: ['General Q&A', 'Task Planning', 'Research', 'Writing'],
      isActive: true,
      responseTime: 0.8,
      accuracy: 94.2,
      totalInteractions: 15847
    },
    {
      id: 'memory-engine',
      name: 'Memory Engine',
      type: 'memory',
      status: 'online',
      avatar: '🧠',
      description: 'Perfect recall with unlimited knowledge storage',
      capabilities: ['Knowledge Retrieval', 'Context Memory', 'Learning', 'Pattern Recognition'],
      isActive: true,
      responseTime: 0.05,
      accuracy: 99.9,
      totalInteractions: 89234
    },
    {
      id: 'parallel-processor',
      name: 'Parallel Processor',
      type: 'parallel',
      status: 'online',
      avatar: '⚡',
      description: 'High-speed parallel processing for complex tasks',
      capabilities: ['Multi-threading', 'Batch Processing', 'Performance Optimization', 'Load Balancing'],
      isActive: true,
      responseTime: 0.02,
      accuracy: 97.8,
      totalInteractions: 45621
    },
    {
      id: 'creative-engine',
      name: 'Creative Engine',
      type: 'creative',
      status: 'online',
      avatar: '🎨',
      description: 'AI-powered innovation and creative problem solving',
      capabilities: ['Creative Writing', 'Brainstorming', 'Design Thinking', 'Innovation'],
      isActive: true,
      responseTime: 1.2,
      accuracy: 92.5,
      totalInteractions: 23456
    },
    {
      id: 'code-specialist',
      name: 'Code Specialist',
      type: 'code',
      status: 'online',
      avatar: '💻',
      description: 'Expert code analysis, debugging, and development',
      capabilities: ['Code Review', 'Debugging', 'Optimization', 'Documentation', 'Testing'],
      isActive: true,
      responseTime: 0.6,
      accuracy: 96.7,
      totalInteractions: 67890
    },
    {
      id: 'debug-detective',
      name: 'Debug Detective',
      type: 'code',
      status: 'busy',
      avatar: '🔍',
      description: 'Specialized in finding and fixing bugs',
      capabilities: ['Bug Detection', 'Error Analysis', 'Performance Debugging', 'Security Auditing'],
      isActive: false,
      responseTime: 0.9,
      accuracy: 98.1,
      totalInteractions: 34567
    },
    {
      id: 'workflow-manager',
      name: 'Workflow Manager',
      type: 'general',
      status: 'online',
      avatar: '📋',
      description: 'Manages complex workflows and task coordination',
      capabilities: ['Task Management', 'Workflow Design', 'Process Optimization', 'Team Coordination'],
      isActive: false,
      responseTime: 0.7,
      accuracy: 95.3,
      totalInteractions: 12345
    }
  ];

  // Sample messages for demonstration
  const sampleMessages: ChatMessage[] = [
    {
      id: '1',
      content: 'Hello! I\'m your enhanced AI assistant. I can help you with coding, analysis, creative tasks, and much more. What would you like to work on today?',
      sender: 'agent',
      agentName: 'General Assistant',
      agentType: 'general',
      timestamp: new Date(Date.now() - 300000),
      type: 'text',
      metadata: {
        confidence: 100,
        processingTime: 0.05,
        tokens: 45,
        cost: 0
      }
    },
    {
      id: '2',
      content: 'Can you help me analyze this React component and suggest improvements?',
      sender: 'user',
      timestamp: new Date(Date.now() - 240000),
      type: 'text'
    },
    {
      id: '3',
      content: `I'd be happy to help you analyze your React component! I can see several areas for improvement:

\`\`\`typescript
// Example optimized component
import React, { memo, useCallback, useMemo } from 'react';

const OptimizedComponent = memo(({ data, onUpdate }) => {
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      processed: true
    }));
  }, [data]);

  const handleClick = useCallback((id) => {
    onUpdate(id);
  }, [onUpdate]);

  return (
    <div className="component">
      {processedData.map(item => (
        <div key={item.id} onClick={() => handleClick(item.id)}>
          {item.name}
        </div>
      ))}
    </div>
  );
});
\`\`\`

Key improvements:
1. **Memoization**: Using \`memo\` to prevent unnecessary re-renders
2. **useCallback**: Optimizing event handlers
3. **useMemo**: Caching expensive computations
4. **TypeScript**: Better type safety`,
      sender: 'agent',
      agentName: 'Code Specialist',
      agentType: 'code',
      timestamp: new Date(Date.now() - 180000),
      type: 'code',
      metadata: {
        language: 'typescript',
        confidence: 96.7,
        processingTime: 1.2,
        tokens: 234,
        cost: 0
      },
      reactions: { '👍': 2, '🔥': 1 }
    }
  ];

  // Initialize with sample messages
  useEffect(() => {
    if (messages.length === 0) {
      setMessages(sampleMessages);
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Handle WebSocket messages
  useEffect(() => {
    if (wsMessages.length > 0) {
      const latestMessage = wsMessages[wsMessages.length - 1];
      // Convert WebSocket message to our format
      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        content: latestMessage.content || '',
        sender: 'agent',
        agentName: latestMessage.agentName || 'Assistant',
        timestamp: new Date(),
        type: 'text',
        metadata: latestMessage.metadata
      };
      setMessages(prev => [...prev, newMessage]);
    }
  }, [wsMessages]);

  // Send message handler
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // Send via WebSocket if connected, otherwise use REST API
      if (isConnected) {
        await sendChatMessage(inputMessage, {
          agents: selectedAgents,
          mode: chatMode,
          threadId: currentThread
        });
      } else {
        const response = await sendMessage(inputMessage, {
          agents: selectedAgents,
          mode: chatMode
        });
        
        if (response) {
          const agentMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            content: response.content,
            sender: 'agent',
            agentName: response.agentName || 'Assistant',
            timestamp: new Date(),
            type: (response.type as 'text' | 'code' | 'image' | 'file' | 'system') || 'text',
            metadata: response.metadata
          };
          setMessages(prev => [...prev, agentMessage]);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'agent',
        agentName: 'System',
        timestamp: new Date(),
        type: 'text',
        metadata: { confidence: 0 }
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, [inputMessage, selectedAgents, chatMode, currentThread, isConnected, sendChatMessage, sendMessage]);

  // Handle key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // File upload handler
  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach(file => {
      const fileMessage: ChatMessage = {
        id: Date.now().toString() + Math.random(),
        content: `Uploaded file: ${file.name}`,
        sender: 'user',
        timestamp: new Date(),
        type: 'file',
        metadata: {
          fileName: file.name,
          fileSize: file.size
        },
        attachments: [{
          id: Date.now().toString(),
          name: file.name,
          type: file.type,
          size: file.size,
          url: URL.createObjectURL(file)
        }]
      };
      setMessages(prev => [...prev, fileMessage]);
    });
  }, []);

  // Voice recording handlers
  const startRecording = useCallback(() => {
    setIsRecording(true);
    // Implement voice recording logic
  }, []);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
    // Implement voice recording stop logic
  }, []);

  // Message actions
  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
  }, []);

  const bookmarkMessage = useCallback((messageId: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, isBookmarked: !msg.isBookmarked } : msg
    ));
  }, []);

  const addReaction = useCallback((messageId: string, emoji: string) => {
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const reactions = { ...msg.reactions };
        reactions[emoji] = (reactions[emoji] || 0) + 1;
        return { ...msg, reactions };
      }
      return msg;
    }));
  }, []);

  // Filter messages
  const filteredMessages = messages.filter(msg => {
    if (filterType !== 'all' && msg.type !== filterType) return false;
    if (searchQuery && !msg.content.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  // Agent selection component
  const AgentSelector = () => (
    <div className="bg-white/5 backdrop-blur-md rounded-xl p-4 border border-white/10">
      <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
        <Users className="w-5 h-5" />
        Active Agents ({selectedAgents.length})
      </h3>
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {availableAgents.map(agent => (
          <div
            key={agent.id}
            className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
              selectedAgents.includes(agent.id)
                ? 'bg-blue-500/20 border-blue-400/50'
                : 'bg-white/5 border-white/10 hover:border-white/20'
            }`}
            onClick={() => {
              if (selectedAgents.includes(agent.id)) {
                setSelectedAgents(prev => prev.filter(id => id !== agent.id));
              } else {
                setSelectedAgents(prev => [...prev, agent.id]);
              }
            }}
          >
            <div className="flex items-center gap-3">
              <div className="text-2xl">{agent.avatar}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">{agent.name}</span>
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'online' ? 'bg-green-400' :
                    agent.status === 'busy' ? 'bg-yellow-400' : 'bg-red-400'
                  }`} />
                </div>
                <p className="text-gray-300 text-sm">{agent.description}</p>
                <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                  <span>⚡ {agent.responseTime}s</span>
                  <span>🎯 {agent.accuracy}%</span>
                  <span>💬 {agent.totalInteractions.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Message component
  const MessageComponent = ({ message }: { message: ChatMessage }) => (
    <div className={`flex gap-3 mb-4 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
        message.sender === 'user' 
          ? 'bg-blue-500' 
          : message.agentType === 'memory' ? 'bg-purple-500' :
            message.agentType === 'parallel' ? 'bg-yellow-500' :
            message.agentType === 'creative' ? 'bg-pink-500' :
            message.agentType === 'code' ? 'bg-green-500' : 'bg-gray-500'
      }`}>
        {message.sender === 'user' ? '👤' : 
         availableAgents.find(a => a.name === message.agentName)?.avatar || '🤖'}
      </div>

      {/* Message content */}
      <div className={`flex-1 max-w-[80%] ${message.sender === 'user' ? 'text-right' : ''}`}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-white font-medium">
            {message.sender === 'user' ? 'You' : message.agentName}
          </span>
          {showTimestamps && (
            <span className="text-gray-400 text-xs">
              {message.timestamp.toLocaleTimeString()}
            </span>
          )}
          {message.metadata?.confidence && (
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
              {message.metadata.confidence}% confidence
            </span>
          )}
        </div>

        {/* Message bubble */}
        <div className={`p-4 rounded-xl ${
          message.sender === 'user'
            ? 'bg-blue-500/20 border border-blue-400/30'
            : 'bg-white/10 border border-white/20'
        }`}>
          {message.type === 'code' ? (
            <div className="bg-black/50 rounded-lg p-4 font-mono text-sm overflow-x-auto">
              <pre className="text-gray-300">{message.content}</pre>
            </div>
          ) : (
            <div className="text-white whitespace-pre-wrap">{message.content}</div>
          )}

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-3 space-y-2">
              {message.attachments.map(attachment => (
                <div key={attachment.id} className="flex items-center gap-2 p-2 bg-white/5 rounded-lg">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <span className="text-white text-sm">{attachment.name}</span>
                  <span className="text-gray-400 text-xs">
                    ({(attachment.size / 1024).toFixed(1)} KB)
                  </span>
                  <button className="ml-auto text-blue-400 hover:text-blue-300">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Metadata */}
          {message.metadata && (
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
              {message.metadata.processingTime && (
                <span>⏱️ {message.metadata.processingTime}s</span>
              )}
              {message.metadata.tokens && (
                <span>🔤 {message.metadata.tokens} tokens</span>
              )}
              {message.metadata.cost !== undefined && (
                <span>💰 ${message.metadata.cost.toFixed(4)}</span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 mt-2">
          <button
            onClick={() => copyMessage(message.content)}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={() => bookmarkMessage(message.id)}
            className={`transition-colors ${
              message.isBookmarked ? 'text-yellow-400' : 'text-gray-400 hover:text-white'
            }`}
          >
            <Bookmark className="w-4 h-4" />
          </button>
          <button
            onClick={() => addReaction(message.id, '👍')}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => addReaction(message.id, '❤️')}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <span>❤️</span>
          </button>

          {/* Reactions */}
          {message.reactions && Object.keys(message.reactions).length > 0 && (
            <div className="flex items-center gap-1 ml-2">
              {Object.entries(message.reactions).map(([emoji, count]) => (
                <span key={emoji} className="text-xs bg-white/10 px-2 py-1 rounded-full">
                  {emoji} {count}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className={`h-screen flex ${isMinimized ? 'h-16' : ''} bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900`}>
      {/* Sidebar */}
      {sidebarOpen && !isMinimized && (
        <div className="w-80 bg-black/20 backdrop-blur-md border-r border-white/10 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-bold text-lg flex items-center gap-2">
                <MessageSquare className="w-6 h-6 text-blue-400" />
                AI Chat Hub
              </h2>
              <button
                onClick={() => setSidebarOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Mode Selector */}
            <div className="space-y-2">
              <label className="text-gray-300 text-sm">Chat Mode</label>
              <select
                value={chatMode}
                onChange={(e) => setChatMode(e.target.value as any)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
              >
                <option value="single">Single Agent</option>
                <option value="multi">Multi-Agent</option>
                <option value="collaborative">Collaborative</option>
              </select>
            </div>
          </div>

          {/* Agent Selector */}
          <div className="flex-1 overflow-y-auto p-4">
            <AgentSelector />
          </div>

          {/* Connection Status */}
          <div className="p-4 border-t border-white/10">
            <div className={`flex items-center gap-2 text-sm ${
              isConnected ? 'text-green-400' : 'text-red-400'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {!isMinimized && (
          <>
            {/* Chat Header */}
            <div className="bg-black/20 backdrop-blur-md border-b border-white/10 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {!sidebarOpen && (
                    <button
                      onClick={() => setSidebarOpen(true)}
                      className="text-gray-400 hover:text-white"
                    >
                      <Users className="w-5 h-5" />
                    </button>
                  )}
                  <h1 className="text-white font-bold text-xl">Enhanced AI Chat</h1>
                  <div className="flex items-center gap-2">
                    {selectedAgents.map(agentId => {
                      const agent = availableAgents.find(a => a.id === agentId);
                      return agent ? (
                        <div key={agentId} className="text-lg" title={agent.name}>
                          {agent.avatar}
                        </div>
                      ) : null;
                    })}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {/* Search */}
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search messages..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-white/10 border border-white/20 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 w-48"
                    />
                  </div>

                  {/* Filter */}
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value as any)}
                    className="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
                  >
                    <option value="all">All</option>
                    <option value="text">Text</option>
                    <option value="code">Code</option>
                    <option value="file">Files</option>
                  </select>

                  {/* Settings */}
                  <button
                    onClick={() => setSettingsOpen(!settingsOpen)}
                    className="text-gray-400 hover:text-white"
                  >
                    <Settings className="w-5 h-5" />
                  </button>

                  {/* Minimize */}
                  <button
                    onClick={() => setIsMinimized(true)}
                    className="text-gray-400 hover:text-white"
                  >
                    <Minimize2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {filteredMessages.map(message => (
                <MessageComponent key={message.id} message={message} />
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <div className="flex gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center">
                    🤖
                  </div>
                  <div className="bg-white/10 border border-white/20 rounded-xl p-4">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                      <span className="text-gray-400 text-sm">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-black/20 backdrop-blur-md border-t border-white/10 p-4">
              <div className="flex items-end gap-3">
                {/* File upload */}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                />

                {/* Voice recording */}
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`transition-colors ${
                    isRecording ? 'text-red-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                {/* Text input */}
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message... (Shift+Enter for new line)"
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 resize-none min-h-[50px] max-h-32"
                    rows={1}
                  />
                  
                  {/* Character count */}
                  <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                    {inputMessage.length}/2000
                  </div>
                </div>

                {/* Send button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || chatLoading}
                  className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white p-3 rounded-lg transition-colors"
                >
                  {chatLoading ? (
                    <Loader className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>

              {/* Quick actions */}
              <div className="flex items-center gap-2 mt-3">
                <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded-full text-gray-300 transition-colors">
                  💡 Suggest improvements
                </button>
                <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded-full text-gray-300 transition-colors">
                  🔍 Analyze code
                </button>
                <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded-full text-gray-300 transition-colors">
                  📝 Write documentation
                </button>
                <button className="text-xs bg-white/10 hover:bg-white/20 px-3 py-1 rounded-full text-gray-300 transition-colors">
                  🚀 Deploy project
                </button>
              </div>
            </div>
          </>
        )}

        {/* Minimized view */}
        {isMinimized && (
          <div className="bg-black/20 backdrop-blur-md border border-white/10 rounded-lg p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-400" />
              <span className="text-white font-medium">AI Chat</span>
              {isConnected && (
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
            </div>
            <button
              onClick={() => setIsMinimized(false)}
              className="text-gray-400 hover:text-white"
            >
              <Maximize2 className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {settingsOpen && !isMinimized && (
        <div className="w-80 bg-black/20 backdrop-blur-md border-l border-white/10 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-bold">Chat Settings</h3>
            <button
              onClick={() => setSettingsOpen(false)}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4">
            {/* Voice Settings */}
            <div>
              <label className="flex items-center gap-2 text-white">
                <input
                  type="checkbox"
                  checked={voiceEnabled}
                  onChange={(e) => setVoiceEnabled(e.target.checked)}
                  className="rounded"
                />
                Enable voice responses
              </label>
            </div>

            {/* Auto-scroll */}
            <div>
              <label className="flex items-center gap-2 text-white">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded"
                />
                Auto-scroll to new messages
              </label>
            </div>

            {/* Show timestamps */}
            <div>
              <label className="flex items-center gap-2 text-white">
                <input
                  type="checkbox"
                  checked={showTimestamps}
                  onChange={(e) => setShowTimestamps(e.target.checked)}
                  className="rounded"
                />
                Show timestamps
              </label>
            </div>

            {/* Show agent metrics */}
            <div>
              <label className="flex items-center gap-2 text-white">
                <input
                  type="checkbox"
                  checked={showAgentMetrics}
                  onChange={(e) => setShowAgentMetrics(e.target.checked)}
                  className="rounded"
                />
                Show agent metrics
              </label>
            </div>

            {/* Font size */}
            <div>
              <label className="text-white text-sm mb-2 block">Font Size</label>
              <select
                value={fontSize}
                onChange={(e) => setFontSize(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white"
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
              </select>
            </div>

            {/* Theme */}
            <div>
              <label className="flex items-center gap-2 text-white">
                <input
                  type="checkbox"
                  checked={darkMode}
                  onChange={(e) => setDarkMode(e.target.checked)}
                  className="rounded"
                />
                Dark mode
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedAIChatInterface;