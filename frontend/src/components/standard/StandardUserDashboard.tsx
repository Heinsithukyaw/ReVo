import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  Users,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Cpu,
  Database,
  Network,
  Shield,
  Zap,
  Brain,
  Palette,
  MessageSquare,
  FileText,
  Code,
  Image,
  Video,
  Music,
  Download,
  Upload,
  RefreshCw,
  Settings,
  Eye,
  EyeOff,
  Filter,
  Search,
  Calendar,
  Bell,
  Star,
  Award,
  Target,
  Gauge,
  PieChart,
  LineChart,
  Layers,
  Workflow,
  GitBranch,
  Timer,
  Lightbulb,
  Rocket,
  Home,
  Bookmark,
  Heart,
  ThumbsUp,
  Share,
  Copy,
  ExternalLink,
  Play,
  Pause,
  SkipForward,
  Volume2,
  Maximize2,
  Minimize2
} from 'lucide-react';

// Import workspace integration
import { AGENT_CATEGORIES } from '../../constants/agents';

interface WorkspaceStats {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  completedTasks: number;
  avgPerformance: number;
  systemUptime: number;
  dataProcessed: number;
  innovationsCreated: number;
  collaborations: number;
  costSavings: number;
}

interface RecentActivity {
  id: string;
  type: 'task_completed' | 'agent_activated' | 'collaboration' | 'innovation' | 'system_update';
  title: string;
  description: string;
  timestamp: Date;
  agent?: string;
  agentIcon?: string;
  status: 'success' | 'warning' | 'info' | 'error';
}

