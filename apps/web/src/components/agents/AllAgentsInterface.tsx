import React, { useState, useEffect } from 'react';
import { 
  Code, 
  Bug, 
  TestTube, 
  Rocket, 
  Globe, 
  Shield, 
  FileText, 
  Zap, 
  Brain,
  Play,
  Pause,
  Settings,
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Users,
  Sparkles
} from 'lucide-react';

interface AllAgentsInterfaceProps {
  agentUpdates: any;
  onAgentSelect: (agentType: string) => void;
}

const AllAgentsInterface: React.FC<AllAgentsInterfaceProps> = ({
  agentUpdates,
  onAgentSelect
}) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Define all 9 agents with their metadata
  const allAgents = [
    {
      id: 'code_generator',
      name: 'Enhanced Code Generator',
      description: 'Advanced AI-powered code generation with multiple language support and intelligent suggestions',
      icon: Code,
      category: 'development',
      status: 'active',
      completedTasks: 142,
      successRate: 98.7,
      avgResponseTime: '8.2s',
      color: 'blue',
      features: ['Multi-language support', 'Code optimization', 'Best practices', 'Real-time suggestions'],
      lastUsed: new Date().toISOString(),
      hasImplementation: true
    },
    {
      id: 'debug_agent',
      name: 'Debug Detective',
      description: 'Intelligent debugging assistant that identifies and resolves complex code issues automatically',
      icon: Bug,
      category: 'development',
      status: 'active',
      completedTasks: 89,
      successRate: 94.3,
      avgResponseTime: '12.1s',
      color: 'red',
      features: ['Error detection', 'Stack trace analysis', 'Fix suggestions', 'Performance insights'],
      lastUsed: new Date(Date.now() - 30000).toISOString(),
      hasImplementation: true
    },
    {
      id: 'testing_agent',
      name: 'Testing Specialist',
      description: 'Comprehensive testing suite generator with unit, integration, and e2e test creation',
      icon: TestTube,
      category: 'quality',
      status: 'active',
      completedTasks: 67,
      successRate: 96.8,
      avgResponseTime: '15.3s',
      color: 'green',
      features: ['Unit tests', 'Integration tests', 'Test coverage', 'Automated validation'],
      lastUsed: new Date(Date.now() - 120000).toISOString(),
      hasImplementation: true
    },
    {
      id: 'deploy_agent',
      name: 'Deployment Manager',
      description: 'Automated deployment and infrastructure management with CI/CD pipeline integration',
      icon: Rocket,
      category: 'operations',
      status: 'idle',
      completedTasks: 34,
      successRate: 99.1,
      avgResponseTime: '25.7s',
      color: 'purple',
      features: ['CI/CD automation', 'Infrastructure as code', 'Rollback capabilities', 'Multi-cloud support'],
      lastUsed: new Date(Date.now() - 3600000).toISOString(),
      hasImplementation: true
    },
    {
      id: 'browser_agent',
      name: 'Web Browser Assistant',
      description: 'Intelligent web automation and browser interaction for testing and data extraction',
      icon: Globe,
      category: 'automation',
      status: 'idle',
      completedTasks: 23,
      successRate: 91.4,
      avgResponseTime: '18.9s',
      color: 'cyan',
      features: ['Web scraping', 'Automated testing', 'Form filling', 'Screenshot capture'],
      lastUsed: new Date(Date.now() - 7200000).toISOString(),
      hasImplementation: true
    },
    {
      id: 'security_agent',
      name: 'Security Guardian',
      description: 'Advanced security scanning and vulnerability assessment with compliance checking',
      icon: Shield,
      category: 'security',
      status: 'active',
      completedTasks: 56,
      successRate: 99.8,
      avgResponseTime: '22.4s',
      color: 'orange',
      features: ['Vulnerability scanning', 'Code security analysis', 'Compliance checks', 'Threat detection'],
      lastUsed: new Date(Date.now() - 600000).toISOString(),
      hasImplementation: false // Missing frontend
    },
    {
      id: 'documentation_agent',
      name: 'Documentation Master',
      description: 'Automatic documentation generation with API docs, README files, and code commenting',
      icon: FileText,
      category: 'development',
      status: 'idle',
      completedTasks: 41,
      successRate: 97.2,
      avgResponseTime: '11.8s',
      color: 'indigo',
      features: ['API documentation', 'README generation', 'Code comments', 'User guides'],
      lastUsed: new Date(Date.now() - 1800000).toISOString(),
      hasImplementation: false // Missing frontend
    },
    {
      id: 'performance_optimizer',
      name: 'Performance Optimizer',
      description: 'Intelligent performance analysis and optimization suggestions for maximum efficiency',
      icon: Zap,
      category: 'optimization',
      status: 'idle',
      completedTasks: 28,
      successRate: 95.6,
      avgResponseTime: '19.7s',
      color: 'yellow',
      features: ['Performance profiling', 'Bottleneck detection', 'Optimization suggestions', 'Resource monitoring'],
      lastUsed: new Date(Date.now() - 5400000).toISOString(),
      hasImplementation: false // Missing frontend
    },
    {
      id: 'architecture_advisor',
      name: 'Architecture Advisor',
      description: 'Strategic architecture guidance and system design recommendations for scalable solutions',
      icon: Brain,
      category: 'strategy',
      status: 'idle',
      completedTasks: 19,
      successRate: 98.9,
      avgResponseTime: '31.2s',
      color: 'pink',
      features: ['Architecture patterns', 'Design principles', 'Scalability analysis', 'Best practices'],
      lastUsed: new Date(Date.now() - 9000000).toISOString(),
      hasImplementation: false // Missing frontend
    }
  ];

  const categories = [
    { id: 'all', name: 'All Agents', count: allAgents.length },
    { id: 'development', name: 'Development', count: allAgents.filter(a => a.category === 'development').length },
    { id: 'security', name: 'Security', count: allAgents.filter(a => a.category === 'security').length },
    { id: 'quality', name: 'Quality', count: allAgents.filter(a => a.category === 'quality').length },
    { id: 'operations', name: 'Operations', count: allAgents.filter(a => a.category === 'operations').length },
    { id: 'automation', name: 'Automation', count: allAgents.filter(a => a.category === 'automation').length },
    { id: 'optimization', name: 'Optimization', count: allAgents.filter(a => a.category === 'optimization').length },
    { id: 'strategy', name: 'Strategy', count: allAgents.filter(a => a.category === 'strategy').length }
  ];

  const filteredAgents = allAgents.filter(agent => {
    const matchesCategory = selectedCategory === 'all' || agent.category === selectedCategory;
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || 
                         (filter === 'active' && agent.status === 'active') ||
                         (filter === 'complete' && agent.hasImplementation) ||
                         (filter === 'incomplete' && !agent.hasImplementation);
    
    return matchesCategory && matchesSearch && matchesFilter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-400';
      case 'idle': return 'bg-yellow-400';
      case 'error': return 'bg-red-400';
      default: return 'bg-gray-400';
    }
  };

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: 'from-blue-400 to-blue-600',
      red: 'from-red-400 to-red-600',
      green: 'from-green-400 to-green-600',
      purple: 'from-purple-400 to-purple-600',
      cyan: 'from-cyan-400 to-cyan-600',
      orange: 'from-orange-400 to-orange-600',
      indigo: 'from-indigo-400 to-indigo-600',
      yellow: 'from-yellow-400 to-yellow-600',
      pink: 'from-pink-400 to-pink-600'
    };
    return colorMap[color as keyof typeof colorMap] || 'from-gray-400 to-gray-600';
  };

  const AgentCard = ({ agent }: { agent: any }) => (
    <div 
      className={`glass-card p-6 relative group cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl ${
        !agent.hasImplementation ? 'ring-2 ring-orange-400/50' : ''
      }`}
      onClick={() => onAgentSelect(agent.id)}
    >
      {/* Status indicator */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)} ${agent.status === 'active' ? 'animate-pulse' : ''}`} />
        {!agent.hasImplementation && (
          <div className="px-2 py-1 bg-orange-400/20 text-orange-300 text-xs rounded-full font-medium">
            Frontend Missing
          </div>
        )}
      </div>

      {/* Agent icon and header */}
      <div className="flex items-center gap-4 mb-4">
        <div className={`p-4 rounded-xl bg-gradient-to-br ${getColorClasses(agent.color)} shadow-lg`}>
          <agent.icon className="w-8 h-8 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white mb-1">{agent.name}</h3>
          <p className="text-white/70 text-sm">{agent.description}</p>
        </div>
      </div>

      {/* Agent statistics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-white">{agent.completedTasks}</div>
          <div className="text-white/60 text-xs">Tasks</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-green-400">{agent.successRate}%</div>
          <div className="text-white/60 text-xs">Success</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-blue-400">{agent.avgResponseTime}</div>
          <div className="text-white/60 text-xs">Avg Time</div>
        </div>
      </div>

      {/* Features */}
      <div className="mb-4">
        <div className="text-white/80 text-sm font-medium mb-2">Key Features:</div>
        <div className="flex flex-wrap gap-1">
          {agent.features.slice(0, 3).map((feature: string, index: number) => (
            <span key={index} className="px-2 py-1 bg-white/10 text-white/70 text-xs rounded-md">
              {feature}
            </span>
          ))}
          {agent.features.length > 3 && (
            <span className="px-2 py-1 bg-white/10 text-white/70 text-xs rounded-md">
              +{agent.features.length - 3} more
            </span>
          )}
        </div>
      </div>

      {/* Last used */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-white/60">
          <Clock className="w-4 h-4" />
          <span>Last used: {new Date(agent.lastUsed).toLocaleTimeString()}</span>
        </div>
        <div className="flex items-center gap-2">
          <button 
            className="p-2 glass-subtle rounded-lg hover:bg-white/20 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              // Handle settings
            }}
          >
            <Settings className="w-4 h-4 text-white/70" />
          </button>
          <button 
            className={`p-2 glass-subtle rounded-lg hover:bg-white/20 transition-colors ${
              agent.status === 'active' ? 'text-green-400' : 'text-gray-400'
            }`}
            onClick={(e) => {
              e.stopPropagation();
              // Handle start/stop
            }}
          >
            {agent.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Hover effect overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out pointer-events-none" />
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-200 to-purple-200 bg-clip-text text-transparent">
            AI Agent Arsenal
          </h1>
          <p className="text-white/70 text-lg">
            🤖 Complete suite of 9 intelligent agents • {filteredAgents.filter(a => a.hasImplementation).length}/9 fully implemented
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Implementation status */}
          <div className="glass-card px-4 py-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              <span className="text-white font-medium">
                {filteredAgents.filter(a => a.hasImplementation).length} Complete • {filteredAgents.filter(a => !a.hasImplementation).length} In Progress
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search agents..."
              className="glass-input w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          {/* Filter */}
          <select 
            className="glass-input"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Agents</option>
            <option value="active">Active Only</option>
            <option value="complete">Complete Implementation</option>
            <option value="incomplete">Missing Frontend</option>
          </select>
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-2 mt-4">
          {categories.map((category) => (
            <button
              key={category.id}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                selectedCategory === category.id
                  ? 'bg-blue-400/30 text-blue-300 ring-2 ring-blue-400/50'
                  : 'glass-subtle text-white/70 hover:bg-white/10'
              }`}
              onClick={() => setSelectedCategory(category.id)}
            >
              {category.name} ({category.count})
            </button>
          ))}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-card p-6 text-center">
          <div className="flex items-center justify-center mb-3">
            <Users className="w-8 h-8 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mb-1">9</div>
          <div className="text-white/70">Total Agents</div>
        </div>
        
        <div className="glass-card p-6 text-center">
          <div className="flex items-center justify-center mb-3">
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-green-400 mb-1">
            {allAgents.filter(a => a.hasImplementation).length}
          </div>
          <div className="text-white/70">Fully Implemented</div>
        </div>
        
        <div className="glass-card p-6 text-center">
          <div className="flex items-center justify-center mb-3">
            <Activity className="w-8 h-8 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-yellow-400 mb-1">
            {allAgents.filter(a => a.status === 'active').length}
          </div>
          <div className="text-white/70">Currently Active</div>
        </div>
        
        <div className="glass-card p-6 text-center">
          <div className="flex items-center justify-center mb-3">
            <TrendingUp className="w-8 h-8 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400 mb-1">96.8%</div>
          <div className="text-white/70">Avg Success Rate</div>
        </div>
      </div>

      {/* Implementation Progress */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="w-6 h-6 text-yellow-400" />
          <h2 className="text-xl font-bold text-white">Implementation Progress</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-white/70">Frontend Implementation</span>
            <span className="text-white font-medium">
              {allAgents.filter(a => a.hasImplementation).length}/9 ({Math.round((allAgents.filter(a => a.hasImplementation).length / 9) * 100)}%)
            </span>
          </div>
          
          <div className="relative h-3 bg-white/10 rounded-full overflow-hidden">
            <div 
              className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-blue-400 to-purple-500 transition-all duration-1000 ease-out"
              style={{ width: `${(allAgents.filter(a => a.hasImplementation).length / 9) * 100}%` }}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-green-400">✅ Complete: {allAgents.filter(a => a.hasImplementation).length} agents</span>
            <span className="text-orange-400">🚧 In Progress: {allAgents.filter(a => !a.hasImplementation).length} agents</span>
          </div>
        </div>
      </div>

      {filteredAgents.length === 0 && (
        <div className="glass-card p-12 text-center">
          <Users className="w-16 h-16 text-white/30 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No agents found</h3>
          <p className="text-white/60">Try adjusting your search or filter criteria</p>
        </div>
      )}
    </div>
  );
};

export default AllAgentsInterface;