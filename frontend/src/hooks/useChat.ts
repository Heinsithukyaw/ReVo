import { useEffect, useCallback } from 'react';
import { useAppStore } from '../store';
import { ChatMessage, ChatSession } from '../types/chat';
import apiClient from '../services/api';
import { webSocketManager } from '../services/websocket';

export const useChat = (sessionId?: string) => {
  const {
    messages,
    sessions,
    currentSession,
    typingIndicators,
    agentActivities,
    isConnected,
    isLoading,
    error,
    setMessages,
    addMessage,
    updateMessage,
    setSessions,
    setCurrentSession,
    addSession,
    updateSession,
    setTypingIndicators,
    addTypingIndicator,
    removeTypingIndicator,
    setAgentActivities,
    updateAgentActivity,
    setConnected,
    setLoading,
    setError,
  } = useAppStore();

  const fetchMessages = useCallback(async (sessionId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const endpoint = sessionId ? `/chat/sessions/${sessionId}/messages` : '/chat/messages';
      const response = await apiClient.get(endpoint);
      setMessages(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch messages');
    } finally {
      setLoading(false);
    }
  }, [setMessages, setLoading, setError]);

  const fetchSessions = useCallback(async () => {
    try {
      const response = await apiClient.get('/chat/sessions');
      setSessions(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sessions');
    }
  }, [setSessions, setError]);

  const createSession = useCallback(async (sessionData: Omit<ChatSession, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/chat/sessions', sessionData);
      addSession(response.data);
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addSession, setLoading, setError]);

  const sendMessage = useCallback(async (content: string, agentId?: string) => {
    try {
      const messageData = {
        content,
        agentId,
        sessionId: currentSession?.id,
        timestamp: new Date().toISOString(),
      };

      // Optimistically add message to UI
      const tempMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user' as const,
        content,
        timestamp: messageData.timestamp,
        agentId,
      };
      addMessage(tempMessage);

      // Send to backend
      const response = await apiClient.post('/chat/send', messageData);
      
      // Update with real message from backend
      updateMessage(tempMessage.id, response.data);
      
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    }
  }, [currentSession?.id, addMessage, updateMessage, setError]);

  const sendToAgent = useCallback(async (content: string, agentId: string) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/agent', {
        query: content,
        agent: agentId,
      });
      
      // Add agent response to messages
      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
        agentId,
        agentName: response.data.agent,
      };
      addMessage(agentMessage);
      
      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message to agent');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addMessage, setLoading, setError]);

  const initializeWebSocket = useCallback(() => {
    webSocketManager.connect('/ws/chat', {
      onOpen: () => setConnected(true),
      onClose: () => setConnected(false),
      onMessage: (data) => {
        switch (data.type) {
          case 'message':
            addMessage(data.message);
            break;
          case 'typing_start':
            addTypingIndicator({
              userId: data.userId,
              agentId: data.agentId,
              isTyping: true,
              timestamp: new Date().toISOString(),
            });
            break;
          case 'typing_stop':
            removeTypingIndicator(data.userId);
            break;
          case 'agent_activity':
            updateAgentActivity(data.agentId, data.activity);
            break;
          default:
            console.log('Unknown message type:', data.type);
        }
      },
      onError: (error) => {
        setError('WebSocket connection error');
        setConnected(false);
      },
    });
  }, [setConnected, addMessage, addTypingIndicator, removeTypingIndicator, updateAgentActivity, setError]);

  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    if (isConnected) {
      webSocketManager.sendMessage('/ws/chat', {
        type: isTyping ? 'typing_start' : 'typing_stop',
        userId: 'user', // This would be dynamic in a real app
        timestamp: new Date().toISOString(),
      });
    }
  }, [isConnected]);

  // Initialize data and WebSocket on mount
  useEffect(() => {
    fetchMessages(sessionId);
    fetchSessions();
    initializeWebSocket();

    return () => {
      webSocketManager.disconnect('/ws/chat');
    };
  }, [sessionId, fetchMessages, fetchSessions, initializeWebSocket]);

  return {
    // State
    messages,
    sessions,
    currentSession,
    typingIndicators,
    agentActivities,
    isConnected,
    isLoading,
    error,
    
    // Actions
    setCurrentSession,
    fetchMessages,
    fetchSessions,
    createSession,
    sendMessage,
    sendToAgent,
    sendTypingIndicator,
  };
};