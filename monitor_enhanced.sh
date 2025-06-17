#!/bin/bash

# Enhanced System Monitor for reVoAgent
echo "📊 reVoAgent Enhanced System Monitor"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a process is running
check_process() {
    local process_name=$1
    local display_name=$2
    
    if pgrep -f "$process_name" > /dev/null; then
        local pid=$(pgrep -f "$process_name" | head -1)
        local memory=$(ps -p $pid -o rss= 2>/dev/null | awk '{print $1/1024}' 2>/dev/null || echo "0")
        log_success "$display_name: Running (PID: $pid, Memory: ${memory}MB)"
        return 0
    else
        log_error "$display_name: Not running"
        return 1
    fi
}

# Function to check port availability
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        local pid=$(lsof -t -i :$port | head -1)
        log_success "$service: Port $port is active (PID: $pid)"
        return 0
    else
        log_warning "$service: Port $port is not in use"
        return 1
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local timeout=${3:-5}
    
    if command -v curl >/dev/null 2>&1; then
        local response=$(curl -s -w "%{http_code}" -m $timeout "$url" -o /dev/null 2>/dev/null)
        if [ "$response" = "200" ]; then
            log_success "$name: HTTP 200 OK"
            return 0
        else
            log_warning "$name: HTTP $response"
            return 1
        fi
    else
        log_warning "$name: curl not available for testing"
        return 1
    fi
}

# Function to get system resources
get_system_resources() {
    echo -e "\n${PURPLE}🖥️  System Resources:${NC}"
    
    # CPU Usage
    if command -v top >/dev/null 2>&1; then
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' 2>/dev/null || echo "unknown")
        echo "   CPU Usage: ${cpu_usage}%"
    fi
    
    # Memory Usage
    if command -v free >/dev/null 2>&1; then
        local mem_info=$(free -h | awk 'NR==2{printf "Used: %s/%s (%.2f%%)", $3,$2,$3*100/$2}')
        echo "   Memory: $mem_info"
    fi
    
    # Disk Usage
    if command -v df >/dev/null 2>&1; then
        local disk_usage=$(df -h . | awk 'NR==2{print $5}')
        echo "   Disk Usage: $disk_usage (current directory)"
    fi
    
    # Load Average
    if [ -f /proc/loadavg ]; then
        local load_avg=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
        echo "   Load Average: $load_avg"
    fi
}

# Function to check LLM status
check_llm_status() {
    echo -e "\n${CYAN}🤖 LLM Status:${NC}"
    
    if test_endpoint "http://localhost:12001/api/config/llm" "LLM Config" 3; then
        if command -v curl >/dev/null 2>&1; then
            local llm_config=$(curl -s http://localhost:12001/api/config/llm 2>/dev/null)
            if [ $? -eq 0 ] && [ ! -z "$llm_config" ]; then
                echo "   Default Model: $(echo $llm_config | grep -o '"default_model":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo 'unknown')"
                echo "   Providers: $(echo $llm_config | grep -o '"available_providers":\[[^]]*\]' | grep -o '"[^"]*"' | wc -l 2>/dev/null || echo 'unknown')"
                
                # Check if API keys are configured
                local has_deepseek=$(echo $llm_config | grep -q "deepseek" && echo "✓" || echo "✗")
                local has_openai=$(echo $llm_config | grep -q "openai" && echo "✓" || echo "✗")
                local has_anthropic=$(echo $llm_config | grep -q "anthropic" && echo "✓" || echo "✗")
                
                echo "   API Keys: DeepSeek($has_deepseek) OpenAI($has_openai) Anthropic($has_anthropic)"
            fi
        fi
    else
        log_warning "LLM configuration endpoint not accessible"
    fi
}

# Function to check recent logs
check_logs() {
    echo -e "\n${PURPLE}📋 Recent Logs:${NC}"
    
    if [ -f logs/revoagent.log ]; then
        echo "   Log file: logs/revoagent.log"
        local log_size=$(du -h logs/revoagent.log | cut -f1)
        echo "   Size: $log_size"
        
        echo "   Last 5 entries:"
        tail -5 logs/revoagent.log | while read line; do
            echo "     $line"
        done
        
        # Check for recent errors
        local error_count=$(tail -100 logs/revoagent.log | grep -i error | wc -l)
        if [ $error_count -gt 0 ]; then
            log_warning "Found $error_count recent errors in logs"
        else
            log_success "No recent errors in logs"
        fi
    else
        log_warning "No log file found at logs/revoagent.log"
    fi
}

# Function to check configuration
check_config() {
    echo -e "\n${CYAN}⚙️  Configuration:${NC}"
    
    # Check .env file
    if [ -f .env ]; then
        log_success ".env file exists"
        local api_key_count=$(grep -c "API_KEY=.*[^[:space:]]" .env 2>/dev/null || echo 0)
        echo "   API Keys configured: $api_key_count"
        
        # Check specific keys (without revealing values)
        local keys=("DEEPSEEK_API_KEY" "OPENAI_API_KEY" "ANTHROPIC_API_KEY" "GEMINI_API_KEY")
        for key in "${keys[@]}"; do
            if grep -q "^${key}=.*[^[:space:]]" .env 2>/dev/null; then
                echo "   ✓ $key: Configured"
            else
                echo "   ✗ $key: Not configured"
            fi
        done
    else
        log_error ".env file missing"
        echo "   Create from template: cp .env.example .env"
    fi
    
    # Check configuration files
    if [ -f config/environment.yaml ]; then
        log_success "environment.yaml exists"
    else
        log_warning "environment.yaml missing"
    fi
    
    if [ -f config/ports.yaml ]; then
        log_success "ports.yaml exists"
    else
        log_warning "ports.yaml missing"
    fi
}

# Function to check network connectivity
check_network() {
    echo -e "\n${BLUE}🌐 Network Connectivity:${NC}"
    
    # Check if we can reach external APIs (basic connectivity test)
    local endpoints=("https://api.openai.com" "https://api.anthropic.com" "https://api.deepseek.com")
    local reachable=0
    
    for endpoint in "${endpoints[@]}"; do
        if command -v curl >/dev/null 2>&1; then
            if curl -s --connect-timeout 3 --max-time 5 "$endpoint" >/dev/null 2>&1; then
                echo "   ✓ $(echo $endpoint | cut -d'/' -f3): Reachable"
                ((reachable++))
            else
                echo "   ✗ $(echo $endpoint | cut -d'/' -f3): Not reachable"
            fi
        fi
    done
    
    if [ $reachable -gt 0 ]; then
        log_success "External API connectivity: $reachable/3 endpoints reachable"
    else
        log_warning "No external API endpoints reachable (check internet connection)"
    fi
}

# Function to perform health checks
check_health() {
    echo -e "\n${GREEN}🏥 Health Checks:${NC}"
    
    # Test health endpoint
    if test_endpoint "http://localhost:12001/health" "Backend Health" 5; then
        if command -v curl >/dev/null 2>&1; then
            local health_data=$(curl -s http://localhost:12001/health 2>/dev/null)
            if [ $? -eq 0 ] && [ ! -z "$health_data" ]; then
                echo "   Status: $(echo $health_data | grep -o '"status":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo 'unknown')"
                echo "   Version: $(echo $health_data | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo 'unknown')"
                echo "   Uptime: $(echo $health_data | grep -o '"uptime":[0-9.]*' | cut -d':' -f2 2>/dev/null || echo 'unknown')s"
            fi
        fi
    fi
    
    # Test readiness probe
    test_endpoint "http://localhost:12001/health/ready" "Readiness Probe" 3
    
    # Test frontend
    test_endpoint "http://localhost:12000" "Frontend" 3
}

# Function to monitor in real-time
monitor_realtime() {
    local interval=${1:-30}
    
    echo -e "\n${PURPLE}🔄 Starting real-time monitoring (refresh every ${interval}s)${NC}"
    echo "Press Ctrl+C to stop..."
    
    while true; do
        clear
        echo "📊 reVoAgent Enhanced System Monitor - $(date)"
        echo "================================================"
        
        # Quick status
        echo -e "\n${CYAN}⚡ Quick Status:${NC}"
        check_process "enhanced_backend_main.py\|backend_main.py" "Backend"
        check_process "frontend.*dev\|vite\|npm.*run.*dev" "Frontend"
        check_port 12001 "Backend API"
        check_port 12000 "Frontend"
        
        # System resources
        get_system_resources
        
        # Health check
        test_endpoint "http://localhost:12001/health" "Backend Health" 2
        
        echo -e "\n${YELLOW}Next refresh in ${interval}s... (Ctrl+C to stop)${NC}"
        sleep $interval
    done
}

# Main monitoring function
main_monitor() {
    echo "Starting comprehensive system monitoring..."
    echo ""
    
    # Process checks
    echo -e "${CYAN}🔍 Process Status:${NC}"
    check_process "enhanced_backend_main.py" "Enhanced Backend"
    if [ $? -ne 0 ]; then
        check_process "backend_main.py" "Regular Backend"
    fi
    check_process "frontend.*dev\|vite\|npm.*run.*dev" "Frontend"
    
    # Port checks
    echo -e "\n${BLUE}🔌 Port Status:${NC}"
    check_port 12001 "Backend API"
    check_port 12000 "Frontend"
    
    # Health checks
    check_health
    
    # LLM status
    check_llm_status
    
    # Configuration
    check_config
    
    # Network connectivity
    check_network
    
    # System resources
    get_system_resources
    
    # Logs
    check_logs
    
    # Summary
    echo -e "\n${PURPLE}📊 Monitoring Summary:${NC}"
    echo "   Timestamp: $(date)"
    echo "   Monitor URL: http://localhost:12001/health"
    echo "   Frontend URL: http://localhost:12000"
    echo "   API Documentation: http://localhost:12001/docs"
}

# Parse command line arguments
case "${1:-}" in
    --watch)
        monitor_realtime "${2:-30}"
        ;;
    --health)
        check_health
        ;;
    --processes)
        echo -e "${CYAN}🔍 Process Status:${NC}"
        check_process "enhanced_backend_main.py\|backend_main.py" "Backend"
        check_process "frontend.*dev\|vite\|npm.*run.*dev" "Frontend"
        ;;
    --logs)
        check_logs
        ;;
    --config)
        check_config
        ;;
    --llm)
        check_llm_status
        ;;
    --network)
        check_network
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --watch [interval]  Monitor in real-time (default: 30s)"
        echo "  --health           Check health endpoints"
        echo "  --processes        Check process status"
        echo "  --logs            Check recent logs"
        echo "  --config          Check configuration"
        echo "  --llm             Check LLM status"
        echo "  --network         Check network connectivity"
        echo "  --help, -h        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                 # Full monitoring report"
        echo "  $0 --watch         # Real-time monitoring"
        echo "  $0 --watch 10      # Real-time monitoring every 10s"
        echo "  $0 --health        # Health check only"
        ;;
    *)
        main_monitor
        ;;
esac