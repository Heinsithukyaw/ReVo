# 🚀 reVoAgent API Documentation

## Overview

The reVoAgent API provides comprehensive endpoints for enterprise AI development with cost-optimized model management, multi-agent collaboration, and real-time communication.

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Authentication**: JWT Bearer Token  
**Content-Type**: `application/json`

---

## 🔐 Authentication

### JWT Token Authentication
```http
Authorization: Bearer <your-jwt-token>
```

### Get Authentication Token
```http
POST /auth/login
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 🏥 Health & Status

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T08:30:00.000Z",
  "service": "reVoAgent Backend API",
  "version": "1.0.0"
}
```

### System Status
```http
GET /status
```

**Response**:
```json
{
  "system_health": "87.5%",
  "active_agents": 4,
  "cost_savings": "100%",
  "uptime": "2h 15m",
  "performance": "EXCELLENT"
}
```

---

## 🤖 AI Models

### List Available Models
```http
GET /api/models
```

**Response**:
```json
{
  "models": [
    {
      "id": "deepseek_r1_0528",
      "name": "DeepSeek R1 0528",
      "type": "local",
      "cost_per_request": 0.0,
      "status": "available",
      "priority": "primary"
    },
    {
      "id": "llama_3_1_70b",
      "name": "Llama 3.1 70B",
      "type": "local",
      "cost_per_request": 0.0,
      "status": "available",
      "priority": "secondary"
    },
    {
      "id": "openai_gpt4",
      "name": "OpenAI GPT-4",
      "type": "cloud",
      "cost_per_request": 0.03,
      "status": "available",
      "priority": "fallback"
    }
  ],
  "cost_savings": "95%+",
  "local_models_active": true
}
```

### Get Model Details
```http
GET /api/models/{model_id}
```

**Response**:
```json
{
  "id": "deepseek_r1_0528",
  "name": "DeepSeek R1 0528",
  "type": "local",
  "cost_per_request": 0.0,
  "status": "available",
  "priority": "primary",
  "performance_metrics": {
    "response_time": "0.002s",
    "success_rate": "100%",
    "last_used": "2025-06-11T08:30:00.000Z"
  },
  "capabilities": [
    "code_generation",
    "debugging",
    "analysis",
    "optimization"
  ]
}
```

### Switch Model Priority
```http
PUT /api/models/{model_id}/priority
Content-Type: application/json

{
  "priority": "primary"
}
```

---

## 🤖 Agents

### List Available Agents
```http
GET /api/agents
```

**Response**:
```json
{
  "agents": [
    {
      "id": "code-analyst",
      "name": "Code Analyst",
      "status": "active",
      "specialization": "code_analysis",
      "performance_score": 95.2
    },
    {
      "id": "debug-detective",
      "name": "Debug Detective", 
      "status": "active",
      "specialization": "debugging",
      "performance_score": 98.1
    },
    {
      "id": "workflow-manager",
      "name": "Workflow Manager",
      "status": "active",
      "specialization": "workflow_orchestration",
      "performance_score": 92.7
    },
    {
      "id": "multi-agent-chat",
      "name": "Multi-Agent Chat",
      "status": "active",
      "specialization": "collaboration",
      "performance_score": 89.4
    }
  ],
  "total_agents": 20,
  "active_agents": 4,
  "collaboration_active": true
}
```

### Get Agent Details
```http
GET /api/agents/{agent_id}
```

**Response**:
```json
{
  "id": "code-analyst",
  "name": "Code Analyst",
  "status": "active",
  "specialization": "code_analysis",
  "capabilities": [
    "static_analysis",
    "code_review",
    "security_scanning",
    "performance_optimization"
  ],
  "performance_metrics": {
    "success_rate": "95.2%",
    "average_response_time": "1.2s",
    "tasks_completed": 1247,
    "user_satisfaction": "4.8/5"
  },
  "configuration": {
    "model": "deepseek_r1_0528",
    "max_context": 8192,
    "temperature": 0.1
  }
}
```

