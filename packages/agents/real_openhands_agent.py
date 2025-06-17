#!/usr/bin/env python3
"""
Real OpenHands Agent Implementation
Specialized AI agent for testing, automation, deployment, and DevOps tasks
"""

import asyncio
import uuid
import time
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.packages.ai.real_model_manager import RealModelManager, RealGenerationRequest, ModelType

logger = logging.getLogger(__name__)

@dataclass
class AutomationTask:
    """Task for automation and testing"""
    task_id: str
    title: str
    description: str
    task_type: str = "testing"  # testing, deployment, monitoring, automation
    target_code: Optional[str] = None
    target_system: Optional[str] = None
    test_framework: str = "pytest"
    environment: str = "development"
    requirements: List[str] = field(default_factory=list)
    context: Optional[str] = None
    deadline: Optional[datetime] = None

@dataclass
class AutomationResult:
    """Result of automation task"""
    task_id: str
    agent_id: str
    task_type: str
    artifacts: Dict[str, str]  # Generated files/scripts
    execution_results: Dict[str, Any]
    test_results: Optional[Dict[str, Any]] = None
    success_rate: float = 0.0
    execution_time: float = 0.0
    cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealOpenHandsAgent:
    """Real OpenHands Agent for automation and testing"""
    
    def __init__(self, model_manager: RealModelManager, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"openhands-{uuid.uuid4().hex[:8]}"
        self.model_manager = model_manager
        self.specialties = [
            "test_automation",
            "unit_testing",
            "integration_testing",
            "deployment_automation",
            "ci_cd_pipeline",
            "monitoring_setup",
            "infrastructure_automation",
            "docker_containerization",
            "kubernetes_deployment",
            "performance_testing"
        ]
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 1.0,
            "tests_generated": 0,
            "tests_passed": 0,
            "average_response_time": 0.0,
            "total_cost": 0.0,
            "automation_scripts_created": 0
        }
        self.is_busy = False
        self.current_task: Optional[str] = None
        self.temp_dir = tempfile.mkdtemp(prefix="openhands_")
        
    async def execute_automation_task(self, task: AutomationTask) -> AutomationResult:
        """Execute automation task"""
        start_time = time.time()
        self.is_busy = True
        self.current_task = task.task_id
        
        try:
            logger.info(f"🤖 {self.agent_id} starting {task.task_type} task: {task.title}")
            
            if task.task_type == "testing":
                return await self._generate_tests(task, start_time)
            elif task.task_type == "deployment":
                return await self._create_deployment_automation(task, start_time)
            elif task.task_type == "monitoring":
                return await self._setup_monitoring(task, start_time)
            elif task.task_type == "automation":
                return await self._create_automation_scripts(task, start_time)
            else:
                return await self._general_automation(task, start_time)
                
        except Exception as e:
            logger.error(f"❌ {self.agent_id} automation task failed: {e}")
            return AutomationResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                task_type=task.task_type,
                artifacts={},
                execution_results={},
                success_rate=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                success=False,
                error_message=str(e)
            )
        finally:
            self.is_busy = False
            self.current_task = None
    
    async def _generate_tests(self, task: AutomationTask, start_time: float) -> AutomationResult:
        """Generate comprehensive test suite"""
        
        # Create test generation prompt
        prompt = self._create_test_generation_prompt(task)
        
        # Generate tests using AI
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.DEEPSEEK_R1,  # Use local model for cost efficiency
            max_tokens=2000,
            temperature=0.3,
            system_prompt=self._get_testing_system_prompt(task.test_framework),
            context=task.context,
            task_type="test_generation"
        )
        
        response = await self.model_manager.generate_response(request)
        
        if not response.success:
            raise Exception(response.error_message or "Test generation failed")
        
        # Parse generated tests
        test_files = self._parse_test_files(response.content, task.test_framework)
        
        # Execute tests if possible
        test_results = await self._execute_tests(test_files, task.test_framework)
        
        # Calculate success rate
        success_rate = self._calculate_test_success_rate(test_results)
        
        # Update metrics
        self.performance_metrics["tests_generated"] += len(test_files)
        if test_results:
            self.performance_metrics["tests_passed"] += test_results.get("passed", 0)
        
        return AutomationResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_type="testing",
            artifacts=test_files,
            execution_results=test_results or {},
            test_results=test_results,
            success_rate=success_rate,
            execution_time=time.time() - start_time,
            cost=response.cost,
            success=True,
            metadata={
                "model_used": response.model_used.value,
                "test_framework": task.test_framework,
                "tests_count": len(test_files)
            }
        )
    
    async def _create_deployment_automation(self, task: AutomationTask, start_time: float) -> AutomationResult:
        """Create deployment automation scripts"""
        
        prompt = f"""
Create comprehensive deployment automation for the following system:

**System**: {task.title}
**Description**: {task.description}
**Environment**: {task.environment}
**Requirements**: {', '.join(task.requirements)}

Generate the following deployment artifacts:

1. **Dockerfile** - Container configuration
2. **docker-compose.yml** - Multi-service orchestration
3. **deploy.sh** - Deployment script
4. **kubernetes.yaml** - Kubernetes deployment (if applicable)
5. **CI/CD Pipeline** - GitHub Actions or similar

**Include**:
- Environment variable configuration
- Health checks and monitoring
- Rollback procedures
- Security best practices
- Documentation

**Output each file separately with clear headers.**
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.CLAUDE_SONNET,  # Use Claude for complex automation
            max_tokens=2500,
            temperature=0.2,
            system_prompt="You are a DevOps expert specializing in deployment automation, containerization, and CI/CD pipelines.",
            context=task.context,
            task_type="deployment_automation"
        )
        
        response = await self.model_manager.generate_response(request)
        
        if not response.success:
            raise Exception(response.error_message or "Deployment automation generation failed")
        
        # Parse deployment files
        deployment_files = self._parse_deployment_files(response.content)
        
        # Validate deployment files
        validation_results = await self._validate_deployment_files(deployment_files)
        
        return AutomationResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_type="deployment",
            artifacts=deployment_files,
            execution_results=validation_results,
            success_rate=validation_results.get("validation_score", 0.8),
            execution_time=time.time() - start_time,
            cost=response.cost,
            success=True,
            metadata={
                "model_used": response.model_used.value,
                "environment": task.environment,
                "files_generated": len(deployment_files)
            }
        )
    
    async def _setup_monitoring(self, task: AutomationTask, start_time: float) -> AutomationResult:
        """Setup monitoring and alerting"""
        
        prompt = f"""
