"""
Production Environment Smoke Tests
Critical validation tests for production deployment
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductionSmokeTestResult:
    test_name: str
    status: str  # PASS, FAIL, CRITICAL
    duration: float
    error_message: str = ""
    response_data: Dict[str, Any] = None
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

class ProductionSmokeTest:
    def __init__(self, base_url: str = "https://revoagent.com"):
        self.base_url = base_url
        self.results: List[ProductionSmokeTestResult] = []
        
    async def test_health_endpoint(self) -> ProductionSmokeTestResult:
        """Test basic health endpoint - CRITICAL"""
        logger.info("🏥 Testing health endpoint...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check health status
                        if data.get("status") == "healthy":
                            return ProductionSmokeTestResult(
                                test_name="Health Endpoint",
                                status="PASS",
                                duration=duration,
                                response_data=data,
                                severity="CRITICAL"
                            )
                        else:
                            return ProductionSmokeTestResult(
                                test_name="Health Endpoint",
                                status="CRITICAL",
                                duration=duration,
                                error_message=f"Unhealthy status: {data.get('status')}",
                                severity="CRITICAL"
                            )
                    else:
                        return ProductionSmokeTestResult(
                            test_name="Health Endpoint",
                            status="CRITICAL",
                            duration=duration,
                            error_message=f"HTTP {response.status}",
                            severity="CRITICAL"
                        )
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Health Endpoint",
                status="CRITICAL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="CRITICAL"
            )
    
    async def test_ssl_certificate(self) -> ProductionSmokeTestResult:
        """Test SSL certificate validity - HIGH"""
        logger.info("🔒 Testing SSL certificate...")
        start_time = time.time()
        
        try:
            import ssl
            import socket
            from urllib.parse import urlparse
            
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate validity
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    duration = time.time() - start_time
                    
                    if days_until_expiry > 7:
                        return ProductionSmokeTestResult(
                            test_name="SSL Certificate",
                            status="PASS",
                            duration=duration,
                            response_data={"days_until_expiry": days_until_expiry},
                            severity="HIGH"
                        )
                    elif days_until_expiry > 0:
                        return ProductionSmokeTestResult(
                            test_name="SSL Certificate",
                            status="FAIL",
                            duration=duration,
                            error_message=f"Certificate expires in {days_until_expiry} days",
                            severity="HIGH"
                        )
                    else:
                        return ProductionSmokeTestResult(
                            test_name="SSL Certificate",
                            status="CRITICAL",
                            duration=duration,
                            error_message="Certificate has expired",
                            severity="CRITICAL"
                        )
                        
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="SSL Certificate",
                status="CRITICAL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="CRITICAL"
            )
    
    async def test_response_time(self) -> ProductionSmokeTestResult:
        """Test response time performance - HIGH"""
        logger.info("⚡ Testing response time...")
        start_time = time.time()
        
        try:
            response_times = []
            
            async with aiohttp.ClientSession() as session:
                # Test multiple requests to get average
                for _ in range(5):
                    request_start = time.time()
                    async with session.get(f"{self.base_url}/api/health", timeout=10) as response:
                        request_duration = time.time() - request_start
                        response_times.append(request_duration)
                        
                        if response.status != 200:
                            return ProductionSmokeTestResult(
                                test_name="Response Time",
                                status="FAIL",
                                duration=time.time() - start_time,
                                error_message=f"HTTP {response.status}",
                                severity="HIGH"
                            )
                
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                duration = time.time() - start_time
                
                # Production SLA: 95% of requests under 1 second
                if max_response_time < 1.0:
                    return ProductionSmokeTestResult(
                        test_name="Response Time",
                        status="PASS",
                        duration=duration,
                        response_data={
                            "avg_response_time": avg_response_time,
                            "max_response_time": max_response_time
                        },
                        severity="HIGH"
                    )
                elif avg_response_time < 2.0:
                    return ProductionSmokeTestResult(
                        test_name="Response Time",
                        status="FAIL",
                        duration=duration,
                        error_message=f"Slow response time: avg={avg_response_time:.3f}s, max={max_response_time:.3f}s",
                        severity="HIGH"
                    )
                else:
                    return ProductionSmokeTestResult(
                        test_name="Response Time",
                        status="CRITICAL",
                        duration=duration,
                        error_message=f"Very slow response time: avg={avg_response_time:.3f}s",
                        severity="CRITICAL"
                    )
                    
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Response Time",
                status="CRITICAL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="CRITICAL"
            )
    
    async def test_core_functionality(self) -> ProductionSmokeTestResult:
        """Test core application functionality - CRITICAL"""
        logger.info("🎯 Testing core functionality...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test critical endpoints
                critical_endpoints = [
                    ("/api/agents/status", "Agent system"),
                    ("/api/models/status", "AI models"),
                    ("/api/system/metrics", "System metrics")
                ]
                
                for endpoint, description in critical_endpoints:
                    async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                        if response.status not in [200, 401, 403]:  # Auth errors are acceptable
                            return ProductionSmokeTestResult(
                                test_name="Core Functionality",
                                status="CRITICAL",
                                duration=time.time() - start_time,
                                error_message=f"{description} endpoint failed: HTTP {response.status}",
                                severity="CRITICAL"
                            )
                
                return ProductionSmokeTestResult(
                    test_name="Core Functionality",
                    status="PASS",
                    duration=time.time() - start_time,
                    response_data={"tested_endpoints": len(critical_endpoints)},
                    severity="CRITICAL"
                )
                
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Core Functionality",
                status="CRITICAL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="CRITICAL"
            )
    
    async def test_database_performance(self) -> ProductionSmokeTestResult:
        """Test database performance - HIGH"""
        logger.info("💾 Testing database performance...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test database-heavy endpoint
                db_start = time.time()
                async with session.get(f"{self.base_url}/api/system/status", timeout=15) as response:
                    db_duration = time.time() - db_start
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check database status and performance
                        db_status = data.get("database", {})
                        if db_status.get("status") == "connected":
                            if db_duration < 2.0:  # Database queries should be fast
                                return ProductionSmokeTestResult(
                                    test_name="Database Performance",
                                    status="PASS",
                                    duration=time.time() - start_time,
                                    response_data={
                                        "db_response_time": db_duration,
                                        "connection_pool": db_status.get("pool_size", "unknown")
                                    },
                                    severity="HIGH"
                                )
                            else:
                                return ProductionSmokeTestResult(
                                    test_name="Database Performance",
                                    status="FAIL",
                                    duration=time.time() - start_time,
                                    error_message=f"Slow database response: {db_duration:.3f}s",
                                    severity="HIGH"
                                )
                        else:
                            return ProductionSmokeTestResult(
                                test_name="Database Performance",
                                status="CRITICAL",
                                duration=time.time() - start_time,
                                error_message="Database not connected",
                                severity="CRITICAL"
                            )
                    else:
                        return ProductionSmokeTestResult(
                            test_name="Database Performance",
                            status="FAIL",
                            duration=time.time() - start_time,
                            error_message=f"HTTP {response.status}",
                            severity="HIGH"
                        )
                        
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Database Performance",
                status="CRITICAL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="CRITICAL"
            )
    
    async def test_security_headers(self) -> ProductionSmokeTestResult:
        """Test security headers - MEDIUM"""
        logger.info("🛡️ Testing security headers...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/", timeout=10) as response:
                    duration = time.time() - start_time
                    
                    # Check for essential security headers
                    required_headers = {
                        "Strict-Transport-Security": "HSTS",
                        "X-Content-Type-Options": "Content type protection",
                        "X-Frame-Options": "Clickjacking protection",
                        "X-XSS-Protection": "XSS protection"
                    }
                    
                    missing_headers = []
                    present_headers = {}
                    
                    for header, description in required_headers.items():
                        if header in response.headers:
                            present_headers[header] = response.headers[header]
                        else:
                            missing_headers.append(f"{header} ({description})")
                    
                    if not missing_headers:
                        return ProductionSmokeTestResult(
                            test_name="Security Headers",
                            status="PASS",
                            duration=duration,
                            response_data={"present_headers": present_headers},
                            severity="MEDIUM"
                        )
                    elif len(missing_headers) <= 1:
                        return ProductionSmokeTestResult(
                            test_name="Security Headers",
                            status="FAIL",
                            duration=duration,
                            error_message=f"Missing headers: {', '.join(missing_headers)}",
                            severity="MEDIUM"
                        )
                    else:
                        return ProductionSmokeTestResult(
                            test_name="Security Headers",
                            status="FAIL",
                            duration=duration,
                            error_message=f"Multiple missing headers: {', '.join(missing_headers)}",
                            severity="HIGH"
                        )
                        
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Security Headers",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="MEDIUM"
            )
    
    async def test_monitoring_availability(self) -> ProductionSmokeTestResult:
        """Test monitoring system availability - MEDIUM"""
        logger.info("📊 Testing monitoring availability...")
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test metrics endpoint
                async with session.get(f"{self.base_url}/metrics", timeout=10) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        metrics_data = await response.text()
                        
                        # Check for critical metrics
                        critical_metrics = [
                            "revoagent_requests_total",
                            "revoagent_errors_total",
                            "revoagent_response_time"
                        ]
                        
                        missing_metrics = [m for m in critical_metrics if m not in metrics_data]
                        
                        if not missing_metrics:
                            return ProductionSmokeTestResult(
                                test_name="Monitoring Availability",
                                status="PASS",
                                duration=duration,
                                response_data={"metrics_size": len(metrics_data)},
                                severity="MEDIUM"
                            )
                        else:
                            return ProductionSmokeTestResult(
                                test_name="Monitoring Availability",
                                status="FAIL",
                                duration=duration,
                                error_message=f"Missing critical metrics: {missing_metrics}",
                                severity="MEDIUM"
                            )
                    else:
                        return ProductionSmokeTestResult(
                            test_name="Monitoring Availability",
                            status="FAIL",
                            duration=duration,
                            error_message=f"Metrics endpoint failed: HTTP {response.status}",
                            severity="MEDIUM"
                        )
                        
        except Exception as e:
            return ProductionSmokeTestResult(
                test_name="Monitoring Availability",
                status="FAIL",
                duration=time.time() - start_time,
                error_message=str(e),
                severity="MEDIUM"
            )
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production smoke tests"""
        logger.info("🚀 Starting Production Smoke Tests...")
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_health_endpoint(),
            self.test_ssl_certificate(),
            self.test_response_time(),
            self.test_core_functionality(),
            self.test_database_performance(),
            self.test_security_headers(),
            self.test_monitoring_availability()
        ]
        
        self.results = await asyncio.gather(*tests)
        
        # Calculate metrics
        total_duration = time.time() - start_time
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        critical_failures = len([r for r in self.results if r.status == "CRITICAL"])
        
        # Categorize by severity
        critical_issues = len([r for r in self.results if r.severity == "CRITICAL" and r.status != "PASS"])
        high_issues = len([r for r in self.results if r.severity == "HIGH" and r.status != "PASS"])
        medium_issues = len([r for r in self.results if r.severity == "MEDIUM" and r.status != "PASS"])
        
        success_rate = (passed_tests / total_tests) * 100
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = "CRITICAL"
        elif critical_issues > 0:
            overall_status = "FAIL"
        elif high_issues > 2:
            overall_status = "FAIL"
        else:
            overall_status = "PASS"
        
        # Generate summary
        summary = {
            "test_suite": "Production Smoke Tests",
            "environment": "production",
            "timestamp": datetime.now().isoformat(),
            "duration": total_duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "critical_failures": critical_failures,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "success_rate": success_rate,
            "overall_status": overall_status,
            "results": [asdict(result) for result in self.results]
        }
        
        # Save results
        with open("production_smoke_test_results.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🧪 PRODUCTION SMOKE TEST SUMMARY")
        print("="*80)
        print(f"🌐 Environment: {self.base_url}")
        print(f"⏱️  Duration: {total_duration:.2f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🚨 Critical Failures: {critical_failures}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎉 Overall Status: {overall_status}")
        print("="*80)
        
        # Print severity breakdown
        print(f"🚨 Critical Issues: {critical_issues}")
        print(f"🔴 High Issues: {high_issues}")
        print(f"🟡 Medium Issues: {medium_issues}")
        print("="*80)
        
        for result in self.results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "CRITICAL": "🚨"}[result.status]
            severity_icon = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[result.severity]
            
            print(f"{status_icon} {severity_icon} {result.test_name} ({result.duration:.2f}s)")
            if result.error_message:
                print(f"   Error: {result.error_message}")
            if result.response_data:
                print(f"   Data: {result.response_data}")
        
        return summary

async def main():
    """Main function to run production smoke tests"""
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://revoagent.com"
    
    tester = ProductionSmokeTest(base_url)
    
    try:
        results = await tester.run_all_tests()
        
        # Exit with appropriate code based on severity
        if results["overall_status"] == "PASS":
            print("🎉 All production smoke tests passed!")
            exit(0)
        elif results["overall_status"] == "CRITICAL":
            print("🚨 CRITICAL production issues detected!")
            exit(2)
        else:
            print("❌ Production smoke tests failed!")
            exit(1)
            
    except Exception as e:
        logger.error(f"Production smoke testing failed: {e}")
        exit(2)

if __name__ == "__main__":
    asyncio.run(main())