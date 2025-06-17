# 🚀 reVoAgent API Examples

## Quick Start Examples

### 1. Basic Health Check
```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T08:30:00.000Z",
  "service": "reVoAgent Backend API",
  "version": "1.0.0"
}
```

### 2. Get Available Models
```bash
curl -X GET http://localhost:8000/api/models \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "models": [
    {
      "id": "deepseek_r1_0528",
      "name": "DeepSeek R1 0528",
      "type": "local",
      "cost_per_request": 0.0,
      "status": "available"
    }
  ],
  "cost_savings": "95%+",
  "local_models_active": true
}
```

### 3. Send Chat Message
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "content": "Analyze this Python function for improvements",
    "context": {
      "code": "def process_data(data):\n    return data.upper()",
      "language": "python"
    }
  }'
```

**Response:**
```json
{
  "response": "I've analyzed your function. Here are some improvements:\n1. Add type hints\n2. Add input validation\n3. Consider error handling",
  "model_used": "deepseek_r1_0528",
  "cost": 0.0,
  "response_time": "0.8s",
  "suggestions": [
    "Add type hints: def process_data(data: str) -> str:",
    "Add input validation for None values",
    "Consider using .title() for better formatting"
  ]
}
```

## Advanced Examples

### 4. Multi-Agent Code Review
```bash
curl -X POST http://localhost:8000/api/chat/multi-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "session_id": "review_session_001",
    "message": "Please review this function for bugs and performance",
    "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "agents": ["code-analyst", "debug-detective", "workflow-manager"]
  }'
```

**Response:**
```json
{
  "session_id": "review_session_001",
  "responses": [
    {
      "agent": "code-analyst",
      "response": "This recursive implementation has exponential time complexity O(2^n). Consider using dynamic programming or memoization.",
      "confidence": 0.95
    },
    {
      "agent": "debug-detective",
      "response": "No bugs detected, but the function will cause stack overflow for large n values (n > 1000).",
      "confidence": 0.88
    },
    {
      "agent": "workflow-manager",
      "response": "For production use, implement iterative version or use lru_cache decorator for memoization.",
      "confidence": 0.92
    }
  ],
  "consensus": "Optimize algorithm using memoization or iterative approach",
  "total_cost": 0.0,
  "collaboration_score": 0.92
}
```

### 5. Start Agent Task
```bash
curl -X POST http://localhost:8000/api/agents/code-analyst/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "task_type": "security_scan",
    "input": {
      "code": "import os\npassword = os.environ.get(\"PASSWORD\")\nprint(f\"Password: {password}\")",
      "language": "python"
    },
    "options": {
      "include_suggestions": true,
      "severity_threshold": "medium"
    }
  }'
```

**Response:**
```json
{
  "task_id": "task_sec_001",
  "status": "started",
  "estimated_completion": "15s",
  "agent_id": "code-analyst"
}
```

### 6. Get Task Results
```bash
curl -X GET http://localhost:8000/api/agents/code-analyst/tasks/task_sec_001 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "task_id": "task_sec_001",
  "status": "completed",
  "result": {
    "security_issues": [
      {
        "severity": "high",
        "type": "information_disclosure",
        "line": 3,
        "description": "Password printed to console - potential information leak",
        "suggestion": "Remove print statement or use logging with appropriate level"
      }
    ],
    "suggestions": [
      "Use logging instead of print for sensitive information",
      "Consider using environment variable validation",
      "Add error handling for missing environment variables"
    ],
    "security_score": 45,
    "overall_assessment": "Code has security vulnerabilities that should be addressed"
  },
  "execution_time": "12.3s",
  "cost": 0.0,
  "model_used": "deepseek_r1_0528"
}
```

## Integration Examples

### 7. GitHub Integration - Create PR
```bash
curl -X POST http://localhost:8000/api/integrations/github/repos/myorg/myrepo/pulls \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "AI-suggested code improvements",
    "body": "This PR contains improvements suggested by reVoAgent AI analysis:\n\n- Added type hints\n- Improved error handling\n- Optimized performance",
    "head": "ai-improvements",
    "base": "main"
  }'
```

### 8. Slack Notification
```bash
curl -X POST http://localhost:8000/api/integrations/slack/notify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "channel": "#development",
    "message": "Code analysis completed for PR #123",
    "attachments": [
      {
        "title": "Analysis Results",
        "text": "Found 3 optimization opportunities and 1 security issue",
        "color": "warning",
        "fields": [
          {
            "title": "Security Issues",
            "value": "1 high severity",
            "short": true
          },
          {
            "title": "Performance",
            "value": "3 optimizations",
            "short": true
          }
        ]
      }
    ]
  }'
