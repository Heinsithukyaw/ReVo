#!/usr/bin/env python3
"""
Test script to verify frontend and backend are working correctly.
"""

import requests
import json
import sys

def test_backend():
    """Test backend API endpoints."""
    print("🧪 Testing Backend API...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:12000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test dashboard stats
        response = requests.get("http://localhost:12000/api/v1/dashboard/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dashboard stats: {data['active_agents']} agents, {data['running_workflows']} workflows")
        else:
            print(f"❌ Dashboard stats failed: {response.status_code}")
            return False
        
        # Test agents endpoint
        response = requests.get("http://localhost:12000/api/v1/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agents endpoint: {len(data['agents'])} agents available")
        else:
            print(f"❌ Agents endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def test_frontend():
    """Test frontend is serving correctly."""
    print("\n🧪 Testing Frontend...")
    
    try:
        # Test main dashboard page
        response = requests.get("http://localhost:12000/")
        if response.status_code == 200 and "reVoAgent Dashboard" in response.text:
            print("✅ Frontend dashboard serving correctly")
            return True
        else:
            print(f"❌ Frontend test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 reVoAgent Frontend/Backend Integration Test")
    print("=" * 50)
    
    backend_ok = test_backend()
    frontend_ok = test_frontend()
    
    print("\n" + "=" * 50)
    if backend_ok and frontend_ok:
        print("🎉 All tests passed! reVoAgent is fully operational!")
        print("\n📍 Access URLs:")
        print("🌐 Main Dashboard: https://work-1-stxiiyanqybjissk.prod-runtime.all-hands.dev")
        print("🔧 Backend API: https://work-1-stxiiyanqybjissk.prod-runtime.all-hands.dev/api/v1/")
        print("💻 Local Backend: http://localhost:12000")
        print("\n🎯 Features Available:")
        print("• Revolutionary AI Agents Dashboard")
        print("• Real-time System Monitoring")
        print("• Multi-Agent Workflow Management")
        print("• Model Registry & Performance Tracking")
        print("• OpenHands Integration")
        print("• Zero-cost Local Infrastructure")
        return 0
    else:
        print("❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())