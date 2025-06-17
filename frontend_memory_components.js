// /src/components/memory/MemoryEnabledChat.jsx
/**
 * Enhanced chat component with memory capabilities
 * Extends existing chat interface with memory context and visualization
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageCircle, 
  Brain, 
  History, 
  Lightbulb, 
  TrendingUp,
  Database,
  Zap,
  User,
  Bot
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Import existing components
import { GlassmorphismCard } from '../ui/GlassmorphismCard';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useMemoryAPI } from '../../hooks/useMemoryAPI';

const MemoryEnabledChat = ({ 
  sessionId, 
  agents = ['general'], 
  enableMemory = true,
  showMemoryContext = true 
}) => {
  // State management
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [memoryContext, setMemoryContext] = useState(null);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const [memoryStats, setMemoryStats] = useState(null);
  
  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Hooks
  const { sendMessage, isConnected } = useWebSocket('/api/memory/ws/' + sessionId);
  const { 
    queryKnowledge, 
    getMemoryStats, 
    memoryChatRequest 
  } = useMemoryAPI();

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Load memory stats on mount
  useEffect(() => {
    if (enableMemory) {
      loadMemoryStats();
    }
  }, [enableMemory]);

  const loadMemoryStats = async () => {
    try {
      const stats = await getMemoryStats();
      setMemoryStats(stats);
    } catch (error) {
      console.error('Failed to load memory stats:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
      agents: agents
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Send memory-enabled chat request
      const response = await memoryChatRequest({
        content: inputMessage,
        agents: agents,
        session_id: sessionId,
        include_memory_context: enableMemory,
        memory_tags: ['chat', 'user_interaction'],
        persist_response: true
      });

      // Add agent responses
      const agentMessages = response.responses.map((agentResponse, index) => ({
        id: Date.now() + index + 1,
        type: 'agent',
        agent_id: agentResponse.agent_id,
        content: agentResponse.content,
        timestamp: new Date().toISOString(),
        cost: agentResponse.cost,
        tokens_used: agentResponse.tokens_used,
        generation_time: agentResponse.generation_time,
        memory_updated: agentResponse.memory_updated,
        provider: agentResponse.provider
      }));

      setMessages(prev => [...prev, ...agentMessages]);
      
      // Update memory context if available
      if (response.memory_context) {
        setMemoryContext(response.memory_context);
      }

      // Update memory stats
      loadMemoryStats();

    } catch (error) {
      console.error('Chat request failed:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getAgentColor = (agentId) => {
    const colors = {
      'code_analyst': 'from-blue-500 to-cyan-500',
      'debug_detective': 'from-red-500 to-pink-500',
      'workflow_manager': 'from-green-500 to-emerald-500',
      'general': 'from-purple-500 to-indigo-500'
    };
    return colors[agentId] || colors.general;
  };

  const getAgentIcon = (agentId) => {
    const icons = {
      'code_analyst': '💻',
      'debug_detective': '🔍',
      'workflow_manager': '⚡',
      'general': '🤖'
    };
    return icons[agentId] || icons.general;
  };

  return (
    <div className="flex h-full bg-transparent">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <GlassmorphismCard className="mb-4 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Memory-Enhanced Chat
                </h2>
                <p className="text-sm text-gray-300">
                  {agents.length} agent{agents.length > 1 ? 's' : ''} • 
                  {enableMemory ? ' Memory Enabled' : ' Memory Disabled'} • 
                  {isConnected ? ' Connected' : ' Disconnected'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Memory Stats Badge */}
              {memoryStats && (
                <div className="px-3 py-1 rounded-full bg-black/20 text-sm text-white">
                  💾 {memoryStats.statistics.total_queries} queries
                </div>
              )}
              
              {/* Memory Panel Toggle */}
              {enableMemory && (
                <button
                  onClick={() => setShowMemoryPanel(!showMemoryPanel)}
                  className={`p-2 rounded-lg transition-all duration-200 ${
                    showMemoryPanel 
                      ? 'bg-blue-500/20 text-blue-400' 
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  <Brain className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </GlassmorphismCard>

        {/* Messages Area */}
        <GlassmorphismCard className="flex-1 p-4 mb-4 overflow-hidden">
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-white/20">
              <AnimatePresence>
                {messages.map((message) => (
                  <MessageBubble 
                    key={message.id} 
                    message={message} 
                    getAgentColor={getAgentColor}
                    getAgentIcon={getAgentIcon}
                  />
                ))}
              </AnimatePresence>
              
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center space-x-2 text-gray-300"
                >
                  <LoadingSpinner size="sm" />
                  <span>Agents are thinking...</span>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>
        </GlassmorphismCard>

        {/* Input Area */}
        <GlassmorphismCard className="p-4">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message... (Shift+Enter for new line)"
                className="w-full bg-white/10 text-white placeholder-gray-400 border border-white/20 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none min-h-[44px] max-h-32"
                rows={1}
                disabled={isLoading}
              />
            </div>
            
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:from-blue-600 hover:to-purple-700 transition-all duration-200 flex items-center space-x-2"
            >
              <span>Send</span>
              <Zap className="w-4 h-4" />
            </button>
          </div>
          
          {/* Agent Pills */}
          <div className="flex items-center space-x-2 mt-3">
            <span className="text-sm text-gray-400">Active agents:</span>
            {agents.map((agent) => (
              <div
                key={agent}
                className={`px-2 py-1 rounded-full text-xs bg-gradient-to-r ${getAgentColor(agent)} text-white`}
              >
                {getAgentIcon(agent)} {agent.replace('_', ' ')}
              </div>
            ))}
          </div>
        </GlassmorphismCard>
      </div>

      {/* Memory Context Panel */}
      <AnimatePresence>
        {showMemoryPanel && enableMemory && (
          <MemoryContextPanel 
            memoryContext={memoryContext}
            memoryStats={memoryStats}
            sessionId={sessionId}
            onClose={() => setShowMemoryPanel(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message, getAgentColor, getAgentIcon }) => {
  const isUser = message.type === 'user';
  const isError = message.type === 'error';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Message Header */}
        {!isUser && (
          <div className="flex items-center space-x-2 mb-1">
            <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${getAgentColor(message.agent_id)} flex items-center justify-center text-xs`}>
              {getAgentIcon(message.agent_id)}
            </div>
            <span className="text-xs text-gray-400">
              {message.agent_id?.replace('_', ' ') || 'Agent'}
            </span>
            {message.memory_updated && (
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" title="Memory Updated" />
            )}
          </div>
        )}

        {/* Message Content */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
              : isError
              ? 'bg-red-500/20 text-red-300 border border-red-500/30'
              : 'bg-white/10 text-white border border-white/20'
          }`}
        >
          <div className="prose prose-invert max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
              {message.content}
            </pre>
          </div>
        </div>

        {/* Message Footer */}
        {!isUser && !isError && (
          <div className="flex items-center justify-between mt-1 text-xs text-gray-400">
            <div className="flex items-center space-x-3">
              <span>{message.provider}</span>
              <span>💰 ${message.cost?.toFixed(4) || '0.0000'}</span>
              <span>⚡ {message.generation_time?.toFixed(2)}s</span>
              <span>📊 {message.tokens_used} tokens</span>
            </div>
            <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          </div>
        )}
      </div>

      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex-shrink-0 ${isUser ? 'order-1 ml-3' : 'order-2 mr-3'} mt-auto mb-2`}>
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-400 to-blue-500 flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
        ) : (
          <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${getAgentColor(message.agent_id)} flex items-center justify-center`}>
            <Bot className="w-4 h-4 text-white" />
          </div>
        )}
      </div>
    </motion.div>
  );
};

// Memory Context Panel Component
const MemoryContextPanel = ({ memoryContext, memoryStats, sessionId, onClose }) => {
  const [activeTab, setActiveTab] = useState('context');
  const [knowledgeQuery, setKnowledgeQuery] = useState('');
  const [queryResults, setQueryResults] = useState([]);
  const [isQuerying, setIsQuerying] = useState(false);
  
  const { queryKnowledge } = useMemoryAPI();

  const handleKnowledgeQuery = async () => {
    if (!knowledgeQuery.trim() || isQuerying) return;

    setIsQuerying(true);
    try {
      const results = await queryKnowledge({
        query: knowledgeQuery,
        query_type: 'insights',
        limit: 10
      });
      setQueryResults(results.results);
    } catch (error) {
      console.error('Knowledge query failed:', error);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <motion.div
      initial={{ x: 300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 300, opacity: 0 }}
      className="w-96 ml-4"
    >
      <GlassmorphismCard className="h-full p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
            <Brain className="w-5 h-5" />
            <span>Memory Context</span>
          </h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-white/10 text-gray-300 hover:bg-white/20 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-4 bg-white/10 rounded-lg p-1">
          {[
            { id: 'context', label: 'Context', icon: History },
            { id: 'stats', label: 'Stats', icon: TrendingUp },
            { id: 'query', label: 'Query', icon: Database }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-1 py-2 px-3 rounded-md text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'context' && (
            <MemoryContextTab memoryContext={memoryContext} />
          )}
          
          {activeTab === 'stats' && (
            <MemoryStatsTab memoryStats={memoryStats} />
          )}
          
          {activeTab === 'query' && (
            <KnowledgeQueryTab
              query={knowledgeQuery}
              setQuery={setKnowledgeQuery}
              results={queryResults}
              isQuerying={isQuerying}
              onQuery={handleKnowledgeQuery}
            />
          )}
        </div>
      </GlassmorphismCard>
    </motion.div>
  );
};

// Memory Context Tab
const MemoryContextTab = ({ memoryContext }) => {
  if (!memoryContext) {
    return (
      <div className="text-center text-gray-400 py-8">
        <Brain className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No memory context available</p>
        <p className="text-sm">Start a conversation to build context</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-full overflow-y-auto scrollbar-thin scrollbar-thumb-white/20">
      {/* Context Summary */}
      {memoryContext.context_summary && (
        <div className="bg-white/10 rounded-lg p-3">
          <h4 className="text-sm font-medium text-blue-400 mb-2">Summary</h4>
          <p className="text-sm text-gray-300">{memoryContext.context_summary}</p>
        </div>
      )}

      {/* Relevant Knowledge */}
      {memoryContext.relevant_knowledge?.length > 0 && (
        <div className="bg-white/10 rounded-lg p-3">
          <h4 className="text-sm font-medium text-green-400 mb-2">
            Relevant Knowledge ({memoryContext.relevant_knowledge.length})
          </h4>
          <div className="space-y-2">
            {memoryContext.relevant_knowledge.map((item, index) => (
              <div key={index} className="bg-white/5 rounded p-2">
                <p className="text-xs text-gray-300">
                  {typeof item === 'object' ? JSON.stringify(item, null, 2) : item}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detected Patterns */}
      {memoryContext.patterns_detected?.length > 0 && (
        <div className="bg-white/10 rounded-lg p-3">
          <h4 className="text-sm font-medium text-purple-400 mb-2">
            Patterns ({memoryContext.patterns_detected.length})
          </h4>
          <div className="space-y-1">
            {memoryContext.patterns_detected.map((pattern, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Lightbulb className="w-3 h-3 text-yellow-400" />
                <span className="text-xs text-gray-300">{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Memory Stats Tab
const MemoryStatsTab = ({ memoryStats }) => {
  if (!memoryStats) {
    return (
      <div className="text-center text-gray-400 py-8">
        <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>Memory stats unavailable</p>
      </div>
    );
  }

  const stats = memoryStats.statistics;
  const performance = memoryStats.performance;

  return (
    <div className="space-y-4 max-h-full overflow-y-auto scrollbar-thin scrollbar-thumb-white/20">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-blue-500/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{stats.total_queries}</div>
          <div className="text-xs text-gray-300">Total Queries</div>
        </div>
        <div className="bg-green-500/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-green-400">{stats.cache_hits}</div>
          <div className="text-xs text-gray-300">Cache Hits</div>
        </div>
        <div className="bg-purple-500/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-purple-400">{stats.memory_updates}</div>
          <div className="text-xs text-gray-300">Updates</div>
        </div>
        <div className="bg-yellow-500/20 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {performance.cache_hit_rate?.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-300">Hit Rate</div>
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white/10 rounded-lg p-3">
        <h4 className="text-sm font-medium text-white mb-2">Configuration</h4>
        <div className="space-y-1 text-xs text-gray-300">
          <div>Vector DB: {memoryStats.configuration.vector_db}</div>
          <div>Graph DB: {memoryStats.configuration.graph_db}</div>
          <div>Cache Size: {memoryStats.configuration.cache_size}</div>
          <div>Auto Persist: {memoryStats.configuration.auto_persist ? 'Yes' : 'No'}</div>
        </div>
      </div>

      {/* Status */}
      <div className="bg-white/10 rounded-lg p-3">
        <h4 className="text-sm font-medium text-white mb-2">Status</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Memory Enabled</span>
            <div className={`w-2 h-2 rounded-full ${memoryStats.memory_enabled ? 'bg-green-400' : 'bg-red-400'}`} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Cognee Initialized</span>
            <div className={`w-2 h-2 rounded-full ${memoryStats.cognee_initialized ? 'bg-green-400' : 'bg-red-400'}`} />
          </div>
        </div>
      </div>
    </div>
  );
};

// Knowledge Query Tab
const KnowledgeQueryTab = ({ query, setQuery, results, isQuerying, onQuery }) => {
  return (
    <div className="space-y-4 max-h-full flex flex-col">
      {/* Query Input */}
      <div className="space-y-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search knowledge graph..."
          className="w-full bg-white/10 text-white placeholder-gray-400 border border-white/20 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          onKeyPress={(e) => e.key === 'Enter' && onQuery()}
          disabled={isQuerying}
        />
        <button
          onClick={onQuery}
          disabled={!query.trim() || isQuerying}
          className="w-full px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg text-sm hover:bg-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isQuerying ? 'Searching...' : 'Search Knowledge'}
        </button>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/20">
        {isQuerying ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="sm" />
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-2">
            {results.map((result, index) => (
              <div key={index} className="bg-white/5 rounded-lg p-3">
                <div className="text-xs text-gray-300">
                  {typeof result === 'object' ? (
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  ) : (
                    result
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : query && !isQuerying ? (
          <div className="text-center text-gray-400 py-8">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No results found</p>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-8">
            <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Enter a query to search</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryEnabledChat;