import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  enhancedChatApi, 
  EnhancedChatMessage, 
  EnhancedAgent, 
  ChatSession, 
  ChatOptions,
  ChatResponse 
} from '../services/enhancedChatApi';

// Enhanced chat hook with full functionality
export function useEnhancedChat() {
  const [messages, setMessages] = useState<EnhancedChatMessage[]>([]);
  const [agents, setAgents] = useState<EnhancedAgent[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [typingAgents, setTypingAgents] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Initialize chat
  useEffect(() => {
    const initializeChat = async () => {
      try {
        setIsLoading(true);
        
        // Load agents
        const agentsData = await enhancedChatApi.getAgents();
        setAgents(agentsData);

        // Load sessions
        const sessionsData = await enhancedChatApi.getChatSessions();
        setSessions(sessionsData);

        // Load recent messages
        const messagesData = await enhancedChatApi.getChatHistory();
        setMessages(messagesData);

        // Connect WebSocket
        enhancedChatApi.connectWebSocket(
          handleNewMessage,
          handleAgentTyping,
          handleWebSocketError
        );
        setIsConnected(true);

      } catch (error) {
        console.error('Error initializing chat:', error);
        setError('Failed to initialize chat');
      } finally {
        setIsLoading(false);
      }
    };

    initializeChat();

    // Cleanup on unmount
    return () => {
      enhancedChatApi.disconnectWebSocket();
    };
  }, []);

  // Handle new messages from WebSocket
  const handleNewMessage = useCallback((message: EnhancedChatMessage) => {
    setMessages(prev => [...prev, message]);
    
    // Remove typing indicator for this agent
    if (message.agentName) {
      setTypingAgents(prev => prev.filter(agent => agent !== message.agentName));
    }
  }, []);

  // Handle agent typing indicator
  const handleAgentTyping = useCallback((agentName: string) => {
    setTypingAgents(prev => {
      if (!prev.includes(agentName)) {
        return [...prev, agentName];
      }
      return prev;
    });

    // Remove typing indicator after 3 seconds
    setTimeout(() => {
      setTypingAgents(prev => prev.filter(agent => agent !== agentName));
    }, 3000);
  }, []);

  // Handle WebSocket errors
  const handleWebSocketError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
    setIsConnected(false);
    setError('Connection lost. Attempting to reconnect...');
  }, []);

  // Send message
  const sendMessage = useCallback(async (
    content: string, 
    options: ChatOptions = {}
  ): Promise<ChatResponse | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // Create user message
      const userMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content,
        sender: 'user',
        timestamp: new Date(),
        type: 'text'
      };

      setMessages(prev => [...prev, userMessage]);

      // Send via WebSocket if connected, otherwise use REST API
      if (isConnected) {
        enhancedChatApi.sendWebSocketMessage(content, options);
        return null; // Response will come via WebSocket
      } else {
        const response = await enhancedChatApi.sendMessage(content, options);
        
        // Create agent message from response
        const agentMessage: EnhancedChatMessage = {
          id: (Date.now() + 1).toString(),
          content: response.content,
          sender: 'agent',
          agentName: response.agentName,
          agentType: response.agentType as any,
          timestamp: new Date(),
          type: response.type as any,
          metadata: response.metadata
        };

        setMessages(prev => [...prev, agentMessage]);
        return response;
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [isConnected]);

  // Send multi-agent message
  const sendMultiAgentMessage = useCallback(async (
    content: string,
    agentIds: string[],
    options: ChatOptions = {}
  ): Promise<ChatResponse[]> => {
    try {
      setIsLoading(true);
      setError(null);

      // Create user message
      const userMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content,
        sender: 'user',
        timestamp: new Date(),
        type: 'text'
      };

      setMessages(prev => [...prev, userMessage]);

      const responses = await enhancedChatApi.sendMultiAgentMessage(content, agentIds, options);
      
      // Create agent messages from responses
      responses.forEach((response, index) => {
        const agentMessage: EnhancedChatMessage = {
          id: (Date.now() + index + 1).toString(),
          content: response.content,
          sender: 'agent',
          agentName: response.agentName,
          agentType: response.agentType as any,
          timestamp: new Date(),
          type: response.type as any,
          metadata: response.metadata
        };

        setMessages(prev => [...prev, agentMessage]);
      });

      return responses;
    } catch (error) {
      console.error('Error sending multi-agent message:', error);
      setError('Failed to send multi-agent message');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Upload file
  const uploadFile = useCallback(async (file: File) => {
    try {
      setIsLoading(true);
      setError(null);

      const uploadResponse = await enhancedChatApi.uploadFile(file);
      
      // Create file message
      const fileMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content: `Uploaded file: ${file.name}`,
        sender: 'user',
        timestamp: new Date(),
        type: 'file',
        metadata: {
          fileName: file.name,
          fileSize: file.size
        },
        attachments: [{
          id: uploadResponse.id,
          name: uploadResponse.name,
          type: uploadResponse.type,
          size: uploadResponse.size,
          url: uploadResponse.url,
          thumbnail: uploadResponse.thumbnail
        }]
      };

      setMessages(prev => [...prev, fileMessage]);
      return uploadResponse;
    } catch (error) {
      console.error('Error uploading file:', error);
      setError('Failed to upload file');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Create new session
  const createSession = useCallback(async (title?: string) => {
    try {
      const session = await enhancedChatApi.createChatSession(title);
      setSessions(prev => [session, ...prev]);
      setCurrentSession(session);
      setMessages([]); // Clear messages for new session
      return session;
    } catch (error) {
      console.error('Error creating session:', error);
      setError('Failed to create session');
      throw error;
    }
  }, []);

  // Switch session
  const switchSession = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        setCurrentSession(session);
        const sessionMessages = await enhancedChatApi.getChatHistory(sessionId);
        setMessages(sessionMessages);
      }
    } catch (error) {
      console.error('Error switching session:', error);
      setError('Failed to switch session');
    } finally {
      setIsLoading(false);
    }
  }, [sessions]);

  // Add reaction to message
  const addReaction = useCallback(async (messageId: string, emoji: string) => {
    try {
      await enhancedChatApi.addReaction(messageId, emoji);
      
      // Update local message
      setMessages(prev => prev.map(msg => {
        if (msg.id === messageId) {
          const reactions = { ...msg.reactions };
          reactions[emoji] = (reactions[emoji] || 0) + 1;
          return { ...msg, reactions };
        }
        return msg;
      }));
    } catch (error) {
      console.error('Error adding reaction:', error);
      setError('Failed to add reaction');
    }
  }, []);

  // Bookmark message
  const bookmarkMessage = useCallback(async (messageId: string) => {
    try {
      await enhancedChatApi.bookmarkMessage(messageId);
      
      // Update local message
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, isBookmarked: !msg.isBookmarked } : msg
      ));
    } catch (error) {
      console.error('Error bookmarking message:', error);
      setError('Failed to bookmark message');
    }
  }, []);

  // Search messages
  const searchMessages = useCallback(async (query: string, filters?: any) => {
    try {
      setIsLoading(true);
      const results = await enhancedChatApi.searchMessages(query, filters);
      return results;
    } catch (error) {
      console.error('Error searching messages:', error);
      setError('Failed to search messages');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Execute code
  const executeCode = useCallback(async (code: string, language: string) => {
    try {
      setIsLoading(true);
      const result = await enhancedChatApi.executeCode(code, language);
      
      // Create execution result message
      const resultMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content: result.success ? result.output : result.error || 'Execution failed',
        sender: 'agent',
        agentName: 'Code Executor',
        agentType: 'code',
        timestamp: new Date(),
        type: 'code',
        metadata: {
          codeExecuted: true,
          executionResult: result.output,
          processingTime: result.executionTime,
          language
        }
      };

      setMessages(prev => [...prev, resultMessage]);
      return result;
    } catch (error) {
      console.error('Error executing code:', error);
      setError('Failed to execute code');
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    // State
    messages,
    agents,
    sessions,
    currentSession,
    isLoading,
    isConnected,
    typingAgents,
    error,

    // Actions
    sendMessage,
    sendMultiAgentMessage,
    uploadFile,
    createSession,
    switchSession,
    addReaction,
    bookmarkMessage,
    searchMessages,
    executeCode,
    clearError,
    clearMessages
  };
}

// Simplified chat hook for basic usage
export function useSimpleChat() {
  const [messages, setMessages] = useState<EnhancedChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Add user message
      const userMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content,
        sender: 'user',
        timestamp: new Date(),
        type: 'text'
      };

      setMessages(prev => [...prev, userMessage]);

      // Send to API
      const response = await enhancedChatApi.sendMessage(content);
      
      // Add agent response
      const agentMessage: EnhancedChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        sender: 'agent',
        agentName: response.agentName,
        timestamp: new Date(),
        type: response.type as any,
        metadata: response.metadata
      };

      setMessages(prev => [...prev, agentMessage]);
      return response;
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    clearError
  };
}