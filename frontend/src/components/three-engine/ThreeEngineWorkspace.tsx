import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Zap,
  Palette,
  Activity,
  Database,
  Cpu,
  Network,
  Workflow,
  GitBranch,
  Layers,
  Target,
  Gauge,
  Timer,
  TrendingUp,
  BarChart3,
  PieChart,
  LineChart,
  RefreshCw,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Maximize2,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Shield,
  CheckCircle,
  AlertCircle,
  Clock,
  Lightbulb,
  Rocket,
  Star,
  Award,
  Users,
  MessageSquare,
  FileText,
  Code,
  Image,
  Video,
  Music,
  Sparkles,
  Flame,
  Snowflake,
  Sun,
  Moon
} from 'lucide-react';

// Import workspace data integration
import { useThreeEngines } from '../../hooks/useThreeEngines';

interface EngineMetrics {
  id: 'memory' | 'parallel' | 'creative';
  name: string;
  icon: React.ReactNode;
  color: string;
  gradient: string;
  status: 'active' | 'idle' | 'processing' | 'optimizing';
  performance: number;
  workload: number;
  efficiency: number;
  uptime: number;
  tasksProcessed: number;
  currentTasks: number;
  avgProcessingTime: number;
  successRate: number;
  innovations: number;
  collaborations: number;
  specialMetrics: {
    [key: string]: any;
  };
}

