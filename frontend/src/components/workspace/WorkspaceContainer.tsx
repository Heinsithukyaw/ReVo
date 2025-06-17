import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentSelectionBar from './AgentSelectionBar';
import ChatWorkspace from './ChatWorkspace';
import InputBar from './InputBar';
import Sidebar from '../layout/Sidebar';
import { Agent } from '../../constants/agents';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useThreeEngines } from '../../hooks/useThreeEngines';
import { useAgentSelection } from '../../hooks/useAgentSelection';

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

const WorkspaceContainer: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [conversations, setConversations] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Custom hooks for functionality
  const { socket, isConnected, sendMessage } = useWebSocket('ws://localhost:8000/ws/chat');
  const { engineStatus, coordinateEngines, isCoordinating } = useThreeEngines();
  const { selectedAgents, toggleAgent, clearSelection } = useAgentSelection();

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome-1',
      content: `🎪 Welcome to the Multi-Agent Workspace Arena! 

Your revolutionary AI command center is ready with:
• 🧠 **Memory Engine**: Persistent context and learning
• ⚡ **Parallel Engine**: Multi-agent coordination  
• 🎨 **Creative Engine**: Innovative problem solving
• 🛠️ **200+ MCP Tools**: Integrated marketplace
• 🖥️ **ReVo Computer**: Browser automation

Select your agents above and start collaborating! 💪`,
      sender: 'system',
      senderName: 'reVoAgent System',
      senderIcon: '🎪',
      timestamp: new Date(),
      reactions: {}
    };
    setConversations([welcomeMessage]);
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    if (socket) {
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'agent_response') {
          const newMessage: Message = {
            id: `msg-${Date.now()}-${Math.random()}`,
            content: data.content,
            sender: 'agent',
            senderName: data.agent_name || 'AI Agent',
            senderIcon: data.agent_icon || '🤖',
            timestamp: new Date(),
            agentType: data.agent_type,
            engineData: data.engine_data,
            reactions: {}
          };
          setConversations(prev => [...prev, newMessage]);
        }
        
        if (data.type === 'engine_status') {
          // Engine status updates handled by useThreeEngines hook
        }
        
        setIsProcessing(false);
      };
    }
  }, [socket]);

  const handleAgentMessage = async (message: string, selectedAgentIds: string[]) => {
    if (!message.trim() || selectedAgentIds.length === 0) return;

    setIsProcessing(true);

    // Add user message to conversation
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: message,
      sender: 'user',
      senderName: 'You',
      senderIcon: '👤',
      timestamp: new Date(),
      reactions: {}
    };
    setConversations(prev => [...prev, userMessage]);

    try {
      // Coordinate three engines for agent response
      const engineResponse = await coordinateEngines({
        message,
        agents: selectedAgentIds,
        mode: 'collaborative'
      });

      // Send message via WebSocket
      if (socket && isConnected) {
        sendMessage({
          type: 'multi_agent_message',
          message,
          agents: selectedAgentIds,
          three_engine_mode: true,
          engine_coordination: engineResponse
        });
      } else {
        // Fallback to direct API call
        const response = await fetch('http://localhost:8000/api/chat/multi-agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            agents: selectedAgentIds,
            three_engine_mode: true
          })
        });

        if (response.ok) {
          const data = await response.json();
          const agentMessage: Message = {
            id: `agent-${Date.now()}`,
            content: data.response,
            sender: 'agent',
            senderName: data.agent_name || 'Multi-Agent Team',
            senderIcon: '🤖',
            timestamp: new Date(),
            engineData: data.engine_data,
            reactions: {}
          };
          setConversations(prev => [...prev, agentMessage]);
        }
        setIsProcessing(false);
      }
    } catch (error) {
      console.error('Agent coordination error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        sender: 'system',
        senderName: 'System Error',
        senderIcon: '⚠️',
        timestamp: new Date(),
        reactions: {}
      };
      setConversations(prev => [...prev, errorMessage]);
      setIsProcessing(false);
    }
  };

  const handleReaction = (messageId: string, reaction: string) => {
    setConversations(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const reactions = { ...msg.reactions };
        reactions[reaction] = (reactions[reaction] || 0) + 1;
        return { ...msg, reactions };
      }
      return msg;
    }));
  };

  const threeEngineMode = engineStatus.memory.active && 
                          engineStatus.parallel.active && 
                          engineStatus.creative.active;

  return (
    <div className="workspace-container h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex overflow-hidden">
      {/* Main Workspace Area */}
      <div className={`workspace-main flex-1 flex flex-col transition-all duration-300 ${
        sidebarCollapsed ? 'mr-16' : 'mr-80'
      }`}>
        {/* Agent Selection Bar - Full Width */}
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="workspace-header"
        >
          <AgentSelectionBar 
            selectedAgents={selectedAgents}
            onAgentToggle={toggleAgent}
            engineStatus={engineStatus}
            threeEngineMode={threeEngineMode}
          />
        </motion.div>

        {/* Chat Workspace - Primary Area */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex-1 overflow-hidden"
        >
          <ChatWorkspace 
            conversations={conversations}
            isConnected={isConnected}
            onReaction={handleReaction}
            isProcessing={isProcessing || isCoordinating}
            engineStatus={engineStatus}
          />
        </motion.div>

        {/* Input Bar - Full Width */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="workspace-footer"
        >
          <InputBar 
            onMessage={handleAgentMessage}
            selectedAgents={selectedAgents}
            isProcessing={isProcessing || isCoordinating}
            threeEngineMode={threeEngineMode}
          />
        </motion.div>
      </div>

      {/* Collapsible Sidebar */}
      <AnimatePresence>
        <motion.div
          initial={{ x: 320 }}
          animate={{ x: sidebarCollapsed ? 256 : 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          className="fixed right-0 top-0 h-full z-40"
        >
          <Sidebar 
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            engineStatus={engineStatus}
            selectedAgents={selectedAgents}
            conversations={conversations}
            isConnected={isConnected}
          />
        </motion.div>
      </AnimatePresence>

      {/* Three-Engine Coordination Overlay */}
      <AnimatePresence>
        {isCoordinating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="bg-gray-800/90 backdrop-blur-md rounded-2xl p-8 border border-gray-700 max-w-md mx-4"
            >
              <div className="text-center">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-xl font-bold text-white mb-2">
                  Three-Engine Coordination Active
                </h3>
                <p className="text-gray-300 mb-4">
                  Memory🧠 + Parallel⚡ + Creative🎨 engines are collaborating...
                </p>
                <div className="flex justify-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-100"></div>
                  <div className="w-2 h-2 bg-pink-500 rounded-full animate-pulse delay-200"></div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Connection Status Indicator */}
      <div className="fixed top-4 left-4 z-30">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className={`px-3 py-2 rounded-full text-sm font-medium backdrop-blur-md border ${
            isConnected 
              ? 'bg-green-500/20 border-green-500/30 text-green-300' 
              : 'bg-red-500/20 border-red-500/30 text-red-300'
          }`}
        >
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-400' : 'bg-red-400'
            } ${isConnected ? 'animate-pulse' : ''}`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default WorkspaceContainer;