Create comprehensive monitoring setup for:

**System**: {task.title}
**Description**: {task.description}
**Environment**: {task.environment}

Generate monitoring configuration including:

1. **Prometheus Configuration** - Metrics collection
2. **Grafana Dashboard** - Visualization
3. **Alert Rules** - Critical alerts
4. **Health Check Scripts** - System health monitoring
5. **Log Aggregation** - Centralized logging setup

**Key Metrics to Monitor**:
- Application performance (response time, throughput)
- System resources (CPU, memory, disk)
- Error rates and exceptions
- Business metrics (if applicable)
- Security events

**Include**:
- Alert thresholds and escalation
- Dashboard layouts and visualizations
- Log parsing and analysis
- Automated remediation scripts
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.GEMINI_PRO,  # Use Gemini for monitoring analysis
            max_tokens=2000,
            temperature=0.2,
            system_prompt="You are a monitoring and observability expert specializing in Prometheus, Grafana, and alerting systems.",
            context=task.context,
            task_type="monitoring_setup"
        )
        
        response = await self.model_manager.generate_response(request)
        
        if not response.success:
            raise Exception(response.error_message or "Monitoring setup generation failed")
        
        # Parse monitoring files
        monitoring_files = self._parse_monitoring_files(response.content)
        
        return AutomationResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_type="monitoring",
            artifacts=monitoring_files,
            execution_results={"monitoring_components": len(monitoring_files)},
            success_rate=0.9,  # High confidence for monitoring setup
            execution_time=time.time() - start_time,
            cost=response.cost,
            success=True,
            metadata={
                "model_used": response.model_used.value,
                "monitoring_type": "comprehensive"
            }
        )
    
    async def _create_automation_scripts(self, task: AutomationTask, start_time: float) -> AutomationResult:
        """Create general automation scripts"""
        
        prompt = f"""
Create automation scripts for:

**Task**: {task.title}
**Description**: {task.description}
**Requirements**: {', '.join(task.requirements)}

Generate automation scripts including:

1. **Main Script** - Primary automation logic
2. **Configuration** - Settings and parameters
3. **Error Handling** - Robust error management
4. **Logging** - Comprehensive logging
5. **Documentation** - Usage instructions

**Script Requirements**:
- Idempotent operations (safe to run multiple times)
- Comprehensive error handling and rollback
- Detailed logging and progress reporting
- Configuration validation
- Security best practices

**Include examples and usage instructions.**
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.DEEPSEEK_R1,  # Use local model for scripts
            max_tokens=1800,
            temperature=0.3,
            system_prompt="You are an automation expert specializing in robust, production-ready scripts and tools.",
            context=task.context,
            task_type="automation"
        )
        
        response = await self.model_manager.generate_response(request)
        
        if not response.success:
            raise Exception(response.error_message or "Automation script generation failed")
        
        # Parse automation files
        automation_files = self._parse_automation_files(response.content)
        
        # Update metrics
        self.performance_metrics["automation_scripts_created"] += len(automation_files)
        
        return AutomationResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_type="automation",
            artifacts=automation_files,
            execution_results={"scripts_generated": len(automation_files)},
            success_rate=0.85,
            execution_time=time.time() - start_time,
            cost=response.cost,
            success=True,
            metadata={
                "model_used": response.model_used.value,
                "script_type": "general_automation"
            }
        )
    
    async def _general_automation(self, task: AutomationTask, start_time: float) -> AutomationResult:
        """Handle general automation tasks"""
        
        prompt = f"""
