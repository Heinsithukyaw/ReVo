// Type-Safe API Responses
interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  services: Record<string, string>;
  llm_status: Record<string, any>;
}

interface ChatResponse {
  response: string;
  model: string;
  timestamp: string;
  tokens_used: number;
  response_time: number;
}

interface AgentResponse {
  agent: string;
  response: string;
  model: string;
  timestamp: string;
}
