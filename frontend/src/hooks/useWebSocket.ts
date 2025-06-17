import { useState, useEffect, useRef, useCallback } from 'react';
import { apiService } from '../services/api';
import type { WebSocketMessage } from '../types';

export interface UseWebSocketOptions {
  endpoint?: string;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    endpoint = '/ws/chat',
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectCountRef = useRef(0);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    setError(null);

    try {
      wsRef.current = apiService.createWebSocket(endpoint);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null);
        reconnectCountRef.current = 0;
        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        if (!mountedRef.current) return;
        
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onDisconnect?.();

        // Attempt to reconnect if we haven't exceeded the limit
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (event) => {
        if (!mountedRef.current) return;
        
        setConnectionStatus('error');
        setError('WebSocket connection error');
        onError?.(event);
      };

    } catch (err) {
      setConnectionStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to create WebSocket connection');
    }
  }, [endpoint, reconnectAttempts, reconnectInterval, onMessage, onConnect, onDisconnect, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messageToSend = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(messageToSend);
      return true;
    }
    return false;
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectCountRef.current = 0;
    setTimeout(connect, 100);
  }, [connect, disconnect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    error,
    sendMessage,
    reconnect,
    disconnect
  };
}

// Specialized hook for real-time dashboard updates
export function useDashboardWebSocket() {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);

  const { isConnected, connectionStatus, sendMessage, error } = useWebSocket({
    endpoint: '/ws/dashboard',
    onMessage: (message) => {
      switch (message.type) {
        case 'dashboard_update':
          setDashboardData(message.data);
          break;
        case 'notification':
          setNotifications(prev => [message.data, ...prev.slice(0, 9)]); // Keep last 10
          break;
        case 'agent_status':
          // Handle agent status updates
          break;
        case 'system_metrics':
          // Handle system metrics updates
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    }
  });

  const sendDashboardCommand = useCallback((command: string, data?: any) => {
    return sendMessage({
      type: 'dashboard_command',
      command,
      data,
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  return {
    isConnected,
    connectionStatus,
    error,
    dashboardData,
    notifications,
    sendDashboardCommand
  };
}

// Chat WebSocket hook
export function useChatWebSocket() {
  const [messages, setMessages] = useState<any[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const { isConnected, connectionStatus, sendMessage, error } = useWebSocket({
    endpoint: '/ws/chat',
    onMessage: (message) => {
      switch (message.type) {
        case 'chat_message':
          setMessages(prev => [...prev, message.data]);
          break;
        case 'typing_start':
          setIsTyping(true);
          break;
        case 'typing_stop':
          setIsTyping(false);
          break;
        case 'chat_error':
          console.error('Chat error:', message.data);
          break;
      }
    }
  });

  const sendChatMessage = useCallback((content: string, options?: any) => {
    const message = {
      type: 'chat_message',
      data: {
        content,
        timestamp: new Date().toISOString(),
        ...options
      }
    };
    return sendMessage(message);
  }, [sendMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    isConnected,
    connectionStatus,
    error,
    messages,
    isTyping,
    sendChatMessage,
    clearMessages
  };
}