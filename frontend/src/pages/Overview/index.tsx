import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, Sparkles, Activity, MessageSquare, Plus, Settings } from 'lucide-react';
import { useAppStore } from '../../store';
import { useAgents } from '../../hooks/useAgents';
import { useChat } from '../../hooks/useChat';

const Overview: React.FC = () => {
  const { engineStatuses, systemMetrics } = useAppStore();
  const { agents, isLoading: agentsLoading } = useAgents();
  const { sendMessage, isConnected } = useChat();
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');

  // Mock data for engines until backend is connected
  const engines = [
    {
      name: 'Perfect Recall Engine',
      icon: Brain,
      status: 'active',
      load: 67,
      description: 'Memory & Knowledge Management',
      metrics: {
        'Memories Stored': '1,247',
        'Recall Speed': '0.03s',
        'Knowledge Graph': '342 nodes'
      }
    },
    {
      name: 'Parallel Mind Engine', 
      icon: Zap,
      status: 'active',
      load: 45,
      description: 'Multi-Agent Coordination',
      metrics: {
        'Active Agents': agents.length.toString(),
        'Tasks Queued': '12',
        'Parallel Threads': '8'
      }
    },
    {
      name: 'Creative Engine',
      icon: Sparkles,
      status: 'active',
      load: 23,
      description: 'Innovation & Problem Solving',
      metrics: {
        'Ideas Generated': '89',
        'Solutions Proposed': '34',
        'Creativity Score': '94%'
      }
    }
  ];

  const handleNewTask = async () => {
    if (newTaskTitle.trim() && selectedAgent) {
      try {
        await sendMessage(`New task: ${newTaskTitle}`, selectedAgent);
        setNewTaskTitle('');
        setSelectedAgent('');
      } catch (error) {
        console.error('Failed to create task:', error);
      }
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Three-Engine Architecture</h1>
          <p className="text-gray-400 mt-2">Orchestrating AI intelligence across memory, parallel processing, and creativity</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Main Content - Dual Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Panel (70%) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Active Task Dashboard */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">Active Task Dashboard</h2>
              <button className="glass-button text-sm">
                <Settings className="w-4 h-4 inline mr-2" />
                Configure
              </button>
            </div>
            
            {/* New Task Creator */}
            <div className="bg-white/5 rounded-lg p-4 mb-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Create New Task</h3>
              <div className="flex space-x-3">
                <input
                  type="text"
                  placeholder="Enter task description..."
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  className="glass-input flex-1"
                />
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="glass-input w-48"
                >
                  <option value="">Select Agent</option>
                  {agents.map(agent => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleNewTask}
                  disabled={!newTaskTitle.trim() || !selectedAgent}
                  className="glass-button disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Task Progress Display */}
            <div className="space-y-3">
              {[1, 2, 3].map((task) => (
                <div key={task} className="bg-white/5 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white font-medium">Task #{task}</span>
                    <span className="text-sm text-gray-400">Progress: {task * 25}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${task * 25}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Multi-Agent Chat Interface */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-panel"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">Multi-Agent Chat Interface</h2>
              <div className="flex space-x-2">
                <button className="glass-button text-sm">
                  <MessageSquare className="w-4 h-4 inline mr-2" />
                  New Chat
                </button>
              </div>
            </div>

            {/* Chat Messages Area */}
            <div className="bg-black/20 rounded-lg p-4 h-64 overflow-y-auto mb-4">
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <Brain className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="bg-white/10 rounded-lg p-3">
                      <p className="text-white text-sm">Memory Engine initialized and ready for queries.</p>
                    </div>
                    <span className="text-xs text-gray-400 mt-1">Just now</span>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="bg-white/10 rounded-lg p-3">
                      <p className="text-white text-sm">Parallel processing agents are standing by.</p>
                    </div>
                    <span className="text-xs text-gray-400 mt-1">2 minutes ago</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Chat Input */}
            <div className="flex space-x-3">
              <input
                type="text"
                placeholder="Type your message..."
                className="glass-input flex-1"
              />
              <button className="glass-button">
                Send
              </button>
            </div>
          </motion.div>
        </div>

        {/* Right Panel (30%) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Three-Engine Status Cards */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-4"
          >
            {engines.map((engine, index) => {
              const IconComponent = engine.icon;
              return (
                <div key={engine.name} className="glass-card">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        index === 0 ? 'bg-blue-500/20' : 
                        index === 1 ? 'bg-purple-500/20' : 
                        'bg-pink-500/20'
                      }`}>
                        <IconComponent className={`w-5 h-5 ${
                          index === 0 ? 'text-blue-400' : 
                          index === 1 ? 'text-purple-400' : 
                          'text-pink-400'
                        }`} />
                      </div>
                      <div>
                        <h3 className="text-white font-medium text-sm">{engine.name}</h3>
                        <p className="text-gray-400 text-xs">{engine.description}</p>
                      </div>
                    </div>
                    <div className="status-indicator status-online"></div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">Load</span>
                      <span className="text-xs text-white">{engine.load}%</span>
                    </div>
                    <div className="progress-bar h-1">
                      <div 
                        className="progress-fill h-full" 
                        style={{ width: `${engine.load}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="mt-3 space-y-1">
                    {Object.entries(engine.metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-xs text-gray-400">{key}</span>
                        <span className="text-xs text-white font-medium">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="glass-card"
          >
            <h3 className="text-white font-medium mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full glass-button text-left justify-start">
                <Activity className="w-4 h-4 mr-2" />
                System Health Check
              </button>
              <button className="w-full glass-button text-left justify-start">
                <Brain className="w-4 h-4 mr-2" />
                Memory Optimization
              </button>
              <button className="w-full glass-button text-left justify-start">
                <Zap className="w-4 h-4 mr-2" />
                Agent Coordination
              </button>
              <button className="w-full glass-button text-left justify-start">
                <Sparkles className="w-4 h-4 mr-2" />
                Creative Session
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Section - System Intelligence */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        <div className="glass-card">
          <h3 className="text-white font-medium mb-3">System Intelligence</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Intelligence Score</span>
              <span className="text-green-400 font-medium">94%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Learning Rate</span>
              <span className="text-blue-400 font-medium">+12%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Adaptation Speed</span>
              <span className="text-purple-400 font-medium">2.3s</span>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <h3 className="text-white font-medium mb-3">Cost Optimization</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Total Saved</span>
              <span className="text-green-400 font-medium text-lg">$0.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">This Month</span>
              <span className="text-blue-400 font-medium">$0.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Efficiency</span>
              <span className="text-purple-400 font-medium">100%</span>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <h3 className="text-white font-medium mb-3">Performance</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Response Time</span>
              <span className="text-green-400 font-medium">0.8s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Uptime</span>
              <span className="text-blue-400 font-medium">99.9%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Throughput</span>
              <span className="text-purple-400 font-medium">1.2k/min</span>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Overview;
