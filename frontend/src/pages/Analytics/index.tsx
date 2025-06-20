import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  DollarSign, TrendingUp, TrendingDown, Activity, Cpu, 
  HardDrive, Wifi, Clock, Target, AlertTriangle, CheckCircle,
  BarChart3, PieChart, LineChart, RefreshCw, Download, Settings,
  Brain, Network, Zap, Eye, Users, MessageSquare
} from 'lucide-react';
import { useAppStore } from '../../store';

const Analytics: React.FC = () => {
  const { systemMetrics, engineStatuses } = useAppStore();
  const [timeRange, setTimeRange] = useState('24h');
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Mock data for demonstrations
  const costData = {
    totalSaved: 1247.50,
    monthlySaved: 89.32,
    weeklyTrend: 12.5,
    efficiency: 94.2,
    breakdown: {
      'Local Processing': 67.2,
      'Model Optimization': 18.9,
      'Caching': 8.7,
      'Load Balancing': 5.2
    }
  };

  const performanceMetrics = {
    avgResponseTime: 0.847,
    throughput: 1243,
    uptime: 99.94,
    errorRate: 0.06,
    trends: {
      responseTime: -12.3,
      throughput: 8.7,
      uptime: 0.2,
      errorRate: -45.2
    }
  };

  const memoryStats = {
    totalNodes: 15847,
    activeConnections: 2341,
    queryPerformance: 0.034,
    storageEfficiency: 87.3,
    growthRate: 23.4
  };

  const systemIntelligence = {
    predictiveAccuracy: 91.7,
    patternRecognition: 88.9,
    anomalyDetection: 96.2,
    adaptationSpeed: 2.3,
    recommendationsGenerated: 47
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return <TrendingUp className="w-4 h-4 text-green-400" />;
    if (trend < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  const getTrendColor = (trend: number) => {
    if (trend > 0) return 'text-green-400';
    if (trend < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics & Monitoring</h1>
          <p className="text-gray-400 mt-2">Real-time insights into system performance and optimization</p>
        </div>
        <div className="flex items-center space-x-4">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="glass-input text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button className="glass-button">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button className="glass-button">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Last Update Indicator */}
      <div className="flex justify-end">
        <span className="text-xs text-gray-400">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </span>
      </div>

      {/* Top Row: Financial & Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Cost Optimization Dashboard */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <DollarSign className="w-5 h-5 mr-2 text-green-400" />
              Cost Optimization
            </h2>
            <button className="glass-button text-sm">
              <Settings className="w-4 h-4" />
            </button>
          </div>

          {/* Cost Summary */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gradient-to-r from-green-500/10 to-green-600/10 rounded-lg p-4 border border-green-500/20">
              <div className="text-2xl font-bold text-green-400">{formatCurrency(costData.totalSaved)}</div>
              <div className="text-sm text-gray-300">Total Saved</div>
              <div className="flex items-center mt-2">
                {getTrendIcon(costData.weeklyTrend)}
                <span className={`text-xs ml-1 ${getTrendColor(costData.weeklyTrend)}`}>
                  {formatPercentage(costData.weeklyTrend)} this week
                </span>
              </div>
            </div>
            
            <div className="bg-gradient-to-r from-blue-500/10 to-blue-600/10 rounded-lg p-4 border border-blue-500/20">
              <div className="text-2xl font-bold text-blue-400">{formatCurrency(costData.monthlySaved)}</div>
              <div className="text-sm text-gray-300">This Month</div>
              <div className="flex items-center mt-2">
                <Target className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-blue-400 ml-1">
                  {formatPercentage(costData.efficiency)} efficiency
                </span>
              </div>
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="space-y-3">
            <h3 className="text-white font-medium">Savings Breakdown</h3>
            {Object.entries(costData.breakdown).map(([category, percentage]) => (
              <div key={category} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">{category}</span>
                  <span className="text-white">{formatPercentage(percentage)}</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Performance Metrics Dashboard */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel"
        >
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-400" />
              Performance Metrics
            </h2>
            <button className="glass-button text-sm">
              <BarChart3 className="w-4 h-4" />
            </button>
          </div>

          {/* Performance Grid */}
          <div className="grid grid-cols-2 gap-4">
            {[
              { 
                label: 'Response Time', 
                value: `${performanceMetrics.avgResponseTime}s`, 
                trend: performanceMetrics.trends.responseTime,
                icon: Clock,
                color: 'purple'
              },
              { 
                label: 'Throughput', 
                value: `${performanceMetrics.throughput}/min`, 
                trend: performanceMetrics.trends.throughput,
                icon: Zap,
                color: 'yellow'
              },
              { 
                label: 'Uptime', 
                value: formatPercentage(performanceMetrics.uptime), 
                trend: performanceMetrics.trends.uptime,
                icon: CheckCircle,
                color: 'green'
              },
              { 
                label: 'Error Rate', 
                value: formatPercentage(performanceMetrics.errorRate), 
                trend: performanceMetrics.trends.errorRate,
                icon: AlertTriangle,
                color: 'red'
              }
            ].map((metric, index) => {
              const IconComponent = metric.icon;
              return (
                <div key={metric.label} className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <IconComponent className={`w-4 h-4 text-${metric.color}-400`} />
                    {getTrendIcon(metric.trend)}
                  </div>
                  <div className="text-lg font-bold text-white">{metric.value}</div>
                  <div className="text-sm text-gray-400">{metric.label}</div>
                  <div className={`text-xs mt-1 ${getTrendColor(metric.trend)}`}>
                    {metric.trend > 0 ? '+' : ''}{formatPercentage(metric.trend)}
                  </div>
                </div>
              );
            })}
          </div>

          {/* System Resources */}
          <div className="mt-6 space-y-3">
            <h3 className="text-white font-medium">System Resources</h3>
            {[
              { label: 'CPU Usage', value: 67, icon: Cpu, color: 'blue' },
              { label: 'Memory', value: 54, icon: Cpu, color: 'green' },
              { label: 'Storage', value: 32, icon: HardDrive, color: 'purple' },
              { label: 'Network', value: 23, icon: Wifi, color: 'orange' }
            ].map((resource) => {
              const IconComponent = resource.icon;
              return (
                <div key={resource.label} className="flex items-center space-x-3">
                  <IconComponent className={`w-4 h-4 text-${resource.color}-400`} />
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{resource.label}</span>
                      <span className="text-white">{resource.value}%</span>
                    </div>
                    <div className="progress-bar h-2">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${resource.value}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* Middle Row: Memory & Knowledge Graph */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-panel"
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center">
            <Brain className="w-5 h-5 mr-2 text-orange-400" />
            Memory & Knowledge Graph Overview
          </h2>
          <div className="flex space-x-2">
            <button className="glass-button text-sm">
              <Network className="w-4 h-4 mr-2" />
              Visualize Graph
            </button>
            <button className="glass-button text-sm">
              <Eye className="w-4 h-4 mr-2" />
              Analyze
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { 
              label: 'Total Nodes', 
              value: memoryStats.totalNodes.toLocaleString(), 
              icon: Network,
              color: 'blue',
              change: '+12%'
            },
            { 
              label: 'Active Connections', 
              value: memoryStats.activeConnections.toLocaleString(), 
              icon: Users,
              color: 'green',
              change: '+5%'
            },
            { 
              label: 'Query Performance', 
              value: `${memoryStats.queryPerformance}s`, 
              icon: Zap,
              color: 'purple',
              change: '-8%'
            },
            { 
              label: 'Storage Efficiency', 
              value: formatPercentage(memoryStats.storageEfficiency), 
              icon: HardDrive,
              color: 'orange',
              change: '+3%'
            },
            { 
              label: 'Growth Rate', 
              value: formatPercentage(memoryStats.growthRate), 
              icon: TrendingUp,
              color: 'pink',
              change: '+15%'
            }
          ].map((stat, index) => {
            const IconComponent = stat.icon;
            return (
              <div key={stat.label} className="bg-white/5 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <IconComponent className={`w-5 h-5 text-${stat.color}-400`} />
                  <span className="text-xs text-green-400">{stat.change}</span>
                </div>
                <div className="text-lg font-bold text-white">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            );
          })}
        </div>

        {/* Knowledge Graph Visualization Placeholder */}
        <div className="mt-6 bg-black/20 rounded-lg p-6 text-center">
          <Network className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-400">Knowledge Graph Visualization</p>
          <p className="text-sm text-gray-500 mt-1">Interactive graph will be rendered here</p>
        </div>
      </motion.div>

      {/* Bottom Row: System Intelligence */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {/* Predictive Analytics */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-4 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2 text-blue-400" />
            Predictive Analytics
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Accuracy Score</span>
              <span className="text-blue-400 font-medium">{formatPercentage(systemIntelligence.predictiveAccuracy)}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill bg-gradient-to-r from-blue-400 to-blue-500" 
                style={{ width: `${systemIntelligence.predictiveAccuracy}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500">
              Forecasting system behavior and resource needs
            </div>
          </div>
        </div>

        {/* Pattern Recognition */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-4 flex items-center">
            <Eye className="w-4 h-4 mr-2 text-purple-400" />
            Pattern Recognition
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Recognition Rate</span>
              <span className="text-purple-400 font-medium">{formatPercentage(systemIntelligence.patternRecognition)}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill bg-gradient-to-r from-purple-400 to-purple-500" 
                style={{ width: `${systemIntelligence.patternRecognition}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500">
              Identifying patterns in user behavior and system usage
            </div>
          </div>
        </div>

        {/* Anomaly Detection */}
        <div className="glass-card">
          <h3 className="text-white font-medium mb-4 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2 text-red-400" />
            Anomaly Detection
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Detection Rate</span>
              <span className="text-red-400 font-medium">{formatPercentage(systemIntelligence.anomalyDetection)}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill bg-gradient-to-r from-red-400 to-red-500" 
                style={{ width: `${systemIntelligence.anomalyDetection}%` }}
              ></div>
            </div>
            <div className="text-xs text-gray-500">
              Detecting unusual patterns and potential issues
            </div>
          </div>
        </div>
      </motion.div>

      {/* Optimization Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-panel"
      >
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <Target className="w-5 h-5 mr-2 text-green-400" />
          AI-Generated Optimization Recommendations
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              priority: 'High',
              title: 'Optimize Memory Usage',
              description: 'Reduce memory consumption by 15% by implementing lazy loading for knowledge graph nodes',
              impact: 'High',
              effort: 'Medium'
            },
            {
              priority: 'Medium',
              title: 'Cache Optimization',
              description: 'Implement intelligent caching for frequently accessed agent responses',
              impact: 'Medium',
              effort: 'Low'
            },
            {
              priority: 'Medium',
              title: 'Load Balancing',
              description: 'Distribute agent workload more evenly to improve response times',
              impact: 'Medium',
              effort: 'Medium'
            },
            {
              priority: 'Low',
              title: 'Database Indexing',
              description: 'Add indexes to frequently queried fields in the knowledge base',
              impact: 'Low',
              effort: 'Low'
            }
          ].map((recommendation, index) => (
            <div key={index} className="bg-white/5 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  recommendation.priority === 'High' ? 'bg-red-500/20 text-red-400' :
                  recommendation.priority === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-green-500/20 text-green-400'
                }`}>
                  {recommendation.priority} Priority
                </span>
                <button className="glass-button text-xs">
                  Implement
                </button>
              </div>
              <h4 className="text-white font-medium mb-1">{recommendation.title}</h4>
              <p className="text-gray-400 text-sm mb-3">{recommendation.description}</p>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Impact: {recommendation.impact}</span>
                <span className="text-gray-500">Effort: {recommendation.effort}</span>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Analytics;