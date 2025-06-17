"""
Comprehensive Health Check System for reVoAgent
Provides detailed health monitoring for all system components
"""

import asyncio
import time
import psutil
import redis
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import aiohttp
import os

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    status: HealthStatus
    response_time: float
    details: Dict[str, Any]
    error: Optional[str] = None

class HealthChecker:
    """
    Comprehensive health checking system
    """
    
    def __init__(self):
        self.checks = {}
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for health checks"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Could not initialize Redis for health checks: {e}")
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        start_time = time.time()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
                status = HealthStatus.DEGRADED
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = HealthStatus.UNHEALTHY
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk_percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            return HealthCheckResult(
                service="system_resources",
                status=status,
                response_time=time.time() - start_time,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()
        
        if not self.redis_client:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={},
                error="Redis client not initialized"
            )
        
        try:
            # Test basic connectivity
            ping_result = self.redis_client.ping()
            
            # Test read/write operations
            test_key = "health_check_test"
            test_value = str(time.time())
            self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = self.redis_client.get(test_key)
            
            # Get Redis info
            info = self.redis_client.info()
            
            status = HealthStatus.HEALTHY
            if not ping_result or retrieved_value != test_value:
                status = HealthStatus.UNHEALTHY
            
            details = {
                "ping": ping_result,
                "read_write_test": retrieved_value == test_value,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
            return HealthCheckResult(
                service="redis",
                status=status,
                response_time=time.time() - start_time,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        start_time = time.time()
        
        try:
            # This is a placeholder - implement based on your database
            # For now, we'll simulate a database check
            await asyncio.sleep(0.1)  # Simulate DB query time
            
            details = {
                "connection_pool": "healthy",
                "query_performance": "good",
                "active_connections": 5,
                "max_connections": 100
            }
            
            return HealthCheckResult(
                service="database",
                status=HealthStatus.HEALTHY,
                response_time=time.time() - start_time,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    async def check_ai_models(self) -> HealthCheckResult:
        """Check AI model availability"""
        start_time = time.time()
        
        try:
            # Import and check model manager
            from packages.ai.enhanced_local_model_manager import EnhancedLocalModelManager
            
            # This would be replaced with actual model health check
            details = {
                "local_models": "available",
                "openai_api": "checking...",
                "anthropic_api": "checking...",
                "model_memory_usage": "normal"
            }
            
            # Check API keys
            if os.getenv("OPENAI_API_KEY"):
                details["openai_api"] = "configured"
            else:
                details["openai_api"] = "not_configured"
            
            if os.getenv("ANTHROPIC_API_KEY"):
                details["anthropic_api"] = "configured"
            else:
                details["anthropic_api"] = "not_configured"
            
            status = HealthStatus.HEALTHY
            if details["openai_api"] == "not_configured" and details["anthropic_api"] == "not_configured":
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                service="ai_models",
                status=status,
                response_time=time.time() - start_time,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="ai_models",
                status=HealthStatus.DEGRADED,
                response_time=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    async def check_external_apis(self) -> HealthCheckResult:
        """Check external API connectivity"""
        start_time = time.time()
        
        try:
            external_services = {}
            
            # Check GitHub API
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.github.com/rate_limit", timeout=5) as response:
                        if response.status == 200:
                            external_services["github"] = "healthy"
                        else:
                            external_services["github"] = "degraded"
            except:
                external_services["github"] = "unhealthy"
            
            # Check OpenAI API (if configured)
            if os.getenv("OPENAI_API_KEY"):
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
                        async with session.get("https://api.openai.com/v1/models", 
                                             headers=headers, timeout=5) as response:
                            if response.status == 200:
                                external_services["openai"] = "healthy"
                            else:
                                external_services["openai"] = "degraded"
                except:
                    external_services["openai"] = "unhealthy"
            
            # Determine overall status
            healthy_count = sum(1 for status in external_services.values() if status == "healthy")
            total_count = len(external_services)
            
            if total_count == 0:
                status = HealthStatus.UNKNOWN
            elif healthy_count == total_count:
                status = HealthStatus.HEALTHY
            elif healthy_count > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                service="external_apis",
                status=status,
                response_time=time.time() - start_time,
                details=external_services
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="external_apis",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        start_time = time.time()
        
        # Run all health checks concurrently
        checks = await asyncio.gather(
            self.check_system_resources(),
            self.check_redis(),
            self.check_database(),
            self.check_ai_models(),
            self.check_external_apis(),
            return_exceptions=True
        )
        
        # Process results
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for check in checks:
            if isinstance(check, Exception):
                logger.error(f"Health check failed: {check}")
                continue
            
            results[check.service] = {
                "status": check.status.value,
                "response_time": check.response_time,
                "details": check.details,
                "error": check.error
            }
            
            # Determine overall status
            if check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif check.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "total_check_time": time.time() - start_time,
            "services": results,
            "summary": {
                "total_services": len(results),
                "healthy_services": sum(1 for r in results.values() if r["status"] == "healthy"),
                "degraded_services": sum(1 for r in results.values() if r["status"] == "degraded"),
                "unhealthy_services": sum(1 for r in results.values() if r["status"] == "unhealthy")
            }
        }

# Global health checker instance
health_checker = HealthChecker()