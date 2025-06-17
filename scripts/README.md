# 🚀 reVoAgent Port Manager

Enhanced Full-Stack Workflow Setup for smooth development experience.

## 🎯 Features

- **🔧 Automated Setup**: One-command setup for frontend and backend
- **🚦 Port Management**: Intelligent port conflict resolution
- **📊 Health Monitoring**: Real-time service health checks
- **🔄 Auto-Recovery**: Automatic service restart on failures
- **📝 Comprehensive Logging**: Detailed logs for debugging
- **🧹 Cleanup Tools**: Automated cleanup of temporary files
- **⚡ Quick Commands**: Simple npm scripts for common tasks

## 🚀 Quick Start

### Development Mode (Recommended)
```bash
# Start complete development environment
npm run dev

# Or directly
./scripts/port-manager.sh dev
```

### Individual Commands
```bash
# Check service status
npm run status

# Start services
npm run start

# Stop services
npm run stop

# Restart services
npm run restart

# Health check
npm run health

# Setup dependencies
npm run setup

# Clean temporary files
npm run cleanup

# Force kill stuck processes
npm run kill-ports
```

## 📋 Available Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `dev` | Start development mode with monitoring | `npm run dev` |
| `start` | Start all services | `npm run start` |
| `stop` | Stop all services | `npm run stop` |
| `restart` | Quick restart all services | `npm run restart` |
| `status` | Check service status | `npm run status` |
| `health` | Perform health check | `npm run health` |
| `setup` | Setup frontend and backend | `npm run setup` |
| `cleanup` | Clean temporary files | `npm run cleanup` |
| `kill-ports` | Force kill processes on our ports | `npm run kill-ports` |

## 🔌 Port Configuration

| Service | Port | URL |
|---------|------|-----|
| Frontend | 12000 | https://work-1-dziuemnamvipshbv.prod-runtime.all-hands.dev |
| Backend | 8000 | http://localhost:8000 |
| Redis | 6379 | localhost:6379 |
| PostgreSQL | 5432 | localhost:5432 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |

## 🛠️ Development Workflow

### 1. Initial Setup
```bash
# Clone repository
git clone https://github.com/heinzdev20/reVoAgent.git
cd reVoAgent

# Setup everything
npm run setup
```

### 2. Start Development
```bash
# Start development environment
npm run dev
```

This will:
- ✅ Check system requirements
- ✅ Setup frontend and backend dependencies
- ✅ Start both services with proper port management
- ✅ Monitor services and auto-restart if needed
- ✅ Provide real-time status updates

### 3. Monitor Services
```bash
# Check status
npm run status

# View logs
npm run logs

# Monitor continuously
npm run monitor
```

### 4. Troubleshooting
```bash
# If services are stuck
npm run kill-ports

# Clean and restart
npm run cleanup
npm run restart

# Health check
npm run health
```

## 📊 Service Monitoring

The port manager provides comprehensive monitoring:

### Status Check
```bash
npm run status
```
Shows:
- ✅ Service status (running/stopped)
- 🌐 Access URLs
- 💾 Memory usage
- 💽 Disk usage

### Health Check
```bash
npm run health
```
Performs:
- 🔍 HTTP endpoint checks
- 📡 API response validation
- ⚡ Performance metrics
- 🚨 Error detection

### Logs
```bash
# View all logs
npm run logs

# View specific service logs
tail -f logs/frontend.log
tail -f logs/backend.log
tail -f logs/port-manager.log
```

## 🔧 Configuration

### Environment Variables
Create `.env` file in project root:
```bash
# Port configuration
FRONTEND_PORT=12000
BACKEND_PORT=8000
REDIS_PORT=6379
POSTGRES_PORT=5432

# Development settings
NODE_ENV=development
DEBUG=true

# API settings
API_BASE_URL=http://localhost:8000
```

### Custom Port Configuration
Edit `scripts/port-manager.sh`:
```bash
# Configuration section
FRONTEND_PORT=12000
BACKEND_PORT=8000
# ... other ports
```

## 🐳 Docker Support

### Build and Run
```bash
# Build containers
npm run docker:build

# Start services
npm run docker:up

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

### Docker Compose
The port manager works seamlessly with Docker Compose for production deployments.

## 🚨 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Solution 1: Kill processes on ports
npm run kill-ports

# Solution 2: Find and kill specific process
lsof -ti:12000 | xargs kill -9
```

#### Services Won't Start
```bash
# Check system requirements
./scripts/port-manager.sh help

# Clean and setup
npm run cleanup
npm run setup
npm run start
```

#### Frontend Build Issues
```bash
# Clean frontend
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

#### Backend Issues
```bash
# Check Python environment
cd backend
python3 --version
pip list

# Reinstall dependencies
pip install -r requirements.txt
```

### Debug Mode
Enable debug logging:
```bash
# Set debug mode
export DEBUG=true

# Run with verbose output
./scripts/port-manager.sh dev
```

## 📝 Logs

All logs are stored in `logs/` directory:
- `port-manager.log` - Port manager operations
- `frontend.log` - Frontend service logs
- `backend.log` - Backend service logs

### Log Rotation
Logs older than 7 days are automatically cleaned during cleanup.

## 🔄 Auto-Recovery

Development mode includes automatic service recovery:
- 🔍 Monitors services every 30 seconds
- 🚨 Detects service failures
- 🔄 Automatically restarts failed services
- 📝 Logs recovery actions

## 🎯 Best Practices

### Development
1. Always use `npm run dev` for development
2. Check `npm run status` before starting work
3. Use `npm run health` to verify everything is working
4. Run `npm run cleanup` periodically

### Production
1. Use Docker containers for production
2. Monitor logs regularly
3. Set up proper environment variables
4. Use reverse proxy for frontend

### Debugging
1. Check logs first: `npm run logs`
2. Verify ports: `npm run status`
3. Test health: `npm run health`
4. Clean if needed: `npm run cleanup`

## 🤝 Contributing

1. Test your changes with the port manager
2. Ensure all services start correctly
3. Verify health checks pass
4. Update documentation if needed

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review logs in `logs/` directory
3. Run health check: `npm run health`
4. Create an issue with log output

---

**Happy Coding! 🚀**