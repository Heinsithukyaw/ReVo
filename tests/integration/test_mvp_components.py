#!/usr/bin/env python3
"""
Test script for MVP components - Database, Authentication, and Agent Integration
"""
import asyncio
import json
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "mvp_test@example.com",
    "username": "mvptest",
    "password": "mvptest123",
    "full_name": "MVP Test User"
}

class MVPTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        
    def test_database_connection(self):
        """Test database initialization and connection."""
        print("🔍 Testing Database Connection...")
        try:
            from packages.core.database import init_database, SessionLocal, User
            init_database()
            
            # Test database session
            db = SessionLocal()
            user_count = db.query(User).count()
            db.close()
            
            print(f"✅ Database connected successfully. Users in DB: {user_count}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint."""
        print("🔍 Testing User Registration...")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data["id"]
                print(f"✅ User registered successfully. ID: {self.user_id}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def test_user_login(self):
        """Test user login and JWT token generation."""
        print("🔍 Testing User Login...")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print(f"✅ Login successful. Token expires in: {token_data['expires_in']}s")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def test_authenticated_endpoint(self):
        """Test authenticated endpoint access."""
        print("🔍 Testing Authenticated Endpoint...")
        try:
            response = self.session.get(f"{BASE_URL}/api/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Authenticated access successful. User: {user_data['username']}")
                return True
            else:
                print(f"❌ Authenticated access failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authenticated access error: {e}")
            return False
    
    def test_agent_execution(self):
        """Test agent execution with authentication."""
        print("🔍 Testing Agent Execution...")
        
        agents_to_test = [
            ("code-generator", "Generate a Python hello world function"),
            ("debug-agent", "Debug this error: AttributeError in line 42"),
            ("testing-agent", "Analyze test coverage for my project")
        ]
        
        results = []
        
        for agent_type, task in agents_to_test:
            try:
                print(f"  Testing {agent_type}...")
                response = self.session.post(
                    f"{BASE_URL}/api/agents/{agent_type}/execute",
                    json={
                        "task_description": task,
                        "parameters": {"test": True}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    execution_time = result.get("execution_time", 0)
                    print(f"  ✅ {agent_type} executed successfully in {execution_time}ms")
                    results.append(True)
                else:
                    print(f"  ❌ {agent_type} execution failed: {response.status_code}")
                    results.append(False)
                    
            except Exception as e:
                print(f"  ❌ {agent_type} execution error: {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results) * 100
        print(f"✅ Agent execution success rate: {success_rate:.1f}%")
        return success_rate > 80
    
    def test_project_management(self):
        """Test project creation and management."""
        print("🔍 Testing Project Management...")
        try:
            # Create a project
            project_data = {
                "name": "MVP Test Project",
                "description": "Test project for MVP validation",
                "settings": {"test_mode": True}
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/projects",
                json=project_data
            )
            
            if response.status_code == 200:
                project = response.json()
                project_id = project["id"]
                print(f"✅ Project created successfully. ID: {project_id}")
                
                # List projects
                response = self.session.get(f"{BASE_URL}/api/projects")
                if response.status_code == 200:
                    projects = response.json()
                    print(f"✅ Project listing successful. Total projects: {len(projects)}")
                    return True
                else:
                    print(f"❌ Project listing failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Project creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Project management error: {e}")
            return False
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint."""
        print("🔍 Testing Dashboard Statistics...")
        try:
            response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Dashboard stats retrieved:")
                print(f"  - Total executions: {stats['total_executions']}")
                print(f"  - Successful executions: {stats['successful_executions']}")
                print(f"  - Total projects: {stats['total_projects']}")
                return True
            else:
                print(f"❌ Dashboard stats failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Dashboard stats error: {e}")
            return False
    
    def test_system_health(self):
        """Test system health endpoint."""
        print("🔍 Testing System Health...")
        try:
            response = self.session.get(f"{BASE_URL}/api/system/health")
            
            if response.status_code == 200:
                health = response.json()
                print(f"✅ System health check passed:")
                print(f"  - Status: {health['status']}")
                print(f"  - Memory usage: {health['memory_usage']:.1f}%")
                print(f"  - CPU usage: {health['cpu_usage']:.1f}%")
                return True
            else:
                print(f"❌ System health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ System health error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all MVP tests."""
        print("🚀 Starting MVP Component Tests")
        print("=" * 50)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Authenticated Access", self.test_authenticated_endpoint),
            ("Agent Execution", self.test_agent_execution),
            ("Project Management", self.test_project_management),
            ("Dashboard Statistics", self.test_dashboard_stats),
            ("System Health", self.test_system_health),
        ]
        
        results = []
        start_time = time.time()
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 30)
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"❌ {test_name} ERROR: {e}")
                results.append((test_name, False))
        
        # Summary
        total_time = time.time() - start_time
        passed = sum(1 for _, result in results if result)
        total = len(results)
        success_rate = passed / total * 100
        
        print("\n" + "=" * 50)
        print("🎯 MVP TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        
        print("\nDetailed Results:")
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if success_rate >= 80:
            print("\n🎉 MVP COMPONENTS READY FOR DEPLOYMENT!")
        else:
            print("\n⚠️  MVP needs attention before deployment")
        
        return success_rate >= 80

def main():
    """Main test execution."""
    print("🔧 reVoAgent MVP Component Tester")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    tester = MVPTester()
    success = tester.run_all_tests()
    
    exit_code = 0 if success else 1
    exit(exit_code)

if __name__ == "__main__":
    main()