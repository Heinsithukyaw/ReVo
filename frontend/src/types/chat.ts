export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agentId?: string;
  agentName?: string;
  attachments?: Attachment[];
  metadata?: Record<string, any>;
}

export interface Attachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'code' | 'link';
  url: string;
  size?: number;
  mimeType?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  participants: string[];
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'archived';
}

export interface TypingIndicator {
  userId: string;
  agentId?: string;
  isTyping: boolean;
  timestamp: string;
}

export interface AgentActivity {
  agentId: string;
  activity: 'thinking' | 'typing' | 'processing' | 'idle';
  timestamp: string;
}