const StandardUserDashboard: React.FC = () => {
  const [workspaceStats, setWorkspaceStats] = useState<WorkspaceStats>({
    totalAgents: 0,
    activeAgents: 0,
    totalTasks: 0,
    completedTasks: 0,
    avgPerformance: 0,
    systemUptime: 0,
    dataProcessed: 0,
    innovationsCreated: 0,
    collaborations: 0,
    costSavings: 0
  });

  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'24h' | '7d' | '30d'>('24h');
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Initialize with workspace data
  useEffect(() => {
    const initializeData = () => {
      const allAgents = Object.values(AGENT_CATEGORIES).flat();
      
      // Generate realistic workspace statistics
      const stats: WorkspaceStats = {
        totalAgents: allAgents.length,
        activeAgents: Math.floor(allAgents.length * 0.7), // 70% active
        totalTasks: Math.floor(Math.random() * 10000) + 5000,
        completedTasks: Math.floor(Math.random() * 8000) + 4000,
        avgPerformance: Math.floor(Math.random() * 20) + 80, // 80-100%
        systemUptime: 99.8,
        dataProcessed: Math.floor(Math.random() * 1000) + 500, // GB
        innovationsCreated: Math.floor(Math.random() * 100) + 50,
        collaborations: Math.floor(Math.random() * 500) + 200,
        costSavings: 0.00 // Local processing
      };

      // Generate recent activity
      const activities: RecentActivity[] = Array.from({ length: 10 }, (_, i) => {
        const agent = allAgents[Math.floor(Math.random() * allAgents.length)];
        const types: RecentActivity['type'][] = ['task_completed', 'agent_activated', 'collaboration', 'innovation', 'system_update'];
        const type = types[Math.floor(Math.random() * types.length)];
        
        const activityTemplates = {
          task_completed: {
            title: `Task completed by ${agent.name}`,
            description: `Successfully processed user request with 98.5% accuracy`,
            status: 'success' as const
          },
          agent_activated: {
            title: `${agent.name} activated`,
            description: `Agent came online and ready for collaboration`,
            status: 'info' as const
          },
          collaboration: {
            title: `Multi-agent collaboration`,
            description: `${agent.name} collaborated with 2 other agents`,
            status: 'success' as const
          },
          innovation: {
            title: `Innovation created`,
            description: `${agent.name} generated new solution approach`,
            status: 'success' as const
          },
          system_update: {
            title: `System optimization`,
            description: `Performance improved by 3.2%`,
            status: 'info' as const
          }
        };

        const template = activityTemplates[type];
        
        return {
          id: `activity-${i}`,
          type,
          title: template.title,
          description: template.description,
          timestamp: new Date(Date.now() - Math.random() * 86400000), // Within last 24h
          agent: agent.name,
          agentIcon: agent.icon,
          status: template.status
        };
      }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

      setWorkspaceStats(stats);
      setRecentActivity(activities);
      setIsLoading(false);
    };

    initializeData();
  }, []);

  // Auto-refresh data
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setWorkspaceStats(prev => ({
        ...prev,
        activeAgents: Math.max(0, prev.activeAgents + Math.floor((Math.random() - 0.5) * 3)),
        completedTasks: prev.completedTasks + Math.floor(Math.random() * 5),
        avgPerformance: Math.max(75, Math.min(100, prev.avgPerformance + (Math.random() - 0.5) * 2)),
        dataProcessed: prev.dataProcessed + Math.random() * 10
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getActivityIcon = (type: RecentActivity['type']) => {
    switch (type) {
      case 'task_completed': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'agent_activated': return <Users className="w-4 h-4 text-blue-400" />;
      case 'collaboration': return <Users className="w-4 h-4 text-purple-400" />;
      case 'innovation': return <Lightbulb className="w-4 h-4 text-yellow-400" />;
      case 'system_update': return <Settings className="w-4 h-4 text-gray-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: RecentActivity['status']) => {
    switch (status) {
      case 'success': return 'bg-green-600/20 border-green-500/30';
      case 'warning': return 'bg-yellow-600/20 border-yellow-500/30';
      case 'info': return 'bg-blue-600/20 border-blue-500/30';
      case 'error': return 'bg-red-600/20 border-red-500/30';
      default: return 'bg-gray-600/20 border-gray-500/30';
    }
  };

  const completionRate = workspaceStats.totalTasks > 0 
    ? (workspaceStats.completedTasks / workspaceStats.totalTasks) * 100 
    : 0;

  const agentUtilization = workspaceStats.totalAgents > 0 
    ? (workspaceStats.activeAgents / workspaceStats.totalAgents) * 100 
    : 0;

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-white mb-2">Loading Dashboard</h2>
          <p className="text-gray-300 mb-4">Gathering workspace data...</p>
          <div className="flex space-x-2 justify-center">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
            <div className="w-3 h-3 bg-gray-400 rounded-full animate-pulse delay-100"></div>
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse delay-200"></div>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800/60 backdrop-blur-md border-b border-gray-700/50 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">Standard Dashboard</h1>
                <p className="text-gray-400">Workspace Arena Overview & Analytics</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Timeframe Selector */}
            <div className="flex items-center space-x-1 bg-gray-700/50 rounded-lg p-1">
              {(['24h', '7d', '30d'] as const).map(timeframe => (
                <button
                  key={timeframe}
                  onClick={() => setSelectedTimeframe(timeframe)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    selectedTimeframe === timeframe
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  {timeframe}
                </button>
              ))}
            </div>

            {/* Auto Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`p-2 rounded-lg transition-colors ${
                autoRefresh ? 'bg-green-600/20 text-green-400' : 'bg-gray-700/50 text-gray-400'
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            </button>

            <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-blue-400 font-bold text-3xl">{workspaceStats.totalAgents}</div>
            <div className="text-gray-400 text-sm mt-1">Total Agents</div>
            <div className="flex items-center justify-center mt-2">
              <Users className="w-4 h-4 text-blue-400" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-green-400 font-bold text-3xl">{workspaceStats.activeAgents}</div>
            <div className="text-gray-400 text-sm mt-1">Active Now</div>
            <div className="flex items-center justify-center mt-2">
              <Activity className="w-4 h-4 text-green-400" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-purple-400 font-bold text-3xl">{workspaceStats.completedTasks.toLocaleString()}</div>
            <div className="text-gray-400 text-sm mt-1">Tasks Done</div>
            <div className="flex items-center justify-center mt-2">
              <CheckCircle className="w-4 h-4 text-purple-400" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-yellow-400 font-bold text-3xl">{workspaceStats.avgPerformance.toFixed(1)}%</div>
            <div className="text-gray-400 text-sm mt-1">Performance</div>
            <div className="flex items-center justify-center mt-2">
              <TrendingUp className="w-4 h-4 text-yellow-400" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-cyan-400 font-bold text-3xl">{workspaceStats.systemUptime}%</div>
            <div className="text-gray-400 text-sm mt-1">Uptime</div>
            <div className="flex items-center justify-center mt-2">
              <Shield className="w-4 h-4 text-cyan-400" />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 text-center"
          >
            <div className="text-pink-400 font-bold text-3xl">${workspaceStats.costSavings.toFixed(2)}</div>
            <div className="text-gray-400 text-sm mt-1">Cost Savings</div>
            <div className="flex items-center justify-center mt-2">
              <Star className="w-4 h-4 text-pink-400" />
            </div>
          </motion.div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Performance Overview */}
          <div className="lg:col-span-2 space-y-6">
            {/* Agent Utilization */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6"
            >
              <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-blue-400" />
                <span>Agent Utilization</span>
              </h3>
              
              <div className="grid grid-cols-2 gap-6">
                {/* Utilization Chart */}
                <div className="relative">
                  <div className="w-32 h-32 mx-auto">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className="text-gray-700"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 40}`}
                        strokeDashoffset={`${2 * Math.PI * 40 * (1 - agentUtilization / 100)}`}
                        className="text-blue-400"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">{agentUtilization.toFixed(0)}%</div>
                        <div className="text-gray-400 text-xs">Active</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Utilization Stats */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Active Agents</span>
                    <span className="text-white font-medium">{workspaceStats.activeAgents}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Idle Agents</span>
                    <span className="text-white font-medium">{workspaceStats.totalAgents - workspaceStats.activeAgents}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Efficiency</span>
                    <span className="text-green-400 font-medium">{(agentUtilization * 0.9).toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Load Balance</span>
                    <span className="text-blue-400 font-medium">Optimal</span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Task Completion */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6"
            >
              <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                <span>Task Completion Rate</span>
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Completion Rate</span>
                  <span className="text-white font-semibold">{completionRate.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700/50 rounded-full h-4">
                  <motion.div
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${completionRate}%` }}
                    transition={{ duration: 1.5 }}
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="text-center">
                    <div className="text-white font-semibold text-lg">{workspaceStats.totalTasks.toLocaleString()}</div>
                    <div className="text-gray-400 text-sm">Total Tasks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-green-400 font-semibold text-lg">{workspaceStats.completedTasks.toLocaleString()}</div>
                    <div className="text-gray-400 text-sm">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-yellow-400 font-semibold text-lg">{(workspaceStats.totalTasks - workspaceStats.completedTasks).toLocaleString()}</div>
                    <div className="text-gray-400 text-sm">Pending</div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* System Resources */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6"
            >
              <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-green-400" />
                <span>System Resources</span>
              </h3>
              
              <div className="space-y-4">
                {[
                  { name: 'CPU Usage', value: 45, color: 'bg-blue-500', icon: <Cpu className="w-4 h-4" /> },
                  { name: 'Memory', value: 62, color: 'bg-green-500', icon: <Database className="w-4 h-4" /> },
                  { name: 'Network I/O', value: 38, color: 'bg-purple-500', icon: <Network className="w-4 h-4" /> },
                  { name: 'Storage', value: 28, color: 'bg-yellow-500', icon: <Database className="w-4 h-4" /> }
                ].map((resource, index) => (
                  <div key={resource.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="text-gray-400">{resource.icon}</div>
                        <span className="text-gray-300 text-sm">{resource.name}</span>
                      </div>
                      <span className="text-white font-medium">{resource.value}%</span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-2">
                      <motion.div
                        className={`h-2 rounded-full ${resource.color}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${resource.value}%` }}
                        transition={{ duration: 1, delay: index * 0.1 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6"
          >
            <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
              <Activity className="w-5 h-5 text-yellow-400" />
              <span>Recent Activity</span>
            </h3>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {recentActivity.map((activity, index) => (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className={`p-4 rounded-lg border ${getStatusColor(activity.status)}`}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        {activity.agentIcon && (
                          <span className="text-lg">{activity.agentIcon}</span>
                        )}
                        <p className="text-white text-sm font-medium">{activity.title}</p>
                      </div>
                      <p className="text-gray-400 text-xs">{activity.description}</p>
                      <p className="text-gray-500 text-xs mt-2">
                        {activity.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Agent Categories Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-8 bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6"
        >
          <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-400" />
            <span>Agent Categories</span>
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(AGENT_CATEGORIES).map(([category, agents]) => (
              <div key={category} className="text-center p-4 bg-gray-700/30 rounded-lg">
                <div className="text-2xl mb-2">{agents[0]?.icon || '🤖'}</div>
                <div className="text-white font-medium text-sm capitalize">{category}</div>
                <div className="text-gray-400 text-xs">{agents.length} agents</div>
                <div className="mt-2">
                  <div className="text-green-400 text-sm font-medium">
                    {Math.floor(agents.length * 0.7)} active
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default StandardUserDashboard;