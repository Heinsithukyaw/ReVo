# 🚀 reVoAgent API Documentation

## 📋 **Overview**

The reVoAgent API provides enterprise-grade access to our revolutionary AI development platform with 95% cost savings through intelligent local-first execution.

**Base URL**: `http://localhost:12001`  
**Version**: `1.0.0`  
**Authentication**: JWT Bearer Token (Enterprise)  
**Rate Limiting**: 60 requests/minute per integration  
**Compliance**: SOC2, HIPAA, GDPR ready  

---

## 🔐 **Authentication**

### Enterprise Authentication
```http
POST /auth/login
Content-Type: application/json

{
  "username": "enterprise_user",
  "password": "secure_password",
  "organization": "your_org"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "organization": "your_org",
  "permissions": ["read", "write", "admin"]
}
```

### Using Authentication
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## 🏥 **Health & Status Endpoints**

### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-11T08:27:36.175941",
  "version": "1.0.0",
  "services": {
    "api": "running",
    "database": "connected",
    "ai_models": "ready"
  },
  "uptime": "2h 15m 30s",
  "system_health": "87.5%"
}
```

### API Status
```http
GET /api/status
```

**Response**:
```json
{
  "api_status": "operational",
  "endpoints": [
    "/health",
    "/api/status",
    "/api/models",
    "/api/chat",
    "/api/integrations",
    "/api/agents"
  ],
  "timestamp": "2025-06-11T08:27:36.175941",
  "performance": {
    "avg_response_time": "45ms",
    "requests_per_second": 150,
    "error_rate": "0.1%"
  }
}
```

---

## 🤖 **AI Models & Cost Optimization**

### List Available Models
```http
GET /api/models
```

**Response**:
```json
{
  "models": [
    {
      "id": "deepseek-r1",
      "name": "DeepSeek R1 0528",
      "type": "local_opensource",
      "priority": 1,
      "cost_per_token": 0.0,
      "status": "available",
      "capabilities": ["code", "analysis", "reasoning"],
      "max_tokens": 32768
    },
    {
      "id": "llama-3.1-70b",
      "name": "Llama 3.1 70B",
      "type": "local_commercial",
      "priority": 2,
      "cost_per_token": 0.0,
      "status": "available",
      "capabilities": ["general", "code", "analysis"],
      "max_tokens": 8192
    },
    {
      "id": "gpt-4",
      "name": "OpenAI GPT-4",
      "type": "cloud_openai",
      "priority": 3,
      "cost_per_token": 0.03,
      "status": "available",
      "capabilities": ["general", "code", "analysis", "vision"],
      "max_tokens": 8192
    }
  ],
  "cost_savings": "95%",
  "local_first": true,
  "fallback_strategy": "intelligent_priority"
}
```

### Get Model Details
```http
GET /api/models/{model_id}
```

**Response**:
```json
{
  "id": "deepseek-r1",
  "name": "DeepSeek R1 0528",
  "type": "local_opensource",
  "priority": 1,
  "cost_per_token": 0.0,
  "status": "available",
  "performance_metrics": {
    "avg_response_time": "1.2s",
    "tokens_per_second": 45,
    "accuracy_score": 94.5,
    "uptime": "99.8%"
  },
  "resource_usage": {
    "memory": "8GB",
    "gpu_utilization": "75%",
    "cpu_utilization": "25%"
  }
}
```

---

## 💬 **Chat & AI Interaction**

### Single AI Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Analyze this code for security vulnerabilities",
  "model": "deepseek-r1",
  "context": {
    "code": "function authenticate(user, pass) { return user === 'admin' && pass === 'password'; }",
    "language": "javascript"
  },
  "options": {
    "max_tokens": 1000,
    "temperature": 0.1,
    "include_reasoning": true
  }
}
```

**Response**:
```json
{
  "response": "I've identified several critical security vulnerabilities in this code:\n\n1. **Hardcoded Credentials**: The password 'password' is hardcoded...",
  "model_used": "deepseek-r1",
  "cost": 0.0,
  "local_execution": true,
  "timestamp": "2025-06-11T08:28:02.630153",
  "performance": {
    "response_time": "1.2s",
    "tokens_generated": 245,
    "reasoning_steps": 5
  },
  "security_analysis": {
    "vulnerabilities_found": 3,
    "severity": "high",
    "recommendations": ["Use environment variables", "Implement proper hashing", "Add rate limiting"]
  }
}
```