### Start Agent Task
```http
POST /api/agents/{agent_id}/tasks
Content-Type: application/json

{
  "task_type": "code_analysis",
  "input": {
    "code": "def example_function():\n    return 'Hello World'",
    "language": "python"
  },
  "options": {
    "include_suggestions": true,
    "security_scan": true
  }
}
```

**Response**:
```json
{
  "task_id": "task_12345",
  "status": "started",
  "estimated_completion": "30s",
  "agent_id": "code-analyst"
}
```

### Get Task Status
```http
GET /api/agents/{agent_id}/tasks/{task_id}
```

**Response**:
```json
{
  "task_id": "task_12345",
  "status": "completed",
  "result": {
    "analysis": "Code is well-structured and follows Python conventions.",
    "suggestions": [
      "Consider adding type hints",
      "Add docstring for better documentation"
    ],
    "security_issues": [],
    "performance_score": 85
  },
  "execution_time": "1.2s",
  "cost": 0.0,
  "model_used": "deepseek_r1_0528"
}
```

---

## 💬 Chat & Communication

### Send Chat Message
```http
POST /api/chat
Content-Type: application/json

{
  "content": "Analyze this code for potential improvements",
  "context": {
    "code": "def process_data(data): return data.upper()",
    "language": "python"
  },
  "options": {
    "model": "auto",
    "include_agents": ["code-analyst", "debug-detective"]
  }
}
```

**Response**:
```json
{
  "response": "I've analyzed your code. Here are the improvements...",
  "model_used": "deepseek_r1_0528",
  "cost": 0.0,
  "response_time": "0.8s",
  "agents_involved": ["code-analyst"],
  "suggestions": [
    "Add type hints: def process_data(data: str) -> str:",
    "Add input validation",
    "Consider error handling"
  ],
  "timestamp": "2025-06-11T08:30:00.000Z"
}
```

### Multi-Agent Chat Session
```http
POST /api/chat/multi-agent
Content-Type: application/json

{
  "session_id": "session_123",
  "message": "I need help debugging and optimizing this function",
  "code": "def slow_function(items): return [item*2 for item in items if item > 0]",
  "agents": ["code-analyst", "debug-detective", "workflow-manager"]
}
```

**Response**:
```json
{
  "session_id": "session_123",
  "responses": [
    {
      "agent": "code-analyst",
      "response": "The function can be optimized using numpy for better performance...",
      "confidence": 0.92
    },
    {
      "agent": "debug-detective", 
      "response": "No bugs detected, but consider edge cases for empty lists...",
      "confidence": 0.88
    },
    {
      "agent": "workflow-manager",
      "response": "This function fits well in a data processing pipeline...",
      "confidence": 0.85
    }
  ],
  "consensus": "Optimize with numpy, add edge case handling",
  "total_cost": 0.0,
  "collaboration_score": 0.89
}
```

---

## 🔗 External Integrations

### GitHub Integration

#### List Repositories
```http
GET /api/integrations/github/repos
Authorization: Bearer <github-token>
```

#### Create Pull Request
```http
POST /api/integrations/github/repos/{owner}/{repo}/pulls
Content-Type: application/json

{
  "title": "AI-generated code improvements",
  "body": "Automated improvements suggested by reVoAgent",
  "head": "feature-branch",
  "base": "main"
}
```

### Slack Integration

#### Send Notification
```http
POST /api/integrations/slack/notify
Content-Type: application/json

{
  "channel": "#development",
  "message": "Code analysis completed",
  "attachments": [
    {
      "title": "Analysis Results",
      "text": "Found 3 optimization opportunities",
      "color": "good"
    }
  ]
}
```

### JIRA Integration

#### Create Issue
```http
POST /api/integrations/jira/issues
Content-Type: application/json

{
  "project": "DEV",
  "summary": "Code optimization suggestions from AI analysis",
  "description": "Automated analysis found several improvement opportunities",
  "issue_type": "Task",
  "priority": "Medium"
}
```

---

## 📊 Analytics & Monitoring

### Cost Analytics
```http
GET /api/analytics/costs
```

**Response**:
```json
{
  "total_requests": 1247,
  "local_requests": 1247,
  "cloud_requests": 0,
  "cost_savings": "100%",
  "total_cost": 0.0,
  "estimated_cloud_cost": 37.41,
  "savings_amount": 37.41,
  "period": "last_30_days"
}
```

### Performance Metrics
```http
GET /api/analytics/performance
```

**Response**:
```json
{
  "average_response_time": "0.8s",
  "success_rate": "99.2%",
  "throughput": "150 requests/minute",
  "agent_utilization": {
    "code-analyst": "78%",
    "debug-detective": "65%",
    "workflow-manager": "45%"
  },
  "system_health": "87.5%"
}
```

---

## 🔧 Configuration

### Update System Configuration
```http
PUT /api/config
Content-Type: application/json

{
  "model_priority": ["deepseek_r1_0528", "llama_3_1_70b", "openai_gpt4"],
  "cost_optimization": true,
  "max_concurrent_agents": 5,
  "response_timeout": 30
}
```

### Get Current Configuration
```http
GET /api/config
```

**Response**:
```json
{
  "model_priority": ["deepseek_r1_0528", "llama_3_1_70b", "openai_gpt4"],
  "cost_optimization": true,
  "max_concurrent_agents": 5,
  "response_timeout": 30,
  "security_level": "enterprise",
  "monitoring_enabled": true
}
```

---

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request parameters are invalid",
    "details": "Missing required field: 'content'",
    "timestamp": "2025-06-11T08:30:00.000Z",
    "request_id": "req_12345"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_REQUEST` | Request parameters are invalid | 400 |
| `UNAUTHORIZED` | Authentication required | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMITED` | Too many requests | 429 |
| `MODEL_UNAVAILABLE` | AI model is not available | 503 |
| `AGENT_BUSY` | Agent is currently processing | 503 |
| `INTERNAL_ERROR` | Internal server error | 500 |

---

## 📡 WebSocket API

### Real-time Multi-Agent Chat
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// Send message
ws.send(JSON.stringify({
  type: 'chat_message',
  content: 'Analyze this code',
  agents: ['code-analyst', 'debug-detective']
}));

// Receive responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent response:', data);
};
```

### Agent Status Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agents');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Handle agent status changes
  console.log('Agent update:', update);
};
```

---

## 🔒 Security

### Rate Limiting
- **Default**: 100 requests per minute per user
- **Premium**: 1000 requests per minute per user
- **Enterprise**: Custom limits

### Data Privacy
- All data is processed locally when using local models
- Cloud models only used as fallback with explicit consent
- No data stored permanently without user permission

### Security Headers
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

---

## 📈 Performance

### Response Times
- **Health Check**: < 10ms
- **Model List**: < 50ms
- **Chat (Local)**: < 1s
- **Chat (Cloud)**: < 3s
- **Agent Tasks**: 1-30s (depending on complexity)

### Throughput
- **Concurrent Users**: Up to 1000
- **Requests per Second**: Up to 500
- **Agent Capacity**: 20 agents, 5 concurrent per agent

---

## 🛠️ SDKs & Libraries

### Python SDK
```python
from revoagent import ReVoAgentClient

client = ReVoAgentClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Send chat message
response = client.chat.send("Analyze this code", code="def hello(): pass")
print(response.content)
```

### JavaScript SDK
```javascript
import { ReVoAgentClient } from '@revoagent/sdk';

const client = new ReVoAgentClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// Send chat message
const response = await client.chat.send({
  content: 'Analyze this code',
  code: 'def hello(): pass'
});
```

---

## 📞 Support

- **Documentation**: [https://docs.revoagent.com](https://docs.revoagent.com)
- **GitHub**: [https://github.com/heinzdev11/reVoAgent](https://github.com/heinzdev11/reVoAgent)
- **Issues**: [GitHub Issues](https://github.com/heinzdev11/reVoAgent/issues)
- **Community**: [Discord Server](https://discord.gg/revoagent)

---

*Last Updated: 2025-06-11*  
*API Version: 1.0.0*  
*reVoAgent Enterprise AI Platform*