```

### 9. JIRA Issue Creation
```bash
curl -X POST http://localhost:8000/api/integrations/jira/issues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "project": "DEV",
    "summary": "Security vulnerability found in authentication module",
    "description": "AI analysis detected potential information disclosure in password handling. See attached analysis report.",
    "issue_type": "Bug",
    "priority": "High",
    "labels": ["security", "ai-detected"],
    "components": ["authentication"]
  }'
```

## Analytics Examples

### 10. Cost Analytics
```bash
curl -X GET http://localhost:8000/api/analytics/costs?period=last_7_days \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "total_requests": 2847,
  "local_requests": 2847,
  "cloud_requests": 0,
  "cost_savings": "100%",
  "total_cost": 0.0,
  "estimated_cloud_cost": 85.41,
  "savings_amount": 85.41,
  "period": "last_7_days",
  "breakdown": {
    "deepseek_r1_0528": {
      "requests": 2103,
      "cost": 0.0
    },
    "llama_3_1_70b": {
      "requests": 744,
      "cost": 0.0
    }
  }
}
```

### 11. Performance Metrics
```bash
curl -X GET http://localhost:8000/api/analytics/performance \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "average_response_time": "0.8s",
  "success_rate": "99.2%",
  "throughput": "150 requests/minute",
  "agent_utilization": {
    "code-analyst": "78%",
    "debug-detective": "65%",
    "workflow-manager": "45%",
    "multi-agent-chat": "32%"
  },
  "system_health": "87.5%",
  "peak_performance": {
    "max_throughput": "245 requests/minute",
    "min_response_time": "0.2s",
    "peak_concurrent_users": 89
  }
}
```

## WebSocket Examples

### 12. Real-time Chat (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// Send message
ws.send(JSON.stringify({
  type: 'chat_message',
  content: 'Analyze this code for performance issues',
  code: 'for i in range(1000000): print(i)',
  agents: ['code-analyst']
}));

// Receive responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent response:', data.response);
  console.log('Cost:', data.cost);
  console.log('Model used:', data.model_used);
};
```

### 13. Agent Status Monitoring (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agents');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  switch(update.type) {
    case 'agent_status_change':
      console.log(`Agent ${update.agent_id} is now ${update.status}`);
      break;
    case 'task_completed':
      console.log(`Task ${update.task_id} completed by ${update.agent_id}`);
      break;
    case 'performance_update':
      console.log(`System performance: ${update.metrics.system_health}`);
      break;
  }
};
```

## Python SDK Examples

### 14. Using Python SDK
```python
from revoagent import ReVoAgentClient

# Initialize client
client = ReVoAgentClient(
    base_url="http://localhost:8000",
    api_key="your-jwt-token"
)

# Simple chat
response = client.chat.send(
    content="Review this function",
    code="def add(a, b): return a + b"
)
print(f"Response: {response.content}")
print(f"Cost: ${response.cost}")

# Multi-agent collaboration
agents_response = client.chat.multi_agent(
    message="Optimize this algorithm",
    code="def bubble_sort(arr): ...",
    agents=["code-analyst", "debug-detective"]
)

for agent_response in agents_response.responses:
    print(f"{agent_response.agent}: {agent_response.response}")

# Start agent task
task = client.agents.start_task(
    agent_id="code-analyst",
    task_type="security_scan",
    input={"code": "...", "language": "python"}
)

# Wait for completion
result = client.agents.wait_for_task(task.task_id)
print(f"Security score: {result.security_score}")
```

## Error Handling Examples

### 15. Handling API Errors
```bash
# Invalid request
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{}'
```

**Error Response:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: 'content'",
    "details": "The 'content' field is required for chat requests",
    "timestamp": "2025-06-11T08:30:00.000Z",
    "request_id": "req_12345"
  }
}
```

### 16. Rate Limiting
```bash
# Too many requests
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"content": "test"}'
```

**Rate Limit Response:**
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "details": "Rate limit exceeded: 100 requests per minute",
    "timestamp": "2025-06-11T08:30:00.000Z",
    "retry_after": 60
  }
}
```

---

## Best Practices

### Authentication
- Always include the JWT token in the Authorization header
- Refresh tokens before they expire
- Use HTTPS in production

### Error Handling
- Check HTTP status codes
- Parse error responses for detailed information
- Implement retry logic for transient errors

### Performance
- Use WebSocket connections for real-time features
- Cache model and agent information
- Batch requests when possible

### Cost Optimization
- Prefer local models for routine tasks
- Use cloud models only for complex operations
- Monitor cost analytics regularly

---

*Last Updated: 2025-06-11*  
*API Version: 1.0.0*