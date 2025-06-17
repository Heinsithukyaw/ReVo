#!/bin/bash

# reVoAgent Port Cleanup Script - CRITICAL for avoiding port conflicts
# This script MUST be run before starting any services

set -e

echo "🧹 reVoAgent Port Cleanup - Starting..."

# Check if enhanced port manager is available
ENHANCED_PORT_MANAGER="/workspace/reVoAgent/scripts/enhanced_port_manager.py"

if [ -f "$ENHANCED_PORT_MANAGER" ]; then
    echo "🔧 Using Enhanced Port Manager for cleanup..."
    
    # Use the enhanced port manager for intelligent cleanup
    python3 "$ENHANCED_PORT_MANAGER" --cleanup --json > /tmp/cleanup_result.json 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Enhanced cleanup completed successfully"
        
        # Show results if available
        if [ -f /tmp/cleanup_result.json ]; then
            python3 -c "
import json
try:
    with open('/tmp/cleanup_result.json', 'r') as f:
        result = json.load(f)
    for port, status in result.items():
        print(f'   Port {port}: {status}')
except:
    pass
"
            rm -f /tmp/cleanup_result.json
        fi
        
        # Verify with port scan
        echo "🔍 Verifying cleanup with port scan..."
        python3 "$ENHANCED_PORT_MANAGER" --scan | grep -E "(FREE|IN USE)" | head -5
        
        exit 0
    else
        echo "⚠️  Enhanced cleanup failed, falling back to basic cleanup..."
    fi
fi

echo "🔧 Using basic cleanup method..."

# Function to kill processes by pattern
kill_processes() {
    local pattern=$1
    local description=$2
    
    echo "🔍 Looking for $description processes..."
    pids=$(ps aux | grep "$pattern" | grep -v grep | awk '{print $2}')
    
    if [ -n "$pids" ]; then
        echo "🛑 Killing $description processes: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        echo "✅ No $description processes found"
    fi
}

# Enhanced process patterns for reVoAgent
echo "🔍 Searching for reVoAgent processes..."

# Backend processes
kill_processes "python.*simple_backend_server" "simple backend server"
kill_processes "python.*apps/backend/main" "backend main"
kill_processes "uvicorn.*main:app" "uvicorn backend"
kill_processes "python.*main.py.*8000" "backend on port 8000"
kill_processes "python.*main.py.*12001" "backend on port 12001"

# Frontend processes
kill_processes "npm.*dev" "npm dev"
kill_processes "vite.*--port" "vite frontend"
kill_processes "node.*vite" "vite node processes"

# Three-engine processes
kill_processes "python.*three_engine" "three engine"
kill_processes "python.*start_three_engine" "three engine starter"

# Memory API processes
kill_processes "python.*memory.*api" "memory API"
kill_processes "python.*cognee" "cognee memory"

# WebSocket processes
kill_processes "python.*websocket" "websocket server"

# Kill any processes using our target ports
echo "🔍 Cleaning up ports..."
for port in 8000 8001 8002 8080 12000 12001 12002 12003 14000 14001; do
    echo "   Checking port $port..."
    
    if command -v fuser >/dev/null 2>&1; then
        fuser -k $port/tcp 2>/dev/null || true
    elif command -v lsof >/dev/null 2>&1; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    else
        # Fallback: Python-based port check and cleanup
        python3 -c "
import socket
import psutil
import sys

port = $port
try:
    # Find processes using the port
    for conn in psutil.net_connections():
        if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
            try:
                proc = psutil.Process(conn.pid)
                print(f'Killing process {conn.pid} ({proc.name()}) on port {port}')
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
except Exception as e:
    pass
" 2>/dev/null
    fi
done

echo "⏳ Waiting for processes to terminate..."
sleep 3

# Enhanced port verification
echo "🔍 Verifying ports are free..."
python3 -c "
import socket
import sys

def check_port(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.bind(('localhost', port))
        sock.close()
        return True
    except OSError:
        return False

# Check all reVoAgent ports
ports = [8000, 8001, 8002, 8080, 12000, 12001, 14000]
free_ports = []
occupied_ports = []

for port in ports:
    if check_port(port):
        free_ports.append(port)
        print(f'✅ Port {port}: FREE')
    else:
        occupied_ports.append(port)
        print(f'❌ Port {port}: STILL IN USE')

print()
if not occupied_ports:
    print('🎉 All reVoAgent ports are now free!')
    sys.exit(0)
else:
    print(f'⚠️  {len(occupied_ports)} ports still in use: {occupied_ports}')
    print('   You may need to restart your terminal or check for external processes.')
    sys.exit(1)
"

cleanup_exit_code=$?

# Additional cleanup for stubborn processes
if [ $cleanup_exit_code -ne 0 ]; then
    echo "🔧 Performing additional cleanup..."
    
    # Kill any remaining Python processes that might be reVoAgent related
    pkill -f "python.*revoagent" 2>/dev/null || true
    pkill -f "python.*simple_backend" 2>/dev/null || true
    pkill -f "npm.*dev.*reVoAgent" 2>/dev/null || true
    
    # Wait and check again
    sleep 2
    
    echo "🔍 Final verification..."
    python3 -c "
import socket

ports = [8000, 12000, 14000]
all_clear = True

for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.close()
        print(f'✅ Port {port}: FREE')
    except OSError:
        print(f'❌ Port {port}: STILL IN USE')
        all_clear = False

if all_clear:
    print('🎉 Critical ports are now free!')
else:
    print('⚠️  Some critical ports are still occupied.')
"
fi

echo "✅ Cleanup complete!"
echo "💡 For advanced port management, use: python3 scripts/enhanced_port_manager.py"