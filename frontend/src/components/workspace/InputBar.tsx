import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Paperclip, 
  Mic, 
  MicOff, 
  Image, 
  Code, 
  Zap, 
  Brain,
  Palette,
  Settings,
  Smile,
  Hash,
  AtSign
} from 'lucide-react';
import { getAgentById } from '../../constants/agents';

interface InputBarProps {
  onMessage: (message: string, selectedAgents: string[]) => void;
  selectedAgents: string[];
  isProcessing: boolean;
  threeEngineMode: boolean;
}

const InputBar: React.FC<InputBarProps> = ({
  onMessage,
  selectedAgents,
  isProcessing,
  threeEngineMode
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showEmojis, setShowEmojis] = useState(false);
  const [showCommands, setShowCommands] = useState(false);
  const [showMentions, setShowMentions] = useState(false);
  const [messageType, setMessageType] = useState<'text' | 'code' | 'image'>('text');
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  // Focus on textarea when agents are selected
  useEffect(() => {
    if (selectedAgents.length > 0 && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [selectedAgents]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || selectedAgents.length === 0 || isProcessing) return;

    onMessage(message.trim(), selectedAgents);
    setMessage('');
    setShowEmojis(false);
    setShowCommands(false);
    setShowMentions(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
    
    // Handle command shortcuts
    if (e.key === '/' && message === '') {
      setShowCommands(true);
    }
    
    if (e.key === '@' && message.endsWith(' ')) {
      setShowMentions(true);
    }
  };

  const insertEmoji = (emoji: string) => {
    setMessage(prev => prev + emoji);
    setShowEmojis(false);
    textareaRef.current?.focus();
  };

  const insertCommand = (command: string) => {
    setMessage(command + ' ');
    setShowCommands(false);
    textareaRef.current?.focus();
  };

  const insertMention = (agentId: string) => {
    const agent = getAgentById(agentId);
    if (agent) {
      setMessage(prev => prev + `@${agent.name} `);
    }
    setShowMentions(false);
    textareaRef.current?.focus();
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording functionality
  };

  const handleFileUpload = () => {
    fileInputRef.current?.click();
  };

  const emojis = ['😊', '👍', '❤️', '🎉', '🚀', '💡', '🔥', '⭐', '🎯', '💪', '🧠', '⚡', '🎨', '🛠️', '📊', '🔍'];
  
  const commands = [
    { command: '/analyze', description: 'Analyze data or code', icon: '📊' },
    { command: '/create', description: 'Create new content', icon: '✨' },
    { command: '/debug', description: 'Debug code or issues', icon: '🐛' },
    { command: '/explain', description: 'Explain concepts', icon: '💡' },
    { command: '/optimize', description: 'Optimize performance', icon: '⚡' },
    { command: '/review', description: 'Review and improve', icon: '👀' },
    { command: '/research', description: 'Research topics', icon: '🔍' },
    { command: '/design', description: 'Design solutions', icon: '🎨' }
  ];

  const selectedAgentNames = selectedAgents.map(id => getAgentById(id)?.name).filter(Boolean);

  return (
    <div className="input-bar bg-gray-800/40 backdrop-blur-md border-t border-gray-700/50 p-4">
      <form onSubmit={handleSubmit} className="relative">
        {/* Agent Selection Display */}
        {selectedAgents.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-3 flex items-center space-x-2"
          >
            <span className="text-sm text-gray-400">Collaborating with:</span>
            <div className="flex items-center space-x-2">
              {selectedAgents.slice(0, 5).map(agentId => {
                const agent = getAgentById(agentId);
                return agent ? (
                  <div
                    key={agentId}
                    className="flex items-center space-x-1 px-2 py-1 bg-gray-700/50 rounded-full text-xs"
                  >
                    <span>{agent.icon}</span>
                    <span className="text-gray-300">{agent.name}</span>
                  </div>
                ) : null;
              })}
              {selectedAgents.length > 5 && (
                <span className="text-xs text-gray-400">
                  +{selectedAgents.length - 5} more
                </span>
              )}
            </div>
            {threeEngineMode && (
              <div className="flex items-center space-x-1 px-2 py-1 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full text-xs">
                <Zap className="w-3 h-3" />
                <span className="text-blue-300">Three-Engine Mode</span>
              </div>
            )}
          </motion.div>
        )}

        {/* Main Input Area */}
        <div className="relative">
          <div className="flex items-end space-x-3">
            {/* Message Type Selector */}
            <div className="flex flex-col space-y-1">
              <button
                type="button"
                onClick={() => setMessageType('text')}
                className={`p-2 rounded-lg transition-colors ${
                  messageType === 'text' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-700/50 text-gray-400 hover:bg-gray-600/50'
                }`}
                title="Text message"
              >
                <Hash className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setMessageType('code')}
                className={`p-2 rounded-lg transition-colors ${
                  messageType === 'code' 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-700/50 text-gray-400 hover:bg-gray-600/50'
                }`}
                title="Code message"
              >
                <Code className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => setMessageType('image')}
                className={`p-2 rounded-lg transition-colors ${
                  messageType === 'image' 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-gray-700/50 text-gray-400 hover:bg-gray-600/50'
                }`}
                title="Image message"
              >
                <Image className="w-4 h-4" />
              </button>
            </div>

            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  selectedAgents.length === 0 
                    ? "Select agents above to start collaborating..." 
                    : `Message ${selectedAgentNames.join(', ')}... (Press / for commands, @ to mention)`
                }
                disabled={selectedAgents.length === 0 || isProcessing}
                className="w-full min-h-[60px] max-h-[200px] p-4 pr-12 bg-gray-700/50 border border-gray-600/50 rounded-xl text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                rows={1}
              />

              {/* Input Actions */}
              <div className="absolute right-2 bottom-2 flex items-center space-x-1">
                <button
                  type="button"
                  onClick={() => setShowEmojis(!showEmojis)}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Add emoji"
                >
                  <Smile className="w-4 h-4 text-gray-400" />
                </button>
                
                <button
                  type="button"
                  onClick={handleFileUpload}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Attach file"
                >
                  <Paperclip className="w-4 h-4 text-gray-400" />
                </button>
                
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={`p-1 rounded-lg transition-colors ${
                    isRecording 
                      ? 'bg-red-600 text-white' 
                      : 'hover:bg-gray-600/50 text-gray-400'
                  }`}
                  title={isRecording ? "Stop recording" : "Start voice recording"}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Send Button */}
            <motion.button
              type="submit"
              disabled={!message.trim() || selectedAgents.length === 0 || isProcessing}
              className={`p-3 rounded-xl transition-all ${
                message.trim() && selectedAgents.length > 0 && !isProcessing
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/25'
                  : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
              }`}
              whileHover={message.trim() && selectedAgents.length > 0 && !isProcessing ? { scale: 1.05 } : {}}
              whileTap={message.trim() && selectedAgents.length > 0 && !isProcessing ? { scale: 0.95 } : {}}
            >
              {isProcessing ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Settings className="w-5 h-5" />
                </motion.div>
              ) : (
                <Send className="w-5 h-5" />
              )}
            </motion.button>
          </div>

          {/* Engine Status Indicators */}
          {threeEngineMode && (
            <div className="flex items-center justify-center space-x-4 mt-2">
              <div className="flex items-center space-x-1 text-xs text-blue-400">
                <Brain className="w-3 h-3" />
                <span>Memory</span>
              </div>
              <div className="flex items-center space-x-1 text-xs text-yellow-400">
                <Zap className="w-3 h-3" />
                <span>Parallel</span>
              </div>
              <div className="flex items-center space-x-1 text-xs text-pink-400">
                <Palette className="w-3 h-3" />
                <span>Creative</span>
              </div>
            </div>
          )}
        </div>

        {/* Emoji Picker */}
        <AnimatePresence>
          {showEmojis && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute bottom-full left-0 mb-2 bg-gray-800/95 backdrop-blur-md rounded-lg p-3 border border-gray-700 shadow-xl z-10"
            >
              <div className="grid grid-cols-8 gap-2">
                {emojis.map(emoji => (
                  <button
                    key={emoji}
                    onClick={() => insertEmoji(emoji)}
                    className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
                  >
                    <span className="text-lg">{emoji}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Command Picker */}
        <AnimatePresence>
          {showCommands && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute bottom-full left-0 mb-2 bg-gray-800/95 backdrop-blur-md rounded-lg p-3 border border-gray-700 shadow-xl z-10 min-w-[300px]"
            >
              <div className="space-y-1">
                {commands.map(cmd => (
                  <button
                    key={cmd.command}
                    onClick={() => insertCommand(cmd.command)}
                    className="w-full flex items-center space-x-3 p-2 hover:bg-gray-700/50 rounded-lg transition-colors text-left"
                  >
                    <span className="text-lg">{cmd.icon}</span>
                    <div>
                      <div className="text-white font-medium">{cmd.command}</div>
                      <div className="text-gray-400 text-sm">{cmd.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mention Picker */}
        <AnimatePresence>
          {showMentions && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute bottom-full left-0 mb-2 bg-gray-800/95 backdrop-blur-md rounded-lg p-3 border border-gray-700 shadow-xl z-10 min-w-[250px]"
            >
              <div className="space-y-1">
                {selectedAgents.map(agentId => {
                  const agent = getAgentById(agentId);
                  return agent ? (
                    <button
                      key={agentId}
                      onClick={() => insertMention(agentId)}
                      className="w-full flex items-center space-x-2 p-2 hover:bg-gray-700/50 rounded-lg transition-colors text-left"
                    >
                      <span className="text-lg">{agent.icon}</span>
                      <span className="text-white">{agent.name}</span>
                    </button>
                  ) : null;
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            // TODO: Handle file uploads
            console.log('Files selected:', e.target.files);
          }}
        />
      </form>
    </div>
  );
};

export default InputBar;