import React, { useState, useEffect } from 'react';
import { 
  Activity, Brain, Zap, MessageSquare, Settings, 
  Users, Database, Shield, BarChart3, GitBranch, Slack,
  Cpu, HardDrive, Network, TrendingUp, Bell, Play,
  Search, Download, Upload, RefreshCw, Eye, Code,
  Bug, TestTube, Rocket, FileText, Monitor, Lock,
  Palette, Home, Workflow, Store, BarChart, Link,
  Cog, Menu, X, ChevronRight, AlertCircle, ChevronLeft,
  Maximize2, Minimize2, PanelLeftClose, PanelLeftOpen,
  PanelRightClose, PanelRightOpen, Expand, Shrink
} from 'lucide-react';

// Import our hooks and services
import { useDashboardStats, useAgents, useSystemMetrics, useHealthCheck, useConnectionStatus } from '../hooks/useApi';
import { useDashboardWebSocket } from '../hooks/useWebSocket';
import EnhancedMultiAgentChat from './EnhancedMultiAgentChat';

const EnhancedCollapsibleDashboard = () => {
  const [activeView, setActiveView] = useState('chat');
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightSidebarOpen, setRightSidebarOpen] = useState(true);
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false);
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Use our custom hooks for real data
  const { stats, loading: statsLoading, error: statsError } = useDashboardStats();
  const { agents, activeTasks, totalAgents, loading: agentsLoading } = useAgents();
  const { metrics, loading: metricsLoading } = useSystemMetrics();
  const { health, loading: healthLoading } = useHealthCheck();
  const isOnline = useConnectionStatus();
  const { isConnected, dashboardData, notifications } = useDashboardWebSocket();

  // Auto-collapse sidebars when in chat mode for better workspace
  useEffect(() => {
    if (activeView === 'chat') {
      // Auto-collapse sidebars for more chat space, but keep them accessible
      setLeftSidebarCollapsed(true);
      setRightSidebarCollapsed(true);
    } else {
      // Expand sidebars for other views
      setLeftSidebarCollapsed(false);
      setRightSidebarCollapsed(false);
    }
  }, [activeView]);

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

  // Toggle fullscreen mode for chat
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    if (!isFullscreen) {
      setLeftSidebarOpen(false);
      setRightSidebarOpen(false);
    } else {
      setLeftSidebarOpen(true);
      setRightSidebarOpen(true);
    }
  };

  // Top Navigation with enhanced controls
  const TopNavigation = () => (
    <div className="bg-black/30 backdrop-blur-md border-b border-white/10 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Sidebar Toggle Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              title="Toggle Left Sidebar"
            >
              {leftSidebarOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
            </button>
            
            {leftSidebarOpen && (
              <button
                onClick={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title={leftSidebarCollapsed ? "Expand Left Sidebar" : "Collapse Left Sidebar"}
              >
                {leftSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">reVoAgent</h1>
              <p className="text-xs text-gray-400">Three-Engine AI Platform</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Chat Mode Controls (only show when in chat view) */}
          {activeView === 'chat' && (
            <div className="flex items-center gap-2">
              <button
                onClick={toggleFullscreen}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
              >
                {isFullscreen ? <Shrink className="w-5 h-5" /> : <Expand className="w-5 h-5" />}
              </button>
            </div>
          )}

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-sm text-gray-300">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Right Sidebar Controls */}
          <div className="flex items-center gap-2">
            {rightSidebarOpen && (
              <button
                onClick={() => setRightSidebarCollapsed(!rightSidebarCollapsed)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title={rightSidebarCollapsed ? "Expand Right Sidebar" : "Collapse Right Sidebar"}
              >
                {rightSidebarCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            )}
            
            <button
              onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              title="Toggle Right Sidebar"
            >
              {rightSidebarOpen ? <PanelRightClose className="w-5 h-5" /> : <PanelRightOpen className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Enhanced Left Sidebar with collapse functionality
  const LeftSidebar = () => (
    <div className={`
      ${leftSidebarOpen ? (leftSidebarCollapsed ? 'w-16' : 'w-64') : 'w-0'} 
      bg-black/20 backdrop-blur-md border-r border-white/10 h-screen overflow-y-auto transition-all duration-300 ease-in-out
    `}>
      {leftSidebarOpen && (
        <div className="p-4 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`
                  w-full p-3 rounded-lg transition-all duration-200 flex items-center gap-3 group
                  ${isActive 
                    ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30 text-white' 
                    : 'hover:bg-white/10 text-gray-300 hover:text-white'
                  }
                `}
                title={leftSidebarCollapsed ? item.label : ''}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-400' : 'text-gray-400 group-hover:text-white'}`} />
                
                {!leftSidebarCollapsed && (
                  <div className="flex-1 text-left">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs text-gray-400">{item.description}</div>
                  </div>
                )}
                
                {!leftSidebarCollapsed && item.badge && (
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full">
                    {item.badge}
                  </span>
                )}
                
                {!leftSidebarCollapsed && isActive && (
                  <ChevronRight className="w-4 h-4 text-blue-400" />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );

  // Enhanced Right Sidebar with collapse functionality
  const RightSidebar = () => (
    <div className={`
      ${rightSidebarOpen ? (rightSidebarCollapsed ? 'w-16' : 'w-80') : 'w-0'} 
      bg-black/20 backdrop-blur-md border-l border-white/10 h-screen overflow-y-auto transition-all duration-300 ease-in-out
    `}>
      {rightSidebarOpen && (
        <div className="p-4 space-y-6">
          {!rightSidebarCollapsed ? (
            <>
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
                </div>
              </div>

              {/* System Status */}
              <div>
                <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  SYSTEM STATUS
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-white/5 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-300">CPU Usage</span>
                      <span className="text-sm text-white">{systemMetrics.cpu}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${systemMetrics.cpu}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="p-3 bg-white/5 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-300">Memory</span>
                      <span className="text-sm text-white">{systemMetrics.memory}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${systemMetrics.memory}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Three Engine Status */}
              <div>
                <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-400" />
                  THREE ENGINES
                </h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Brain className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-white">Memory</span>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${engineStatus.memory.status === 'active' ? 'bg-green-400' : 'bg-red-400'}`} />
                  </div>
                  
                  <div className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm text-white">Parallel</span>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${engineStatus.parallel.status === 'active' ? 'bg-green-400' : 'bg-red-400'}`} />
                  </div>
                  
                  <div className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Palette className="w-4 h-4 text-pink-400" />
                      <span className="text-sm text-white">Creative</span>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${engineStatus.creative.status === 'active' ? 'bg-green-400' : 'bg-red-400'}`} />
                  </div>
                </div>
              </div>
            </>
          ) : (
            // Collapsed view - show only icons
            <div className="space-y-4">
              <div className="p-2 bg-white/5 rounded-lg" title="Quick Actions">
                <Play className="w-6 h-6 text-green-400 mx-auto" />
              </div>
              <div className="p-2 bg-white/5 rounded-lg" title="System Status">
                <Activity className="w-6 h-6 text-blue-400 mx-auto" />
              </div>
              <div className="p-2 bg-white/5 rounded-lg" title="Three Engines">
                <Brain className="w-6 h-6 text-purple-400 mx-auto" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Main content area with dynamic sizing
  const renderMainContent = () => {
    const contentClass = `
      flex-1 overflow-hidden transition-all duration-300 ease-in-out
      ${isFullscreen ? 'h-screen' : 'h-[calc(100vh-80px)]'}
    `;

    switch (activeView) {
      case 'chat':
        return (
          <div className={contentClass}>
            <EnhancedMultiAgentChat 
              isFullscreen={isFullscreen}
              leftSidebarOpen={leftSidebarOpen}
              rightSidebarOpen={rightSidebarOpen}
            />
          </div>
        );
      case 'dashboard':
        return (
          <div className={contentClass}>
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-6">🚀 Three-Engine Dashboard</h2>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                <p className="text-gray-300">Dashboard content...</p>
              </div>
            </div>
          </div>
        );
      case 'agents':
        return (
          <div className={contentClass}>
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-6">🤖 AI Agents Hub</h2>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                <p className="text-gray-300">Agents management interface...</p>
              </div>
            </div>
          </div>
        );
      default:
        return (
          <div className={contentClass}>
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-6">
                {activeView.charAt(0).toUpperCase() + activeView.slice(1)}
              </h2>
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                <p className="text-gray-300">This section is under development...</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {!isFullscreen && <TopNavigation />}
      
      <div className="flex">
        {!isFullscreen && <LeftSidebar />}
        
        {renderMainContent()}
        
        {!isFullscreen && <RightSidebar />}
      </div>
    </div>
  );
};

export default EnhancedCollapsibleDashboard;