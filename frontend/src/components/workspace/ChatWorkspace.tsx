import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Zap, Palette, RefreshCw, Download, Eye } from 'lucide-react';
import MessageBubble from '../ui/MessageBubble';
import ThreeEngineOrchestration from './ThreeEngineOrchestration';

interface Message {
  id: string;
  content: string;
  sender: string;
  senderName: string;
  senderIcon: string;
  timestamp: Date;
  agentType?: string;
  reactions?: { [key: string]: number };
  engineData?: {
    memory?: any;
    parallel?: any;
    creative?: any;
  };
}

interface EngineStatus {
  memory: { active: boolean; entities?: number };
  parallel: { active: boolean; tasks?: number };
  creative: { active: boolean; ideas?: number };
}

interface ChatWorkspaceProps {
  conversations: Message[];
  isConnected: boolean;
  onReaction: (messageId: string, reaction: string) => void;
  isProcessing: boolean;
  engineStatus: EngineStatus;
}

const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  conversations,
  isConnected,
  onReaction,
  isProcessing,
  engineStatus
}) => {
  const chatRef = useRef<HTMLDivElement>(null);
  const [typingAgents, setTypingAgents] = useState<Array<{ id: string; name: string; icon: string }>>([]);
  const [orchestrationActive, setOrchestrationActive] = useState(false);
  const [contextItems, setContextItems] = useState<any[]>([]);
  const [showEngineDetails, setShowEngineDetails] = useState(false);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [conversations]);

  // Simulate typing indicators when processing
  useEffect(() => {
    if (isProcessing) {
      setTypingAgents([
        { id: 'memory', name: 'Memory Engine', icon: '🧠' },
        { id: 'parallel', name: 'Parallel Engine', icon: '⚡' },
        { id: 'creative', name: 'Creative Engine', icon: '🎨' }
      ]);
    } else {
      setTypingAgents([]);
    }
  }, [isProcessing]);

  // Load memory context (simulated)
  const loadContext = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/memory/context');
      if (response.ok) {
        const data = await response.json();
        setContextItems(data.context || []);
      }
    } catch (error) {
      console.error('Failed to load context:', error);
    }
  };

  useEffect(() => {
    loadContext();
  }, [conversations]);

  const exportConversation = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      conversations,
      engineStatus,
      contextItems
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `revoagent-conversation-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const messageVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { duration: 0.5, ease: "easeOut" }
    },
    exit: { 
      opacity: 0, 
      y: -20, 
      scale: 0.95,
      transition: { duration: 0.3 }
    }
  };

  const threeEngineMode = engineStatus.memory.active && 
                          engineStatus.parallel.active && 
                          engineStatus.creative.active;

  return (
    <div className="chat-workspace h-full flex flex-col bg-gray-800/20 backdrop-blur-sm border border-gray-700/30 rounded-lg m-4">
      {/* Chat Header */}
      <div className="chat-header p-4 border-b border-gray-700/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className="connection-status flex items-center space-x-2">
              <div className={`status-indicator w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`} />
              <span className="text-white font-medium">
                {isConnected ? 'Three-Engine Live Connection' : 'Reconnecting...'}
              </span>
            </div>

            {/* Engine Status Indicators */}
            <div className="flex items-center space-x-3">
              <motion.div
                className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                  engineStatus.memory.active 
                    ? 'bg-blue-500/20 text-blue-300' 
                    : 'bg-gray-700/50 text-gray-500'
                }`}
                whileHover={{ scale: 1.05 }}
              >
                <Brain className="w-3 h-3" />
                <span>Memory</span>
                {engineStatus.memory.active && (
                  <span className="text-blue-200">({engineStatus.memory.entities || 0})</span>
                )}
              </motion.div>

              <motion.div
                className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                  engineStatus.parallel.active 
                    ? 'bg-yellow-500/20 text-yellow-300' 
                    : 'bg-gray-700/50 text-gray-500'
                }`}
                whileHover={{ scale: 1.05 }}
              >
                <Zap className="w-3 h-3" />
                <span>Parallel</span>
                {engineStatus.parallel.active && (
                  <span className="text-yellow-200">({engineStatus.parallel.tasks || 0})</span>
                )}
              </motion.div>

              <motion.div
                className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                  engineStatus.creative.active 
                    ? 'bg-pink-500/20 text-pink-300' 
                    : 'bg-gray-700/50 text-gray-500'
                }`}
                whileHover={{ scale: 1.05 }}
              >
                <Palette className="w-3 h-3" />
                <span>Creative</span>
                {engineStatus.creative.active && (
                  <span className="text-pink-200">({engineStatus.creative.ideas || 0})</span>
                )}
              </motion.div>
            </div>
          </div>

          {/* Context and Actions */}
          <div className="flex items-center space-x-3">
            <div className="context-indicator text-sm text-gray-300">
              🧠 Memory Context: {contextItems.length} items loaded
            </div>
            
            <button
              onClick={() => setShowEngineDetails(!showEngineDetails)}
              className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
              title="Engine Details"
            >
              <Eye className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Engine Details Panel */}
        <AnimatePresence>
          {showEngineDetails && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 p-3 bg-gray-700/30 rounded-lg border border-gray-600/30"
            >
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-blue-400 font-medium">Memory Engine</div>
                  <div className="text-gray-300">Entities: {engineStatus.memory.entities || 0}</div>
                  <div className="text-gray-300">Status: {engineStatus.memory.active ? 'Active' : 'Inactive'}</div>
                </div>
                <div className="text-center">
                  <div className="text-yellow-400 font-medium">Parallel Engine</div>
                  <div className="text-gray-300">Tasks: {engineStatus.parallel.tasks || 0}</div>
                  <div className="text-gray-300">Status: {engineStatus.parallel.active ? 'Active' : 'Inactive'}</div>
                </div>
                <div className="text-center">
                  <div className="text-pink-400 font-medium">Creative Engine</div>
                  <div className="text-gray-300">Ideas: {engineStatus.creative.ideas || 0}</div>
                  <div className="text-gray-300">Status: {engineStatus.creative.active ? 'Active' : 'Inactive'}</div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Chat Messages */}
      <div className="chat-messages flex-1 overflow-y-auto p-4 space-y-4" ref={chatRef}>
        <AnimatePresence>
          {conversations.map((message, index) => (
            <motion.div
              key={message.id}
              variants={messageVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              layout
            >
              <MessageBubble 
                message={message}
                onReaction={onReaction}
                contextAware={contextItems.some(item => 
                  item.relatedTo?.includes(message.id)
                )}
                engineData={message.engineData}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicators */}
        <AnimatePresence>
          {typingAgents.map(agent => (
            <motion.div
              key={`typing-${agent.id}`}
              className="typing-indicator flex items-center space-x-3 p-3 bg-gray-700/30 rounded-lg"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="typing-content flex items-center space-x-2">
                <span className="text-lg">{agent.icon}</span>
                <span className="text-white font-medium">{agent.name}</span>
                <span className="text-gray-300">is thinking</span>
                <div className="typing-dots flex space-x-1">
                  <motion.div
                    className="w-2 h-2 bg-blue-400 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-blue-400 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-blue-400 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Three-Engine Orchestration Display */}
        {orchestrationActive && (
          <ThreeEngineOrchestration 
            onComplete={() => setOrchestrationActive(false)}
            engineStatus={engineStatus}
          />
        )}

        {/* Empty State */}
        {conversations.length === 0 && !isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="text-6xl mb-4">🎪</div>
            <h3 className="text-xl font-bold text-white mb-2">
              Welcome to the Multi-Agent Workspace Arena!
            </h3>
            <p className="text-gray-300 max-w-md mx-auto">
              Select your agents above and start a conversation to see the three-engine coordination in action.
            </p>
          </motion.div>
        )}
      </div>

      {/* Chat Actions */}
      <div className="chat-actions p-4 border-t border-gray-700/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <motion.button
              onClick={loadContext}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 rounded-lg transition-colors"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh Memory Context</span>
            </motion.button>

            <motion.button
              onClick={() => setOrchestrationActive(true)}
              disabled={!threeEngineMode}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                threeEngineMode
                  ? 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-300'
                  : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
              }`}
              whileHover={threeEngineMode ? { scale: 1.02 } : {}}
              whileTap={threeEngineMode ? { scale: 0.98 } : {}}
            >
              <Zap className="w-4 h-4" />
              <span>Trigger Three-Engine Mode</span>
            </motion.button>
          </div>

          <motion.button
            onClick={exportConversation}
            className="flex items-center space-x-2 px-3 py-2 bg-green-600/20 hover:bg-green-600/30 text-green-300 rounded-lg transition-colors"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Download className="w-4 h-4" />
            <span>Export Conversation</span>
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default ChatWorkspace;