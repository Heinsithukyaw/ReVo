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
  Menu, ArrowLeft, ArrowRight, Home
} from 'lucide-react';

// Import our existing hooks
import { useChat } from '../hooks/useApi';
import { useChatWebSocket } from '../hooks/useWebSocket';

// Mobile-optimized chat interface
const MobileAIChatInterface = () => {
  const [messages, setMessages] = useState<any[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('general-assistant');
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Custom hooks
  const { sendMessage, loading: chatLoading } = useChat();
  const { isConnected, sendChatMessage } = useChatWebSocket();

  // Mobile-optimized agents
  const mobileAgents = [
    {
      id: 'general-assistant',
      name: 'Assistant',
      avatar: '🤖',
      color: 'bg-blue-500',
      description: 'General AI assistant'
    },
    {
      id: 'memory-engine',
      name: 'Memory',
      avatar: '🧠',
      color: 'bg-purple-500',
      description: 'Perfect recall engine'
    },
    {
      id: 'code-specialist',
      name: 'Code',
      avatar: '💻',
      color: 'bg-green-500',
      description: 'Code expert'
    },
    {
      id: 'creative-engine',
      name: 'Creative',
      avatar: '🎨',
      color: 'bg-pink-500',
      description: 'Creative AI'
    }
  ];

  // Sample mobile messages
  const sampleMobileMessages = [
    {
      id: '1',
      content: 'Hi! I\'m your mobile AI assistant. How can I help you today?',
      sender: 'agent',
      agentName: 'Assistant',
      timestamp: new Date(Date.now() - 300000),
      type: 'text'
    },
    {
      id: '2',
      content: 'Can you help me with a quick code review?',
      sender: 'user',
      timestamp: new Date(Date.now() - 240000),
      type: 'text'
    },
    {
      id: '3',
      content: 'Absolutely! Please share your code and I\'ll review it for you. I can check for:\n\n• Performance issues\n• Security vulnerabilities\n• Best practices\n• Code optimization\n\nJust paste your code or upload a file!',
      sender: 'agent',
      agentName: 'Code Specialist',
      timestamp: new Date(Date.now() - 180000),
      type: 'text'
    }
  ];

  // Initialize with sample messages
  useEffect(() => {
    if (messages.length === 0) {
      setMessages(sampleMobileMessages);
    }
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Send message handler
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
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
      // Simulate AI response for mobile demo
      setTimeout(() => {
        const selectedAgentData = mobileAgents.find(a => a.id === selectedAgent);
        const agentMessage = {
          id: (Date.now() + 1).toString(),
          content: `I understand you want help with: "${inputMessage}". Let me assist you with that right away!`,
          sender: 'agent',
          agentName: selectedAgentData?.name || 'Assistant',
          timestamp: new Date(),
          type: 'text'
        };
        setMessages(prev => [...prev, agentMessage]);
        setIsTyping(false);
      }, 1500);
    } catch (error) {
      console.error('Error sending message:', error);
      setIsTyping(false);
    }
  }, [inputMessage, selectedAgent]);

  // Handle key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // Quick action buttons
  const quickActions = [
    { label: '💡 Ideas', action: () => setInputMessage('Give me some creative ideas for...') },
    { label: '🔍 Analyze', action: () => setInputMessage('Please analyze this...') },
    { label: '📝 Write', action: () => setInputMessage('Help me write...') },
    { label: '🚀 Deploy', action: () => setInputMessage('How do I deploy...') }
  ];

  // Mobile message component
  const MobileMessage = ({ message }: { message: any }) => (
    <div className={`flex gap-2 mb-3 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
        message.sender === 'user' 
          ? 'bg-blue-500' 
          : mobileAgents.find(a => a.name === message.agentName)?.color || 'bg-gray-500'
      }`}>
        {message.sender === 'user' ? '👤' : 
         mobileAgents.find(a => a.name === message.agentName)?.avatar || '🤖'}
      </div>

      {/* Message bubble */}
      <div className={`max-w-[75%] ${message.sender === 'user' ? 'text-right' : ''}`}>
        <div className={`p-3 rounded-2xl ${
          message.sender === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-white/10 text-white border border-white/20'
        }`}>
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        </div>
        
        {/* Timestamp */}
        <div className="text-xs text-gray-400 mt-1 px-2">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );

  return (
    <div className={`${isFullscreen ? 'fixed inset-0 z-50' : 'h-screen'} bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col`}>
      {/* Mobile Header */}
      <div className="bg-black/20 backdrop-blur-md border-b border-white/10 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
            {mobileAgents.find(a => a.id === selectedAgent)?.avatar || '🤖'}
          </div>
          <div>
            <h1 className="text-white font-semibold text-lg">AI Chat</h1>
            <div className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isConnected ? 'Online' : 'Offline'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Agent selector */}
          <button
            onClick={() => setShowAgentSelector(!showAgentSelector)}
            className="text-white p-2 rounded-lg bg-white/10"
          >
            <Users className="w-5 h-5" />
          </button>

          {/* Settings */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="text-white p-2 rounded-lg bg-white/10"
          >
            <Settings className="w-5 h-5" />
          </button>

          {/* Fullscreen toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="text-white p-2 rounded-lg bg-white/10"
          >
            {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Agent Selector Modal */}
      {showAgentSelector && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center p-4">
          <div className="bg-black/80 backdrop-blur-md rounded-xl p-6 w-full max-w-sm border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Select Agent</h3>
              <button
                onClick={() => setShowAgentSelector(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-3">
              {mobileAgents.map(agent => (
                <button
                  key={agent.id}
                  onClick={() => {
                    setSelectedAgent(agent.id);
                    setShowAgentSelector(false);
                  }}
                  className={`w-full p-3 rounded-lg border transition-all duration-200 ${
                    selectedAgent === agent.id
                      ? 'bg-blue-500/20 border-blue-400/50'
                      : 'bg-white/5 border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full ${agent.color} flex items-center justify-center text-lg`}>
                      {agent.avatar}
                    </div>
                    <div className="text-left">
                      <div className="text-white font-medium">{agent.name}</div>
                      <div className="text-gray-300 text-sm">{agent.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center p-4">
          <div className="bg-black/80 backdrop-blur-md rounded-xl p-6 w-full max-w-sm border border-white/20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Settings</h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-white">Voice Input</span>
                <button className="w-12 h-6 bg-gray-600 rounded-full relative">
                  <div className="w-5 h-5 bg-white rounded-full absolute top-0.5 left-0.5 transition-transform" />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-white">Auto-scroll</span>
                <button className="w-12 h-6 bg-blue-500 rounded-full relative">
                  <div className="w-5 h-5 bg-white rounded-full absolute top-0.5 right-0.5 transition-transform" />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-white">Notifications</span>
                <button className="w-12 h-6 bg-blue-500 rounded-full relative">
                  <div className="w-5 h-5 bg-white rounded-full absolute top-0.5 right-0.5 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map(message => (
          <MobileMessage key={message.id} message={message} />
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center text-sm">
              🤖
            </div>
            <div className="bg-white/10 border border-white/20 rounded-2xl p-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
                <span className="text-gray-400 text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={action.action}
              className="flex-shrink-0 bg-white/10 hover:bg-white/20 px-3 py-2 rounded-full text-white text-sm transition-colors"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-black/20 backdrop-blur-md border-t border-white/10 p-4">
        <div className="flex items-end gap-3">
          {/* Attachment button */}
          <button className="text-gray-400 hover:text-white transition-colors p-2">
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="w-full bg-white/10 border border-white/20 rounded-2xl px-4 py-3 text-white placeholder-gray-400 resize-none min-h-[44px] max-h-32"
              rows={1}
            />
          </div>

          {/* Voice/Send button */}
          <button
            onClick={inputMessage.trim() ? handleSendMessage : () => setIsRecording(!isRecording)}
            disabled={chatLoading}
            className={`p-3 rounded-full transition-colors ${
              inputMessage.trim()
                ? 'bg-blue-500 hover:bg-blue-600 text-white'
                : isRecording
                ? 'bg-red-500 text-white'
                : 'bg-white/10 text-gray-400 hover:text-white'
            }`}
          >
            {chatLoading ? (
              <Loader className="w-5 h-5 animate-spin" />
            ) : inputMessage.trim() ? (
              <Send className="w-5 h-5" />
            ) : isRecording ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MobileAIChatInterface;