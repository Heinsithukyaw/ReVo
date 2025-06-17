import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, ThumbsUp, Smile, Star, Brain, Copy, Share, MoreHorizontal } from 'lucide-react';

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

interface MessageBubbleProps {
  message: Message;
  onReaction: (messageId: string, reaction: string) => void;
  contextAware?: boolean;
  engineData?: any;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onReaction,
  contextAware = false,
  engineData
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [hovering, setHovering] = useState(false);
  const [showReactions, setShowReactions] = useState(false);

  const isSystemMessage = message.sender === 'system';
  const isUserMessage = message.sender === 'user';
  const isAgentMessage = message.sender === 'agent';

  const reactions = ['👍', '❤️', '😊', '⭐', '🧠', '⚡', '🎨', '🔥'];

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getAgentColor = (agentType?: string) => {
    const colors: { [key: string]: string } = {
      'development': '59, 130, 246', // blue
      'ai-ml': '139, 92, 246', // purple
      'business': '16, 185, 129', // green
      'creative': '236, 72, 153', // pink
      'security': '239, 68, 68', // red
      'operations': '245, 158, 11' // yellow
    };
    return colors[agentType || 'default'] || '107, 114, 128'; // gray
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
  };

  const shareMessage = () => {
    if (navigator.share) {
      navigator.share({
        title: `Message from ${message.senderName}`,
        text: message.content
      });
    }
  };

  const messageStyle = isSystemMessage 
    ? 'bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/20'
    : isUserMessage
    ? 'bg-gray-700/30 border-gray-600/30 ml-12'
    : `bg-gray-800/40 border-gray-600/30 mr-12`;

  return (
    <motion.div 
      className={`message-bubble relative p-4 rounded-2xl border backdrop-blur-sm ${messageStyle} ${
        contextAware ? 'ring-2 ring-blue-500/30' : ''
      }`}
      onHoverStart={() => setHovering(true)}
      onHoverEnd={() => setHovering(false)}
      whileHover={{ scale: 1.01 }}
      layout
    >
      {/* Message Header */}
      <div className="message-header flex items-center justify-between mb-2">
        <div className="sender-info flex items-center space-x-2">
          <span className="text-2xl">{message.senderIcon}</span>
          <span className="text-white font-medium">{message.senderName}</span>
          {contextAware && (
            <motion.span 
              className="context-badge bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full text-xs flex items-center space-x-1"
              title="Memory context available"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
            >
              <Brain className="w-3 h-3" />
              <span>Context</span>
            </motion.span>
          )}
          {message.agentType && (
            <span className="text-xs text-gray-400 capitalize">
              {message.agentType}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-gray-400 text-sm">{formatTime(message.timestamp)}</span>
          
          {/* Message Actions */}
          <AnimatePresence>
            {hovering && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center space-x-1"
              >
                <button
                  onClick={() => setShowReactions(!showReactions)}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Add reaction"
                >
                  <Smile className="w-4 h-4 text-gray-400" />
                </button>
                <button
                  onClick={copyToClipboard}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Copy message"
                >
                  <Copy className="w-4 h-4 text-gray-400" />
                </button>
                <button
                  onClick={shareMessage}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Share message"
                >
                  <Share className="w-4 h-4 text-gray-400" />
                </button>
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="p-1 hover:bg-gray-600/50 rounded-lg transition-colors"
                  title="Message details"
                >
                  <MoreHorizontal className="w-4 h-4 text-gray-400" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Message Content */}
      <div className="message-content text-gray-100 leading-relaxed whitespace-pre-wrap">
        {message.content}
      </div>

      {/* Engine Data Display */}
      {engineData && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="engine-data mt-3 p-3 bg-gray-700/30 rounded-lg border border-gray-600/30"
        >
          <div className="text-sm text-gray-300 mb-2">Engine Analysis:</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {engineData.memory && (
              <div className="bg-blue-500/10 p-2 rounded border border-blue-500/20">
                <div className="text-blue-300 font-medium">Memory Engine</div>
                <div className="text-gray-300">Entities: {engineData.memory.entities || 0}</div>
                <div className="text-gray-300">Relevance: {engineData.memory.relevance || 0}%</div>
              </div>
            )}
            {engineData.parallel && (
              <div className="bg-yellow-500/10 p-2 rounded border border-yellow-500/20">
                <div className="text-yellow-300 font-medium">Parallel Engine</div>
                <div className="text-gray-300">Tasks: {engineData.parallel.tasks || 0}</div>
                <div className="text-gray-300">Speed: {engineData.parallel.speed || 0}ms</div>
              </div>
            )}
            {engineData.creative && (
              <div className="bg-pink-500/10 p-2 rounded border border-pink-500/20">
                <div className="text-pink-300 font-medium">Creative Engine</div>
                <div className="text-gray-300">Ideas: {engineData.creative.ideas || 0}</div>
                <div className="text-gray-300">Innovation: {engineData.creative.innovation || 0}%</div>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Message Details */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="message-details mt-3 p-3 bg-gray-700/30 rounded-lg border border-gray-600/30"
          >
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Message ID:</span>
                <span className="text-gray-300 font-mono text-xs">{message.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Timestamp:</span>
                <span className="text-gray-300">{message.timestamp.toISOString()}</span>
              </div>
              {message.agentType && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Agent Type:</span>
                  <span className="text-gray-300 capitalize">{message.agentType}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Character Count:</span>
                <span className="text-gray-300">{message.content.length}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reactions */}
      {message.reactions && Object.keys(message.reactions).length > 0 && (
        <div className="message-reactions flex items-center space-x-2 mt-3">
          {Object.entries(message.reactions).map(([reaction, count]) => (
            <motion.button
              key={reaction}
              onClick={() => onReaction(message.id, reaction)}
              className="flex items-center space-x-1 px-2 py-1 bg-gray-700/50 hover:bg-gray-600/50 rounded-full text-sm transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span>{reaction}</span>
              <span className="text-gray-300">{count}</span>
            </motion.button>
          ))}
        </div>
      )}

      {/* Reaction Picker */}
      <AnimatePresence>
        {showReactions && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            className="absolute bottom-full left-4 mb-2 bg-gray-800/95 backdrop-blur-md rounded-lg p-2 border border-gray-700 shadow-xl z-10"
          >
            <div className="flex items-center space-x-1">
              {reactions.map(reaction => (
                <motion.button
                  key={reaction}
                  onClick={() => {
                    onReaction(message.id, reaction);
                    setShowReactions(false);
                  }}
                  className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
                  whileHover={{ scale: 1.2 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <span className="text-lg">{reaction}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Context Awareness Indicator */}
      {contextAware && (
        <motion.div
          className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          title="This message has memory context"
        >
          <Brain className="w-2 h-2 text-white" />
        </motion.div>
      )}
    </motion.div>
  );
};

export default MessageBubble;