### Multi-Agent Collaboration
```http
POST /api/chat/multi-agent
Content-Type: application/json

{
  "message": "Review this pull request for code quality and security",
  "agents": ["code_reviewer", "security_analyst", "performance_expert"],
  "collaboration_mode": "consensus",
  "context": {
    "pr_url": "https://github.com/org/repo/pull/123",
    "files_changed": 5,
    "lines_added": 150,
    "lines_removed": 30
  }
}
```

**Response**:
```json
{
  "session_id": "collab_abc123",
  "collaboration_mode": "consensus",
  "agents_involved": ["code_reviewer", "security_analyst", "performance_expert"],
  "consensus_reached": true,
  "individual_responses": {
    "code_reviewer": {
      "score": 85,
      "issues": ["Missing error handling", "Inconsistent naming"],
      "suggestions": ["Add try-catch blocks", "Use camelCase consistently"]
    },
    "security_analyst": {
      "score": 78,
      "vulnerabilities": ["SQL injection risk", "Missing input validation"],
      "recommendations": ["Use parameterized queries", "Validate all inputs"]
    },
    "performance_expert": {
      "score": 92,
      "optimizations": ["Cache database queries", "Optimize loop performance"],
      "impact": "15% performance improvement expected"
    }
  },
  "final_consensus": {
    "overall_score": 85,
    "recommendation": "APPROVE_WITH_CHANGES",
    "priority_fixes": ["Security vulnerabilities", "Error handling"],
    "estimated_fix_time": "2-3 hours"
  },
  "cost_breakdown": {
    "local_execution": 0.0,
    "cloud_fallback": 0.0,
    "total_cost": 0.0,
    "savings_vs_cloud": "95%"
  }
}
```

---

## 🔗 **External Integrations**

### List Integrations
```http
GET /api/integrations
```

**Response**:
```json
{
  "integrations": [
    {
      "name": "github",
      "type": "version_control",
      "status": "active",
      "health_score": 98,
      "last_sync": "2025-06-11T08:25:00Z",
      "features": ["webhooks", "pr_analysis", "code_review"]
    },
    {
      "name": "slack",
      "type": "communication",
      "status": "active",
      "health_score": 95,
      "last_sync": "2025-06-11T08:24:30Z",
      "features": ["notifications", "interactive_commands", "file_sharing"]
    },
    {
      "name": "jira",
      "type": "project_management",
      "status": "active",
      "health_score": 92,
      "last_sync": "2025-06-11T08:23:45Z",
      "features": ["issue_creation", "status_updates", "ai_analysis"]
    }
  ],
  "enterprise_features": {
    "sso_enabled": true,
    "audit_logging": true,
    "rate_limiting": true,
    "circuit_breaker": true,
    "compliance_mode": "SOC2"
  }
}
```

### GitHub Integration
```http
POST /api/integrations/github/analyze-pr
Content-Type: application/json

{
  "repository": "org/repo",
  "pr_number": 123,
  "analysis_type": "comprehensive",
  "include_security": true,
  "include_performance": true
}
```

**Response**:
```json
{
  "pr_analysis": {
    "pr_number": 123,
    "repository": "org/repo",
    "analysis_id": "analysis_xyz789",
    "overall_score": 87,
    "security_score": 82,
    "performance_score": 91,
    "code_quality_score": 89,
    "recommendations": [
      {
        "type": "security",
        "severity": "high",
        "description": "Potential SQL injection vulnerability",
        "file": "src/database.js",
        "line": 45,
        "suggestion": "Use parameterized queries"
      },
      {
        "type": "performance",
        "severity": "medium",
        "description": "Inefficient loop detected",
        "file": "src/utils.js",
        "line": 23,
        "suggestion": "Consider using Array.map() for better performance"
      }
    ],
    "ai_comment_posted": true,
    "comment_url": "https://github.com/org/repo/pull/123#issuecomment-123456"
  }
}
```

---

## 🎯 **Agent Management**

### List Available Agents
```http
GET /api/agents
```

