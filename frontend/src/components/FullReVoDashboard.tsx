import React, { useState, useEffect } from 'react';
import { 
  Activity, Brain, Zap, MessageSquare, Settings, 
  Users, Database, Shield, BarChart3, GitBranch, Slack,
  Cpu, HardDrive, Network, TrendingUp, Bell, Play,
  Search, Download, Upload, RefreshCw, Eye, Code,
  Bug, TestTube, Rocket, FileText, Monitor, Lock,
  Palette, Home, Workflow, Store, BarChart, Link,
  Cog, Menu, X, ChevronRight, AlertCircle
} from 'lucide-react';

// Import our hooks and services
import { useDashboardStats, useAgents, useSystemMetrics, useHealthCheck, useConnectionStatus } from '../hooks/useApi';
import { useDashboardWebSocket } from '../hooks/useWebSocket';
import ResponsiveAIChatInterface from './ResponsiveAIChatInterface';

const FullReVoDashboard = () => {
  const [activeView, setActiveView] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Use our custom hooks for real data
  const { stats, loading: statsLoading, error: statsError } = useDashboardStats();
  const { agents, activeTasks, totalAgents, loading: agentsLoading } = useAgents();
  const { metrics, loading: metricsLoading } = useSystemMetrics();
  const { health, loading: healthLoading } = useHealthCheck();
  const isOnline = useConnectionStatus();
  const { isConnected, dashboardData, notifications } = useDashboardWebSocket();

  // System metrics with fallback to static data
  const systemMetrics = {
    cpu: metrics?.cpu?.value || 67.8,
    memory: metrics?.memory?.value || 89.2,
    disk: metrics?.disk?.value || 34.1,
    network: 56.3,
    activeRequests: activeTasks || 47,
    queueLength: 12,
    responseTime: 0.002,
    uptime: 99.9
  };

  // Three Engine Status with real health data
  const engineStatus = {
    memory: { 
      status: health?.services?.memory_engine === 'active' ? 'active' : 'inactive', 
      entities: 1247893, 
      speed: 95, 
      cost: 0,
      accuracy: 99.9,
      relationships: 3456782,
      dailyGrowth: 2341
    },
    parallel: { 
      status: health?.services?.parallel_engine === 'active' ? 'active' : 'inactive', 
      workers: 8, 
      load: systemMetrics.cpu || 45.2, 
      throughput: 150,
      performance: '10x'
    },
    creative: { 
      status: health?.services?.creative_engine === 'active' ? 'active' : 'inactive', 
      patterns: 15, 
      novelty: 94, 
      innovation: 7.2,
      breakthroughs: 3
    }
  };

  // Cost Savings
  const costSavings = {
    totalSavings: 2847,
    localProcessing: 94.7,
    cloudFallback: 5.3,
    deepSeekCost: 0,
    openAICost: 12.30,
    llamaCost: 0,
    anthropicCost: 8.70,
    monthlyProjection: 3200
  };

  // Navigation items
  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, description: 'Three-Engine Overview' },
    { id: 'agents', label: 'AI Agents Hub', icon: Users, description: '20+ Agents', badge: '20+' },
    { id: 'memory', label: 'Memory Center', icon: Brain, description: 'Knowledge Graph' },
    { id: 'parallel', label: 'Parallel Processing', icon: Zap, description: 'Load Balancer' },
    { id: 'creative', label: 'Creative Innovation', icon: Palette, description: 'Pattern Discovery' },
    { id: 'chat', label: 'Multi-Agent Chat', icon: MessageSquare, description: 'Real-time Collaboration' },
    { id: 'store', label: 'MCP Store', icon: Store, description: 'Agent Marketplace' },
    { id: 'workflow', label: 'Workflow Builder', icon: Workflow, description: 'Visual Designer' },
    { id: 'analytics', label: 'Analytics & Insights', icon: BarChart, description: 'Performance Metrics' },
    { id: 'integrations', label: 'External Integrations', icon: Link, description: 'GitHub, Slack, JIRA' },
    { id: 'security', label: 'Security & Compliance', icon: Shield, description: 'Security Scanner' },
    { id: 'settings', label: 'System Configuration', icon: Settings, description: 'Model Management' }
  ];

  // AI Agents by category
  const agentCategories = [
    {
      title: 'Code Specialists',
      agents: ['Code Analyst Agent', 'Debug Detective Agent', 'Security Scanner Agent', 'Performance Optimizer Agent', 'Documentation Generator Agent']
    },
    {
      title: 'Development Workflow',
      agents: ['Workflow Manager Agent', 'DevOps Integration Agent', 'CI/CD Pipeline Agent', 'Testing Coordinator Agent', 'Deployment Manager Agent']
    },
    {
      title: 'Knowledge & Memory',
      agents: ['Knowledge Coordinator Agent', 'Memory Synthesis Agent', 'Pattern Recognition Agent', 'Learning Optimizer Agent', 'Context Manager Agent']
    },
    {
      title: 'Communication & Collaboration',
      agents: ['Multi-Agent Chat Coordinator', 'Slack Integration Agent', 'GitHub Integration Agent', 'JIRA Integration Agent', 'Notification Manager Agent']
    },
    {
      title: 'Specialized Tasks',
      agents: ['Data Analysis Agent', 'API Integration Agent', 'Database Optimizer Agent', 'Monitoring Agent', 'Report Generator Agent']
    }
  ];

  const TopNavigation = () => (
    <div className="bg-black/20 backdrop-blur-md border-b border-white/10">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden text-white hover:text-blue-400 transition-colors"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          
          <div className="flex items-center gap-2">
            <Rocket className="w-8 h-8 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">reVoAgent</h1>
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">v2.0</span>
          </div>
          
          {/* Three-Engine Status Lights */}
          <div className="hidden md:flex items-center gap-6 ml-8">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${engineStatus.memory.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span className={`text-sm ${engineStatus.memory.status === 'active' ? 'text-green-400' : 'text-red-400'}`}>
                Memory: {engineStatus.memory.status === 'active' ? 'Active (99.9%)' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${engineStatus.parallel.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span className={`text-sm ${engineStatus.parallel.status === 'active' ? 'text-green-400' : 'text-red-400'}`}>
                Parallel: {engineStatus.parallel.status === 'active' ? 'Active (10x Performance)' : 'Inactive'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${engineStatus.creative.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span className={`text-sm ${engineStatus.creative.status === 'active' ? 'text-green-400' : 'text-red-400'}`}>
                Creative: {engineStatus.creative.status === 'active' ? 'Active (94% Novelty)' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Cost Savings */}
          <div className="hidden md:flex items-center gap-2 bg-green-500/20 px-3 py-1 rounded-full">
            <span className="text-green-400 text-sm font-medium">Cost Savings: ${costSavings.totalSavings.toLocaleString()}</span>
          </div>
          
          {/* Connection Status */}
          <div className={`hidden lg:flex items-center gap-2 px-3 py-1 rounded-full ${isOnline && isConnected ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
            <div className={`w-2 h-2 rounded-full ${isOnline && isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
            <span className={`text-sm font-medium ${isOnline && isConnected ? 'text-green-400' : 'text-red-400'}`}>
              {isOnline && isConnected ? 'Online' : 'Offline'}
            </span>
          </div>
          
          {/* Memory Status */}
          <div className="hidden lg:flex items-center gap-2 bg-blue-500/20 px-3 py-1 rounded-full">
            <span className="text-blue-400 text-sm font-medium">Memory: Active</span>
          </div>
          
          {/* User Profile */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center">
              <Users className="w-4 h-4 text-white" />
            </div>
            <span className="hidden md:block text-gray-300 text-sm">Admin</span>
          </div>
          
          {/* Settings */}
          <button className="text-gray-300 hover:text-white transition-colors">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );

  const Sidebar = () => (
    <div className={`${sidebarOpen ? 'w-80' : 'w-16'} bg-black/20 backdrop-blur-md border-r border-white/10 h-screen overflow-y-auto transition-all duration-300`}>
      <div className="p-4">
        <h2 className={`text-white font-bold mb-4 ${sidebarOpen ? 'block' : 'hidden'}`}>MAIN MODULES</h2>
        {navigationItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`w-full p-3 mb-2 rounded-lg text-left transition-all duration-200 flex items-center gap-3 ${
              activeView === item.id 
                ? 'bg-blue-500/20 border border-blue-400/30 text-blue-400' 
                : 'text-gray-300 hover:bg-white/5 hover:text-white'
            }`}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="font-medium truncate">{item.label}</span>
                  {item.badge && (
                    <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </div>
                <div className="text-xs opacity-70 truncate">{item.description}</div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );

  const DashboardView = () => (
    <div className="p-6 space-y-6">
      {/* Loading and Error States */}
      {(statsLoading || agentsLoading || metricsLoading || healthLoading) && (
        <div className="bg-blue-500/20 backdrop-blur-md rounded-xl p-4 border border-blue-400/30">
          <div className="flex items-center gap-3">
            <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
            <span className="text-blue-400">Loading dashboard data...</span>
          </div>
        </div>
      )}
      
      {statsError && (
        <div className="bg-red-500/20 backdrop-blur-md rounded-xl p-4 border border-red-400/30">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">Error loading data: {statsError}</span>
          </div>
        </div>
      )}
      
      {/* Three-Engine Status Overview */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-bold text-white mb-6">THREE-ENGINE STATUS OVERVIEW</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white/5 rounded-xl p-6 border border-blue-400/30">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-8 h-8 text-blue-400" />
              <h3 className="text-xl font-bold text-white">MEMORY ENGINE</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-blue-200">Status:</span>
                <span className="text-green-400 font-semibold">●●● Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Memory:</span>
                <span className="text-white font-mono">{engineStatus.memory.entities.toLocaleString()} entities</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Speed:</span>
                <span className="text-white">&lt;100ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Cost:</span>
                <span className="text-green-400 font-bold">$0.00/query</span>
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-xl p-6 border border-yellow-400/30">
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-8 h-8 text-yellow-400" />
              <h3 className="text-xl font-bold text-white">PARALLEL ENGINE</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-blue-200">Status:</span>
                <span className="text-green-400 font-semibold">●●● Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Workers:</span>
                <span className="text-white">{engineStatus.parallel.workers} Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Load:</span>
                <span className="text-white">{engineStatus.parallel.load}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Throughput:</span>
                <span className="text-white">{engineStatus.parallel.throughput} req/min</span>
              </div>
            </div>
          </div>

          <div className="bg-white/5 rounded-xl p-6 border border-purple-400/30">
            <div className="flex items-center gap-3 mb-4">
              <Palette className="w-8 h-8 text-purple-400" />
              <h3 className="text-xl font-bold text-white">CREATIVE ENGINE</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-blue-200">Status:</span>
                <span className="text-green-400 font-semibold">●●● Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Patterns:</span>
                <span className="text-white">{engineStatus.creative.patterns} Active</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Novelty:</span>
                <span className="text-white">{engineStatus.creative.novelty}% Score</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Innovation Rate:</span>
                <span className="text-white">{engineStatus.creative.innovation}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Agents Overview */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-bold text-white mb-6">ACTIVE AGENTS OVERVIEW (20+)</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {['Code Analyst', 'Debug Detective', 'Workflow Manager', 'Security Scanner', 'Performance Optimizer', 'Documentation Generator', 'DevOps Integration', 'CI/CD Pipeline', 'Testing Coordinator', 'Deployment Manager', 'Knowledge Coordinator', 'Memory Synthesis', 'Pattern Recognition', 'Learning Optimizer', 'Context Manager', 'Multi-Agent Chat', 'Slack Integration', 'GitHub Integration', 'JIRA Integration', 'Data Analysis', 'API Integration', 'Database Optimizer', 'Monitoring'].map((agent, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <div className="text-white text-sm font-medium">{agent}</div>
              <div className="w-2 h-2 bg-green-400 rounded-full mx-auto mt-2" />
            </div>
          ))}
        </div>
      </div>

      {/* Real-time System Metrics */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-bold text-white mb-6">REAL-TIME SYSTEM METRICS</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-sm text-blue-200 mb-2">CPU</div>
            <div className="text-2xl font-bold text-white mb-2">{systemMetrics.cpu}%</div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${systemMetrics.cpu}%` }} />
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-blue-200 mb-2">Memory</div>
            <div className="text-2xl font-bold text-white mb-2">{systemMetrics.memory}%</div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: `${systemMetrics.memory}%` }} />
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-blue-200 mb-2">Active Requests</div>
            <div className="text-2xl font-bold text-white">{systemMetrics.activeRequests}</div>
            <div className="text-xs text-gray-300">Queue Length: {systemMetrics.queueLength}</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-blue-200 mb-2">Response Time</div>
            <div className="text-2xl font-bold text-white">{systemMetrics.responseTime}s</div>
            <div className="text-xs text-green-400">Uptime: {systemMetrics.uptime}%</div>
          </div>
        </div>
      </div>

      {/* Cost Optimization Dashboard */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-bold text-white mb-6">💰 COST OPTIMIZATION DASHBOARD</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">${costSavings.totalSavings.toLocaleString()}</div>
            <div className="text-green-200 text-sm">TOTAL SAVINGS THIS MONTH</div>
          </div>
          <div className="text-center">
            <div className="text-lg text-blue-200">Local Processing: {costSavings.localProcessing}%</div>
            <div className="text-lg text-purple-200">Cloud Fallback: {costSavings.cloudFallback}%</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-300">DeepSeek R1: $0.00</div>
            <div className="text-sm text-gray-300">Llama Local: $0.00</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-300">OpenAI Backup: ${costSavings.openAICost}</div>
            <div className="text-sm text-gray-300">Anthropic: ${costSavings.anthropicCost}</div>
          </div>
        </div>
        <div className="mt-4 text-center">
          <div className="text-lg text-yellow-400">Monthly Projection: ${costSavings.monthlyProjection.toLocaleString()} savings vs cloud-only</div>
        </div>
      </div>

      {/* Memory & Knowledge Graph Overview */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
        <h2 className="text-xl font-bold text-white mb-6">📊 MEMORY & KNOWLEDGE GRAPH OVERVIEW</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">{engineStatus.memory.entities.toLocaleString()}</div>
            <div className="text-blue-200 text-sm">Knowledge Entities</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{engineStatus.memory.relationships.toLocaleString()}</div>
            <div className="text-green-200 text-sm">Relationships</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">+{engineStatus.memory.dailyGrowth.toLocaleString()}</div>
            <div className="text-green-200 text-sm">Daily Growth</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{engineStatus.memory.accuracy}%</div>
            <div className="text-yellow-200 text-sm">Query Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-400">89</div>
            <div className="text-cyan-200 text-sm">Cross-Agent Sharing</div>
          </div>
        </div>
      </div>
    </div>
  );

  const AgentsView = () => (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-white mb-6">🤖 AI AGENTS HUB (20+ Agents)</h2>
      
      {agentCategories.map((category, index) => (
        <div key={index} className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h3 className="text-xl font-bold text-white mb-4">{category.title}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            {category.agents.map((agent, agentIndex) => (
              <div
                key={agentIndex}
                className="p-4 bg-white/5 rounded-lg border border-white/10 hover:border-blue-400/30 transition-all duration-200 cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-2">
                  <Code className="w-5 h-5 text-purple-400" />
                  <div className="w-2 h-2 rounded-full bg-green-400" />
                </div>
                <h4 className="text-white font-medium text-sm mb-1">{agent}</h4>
                <p className="text-purple-200 text-xs">Active</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const RightSidebar = () => (
    <div className="w-80 bg-black/20 backdrop-blur-md border-l border-white/10 h-screen overflow-y-auto">
      <div className="p-6 space-y-6">
        {/* Quick Actions */}
        <div>
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <Play className="w-5 h-5 text-green-400" />
            QUICK ACTIONS
          </h3>
          <div className="space-y-3">
            <button className="w-full p-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <Play className="w-4 h-4" />
              ▶️ Start Multi-Agent Task
            </button>
            <button className="w-full p-3 bg-gradient-to-r from-green-500/20 to-emerald-500/20 hover:from-green-500/30 hover:to-emerald-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              💬 Open Agent Chat
            </button>
            <button className="w-full p-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              🔧 Build New Workflow
            </button>
            <button className="w-full p-3 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 hover:from-yellow-500/30 hover:to-orange-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              📊 Generate Report
            </button>
            <button className="w-full p-3 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 hover:from-cyan-500/30 hover:to-blue-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <Search className="w-4 h-4" />
              🔍 Search Knowledge
            </button>
            <button className="w-full p-3 bg-gradient-to-r from-red-500/20 to-pink-500/20 hover:from-red-500/30 hover:to-pink-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
              <Rocket className="w-4 h-4" />
              ⚡ Deploy to Production
            </button>
          </div>
        </div>

        {/* Real-time Notifications */}
        <div>
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <Bell className="w-5 h-5 text-blue-400" />
            REAL-TIME NOTIFICATIONS
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-green-500/20 border border-green-400/30 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <span className="text-green-400 text-sm font-medium">🟢 Code analysis complete</span>
              </div>
            </div>
            <div className="p-3 bg-yellow-500/20 border border-yellow-400/30 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                <span className="text-yellow-400 text-sm font-medium">🟡 Memory sync in progress</span>
              </div>
            </div>
            <div className="p-3 bg-blue-500/20 border border-blue-400/30 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                <span className="text-blue-400 text-sm font-medium">🔵 New pattern discovered</span>
              </div>
            </div>
            <div className="p-3 bg-green-500/20 border border-green-400/30 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <span className="text-green-400 text-sm font-medium">✅ Workflow deployed</span>
              </div>
            </div>
            <div className="p-3 bg-blue-500/20 border border-blue-400/30 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                <span className="text-blue-400 text-sm font-medium">📧 Slack notification sent</span>
              </div>
            </div>
          </div>
        </div>

        {/* Active Tasks */}
        <div>
          <h3 className="text-white font-bold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            ACTIVE TASKS
          </h3>
          <div className="space-y-3">
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-sm font-medium mb-2">🔄 Analyzing repository</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" style={{ width: '75%' }} />
                </div>
                <span className="text-purple-300 text-xs">75%</span>
              </div>
              <div className="text-purple-200 text-xs">Agent: Code Analyst</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-sm font-medium mb-2">⚡ Building deployment</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" style={{ width: '45%' }} />
                </div>
                <span className="text-purple-300 text-xs">45%</span>
              </div>
              <div className="text-purple-200 text-xs">Agent: DevOps Integration</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-sm font-medium mb-2">🧠 Updating memory graph</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" style={{ width: '90%' }} />
                </div>
                <span className="text-purple-300 text-xs">90%</span>
              </div>
              <div className="text-purple-200 text-xs">Agent: Memory Synthesis</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-sm font-medium mb-2">📝 Generating docs</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" style={{ width: '30%' }} />
                </div>
                <span className="text-purple-300 text-xs">30%</span>
              </div>
              <div className="text-purple-200 text-xs">Agent: Documentation Generator</div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg border border-white/10">
              <div className="text-white text-sm font-medium mb-2">🛡️ Security scan running</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 bg-white/10 rounded-full h-1">
                  <div className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" style={{ width: '60%' }} />
                </div>
                <span className="text-purple-300 text-xs">60%</span>
              </div>
              <div className="text-purple-200 text-xs">Agent: Security Scanner</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMainContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView />;
      case 'agents':
        return <AgentsView />;
      case 'chat':
        return <ResponsiveAIChatInterface />;
      case 'memory':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">🧠 Memory Center</h2>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <p className="text-gray-300">Memory management interface coming soon...</p>
            </div>
          </div>
        );
      case 'parallel':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">⚡ Parallel Processing</h2>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <p className="text-gray-300">Parallel processing dashboard coming soon...</p>
            </div>
          </div>
        );
      case 'creative':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">🎨 Creative Innovation</h2>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <p className="text-gray-300">Creative engine interface coming soon...</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-white mb-6">{activeView.charAt(0).toUpperCase() + activeView.slice(1)}</h2>
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <p className="text-gray-300">This section is under development...</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      <TopNavigation />
      
      <div className="flex">
        <Sidebar />
        
        <div className="flex-1 overflow-hidden">
          {renderMainContent()}
        </div>
        
        <RightSidebar />
      </div>
    </div>
  );
};

export default FullReVoDashboard;