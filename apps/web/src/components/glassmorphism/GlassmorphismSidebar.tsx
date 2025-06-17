import React, { useState } from 'react';
import { 
  LayoutDashboard,
  Bot,
  Activity,
  BarChart3,
  Settings,
  Building,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Shield,
  Zap,
  FileText,
  Brain,
  Code,
  Bug,
  TestTube,
  Rocket,
  Globe,
  Cpu,
  MemoryStick,
  HardDrive,
  TrendingUp,
  DollarSign
} from 'lucide-react';

interface GlassmorphismSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentPage: string;
  onPageChange: (page: string) => void;
  systemMetrics: any;
}

const GlassmorphismSidebar: React.FC<GlassmorphismSidebarProps> = ({
  isOpen,
  onToggle,
  currentPage,
  onPageChange,
  systemMetrics
}) => {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Overview and system status',
      color: 'blue'
    },
    {
      id: 'agents',
      label: 'AI Agents',
      icon: Bot,
      description: 'Manage all 9 AI agents',
      color: 'purple',
      badge: '9'
    },
    {
      id: 'monitoring',
      label: 'System Monitor',
      icon: Activity,
      description: 'Real-time system monitoring',
      color: 'green'
    },
    {
      id: 'analytics',
      label: 'Cost Analytics',
      icon: BarChart3,
      description: 'Cost savings and analytics',
      color: 'orange'
    },
    {
      id: 'enterprise',
      label: 'Enterprise',
      icon: Building,
      description: 'Enterprise settings',
      color: 'indigo'
    }
  ];

  const agentItems = [
    { id: 'code_generator', label: 'Code Generator', icon: Code, status: 'active' },
    { id: 'debug_agent', label: 'Debug Detective', icon: Bug, status: 'active' },
    { id: 'testing_agent', label: 'Testing Agent', icon: TestTube, status: 'active' },
    { id: 'deploy_agent', label: 'Deploy Agent', icon: Rocket, status: 'idle' },
    { id: 'browser_agent', label: 'Browser Agent', icon: Globe, status: 'idle' },
    { id: 'security_agent', label: 'Security Agent', icon: Shield, status: 'active', new: true },
    { id: 'documentation_agent', label: 'Docs Agent', icon: FileText, status: 'idle', new: true },
    { id: 'performance_optimizer', label: 'Performance', icon: Zap, status: 'idle', new: true },
    { id: 'architecture_advisor', label: 'Architecture', icon: Brain, status: 'idle', new: true }
  ];

  const quickStats = [
    {
      label: 'CPU',
      value: systemMetrics?.cpu_usage || 24,
      max: 100,
      color: 'blue',
      icon: Cpu
    },
    {
      label: 'Memory', 
      value: systemMetrics?.memory_usage || 67,
      max: 100,
      color: 'green',
      icon: MemoryStick
    },
    {
      label: 'Storage',
      value: 45,
      max: 100,
      color: 'purple',
      icon: HardDrive
    }
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: 'text-blue-400 group-hover:text-blue-300',
      purple: 'text-purple-400 group-hover:text-purple-300',
      green: 'text-green-400 group-hover:text-green-300',
      orange: 'text-orange-400 group-hover:text-orange-300',
      indigo: 'text-indigo-400 group-hover:text-indigo-300',
      red: 'text-red-400 group-hover:text-red-300'
    };
    return colorMap[color as keyof typeof colorMap] || 'text-gray-400';
  };

  const renderQuickStat = (stat: any) => {
    const percentage = (stat.value / stat.max) * 100;
    
    return (
      <div key={stat.label} className="glass-subtle p-3 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <stat.icon className={`w-4 h-4 ${getColorClasses(stat.color)}`} />
            <span className="text-white/80 text-sm font-medium">{stat.label}</span>
          </div>
          <span className="text-white text-sm font-bold">{stat.value}%</span>
        </div>
        
        <div className="relative h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div 
            className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 bg-gradient-to-r from-${stat.color}-400 to-${stat.color}-600`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed left-0 top-0 bottom-0 z-50 lg:z-auto
        glass-card border-r border-white/10
        transition-all duration-300 ease-in-out
        ${isOpen ? 'w-80' : 'w-0 lg:w-16'}
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        overflow-hidden
      `}>
        
        {/* Toggle Button */}
        <button
          onClick={onToggle}
          className="absolute -right-3 top-6 w-6 h-6 glass-card rounded-full flex items-center justify-center hover:scale-110 transition-transform z-10 group"
        >
          {isOpen ? (
            <ChevronLeft className="w-3 h-3 text-white/70 group-hover:text-white" />
          ) : (
            <ChevronRight className="w-3 h-3 text-white/70 group-hover:text-white" />
          )}
        </button>

        <div className="flex flex-col h-full">
          
          {/* Header */}
          <div className="p-6 border-b border-white/10">
            {isOpen ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-blue-400 to-purple-600 shadow-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">reVoAgent</h2>
                    <p className="text-xs text-white/60">Glassmorphism Edition</p>
                  </div>
                </div>
                
                {/* Quick status */}
                <div className="flex items-center gap-2 px-3 py-2 glass-subtle rounded-lg">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-white/80 text-sm font-medium">All Systems Operational</span>
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-400 to-purple-600 shadow-lg">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            
            {/* Main Navigation */}
            <div className="space-y-2">
              {isOpen && (
                <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider px-3">
                  Navigation
                </h3>
              )}
              
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onPageChange(item.id)}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
                  className={`
                    w-full flex items-center gap-3 px-3 py-3 rounded-xl
                    transition-all duration-200 group relative
                    ${currentPage === item.id 
                      ? 'bg-gradient-to-r from-blue-400/20 to-purple-400/20 ring-1 ring-blue-400/30' 
                      : 'hover:bg-white/10'
                    }
                  `}
                >
                  <item.icon className={`w-5 h-5 ${
                    currentPage === item.id 
                      ? 'text-blue-400' 
                      : getColorClasses(item.color)
                  }`} />
                  
                  {isOpen && (
                    <>
                      <div className="flex-1 text-left">
                        <div className="font-medium text-white">{item.label}</div>
                        <div className="text-xs text-white/60">{item.description}</div>
                      </div>
                      
                      {item.badge && (
                        <div className="px-2 py-1 bg-blue-400/20 text-blue-300 text-xs rounded-full font-medium">
                          {item.badge}
                        </div>
                      )}
                    </>
                  )}

                  {/* Tooltip for collapsed state */}
                  {!isOpen && hoveredItem === item.id && (
                    <div className="absolute left-16 top-1/2 transform -translate-y-1/2 glass-card px-3 py-2 rounded-lg border border-white/20 z-50 whitespace-nowrap">
                      <div className="font-medium text-white">{item.label}</div>
                      <div className="text-xs text-white/60">{item.description}</div>
                    </div>
                  )}
                </button>
              ))}
            </div>

            {/* Quick Agent Access */}
            {isOpen && (
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider px-3">
                  Quick Agent Access
                </h3>
                
                <div className="space-y-1">
                  {agentItems.slice(0, 5).map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => onPageChange(`agent-${agent.id}`)}
                      className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition-colors group"
                    >
                      <agent.icon className="w-4 h-4 text-white/70 group-hover:text-white" />
                      <span className="text-sm text-white/80 group-hover:text-white flex-1 text-left">
                        {agent.label}
                      </span>
                      <div className={`w-2 h-2 rounded-full ${
                        agent.status === 'active' ? 'bg-green-400' : 'bg-gray-400'
                      }`} />
                      {agent.new && (
                        <div className="px-1.5 py-0.5 bg-orange-400/20 text-orange-300 text-xs rounded font-medium">
                          NEW
                        </div>
                      )}
                    </button>
                  ))}
                  
                  <button 
                    onClick={() => onPageChange('agents')}
                    className="w-full text-center py-2 text-white/60 hover:text-white text-sm transition-colors"
                  >
                    View all 9 agents →
                  </button>
                </div>
              </div>
            )}

            {/* System Stats */}
            {isOpen && (
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider px-3">
                  System Status
                </h3>
                
                <div className="space-y-2">
                  {quickStats.map(renderQuickStat)}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-white/10">
            {isOpen ? (
              <div className="space-y-3">
                {/* Cost Savings Display */}
                <div className="glass-subtle p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <DollarSign className="w-4 h-4 text-green-400" />
                    <span className="text-white/80 text-sm font-medium">Monthly Savings</span>
                  </div>
                  <div className="text-lg font-bold text-green-400">$5,420</div>
                  <div className="text-xs text-white/60">vs cloud solutions</div>
                </div>

                {/* Settings Button */}
                <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition-colors group">
                  <Settings className="w-4 h-4 text-white/70 group-hover:text-white" />
                  <span className="text-sm text-white/80 group-hover:text-white">Settings</span>
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <button className="w-full flex justify-center p-2 rounded-lg hover:bg-white/10 transition-colors">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </button>
                <button className="w-full flex justify-center p-2 rounded-lg hover:bg-white/10 transition-colors">
                  <Settings className="w-5 h-5 text-white/70 hover:text-white" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Glassmorphism glow effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      </aside>
    </>
  );
};

export default GlassmorphismSidebar;