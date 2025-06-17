#!/usr/bin/env python3
"""
Critical Fixes Validation Test Suite
Tests all the architectural fixes implemented for reVoAgent
"""

import os
import sys
import yaml
import json
import time
import subprocess
import requests
from pathlib import Path

class CriticalFixesValidator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results = {
            'port_management': False,
            'backend_consolidation': False,
            'configuration_unified': False,
            'documentation_organized': False,
            'startup_script': False,
            'api_endpoints': False,
            'frontend_integration': False
        }
        
    def test_port_configuration(self):
        """Test unified port configuration"""
        print("🔧 Testing Port Configuration...")
        try:
            ports_file = self.base_dir / 'config' / 'ports.yaml'
            if not ports_file.exists():
                print("❌ ports.yaml not found")
                return False
                
            with open(ports_file) as f:
                ports = yaml.safe_load(f)
                
            # Check required sections
            required_sections = ['production', 'development', 'infrastructure']
            for section in required_sections:
                if section not in ports:
                    print(f"❌ Missing section: {section}")
                    return False
                    
            # Check production ports
            prod_ports = ports['production']
            if prod_ports.get('backend') != 12001:
                print(f"❌ Backend port should be 12001, got {prod_ports.get('backend')}")
                return False
                
            if prod_ports.get('frontend') != 12000:
                print(f"❌ Frontend port should be 12000, got {prod_ports.get('frontend')}")
                return False
                
            print("✅ Port configuration is valid")
            self.results['port_management'] = True
            return True
            
        except Exception as e:
            print(f"❌ Port configuration test failed: {e}")
            return False
            
    def test_backend_consolidation(self):
        """Test consolidated backend"""
        print("🔧 Testing Backend Consolidation...")
        try:
            backend_file = self.base_dir / 'backend_main.py'
            if not backend_file.exists():
                print("❌ backend_main.py not found")
                return False
                
            with open(backend_file) as f:
                content = f.read()
                
            # Check for required components
            required_components = [
                'FastAPI',
                'uvicorn',
                '/health',
                '/api/chat',
                '/api/models',
                'WebSocket'
            ]
            
            for component in required_components:
                if component not in content:
                    print(f"❌ Missing component: {component}")
                    return False
                    
            print("✅ Backend consolidation is valid")
            self.results['backend_consolidation'] = True
            return True
            
        except Exception as e:
            print(f"❌ Backend consolidation test failed: {e}")
            return False
            
    def test_configuration_unified(self):
        """Test unified configuration system"""
        print("🔧 Testing Configuration Unification...")
        try:
            config_dir = self.base_dir / 'config'
            if not config_dir.exists():
                print("❌ config directory not found")
                return False
                
            required_configs = ['ports.yaml', 'environment.yaml']
            for config in required_configs:
                config_file = config_dir / config
                if not config_file.exists():
                    print(f"❌ Missing config file: {config}")
                    return False
                    
                # Test YAML parsing
                with open(config_file) as f:
                    yaml.safe_load(f)
                    
            print("✅ Configuration unification is valid")
            self.results['configuration_unified'] = True
            return True
            
        except Exception as e:
            print(f"❌ Configuration unification test failed: {e}")
            return False
            
    def test_documentation_organization(self):
        """Test documentation organization"""
        print("🔧 Testing Documentation Organization...")
        try:
            docs_dir = self.base_dir / 'docs'
            if not docs_dir.exists():
                print("❌ docs directory not found")
                return False
                
            required_subdirs = ['guides', 'reports', 'implementation', 'deployment', 'archive']
            for subdir in required_subdirs:
                subdir_path = docs_dir / subdir
                if not subdir_path.exists():
                    print(f"❌ Missing docs subdirectory: {subdir}")
                    return False
                    
            # Check that root directory is clean of markdown files
            root_md_files = list(self.base_dir.glob('*.md'))
            if len(root_md_files) > 2:  # Allow README.md and maybe one more
                print(f"❌ Too many markdown files in root: {len(root_md_files)}")
                return False
                
            print("✅ Documentation organization is valid")
            self.results['documentation_organized'] = True
            return True
            
        except Exception as e:
            print(f"❌ Documentation organization test failed: {e}")
            return False
            
    def test_startup_script(self):
        """Test consolidated startup script"""
        print("🔧 Testing Startup Script...")
        try:
            startup_script = self.base_dir / 'start_consolidated.sh'
            if not startup_script.exists():
                print("❌ start_consolidated.sh not found")
                return False
                
            # Check if script is executable
            if not os.access(startup_script, os.X_OK):
                print("❌ start_consolidated.sh is not executable")
                return False
                
            with open(startup_script) as f:
                content = f.read()
                
            # Check for required components
            required_components = [
                'cleanup_ports.sh',
                'backend_main.py',
                'npm run dev',
                'health check',
                'monitoring'
            ]
            
            for component in required_components:
                if component not in content:
                    print(f"❌ Missing startup component: {component}")
                    return False
                    
            print("✅ Startup script is valid")
            self.results['startup_script'] = True
            return True
            
        except Exception as e:
            print(f"❌ Startup script test failed: {e}")
            return False
            
    def test_api_endpoints_structure(self):
        """Test API endpoints structure (without running server)"""
        print("🔧 Testing API Endpoints Structure...")
        try:
            backend_file = self.base_dir / 'backend_main.py'
            with open(backend_file) as f:
                content = f.read()
                
            # Check for required API endpoints
            required_endpoints = [
                '/health',
                '/api/models',
                '/api/chat',
                '@app.websocket'
            ]
            
            for endpoint in required_endpoints:
                if endpoint not in content:
                    print(f"❌ Missing API endpoint: {endpoint}")
                    return False
                    
            print("✅ API endpoints structure is valid")
            self.results['api_endpoints'] = True
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test failed: {e}")
            return False
            
    def test_frontend_integration(self):
        """Test frontend integration setup"""
        print("🔧 Testing Frontend Integration...")
        try:
            frontend_dir = self.base_dir / 'frontend'
            if not frontend_dir.exists():
                print("❌ frontend directory not found")
                return False
                
            # Check package.json
            package_json = frontend_dir / 'package.json'
            if not package_json.exists():
                print("❌ package.json not found")
                return False
                
            with open(package_json) as f:
                package_data = json.load(f)
                
            # Check required scripts
            scripts = package_data.get('scripts', {})
            if 'dev' not in scripts:
                print("❌ Missing dev script in package.json")
                return False
                
            # Check vite config
            vite_config = frontend_dir / 'vite.config.ts'
            if not vite_config.exists():
                print("❌ vite.config.ts not found")
                return False
                
            with open(vite_config) as f:
                vite_content = f.read()
                
            if 'port: 12000' not in vite_content:
                print("❌ Frontend not configured for port 12000")
                return False
                
            print("✅ Frontend integration is valid")
            self.results['frontend_integration'] = True
            return True
            
        except Exception as e:
            print(f"❌ Frontend integration test failed: {e}")
            return False
            
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Running Critical Fixes Validation Suite")
        print("=" * 60)
        
        tests = [
            self.test_port_configuration,
            self.test_backend_consolidation,
            self.test_configuration_unified,
            self.test_documentation_organization,
            self.test_startup_script,
            self.test_api_endpoints_structure,
            self.test_frontend_integration
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                print()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                print()
                
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
            print("\n✅ Architecture conflicts resolved")
            print("✅ Port conflicts eliminated")
            print("✅ Backend consolidation complete")
            print("✅ Configuration unified")
            print("✅ Documentation organized")
            print("✅ Integration issues fixed")
            return True
        else:
            print("❌ Some critical fixes need attention")
            failed_tests = [k for k, v in self.results.items() if not v]
            print(f"Failed areas: {', '.join(failed_tests)}")
            return False
            
    def generate_report(self):
        """Generate detailed validation report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'validation_results': self.results,
            'overall_status': all(self.results.values()),
            'fixes_implemented': [
                'Unified port configuration (config/ports.yaml)',
                'Consolidated backend (backend_main.py)',
                'Unified environment config (config/environment.yaml)',
                'Organized documentation (docs/ structure)',
                'Enhanced startup script (start_consolidated.sh)',
                'Standardized API endpoints',
                'Fixed frontend integration'
            ]
        }
        
        report_file = self.base_dir / 'validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📄 Detailed report saved to: {report_file}")
        return report

if __name__ == "__main__":
    validator = CriticalFixesValidator()
    success = validator.run_all_tests()
    validator.generate_report()
    
    sys.exit(0 if success else 1)