const ThreeEngineWorkspace: React.FC = () => {
  const [selectedEngine, setSelectedEngine] = useState<'memory' | 'parallel' | 'creative' | 'all'>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'workflow' | 'analytics'>('overview');
  const [isAutoOptimizing, setIsAutoOptimizing] = useState(true);
  const [showAdvancedMetrics, setShowAdvancedMetrics] = useState(false);
  
  // Use workspace integration hook
  const { 
    memoryEngine, 
    parallelEngine, 
    creativeEngine, 
    isCoordinating, 
    coordinationMode,
    startCoordination,
    stopCoordination 
  } = useThreeEngines();

  const [engineMetrics, setEngineMetrics] = useState<EngineMetrics[]>([
    {
      id: 'memory',
      name: 'Memory Engine',
      icon: <Brain className="w-8 h-8" />,
      color: 'text-blue-400',
      gradient: 'from-blue-500 to-cyan-500',
      status: 'active',
      performance: 94.2,
      workload: 67.8,
      efficiency: 91.5,
      uptime: 99.8,
      tasksProcessed: 1248038,
      currentTasks: 23,
      avgProcessingTime: 0.12,
      successRate: 99.2,
      innovations: 156,
      collaborations: 892,
      specialMetrics: {
        entitiesStored: 1248038,
        memoryUtilization: 67.8,
        retrievalSpeed: 0.08,
        contextAccuracy: 96.7,
        knowledgeGraphs: 45,
        semanticConnections: 15420
      }
    },
    {
      id: 'parallel',
      name: 'Parallel Engine',
      icon: <Zap className="w-8 h-8" />,
      color: 'text-yellow-400',
      gradient: 'from-yellow-500 to-orange-500',
      status: 'processing',
      performance: 97.1,
      workload: 82.3,
      efficiency: 95.8,
      uptime: 99.9,
      tasksProcessed: 567234,
      currentTasks: 47,
      avgProcessingTime: 0.05,
      successRate: 98.9,
      innovations: 203,
      collaborations: 1156,
      specialMetrics: {
        threadsActive: 47,
        queueLength: 12,
        throughput: 1250,
        concurrency: 95.8,
        loadBalancing: 98.2,
        resourceOptimization: 94.1
      }
    },
    {
      id: 'creative',
      name: 'Creative Engine',
      icon: <Palette className="w-8 h-8" />,
      color: 'text-pink-400',
      gradient: 'from-pink-500 to-purple-500',
      status: 'optimizing',
      performance: 89.7,
      workload: 54.2,
      efficiency: 87.3,
      uptime: 99.5,
      tasksProcessed: 234567,
      currentTasks: 18,
      avgProcessingTime: 0.28,
      successRate: 96.4,
      innovations: 445,
      collaborations: 678,
      specialMetrics: {
        ideasGenerated: 445,
        creativityIndex: 92.1,
        originalityScore: 88.7,
        inspirationSources: 234,
        artisticVariations: 1567,
        multiModalOutputs: 892
      }
    }
  ]);

  // Real-time updates from workspace
  useEffect(() => {
    const updateMetrics = () => {
      setEngineMetrics(prev => prev.map(engine => {
        // Integrate with workspace data
        let workspaceData = {};
        if (engine.id === 'memory') workspaceData = memoryEngine;
        if (engine.id === 'parallel') workspaceData = parallelEngine;
        if (engine.id === 'creative') workspaceData = creativeEngine;

        return {
          ...engine,
          ...workspaceData,
          performance: Math.max(85, Math.min(100, engine.performance + (Math.random() - 0.5) * 2)),
          workload: Math.max(0, Math.min(100, engine.workload + (Math.random() - 0.5) * 5)),
          currentTasks: Math.max(0, engine.currentTasks + Math.floor((Math.random() - 0.5) * 3)),
          tasksProcessed: engine.tasksProcessed + Math.floor(Math.random() * 10)
        };
      }));
    };

    const interval = setInterval(updateMetrics, 2000);
    return () => clearInterval(interval);
  }, [memoryEngine, parallelEngine, creativeEngine]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'processing': return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'optimizing': return <Target className="w-4 h-4 text-yellow-400" />;
      case 'idle': return <Clock className="w-4 h-4 text-gray-400" />;
      default: return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const getPerformanceColor = (performance: number) => {
    if (performance >= 95) return 'text-green-400';
    if (performance >= 85) return 'text-yellow-400';
    if (performance >= 75) return 'text-orange-400';
    return 'text-red-400';
  };

  const overallMetrics = {
    avgPerformance: engineMetrics.reduce((sum, e) => sum + e.performance, 0) / engineMetrics.length,
    totalTasks: engineMetrics.reduce((sum, e) => sum + e.tasksProcessed, 0),
    avgEfficiency: engineMetrics.reduce((sum, e) => sum + e.efficiency, 0) / engineMetrics.length,
    totalInnovations: engineMetrics.reduce((sum, e) => sum + e.innovations, 0),
    coordinationScore: isCoordinating ? 98.5 : 0
  };

  return (
    <div className="h-full bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800/60 backdrop-blur-md border-b border-gray-700/50 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="flex items-center space-x-1">
                  <Brain className="w-8 h-8 text-blue-400" />
                  <Zap className="w-8 h-8 text-yellow-400" />
                  <Palette className="w-8 h-8 text-pink-400" />
                </div>
                {isCoordinating && (
                  <motion.div
                    className="absolute -inset-2 border-2 border-purple-500/50 rounded-lg"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Three-Engine Coordination</h1>
                <p className="text-gray-400">Memory • Parallel • Creative Integration</p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Coordination Control */}
            <div className="flex items-center space-x-2">
              <button
                onClick={isCoordinating ? stopCoordination : startCoordination}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  isCoordinating
                    ? 'bg-red-600/20 text-red-400 border border-red-500/30'
                    : 'bg-green-600/20 text-green-400 border border-green-500/30'
                }`}
              >
                {isCoordinating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                <span>{isCoordinating ? 'Stop' : 'Start'} Coordination</span>
              </button>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-1 bg-gray-700/50 rounded-lg p-1">
              {(['overview', 'detailed', 'workflow', 'analytics'] as const).map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    viewMode === mode
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>

            <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Overall Status */}
        <div className="mt-6 grid grid-cols-5 gap-4">
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-purple-400 font-bold text-2xl">{overallMetrics.avgPerformance.toFixed(1)}%</div>
            <div className="text-gray-400 text-sm">Overall Performance</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-blue-400 font-bold text-2xl">{overallMetrics.totalTasks.toLocaleString()}</div>
            <div className="text-gray-400 text-sm">Total Tasks</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-green-400 font-bold text-2xl">{overallMetrics.avgEfficiency.toFixed(1)}%</div>
            <div className="text-gray-400 text-sm">Efficiency</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className="text-yellow-400 font-bold text-2xl">{overallMetrics.totalInnovations}</div>
            <div className="text-gray-400 text-sm">Innovations</div>
          </div>
          <div className="bg-gray-700/30 rounded-lg p-4 text-center">
            <div className={`font-bold text-2xl ${isCoordinating ? 'text-green-400' : 'text-gray-400'}`}>
              {overallMetrics.coordinationScore.toFixed(1)}%
            </div>
            <div className="text-gray-400 text-sm">Coordination</div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {viewMode === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {engineMetrics.map((engine, index) => (
              <motion.div
                key={engine.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
                className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6 hover:border-gray-600/50 transition-all"
              >
                {/* Engine Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className={`p-3 rounded-xl bg-gradient-to-r ${engine.gradient} bg-opacity-20`}>
                      <div className={engine.color}>
                        {engine.icon}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-white font-bold text-lg">{engine.name}</h3>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(engine.status)}
                        <span className="text-gray-400 text-sm capitalize">{engine.status}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Performance Ring */}
                <div className="relative mb-6">
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
                        strokeDashoffset={`${2 * Math.PI * 40 * (1 - engine.performance / 100)}`}
                        className={engine.color}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className={`text-2xl font-bold ${getPerformanceColor(engine.performance)}`}>
                          {engine.performance.toFixed(1)}%
                        </div>
                        <div className="text-gray-400 text-xs">Performance</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-white font-semibold text-lg">{engine.currentTasks}</div>
                    <div className="text-gray-400 text-sm">Active Tasks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-semibold text-lg">{engine.avgProcessingTime.toFixed(2)}s</div>
                    <div className="text-gray-400 text-sm">Avg Time</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-semibold text-lg">{engine.successRate}%</div>
                    <div className="text-gray-400 text-sm">Success Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-white font-semibold text-lg">{engine.innovations}</div>
                    <div className="text-gray-400 text-sm">Innovations</div>
                  </div>
                </div>

                {/* Workload Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400 text-sm">Workload</span>
                    <span className="text-white text-sm">{engine.workload.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-700/50 rounded-full h-3">
                    <motion.div
                      className={`h-3 rounded-full bg-gradient-to-r ${engine.gradient}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${engine.workload}%` }}
                      transition={{ duration: 1, delay: index * 0.2 }}
                    />
                  </div>
                </div>

                {/* Special Metrics Preview */}
                <div className="space-y-2">
                  {Object.entries(engine.specialMetrics).slice(0, 2).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                      <span className="text-white font-medium">
                        {typeof value === 'number' ? value.toLocaleString() : value}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Engine Actions */}
                <div className="mt-6 flex items-center justify-between">
                  <button
                    onClick={() => setSelectedEngine(engine.id)}
                    className="px-4 py-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg text-sm text-gray-300 transition-colors"
                  >
                    View Details
                  </button>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
                      <Eye className="w-4 h-4 text-gray-400" />
                    </button>
                    <button className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors">
                      <Settings className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {viewMode === 'workflow' && (
          <div className="space-y-6">
            {/* Coordination Flow */}
            <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
              <h3 className="text-white font-semibold mb-6 flex items-center space-x-2">
                <Workflow className="w-6 h-6 text-purple-400" />
                <span>Three-Engine Coordination Flow</span>
              </h3>
              
              <div className="relative">
                {/* Flow Diagram */}
                <div className="flex items-center justify-between">
                  {engineMetrics.map((engine, index) => (
                    <div key={engine.id} className="flex flex-col items-center space-y-4">
                      {/* Engine Node */}
                      <motion.div
                        className={`relative p-6 rounded-xl bg-gradient-to-r ${engine.gradient} bg-opacity-20 border-2 ${
                          isCoordinating ? 'border-purple-500/50' : 'border-gray-600/30'
                        }`}
                        animate={isCoordinating ? { scale: [1, 1.05, 1] } : {}}
                        transition={{ duration: 2, repeat: Infinity, delay: index * 0.5 }}
                      >
                        <div className={engine.color}>
                          {engine.icon}
                        </div>
                        {isCoordinating && (
                          <motion.div
                            className="absolute -inset-1 border-2 border-purple-400/30 rounded-xl"
                            animate={{ opacity: [0.3, 0.8, 0.3] }}
                            transition={{ duration: 1.5, repeat: Infinity, delay: index * 0.3 }}
                          />
                        )}
                      </motion.div>
                      
                      {/* Engine Info */}
                      <div className="text-center">
                        <div className="text-white font-medium">{engine.name}</div>
                        <div className="text-gray-400 text-sm">{engine.currentTasks} tasks</div>
                        <div className={`text-sm font-semibold ${getPerformanceColor(engine.performance)}`}>
                          {engine.performance.toFixed(1)}%
                        </div>
                      </div>
                      
                      {/* Connection Lines */}
                      {index < engineMetrics.length - 1 && (
                        <motion.div
                          className="absolute top-1/2 left-full w-24 h-0.5 bg-gradient-to-r from-purple-500 to-transparent"
                          style={{ transform: 'translateY(-50%)' }}
                          animate={isCoordinating ? { opacity: [0.3, 1, 0.3] } : { opacity: 0.3 }}
                          transition={{ duration: 1, repeat: Infinity, delay: index * 0.2 }}
                        />
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Coordination Status */}
                <div className="mt-8 text-center">
                  <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg ${
                    isCoordinating 
                      ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                      : 'bg-gray-700/30 text-gray-400 border border-gray-600/30'
                  }`}>
                    {isCoordinating ? (
                      <>
                        <CheckCircle className="w-4 h-4" />
                        <span>Engines Coordinating - Mode: {coordinationMode}</span>
                      </>
                    ) : (
                      <>
                        <Clock className="w-4 h-4" />
                        <span>Coordination Inactive</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Real-time Coordination Metrics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
                <h4 className="text-white font-semibold mb-4 flex items-center space-x-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  <span>Coordination Efficiency</span>
                </h4>
                <div className="space-y-4">
                  {['Memory-Parallel Sync', 'Parallel-Creative Flow', 'Creative-Memory Loop'].map((metric, index) => {
                    const efficiency = 85 + Math.random() * 15;
                    return (
                      <div key={metric} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-300 text-sm">{metric}</span>
                          <span className="text-white font-medium">{efficiency.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-700/50 rounded-full h-2">
                          <motion.div
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                            initial={{ width: 0 }}
                            animate={{ width: `${efficiency}%` }}
                            transition={{ duration: 1, delay: index * 0.2 }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-gray-800/40 backdrop-blur-md border border-gray-700/30 rounded-xl p-6">
                <h4 className="text-white font-semibold mb-4 flex items-center space-x-2">
                  <Network className="w-5 h-5 text-green-400" />
                  <span>Data Flow</span>
                </h4>
                <div className="space-y-4">
                  {engineMetrics.map(engine => (
                    <div key={engine.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={engine.color}>
                          {React.cloneElement(engine.icon as React.ReactElement, { className: 'w-5 h-5' })}
                        </div>
                        <span className="text-white text-sm">{engine.name}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-medium">{(Math.random() * 1000 + 500).toFixed(0)} MB/s</div>
                        <div className="text-gray-400 text-xs">Data throughput</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ThreeEngineWorkspace;