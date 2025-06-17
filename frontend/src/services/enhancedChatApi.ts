// Enhanced Chat API Service for reVoAgent

export interface EnhancedChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  agentName?: string;
  agentType?: 'memory' | 'parallel' | 'creative' | 'code' | 'general';
  timestamp: Date;
  type: 'text' | 'code' | 'image' | 'file' | 'system';
  metadata?: {
    language?: string;
    fileName?: string;
    fileSize?: number;
    codeExecuted?: boolean;
    executionResult?: string;
    confidence?: number;
    processingTime?: number;
    tokens?: number;
    cost?: number;
    model?: string;
    temperature?: number;
  };
  reactions?: { [emoji: string]: number };
  isEdited?: boolean;
  isBookmarked?: boolean;
  isPinned?: boolean;
  threadId?: string;
  replyTo?: string;
  attachments?: Array<{
    id: string;
    name: string;
    type: string;
    size: number;
    url: string;
    thumbnail?: string;
  }>;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  participants: string[];
  isActive: boolean;
  metadata?: {
    totalTokens?: number;
    totalCost?: number;
    averageResponseTime?: number;
  };
}

export interface AgentCapability {
  id: string;
  name: string;
  description: string;
  category: string;
  examples: string[];
}

export interface EnhancedAgent {
  id: string;
  name: string;
  type: 'memory' | 'parallel' | 'creative' | 'code' | 'general';
  status: 'online' | 'busy' | 'offline' | 'maintenance';
  avatar: string;
  description: string;
  capabilities: AgentCapability[];
  isActive: boolean;
  responseTime: number;
  accuracy: number;
  totalInteractions: number;
  costPerToken: number;
  model: string;
  version: string;
  lastUpdated: Date;
  specializations: string[];
  supportedLanguages: string[];
  maxTokens: number;
  temperature: number;
}

export interface ChatOptions {
  agents?: string[];
  mode?: 'single' | 'multi' | 'collaborative';
  threadId?: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
  includeContext?: boolean;
  contextWindow?: number;
  model?: string;
  priority?: 'low' | 'normal' | 'high';
  timeout?: number;
}

export interface ChatResponse {
  id: string;
  content: string;
  agentName: string;
  agentType: string;
  type: 'text' | 'code' | 'image' | 'file' | 'system';
  metadata: {
    confidence: number;
    processingTime: number;
    tokens: number;
    cost: number;
    model: string;
    temperature: number;
  };
  suggestions?: string[];
  followUpQuestions?: string[];
  relatedTopics?: string[];
  codeBlocks?: Array<{
    language: string;
    code: string;
    explanation: string;
  }>;
}

export interface FileUploadResponse {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  thumbnail?: string;
  extractedText?: string;
  metadata?: any;
}

