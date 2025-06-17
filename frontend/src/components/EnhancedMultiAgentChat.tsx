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
  FastForward, Rewind, SkipBack, SkipForward,
  Network, Workflow, GitBranch, Layers, Target,
  Lightbulb, Sparkles, Rocket, Gauge, Timer
} from 'lucide-react';

// Import our existing hooks
import { useChat } from '../hooks/useApi';
import { useChatWebSocket } from '../hooks/useWebSocket';

// Enhanced types for multi-agent chat
interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agentId?: string;
  agentName?: string;
  agentType?: 'memory' | 'parallel' | 'creative' | 'code' | 'general';
  timestamp: Date;
  type: 'text' | 'code' | 'image' | 'file' | 'system' | 'workflow' | 'collaboration';
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
    engineUsed?: string[];
    collaborationId?: string;
    workflowStep?: number;
    totalSteps?: number;
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
  status: 'online' | 'busy' | 'offline' | 'processing';
  avatar: string;
  description: string;
  capabilities: string[];
  isActive: boolean;
  responseTime: number;
  accuracy: number;
  totalInteractions: number;
  currentLoad?: number;
  specialization?: string[];
}

interface ChatMode {
  id: 'single' | 'multi' | 'collaborative';
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  features: string[];
  engineUsage: string[];
}

interface EnhancedMultiAgentChatProps {
  isFullscreen?: boolean;
  leftSidebarOpen?: boolean;
  rightSidebarOpen?: boolean;
}

