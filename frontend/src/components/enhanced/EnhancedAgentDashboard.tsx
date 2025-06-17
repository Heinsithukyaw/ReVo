import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  BarChart3,
  Brain,
  Cpu,
  Database,
  TrendingUp,
  Users,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  Pause,
  Play,
  RotateCcw,
  Settings,
  Filter,
  Download,
  RefreshCw,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Star,
  Award,
  Target,
  Gauge,
  PieChart,
  LineChart,
  BarChart,
  Layers,
  Network,
  Workflow,
  GitBranch,
  Timer,
  Lightbulb,
  Rocket,
  Shield,
  Lock,
  Unlock
} from 'lucide-react';

// Import agents from workspace
import { AGENT_CATEGORIES } from '../../constants/agents';

interface AgentStats {
  id: string;
  name: string;
  icon: string;
  category: string;
  status: 'active' | 'idle' | 'busy' | 'offline';
  workload: number;
  performance: number;
  tasksCompleted: number;
  avgResponseTime: number;
  successRate: number;
  currentTasks: number;
  totalTasks: number;
  uptime: number;
  lastActive: Date;
  specialties: string[];
  collaborations: number;
  innovations: number;
  efficiency: number;
}

const EnhancedAgentDashboard: React.FC = () => {
  const [agentStats, setAgentStats] = useState<AgentStats[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'analytics'>('grid');
  const [sortBy, setSortBy] = useState<'performance' | 'workload' | 'tasks' | 'efficiency'>('performance');
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Generate realistic agent statistics
  useEffect(() => {
    const generateAgentStats = (): AgentStats[] => {
      const allAgents = Object.values(AGENT_CATEGORIES).flat();
      
      return allAgents.map(agent => ({
        id: agent.id,
        name: agent.name,
        icon: agent.icon,
        category: agent.category,
        status: ['active', 'idle', 'busy'][Math.floor(Math.random() * 3)] as any,
        workload: Math.floor(Math.random() * 100),
        performance: Math.floor(Math.random() * 40) + 60, // 60-100%
        tasksCompleted: Math.floor(Math.random() * 500) + 50,
        avgResponseTime: Math.random() * 2 + 0.5, // 0.5-2.5 seconds
        successRate: Math.floor(Math.random() * 20) + 80, // 80-100%
        currentTasks: Math.floor(Math.random() * 10),
        totalTasks: Math.floor(Math.random() * 1000) + 100,
        uptime: Math.floor(Math.random() * 100),
        lastActive: new Date(Date.now() - Math.random() * 3600000), // Within last hour
        specialties: agent.description ? [agent.description] : ['General AI'],
        collaborations: Math.floor(Math.random() * 50),
        innovations: Math.floor(Math.random() * 25),
        efficiency: Math.floor(Math.random() * 30) + 70 // 70-100%
      }));
    };

    setIsLoading(true);
    setTimeout(() => {
      setAgentStats(generateAgentStats());
      setIsLoading(false);
    }, 1000);
  }, []);

  // Auto-refresh data
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      setAgentStats(prev => prev.map(agent => ({
        ...agent,
        workload: Math.max(0, agent.workload + (Math.random() - 0.5) * 10),
        performance: Math.max(60, Math.min(100, agent.performance + (Math.random() - 0.5) * 5)),
        currentTasks: Math.max(0, agent.currentTasks + Math.floor((Math.random() - 0.5) * 3)),
        lastActive: Math.random() > 0.7 ? new Date() : agent.lastActive
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const categories = ['all', ...Object.keys(AGENT_CATEGORIES)];
  
  const filteredAgents = agentStats.filter(agent => 
    selectedCategory === 'all' || agent.category === selectedCategory
  ).sort((a, b) => {
    switch (sortBy) {
      case 'performance': return b.performance - a.performance;
      case 'workload': return b.workload - a.workload;
      case 'tasks': return b.tasksCompleted - a.tasksCompleted;
      case 'efficiency': return b.efficiency - a.efficiency;
      default: return 0;
    }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-400/20';
      case 'busy': return 'text-yellow-400 bg-yellow-400/20';
      case 'idle': return 'text-blue-400 bg-blue-400/20';
      case 'offline': return 'text-gray-400 bg-gray-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  const getPerformanceColor = (performance: number) => {
    if (performance >= 90) return 'text-green-400';
    if (performance >= 75) return 'text-yellow-400';
    if (performance >= 60) return 'text-orange-400';
    return 'text-red-400';
  };

  const overallStats = {
    totalAgents: agentStats.length,
    activeAgents: agentStats.filter(a => a.status === 'active').length,
    avgPerformance: agentStats.reduce((sum, a) => sum + a.performance, 0) / agentStats.length || 0,
    totalTasks: agentStats.reduce((sum, a) => sum + a.tasksCompleted, 0),
    avgResponseTime: agentStats.reduce((sum, a) => sum + a.avgResponseTime, 0) / agentStats.length || 0,
    totalCollaborations: agentStats.reduce((sum, a) => sum + a.collaborations, 0)
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="text-6xl mb-4">🤖</div>
          <h2 className="text-2xl font-bold text-white mb-2">Loading Agent Analytics</h2>
          <p className="text-gray-300 mb-4">Gathering performance data...</p>
          <div className="flex space-x-2 justify-center">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
            <div className="w-3 h-3 bg-purple-400 rounded-full animate-pulse delay-100"></div>
            <div className="w-3 h-3 bg-pink-400 rounded-full animate-pulse delay-200"></div>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800/60 backdrop-blur-md border-b border-gray-700/50 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-2xl font-bold text-white">Enhanced Agent Dashboard</h1>
                <p className="text-gray-400">Real-time agent performance & analytics</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* View Mode Toggle */}
            <div className="flex items-center space-x-1 bg-gray-700/50 rounded-lg p-1">
              {(['grid', 'list', 'analytics'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === mode
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  {mode === 'grid' && <BarChart className="w-4 h-4" />}
                  {mode === 'list' && <Users className="w-4 h-4" />}
                  {mode === 'analytics' && <LineChart className="w-4 h-4" />}
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

        {/* Overall Stats */}
        <div className="mt-6 grid grid-cols-6 gap-4">
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-blue-400 font-bold text-2xl">{overallStats.totalAgents}</div>
            <div className="text-gray-400 text-sm">Total Agents</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-green-400 font-bold text-2xl">{overallStats.activeAgents}</div>
            <div className="text-gray-400 text-sm">Active Now</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-purple-400 font-bold text-2xl">{overallStats.avgPerformance.toFixed(1)}%</div>
            <div className="text-gray-400 text-sm">Avg Performance</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-yellow-400 font-bold text-2xl">{overallStats.totalTasks.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">Tasks Completed</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-pink-400 font-bold text-2xl">{overallStats.avgResponseTime.toFixed(2)}s</div>
            <div className="text-gray-400 text-sm">Avg Response</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-cyan-400 font-bold text-2xl">{overallStats.totalCollaborations}</div>
            <div className="text-gray-400 text-sm">Collaborations</div>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Category Filter */}
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-gray-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort By */}
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-gray-700/50 border border-gray-600/50 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="performance">Performance</option>
                <option value="workload">Workload</option>
                <option value="tasks">Tasks Completed</option>
                <option value="efficiency">Efficiency</option>
              </select>
            </div>
          </div>

          <div className="text-sm text-gray-400">
            Showing {filteredAgents.length} of {agentStats.length} agents
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {viewMode === 'grid' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAgents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 hover:border-gray-600/50 transition-all"
              >
                {/* Agent Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-3xl">{agent.icon}</span>
                    <div>
                      <h3 className="text-white font-semibold">{agent.name}</h3>
                      <p className="text-gray-400 text-sm">{agent.category}</p>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 text-sm">Performance</span>
                    <span className={`font-semibold ${getPerformanceColor(agent.performance)}`}>
                      {agent.performance}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-700/50 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${agent.performance}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3 mt-4">
                    <div className="text-center">
                      <div className="text-white font-semibold">{agent.tasksCompleted}</div>
                      <div className="text-gray-400 text-xs">Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{agent.avgResponseTime.toFixed(1)}s</div>
                      <div className="text-gray-400 text-xs">Response</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{agent.successRate}%</div>
                      <div className="text-gray-400 text-xs">Success</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{agent.currentTasks}</div>
                      <div className="text-gray-400 text-xs">Active</div>
                    </div>
                  </div>

                  {/* Workload Indicator */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-gray-400 text-sm">Workload</span>
                      <span className="text-white text-sm">{agent.workload.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-500 ${
                          agent.workload > 80 ? 'bg-red-500' :
                          agent.workload > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${agent.workload}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    Last active: {agent.lastActive.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="flex items-center space-x-1">
                    <button className="p-1 hover:bg-gray-700/50 rounded transition-colors">
                      <Eye className="w-3 h-3 text-gray-400" />
                    </button>
                    <button className="p-1 hover:bg-gray-700/50 rounded transition-colors">
                      <Settings className="w-3 h-3 text-gray-400" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {viewMode === 'list' && (
          <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700/50">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Agent</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Performance</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Workload</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Tasks</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Response Time</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Success Rate</th>
                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700/30">
                  {filteredAgents.map((agent, index) => (
                    <motion.tr
                      key={agent.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className="hover:bg-gray-700/20 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <span className="text-2xl">{agent.icon}</span>
                          <div>
                            <div className="text-white font-medium">{agent.name}</div>
                            <div className="text-gray-400 text-sm">{agent.category}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                          {agent.status}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-700/50 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                              style={{ width: `${agent.performance}%` }}
                            />
                          </div>
                          <span className={`text-sm font-medium ${getPerformanceColor(agent.performance)}`}>
                            {agent.performance}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-700/50 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                agent.workload > 80 ? 'bg-red-500' :
                                agent.workload > 60 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${agent.workload}%` }}
                            />
                          </div>
                          <span className="text-white text-sm">{agent.workload.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-white text-sm">
                        {agent.tasksCompleted.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-white text-sm">
                        {agent.avgResponseTime.toFixed(2)}s
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-white text-sm">
                        {agent.successRate}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button className="p-1 hover:bg-gray-700/50 rounded transition-colors">
                            <Eye className="w-4 h-4 text-gray-400" />
                          </button>
                          <button className="p-1 hover:bg-gray-700/50 rounded transition-colors">
                            <Settings className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {viewMode === 'analytics' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Distribution */}
            <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                <PieChart className="w-5 h-5 text-blue-400" />
                <span>Performance Distribution</span>
              </h3>
              <div className="space-y-3">
                {['Excellent (90-100%)', 'Good (75-89%)', 'Average (60-74%)', 'Poor (<60%)'].map((range, index) => {
                  const colors = ['bg-green-500', 'bg-blue-500', 'bg-yellow-500', 'bg-red-500'];
                  const count = agentStats.filter(agent => {
                    if (index === 0) return agent.performance >= 90;
                    if (index === 1) return agent.performance >= 75 && agent.performance < 90;
                    if (index === 2) return agent.performance >= 60 && agent.performance < 75;
                    return agent.performance < 60;
                  }).length;
                  const percentage = (count / agentStats.length) * 100;
                  
                  return (
                    <div key={range} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${colors[index]}`} />
                        <span className="text-gray-300 text-sm">{range}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-white font-medium">{count}</span>
                        <span className="text-gray-400 text-sm">({percentage.toFixed(1)}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Category Performance */}
            <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                <span>Category Performance</span>
              </h3>
              <div className="space-y-3">
                {Object.keys(AGENT_CATEGORIES).map(category => {
                  const categoryAgents = agentStats.filter(agent => agent.category === category);
                  const avgPerformance = categoryAgents.reduce((sum, agent) => sum + agent.performance, 0) / categoryAgents.length || 0;
                  
                  return (
                    <div key={category} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-300 text-sm capitalize">{category}</span>
                        <span className="text-white font-medium">{avgPerformance.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-700/50 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                          style={{ width: `${avgPerformance}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Real-time Activity */}
            <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                <Activity className="w-5 h-5 text-green-400" />
                <span>Real-time Activity</span>
              </h3>
              <div className="space-y-3">
                {agentStats.filter(agent => agent.status === 'active').slice(0, 5).map(agent => (
                  <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg">{agent.icon}</span>
                      <div>
                        <div className="text-white text-sm font-medium">{agent.name}</div>
                        <div className="text-gray-400 text-xs">{agent.currentTasks} active tasks</div>
                      </div>
                    </div>
                    <div className="text-green-400 text-sm">
                      {agent.avgResponseTime.toFixed(1)}s
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Performers */}
            <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                <Award className="w-5 h-5 text-yellow-400" />
                <span>Top Performers</span>
              </h3>
              <div className="space-y-3">
                {agentStats.sort((a, b) => b.performance - a.performance).slice(0, 5).map((agent, index) => (
                  <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        index === 0 ? 'bg-yellow-500 text-black' :
                        index === 1 ? 'bg-gray-400 text-black' :
                        index === 2 ? 'bg-orange-500 text-black' : 'bg-gray-600 text-white'
                      }`}>
                        {index + 1}
                      </div>
                      <span className="text-lg">{agent.icon}</span>
                      <div>
                        <div className="text-white text-sm font-medium">{agent.name}</div>
                        <div className="text-gray-400 text-xs">{agent.tasksCompleted} tasks completed</div>
                      </div>
                    </div>
                    <div className="text-green-400 text-sm font-semibold">
                      {agent.performance}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedAgentDashboard;