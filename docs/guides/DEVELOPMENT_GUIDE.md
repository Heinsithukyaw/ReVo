# reVoAgent Development Guide

## Avoiding Port Conflicts

Port conflicts are a common issue in development environments. This guide provides multiple strategies to avoid them.

## Quick Start (Recommended)

### Option 1: Use Our Smart Scripts

```bash
# Clean up any existing processes
./scripts/cleanup_ports.sh

# Start the full stack (handles port conflicts automatically)
./scripts/start_fullstack.sh

# Stop the full stack
./scripts/stop_fullstack.sh
```

### Option 2: Use Docker (Isolated Environment)

```bash
# Start with Docker (completely isolated)
docker-compose -f docker-compose.dev.yml up

# Stop with Docker
docker-compose -f docker-compose.dev.yml down
```

## Port Management Tools

### Check Port Status
```bash
# Check all default ports
python scripts/port_manager.py --check

# Check specific port
python scripts/port_manager.py --port 12001

# Get suggestions for alternative ports
python scripts/port_manager.py --suggest

# Find next free port starting from 12000
python scripts/port_manager.py --find-free 12000
```

### Manual Port Management
```bash
# Check what's using a port (if available)
lsof -i :12001
netstat -tulpn | grep :12001
ss -tulpn | grep :12001

# Kill process using a port
fuser -k 12001/tcp
```

## Why Port Conflicts Happen

1. **Background Processes**: Previous runs didn't clean up properly
2. **Multiple Terminals**: Running the same services in different terminals
3. **System Services**: Other applications using the same ports
4. **Development Tools**: Hot reload servers, debuggers, etc.
5. **Container Conflicts**: Docker containers holding ports

## Prevention Strategies

### 1. Always Clean Up Before Starting
```bash
# Our cleanup script handles this
./scripts/cleanup_ports.sh
```

### 2. Use Process Management
```bash
# Our scripts save PIDs for proper cleanup
cat logs/backend.pid
cat logs/frontend.pid
```

### 3. Use Strict Port Configuration
```typescript
// In vite.config.ts
server: {
  port: 12000,
  strictPort: true, // Fail instead of finding alternative ports
}
```

### 4. Environment-Specific Ports
```bash
# Development
BACKEND_PORT=12001
FRONTEND_PORT=12000

# Testing
BACKEND_PORT=13001
FRONTEND_PORT=13000

# Production
BACKEND_PORT=8001
FRONTEND_PORT=8000
```

## Troubleshooting Port Conflicts

### Problem: "Port already in use"
```bash
# Solution 1: Clean up
./scripts/cleanup_ports.sh

# Solution 2: Find what's using the port
python scripts/port_manager.py --port 12001

# Solution 3: Use alternative ports
python scripts/port_manager.py --suggest
```

### Problem: Multiple processes running
```bash
# Check running processes
ps aux | grep -E "(python.*main.py|npm.*dev|vite)"

# Kill specific processes
pkill -f "python.*apps/backend/main.py"
pkill -f "npm.*dev"
```

### Problem: Zombie processes
```bash
# Force cleanup
./scripts/cleanup_ports.sh

# Or restart your terminal/container
```

## Best Practices

### 1. Use Our Scripts
- Always use `./scripts/start_fullstack.sh` instead of manual startup
- Use `./scripts/stop_fullstack.sh` to properly stop services
- Run `./scripts/cleanup_ports.sh` if you encounter issues

### 2. Check Logs
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log
```

### 3. Monitor Resources
```bash
# Check port status
python scripts/port_manager.py --check

# Check system resources
htop
free -h
df -h
```

### 4. Use Docker for Isolation
```bash
# Complete isolation with Docker
docker-compose -f docker-compose.dev.yml up

# No port conflicts with host system
# Easy cleanup: docker-compose down
```

## Configuration Files

### Backend Port Configuration
```python
# apps/backend/main.py
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("BACKEND_PORT", 12001)),
        reload=False,
        log_level="info"
    )
```

### Frontend Port Configuration
```typescript
// frontend/vite.config.ts
server: {
  port: parseInt(process.env.FRONTEND_PORT || '12000'),
  strictPort: true,
  host: true,
}
```

### Environment Variables
```bash
# .env file
BACKEND_PORT=12001
FRONTEND_PORT=12000
REDIS_PORT=6379
```

## Advanced Solutions

### 1. Port Ranges
```bash
# Use port ranges for different environments
# Dev: 12000-12099
# Test: 12100-12199
# Staging: 12200-12299
```

### 2. Dynamic Port Assignment
```python
# Automatically find free ports
def find_free_port(start=12000):
    for port in range(start, start + 100):
        if is_port_free(port):
            return port
    raise Exception("No free ports found")
```

### 3. Service Discovery
```bash
# Use service discovery instead of hardcoded ports
# Consul, etcd, or simple file-based discovery
```

## Emergency Recovery

If everything fails:

```bash
# Nuclear option: kill everything
sudo pkill -f python
sudo pkill -f node
sudo pkill -f npm

# Clean up Docker
docker-compose down --remove-orphans
docker system prune -f

# Restart terminal/shell
exec $SHELL

# Start fresh
./scripts/start_fullstack.sh
```

## Summary

The key to avoiding port conflicts:

1. **Always use our scripts** - They handle cleanup automatically
2. **Check ports before starting** - Use our port manager
3. **Clean up properly** - Don't leave zombie processes
4. **Use Docker for isolation** - When you need guaranteed clean environment
5. **Monitor and log** - Keep track of what's running

With these tools and practices, you should never have port conflicts again!