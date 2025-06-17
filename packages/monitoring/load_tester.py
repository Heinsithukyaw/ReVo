"""
Load Tester for Phase 4 Comprehensive Monitoring

Provides comprehensive load testing, performance regression testing,
and continuous performance validation capabilities.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import aiofiles
from pathlib import Path
import statistics
import random
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class LoadTestType(Enum):
    """Types of load tests"""
    SMOKE = "smoke"
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    VOLUME = "volume"
    ENDURANCE = "endurance"

class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    name: str
    test_type: LoadTestType
    target_url: str
    duration_seconds: int
    concurrent_users: int
    requests_per_second: Optional[int] = None
    ramp_up_seconds: int = 30
    ramp_down_seconds: int = 30
    headers: Dict[str, str] = None
    payload: Optional[Dict[str, Any]] = None
    method: str = "GET"
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

@dataclass
class RequestResult:
    """Individual request result"""
    timestamp: datetime
    response_time_ms: float
    status_code: int
    success: bool
    error: Optional[str] = None
    size_bytes: int = 0

@dataclass
class LoadTestResult:
    """Load test execution result"""
    test_id: str
    config: LoadTestConfig
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    throughput_mb_per_sec: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['config'] = asdict(self.config)
        data['config']['test_type'] = self.config.test_type.value
        data['status'] = self.status.value
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat() if self.end_time else None
        return data

@dataclass
class PerformanceBaseline:
    """Performance baseline for regression testing"""
    endpoint: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    max_response_time_ms: float
    error_rate: float
    throughput_rps: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class LoadTester:
    """
    Comprehensive load testing system with performance regression detection
    and continuous performance validation
    """
    
    def __init__(self,
                 storage_path: str = "monitoring/load_tests",
                 baseline_storage: str = "monitoring/baselines"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.baseline_storage = Path(baseline_storage)
        self.baseline_storage.mkdir(parents=True, exist_ok=True)
        
        # Test execution state
        self.running_tests: Dict[str, LoadTestResult] = {}
        self.test_history: List[LoadTestResult] = []
        self.performance_baselines: Dict[str, PerformanceBaseline] = {}
        
        # Default test configurations
        self.default_configs = self._create_default_configs()
        
        logger.info("LoadTester initialized")
    
    def _create_default_configs(self) -> Dict[str, LoadTestConfig]:
        """Create default test configurations"""
        return {
            "api_smoke_test": LoadTestConfig(
                name="API Smoke Test",
                test_type=LoadTestType.SMOKE,
                target_url="http://localhost:8000/health",
                duration_seconds=60,
                concurrent_users=5,
                ramp_up_seconds=10,
                ramp_down_seconds=10
            ),
            "api_load_test": LoadTestConfig(
                name="API Load Test",
                test_type=LoadTestType.LOAD,
                target_url="http://localhost:8000/api/v1/agents",
                duration_seconds=300,
                concurrent_users=50,
                requests_per_second=100,
                ramp_up_seconds=60,
                ramp_down_seconds=60
            ),
            "api_stress_test": LoadTestConfig(
                name="API Stress Test",
                test_type=LoadTestType.STRESS,
                target_url="http://localhost:8000/api/v1/agents",
                duration_seconds=600,
                concurrent_users=200,
                requests_per_second=500,
                ramp_up_seconds=120,
                ramp_down_seconds=120
            ),
            "memory_endurance_test": LoadTestConfig(
                name="Memory Endurance Test",
                test_type=LoadTestType.ENDURANCE,
                target_url="http://localhost:8000/api/v1/memory/search",
                duration_seconds=3600,  # 1 hour
                concurrent_users=20,
                requests_per_second=50,
                ramp_up_seconds=300,
                ramp_down_seconds=300,
                payload={"query": "test query", "limit": 10}
            )
        }
    
    async def run_load_test(self, config: LoadTestConfig) -> str:
        """Run a load test and return test ID"""
        test_id = str(uuid.uuid4())
        
        # Initialize test result
        test_result = LoadTestResult(
            test_id=test_id,
            config=config,
            status=TestStatus.PENDING,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=0,
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            avg_response_time_ms=0,
            min_response_time_ms=0,
            max_response_time_ms=0,
            p50_response_time_ms=0,
            p95_response_time_ms=0,
            p99_response_time_ms=0,
            requests_per_second=0,
            error_rate=0,
            throughput_mb_per_sec=0,
            errors=[]
        )
        
        self.running_tests[test_id] = test_result
        
        # Start test execution
        asyncio.create_task(self._execute_load_test(test_id, config))
        
        logger.info(f"Started load test: {config.name} (ID: {test_id})")
        return test_id
    
    async def _execute_load_test(self, test_id: str, config: LoadTestConfig):
        """Execute the actual load test"""
        test_result = self.running_tests[test_id]
        
        try:
            test_result.status = TestStatus.RUNNING
            test_result.start_time = datetime.now()
            
            # Collect request results
            request_results: List[RequestResult] = []
            
            # Create semaphore for concurrent users
            semaphore = asyncio.Semaphore(config.concurrent_users)
            
            # Calculate test phases
            total_duration = config.duration_seconds
            ramp_up_duration = config.ramp_up_seconds
            steady_duration = total_duration - config.ramp_up_seconds - config.ramp_down_seconds
            ramp_down_duration = config.ramp_down_seconds
            
            # Execute test phases
            tasks = []
            
            # Ramp-up phase
            if ramp_up_duration > 0:
                ramp_up_tasks = await self._create_ramp_up_tasks(
                    config, semaphore, ramp_up_duration, request_results
                )
                tasks.extend(ramp_up_tasks)
            
            # Steady state phase
            if steady_duration > 0:
                steady_tasks = await self._create_steady_state_tasks(
                    config, semaphore, steady_duration, request_results
                )
                tasks.extend(steady_tasks)
            
            # Ramp-down phase
            if ramp_down_duration > 0:
                ramp_down_tasks = await self._create_ramp_down_tasks(
                    config, semaphore, ramp_down_duration, request_results
                )
                tasks.extend(ramp_down_tasks)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate results
            await self._calculate_test_results(test_result, request_results)
            
            test_result.status = TestStatus.COMPLETED
            test_result.end_time = datetime.now()
            test_result.duration_seconds = (test_result.end_time - test_result.start_time).total_seconds()
            
            # Save results
            await self._save_test_result(test_result)
            
            # Move to history
            self.test_history.append(test_result)
            del self.running_tests[test_id]
            
            logger.info(f"Completed load test: {config.name} (ID: {test_id})")
            
        except Exception as e:
            test_result.status = TestStatus.FAILED
            test_result.errors.append(str(e))
            logger.error(f"Load test failed: {config.name} (ID: {test_id}): {e}")
    
    async def _create_ramp_up_tasks(self, config: LoadTestConfig, semaphore: asyncio.Semaphore,
                                  duration: int, request_results: List[RequestResult]) -> List[asyncio.Task]:
        """Create tasks for ramp-up phase"""
        tasks = []
        
        # Gradually increase load
        for i in range(duration):
            # Calculate current load level (0 to 100%)
            load_factor = (i + 1) / duration
            current_rps = (config.requests_per_second or 10) * load_factor
            
            # Create requests for this second
            requests_this_second = max(1, int(current_rps))
            
            for _ in range(requests_this_second):
                task = asyncio.create_task(
                    self._make_request(config, semaphore, request_results)
                )
                tasks.append(task)
                
                # Add small delay between requests
                await asyncio.sleep(1.0 / requests_this_second)
        
        return tasks
    
    async def _create_steady_state_tasks(self, config: LoadTestConfig, semaphore: asyncio.Semaphore,
                                       duration: int, request_results: List[RequestResult]) -> List[asyncio.Task]:
        """Create tasks for steady state phase"""
        tasks = []
        target_rps = config.requests_per_second or 10
        
        for i in range(duration):
            # Create requests for this second
            for _ in range(target_rps):
                task = asyncio.create_task(
                    self._make_request(config, semaphore, request_results)
                )
                tasks.append(task)
            
            # Wait for next second
            await asyncio.sleep(1.0)
        
        return tasks
    
    async def _create_ramp_down_tasks(self, config: LoadTestConfig, semaphore: asyncio.Semaphore,
                                    duration: int, request_results: List[RequestResult]) -> List[asyncio.Task]:
        """Create tasks for ramp-down phase"""
        tasks = []
        
        # Gradually decrease load
        for i in range(duration):
            # Calculate current load level (100% to 0%)
            load_factor = 1.0 - ((i + 1) / duration)
            current_rps = (config.requests_per_second or 10) * load_factor
            
            # Create requests for this second
            requests_this_second = max(1, int(current_rps))
            
            for _ in range(requests_this_second):
                task = asyncio.create_task(
                    self._make_request(config, semaphore, request_results)
                )
                tasks.append(task)
                
                # Add small delay between requests
                if requests_this_second > 0:
                    await asyncio.sleep(1.0 / requests_this_second)
        
        return tasks
    
    async def _make_request(self, config: LoadTestConfig, semaphore: asyncio.Semaphore,
                          request_results: List[RequestResult]):
        """Make a single HTTP request"""
        async with semaphore:
            start_time = time.time()
            timestamp = datetime.now()
            
            try:
                timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if config.method.upper() == "GET":
                        async with session.get(config.target_url, headers=config.headers) as response:
                            content = await response.read()
                            size_bytes = len(content)
                            status_code = response.status
                    elif config.method.upper() == "POST":
                        async with session.post(
                            config.target_url, 
                            headers=config.headers,
                            json=config.payload
                        ) as response:
                            content = await response.read()
                            size_bytes = len(content)
                            status_code = response.status
                    else:
                        raise ValueError(f"Unsupported HTTP method: {config.method}")
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                result = RequestResult(
                    timestamp=timestamp,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    success=200 <= status_code < 400,
                    size_bytes=size_bytes
                )
                
                request_results.append(result)
                
            except Exception as e:
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                result = RequestResult(
                    timestamp=timestamp,
                    response_time_ms=response_time_ms,
                    status_code=0,
                    success=False,
                    error=str(e)
                )
                
                request_results.append(result)
    
    async def _calculate_test_results(self, test_result: LoadTestResult, request_results: List[RequestResult]):
        """Calculate test results from request data"""
        if not request_results:
            return
        
        # Basic counts
        test_result.total_requests = len(request_results)
        test_result.successful_requests = sum(1 for r in request_results if r.success)
        test_result.failed_requests = test_result.total_requests - test_result.successful_requests
        
        # Response times
        response_times = [r.response_time_ms for r in request_results]
        test_result.avg_response_time_ms = statistics.mean(response_times)
        test_result.min_response_time_ms = min(response_times)
        test_result.max_response_time_ms = max(response_times)
        
        # Percentiles
        sorted_times = sorted(response_times)
        test_result.p50_response_time_ms = statistics.median(sorted_times)
        test_result.p95_response_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
        test_result.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Rates
        test_result.error_rate = test_result.failed_requests / test_result.total_requests
        test_result.requests_per_second = test_result.total_requests / test_result.duration_seconds
        
        # Throughput
        total_bytes = sum(r.size_bytes for r in request_results)
        test_result.throughput_mb_per_sec = (total_bytes / (1024 * 1024)) / test_result.duration_seconds
        
        # Collect unique errors
        errors = set()
        for r in request_results:
            if r.error:
                errors.add(r.error)
        test_result.errors = list(errors)
    
    async def _save_test_result(self, test_result: LoadTestResult):
        """Save test result to storage"""
        try:
            result_file = self.storage_path / f"load_test_{test_result.test_id}.json"
            async with aiofiles.open(result_file, 'w') as f:
                await f.write(json.dumps(test_result.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Error saving test result: {e}")
    
    async def run_regression_test(self, endpoint: str, baseline_name: Optional[str] = None) -> Dict[str, Any]:
        """Run performance regression test against baseline"""
        try:
            # Get or create baseline
            if baseline_name and baseline_name in self.performance_baselines:
                baseline = self.performance_baselines[baseline_name]
            else:
                baseline = await self._get_baseline_for_endpoint(endpoint)
                if not baseline:
                    return {"status": "no_baseline", "message": "No baseline found for endpoint"}
            
            # Run current test
            config = LoadTestConfig(
                name=f"Regression Test - {endpoint}",
                test_type=LoadTestType.LOAD,
                target_url=endpoint,
                duration_seconds=120,
                concurrent_users=20,
                requests_per_second=50
            )
            
            test_id = await self.run_load_test(config)
            
            # Wait for test completion
            while test_id in self.running_tests:
                await asyncio.sleep(1)
            
            # Get test result
            current_result = next((r for r in self.test_history if r.test_id == test_id), None)
            if not current_result:
                return {"status": "test_failed", "message": "Test execution failed"}
            
            # Compare with baseline
            regression_analysis = await self._analyze_regression(baseline, current_result)
            
            return {
                "status": "completed",
                "baseline": baseline.to_dict(),
                "current": current_result.to_dict(),
                "regression_analysis": regression_analysis
            }
            
        except Exception as e:
            logger.error(f"Error running regression test: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _get_baseline_for_endpoint(self, endpoint: str) -> Optional[PerformanceBaseline]:
        """Get performance baseline for endpoint"""
        # Look for existing baseline file
        baseline_file = self.baseline_storage / f"baseline_{endpoint.replace('/', '_').replace(':', '_')}.json"
        
        if baseline_file.exists():
            try:
                async with aiofiles.open(baseline_file, 'r') as f:
                    data = json.loads(await f.read())
                    return PerformanceBaseline(
                        endpoint=data['endpoint'],
                        avg_response_time_ms=data['avg_response_time_ms'],
                        p95_response_time_ms=data['p95_response_time_ms'],
                        max_response_time_ms=data['max_response_time_ms'],
                        error_rate=data['error_rate'],
                        throughput_rps=data['throughput_rps'],
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )
            except Exception as e:
                logger.error(f"Error loading baseline: {e}")
        
        return None
    
    async def _analyze_regression(self, baseline: PerformanceBaseline, 
                                current: LoadTestResult) -> Dict[str, Any]:
        """Analyze performance regression"""
        analysis = {
            "has_regression": False,
            "regressions": [],
            "improvements": [],
            "summary": ""
        }
        
        # Response time regression
        response_time_change = ((current.avg_response_time_ms - baseline.avg_response_time_ms) / 
                              baseline.avg_response_time_ms) * 100
        
        if response_time_change > 20:  # 20% slower
            analysis["has_regression"] = True
            analysis["regressions"].append({
                "metric": "avg_response_time",
                "baseline": baseline.avg_response_time_ms,
                "current": current.avg_response_time_ms,
                "change_percent": response_time_change,
                "severity": "high" if response_time_change > 50 else "medium"
            })
        elif response_time_change < -10:  # 10% faster
            analysis["improvements"].append({
                "metric": "avg_response_time",
                "baseline": baseline.avg_response_time_ms,
                "current": current.avg_response_time_ms,
                "change_percent": response_time_change
            })
        
        # P95 response time regression
        p95_change = ((current.p95_response_time_ms - baseline.p95_response_time_ms) / 
                     baseline.p95_response_time_ms) * 100
        
        if p95_change > 25:  # 25% slower
            analysis["has_regression"] = True
            analysis["regressions"].append({
                "metric": "p95_response_time",
                "baseline": baseline.p95_response_time_ms,
                "current": current.p95_response_time_ms,
                "change_percent": p95_change,
                "severity": "high" if p95_change > 75 else "medium"
            })
        
        # Error rate regression
        error_rate_change = current.error_rate - baseline.error_rate
        
        if error_rate_change > 0.02:  # 2% increase in error rate
            analysis["has_regression"] = True
            analysis["regressions"].append({
                "metric": "error_rate",
                "baseline": baseline.error_rate,
                "current": current.error_rate,
                "change_percent": error_rate_change * 100,
                "severity": "critical" if error_rate_change > 0.1 else "high"
            })
        
        # Throughput regression
        throughput_change = ((current.requests_per_second - baseline.throughput_rps) / 
                           baseline.throughput_rps) * 100
        
        if throughput_change < -20:  # 20% lower throughput
            analysis["has_regression"] = True
            analysis["regressions"].append({
                "metric": "throughput",
                "baseline": baseline.throughput_rps,
                "current": current.requests_per_second,
                "change_percent": throughput_change,
                "severity": "medium"
            })
        elif throughput_change > 10:  # 10% higher throughput
            analysis["improvements"].append({
                "metric": "throughput",
                "baseline": baseline.throughput_rps,
                "current": current.requests_per_second,
                "change_percent": throughput_change
            })
        
        # Generate summary
        if analysis["has_regression"]:
            regression_count = len(analysis["regressions"])
            analysis["summary"] = f"Performance regression detected: {regression_count} metrics degraded"
        elif analysis["improvements"]:
            improvement_count = len(analysis["improvements"])
            analysis["summary"] = f"Performance improved: {improvement_count} metrics enhanced"
        else:
            analysis["summary"] = "Performance stable: no significant changes detected"
        
        return analysis
    
    async def create_baseline(self, endpoint: str, test_result: LoadTestResult) -> bool:
        """Create performance baseline from test result"""
        try:
            baseline = PerformanceBaseline(
                endpoint=endpoint,
                avg_response_time_ms=test_result.avg_response_time_ms,
                p95_response_time_ms=test_result.p95_response_time_ms,
                max_response_time_ms=test_result.max_response_time_ms,
                error_rate=test_result.error_rate,
                throughput_rps=test_result.requests_per_second,
                timestamp=datetime.now()
            )
            
            # Save baseline
            baseline_file = self.baseline_storage / f"baseline_{endpoint.replace('/', '_').replace(':', '_')}.json"
            async with aiofiles.open(baseline_file, 'w') as f:
                await f.write(json.dumps(baseline.to_dict(), indent=2))
            
            # Store in memory
            self.performance_baselines[endpoint] = baseline
            
            logger.info(f"Created performance baseline for {endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating baseline: {e}")
            return False
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get status of running or completed test"""
        if test_id in self.running_tests:
            test = self.running_tests[test_id]
            return {
                "test_id": test_id,
                "status": test.status.value,
                "progress": self._calculate_test_progress(test),
                "current_metrics": {
                    "total_requests": test.total_requests,
                    "successful_requests": test.successful_requests,
                    "failed_requests": test.failed_requests
                }
            }
        
        # Check history
        for test in self.test_history:
            if test.test_id == test_id:
                return test.to_dict()
        
        return None
    
    def _calculate_test_progress(self, test: LoadTestResult) -> float:
        """Calculate test progress percentage"""
        if test.status != TestStatus.RUNNING:
            return 100.0 if test.status == TestStatus.COMPLETED else 0.0
        
        elapsed = (datetime.now() - test.start_time).total_seconds()
        total_duration = test.config.duration_seconds + test.config.ramp_up_seconds + test.config.ramp_down_seconds
        
        return min(100.0, (elapsed / total_duration) * 100)
    
    def get_load_test_summary(self) -> Dict[str, Any]:
        """Get load testing summary"""
        return {
            "running_tests": len(self.running_tests),
            "completed_tests": len(self.test_history),
            "available_configs": list(self.default_configs.keys()),
            "performance_baselines": len(self.performance_baselines),
            "recent_tests": [
                {
                    "test_id": test.test_id,
                    "name": test.config.name,
                    "status": test.status.value,
                    "start_time": test.start_time.isoformat(),
                    "duration": test.duration_seconds
                }
                for test in self.test_history[-5:]  # Last 5 tests
            ]
        }

# Global instance
_load_tester = None

async def get_load_tester() -> LoadTester:
    """Get or create global load tester instance"""
    global _load_tester
    if _load_tester is None:
        _load_tester = LoadTester()
    return _load_tester