#!/usr/bin/env python3
"""
🧪 Comprehensive Load Testing Framework
Phase 3 - Load Testing Validation (1000+ requests/minute)

Advanced load testing with realistic scenarios and comprehensive metrics.
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import concurrent.futures
import random
import uuid
import psutil
import ssl

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    # Test parameters
    target_rps: int = 1000  # Requests per second
    test_duration_minutes: int = 10
    ramp_up_minutes: int = 2
    ramp_down_minutes: int = 1
    
    # Connection settings
    max_connections: int = 500
    connection_timeout: int = 30
    request_timeout: int = 10
    
    # Test scenarios
    api_weight: float = 0.6  # 60% API calls
    websocket_weight: float = 0.3  # 30% WebSocket
    mixed_weight: float = 0.1  # 10% mixed operations
    
    # Target endpoints
    base_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000/ws"
    
    # Performance targets
    target_response_time_p95: float = 2.0  # 2 seconds
    target_error_rate: float = 0.1  # 0.1%
    target_throughput: int = 1000  # RPS

@dataclass
class RequestResult:
    """Individual request result"""
    timestamp: float
    request_type: str
    endpoint: str
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    payload_size: int = 0

@dataclass
class LoadTestMetrics:
    """Load test metrics"""
    timestamp: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate_percent: float
    
    # Response time metrics
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    
    # Throughput metrics
    requests_per_second: float
    peak_rps: float
    
    # System metrics
    cpu_usage_percent: float
    memory_usage_percent: float
    network_io_mbps: float
    
    # Test status
    test_passed: bool
    performance_score: float

class APILoadTester:
    """API endpoint load testing"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.session = None
        self.results = []
        
    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=100,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.request_timeout,
            connect=self.config.connection_timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str, method: str = 'GET', 
                          payload: Dict = None) -> RequestResult:
        """Make individual API request"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            url = f"{self.config.base_url}{endpoint}"
            
            if method == 'GET':
                async with self.session.get(url) as response:
                    data = await response.text()
                    
            elif method == 'POST':
                async with self.session.post(url, json=payload) as response:
                    data = await response.text()
            
            response_time = time.time() - start_time
            
            return RequestResult(
                timestamp=start_time,
                request_type='api',
                endpoint=endpoint,
                response_time=response_time,
                status_code=response.status,
                success=200 <= response.status < 400,
                payload_size=len(data)
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            
            return RequestResult(
                timestamp=start_time,
                request_type='api',
                endpoint=endpoint,
                response_time=response_time,
                status_code=0,
                success=False,
                error_message=str(e)
            )
    
    async def run_api_scenario(self, duration_seconds: int) -> List[RequestResult]:
        """Run API load test scenario"""
        results = []
        end_time = time.time() + duration_seconds
        
        # Define test endpoints with realistic payloads
        endpoints = [
            ('/health', 'GET', None),
            ('/api/v1/engines/status', 'GET', None),
            ('/api/v1/chat/completions', 'POST', {
                'messages': [{'role': 'user', 'content': 'Test message'}],
                'model': 'deepseek-r1',
                'max_tokens': 100
            }),
            ('/api/v1/memory/search', 'POST', {
                'query': 'test search query',
                'limit': 10
            }),
            ('/api/v1/agents/analyze', 'POST', {
                'code': 'def test(): return "hello"',
                'language': 'python'
            })
        ]
        
        while time.time() < end_time:
            # Select random endpoint
            endpoint, method, payload = random.choice(endpoints)
            
            # Make request
            result = await self.make_request(endpoint, method, payload)
            results.append(result)
            
            # Control request rate
            await asyncio.sleep(random.uniform(0.01, 0.1))
        
        return results

class SystemMonitor:
    """System resource monitoring during load test"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
    
    async def start_monitoring(self):
        """Start system monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                # CPU and memory
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Network I/O
                net_io = psutil.net_io_counters()
                
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'network_bytes_sent': net_io.bytes_sent,
                    'network_bytes_recv': net_io.bytes_recv
                }
                
                self.metrics.append(metric)
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Get average system metrics"""
        if not self.metrics:
            return {}
        
        return {
            'avg_cpu_percent': statistics.mean(m['cpu_percent'] for m in self.metrics),
            'avg_memory_percent': statistics.mean(m['memory_percent'] for m in self.metrics),
            'peak_cpu_percent': max(m['cpu_percent'] for m in self.metrics),
            'peak_memory_percent': max(m['memory_percent'] for m in self.metrics)
        }

class ComprehensiveLoadTester:
    """Main load testing orchestrator"""
    
    def __init__(self, config: LoadTestConfig = None):
        self.config = config or LoadTestConfig()
        self.api_tester = APILoadTester(self.config)
        self.monitor = SystemMonitor()
        
        self.all_results = []
        self.test_start_time = None
        self.test_end_time = None
    
    async def run_load_test(self) -> LoadTestMetrics:
        """Run comprehensive load test"""
        print(f"🚀 Starting Comprehensive Load Test")
        print(f"   Target: {self.config.target_rps} RPS for {self.config.test_duration_minutes} minutes")
        print(f"   Endpoints: {self.config.base_url}")
        
        self.test_start_time = time.time()
        
        try:
            # Initialize components
            await self.api_tester.initialize()
            
            # Start system monitoring
            monitor_task = asyncio.create_task(self.monitor.start_monitoring())
            
            # Calculate test phases
            total_duration = self.config.test_duration_minutes * 60
            
            print(f"📊 Test Duration: {self.config.test_duration_minutes} minutes")
            
            # Run API load test
            api_results = await self.api_tester.run_api_scenario(total_duration)
            self.all_results.extend(api_results)
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            monitor_task.cancel()
            
            self.test_end_time = time.time()
            
            # Generate metrics
            metrics = self._calculate_metrics()
            
            print(f"✅ Load Test Complete!")
            print(f"   Total Requests: {metrics.total_requests}")
            print(f"   Success Rate: {100 - metrics.error_rate_percent:.2f}%")
            print(f"   Average RPS: {metrics.requests_per_second:.1f}")
            print(f"   P95 Response Time: {metrics.p95_response_time:.3f}s")
            print(f"   Performance Score: {metrics.performance_score:.1f}%")
            
            return metrics
            
        finally:
            await self.api_tester.cleanup()
    
    def _calculate_metrics(self) -> LoadTestMetrics:
        """Calculate comprehensive test metrics"""
        if not self.all_results:
            return LoadTestMetrics(
                timestamp=datetime.now().isoformat(),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                error_rate_percent=100.0,
                avg_response_time=0.0,
                p50_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                max_response_time=0.0,
                requests_per_second=0.0,
                peak_rps=0.0,
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                network_io_mbps=0.0,
                test_passed=False,
                performance_score=0.0
            )
        
        # Basic counts
        total_requests = len(self.all_results)
        successful_requests = sum(1 for r in self.all_results if r.success)
        failed_requests = total_requests - successful_requests
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 100
        
        # Response time metrics
        response_times = [r.response_time for r in self.all_results if r.success]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p50_response_time = statistics.median(response_times)
            # Use sorted list for percentiles if quantiles not available
            sorted_times = sorted(response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
            p95_response_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]
            p99_response_time = sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1]
            max_response_time = max(response_times)
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = max_response_time = 0.0
        
        # Throughput metrics
        test_duration = self.test_end_time - self.test_start_time if self.test_end_time else 1
        requests_per_second = total_requests / test_duration
        
        # Calculate peak RPS (highest RPS in any 10-second window)
        peak_rps = self._calculate_peak_rps()
        
        # System metrics
        system_metrics = self.monitor.get_average_metrics()
        
        # Performance score calculation
        performance_score = self._calculate_performance_score(
            error_rate, p95_response_time, requests_per_second
        )
        
        # Test pass/fail
        test_passed = (
            error_rate <= self.config.target_error_rate and
            p95_response_time <= self.config.target_response_time_p95 and
            requests_per_second >= self.config.target_throughput * 0.8  # 80% of target
        )
        
        return LoadTestMetrics(
            timestamp=datetime.now().isoformat(),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            error_rate_percent=error_rate,
            avg_response_time=avg_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            peak_rps=peak_rps,
            cpu_usage_percent=system_metrics.get('avg_cpu_percent', 0.0),
            memory_usage_percent=system_metrics.get('avg_memory_percent', 0.0),
            network_io_mbps=0.0,  # Calculated separately if needed
            test_passed=test_passed,
            performance_score=performance_score
        )
    
    def _calculate_peak_rps(self) -> float:
        """Calculate peak requests per second"""
        if not self.all_results:
            return 0.0
        
        # Group requests by 10-second windows
        window_size = 10  # seconds
        windows = {}
        
        for result in self.all_results:
            window = int(result.timestamp // window_size) * window_size
            if window not in windows:
                windows[window] = 0
            windows[window] += 1
        
        # Find peak
        return max(windows.values()) / window_size if windows else 0.0
    
    def _calculate_performance_score(self, error_rate: float, p95_time: float, rps: float) -> float:
        """Calculate overall performance score"""
        # Error rate score (0-100, lower is better)
        error_score = max(0, 100 - (error_rate / self.config.target_error_rate) * 100)
        
        # Response time score (0-100, lower is better)
        time_score = max(0, 100 - (p95_time / self.config.target_response_time_p95) * 100)
        
        # Throughput score (0-100, higher is better)
        throughput_score = min(100, (rps / self.config.target_throughput) * 100)
        
        # Weighted average
        total_score = (error_score * 0.4 + time_score * 0.4 + throughput_score * 0.2)
        
        return min(100.0, max(0.0, total_score))
    
    def save_results(self, filename: str):
        """Save test results to file"""
        metrics = self._calculate_metrics()
        
        report = {
            'test_config': asdict(self.config),
            'test_metrics': asdict(metrics),
            'system_metrics': self.monitor.get_average_metrics(),
            'detailed_results': [asdict(r) for r in self.all_results[-100:]]  # Last 100 results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📁 Results saved to: {filename}")

async def main():
    """Main load testing execution"""
    # Configure test
    config = LoadTestConfig(
        target_rps=1000,
        test_duration_minutes=2,  # Shorter for demo
        base_url="http://localhost:8000"
    )
    
    # Run load test
    tester = ComprehensiveLoadTester(config)
    
    try:
        metrics = await tester.run_load_test()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/workspace/reVoAgent/tests/load_testing/load_test_results_{timestamp}.json"
        tester.save_results(filename)
        
        # Print summary
        print(f"\n🎯 Load Test Summary:")
        print(f"   Test Passed: {'✅ YES' if metrics.test_passed else '❌ NO'}")
        print(f"   Performance Score: {metrics.performance_score:.1f}%")
        print(f"   Total Requests: {metrics.total_requests:,}")
        print(f"   Success Rate: {100 - metrics.error_rate_percent:.2f}%")
        print(f"   Average RPS: {metrics.requests_per_second:.1f}")
        print(f"   Peak RPS: {metrics.peak_rps:.1f}")
        print(f"   P95 Response Time: {metrics.p95_response_time:.3f}s")
        print(f"   CPU Usage: {metrics.cpu_usage_percent:.1f}%")
        print(f"   Memory Usage: {metrics.memory_usage_percent:.1f}%")
        
        return metrics.test_passed
        
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        logging.error(f"Load test error: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = asyncio.run(main())