**Response**:
```json
{
  "agents": [
    {
      "id": "code_reviewer",
      "name": "Code Review Specialist",
      "type": "analysis",
      "status": "active",
      "capabilities": ["code_analysis", "best_practices", "refactoring"],
      "specializations": ["javascript", "python", "java", "security"],
      "performance_score": 94
    },
    {
      "id": "security_analyst",
      "name": "Security Analysis Expert",
      "type": "security",
      "status": "active",
      "capabilities": ["vulnerability_detection", "threat_analysis", "compliance"],
      "specializations": ["owasp", "penetration_testing", "encryption"],
      "performance_score": 96
    },
    {
      "id": "performance_expert",
      "name": "Performance Optimization Specialist",
      "type": "optimization",
      "status": "active",
      "capabilities": ["performance_analysis", "optimization", "monitoring"],
      "specializations": ["database", "frontend", "backend", "caching"],
      "performance_score": 92
    }
  ],
  "total_agents": 8,
  "active_agents": 8,
  "collaboration_modes": ["consensus", "parallel", "sequential", "competitive", "hierarchical"]
}
```

### Create Agent Collaboration Session
```http
POST /api/agents/collaborate
Content-Type: application/json

{
  "agents": ["code_reviewer", "security_analyst"],
  "mode": "consensus",
  "task": "analyze_code",
  "context": {
    "code": "function processPayment(amount, card) { ... }",
    "language": "javascript"
  },
  "options": {
    "timeout": 300,
    "require_consensus": true,
    "conflict_resolution": "voting"
  }
}
```

**Response**:
```json
{
  "session_id": "collab_def456",
  "status": "created",
  "agents": ["code_reviewer", "security_analyst"],
  "mode": "consensus",
  "estimated_completion": "2-3 minutes",
  "websocket_url": "ws://localhost:12001/ws/collaborate/collab_def456"
}
```

---

## 📊 **Enterprise Monitoring & Analytics**

### System Metrics
```http
GET /api/metrics
```

**Response**:
```json
{
  "system_health": {
    "overall_score": 87.5,
    "status": "EXCELLENT",
    "components": {
      "api": 95,
      "database": 90,
      "ai_models": 85,
      "integrations": 88
    }
  },
  "performance_metrics": {
    "avg_response_time": "45ms",
    "requests_per_second": 150,
    "error_rate": "0.1%",
    "uptime": "99.8%"
  },
  "cost_analytics": {
    "total_requests": 10000,
    "local_execution": 9500,
    "cloud_fallback": 500,
    "cost_savings": "95%",
    "monthly_savings": "$1,850"
  },
  "usage_analytics": {
    "top_models": ["deepseek-r1", "llama-3.1-70b"],
    "top_integrations": ["github", "slack"],
    "top_agents": ["code_reviewer", "security_analyst"]
  }
}
```

### Enterprise Health Report
```http
GET /api/enterprise/health
```

**Response**:
```json
{
  "enterprise_config": {
    "compliance_mode": "SOC2",
    "sso_enabled": true,
    "audit_logging": true,
    "rate_limiting": true,
    "encryption_at_rest": true
  },
  "integration_health": {
    "github": {
      "enabled": true,
      "circuit_breaker_status": false,
      "recent_requests": 45,
      "health_score": 98
    },
    "slack": {
      "enabled": true,
      "circuit_breaker_status": false,
      "recent_requests": 23,
      "health_score": 95
    }
  },
  "audit_summary": {
    "total_events": 1250,
    "recent_events": 45
  },
  "compliance_status": {
    "mode": "SOC2",
    "backup_retention": "90 days",
    "max_connections": 1000,
    "webhook_timeout": "30s"
  },
  "security_score": 94.29
}
```

---

## 🔒 **Security & Compliance**

### Audit Logs
```http
GET /api/audit/logs?limit=100&offset=0
Authorization: Bearer {admin_token}
```

**Response**:
```json
{
  "logs": [
    {
      "timestamp": "2025-06-11T08:27:36.175941Z",
      "event_type": "API_ACCESS",
      "user": "enterprise_user",
      "endpoint": "/api/chat",
      "ip_address": "192.168.1.100",
      "status": "success",
      "details": {
        "model_used": "deepseek-r1",
        "tokens_generated": 245,
        "cost": 0.0
      }
    },
    {
      "timestamp": "2025-06-11T08:26:15.123456Z",
      "event_type": "INTEGRATION_ACCESS",
      "integration": "github",
      "action": "pr_analysis",
      "status": "success",
      "details": {
        "repository": "org/repo",
        "pr_number": 123
      }
    }
  ],
  "total_count": 1250,
  "compliance_mode": "SOC2"
}
```

### Compliance Report
```http
GET /api/compliance/report
Authorization: Bearer {admin_token}
```

