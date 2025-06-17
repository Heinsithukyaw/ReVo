import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Menu, Keyboard } from 'lucide-react';
import FullReVoDashboard from './components/FullReVoDashboard';
import ThreeEngineArchitectureDashboard from './components/ThreeEngineArchitectureDashboard';
import EnhancedCollapsibleDashboard from './components/EnhancedCollapsibleDashboard';
import WorkspaceContainer from './components/workspace/WorkspaceContainer';
import EnhancedWorkspaceChat from './components/enhanced/EnhancedWorkspaceChat';
import StreamingChat from './components/enhanced/StreamingChat';
import EnhancedAgentDashboard from './components/enhanced/EnhancedAgentDashboard';
import ThreeEngineWorkspace from './components/three-engine/ThreeEngineWorkspace';
import StandardUserDashboard from './components/standard/StandardUserDashboard';
import LLMDashboard from './components/LLMDashboard';
import EnhancedChat from './components/EnhancedChat';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'workspace' | 'enhanced' | 'standard' | 'three-engine' | 'llm' | 'enhanced-chat'>('enhanced-chat');
  const [enhancedMode, setEnhancedMode] = useState<'chat' | 'streaming' | 'dashboard'>('streaming');
  const [isToolbarCollapsed, setIsToolbarCollapsed] = useState(false);

  // Keyboard shortcut to toggle toolbar (Ctrl/Cmd + `)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === '`') {
        event.preventDefault();
        setIsToolbarCollapsed(!isToolbarCollapsed);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isToolbarCollapsed]);

  return (
    <div>
      {/* Enhanced Collapsible Toolbar */}
      <div className="fixed top-4 right-4 z-50">
        <motion.div
          initial={false}
          animate={{
            width: isToolbarCollapsed ? 'auto' : 'auto',
            opacity: 1
          }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="relative"
        >
          {/* Collapse/Expand Toggle Button */}
          <motion.button
            onClick={() => setIsToolbarCollapsed(!isToolbarCollapsed)}
            className="absolute -left-10 top-2 bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 border border-gray-700 hover:bg-gray-700/90 transition-all duration-200 z-10 group"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title={`${isToolbarCollapsed ? 'Expand' : 'Collapse'} Toolbar (Ctrl/Cmd + \`)`}
          >
            <motion.div
              animate={{ rotate: isToolbarCollapsed ? 0 : 180 }}
              transition={{ duration: 0.3 }}
            >
              {isToolbarCollapsed ? (
                <ChevronLeft className="w-4 h-4 text-gray-300 group-hover:text-white" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-white" />
              )}
            </motion.div>
            
            {/* Keyboard shortcut indicator */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              whileHover={{ opacity: 1, scale: 1 }}
              className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-xs text-gray-300 px-2 py-1 rounded border border-gray-600 whitespace-nowrap"
            >
              <Keyboard className="w-3 h-3 inline mr-1" />
              Ctrl+`
            </motion.div>
          </motion.button>

          {/* Collapsed State - Show only active tab indicator */}
          <AnimatePresence>
            {isToolbarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 border border-gray-700 cursor-pointer hover:bg-gray-700/90 transition-all duration-200"
                onClick={() => setIsToolbarCollapsed(false)}
                title="Click to expand toolbar"
              >
                <div className="flex items-center space-x-2">
                  <Menu className="w-4 h-4 text-gray-400" />
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span className="text-xs text-gray-300 font-medium">
                    {currentView === 'llm' && '🤖'}
                    {currentView === 'workspace' && '🎪'}
                    {currentView === 'enhanced' && '🚀'}
                    {currentView === 'three-engine' && '🧠'}
                    {currentView === 'standard' && '📊'}
                    {currentView === 'enhanced-chat' && '💬'}
                  </span>
                  <span className="text-xs text-gray-500 ml-1">
                    {currentView === 'llm' && 'LLM'}
                    {currentView === 'workspace' && 'Arena'}
                    {currentView === 'enhanced' && 'Enhanced'}
                    {currentView === 'three-engine' && 'Engine'}
                    {currentView === 'standard' && 'Standard'}
                    {currentView === 'enhanced-chat' && 'Enhanced Chat'}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Expanded State - Show full toolbar */}
          <AnimatePresence>
            {!isToolbarCollapsed && (
              <motion.div
                initial={{ opacity: 0, x: 20, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 20, scale: 0.95 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              >
                <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 border border-gray-700 shadow-xl">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentView('enhanced-chat')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'enhanced-chat'
                          ? 'bg-green-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      💬 Enhanced Chat
                    </button>
                    <button
                      onClick={() => setCurrentView('llm')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'llm'
                          ? 'bg-blue-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      🤖 LLM Hub
                    </button>
                    <button
                      onClick={() => setCurrentView('workspace')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'workspace'
                          ? 'bg-blue-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      🎪 Workspace
                    </button>
                    <button
                      onClick={() => setCurrentView('enhanced')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'enhanced'
                          ? 'bg-blue-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      🚀 Enhanced
                    </button>
                    <button
                      onClick={() => setCurrentView('three-engine')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'three-engine'
                          ? 'bg-blue-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      🧠 Three-Engine
                    </button>
                    <button
                      onClick={() => setCurrentView('standard')}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                        currentView === 'standard'
                          ? 'bg-blue-600 text-white shadow-lg'
                          : 'text-gray-300 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      📊 Standard
                    </button>
                  </div>
                </div>
                
                {/* Mode Toggle for Enhanced */}
                <AnimatePresence>
                  {currentView === 'enhanced' && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2, delay: 0.1 }}
                      className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-2 border border-gray-700 mt-2 shadow-lg"
                    >
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setEnhancedMode('chat')}
                          className={`px-3 py-1 rounded text-xs font-medium transition-all duration-200 ${
                            enhancedMode === 'chat'
                              ? 'bg-purple-600 text-white shadow-md'
                              : 'text-gray-300 hover:text-white hover:bg-gray-700'
                          }`}
                        >
                          💬 Chat
                        </button>
                        <button
                          onClick={() => setEnhancedMode('streaming')}
                          className={`px-3 py-1 rounded text-xs font-medium transition-all duration-200 ${
                            enhancedMode === 'streaming'
                              ? 'bg-blue-600 text-white shadow-md'
                              : 'text-gray-300 hover:text-white hover:bg-gray-700'
                          }`}
                        >
                          ⚡ Streaming
                        </button>
                        <button
                          onClick={() => setEnhancedMode('dashboard')}
                          className={`px-3 py-1 rounded text-xs font-medium transition-all duration-200 ${
                            enhancedMode === 'dashboard'
                              ? 'bg-purple-600 text-white shadow-md'
                              : 'text-gray-300 hover:text-white hover:bg-gray-700'
                          }`}
                        >
                          📊 Analytics
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Dashboard Views */}
      {currentView === 'enhanced-chat' ? (
        <EnhancedChat />
      ) : currentView === 'llm' ? (
        <LLMDashboard />
      ) : currentView === 'workspace' ? (
        <WorkspaceContainer />
      ) : currentView === 'enhanced' ? (
        enhancedMode === 'chat' ? <EnhancedWorkspaceChat /> : 
        enhancedMode === 'streaming' ? <StreamingChat /> : 
        <EnhancedAgentDashboard />
      ) : currentView === 'three-engine' ? (
        <ThreeEngineWorkspace />
      ) : (
        <StandardUserDashboard />
      )}
    </div>
  );
};

export default App;