import { useState, useEffect, useCallback } from 'react';
import { frontendLLMApi, ChatRequest, ChatResponse } from '../services/frontend_llm_api';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  model?: string;
  loading?: boolean;
}

export interface UseLLMChatProps {
  defaultModel?: string;
  defaultTemperature?: number;
  defaultMaxTokens?: number;
}

export function useLLMChat({
  defaultModel = 'deepseek-r1',
  defaultTemperature = 0.7,
  defaultMaxTokens = 1000
}: UseLLMChatProps = {}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [currentModel, setCurrentModel] = useState(defaultModel);
  const [temperature, setTemperature] = useState(defaultTemperature);
  const [maxTokens, setMaxTokens] = useState(defaultMaxTokens);
  const [hasStreamingSupport, setHasStreamingSupport] = useState<boolean | null>(null);
  
  // Check for streaming support on mount
  useEffect(() => {
    const checkStreamingSupport = async () => {
      try {
        const health = await frontendLLMApi.getHealth();
        // This is a simplified check - in real app we might look at specific capabilities
        setHasStreamingSupport(true);
      } catch (err) {
        setHasStreamingSupport(false);
        console.warn('Error checking streaming support:', err);
      }
    };
    
    checkStreamingSupport();
  }, []);
  
  // Send message using standard (non-streaming) API
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    // Add user message immediately
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Add placeholder for assistant message
    const placeholderId = `placeholder-${Date.now()}`;
    const placeholderMessage: Message = {
      id: placeholderId,
      role: 'assistant',
      content: '',
      loading: true,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prevMessages => [...prevMessages, placeholderMessage]);
    setLoading(true);
    setError(null);
    
    try {
      // Send chat request to API
      const request: ChatRequest = {
        message: content,
        model: currentModel,
        temperature,
        max_tokens: maxTokens
      };
      
      const response = await frontendLLMApi.chat(request);
      
      // Replace placeholder with actual response
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === placeholderId
            ? {
                id: Date.now().toString(),
                role: 'assistant',
                content: response.response,
                timestamp: response.timestamp,
                model: response.model,
                loading: false
              }
            : msg
        )
      );
    } catch (err) {
      setError(err as Error);
      // Update placeholder to show error
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === placeholderId
            ? {
                id: Date.now().toString(),
                role: 'assistant',
                content: `Error: ${(err as Error).message}`,
                timestamp: new Date().toISOString(),
                loading: false
              }
            : msg
        )
      );
    } finally {
      setLoading(false);
    }
  }, [currentModel, temperature, maxTokens]);
  
  // Send message with streaming response
  const sendStreamingMessage = useCallback((content: string) => {
    if (!content.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    // Add user message immediately
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Add placeholder for assistant message
    const placeholderId = `placeholder-${Date.now()}`;
    const placeholderMessage: Message = {
      id: placeholderId,
      role: 'assistant',
      content: '',
      loading: true,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prevMessages => [...prevMessages, placeholderMessage]);
    setLoading(true);
    setError(null);
    
    // Create streaming response
    frontendLLMApi.streamChat(
      content,
      currentModel,
      (chunk) => {
        // Update placeholder with received chunk
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === placeholderId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      },
      (response) => {
        // Complete the message when streaming is done
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === placeholderId
              ? {
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: response.response, // Use the final response
                  timestamp: response.timestamp,
                  model: response.model,
                  loading: false
                }
              : msg
          )
        );
        setLoading(false);
      },
      (error) => {
        setError(error);
        // Update placeholder to show error
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === placeholderId
              ? {
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: `Error: ${error.message}`,
                  timestamp: new Date().toISOString(),
                  loading: false
                }
              : msg
          )
        );
        setLoading(false);
      }
    );
  }, [currentModel]);
  
  // Choose the appropriate send function based on streaming support
  const send = useCallback((content: string) => {
    if (hasStreamingSupport) {
      sendStreamingMessage(content);
    } else {
      sendMessage(content);
    }
  }, [hasStreamingSupport, sendMessage, sendStreamingMessage]);
  
  // Clear conversation
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);
  
  return {
    messages,
    loading,
    error,
    send,
    clearMessages,
    currentModel,
    setCurrentModel,
    temperature,
    setTemperature,
    maxTokens,
    setMaxTokens,
    hasStreamingSupport
  };
}