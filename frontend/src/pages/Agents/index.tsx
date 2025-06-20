import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Code, Workflow, Database, Link, Play, Pause, Settings, 
  Activity, CheckCircle, XCircle, Clock, Users, GitBranch,
  Search, Filter, Plus, MoreVertical
} from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';

const Agents: React.FC = () => {
  const { agents, isLoading, createAgent, updateAgent, deleteAgent } = useAgents();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Mock agent data organized by categories
  const agentCategories = {
    code: {
      title: 'Code Team Agents',
      icon: Code,
      color: 'blue',
      agents: [
        { id: '1', name: 'Frontend Developer', status: 'active', tasks: 12, successRate: 94 },
        { id: '2', name: 'Backend Engineer', status: 'active', tasks: 8, successRate: 96 },
        { id: '3', name: 'DevOps Specialist', status: 'busy', tasks: 5, successRate: 92 },
        { id: '4', name: 'Code Reviewer', status: 'active', tasks: 15, successRate: 98 }
      ]
    },
    workflow: {
      title: 'Workflow Management',
      icon: Workflow,
      color: 'purple',
      agents: [
        { id: '5', name: 'Project Manager', status: 'active', tasks: 20, successRate: 89 },
        { id: '6', name: 'CI/CD Pipeline', status: 'active', tasks: 30, successRate: 95 },
        { id: '7', name: 'Task Coordinator', status: 'active', tasks: 18, successRate: 91 },
        { id: '8', name: 'Quality Assurance', status: 'busy', tasks: 7, successRate: 97 }
      ]
    },
    knowledge: {
      title: 'Knowledge & Memory',
      icon: Database,
      color: 'green',
      agents: [
        { id: '9', name: 'Knowledge Curator', status: 'active', tasks: 25, successRate: 93 },
        { id: '10', name: 'Memory Manager', status: 'active', tasks: 40, successRate: 96 },
        { id: '11', name: 'Research Assistant', status: 'active', tasks: 12, successRate: 88 },
        { id: '12', name: 'Data Analyst', status: 'busy', tasks: 9, successRate: 94 }
      ]
    },
    integration: {
      title: 'Integration & Communication',
      icon: Link,
      color: 'orange',
      agents: [
        { id: '13', name: 'API Gateway', status: 'active', tasks: 35, successRate: 99 },
        { id: '14', name: 'Webhook Manager', status: 'active', tasks: 22, successRate: 97 },
        { id: '15', name: 'External Connector', status: 'active', tasks: 14, successRate: 90 },
        { id: '16', name: 'Message Broker', status: 'error', tasks: 3, successRate: 85 }
      ]
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'busy': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'busy': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'error': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getCategoryColor = (color: string) => {
    const colors = {
      blue: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
      purple: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
      green: 'bg-green-500/10 border-green-500/30 text-green-400',
      orange: 'bg-orange-500/10 border-orange-500/30 text-orange-400'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">AI Agents Control Center</h1>
          <p className="text-gray-400 mt-2">Manage and monitor your 20+ specialized AI agents</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="glass-input w-64"
            />
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="glass-button"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Agent
          </button>
        </div>
      </div>

      {/* Agent Orchestration Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel"
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-white">Agent Orchestration</h2>
          <div className="flex space-x-3">
            <button className="glass-button">
              <Users className="w-4 h-4 mr-2" />
              Multi-Agent Task
            </button>
            <button className="glass-button">
              <GitBranch className="w-4 h-4 mr-2" />
              Collaboration Setup
            </button>
            <button className="glass-button">
              <Activity className="w-4 h-4 mr-2" />
              Performance Monitor
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white/5 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">16</div>
            <div className="text-sm text-gray-400">Active Agents</div>
          </div>
          <div className="bg-white/5 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">143</div>
            <div className="text-sm text-gray-400">Tasks Completed</div>
          </div>
          <div className="bg-white/5 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-400">94%</div>
            <div className="text-sm text-gray-400">Success Rate</div>
          </div>
          <div className="bg-white/5 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-400">2.3s</div>
            <div className="text-sm text-gray-400">Avg Response</div>
          </div>
        </div>
      </motion.div>

      {/* Four-Column Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        {Object.entries(agentCategories).map(([key, category], categoryIndex) => {
          const IconComponent = category.icon;
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: categoryIndex * 0.1 }}
              className="glass-card"
            >
              {/* Category Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${getCategoryColor(category.color)}`}>
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-white font-medium">{category.title}</h3>
                    <p className="text-xs text-gray-400">{category.agents.length} agents</p>
                  </div>
                </div>
                <button className="text-gray-400 hover:text-white">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>

              {/* Agent List */}
              <div className="space-y-3">
                {category.agents.map((agent, agentIndex) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: (categoryIndex * 0.1) + (agentIndex * 0.05) }}
                    className="bg-white/5 rounded-lg p-3 hover:bg-white/10 transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(agent.status)}
                        <span className="text-white text-sm font-medium">{agent.name}</span>
                      </div>
                      <div className="flex space-x-1">
                        <button className="text-gray-400 hover:text-green-400 p-1">
                          <Play className="w-3 h-3" />
                        </button>
                        <button className="text-gray-400 hover:text-yellow-400 p-1">
                          <Pause className="w-3 h-3" />
                        </button>
                        <button className="text-gray-400 hover:text-blue-400 p-1">
                          <Settings className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-400">Tasks: {agent.tasks}</span>
                      <span className="text-gray-400">Success: {agent.successRate}%</span>
                    </div>
                    
                    <div className="mt-2">
                      <div className="progress-bar h-1">
                        <div 
                          className="progress-fill h-full" 
                          style={{ width: `${agent.successRate}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className={`inline-block px-2 py-1 rounded text-xs font-medium mt-2 border ${getStatusColor(agent.status)}`}>
                      {agent.status.toUpperCase()}
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Category Controls */}
              <div className="mt-4 pt-3 border-t border-white/10">
                <div className="flex justify-between">
                  <button className="text-xs text-gray-400 hover:text-white">
                    View All
                  </button>
                  <button className="text-xs text-gray-400 hover:text-white">
                    Configure
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-panel"
      >
        <h2 className="text-xl font-semibold text-white mb-4">Recent Agent Activity</h2>
        <div className="space-y-3">
          {[
            { agent: 'Frontend Developer', action: 'Completed React component optimization', time: '2 minutes ago', status: 'success' },
            { agent: 'CI/CD Pipeline', action: 'Deployed version 2.3.4 to production', time: '5 minutes ago', status: 'success' },
            { agent: 'Code Reviewer', action: 'Reviewed pull request #247', time: '8 minutes ago', status: 'success' },
            { agent: 'Message Broker', action: 'Connection timeout to external API', time: '12 minutes ago', status: 'error' },
            { agent: 'Memory Manager', action: 'Optimized knowledge graph structure', time: '15 minutes ago', status: 'success' }
          ].map((activity, index) => (
            <div key={index} className="activity-item">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                activity.status === 'success' ? 'bg-green-500/20' : 'bg-red-500/20'
              }`}>
                {activity.status === 'success' ? 
                  <CheckCircle className="w-4 h-4 text-green-400" /> : 
                  <XCircle className="w-4 h-4 text-red-400" />
                }
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-white text-sm font-medium">{activity.agent}</p>
                    <p className="text-gray-400 text-sm">{activity.action}</p>
                  </div>
                  <span className="text-xs text-gray-500">{activity.time}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default Agents;
