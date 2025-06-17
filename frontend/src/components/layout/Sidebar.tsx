import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  Brain, 
  Zap, 
  Palette, 
  Settings, 
  Activity,
  Users,
  MessageSquare,
  BarChart3,
  Cpu,
  Database,
  Network,
  Shield
} from 'lucide-react';
import ThreeEngineStatus from '../sidebar/ThreeEngineStatus';
import MemoryManager from '../sidebar/MemoryManager';
import MCPToolsPanel from '../sidebar/MCPToolsPanel';
import ReVoComputerStatus from '../sidebar/ReVoComputerStatus';

interface Message {
  id: string;
  content: string;
  sender: string;
  senderName: string;
  senderIcon: string;
  timestamp: Date;
}

interface EngineStatus {
  memory: { active: boolean; entities?: number; speed?: number };
  parallel: { active: boolean; tasks?: number; throughput?: number };
  creative: { active: boolean; ideas?: number; innovation?: number };
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  engineStatus: EngineStatus;
  selectedAgents: string[];
  conversations: Message[];
  isConnected: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  engineStatus,
  selectedAgents,
  conversations,
  isConnected
}) => {
  const [activeTab, setActiveTab] = useState<'engines' | 'memory' | 'tools' | 'computer' | 'stats'>('engines');

  const tabs = [
    { id: 'engines', label: 'Engines', icon: Zap, color: 'text-yellow-400' },
    { id: 'memory', label: 'Memory', icon: Brain, color: 'text-blue-400' },
    { id: 'tools', label: 'MCP Tools', icon: Settings, color: 'text-green-400' },
    { id: 'computer', label: 'ReVo Computer', icon: Cpu, color: 'text-purple-400' },
    { id: 'stats', label: 'Statistics', icon: BarChart3, color: 'text-pink-400' }
  ];

  const sidebarVariants = {
    expanded: { width: 320 },
    collapsed: { width: 64 }
  };

  const contentVariants = {
    expanded: { opacity: 1, x: 0 },
    collapsed: { opacity: 0, x: 20 }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'engines':
        return (
          <ThreeEngineStatus 
            engineStatus={engineStatus}
            isConnected={isConnected}
          />
        );
      case 'memory':
        return (
          <MemoryManager 
            conversations={conversations}
            selectedAgents={selectedAgents}
          />
        );
      case 'tools':
        return (
          <MCPToolsPanel 
            selectedAgents={selectedAgents}
          />
        );
      case 'computer':
        return (
          <ReVoComputerStatus 
            isConnected={isConnected}
          />
        );
      case 'stats':
        return (
          <div className="space-y-4">
            <div className="bg-gray-700/30 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
                <Users className="w-4 h-4" />
                <span>Agent Statistics</span>
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Selected Agents:</span>
                  <span className="text-white">{selectedAgents.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Messages:</span>
                  <span className="text-white">{conversations.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Connection Status:</span>
                  <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-700/30 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>System Health</span>
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Memory Engine</span>
                  <div className={`w-3 h-3 rounded-full ${
                    engineStatus.memory.active ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Parallel Engine</span>
                  <div className={`w-3 h-3 rounded-full ${
                    engineStatus.parallel.active ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Creative Engine</span>
                  <div className={`w-3 h-3 rounded-full ${
                    engineStatus.creative.active ? 'bg-green-400' : 'bg-red-400'
                  }`} />
                </div>
              </div>
            </div>

            <div className="bg-gray-700/30 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
                <Shield className="w-4 h-4" />
                <span>Security</span>
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Local Processing:</span>
                  <span className="text-green-400">100%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Cost Optimization:</span>
                  <span className="text-green-400">$0.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Data Privacy:</span>
                  <span className="text-green-400">Secured</span>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <motion.div
      className="sidebar bg-gray-800/60 backdrop-blur-md border-l border-gray-700/50 h-full flex flex-col"
      variants={sidebarVariants}
      animate={collapsed ? "collapsed" : "expanded"}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      {/* Sidebar Header */}
      <div className="sidebar-header p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                variants={contentVariants}
                initial="collapsed"
                animate="expanded"
                exit="collapsed"
                className="flex items-center space-x-2"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h2 className="text-white font-semibold text-sm">Control Center</h2>
                  <p className="text-gray-400 text-xs">Three-Engine Coordination</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <button
            onClick={onToggle}
            className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
          >
            {collapsed ? (
              <ChevronLeft className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-400" />
            )}
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation p-2 border-b border-gray-700/50">
        {collapsed ? (
          <div className="space-y-2">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full p-2 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-gray-700/50 text-white'
                      : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
                  }`}
                  title={tab.label}
                >
                  <Icon className="w-4 h-4 mx-auto" />
                </button>
              );
            })}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-1">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`p-2 rounded-lg transition-colors text-xs font-medium ${
                    activeTab === tab.id
                      ? 'bg-gray-700/50 text-white'
                      : 'text-gray-400 hover:bg-gray-700/30 hover:text-white'
                  }`}
                >
                  <Icon className="w-3 h-3 mx-auto mb-1" />
                  <div className="truncate">{tab.label}</div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Tab Content */}
      <div className="tab-content flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              key={activeTab}
              variants={contentVariants}
              initial="collapsed"
              animate="expanded"
              exit="collapsed"
              transition={{ duration: 0.2 }}
              className="p-4"
            >
              {renderTabContent()}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Sidebar Footer */}
      {!collapsed && (
        <motion.div
          variants={contentVariants}
          initial="collapsed"
          animate="expanded"
          exit="collapsed"
          className="sidebar-footer p-4 border-t border-gray-700/50"
        >
          <div className="text-center">
            <div className="text-xs text-gray-400 mb-2">reVoAgent v1.0</div>
            <div className="flex items-center justify-center space-x-2 text-xs">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400' : 'bg-red-400'
              }`} />
              <span className="text-gray-400">
                {isConnected ? 'System Online' : 'Reconnecting...'}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Sidebar;