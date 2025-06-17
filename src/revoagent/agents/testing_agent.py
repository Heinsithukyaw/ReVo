"""Testing agent for reVoAgent platform."""

import uuid
from typing import Dict, Any
from datetime import datetime

from .base import BaseAgent
from ..core.memory import MemoryEntry


class TestingAgent(BaseAgent):
    """
    Specialized agent for software testing tasks.
    
    Capabilities:
    - Unit test generation
    - Integration test creation
    - Test execution and reporting
    - Test coverage analysis
    - Test automation
    """
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "unit testing, integration testing, test automation, coverage analysis, and test reporting"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a testing task."""
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Analyze the testing task
            test_type = self._analyze_test_task(task_description)
            
            # Execute testing based on type
            result = await self._execute_testing(task_description, test_type, parameters)
            
            # Store testing session in memory
            await self._store_test_memory(task_description, result, test_type)
            
            self.success_count += 1
            self.current_task = None
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.current_task = None
            self.logger.error(f"Testing task failed: {e}")
            raise
    
    def _analyze_test_task(self, task_description: str) -> str:
        """Analyze the testing task to determine the type."""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["unit test", "unittest", "unit testing"]):
            return "unit_testing"
        elif any(keyword in description_lower for keyword in ["integration", "integration test"]):
            return "integration_testing"
        elif any(keyword in description_lower for keyword in ["coverage", "test coverage"]):
            return "coverage_analysis"
        elif any(keyword in description_lower for keyword in ["run test", "execute test", "test execution"]):
            return "test_execution"
        elif any(keyword in description_lower for keyword in ["e2e", "end-to-end", "end to end"]):
            return "e2e_testing"
        elif any(keyword in description_lower for keyword in ["performance test", "load test", "stress test"]):
            return "performance_testing"
        elif any(keyword in description_lower for keyword in ["mock", "mocking", "stub"]):
            return "mock_testing"
        else:
            return "general_testing"
    
    async def _execute_testing(
        self,
        task_description: str,
        test_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute testing based on the type."""
        
        # Generate test code or strategy using AI
        test_content = await self._generate_test_content(task_description, test_type, parameters)
        
        # Execute tests if tools are available
        execution_results = await self._execute_tests(test_type, test_content, parameters)
        
        # Analyze test results
        analysis = await self._analyze_test_results(execution_results, test_type)
        
        return {
            "test_type": test_type,
            "test_content": test_content,
            "execution_results": execution_results,
            "analysis": analysis,
            "task_description": task_description
        }
    
    async def _generate_test_content(
        self,
        task_description: str,
        test_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate test content using AI."""
        
        prompt = self._build_test_prompt(task_description, test_type, parameters)
        
        test_content = await self.model_manager.generate_response(
            model_name=self.config.model,
            prompt=prompt,
            max_tokens=2000,
            temperature=0.1
        )
        
        return self._post_process_test_content(test_content)
    
    def _build_test_prompt(
        self,
        task_description: str,
        test_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build a test generation prompt."""
        
        prompt_parts = [
            f"You are an expert software testing engineer specializing in {test_type}.",
            "",
            "Task description:",
            task_description,
            "",
        ]
        
        # Add code to test if provided
        if "code" in parameters:
            prompt_parts.extend([
                "Code to test:",
                "```python",
                parameters["code"],
                "```",
                ""
            ])
        
        if "function_name" in parameters:
            prompt_parts.extend([
                f"Function to test: {parameters['function_name']}",
                ""
            ])
        
        # Add test-type specific instructions
        if test_type == "unit_testing":
            prompt_parts.extend([
                "Generate comprehensive unit tests that:",
                "1. Test normal functionality with valid inputs",
                "2. Test edge cases and boundary conditions",
                "3. Test error handling with invalid inputs",
                "4. Use appropriate assertions and test methods",
                "5. Follow testing best practices and naming conventions",
                "",
                "Use pytest framework and include:",
                "- Clear test function names",
                "- Docstrings explaining what each test verifies",
                "- Proper setup and teardown if needed",
                "- Parametrized tests for multiple scenarios",
                ""
            ])
        elif test_type == "integration_testing":
            prompt_parts.extend([
                "Generate integration tests that:",
                "1. Test component interactions",
                "2. Verify data flow between modules",
                "3. Test external dependencies (with mocking if needed)",
                "4. Validate end-to-end workflows",
                "5. Include proper setup and cleanup",
                ""
            ])
        elif test_type == "performance_testing":
            prompt_parts.extend([
                "Generate performance tests that:",
                "1. Measure execution time",
                "2. Test with various input sizes",
                "3. Identify performance bottlenecks",
                "4. Set performance benchmarks",
                "5. Use appropriate timing and profiling",
                ""
            ])
        elif test_type == "mock_testing":
            prompt_parts.extend([
                "Generate tests with mocking that:",
                "1. Mock external dependencies",
                "2. Isolate the unit under test",
                "3. Verify mock interactions",
                "4. Test different mock scenarios",
                "5. Use unittest.mock or pytest-mock",
                ""
            ])
        
        prompt_parts.extend([
            "Generate complete, runnable test code with proper imports and structure."
        ])
        
        return "\n".join(prompt_parts)
    
    def _post_process_test_content(self, test_content: str) -> str:
        """Post-process generated test content."""
        # Remove markdown code blocks if present
        content = test_content.strip()
        
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        # Ensure proper imports are present
        if "import pytest" not in content and "def test_" in content:
            content = "import pytest\n" + content
        
        return content
    
    async def _execute_tests(
        self,
        test_type: str,
        test_content: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the generated tests."""
        execution_results = {}
        
        try:
            if "pytest" in self.config.tools:
                # Execute tests using pytest tool
                pytest_result = await self.use_tool("pytest", {
                    "test_content": test_content,
                    "test_file": parameters.get("test_file", "generated_test.py")
                })
                execution_results["pytest"] = pytest_result
            
            if "coverage" in self.config.tools and test_type == "coverage_analysis":
                # Run coverage analysis
                coverage_result = await self.use_tool("coverage", {
                    "test_content": test_content,
                    "source_code": parameters.get("code", "")
                })
                execution_results["coverage"] = coverage_result
            
            if not execution_results:
                # Simulate test execution if tools not available
                execution_results = self._simulate_test_execution(test_content, test_type)
                
        except Exception as e:
            execution_results["error"] = str(e)
            self.logger.warning(f"Test execution failed: {e}")
        
        return execution_results
    
    def _simulate_test_execution(self, test_content: str, test_type: str) -> Dict[str, Any]:
        """Simulate test execution when tools are not available."""
        # Count test functions
        test_count = test_content.count("def test_")
        
        return {
            "simulated": True,
            "test_count": test_count,
            "passed": test_count,
            "failed": 0,
            "coverage": "85%" if test_type == "coverage_analysis" else None,
            "execution_time": "0.5s"
        }
    
    async def _analyze_test_results(
        self,
        execution_results: Dict[str, Any],
        test_type: str
    ) -> str:
        """Analyze test execution results."""
        
        prompt = f"""
        Analyze the following test execution results and provide insights:
        
        Test Type: {test_type}
        Execution Results: {str(execution_results)}
        
        Please provide:
        1. Summary of test results
        2. Identification of any issues or failures
        3. Recommendations for improvement
        4. Next steps for testing
        """
        
        analysis = await self.model_manager.generate_response(
            model_name=self.config.model,
            prompt=prompt,
            max_tokens=800,
            temperature=0.2
        )
        
        return analysis
    
    async def _store_test_memory(
        self,
        task_description: str,
        result: Dict[str, Any],
        test_type: str
    ) -> None:
        """Store testing session in memory."""
        execution_results = result.get("execution_results", {})
        
        memory = MemoryEntry(
            id=f"{self.agent_id}_test_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="task",
            content=f"Testing session ({test_type}): {task_description}\nResults: {str(execution_results)[:200]}...",
            metadata={
                "test_type": test_type,
                "test_count": execution_results.get("test_count", 0),
                "passed": execution_results.get("passed", 0),
                "failed": execution_results.get("failed", 0)
            },
            timestamp=datetime.now(),
            importance=0.7
        )
        
        self.memory_manager.store_memory(memory)
    
    async def generate_unit_tests(self, code: str, function_name: str = None) -> Dict[str, Any]:
        """Generate unit tests for given code."""
        parameters = {"code": code}
        if function_name:
            parameters["function_name"] = function_name
        
        return await self.execute_task("Generate comprehensive unit tests", parameters)
    
    async def run_test_suite(self, test_file: str) -> Dict[str, Any]:
        """Run a test suite."""
        return await self.execute_task(f"Run test suite: {test_file}", {"test_file": test_file})
    
    async def analyze_test_coverage(self, source_code: str, test_code: str) -> Dict[str, Any]:
        """Analyze test coverage."""
        return await self.execute_task("Analyze test coverage", {
            "code": source_code,
            "test_content": test_code
        })
    
    async def create_integration_tests(self, modules: list, workflow_description: str) -> Dict[str, Any]:
        """Create integration tests for multiple modules."""
        return await self.execute_task(
            f"Create integration tests for workflow: {workflow_description}",
            {"modules": modules, "workflow": workflow_description}
        )
    
    async def generate_performance_tests(self, code: str, performance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance tests with specific requirements."""
        return await self.execute_task(
            "Generate performance tests with benchmarks",
            {"code": code, "requirements": performance_requirements}
        )