import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Zap, Brain, Palette, Users, Settings } from 'lucide-react';
import AgentChip from '../ui/AgentChip';
import { AGENT_CATEGORIES, Agent, getAgentById } from '../../constants/agents';

interface EngineStatus {
  memory: { active: boolean; entities?: number; speed?: number };
  parallel: { active: boolean; tasks?: number; throughput?: number };
  creative: { active: boolean; ideas?: number; innovation?: number };
  mcpTools?: { count: number; active: boolean };
  revoComputer?: { status: string; active: boolean };
}

interface AgentSelectionBarProps {
  selectedAgents: string[];
  onAgentToggle: (agentId: string) => void;
  engineStatus: EngineStatus;
  threeEngineMode: boolean;
}

const AgentSelectionBar: React.FC<AgentSelectionBarProps> = ({
  selectedAgents,
  onAgentToggle,
  engineStatus,
  threeEngineMode
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const filteredAgents = useMemo(() => {
    return AGENT_CATEGORIES.map(category => ({
      ...category,
      agents: category.agents.filter(agent => {
        const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            agent.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            agent.capabilities.some(cap => cap.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const matchesCategory = !selectedCategory || category.id === selectedCategory;
        
        return matchesSearch && matchesCategory;
      })
    })).filter(category => category.agents.length > 0);
  }, [searchTerm, selectedCategory]);

  const selectedAgentCount = selectedAgents.length;
  const selectedAgentIcons = selectedAgents.map(id => getAgentById(id)?.icon || '🤖').join('');

  const engineStats = {
    memory: engineStatus.memory.entities || 0,
    parallel: engineStatus.parallel.tasks || 0,
    creative: engineStatus.creative.ideas || 0,
    mcpTools: engineStatus.mcpTools?.count || 0,
    revoComputer: engineStatus.revoComputer?.status || 'Ready'
  };

  return (
    <motion.div 
      className="agent-selection-bar bg-gray-800/40 backdrop-blur-md border-b border-gray-700/50 p-4"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {/* Header Section */}
      <div className="selection-header mb-4">
        <div className="flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
              <span className="text-3xl">🎪</span>
              <span>Multi-Agent Workspace Arena</span>
              {threeEngineMode && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="text-sm bg-gradient-to-r from-blue-500 to-purple-500 text-white px-3 py-1 rounded-full"
                >
                  ⚡ Three-Engine Mode
                </motion.span>
              )}
            </h2>
            <p className="text-gray-300 text-sm mt-1">
              Your AI Command Center - Select agents and coordinate with three engines
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="flex items-center space-x-4"
          >
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-700/50 hover:bg-gray-600/50 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span className="text-sm">Advanced</span>
            </button>
          </motion.div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4 mt-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="🔍 Search agents by name, description, or capabilities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700/50 border border-gray-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent"
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                !selectedCategory 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
              }`}
            >
              All Categories
            </button>
            {AGENT_CATEGORIES.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id === selectedCategory ? null : category.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1 ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                }`}
              >
                <span>{category.icon}</span>
                <span>{category.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Agent Categories and Selection */}
      <div className="agent-categories space-y-4">
        <AnimatePresence>
          {filteredAgents.map((category, categoryIndex) => (
            <motion.div
              key={category.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: categoryIndex * 0.1 }}
              className="agent-category"
            >
              <div className="category-label flex items-center space-x-2 mb-3">
                <span className="text-lg">{category.icon}</span>
                <span className="text-white font-medium">{category.name}</span>
                <span className="text-gray-400 text-sm">({category.agents.length} agents)</span>
              </div>
              
              <div className="agent-chips grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
                {category.agents.map((agent, agentIndex) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: (categoryIndex * 0.1) + (agentIndex * 0.05) }}
                  >
                    <AgentChip
                      agent={agent}
                      isSelected={selectedAgents.includes(agent.id)}
                      onToggle={() => onAgentToggle(agent.id)}
                      engineConnected={threeEngineMode}
                      engineType={agent.engineType}
                    />
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Active Selection Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="active-selection mt-6 p-4 bg-gray-700/30 rounded-lg border border-gray-600/30"
      >
        <div className="flex items-center justify-between">
          <div className="selection-summary">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Users className="w-5 h-5 text-blue-400" />
                <span className="text-white font-medium">
                  Active Selection: {selectedAgentIcons} [{selectedAgentCount} agents]
                </span>
              </div>
              
              {selectedAgentCount > 0 && (
                <div className="flex items-center space-x-2 text-sm text-gray-300">
                  <span>Ready for collaboration</span>
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-2 h-2 bg-green-400 rounded-full"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="engine-status flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <Brain className={`w-4 h-4 ${engineStatus.memory.active ? 'text-blue-400' : 'text-gray-500'}`} />
              <span className={engineStatus.memory.active ? 'text-blue-400' : 'text-gray-500'}>
                Memory: {engineStats.memory.toLocaleString()} entities
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Zap className={`w-4 h-4 ${engineStatus.parallel.active ? 'text-yellow-400' : 'text-gray-500'}`} />
              <span className={engineStatus.parallel.active ? 'text-yellow-400' : 'text-gray-500'}>
                Parallel: {engineStats.parallel} tasks
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <Palette className={`w-4 h-4 ${engineStatus.creative.active ? 'text-pink-400' : 'text-gray-500'}`} />
              <span className={engineStatus.creative.active ? 'text-pink-400' : 'text-gray-500'}>
                Creative: {engineStats.creative} ideas
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className="text-gray-400">🛠️ MCP Tools:</span>
              <span className="text-green-400">{engineStats.mcpTools} Available</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className="text-gray-400">🖥️ ReVo Computer:</span>
              <span className="text-green-400">{engineStats.revoComputer}</span>
            </div>
          </div>
        </div>

        {/* Advanced Stats (when expanded) */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 pt-4 border-t border-gray-600/30"
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="bg-gray-800/50 p-3 rounded-lg">
                  <div className="text-gray-400">Memory Speed</div>
                  <div className="text-white font-medium">{engineStatus.memory.speed || 95}%</div>
                </div>
                <div className="bg-gray-800/50 p-3 rounded-lg">
                  <div className="text-gray-400">Parallel Throughput</div>
                  <div className="text-white font-medium">{engineStatus.parallel.throughput || 87}%</div>
                </div>
                <div className="bg-gray-800/50 p-3 rounded-lg">
                  <div className="text-gray-400">Creative Innovation</div>
                  <div className="text-white font-medium">{engineStatus.creative.innovation || 92}%</div>
                </div>
                <div className="bg-gray-800/50 p-3 rounded-lg">
                  <div className="text-gray-400">Cost Optimization</div>
                  <div className="text-green-400 font-medium">$0.00 (100% Local)</div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
};

export default AgentSelectionBar;