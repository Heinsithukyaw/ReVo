import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketHookReturn {
  isConnected: boolean;
  dashboardData: any;
  systemMetrics: any;
  agentUpdates: any[];
  sendMessage: (message: any) => void;
  reconnect: () => void;
}

export const useWebSocket = (url: string): WebSocketHookReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [systemMetrics, setSystemMetrics] = useState<any>({});
  const [agentUpdates, setAgentUpdates] = useState<any[]>([]);
  
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;

  const connect = useCallback(() => {
    try {
      websocketRef.current = new WebSocket(url);

      websocketRef.current.onopen = () => {
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        
        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000);
      };

      websocketRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'initial_dashboard':
              setDashboardData(message.data);
              break;
              
            case 'glassmorphism_update':
              setSystemMetrics(message.data);
              break;
              
            case 'dashboard_refresh':
              setDashboardData(message.data);
              break;
              
            case 'agent_update':
              setAgentUpdates(prev => [message, ...prev.slice(0, 99)]); // Keep last 100
              break;
              
            case 'pong':
              // Handle pong response
              if (message.metrics) {
                setSystemMetrics(prev => ({ ...prev, ...message.metrics }));
              }
              break;
              
            default:
              console.log('📨 Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };

      websocketRef.current.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect unless it was a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`🔄 Attempting to reconnect in ${delay}ms...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      websocketRef.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
    }
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
    }
  }, []);

  const reconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (websocketRef.current) {
        websocketRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  return {
    isConnected,
    dashboardData,
    systemMetrics,
    agentUpdates,
    sendMessage,
    reconnect
  };
};