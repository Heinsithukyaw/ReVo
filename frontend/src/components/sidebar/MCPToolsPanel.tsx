import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Search, Star, Download, ExternalLink, Play, Pause, RefreshCw } from 'lucide-react';

interface MCPTool {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  status: 'active' | 'inactive' | 'installing' | 'error';
  rating: number;
  downloads: number;
  icon: string;
  capabilities: string[];
  author: string;
  lastUpdated: Date;
}

interface MCPToolsPanelProps {
  selectedAgents: string[];
}

const MCPToolsPanel: React.FC<MCPToolsPanelProps> = ({ selectedAgents }) => {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [toolStats, setToolStats] = useState({
    totalTools: 247,
    activeTools: 23,
    categories: 12,
    lastSync: new Date()
  });

  // Load MCP tools from backend
  const loadMCPTools = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/mcp/tools');
      if (response.ok) {
        const data = await response.json();
        setTools(data.tools || []);
        setToolStats(prev => ({ ...prev, ...data.stats }));
      }
    } catch (error) {
      console.error('Failed to load MCP tools:', error);
      // Generate mock data for demo
      generateMockTools();
    } finally {
      setIsLoading(false);
    }
  };

  // Generate mock MCP tools for demo
  const generateMockTools = () => {
    const mockTools: MCPTool[] = [
      {
        id: 'web-scraper',
        name: 'Web Scraper Pro',
        description: 'Advanced web scraping with AI-powered content extraction',
        category: 'data',
        version: '2.1.0',
        status: 'active',
        rating: 4.8,
        downloads: 15420,
        icon: '🕷️',
        capabilities: ['HTML parsing', 'Dynamic content', 'Rate limiting', 'Proxy support'],
        author: 'DataTools Inc',
        lastUpdated: new Date(Date.now() - 86400000)
      },
      {
        id: 'code-analyzer',
        name: 'Code Quality Analyzer',
        description: 'Static code analysis with security vulnerability detection',
        category: 'development',
        version: '1.5.2',
        status: 'active',
        rating: 4.6,
        downloads: 8930,
        icon: '🔍',
        capabilities: ['Security scanning', 'Code metrics', 'Best practices', 'Multi-language'],
        author: 'SecureCode Labs',
        lastUpdated: new Date(Date.now() - 172800000)
      },
      {
        id: 'api-tester',
        name: 'API Testing Suite',
        description: 'Comprehensive API testing and documentation generator',
        category: 'testing',
        version: '3.0.1',
        status: 'active',
        rating: 4.9,
        downloads: 12750,
        icon: '🧪',
        capabilities: ['REST/GraphQL', 'Load testing', 'Auto docs', 'Mock servers'],
        author: 'TestMaster Pro',
        lastUpdated: new Date(Date.now() - 259200000)
      },
      {
        id: 'image-processor',
        name: 'AI Image Processor',
        description: 'Advanced image processing with machine learning',
        category: 'ai',
        version: '2.3.0',
        status: 'inactive',
        rating: 4.7,
        downloads: 6840,
        icon: '🖼️',
        capabilities: ['Object detection', 'Style transfer', 'Enhancement', 'Format conversion'],
        author: 'VisionAI Corp',
        lastUpdated: new Date(Date.now() - 345600000)
      },
      {
        id: 'database-optimizer',
        name: 'Database Optimizer',
        description: 'Intelligent database performance optimization',
        category: 'database',
        version: '1.8.3',
        status: 'active',
        rating: 4.5,
        downloads: 4320,
        icon: '🗄️',
        capabilities: ['Query optimization', 'Index analysis', 'Performance monitoring', 'Schema design'],
        author: 'DBTech Solutions',
        lastUpdated: new Date(Date.now() - 432000000)
      }
    ];
    setTools(mockTools);
  };

  useEffect(() => {
    loadMCPTools();
  }, []);

  // Filter tools based on search and category
  const filteredTools = tools.filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tool.capabilities.some(cap => cap.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['all', ...Array.from(new Set(tools.map(tool => tool.category)))];

  const toggleTool = async (toolId: string) => {
    const tool = tools.find(t => t.id === toolId);
    if (!tool) return;

    const newStatus = tool.status === 'active' ? 'inactive' : 'active';
    
    try {
      const response = await fetch(`http://localhost:8000/api/mcp/tools/${toolId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        setTools(prev => prev.map(t => 
          t.id === toolId ? { ...t, status: newStatus } : t
        ));
      }
    } catch (error) {
      console.error('Failed to toggle tool:', error);
      // Update locally for demo
      setTools(prev => prev.map(t => 
        t.id === toolId ? { ...t, status: newStatus } : t
      ));
    }
  };

  const installTool = async (toolId: string) => {
    try {
      setTools(prev => prev.map(t => 
        t.id === toolId ? { ...t, status: 'installing' } : t
      ));

      const response = await fetch(`http://localhost:8000/api/mcp/tools/${toolId}/install`, {
        method: 'POST'
      });

      if (response.ok) {
        setTimeout(() => {
          setTools(prev => prev.map(t => 
            t.id === toolId ? { ...t, status: 'active' } : t
          ));
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to install tool:', error);
      setTools(prev => prev.map(t => 
        t.id === toolId ? { ...t, status: 'error' } : t
      ));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'inactive': return 'text-gray-400';
      case 'installing': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Play className="w-3 h-3" />;
      case 'inactive': return <Pause className="w-3 h-3" />;
      case 'installing': return <RefreshCw className="w-3 h-3 animate-spin" />;
      case 'error': return <ExternalLink className="w-3 h-3" />;
      default: return <Pause className="w-3 h-3" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* MCP Tools Statistics */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Settings className="w-4 h-4" />
          <span>MCP Tools Marketplace</span>
        </h3>
        
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="text-center">
            <div className="text-green-400 font-bold">{toolStats.totalTools}</div>
            <div className="text-gray-400 text-xs">Available Tools</div>
          </div>
          <div className="text-center">
            <div className="text-blue-400 font-bold">{toolStats.activeTools}</div>
            <div className="text-gray-400 text-xs">Active Tools</div>
          </div>
          <div className="text-center">
            <div className="text-purple-400 font-bold">{toolStats.categories}</div>
            <div className="text-gray-400 text-xs">Categories</div>
          </div>
          <div className="text-center">
            <div className="text-yellow-400 font-bold">$0.00</div>
            <div className="text-gray-400 text-xs">Cost Savings</div>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-600/50 border border-gray-500/50 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>

        <div className="flex flex-wrap gap-1">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-600/50 text-gray-300 hover:bg-gray-500/50'
              }`}
            >
              {category === 'all' ? 'All' : category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tools List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-white font-medium text-sm">Available Tools</h4>
          <button
            onClick={loadMCPTools}
            disabled={isLoading}
            className="p-1 hover:bg-gray-600/50 rounded transition-colors"
            title="Refresh tools"
          >
            <RefreshCw className={`w-4 h-4 text-gray-400 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        
        {isLoading ? (
          <div className="text-center py-4">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mx-auto mb-2" />
            <div className="text-gray-400 text-sm">Loading tools...</div>
          </div>
        ) : filteredTools.length === 0 ? (
          <div className="text-center py-4">
            <Settings className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <div className="text-gray-400 text-sm">No tools found</div>
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {filteredTools.map(tool => (
              <motion.div
                key={tool.id}
                className="bg-gray-700/30 rounded-lg p-3 border border-gray-600/30"
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{tool.icon}</span>
                    <div>
                      <div className="text-white font-medium text-sm">{tool.name}</div>
                      <div className="text-gray-400 text-xs">v{tool.version} by {tool.author}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className={`flex items-center space-x-1 text-xs ${getStatusColor(tool.status)}`}>
                      {getStatusIcon(tool.status)}
                      <span className="capitalize">{tool.status}</span>
                    </div>
                    
                    <button
                      onClick={() => toggleTool(tool.id)}
                      disabled={tool.status === 'installing'}
                      className={`p-1 rounded transition-colors ${
                        tool.status === 'active'
                          ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400'
                          : 'bg-green-600/20 hover:bg-green-600/30 text-green-400'
                      }`}
                      title={tool.status === 'active' ? 'Deactivate' : 'Activate'}
                    >
                      {tool.status === 'active' ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
                
                <div className="text-gray-300 text-sm mb-2 line-clamp-2">
                  {tool.description}
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center space-x-1">
                      <Star className="w-3 h-3 text-yellow-400" />
                      <span className="text-gray-300">{tool.rating}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Download className="w-3 h-3 text-gray-400" />
                      <span className="text-gray-300">{tool.downloads.toLocaleString()}</span>
                    </div>
                  </div>
                  
                  <div className="text-gray-400">
                    {tool.category}
                  </div>
                </div>
                
                {/* Capabilities */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {tool.capabilities.slice(0, 3).map(capability => (
                    <span
                      key={capability}
                      className="px-1 py-0.5 bg-gray-600/50 rounded text-gray-300 text-xs"
                    >
                      {capability}
                    </span>
                  ))}
                  {tool.capabilities.length > 3 && (
                    <span className="text-gray-400 text-xs">+{tool.capabilities.length - 3}</span>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-lg p-4 border border-green-500/20">
        <h4 className="text-white font-medium mb-2">Quick Actions</h4>
        
        <div className="space-y-2">
          <button className="w-full text-left p-2 bg-gray-700/30 hover:bg-gray-600/30 rounded-lg transition-colors text-sm">
            <div className="text-white">🔄 Sync with MCP Registry</div>
            <div className="text-gray-400 text-xs">Update available tools</div>
          </button>
          
          <button className="w-full text-left p-2 bg-gray-700/30 hover:bg-gray-600/30 rounded-lg transition-colors text-sm">
            <div className="text-white">📦 Install Recommended</div>
            <div className="text-gray-400 text-xs">Based on selected agents</div>
          </button>
          
          <button className="w-full text-left p-2 bg-gray-700/30 hover:bg-gray-600/30 rounded-lg transition-colors text-sm">
            <div className="text-white">⚙️ Configure Auto-Install</div>
            <div className="text-gray-400 text-xs">Smart tool management</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MCPToolsPanel;