const EnhancedMultiAgentChat: React.FC<EnhancedMultiAgentChatProps> = ({
  isFullscreen = false,
  leftSidebarOpen = true,
  rightSidebarOpen = true
}) => {
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>(['general-assistant']);
  const [isRecording, setIsRecording] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [chatMode, setChatMode] = useState<'single' | 'multi' | 'collaborative'>('single');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'text' | 'code' | 'files'>('all');
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [currentThread, setCurrentThread] = useState<string | null>(null);
  const [showAgentMetrics, setShowAgentMetrics] = useState(false);
  const [collaborationSession, setCollaborationSession] = useState<string | null>(null);
  const [workflowActive, setWorkflowActive] = useState(false);
  const [currentWorkflowStep, setCurrentWorkflowStep] = useState(0);

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

  // Chat modes configuration
  const chatModes: ChatMode[] = [
    {
      id: 'single',
      name: 'Single Agent',
      description: 'One-on-one conversation with a specialized AI agent',
      icon: Bot,
      features: [
        'Direct agent communication',
        'Focused expertise',
        'Fast response times',
        'Specialized knowledge'
      ],
      engineUsage: ['Selected agent engine only']
    },
    {
      id: 'multi',
      name: 'Multi Agent',
      description: 'Multiple agents collaborate to solve complex problems',
      icon: Users,
      features: [
        'Agent collaboration',
        'Diverse perspectives',
        'Parallel processing',
        'Comprehensive solutions'
      ],
      engineUsage: ['Memory Engine', 'Parallel Engine', 'Creative Engine']
    },
    {
      id: 'collaborative',
      name: 'Collaborative',
      description: 'Advanced collaborative mode with shared context and memory',
      icon: Network,
      features: [
        'Shared memory context',
        'Real-time collaboration',
        'Workflow orchestration',
        'Cross-agent learning'
      ],
      engineUsage: ['All Three Engines', 'Shared Memory', 'Workflow Engine']
    }
  ];

  // Available agents with enhanced metadata - 20+ specialized agents
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
      totalInteractions: 15847,
      currentLoad: 23,
      specialization: ['General Tasks', 'Planning', 'Research']
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
      totalInteractions: 89234,
      currentLoad: 67,
      specialization: ['Knowledge Management', 'Memory Retrieval', 'Learning']
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
      totalInteractions: 45621,
      currentLoad: 45,
      specialization: ['Parallel Computing', 'Performance', 'Optimization']
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
      totalInteractions: 23456,
      currentLoad: 34,
      specialization: ['Creative Thinking', 'Innovation', 'Design']
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
      totalInteractions: 67890,
      currentLoad: 56,
      specialization: ['Code Analysis', 'Debugging', 'Development']
    },
    {
      id: 'debug-detective',
      name: 'Debug Detective',
      type: 'code',
      status: 'busy',
      avatar: '🔍',
      description: 'Specialized in finding and fixing bugs',
      capabilities: ['Bug Detection', 'Error Analysis', 'Performance Debugging', 'Security Auditing'],
      isActive: true,
      responseTime: 0.9,
      accuracy: 98.1,
      totalInteractions: 34567,
      currentLoad: 89,
      specialization: ['Bug Detection', 'Error Analysis', 'Security']
    },
    {
      id: 'workflow-manager',
      name: 'Workflow Manager',
      type: 'general',
      status: 'online',
      avatar: '📋',
      description: 'Manages complex workflows and task coordination',
      capabilities: ['Task Management', 'Workflow Design', 'Process Optimization', 'Team Coordination'],
      isActive: true,
      responseTime: 0.7,
      accuracy: 95.3,
      totalInteractions: 12345,
      currentLoad: 12,
      specialization: ['Workflow Design', 'Task Management', 'Coordination']
    },
    {
      id: 'data-analyst',
      name: 'Data Analyst',
      type: 'general',
      status: 'online',
      avatar: '📊',
      description: 'Advanced data analysis and visualization expert',
      capabilities: ['Data Mining', 'Statistical Analysis', 'Visualization', 'Reporting'],
      isActive: true,
      responseTime: 1.1,
      accuracy: 96.8,
      totalInteractions: 28934,
      currentLoad: 42,
      specialization: ['Data Science', 'Analytics', 'Visualization']
    },
    {
      id: 'security-expert',
      name: 'Security Expert',
      type: 'code',
      status: 'online',
      avatar: '🛡️',
      description: 'Cybersecurity and vulnerability assessment specialist',
      capabilities: ['Security Auditing', 'Penetration Testing', 'Compliance', 'Risk Assessment'],
      isActive: true,
      responseTime: 0.9,
      accuracy: 97.5,
      totalInteractions: 19876,
      currentLoad: 38,
      specialization: ['Cybersecurity', 'Compliance', 'Risk Management']
    },
    {
      id: 'devops-engineer',
      name: 'DevOps Engineer',
      type: 'code',
      status: 'online',
      avatar: '🔧',
      description: 'Infrastructure automation and deployment specialist',
      capabilities: ['CI/CD', 'Infrastructure as Code', 'Monitoring', 'Automation'],
      isActive: true,
      responseTime: 0.8,
      accuracy: 95.9,
      totalInteractions: 31245,
      currentLoad: 51,
      specialization: ['DevOps', 'Automation', 'Infrastructure']
    },
    {
      id: 'ui-ux-designer',
      name: 'UI/UX Designer',
      type: 'creative',
      status: 'online',
      avatar: '🎯',
      description: 'User interface and experience design expert',
      capabilities: ['UI Design', 'UX Research', 'Prototyping', 'User Testing'],
      isActive: true,
      responseTime: 1.3,
      accuracy: 94.7,
      totalInteractions: 22156,
      currentLoad: 29,
      specialization: ['UI Design', 'UX Research', 'Prototyping']
    },
    {
      id: 'ml-engineer',
      name: 'ML Engineer',
      type: 'parallel',
      status: 'online',
      avatar: '🤖',
      description: 'Machine learning and AI model development specialist',
      capabilities: ['Model Training', 'Feature Engineering', 'MLOps', 'Model Optimization'],
      isActive: true,
      responseTime: 1.5,
      accuracy: 97.2,
      totalInteractions: 18743,
      currentLoad: 63,
      specialization: ['Machine Learning', 'AI Models', 'MLOps']
    },
    {
      id: 'content-writer',
      name: 'Content Writer',
      type: 'creative',
      status: 'online',
      avatar: '✍️',
      description: 'Professional content creation and copywriting expert',
      capabilities: ['Content Strategy', 'SEO Writing', 'Copywriting', 'Editorial'],
      isActive: true,
      responseTime: 1.0,
      accuracy: 93.8,
      totalInteractions: 35672,
      currentLoad: 27,
      specialization: ['Content Creation', 'SEO', 'Copywriting']
    },
    {
      id: 'project-manager',
      name: 'Project Manager',
      type: 'general',
      status: 'online',
      avatar: '📈',
      description: 'Agile project management and team coordination expert',
      capabilities: ['Agile Methodology', 'Resource Planning', 'Risk Management', 'Stakeholder Communication'],
      isActive: true,
      responseTime: 0.9,
      accuracy: 95.1,
      totalInteractions: 24589,
      currentLoad: 35,
      specialization: ['Project Management', 'Agile', 'Team Leadership']
    },
    {
      id: 'api-architect',
      name: 'API Architect',
      type: 'code',
      status: 'online',
      avatar: '🔗',
      description: 'RESTful API design and microservices architecture expert',
      capabilities: ['API Design', 'Microservices', 'Documentation', 'Integration'],
      isActive: true,
      responseTime: 0.7,
      accuracy: 96.4,
      totalInteractions: 16834,
      currentLoad: 44,
      specialization: ['API Design', 'Microservices', 'Integration']
    },
    {
      id: 'database-admin',
      name: 'Database Admin',
      type: 'code',
      status: 'online',
      avatar: '🗄️',
      description: 'Database optimization and management specialist',
      capabilities: ['Query Optimization', 'Database Design', 'Performance Tuning', 'Backup & Recovery'],
      isActive: true,
      responseTime: 0.6,
      accuracy: 97.8,
      totalInteractions: 21456,
      currentLoad: 58,
      specialization: ['Database Management', 'Performance', 'Optimization']
    },
    {
      id: 'cloud-architect',
      name: 'Cloud Architect',
      type: 'code',
      status: 'online',
      avatar: '☁️',
      description: 'Cloud infrastructure and scalability expert',
      capabilities: ['Cloud Design', 'Scalability', 'Cost Optimization', 'Multi-cloud Strategy'],
      isActive: true,
      responseTime: 1.0,
      accuracy: 96.1,
      totalInteractions: 19234,
      currentLoad: 41,
      specialization: ['Cloud Architecture', 'Scalability', 'Cost Optimization']
    },
    {
      id: 'qa-engineer',
      name: 'QA Engineer',
      type: 'code',
      status: 'online',
      avatar: '🧪',
      description: 'Quality assurance and automated testing specialist',
      capabilities: ['Test Automation', 'Quality Assurance', 'Performance Testing', 'Test Strategy'],
      isActive: true,
      responseTime: 0.8,
      accuracy: 95.6,
      totalInteractions: 27891,
      currentLoad: 33,
      specialization: ['Quality Assurance', 'Test Automation', 'Performance Testing']
    },
    {
      id: 'business-analyst',
      name: 'Business Analyst',
      type: 'general',
      status: 'online',
      avatar: '💼',
      description: 'Business requirements and process optimization expert',
      capabilities: ['Requirements Analysis', 'Process Mapping', 'Business Intelligence', 'Stakeholder Management'],
      isActive: true,
      responseTime: 1.1,
      accuracy: 94.3,
      totalInteractions: 22567,
      currentLoad: 31,
      specialization: ['Business Analysis', 'Process Optimization', 'Requirements']
    },
    {
      id: 'technical-writer',
      name: 'Technical Writer',
      type: 'creative',
      status: 'online',
      avatar: '📝',
      description: 'Technical documentation and API documentation specialist',
      capabilities: ['Technical Documentation', 'API Docs', 'User Guides', 'Knowledge Base'],
      isActive: true,
      responseTime: 1.2,
      accuracy: 93.9,
      totalInteractions: 18456,
      currentLoad: 26,
      specialization: ['Technical Writing', 'Documentation', 'Knowledge Management']
    },
    {
      id: 'performance-optimizer',
      name: 'Performance Optimizer',
      type: 'parallel',
      status: 'online',
      avatar: '⚡',
      description: 'Application performance and optimization specialist',
      capabilities: ['Performance Analysis', 'Code Optimization', 'Profiling', 'Benchmarking'],
      isActive: true,
      responseTime: 0.5,
      accuracy: 97.6,
      totalInteractions: 15234,
      currentLoad: 52,
      specialization: ['Performance Optimization', 'Profiling', 'Benchmarking']
    },
    {
      id: 'integration-specialist',
      name: 'Integration Specialist',
      type: 'code',
      status: 'online',
      avatar: '🔄',
      description: 'System integration and middleware expert',
      capabilities: ['System Integration', 'Middleware', 'Data Migration', 'Legacy Systems'],
      isActive: true,
      responseTime: 0.9,
      accuracy: 95.8,
      totalInteractions: 13789,
      currentLoad: 39,
      specialization: ['System Integration', 'Middleware', 'Data Migration']
    },
    {
      id: 'mobile-developer',
      name: 'Mobile Developer',
      type: 'code',
      status: 'online',
      avatar: '📱',
      description: 'Cross-platform mobile application development expert',
      capabilities: ['React Native', 'Flutter', 'iOS Development', 'Android Development'],
      isActive: true,
      responseTime: 1.0,
      accuracy: 94.5,
      totalInteractions: 20123,
      currentLoad: 47,
      specialization: ['Mobile Development', 'Cross-platform', 'App Store Optimization']
    },
    {
      id: 'blockchain-expert',
      name: 'Blockchain Expert',
      type: 'code',
      status: 'online',
      avatar: '⛓️',
      description: 'Blockchain and smart contract development specialist',
      capabilities: ['Smart Contracts', 'DeFi', 'Web3', 'Cryptocurrency'],
      isActive: true,
      responseTime: 1.4,
      accuracy: 93.2,
      totalInteractions: 8945,
      currentLoad: 28,
      specialization: ['Blockchain', 'Smart Contracts', 'Web3']
    },
    {
      id: 'ai-researcher',
      name: 'AI Researcher',
      type: 'memory',
      status: 'online',
      avatar: '🔬',
      description: 'Artificial intelligence research and development specialist',
      capabilities: ['AI Research', 'Neural Networks', 'Deep Learning', 'Computer Vision'],
      isActive: true,
      responseTime: 1.8,
      accuracy: 98.5,
      totalInteractions: 12456,
      currentLoad: 71,
      specialization: ['AI Research', 'Neural Networks', 'Computer Vision']
    }
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  // Handle chat mode changes and agent selection
  useEffect(() => {
    switch (chatMode) {
      case 'single':
        // Single agent mode - user selects one agent
        if (selectedAgents.length > 1) {
          setSelectedAgents([selectedAgents[0]]);
        }
        break;
      case 'multi':
        // Multi-agent mode - select relevant agents based on task
        if (selectedAgents.length < 2) {
          setSelectedAgents(['memory-engine', 'parallel-processor', 'creative-engine']);
        }
        break;
      case 'collaborative':
        // Collaborative mode - all engines active
        setSelectedAgents(['memory-engine', 'parallel-processor', 'creative-engine', 'workflow-manager']);
        setCollaborationSession(`collab-${Date.now()}`);
        break;
    }
  }, [chatMode]);

  // Handle message sending with different workflows
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
      type: 'text',
      metadata: {
        collaborationId: collaborationSession || undefined
      }
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      // Different processing based on chat mode
      switch (chatMode) {
        case 'single':
          await handleSingleAgentResponse(userMessage);
          break;
        case 'multi':
          await handleMultiAgentResponse(userMessage);
          break;
        case 'collaborative':
          await handleCollaborativeResponse(userMessage);
          break;
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  }, [inputMessage, chatMode, selectedAgents, collaborationSession]);

  // Single agent response handler
  const handleSingleAgentResponse = async (userMessage: ChatMessage) => {
    const selectedAgent = availableAgents.find(agent => agent.id === selectedAgents[0]);
    if (!selectedAgent) return;

    // Simulate agent processing
    setTimeout(() => {
      const agentResponse: ChatMessage = {
        id: `msg-${Date.now()}-agent`,
        content: `[${selectedAgent.name}] I understand your request. Let me help you with that...`,
        sender: 'agent',
        agentId: selectedAgent.id,
        agentName: selectedAgent.name,
        agentType: selectedAgent.type,
        timestamp: new Date(),
        type: 'text',
        metadata: {
          processingTime: selectedAgent.responseTime,
          confidence: selectedAgent.accuracy,
          engineUsed: [selectedAgent.type]
        }
      };

      setMessages(prev => [...prev, agentResponse]);
    }, selectedAgent.responseTime * 1000);
  };

  // Multi-agent response handler
  const handleMultiAgentResponse = async (userMessage: ChatMessage) => {
    // Simulate multiple agents responding in sequence
    const activeAgents = availableAgents.filter(agent => selectedAgents.includes(agent.id));
    
    for (let i = 0; i < activeAgents.length; i++) {
      const agent = activeAgents[i];
      
      setTimeout(() => {
        const agentResponse: ChatMessage = {
          id: `msg-${Date.now()}-${agent.id}`,
          content: `[${agent.name}] From my ${agent.type} perspective: ${getAgentSpecificResponse(agent, userMessage.content)}`,
          sender: 'agent',
          agentId: agent.id,
          agentName: agent.name,
          agentType: agent.type,
          timestamp: new Date(),
          type: 'text',
          metadata: {
            processingTime: agent.responseTime,
            confidence: agent.accuracy,
            engineUsed: [agent.type],
            workflowStep: i + 1,
            totalSteps: activeAgents.length
          }
        };

        setMessages(prev => [...prev, agentResponse]);
      }, (i + 1) * agent.responseTime * 1000);
    }
  };

  // Collaborative response handler
  const handleCollaborativeResponse = async (userMessage: ChatMessage) => {
    setWorkflowActive(true);
    setCurrentWorkflowStep(0);

    // Simulate collaborative workflow
    const workflow = [
      { agent: 'memory-engine', action: 'Retrieving relevant knowledge...' },
      { agent: 'parallel-processor', action: 'Processing multiple approaches...' },
      { agent: 'creative-engine', action: 'Generating innovative solutions...' },
      { agent: 'workflow-manager', action: 'Coordinating final response...' }
    ];

    for (let i = 0; i < workflow.length; i++) {
      const step = workflow[i];
      const agent = availableAgents.find(a => a.id === step.agent);
      
      setTimeout(() => {
        setCurrentWorkflowStep(i + 1);
        
        const workflowMessage: ChatMessage = {
          id: `msg-${Date.now()}-workflow-${i}`,
          content: `[${agent?.name}] ${step.action}`,
          sender: 'agent',
          agentId: agent?.id,
          agentName: agent?.name,
          agentType: agent?.type,
          timestamp: new Date(),
          type: 'workflow',
          metadata: {
            processingTime: agent?.responseTime || 0.5,
            confidence: agent?.accuracy || 95,
            engineUsed: ['memory', 'parallel', 'creative'],
            collaborationId: collaborationSession || undefined,
            workflowStep: i + 1,
            totalSteps: workflow.length
          }
        };

        setMessages(prev => [...prev, workflowMessage]);

        // Final collaborative response
        if (i === workflow.length - 1) {
          setTimeout(() => {
            const finalResponse: ChatMessage = {
              id: `msg-${Date.now()}-collaborative`,
              content: `[Collaborative Response] Based on our three-engine analysis:\n\n🧠 Memory Engine found relevant patterns\n⚡ Parallel Processor optimized the approach\n🎨 Creative Engine added innovative elements\n📋 Workflow Manager coordinated the solution\n\nHere's our comprehensive response...`,
              sender: 'agent',
              agentId: 'collaborative-system',
              agentName: 'Collaborative System',
              agentType: 'general',
              timestamp: new Date(),
              type: 'collaboration',
              metadata: {
                processingTime: 2.5,
                confidence: 98.5,
                engineUsed: ['memory', 'parallel', 'creative'],
                collaborationId: collaborationSession || undefined
              }
            };

            setMessages(prev => [...prev, finalResponse]);
            setWorkflowActive(false);
            setCurrentWorkflowStep(0);
          }, 1000);
        }
      }, (i + 1) * 1500);
    }
  };

  // Get agent-specific response based on their specialization
  const getAgentSpecificResponse = (agent: Agent, userInput: string) => {
    switch (agent.type) {
      case 'memory':
        return 'I can recall relevant information and patterns from our knowledge base...';
      case 'parallel':
        return 'I can process this efficiently using parallel computing approaches...';
      case 'creative':
        return 'Let me think of innovative and creative solutions for this...';
      case 'code':
        return 'From a technical perspective, here\'s how we can implement this...';
      default:
        return 'I can help you with this task using my general capabilities...';
    }
  };

  // Chat Mode Selector
  const ChatModeSelector = () => (
    <div className="p-4 border-b border-white/10">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-blue-400" />
          AI Chat Hub
        </h3>
        <button
          onClick={() => setSettingsOpen(!settingsOpen)}
          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          <Settings className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Chat Mode Dropdown */}
      <div className="relative">
        <select
          value={chatMode}
          onChange={(e) => setChatMode(e.target.value as 'single' | 'multi' | 'collaborative')}
          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-blue-400 appearance-none cursor-pointer"
        >
          {chatModes.map((mode) => (
            <option key={mode.id} value={mode.id} className="bg-gray-800 text-white">
              {mode.name} - {mode.description}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
      </div>

      {/* Mode Description */}
      <div className="mt-3 p-3 bg-white/5 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          {React.createElement(chatModes.find(m => m.id === chatMode)?.icon || Bot, { 
            className: "w-5 h-5 text-blue-400" 
          })}
          <span className="font-medium text-white">
            {chatModes.find(m => m.id === chatMode)?.name}
          </span>
        </div>
        <p className="text-sm text-gray-300 mb-2">
          {chatModes.find(m => m.id === chatMode)?.description}
        </p>
        
        {/* Features */}
        <div className="space-y-1">
          <div className="text-xs text-gray-400">Features:</div>
          {chatModes.find(m => m.id === chatMode)?.features.map((feature, index) => (
            <div key={index} className="text-xs text-gray-300 flex items-center gap-1">
              <CheckCircle className="w-3 h-3 text-green-400" />
              {feature}
            </div>
          ))}
        </div>

        {/* Engine Usage */}
        <div className="mt-2 space-y-1">
          <div className="text-xs text-gray-400">Engine Usage:</div>
          {chatModes.find(m => m.id === chatMode)?.engineUsage.map((engine, index) => (
            <div key={index} className="text-xs text-blue-300 flex items-center gap-1">
              <Cpu className="w-3 h-3 text-blue-400" />
              {engine}
            </div>
          ))}
        </div>
      </div>

      {/* Workflow Status (for collaborative mode) */}
      {chatMode === 'collaborative' && workflowActive && (
        <div className="mt-3 p-3 bg-purple-500/20 border border-purple-400/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Workflow className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium text-white">Collaborative Workflow Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentWorkflowStep / 4) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-300">{currentWorkflowStep}/4</span>
          </div>
        </div>
      )}
    </div>
  );

  // Agent Selection Panel
  const AgentSelectionPanel = () => (
    <div className="p-4 border-b border-white/10">
      <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
        <Users className="w-4 h-4 text-green-400" />
        Available Agents ({availableAgents.length}) | Selected ({selectedAgents.length})
      </h4>
      
      <div className="space-y-2 max-h-60 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
        {availableAgents.map((agent) => {
          const isSelected = selectedAgents.includes(agent.id);
          const canSelect = chatMode === 'single' ? selectedAgents.length === 0 || isSelected : true;
          
          return (
            <div
              key={agent.id}
              className={`
                p-2 rounded-lg border transition-all duration-200 cursor-pointer
                ${isSelected 
                  ? 'bg-blue-500/20 border-blue-400/30 text-white' 
                  : canSelect 
                    ? 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/20' 
                    : 'bg-gray-500/10 border-gray-500/20 text-gray-500 cursor-not-allowed'
                }
              `}
              onClick={() => {
                if (!canSelect) return;
                
                if (chatMode === 'single') {
                  setSelectedAgents(isSelected ? [] : [agent.id]);
                } else {
                  setSelectedAgents(prev => 
                    isSelected 
                      ? prev.filter(id => id !== agent.id)
                      : [...prev, agent.id]
                  );
                }
              }}
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">{agent.avatar}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{agent.name}</span>
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'online' ? 'bg-green-400' :
                      agent.status === 'busy' ? 'bg-yellow-400' :
                      agent.status === 'processing' ? 'bg-blue-400' : 'bg-red-400'
                    }`} />
                  </div>
                  <div className="text-xs text-gray-400 truncate">{agent.description}</div>
                  {agent.currentLoad !== undefined && (
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-full bg-gray-700 rounded-full h-1">
                        <div 
                          className={`h-1 rounded-full transition-all duration-300 ${
                            agent.currentLoad > 80 ? 'bg-red-400' :
                            agent.currentLoad > 60 ? 'bg-yellow-400' : 'bg-green-400'
                          }`}
                          style={{ width: `${agent.currentLoad}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{agent.currentLoad}%</span>
                    </div>
                  )}
                </div>
                {isSelected && <CheckCircle className="w-4 h-4 text-blue-400" />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Message Component
  const MessageComponent = ({ message }: { message: ChatMessage }) => (
    <div className={`flex gap-3 p-4 ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
        message.sender === 'user' 
          ? 'bg-blue-500 text-white' 
          : message.agentType === 'memory' ? 'bg-purple-500 text-white'
          : message.agentType === 'parallel' ? 'bg-yellow-500 text-white'
          : message.agentType === 'creative' ? 'bg-pink-500 text-white'
          : message.agentType === 'code' ? 'bg-green-500 text-white'
          : 'bg-gray-500 text-white'
      }`}>
        {message.sender === 'user' ? '👤' : 
         availableAgents.find(a => a.id === message.agentId)?.avatar || '🤖'}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${message.sender === 'user' ? 'text-right' : 'text-left'}`}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          {message.sender === 'user' ? (
            <span className="text-sm font-medium text-blue-300">You</span>
          ) : (
            <>
              <span className="text-sm font-medium text-white">{message.agentName}</span>
              {message.agentType && (
                <span className={`text-xs px-2 py-1 rounded-full ${
                  message.agentType === 'memory' ? 'bg-purple-500/20 text-purple-300' :
                  message.agentType === 'parallel' ? 'bg-yellow-500/20 text-yellow-300' :
                  message.agentType === 'creative' ? 'bg-pink-500/20 text-pink-300' :
                  message.agentType === 'code' ? 'bg-green-500/20 text-green-300' :
                  'bg-gray-500/20 text-gray-300'
                }`}>
                  {message.agentType}
                </span>
              )}
            </>
          )}
          {showTimestamps && (
            <span className="text-xs text-gray-400">
              {message.timestamp.toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Message Body */}
        <div className={`p-3 rounded-lg ${
          message.sender === 'user' 
            ? 'bg-blue-500/20 border border-blue-400/30' 
            : message.type === 'workflow' 
              ? 'bg-purple-500/20 border border-purple-400/30'
              : message.type === 'collaboration'
                ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-400/30'
                : 'bg-white/10 border border-white/20'
        }`}>
          <div className="text-white whitespace-pre-wrap">{message.content}</div>
          
          {/* Metadata */}
          {message.metadata && (
            <div className="mt-2 pt-2 border-t border-white/10 text-xs text-gray-400 space-y-1">
              {message.metadata.processingTime && (
                <div className="flex items-center gap-1">
                  <Timer className="w-3 h-3" />
                  Processing: {message.metadata.processingTime}s
                </div>
              )}
              {message.metadata.confidence && (
                <div className="flex items-center gap-1">
                  <Target className="w-3 h-3" />
                  Confidence: {message.metadata.confidence}%
                </div>
              )}
              {message.metadata.engineUsed && (
                <div className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  Engines: {message.metadata.engineUsed.join(', ')}
                </div>
              )}
              {message.metadata.workflowStep && (
                <div className="flex items-center gap-1">
                  <Workflow className="w-3 h-3" />
                  Step: {message.metadata.workflowStep}/{message.metadata.totalSteps}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Input Area
  const InputArea = () => (
    <div className="p-4 border-t border-white/10 bg-gray-900/50">
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={`Message ${chatMode === 'single' ? 'agent' : 'agents'}...`}
            className="w-full p-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 resize-none min-h-[60px]"
            rows={2}
          />
        </div>
        
        <div className="flex flex-col gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-3 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
            title="Attach file"
          >
            <Paperclip className="w-5 h-5 text-gray-400" />
          </button>
          
          <button
            onClick={() => setIsRecording(!isRecording)}
            className={`p-3 rounded-lg transition-colors ${
              isRecording 
                ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400' 
                : 'bg-white/10 hover:bg-white/20 text-gray-400'
            }`}
            title="Voice input"
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || chatLoading}
            className="p-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed rounded-lg transition-colors"
            title="Send message"
          >
            {chatLoading ? (
              <Loader className="w-5 h-5 text-white animate-spin" />
            ) : (
              <Send className="w-5 h-5 text-white" />
            )}
          </button>
        </div>
      </div>
      
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => {
          // Handle file upload
          console.log('Files selected:', e.target.files);
        }}
      />
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900/50 via-purple-900/50 to-slate-900/50">
      {/* Chat Mode Selector */}
      <ChatModeSelector />
      
      {/* Agent Selection Panel */}
      <AgentSelectionPanel />
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">
                Welcome to {chatModes.find(m => m.id === chatMode)?.name} Mode
              </h3>
              <p className="text-gray-400 max-w-md">
                {chatModes.find(m => m.id === chatMode)?.description}
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((message) => (
              <MessageComponent key={message.id} message={message} />
            ))}
            {isTyping && (
              <div className="flex gap-3 p-4">
                <div className="w-8 h-8 rounded-full bg-gray-500 flex items-center justify-center">
                  <Loader className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="flex-1">
                  <div className="text-sm text-gray-400 mb-1">
                    {chatMode === 'single' ? 'Agent is typing...' : 'Agents are processing...'}
                  </div>
                  <div className="p-3 bg-white/10 rounded-lg border border-white/20">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      {/* Input Area */}
      <InputArea />
    </div>
  );
};

export default EnhancedMultiAgentChat;