class EnhancedChatApiService {
  private baseUrl: string;
  private wsConnection: WebSocket | null = null;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  // Helper method for making API requests
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  // Enhanced chat message sending
  // FIXED: Connected to real AI generation endpoint
  async sendMessage(
    content: string, 
    options: ChatOptions = {}
  ): Promise<ChatResponse> {
    try {
      // Use the real AI generation endpoint
      const response = await this.makeRequest<any>('/api/v1/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          prompt: content, // Backend expects 'prompt' not 'content'
          max_tokens: options.maxTokens || 1024,
          temperature: options.temperature || 0.7,
          force_local: true // Use local models for cost optimization
        })
      });

      // Convert to ChatResponse format
      return {
        id: Date.now().toString(),
        content: response.content || response.response || 'No response',
        agentName: 'reVoAgent AI',
        agentType: 'general',
        type: 'text',
        metadata: {
          confidence: 0.95,
          processingTime: response.response_time || 0,
          tokens: response.usage?.total_tokens || 0,
          cost: response.cost || 0,
          model: response.model || 'deepseek-r1',
          temperature: options.temperature || 0.7
        },
        suggestions: this.generateSuggestions(content),
        followUpQuestions: this.generateFollowUpQuestions(content),
        relatedTopics: this.extractRelatedTopics(content)
      };
    } catch (error) {
      console.error('Error sending enhanced chat message:', error);
      throw error;
    }
  }

  // Multi-agent conversation
  async sendMultiAgentMessage(
    content: string,
    agentIds: string[],
    options: ChatOptions = {}
  ): Promise<ChatResponse[]> {
    try {
      const response = await this.makeRequest<{responses: ChatResponse[]}>('/api/chat/multi-agent', {
        method: 'POST',
        body: JSON.stringify({
          content,
          agentIds,
          ...options,
          timestamp: new Date().toISOString()
        })
      });

      return response.responses || [];
    } catch (error) {
      console.error('Error sending multi-agent message:', error);
      throw error;
    }
  }

  // Stream chat response
  async streamMessage(
    content: string,
    options: ChatOptions = {},
    onChunk: (chunk: string) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          ...options,
          stream: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'chunk') {
                onChunk(parsed.content);
              } else if (parsed.type === 'complete') {
                onComplete(parsed.response);
              }
            } catch (e) {
              console.warn('Failed to parse streaming data:', e);
            }
          }
        }
      }
    } catch (error) {
      onError(error as Error);
    }
  }

  // File upload
  async uploadFile(file: File): Promise<FileUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/api/chat/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  }

  // Get available agents
  async getAgents(): Promise<EnhancedAgent[]> {
    try {
      const response = await this.makeRequest<{agents: EnhancedAgent[]}>('/api/agents/enhanced');
      return response.agents || [];
    } catch (error) {
      console.error('Error fetching agents:', error);
      return [];
    }
  }

  // Get agent details
  async getAgent(agentId: string): Promise<EnhancedAgent | null> {
    try {
      const response = await this.makeRequest<{agent: EnhancedAgent}>(`/api/agents/${agentId}`);
      return response.agent || null;
    } catch (error) {
      console.error('Error fetching agent details:', error);
      return null;
    }
  }

  // Get chat sessions
  async getChatSessions(): Promise<ChatSession[]> {
    try {
      const response = await this.makeRequest<{sessions: ChatSession[]}>('/api/chat/sessions');
      return response.sessions || [];
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
      return [];
    }
  }

  // Create new chat session
  async createChatSession(title?: string): Promise<ChatSession> {
    try {
      const response = await this.makeRequest<{session: ChatSession}>('/api/chat/sessions', {
        method: 'POST',
        body: JSON.stringify({
          title: title || `Chat ${new Date().toLocaleString()}`
        })
      });
      return response.session;
    } catch (error) {
      console.error('Error creating chat session:', error);
      throw error;
    }
  }

  // Get chat history
  async getChatHistory(
    sessionId?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<EnhancedChatMessage[]> {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
      });
      
      if (sessionId) {
        params.append('sessionId', sessionId);
      }

      const response = await this.makeRequest<{messages: EnhancedChatMessage[]}>(`/api/chat/history?${params}`);
      return response.messages || [];
    } catch (error) {
      console.error('Error fetching chat history:', error);
      return [];
    }
  }

  // Search messages
  async searchMessages(
    query: string,
    filters?: {
      type?: string;
      agentType?: string;
      dateFrom?: Date;
      dateTo?: Date;
      sessionId?: string;
    }
  ): Promise<EnhancedChatMessage[]> {
    try {
      const response = await this.makeRequest<{messages: EnhancedChatMessage[]}>('/api/chat/search', {
        method: 'POST',
        body: JSON.stringify({
          query,
          filters
        })
      });
      return response.messages || [];
    } catch (error) {
      console.error('Error searching messages:', error);
      return [];
    }
  }

  // Add reaction to message
  async addReaction(messageId: string, emoji: string): Promise<void> {
    try {
      await this.makeRequest(`/api/chat/messages/${messageId}/reactions`, {
        method: 'POST',
        body: JSON.stringify({ emoji })
      });
    } catch (error) {
      console.error('Error adding reaction:', error);
      throw error;
    }
  }

  // Bookmark message
  async bookmarkMessage(messageId: string): Promise<void> {
    try {
      await this.makeRequest(`/api/chat/messages/${messageId}/bookmark`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error bookmarking message:', error);
      throw error;
    }
  }

  // Get bookmarked messages
  async getBookmarkedMessages(): Promise<EnhancedChatMessage[]> {
    try {
      const response = await this.makeRequest<{messages: EnhancedChatMessage[]}>('/api/chat/bookmarks');
      return response.messages || [];
    } catch (error) {
      console.error('Error fetching bookmarked messages:', error);
      return [];
    }
  }

  // Execute code
  async executeCode(
    code: string,
    language: string,
    options?: {
      timeout?: number;
      environment?: string;
    }
  ): Promise<{
    success: boolean;
    output: string;
    error?: string;
    executionTime: number;
  }> {
    try {
      const response = await this.makeRequest<{
        success: boolean;
        output: string;
        error?: string;
        executionTime: number;
      }>('/api/chat/execute-code', {
        method: 'POST',
        body: JSON.stringify({
          code,
          language,
          options
        })
      });
      return response;
    } catch (error) {
      console.error('Error executing code:', error);
      throw error;
    }
  }

  // Get chat analytics
  async getChatAnalytics(
    timeRange?: {
      from: Date;
      to: Date;
    }
  ): Promise<{
    totalMessages: number;
    totalSessions: number;
    averageResponseTime: number;
    totalTokens: number;
    totalCost: number;
    agentUsage: { [agentId: string]: number };
    popularTopics: string[];
    userSatisfaction: number;
  }> {
    try {
      const response = await this.makeRequest<{analytics: {
        totalMessages: number;
        totalSessions: number;
        averageResponseTime: number;
        totalTokens: number;
        totalCost: number;
        agentUsage: { [agentId: string]: number };
        popularTopics: string[];
        userSatisfaction: number;
      }}>('/api/chat/analytics', {
        method: 'POST',
        body: JSON.stringify({ timeRange })
      });
      return response.analytics;
    } catch (error) {
      console.error('Error fetching chat analytics:', error);
      throw error;
    }
  }

  // WebSocket connection for real-time chat
  connectWebSocket(
    onMessage: (message: EnhancedChatMessage) => void,
    onAgentTyping: (agentName: string) => void,
    onError: (error: Event) => void
  ): void {
    try {
      const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/chat/enhanced';
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log('Enhanced chat WebSocket connected');
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'message':
              onMessage(data.message);
              break;
            case 'agent_typing':
              onAgentTyping(data.agentName);
              break;
            case 'error':
              console.error('WebSocket error:', data.error);
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.wsConnection.onerror = onError;

      this.wsConnection.onclose = () => {
        console.log('Enhanced chat WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          this.connectWebSocket(onMessage, onAgentTyping, onError);
        }, 3000);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }

  // Send message via WebSocket
  sendWebSocketMessage(content: string, options: ChatOptions = {}): void {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify({
        type: 'chat_message',
        content,
        options,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.warn('WebSocket not connected');
    }
  }

  // Disconnect WebSocket
  disconnectWebSocket(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }
}

export const enhancedChatApi = new EnhancedChatApiService();