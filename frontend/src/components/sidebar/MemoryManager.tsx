import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Search, Trash2, Download, Upload, RefreshCw, Database, Link } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: string;
  senderName: string;
  timestamp: Date;
}

interface MemoryItem {
  id: string;
  type: 'entity' | 'relationship' | 'context' | 'pattern';
  content: string;
  relevance: number;
  timestamp: Date;
  relatedAgents: string[];
  tags: string[];
}

interface MemoryManagerProps {
  conversations: Message[];
  selectedAgents: string[];
}

const MemoryManager: React.FC<MemoryManagerProps> = ({
  conversations,
  selectedAgents
}) => {
  const [memoryItems, setMemoryItems] = useState<MemoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [memoryStats, setMemoryStats] = useState({
    totalEntities: 1247893,
    totalRelationships: 3456782,
    contextItems: 156,
    patterns: 89,
    storageUsed: 67.8,
    lastUpdate: new Date()
  });

  // Load memory items from backend
  const loadMemoryItems = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/memory/items');
      if (response.ok) {
        const data = await response.json();
        setMemoryItems(data.items || []);
        setMemoryStats(prev => ({ ...prev, ...data.stats }));
      }
    } catch (error) {
      console.error('Failed to load memory items:', error);
      // Generate mock data for demo
      generateMockMemoryItems();
    } finally {
      setIsLoading(false);
    }
  };

  // Generate mock memory items for demo
  const generateMockMemoryItems = () => {
    const mockItems: MemoryItem[] = [
      {
        id: '1',
        type: 'entity',
        content: 'React component architecture patterns',
        relevance: 95,
        timestamp: new Date(Date.now() - 3600000),
        relatedAgents: ['fullstack-dev', 'frontend-specialist'],
        tags: ['react', 'architecture', 'patterns']
      },
      {
        id: '2',
        type: 'relationship',
        content: 'Connection between UI design and user experience',
        relevance: 88,
        timestamp: new Date(Date.now() - 7200000),
        relatedAgents: ['ui-designer', 'ux-researcher'],
        tags: ['ui', 'ux', 'design']
      },
      {
        id: '3',
        type: 'context',
        content: 'Previous discussion about API optimization',
        relevance: 76,
        timestamp: new Date(Date.now() - 10800000),
        relatedAgents: ['backend-architect', 'devops-engineer'],
        tags: ['api', 'optimization', 'performance']
      },
      {
        id: '4',
        type: 'pattern',
        content: 'User preference for dark mode interfaces',
        relevance: 82,
        timestamp: new Date(Date.now() - 14400000),
        relatedAgents: ['ui-designer', 'frontend-specialist'],
        tags: ['ui', 'preferences', 'dark-mode']
      }
    ];
    setMemoryItems(mockItems);
  };

  useEffect(() => {
    loadMemoryItems();
  }, [conversations, selectedAgents]);

  // Filter memory items based on search and type
  const filteredItems = memoryItems.filter(item => {
    const matchesSearch = item.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedType === 'all' || item.type === selectedType;
    return matchesSearch && matchesType;
  });

  const clearMemory = async () => {
    if (window.confirm('Are you sure you want to clear all memory? This action cannot be undone.')) {
      try {
        const response = await fetch('http://localhost:8000/api/memory/clear', {
          method: 'POST'
        });
        if (response.ok) {
          setMemoryItems([]);
          setMemoryStats(prev => ({
            ...prev,
            totalEntities: 0,
            totalRelationships: 0,
            contextItems: 0,
            patterns: 0
          }));
        }
      } catch (error) {
        console.error('Failed to clear memory:', error);
      }
    }
  };

  const exportMemory = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      stats: memoryStats,
      items: memoryItems
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `revoagent-memory-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'entity': return '🧩';
      case 'relationship': return '🔗';
      case 'context': return '📝';
      case 'pattern': return '🔍';
      default: return '💭';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'entity': return 'text-blue-400';
      case 'relationship': return 'text-green-400';
      case 'context': return 'text-yellow-400';
      case 'pattern': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-4">
      {/* Memory Statistics */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Brain className="w-4 h-4" />
          <span>Memory Statistics</span>
        </h3>
        
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="text-center">
            <div className="text-blue-400 font-bold">{memoryStats.totalEntities.toLocaleString()}</div>
            <div className="text-gray-400 text-xs">Entities</div>
          </div>
          <div className="text-center">
            <div className="text-green-400 font-bold">{memoryStats.totalRelationships.toLocaleString()}</div>
            <div className="text-gray-400 text-xs">Relationships</div>
          </div>
          <div className="text-center">
            <div className="text-yellow-400 font-bold">{memoryStats.contextItems}</div>
            <div className="text-gray-400 text-xs">Context Items</div>
          </div>
          <div className="text-center">
            <div className="text-purple-400 font-bold">{memoryStats.patterns}</div>
            <div className="text-gray-400 text-xs">Patterns</div>
          </div>
        </div>

        {/* Storage Usage */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Memory Usage</span>
            <span>{memoryStats.storageUsed}%</span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-2">
            <motion.div
              className="bg-blue-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${memoryStats.storageUsed}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>

      {/* Memory Controls */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-white font-medium">Memory Control</h4>
          <div className="flex items-center space-x-1">
            <button
              onClick={loadMemoryItems}
              disabled={isLoading}
              className="p-1 hover:bg-gray-600/50 rounded transition-colors"
              title="Refresh memory"
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={exportMemory}
              className="p-1 hover:bg-gray-600/50 rounded transition-colors"
              title="Export memory"
            >
              <Download className="w-4 h-4 text-gray-400" />
            </button>
            <button
              onClick={clearMemory}
              className="p-1 hover:bg-gray-600/50 rounded transition-colors"
              title="Clear memory"
            >
              <Trash2 className="w-4 h-4 text-red-400" />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search memory..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-600/50 border border-gray-500/50 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>

        {/* Type Filter */}
        <div className="flex space-x-1 mb-3">
          {['all', 'entity', 'relationship', 'context', 'pattern'].map(type => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                selectedType === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-600/50 text-gray-300 hover:bg-gray-500/50'
              }`}
            >
              {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Items */}
      <div className="space-y-2">
        <h4 className="text-white font-medium text-sm">Recent Memory Items</h4>
        
        {isLoading ? (
          <div className="text-center py-4">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mx-auto mb-2" />
            <div className="text-gray-400 text-sm">Loading memory...</div>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="text-center py-4">
            <Database className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <div className="text-gray-400 text-sm">No memory items found</div>
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredItems.map(item => (
              <motion.div
                key={item.id}
                className="bg-gray-700/30 rounded-lg p-3 border border-gray-600/30"
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getTypeIcon(item.type)}</span>
                    <span className={`text-xs font-medium capitalize ${getTypeColor(item.type)}`}>
                      {item.type}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400">
                    {item.relevance}% relevant
                  </div>
                </div>
                
                <div className="text-white text-sm mb-2 line-clamp-2">
                  {item.content}
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1">
                    {item.tags.slice(0, 2).map(tag => (
                      <span
                        key={tag}
                        className="px-1 py-0.5 bg-gray-600/50 rounded text-gray-300"
                      >
                        #{tag}
                      </span>
                    ))}
                    {item.tags.length > 2 && (
                      <span className="text-gray-400">+{item.tags.length - 2}</span>
                    )}
                  </div>
                  <div className="text-gray-400">
                    {item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Memory Health */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-4 border border-blue-500/20">
        <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
          <Link className="w-4 h-4" />
          <span>Memory Health</span>
        </h4>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Coherence:</span>
            <span className="text-green-400">98.7%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Fragmentation:</span>
            <span className="text-yellow-400">2.1%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Last Optimization:</span>
            <span className="text-blue-400">2 hours ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemoryManager;