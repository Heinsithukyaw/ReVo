# reVoAgent Repository Microagent

## 🚨 QUICK REFERENCE: Port Management (CRITICAL)

**ALWAYS run before starting full stack to avoid sticking issues:**
```bash
# 1. Clean ports (MANDATORY)
./scripts/cleanup_ports.sh
sleep 3

# 2. Start backend first
python simple_backend_server.py &
sleep 5

# 3. Start frontend
cd frontend && npm run dev
```

**Emergency Recovery:**
```bash
pkill -f "python.*simple_backend_server"
pkill -f "npm.*dev"
./scripts/cleanup_ports.sh
sleep 5
```

---

## Repository Overview

**reVoAgent** is a revolutionary AI platform featuring the world's first three-engine architecture that combines memory, parallel processing, and creative innovation. This is a comprehensive multi-agent AI system designed for enterprise-grade development workflows with 100% cost optimization through local model processing.

## Key Features

### 🧠 Three-Engine Architecture
- **Perfect Recall Engine**: Persistent memory system with unlimited storage and 99.9% accuracy
- **Parallel Mind Engine**: Intelligent multi-processing with 8 active workers and 10x performance boost
- **Creative Engine**: AI-powered innovation generator with 94% novelty score

### 🤖 Multi-Agent System
- 20+ memory-enabled agents with persistent learning capabilities
- Code Analysis Agent, Debug Detective Agent, Workflow Manager, Knowledge Coordinator
- Real-time multi-agent collaboration with shared memory context

### 💰 Cost Optimization
- 100% cost savings through local model processing
- DeepSeek R1, Llama 3.1 70B running locally at $0.00 per request
- Enterprise ROI of 95%+ cost reduction

### 🛡️ Enterprise Security
- JWT Authentication with RBAC authorization
- Container and Kubernetes security hardening
- 94.29/100 security score with comprehensive audit logging

## Project Structure

```
reVoAgent/
├── apps/                    # Application modules
│   ├── api/                # REST API endpoints
│   ├── backend/            # Backend services
│   ├── cli/                # Command-line interface
│   └── web/                # Web interface
├── packages/               # Core packages
│   ├── agents/             # AI agent implementations
│   ├── engines/            # Three-engine architecture
│   ├── memory/             # Memory system (Cognee integration)
│   ├── integrations/       # External service integrations
│   └── monitoring/         # Performance monitoring
├── frontend/               # React/TypeScript frontend
├── deployment/             # Docker and Kubernetes configs
├── config/                 # Configuration files
├── docs/                   # Documentation
└── tests/                  # Comprehensive test suite
```

## How to Run the Code

### Quick Start (Recommended)

1. **Clone and Setup**:
```bash
git clone https://github.com/Heinzdev18/reVoAgent.git
cd reVoAgent
git checkout final_reVoAgent
```

2. **Automated Setup**:
```bash
python setup_memory_integration.py
```

3. **Access the Platform**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Memory API: http://localhost:8000/api/memory/stats

### Development Setup (Port-Safe Method)

1. **Install Dependencies**:
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

2. **🚨 CRITICAL: Clean Ports First (MANDATORY)**:
```bash
# ALWAYS run this before starting any services
./scripts/cleanup_ports.sh
# Or manual: lsof -ti:12000,12001,8000 | xargs kill -9 2>/dev/null || true
sleep 3
```

3. **Start Backend (Port 12001)**:
```bash
python simple_backend_server.py &
sleep 5
# Verify: curl http://localhost:12001/health
```

4. **Start Frontend (Port 12000)** (same or new terminal):
```bash
cd frontend && npm run dev
# Runs on http://localhost:12000
# Verify: curl http://localhost:12000
```

### ⚠️ **IMPORTANT: If Full Stack Gets Stuck**
```bash
# Emergency recovery sequence:
pkill -f "python.*simple_backend_server"
pkill -f "npm.*dev"
./scripts/cleanup_ports.sh
sleep 5
# Then restart following the sequence above
```

### Docker Deployment

1. **Production Deployment**:
```bash
docker-compose -f docker-compose.production.yml up -d
```

2. **Memory-Enabled Deployment**:
```bash
docker-compose -f docker-compose.memory.yml up -d
```

3. **Three-Engine System**:
```bash
docker-compose -f docker-compose.three-engine.yml up -d
```

### Kubernetes Production

```bash
kubectl apply -f k8s/production/
kubectl get services revoagent-frontend
```

## Key Scripts and Entry Points

### Main Entry Points
- `main.py` - Primary application entry point
- `simple_backend_server.py` - Simplified backend for development
- `start_enhanced_system.py` - Enhanced three-engine system startup
- `setup_memory_integration.py` - Automated memory system setup

### Development Scripts
- `scripts/setup_environment.py` - Environment configuration
- `scripts/start_fullstack.sh` - Full-stack development startup
- `scripts/quick_setup.sh` - Quick development setup

### Testing and Validation
- `test_critical_fixes.py` - Critical functionality validation
- `system_health_check.py` - System health monitoring
- `test_phase4_final_validation.py` - Comprehensive system testing

## API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `GET /api/models` - Available AI models
- `POST /api/chat` - Chat with agents
- `POST /api/chat/multi-agent` - Multi-agent collaboration

### Memory System
- `POST /api/chat/memory-enabled` - Memory-enhanced chat
- `GET /api/memory/stats` - Memory system statistics
- `WS /api/memory/ws/{session_id}` - Real-time memory WebSocket

### External Integrations
- `POST /api/integrations/github/repos/{owner}/{repo}/pulls` - GitHub PR creation
- `POST /api/integrations/slack/notify` - Slack notifications
- `POST /api/integrations/jira/issues` - JIRA issue creation

## Configuration

### Environment Variables
- `REVOAGENT_MODE` - Operation mode (development/production/demo/minimal)
- `GITHUB_TOKEN` - GitHub integration token
- `SLACK_TOKEN` - Slack integration token
- `JIRA_TOKEN` - JIRA integration token

### Configuration Files
- `config/base.yaml` - Base configuration
- `config/production.yaml` - Production settings
- `config/engines.yaml` - Three-engine configuration
- `config/agents.yaml` - Agent configurations

## Performance Metrics

- **Startup Success Rate**: 100%
- **API Response Time**: ~50ms average
- **Memory Response Time**: <100ms for context retrieval
- **Concurrent Operations**: 100+ simultaneous memory queries
- **Throughput**: 150+ requests/minute
- **Uptime Capability**: 99.9%

## Testing

### Run All Tests
```bash
python test_phase_completion_final.py
```

### Specific Test Suites
```bash
python test_critical_fixes.py           # Critical functionality
python system_health_check.py           # System health
python test_phase4_final_validation.py  # Comprehensive validation
```

### Expected Results
- 100% test success rate
- All critical fixes validated
- Memory system operational
- Three-engine coordination functional

## ⚠️ CRITICAL: Full Stack Port Management Issues

### 🚨 **KNOWN ISSUE: Full Stack Sticking Problem**
When running the full stack, the system frequently gets stuck due to port conflicts and improper port management. This is a **critical known issue** that requires careful port handling.

### 🔧 **Port Management Strategy (ESSENTIAL)**

#### **Standard Port Configuration**
- **Frontend**: Port 12000 (Vite dev server)
- **Backend**: Port 12001 (FastAPI server)
- **Memory System**: Port 8000 (Memory API)
- **Three-Engine System**: Port 12000 (Engine coordination)
- **WebSocket**: Uses same ports as respective services

#### **Pre-Startup Port Cleanup (MANDATORY)**
```bash
# ALWAYS run this before starting full stack
./scripts/cleanup_ports.sh

# Or manual cleanup:
lsof -ti:12000,12001,8000 | xargs kill -9 2>/dev/null || true
```

#### **Safe Full Stack Startup Sequence**
```bash
# 1. Clean all ports first (CRITICAL)
./scripts/cleanup_ports.sh

# 2. Wait for ports to be fully released
sleep 3

# 3. Start backend first (port 12001)
python simple_backend_server.py &
sleep 5

# 4. Verify backend is running
curl http://localhost:12001/health

# 5. Start frontend (port 12000)
cd frontend && npm run dev &

# 6. Wait and verify both services
sleep 5
curl http://localhost:12000
```

#### **Docker Full Stack (Recommended for Stability)**
```bash
# Clean any existing containers
docker-compose down --remove-orphans
docker system prune -f

# Start with proper port mapping
docker-compose -f docker-compose.production.yml up -d

# Verify services
docker-compose ps
```

### **Port Conflict Detection and Resolution**

#### **Check Port Usage Before Starting**
```bash
# Check if ports are in use
netstat -tulpn | grep -E ':(12000|12001|8000)'

# Kill specific port processes
kill -9 $(lsof -t -i:12000) 2>/dev/null || true
kill -9 $(lsof -t -i:12001) 2>/dev/null || true
kill -9 $(lsof -t -i:8000) 2>/dev/null || true
```

#### **Automated Port Management Script**
```bash
# Use the port manager for safe startup
python scripts/port_manager.py --cleanup --start-fullstack
```

### **Full Stack Sticking Symptoms and Solutions**

#### **Symptom 1: Frontend Won't Connect to Backend**
```bash
# Solution:
1. Check backend is actually running: curl http://localhost:12001/health
2. Verify CORS configuration in backend
3. Check browser console for connection errors
4. Restart backend with proper port binding
```

#### **Symptom 2: Services Start But Become Unresponsive**
```bash
# Solution:
1. Check for port conflicts: netstat -tulpn | grep -E ':(12000|12001)'
2. Monitor resource usage: htop or docker stats
3. Check logs for memory/CPU issues
4. Restart with resource limits: docker-compose up --scale backend=1
```

#### **Symptom 3: WebSocket Connections Fail**
```bash
# Solution:
1. Verify WebSocket endpoint: ws://localhost:12001/ws/dashboard
2. Check firewall/proxy settings
3. Test with simple WebSocket client
4. Restart with WebSocket debugging enabled
```

### **Emergency Recovery Procedures**

#### **Complete System Reset**
```bash
# Nuclear option - clean everything
pkill -f "python.*simple_backend_server"
pkill -f "npm.*dev"
docker-compose down --remove-orphans
docker system prune -f
./scripts/cleanup_ports.sh
sleep 10
# Then restart following safe sequence above
```

#### **Graceful Recovery**
```bash
# Gentle restart
./scripts/stop_fullstack.sh
sleep 5
./scripts/cleanup_ports.sh
sleep 3
./scripts/start_fullstack.sh
```

## Troubleshooting

### Common Issues
1. **🚨 CRITICAL - Port Conflicts**: ALWAYS use `scripts/cleanup_ports.sh` before starting
2. **Full Stack Sticking**: Follow the port management strategy above
3. **Memory Issues**: Check `docker-compose.memory.yml` configuration
4. **Frontend Build**: Clear `node_modules` and reinstall dependencies
5. **Backend Startup**: Verify Python dependencies and port availability
6. **WebSocket Failures**: Check port binding and CORS configuration

### Health Checks
- Backend: `curl http://localhost:12001/health`
- Memory System: `curl http://localhost:8000/api/memory/health`
- Three-Engine Status: `curl http://localhost:12000/engines/status`
- Port Status: `netstat -tulpn | grep -E ':(12000|12001|8000)'`

## Development Workflow

1. **Make Changes**: Edit files in respective directories
2. **Test Changes**: Run `python test_critical_fixes.py`
3. **Validate System**: Run `python system_health_check.py`
4. **Deploy**: Use appropriate Docker Compose configuration

## External Dependencies

### AI Models (Local)
- DeepSeek R1 0528
- Llama 3.1 70B
- Sentence Transformers for embeddings

### Databases
- PostgreSQL (memory storage)
- LanceDB (vector database)
- Redis (caching)

### External Services
- GitHub API
- Slack API
- JIRA API
- Cognee (memory integration)

## Security Considerations

- All API keys should be stored in environment variables
- JWT tokens for authentication
- Container security hardening applied
- Network isolation in Kubernetes deployments
- Comprehensive audit logging enabled

This microagent description provides OpenHands with comprehensive knowledge about the reVoAgent repository structure, how to run the code, key features, and development workflows.