# reVoAgent Enhanced System - Quick Reference

## 🚀 Quick Start Commands

```bash
# Start the enhanced full stack system
./start_fullstack_enhanced.sh

# Stop the enhanced full stack system  
./stop_fullstack_enhanced.sh

# Check system status
python3 scripts/advanced_process_manager.py --status

# Run comprehensive tests
python3 test_enhanced_system.py
```

## 🔧 Process Management

```bash
# Start specific services
python3 scripts/advanced_process_manager.py --start backend frontend

# Stop specific services
python3 scripts/advanced_process_manager.py --stop backend frontend

# Restart services
python3 scripts/advanced_process_manager.py --restart backend

# Monitor services in real-time
python3 scripts/advanced_process_manager.py --monitor
```

## 🧹 Cleanup & Troubleshooting

```bash
# Clean up all processes and ports
python3 scripts/advanced_process_manager.py --cleanup

# Force stop everything
./stop_fullstack_enhanced.sh --force

# Check for zombie processes
ps aux | awk '$8 ~ /^Z/ { print $2, $11 }'

# Scan port usage
python3 scripts/advanced_process_manager.py --scan
```

## 📊 Health Checks

```bash
# Backend health
curl http://localhost:12001/health

# Frontend health
curl http://localhost:12000

# System metrics
curl http://localhost:12001/api/system/metrics

# API documentation
open http://localhost:12001/docs
```

## 🔍 Debugging

```bash
# View logs
tail -f logs/startup.log
tail -f logs/backend.log
tail -f logs/process_manager.log

# Check test results
cat logs/enhanced_system_test_results.json

# Get detailed status with JSON
python3 scripts/advanced_process_manager.py --status --json
```

## ⚙️ Configuration Files

- `config/process_manager_config.json` - Process manager settings
- `.env.development` - Environment variables
- `port_config.json` - Port assignments
- `logs/` - All log files

## 🆘 Emergency Recovery

```bash
# If everything is broken:
1. ./stop_fullstack_enhanced.sh --force
2. python3 scripts/advanced_process_manager.py --cleanup
3. rm -f logs/*.pid
4. ./start_fullstack_enhanced.sh

# If ports are stuck:
1. python3 scripts/advanced_process_manager.py --scan
2. python3 scripts/advanced_process_manager.py --cleanup
3. ./start_fullstack_enhanced.sh --cleanup

# If zombies accumulate:
1. python3 scripts/advanced_process_manager.py --cleanup
2. ps aux | awk '$8 ~ /^Z/ { print $2, $11 }'
```

## 📈 Key Features

✅ **Zero zombie processes** - Automatic cleanup every 60 seconds  
✅ **Zero port conflicts** - Intelligent resolution and migration  
✅ **Graceful shutdown** - Proper signal handling (SIGTERM/SIGINT)  
✅ **Auto-restart** - Services restart on failure (up to 3 attempts)  
✅ **Real-time monitoring** - Continuous health checks  
✅ **Comprehensive logging** - Full audit trail in logs/  
✅ **Easy troubleshooting** - Clear error messages and recovery  

## 🎯 Default Ports

- **Backend**: 12001 (alternatives: 8000, 8001, 8002)
- **Frontend**: 12000 (alternatives: 3000, 3001, 3002)  
- **Memory API**: 8001 (alternatives: 8002, 8003, 8004)
- **Three Engine**: 8002 (alternatives: 8003, 8004, 8005)

---
**Need help? Check `ENHANCED_SYSTEM_SUMMARY.md` for detailed documentation!**