Create automation solution for:

**Task**: {task.title}
**Type**: {task.task_type}
**Description**: {task.description}
**Requirements**: {', '.join(task.requirements)}

Provide a comprehensive automation solution including:
- Implementation approach
- Required tools and technologies
- Step-by-step automation process
- Configuration files
- Testing and validation procedures
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.CLAUDE_SONNET,
            max_tokens=1500,
            temperature=0.3,
            system_prompt="You are a versatile automation expert capable of creating solutions for various automation challenges.",
            context=task.context,
            task_type="general_automation"
        )
        
        response = await self.model_manager.generate_response(request)
        
        if not response.success:
            raise Exception(response.error_message or "General automation failed")
        
        return AutomationResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_type=task.task_type,
            artifacts={"solution": response.content},
            execution_results={"solution_provided": True},
            success_rate=0.8,
            execution_time=time.time() - start_time,
            cost=response.cost,
            success=True,
            metadata={
                "model_used": response.model_used.value,
                "solution_type": "general"
            }
        )
    
    def _create_test_generation_prompt(self, task: AutomationTask) -> str:
        """Create prompt for test generation"""
        prompt = f"""
Generate comprehensive {task.test_framework} tests for the following code:

**Code to Test**:
```
{task.target_code or "No specific code provided - generate example tests"}
```

**Test Requirements**:
"""
        for req in task.requirements:
            prompt += f"- {req}\n"
        
        prompt += f"""

**Generate the following test types**:
1. **Unit Tests** - Test individual functions/methods
2. **Integration Tests** - Test component interactions
3. **Edge Case Tests** - Test boundary conditions and error cases
4. **Performance Tests** - Basic performance validation
5. **Mock Tests** - Test with mocked dependencies

**Test Framework**: {task.test_framework}

**Requirements**:
- Comprehensive test coverage
- Clear test names and descriptions
- Proper setup and teardown
- Assertion messages
- Test data and fixtures
- Error case testing

**Output Format**:
Provide each test file with clear headers and explanations.
"""
        return prompt
    
    def _get_testing_system_prompt(self, framework: str) -> str:
        """Get system prompt for testing"""
        base_prompt = """You are a test automation expert with extensive experience in:

- Test-driven development (TDD)
- Behavior-driven development (BDD)
- Unit, integration, and end-to-end testing
- Test automation frameworks and tools
- Mock and stub creation
- Performance and load testing
- Continuous integration testing

You write comprehensive, maintainable tests that provide excellent coverage and catch edge cases."""
        
        framework_specific = {
            "pytest": """
You specialize in pytest and Python testing. You know:
- Pytest fixtures and parametrization
- Pytest plugins and extensions
- Mock and patch techniques
- Async testing with pytest-asyncio
- Property-based testing with hypothesis
- Test organization and best practices
""",
            "jest": """
You specialize in Jest and JavaScript testing. You know:
- Jest matchers and assertions
- Mock functions and modules
- Snapshot testing
- Async testing with promises
- React Testing Library integration
- Test setup and configuration
""",
            "unittest": """
You specialize in Python unittest framework. You know:
- TestCase classes and methods
- setUp and tearDown methods
- Mock and patch decorators
- Test discovery and organization
- Assertion methods and custom assertions
"""
        }
        
        return base_prompt + framework_specific.get(framework, "")
    
    def _parse_test_files(self, content: str, framework: str) -> Dict[str, str]:
        """Parse generated test files"""
        import re
        
        files = {}
        
        # Look for file headers or code blocks
        if framework == "pytest":
            # Extract Python test files
            test_pattern = r'```python(.*?)```'
            matches = re.findall(test_pattern, content, re.DOTALL)
            
            for i, match in enumerate(matches):
                filename = f"test_{i+1}.py"
                files[filename] = match.strip()
        
        elif framework == "jest":
            # Extract JavaScript test files
            test_pattern = r'```(?:javascript|js)(.*?)```'
            matches = re.findall(test_pattern, content, re.DOTALL)
            
            for i, match in enumerate(matches):
                filename = f"test_{i+1}.test.js"
                files[filename] = match.strip()
        
        # If no specific patterns found, create a single test file
        if not files:
            files["generated_tests.py"] = content
        
        return files
    
    def _parse_deployment_files(self, content: str) -> Dict[str, str]:
        """Parse deployment files from generated content"""
        import re
        
        files = {}
        
        # Common deployment file patterns
        file_patterns = {
            "Dockerfile": r'```dockerfile(.*?)```',
            "docker-compose.yml": r'```(?:yaml|yml)(.*?)```',
            "deploy.sh": r'```(?:bash|shell)(.*?)```',
            "kubernetes.yaml": r'```(?:yaml|yml)(.*?)```'
        }
        
        for filename, pattern in file_patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                files[filename] = matches[0].strip()
        
        # Extract any other code blocks
        general_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(general_pattern, content, re.DOTALL)
        
        for i, (lang, code) in enumerate(matches):
            if not any(code.strip() in existing for existing in files.values()):
                filename = f"deployment_file_{i+1}.{lang or 'txt'}"
                files[filename] = code.strip()
        
        return files
    
    def _parse_monitoring_files(self, content: str) -> Dict[str, str]:
        """Parse monitoring configuration files"""
        import re
        
        files = {}
        
        # Monitoring file patterns
        patterns = {
            "prometheus.yml": r'```(?:yaml|yml)(.*?)```',
            "grafana-dashboard.json": r'```json(.*?)```',
            "alert-rules.yml": r'```(?:yaml|yml)(.*?)```',
            "health-check.sh": r'```(?:bash|shell)(.*?)```'
        }
        
        for filename, pattern in patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                files[filename] = matches[0].strip()
        
        return files
    
    def _parse_automation_files(self, content: str) -> Dict[str, str]:
        """Parse automation script files"""
        import re
        
        files = {}
        
        # Script patterns
        patterns = {
            "automation.py": r'```python(.*?)```',
            "automation.sh": r'```(?:bash|shell)(.*?)```',
            "config.yaml": r'```(?:yaml|yml)(.*?)```',
            "README.md": r'```(?:markdown|md)(.*?)```'
        }
        
        for filename, pattern in patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                files[filename] = matches[0].strip()
        
        return files
    
    async def _execute_tests(self, test_files: Dict[str, str], framework: str) -> Optional[Dict[str, Any]]:
        """Execute generated tests"""
        if not test_files:
            return None
        
        try:
            # Create temporary test files
            test_dir = os.path.join(self.temp_dir, "tests")
            os.makedirs(test_dir, exist_ok=True)
            
            for filename, content in test_files.items():
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
            
            # Execute tests based on framework
            if framework == "pytest":
                result = subprocess.run(
                    ["python", "-m", "pytest", test_dir, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif framework == "unittest":
                result = subprocess.run(
                    ["python", "-m", "unittest", "discover", test_dir],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # For other frameworks, just validate syntax
                result = subprocess.run(
                    ["python", "-m", "py_compile"] + [os.path.join(test_dir, f) for f in test_files.keys()],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            # Parse test results
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0,
                "test_count": len(test_files)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test execution timeout",
                "passed": False,
                "test_count": len(test_files)
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "passed": False,
                "test_count": len(test_files)
            }
    
    async def _validate_deployment_files(self, deployment_files: Dict[str, str]) -> Dict[str, Any]:
        """Validate deployment files"""
        validation_results = {
            "valid_files": 0,
            "total_files": len(deployment_files),
            "validation_score": 0.0,
            "issues": []
        }
        
        for filename, content in deployment_files.items():
            if self._validate_file_content(filename, content):
                validation_results["valid_files"] += 1
            else:
                validation_results["issues"].append(f"Invalid content in {filename}")
        
        if validation_results["total_files"] > 0:
            validation_results["validation_score"] = validation_results["valid_files"] / validation_results["total_files"]
        
        return validation_results
    
    def _validate_file_content(self, filename: str, content: str) -> bool:
        """Basic validation of file content"""
        if not content or len(content.strip()) < 10:
            return False
        
        # Basic syntax checks based on file type
        if filename.endswith('.py'):
            try:
                compile(content, filename, 'exec')
                return True
            except SyntaxError:
                return False
        elif filename.endswith(('.yml', '.yaml')):
            try:
                import yaml
                yaml.safe_load(content)
                return True
            except:
                return False
        elif filename.endswith('.json'):
            try:
                import json
                json.loads(content)
                return True
            except:
                return False
        
        return True  # Default to valid for other file types
    
    def _calculate_test_success_rate(self, test_results: Optional[Dict[str, Any]]) -> float:
        """Calculate test success rate"""
        if not test_results:
            return 0.0
        
        if test_results.get("passed", False):
            return 1.0
        elif test_results.get("exit_code", -1) == 0:
            return 0.8
        else:
            return 0.3  # Partial credit for generating tests even if they don't pass
    
    async def _update_performance_metrics(self, result: AutomationResult):
        """Update agent performance metrics"""
        self.performance_metrics["tasks_completed"] += 1
        self.performance_metrics["total_cost"] += result.cost
        
        # Update success rate
        current_success_rate = self.performance_metrics["success_rate"]
        tasks_completed = self.performance_metrics["tasks_completed"]
        
        if result.success:
            self.performance_metrics["success_rate"] = (
                (current_success_rate * (tasks_completed - 1) + 1.0) / tasks_completed
            )
        else:
            self.performance_metrics["success_rate"] = (
                (current_success_rate * (tasks_completed - 1) + 0.0) / tasks_completed
            )
        
        # Update average response time
        current_avg_time = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg_time * (tasks_completed - 1) + result.execution_time) / tasks_completed
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "specialties": self.specialties,
            "is_busy": self.is_busy,
            "current_task": self.current_task,
            "performance_metrics": self.performance_metrics.copy()
        }
    
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "Test automation and generation",
            "Unit and integration testing",
            "Deployment automation",
            "CI/CD pipeline creation",
            "Monitoring and alerting setup",
            "Infrastructure automation",
            "Docker containerization",
            "Kubernetes deployment",
            "Performance testing",
            "DevOps best practices"
        ]
    
    def cleanup(self):
        """Cleanup temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass


# Factory function for easy agent creation
async def create_openhands_agent(model_manager: RealModelManager) -> RealOpenHandsAgent:
    """Create a new OpenHands agent"""
    agent = RealOpenHandsAgent(model_manager)
    logger.info(f"🛠️ Created OpenHands agent: {agent.agent_id}")
    return agent


if __name__ == "__main__":
    # Test the OpenHands agent
    async def test_openhands_agent():
        from src.packages.ai.real_model_manager import create_real_model_manager
        
        # Create model manager and agent
        model_manager = await create_real_model_manager()
        agent = await create_openhands_agent(model_manager)
        
        # Test test generation
        test_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
"""
        
        task = AutomationTask(
            task_id="test_001",
            title="Generate Test Suite",
            description="Create comprehensive tests for utility functions",
            task_type="testing",
            target_code=test_code,
            test_framework="pytest",
            requirements=[
                "Test edge cases and error conditions",
                "Include performance tests",
                "Add mock tests where appropriate",
                "Ensure high test coverage"
            ]
        )
        
        result = await agent.execute_automation_task(task)
        
        print(f"✅ Automation result:")
        print(f"📝 Success: {result.success}")
        print(f"🎯 Success Rate: {result.success_rate:.2f}")
        print(f"💰 Cost: ${result.cost:.6f}")
        print(f"⏱️ Time: {result.execution_time:.2f}s")
        print(f"📄 Artifacts: {list(result.artifacts.keys())}")
        print(f"🧪 Test Results: {result.test_results}")
        
        # Show generated test file
        if result.artifacts:
            first_file = list(result.artifacts.keys())[0]
            print(f"\n📋 Generated {first_file}:")
            print(result.artifacts[first_file][:500] + "..." if len(result.artifacts[first_file]) > 500 else result.artifacts[first_file])
        
        agent.cleanup()
        await model_manager.shutdown()
    
    asyncio.run(test_openhands_agent())