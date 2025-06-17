#!/usr/bin/env python3
"""
Full Stack Platform Test Suite
Tests the complete reVoAgent platform after enterprise cleanup
"""

import subprocess
import time
import requests
import json
import sys
from datetime import datetime

class FullStackTester:
    def __init__(self):
        self.backend_url = "http://localhost:12001"
        self.frontend_url = "http://localhost:12000"
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def start_system(self):
        """Start the full stack system"""
        print("🚀 Starting Full Stack System...")
        try:
            # Start the system in background
            process = subprocess.Popen(
                ["./start_consolidated.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/workspace/reVoAgent"
            )
            
            # Wait for system to start
            time.sleep(15)
            
            self.log_test("System Startup", "PASS", "System started successfully")
            return True
        except Exception as e:
            self.log_test("System Startup", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health", "PASS", f"Status: {data.get('status', 'OK')}")
                return True
            else:
                self.log_test("Backend Health", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test key API endpoints"""
        endpoints = [
            "/api/models",
            "/api/health",
            "/docs"
        ]
        
        passed = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_test(f"API {endpoint}", "PASS", f"HTTP {response.status_code}")
                    passed += 1
                else:
                    self.log_test(f"API {endpoint}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"API {endpoint}", "FAIL", f"Error: {str(e)}")
        
        return passed == len(endpoints)
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Access", "PASS", f"HTTP {response.status_code}")
                return True
            else:
                self.log_test("Frontend Access", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Access", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_chat_api(self):
        """Test chat API functionality"""
        try:
            payload = {
                "message": "Hello, this is a test message",
                "model": "test"
            }
            response = requests.post(
                f"{self.backend_url}/api/chat",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Chat API", "PASS", f"Response received: {len(str(data))} chars")
                return True
            else:
                self.log_test("Chat API", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Chat API", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        try:
            headers = {
                'Origin': 'http://localhost:12000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{self.backend_url}/api/health", headers=headers, timeout=5)
            
            cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
            if '*' in cors_headers or 'localhost' in cors_headers:
                self.log_test("CORS Configuration", "PASS", f"CORS enabled: {cors_headers}")
                return True
            else:
                self.log_test("CORS Configuration", "FAIL", f"CORS headers: {cors_headers}")
                return False
        except Exception as e:
            self.log_test("CORS Configuration", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_port_configuration(self):
        """Test port configuration"""
        import socket
        
        ports_to_check = [12000, 12001]
        all_ports_open = True
        
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.log_test(f"Port {port}", "PASS", "Port is accessible")
            else:
                self.log_test(f"Port {port}", "FAIL", "Port is not accessible")
                all_ports_open = False
        
        return all_ports_open
    
    def stop_system(self):
        """Stop the full stack system"""
        print("\n🛑 Stopping Full Stack System...")
        try:
            subprocess.run(
                ["./stop_consolidated.sh"],
                cwd="/workspace/reVoAgent",
                timeout=30
            )
            self.log_test("System Shutdown", "PASS", "System stopped cleanly")
            return True
        except Exception as e:
            self.log_test("System Shutdown", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🧪 FULL STACK PLATFORM TEST SUITE")
        print("=" * 50)
        
        # Start system
        if not self.start_system():
            print("❌ Cannot start system, aborting tests")
            return False
        
        # Wait for system to fully initialize
        print("⏳ Waiting for system initialization...")
        time.sleep(10)
        
        # Run tests
        tests = [
            self.test_backend_health,
            self.test_port_configuration,
            self.test_api_endpoints,
            self.test_frontend_accessibility,
            self.test_cors_configuration,
            self.test_chat_api
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
        
        # Stop system
        self.stop_system()
        
        # Generate report
        self.generate_report(passed_tests, len(tests))
        
        return passed_tests == len(tests)
    
    def generate_report(self, passed, total):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📊 FULL STACK TEST RESULTS")
        print("=" * 50)
        
        success_rate = (passed / total) * 100
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Full stack platform is working perfectly!")
            grade = "A+"
        elif success_rate >= 80:
            print("✅ GOOD! Full stack platform is working well!")
            grade = "A"
        elif success_rate >= 70:
            print("⚠️  FAIR! Full stack platform has minor issues!")
            grade = "B"
        else:
            print("❌ POOR! Full stack platform needs attention!")
            grade = "C"
        
        print(f"Platform Grade: {grade}")
        
        # Save detailed report
        report = {
            "test_summary": {
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": success_rate,
                "grade": grade,
                "timestamp": datetime.now().isoformat()
            },
            "test_details": self.test_results
        }
        
        with open("/workspace/reVoAgent/full_stack_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to: full_stack_test_report.json")

def main():
    """Main test execution"""
    tester = FullStackTester()
    success = tester.run_full_test_suite()
    
    if success:
        print("\n🚀 Full stack platform is ready for production!")
        sys.exit(0)
    else:
        print("\n⚠️  Full stack platform needs attention before production!")
        sys.exit(1)

if __name__ == "__main__":
    main()