**Response**:
```json
{
  "compliance_mode": "SOC2",
  "report_date": "2025-06-11T08:27:36.175941Z",
  "overall_score": 94.29,
  "categories": {
    "access_control": {
      "score": 96,
      "status": "COMPLIANT",
      "checks": ["SSO enabled", "RBAC implemented", "Session management"]
    },
    "data_protection": {
      "score": 94,
      "status": "COMPLIANT",
      "checks": ["Encryption at rest", "Secure transmission", "Data retention"]
    },
    "audit_logging": {
      "score": 98,
      "status": "COMPLIANT",
      "checks": ["Comprehensive logging", "Log retention", "Access monitoring"]
    },
    "incident_response": {
      "score": 90,
      "status": "COMPLIANT",
      "checks": ["Monitoring systems", "Alert mechanisms", "Response procedures"]
    }
  },
  "recommendations": [
    "Implement additional backup verification",
    "Enhance incident response automation"
  ]
}
```

---

## 🚀 **WebSocket Real-time API**

### Connect to Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:12001/ws/updates');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

### Real-time Collaboration
```javascript
const collaborationWs = new WebSocket('ws://localhost:12001/ws/collaborate/session_id');

collaborationWs.onmessage = function(event) {
  const update = JSON.parse(event.data);
  // Handle collaboration updates
};
```

---

## 📈 **Rate Limits & Quotas**

| Endpoint Category | Rate Limit | Burst Limit | Enterprise Limit |
|------------------|------------|-------------|------------------|
| Health/Status | 100/min | 200/min | Unlimited |
| Chat API | 60/min | 120/min | 500/min |
| Integrations | 60/min | 100/min | 300/min |
| Agent Collaboration | 30/min | 60/min | 200/min |
| Admin/Audit | 30/min | 50/min | 100/min |

---

## 🔧 **Error Handling**

### Standard Error Response
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request is missing required parameters",
    "details": {
      "missing_fields": ["message", "model"],
      "request_id": "req_abc123"
    },
    "timestamp": "2025-06-11T08:27:36.175941Z"
  }
}
```

### Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## 🎯 **SDKs & Libraries**

### Python SDK
```python
from revoagent import ReVoAgentClient

client = ReVoAgentClient(
    base_url="http://localhost:12001",
    api_key="your_api_key"
)

# Single AI chat
response = await client.chat(
    message="Analyze this code",
    model="deepseek-r1",
    context={"code": "function example() { ... }"}
)

# Multi-agent collaboration
collaboration = await client.collaborate(
    agents=["code_reviewer", "security_analyst"],
    mode="consensus",
    task="analyze_code"
)
```

### JavaScript SDK
```javascript
import { ReVoAgentClient } from '@revoagent/sdk';

const client = new ReVoAgentClient({
  baseUrl: 'http://localhost:12001',
  apiKey: 'your_api_key'
});

// Single AI chat
const response = await client.chat({
  message: 'Analyze this code',
  model: 'deepseek-r1',
  context: { code: 'function example() { ... }' }
});

// Multi-agent collaboration
const collaboration = await client.collaborate({
  agents: ['code_reviewer', 'security_analyst'],
  mode: 'consensus',
  task: 'analyze_code'
});
```

---

## 🏆 **Enterprise Features Summary**

### ✅ **Production Ready**
- **95% Cost Savings** through intelligent local-first execution
- **Enterprise Security** with SOC2/HIPAA/GDPR compliance
- **Multi-Agent Collaboration** with 5 collaboration modes
- **Real-time Processing** with WebSocket support
- **Comprehensive Monitoring** with health metrics and alerting
- **External Integrations** with GitHub, Slack, JIRA, and more

### ✅ **Scalability & Performance**
- **Auto-scaling** Kubernetes deployment
- **Load balancing** with intelligent routing
- **Circuit breakers** for fault tolerance
- **Rate limiting** for API protection
- **Caching** for optimal performance

### ✅ **Developer Experience**
- **Comprehensive API** with RESTful design
- **Real-time WebSocket** support
- **Multiple SDKs** (Python, JavaScript, more coming)
- **Detailed Documentation** with examples
- **Interactive API Explorer** (Swagger/OpenAPI)

---

**🚀 Ready to revolutionize your AI development workflow with 95% cost savings!**

**📞 Contact**: enterprise@revoagent.com  
**📚 Documentation**: https://docs.revoagent.com  
**🔧 Support**: https://support.revoagent.com