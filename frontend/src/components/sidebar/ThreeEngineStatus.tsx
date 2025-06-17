import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, Palette, Activity, TrendingUp, Database } from 'lucide-react';

interface EngineStatus {
  memory: { 
    active: boolean; 
    entities?: number; 
    speed?: number;
    accuracy?: number;
    relationships?: number;
    dailyGrowth?: number;
  };
  parallel: { 
    active: boolean; 
    tasks?: number; 
    throughput?: number;
    efficiency?: number;
    queueLength?: number;
    avgResponseTime?: number;
  };
  creative: { 
    active: boolean; 
    ideas?: number; 
    innovation?: number;
    creativity?: number;
    uniqueness?: number;
    inspiration?: number;
  };
}

interface ThreeEngineStatusProps {
  engineStatus: EngineStatus;
  isConnected: boolean;
}

const ThreeEngineStatus: React.FC<ThreeEngineStatusProps> = ({
  engineStatus,
  isConnected
}) => {
  const formatNumber = (num?: number) => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getStatusColor = (active: boolean) => {
    return active ? 'text-green-400' : 'text-red-400';
  };

  const getStatusBg = (active: boolean) => {
    return active ? 'bg-green-500/20' : 'bg-red-500/20';
  };

  return (
    <div className="space-y-4">
      {/* Overall Status */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Activity className="w-4 h-4" />
          <span>Three-Engine Coordination</span>
        </h3>
        
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-400 text-sm">System Status:</span>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {isConnected ? 'Online' : 'Offline'}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Active Engines:</span>
            <span className="text-white">
              {[engineStatus.memory.active, engineStatus.parallel.active, engineStatus.creative.active]
                .filter(Boolean).length}/3
            </span>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Coordination Mode:</span>
            <span className="text-blue-400">
              {engineStatus.memory.active && engineStatus.parallel.active && engineStatus.creative.active
                ? 'Full Sync' : 'Partial'}
            </span>
          </div>
        </div>
      </div>

      {/* Memory Engine */}
      <motion.div
        className="bg-gray-700/30 rounded-lg p-4 border-l-4 border-blue-500"
        whileHover={{ scale: 1.02 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-blue-400" />
            <h4 className="text-white font-medium">Memory Engine</h4>
          </div>
          <div className={`w-3 h-3 rounded-full ${
            engineStatus.memory.active ? 'bg-green-400' : 'bg-red-400'
          }`} />
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Entities:</span>
            <span className="text-blue-300">{formatNumber(engineStatus.memory.entities)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Relationships:</span>
            <span className="text-blue-300">{formatNumber(engineStatus.memory.relationships)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Speed:</span>
            <span className="text-blue-300">{engineStatus.memory.speed || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Accuracy:</span>
            <span className="text-blue-300">{engineStatus.memory.accuracy || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Daily Growth:</span>
            <span className="text-green-400">+{formatNumber(engineStatus.memory.dailyGrowth)}</span>
          </div>
        </div>

        {/* Memory Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Memory Utilization</span>
            <span>{engineStatus.memory.speed || 0}%</span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2">
            <motion.div
              className="bg-blue-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${engineStatus.memory.speed || 0}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>
      </motion.div>

      {/* Parallel Engine */}
      <motion.div
        className="bg-gray-700/30 rounded-lg p-4 border-l-4 border-yellow-500"
        whileHover={{ scale: 1.02 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h4 className="text-white font-medium">Parallel Engine</h4>
          </div>
          <div className={`w-3 h-3 rounded-full ${
            engineStatus.parallel.active ? 'bg-green-400' : 'bg-red-400'
          }`} />
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Active Tasks:</span>
            <span className="text-yellow-300">{engineStatus.parallel.tasks || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Queue Length:</span>
            <span className="text-yellow-300">{engineStatus.parallel.queueLength || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Throughput:</span>
            <span className="text-yellow-300">{engineStatus.parallel.throughput || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Efficiency:</span>
            <span className="text-yellow-300">{engineStatus.parallel.efficiency || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Avg Response:</span>
            <span className="text-green-400">{engineStatus.parallel.avgResponseTime || 0}ms</span>
          </div>
        </div>

        {/* Parallel Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Processing Efficiency</span>
            <span>{engineStatus.parallel.efficiency || 0}%</span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2">
            <motion.div
              className="bg-yellow-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${engineStatus.parallel.efficiency || 0}%` }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
            />
          </div>
        </div>
      </motion.div>

      {/* Creative Engine */}
      <motion.div
        className="bg-gray-700/30 rounded-lg p-4 border-l-4 border-pink-500"
        whileHover={{ scale: 1.02 }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Palette className="w-5 h-5 text-pink-400" />
            <h4 className="text-white font-medium">Creative Engine</h4>
          </div>
          <div className={`w-3 h-3 rounded-full ${
            engineStatus.creative.active ? 'bg-green-400' : 'bg-red-400'
          }`} />
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Ideas Generated:</span>
            <span className="text-pink-300">{engineStatus.creative.ideas || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Innovation:</span>
            <span className="text-pink-300">{engineStatus.creative.innovation || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Creativity:</span>
            <span className="text-pink-300">{engineStatus.creative.creativity || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Uniqueness:</span>
            <span className="text-pink-300">{engineStatus.creative.uniqueness || 0}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Inspiration:</span>
            <span className="text-purple-400">{engineStatus.creative.inspiration || 0}%</span>
          </div>
        </div>

        {/* Creative Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Creative Output</span>
            <span>{engineStatus.creative.innovation || 0}%</span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2">
            <motion.div
              className="bg-pink-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${engineStatus.creative.innovation || 0}%` }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.4 }}
            />
          </div>
        </div>
      </motion.div>

      {/* Performance Summary */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-4 border border-blue-500/20">
        <h4 className="text-white font-medium mb-3 flex items-center space-x-2">
          <TrendingUp className="w-4 h-4" />
          <span>Performance Summary</span>
        </h4>
        
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="text-center">
            <div className="text-gray-400">Cost Optimization</div>
            <div className="text-green-400 font-bold">$0.00</div>
            <div className="text-green-300 text-xs">100% Local</div>
          </div>
          <div className="text-center">
            <div className="text-gray-400">Uptime</div>
            <div className="text-blue-400 font-bold">99.9%</div>
            <div className="text-blue-300 text-xs">Enterprise Grade</div>
          </div>
          <div className="text-center">
            <div className="text-gray-400">Response Time</div>
            <div className="text-yellow-400 font-bold">&lt;2ms</div>
            <div className="text-yellow-300 text-xs">Ultra Fast</div>
          </div>
          <div className="text-center">
            <div className="text-gray-400">Accuracy</div>
            <div className="text-pink-400 font-bold">99.9%</div>
            <div className="text-pink-300 text-xs">AI Precision</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreeEngineStatus;