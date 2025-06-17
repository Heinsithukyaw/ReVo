import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, Palette, Cpu } from 'lucide-react';
import { Agent } from '../../constants/agents';

interface AgentChipProps {
  agent: Agent;
  isSelected: boolean;
  onToggle: () => void;
  engineConnected: boolean;
  engineType: Agent['engineType'];
}

const AgentChip: React.FC<AgentChipProps> = ({
  agent,
  isSelected,
  onToggle,
  engineConnected,
  engineType
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getEngineIcon = () => {
    switch (engineType) {
      case 'memory': return <Brain className="w-3 h-3" />;
      case 'parallel': return <Zap className="w-3 h-3" />;
      case 'creative': return <Palette className="w-3 h-3" />;
      case 'hybrid': return <Cpu className="w-3 h-3" />;
      default: return <Cpu className="w-3 h-3" />;
    }
  };

  const getEngineColor = () => {
    switch (engineType) {
      case 'memory': return 'text-blue-400';
      case 'parallel': return 'text-yellow-400';
      case 'creative': return 'text-pink-400';
      case 'hybrid': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const chipVariants = {
    selected: {
      background: `linear-gradient(135deg, ${agent.color}40, ${agent.color}20)`,
      borderColor: agent.color,
      scale: 1.02,
      boxShadow: `0 4px 20px ${agent.color}30`
    },
    unselected: {
      background: 'rgba(55, 65, 81, 0.5)',
      borderColor: 'rgba(75, 85, 99, 0.5)',
      scale: 1,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
    },
    hover: {
      scale: 1.05,
      background: 'rgba(75, 85, 99, 0.7)',
      borderColor: 'rgba(156, 163, 175, 0.8)'
    }
  };

  return (
    <div className="relative">
      <motion.div
        className={`agent-chip relative cursor-pointer p-3 rounded-xl border-2 transition-all duration-200 ${
          isSelected ? 'ring-2 ring-offset-2 ring-offset-gray-900' : ''
        }`}
        style={{ 
          ringColor: isSelected ? agent.color : 'transparent',
          borderColor: isSelected ? agent.color : 'rgba(75, 85, 99, 0.5)'
        }}
        variants={chipVariants}
        initial="unselected"
        animate={isSelected ? "selected" : "unselected"}
        whileHover="hover"
        whileTap={{ scale: 0.95 }}
        onClick={onToggle}
        onHoverStart={() => setShowTooltip(true)}
        onHoverEnd={() => setShowTooltip(false)}
      >
        <div className="chip-content flex flex-col items-center space-y-2">
          {/* Agent Icon */}
          <div className="relative">
            <span className="text-2xl">{agent.icon}</span>
            {engineConnected && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className={`absolute -top-1 -right-1 w-4 h-4 rounded-full bg-gray-800 border-2 border-gray-700 flex items-center justify-center ${getEngineColor()}`}
              >
                {getEngineIcon()}
              </motion.div>
            )}
          </div>

          {/* Agent Name */}
          <div className="text-center">
            <div className="text-white font-medium text-sm leading-tight">
              {agent.name}
            </div>
            <div className="text-gray-400 text-xs mt-1 capitalize">
              {agent.category}
            </div>
          </div>

          {/* Engine Type Indicator */}
          <div className={`flex items-center space-x-1 text-xs ${getEngineColor()}`}>
            {getEngineIcon()}
            <span className="capitalize">{engineType}</span>
          </div>
        </div>

        {/* Selection Glow Effect */}
        {isSelected && (
          <motion.div
            className="selection-glow absolute inset-0 rounded-xl pointer-events-none"
            style={{
              background: `linear-gradient(135deg, ${agent.color}20, transparent)`,
              border: `1px solid ${agent.color}40`
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          />
        )}

        {/* Pulse Effect for Engine Connection */}
        {engineConnected && isSelected && (
          <motion.div
            className="absolute inset-0 rounded-xl border-2 pointer-events-none"
            style={{ borderColor: agent.color }}
            animate={{
              opacity: [0.5, 1, 0.5],
              scale: [1, 1.02, 1]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}
      </motion.div>

      {/* Enhanced Tooltip */}
      {showTooltip && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.9 }}
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50"
        >
          <div className="bg-gray-800/95 backdrop-blur-md rounded-lg p-4 border border-gray-700 shadow-xl max-w-xs">
            {/* Tooltip Header */}
            <div className="tooltip-header flex items-center space-x-2 mb-2">
              <span className="text-lg">{agent.icon}</span>
              <span className="text-white font-semibold">{agent.name}</span>
              <div className={`flex items-center space-x-1 text-xs ${getEngineColor()}`}>
                {getEngineIcon()}
                <span className="capitalize">{engineType}</span>
              </div>
            </div>

            {/* Description */}
            <div className="tooltip-description text-gray-300 text-sm mb-3">
              {agent.description}
            </div>

            {/* Capabilities */}
            <div className="tooltip-capabilities">
              <div className="text-white font-medium text-sm mb-2">Capabilities:</div>
              <div className="grid grid-cols-1 gap-1">
                {agent.capabilities.map((capability, index) => (
                  <div
                    key={index}
                    className="text-xs text-gray-400 flex items-center space-x-1"
                  >
                    <div className="w-1 h-1 bg-gray-500 rounded-full"></div>
                    <span>{capability}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Engine Integration Status */}
            {engineConnected && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <div className="flex items-center space-x-2 text-xs">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-green-400">Three-Engine Integration Active</span>
                </div>
              </div>
            )}

            {/* Tooltip Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2">
              <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AgentChip;