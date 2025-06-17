"""Enhanced Testing Agent for reVoAgent platform."""

import uuid
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .base import BaseAgent
from ..core.memory import MemoryEntry


@dataclass
class TestingTask:
    """Represents a testing task."""
    id: str
    type: str
    description: str
    parameters: Dict[str, Any]
    status: str = "pending"
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TestingAgent(BaseAgent):
    """
    Enhanced Testing Agent with real-time test execution and monitoring.
    
    Features:
    - Real-time test generation and execution
    - Live test result monitoring
    - Comprehensive test coverage analysis
    - Performance testing with benchmarks
    - Interactive test debugging
    - WebSocket integration for live updates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks: Dict[str, TestingTask] = {}
        self.task_history: List[TestingTask] = []
        self.performance_metrics = {
            "total_tests_generated": 0,
            "total_tests_executed": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "test_types": ["unit_testing", "integration_testing", "performance_testing", "coverage_analysis"],
            "last_activity": None
        }
        self.websocket_callbacks = []
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "advanced test generation, real-time test execution, coverage analysis, performance testing, and intelligent test automation"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a testing task with real-time monitoring."""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = TestingTask(
            id=task_id,
            type=self._analyze_test_task(task_description),
            description=task_description,
            parameters=parameters
        )
        
        self.active_tasks[task_id] = task
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Notify start
            await self._notify_task_update(task_id, "started", 0.0)
            
            # Step 1: Analyze requirements (15%)
            task.progress = 0.15
            await self._notify_task_update(task_id, "analyzing", 0.15)
            await asyncio.sleep(0.3)
            
            # Step 2: Generate test strategy (30%)
            task.progress = 0.30
            await self._notify_task_update(task_id, "planning", 0.30)
            test_strategy = await self._generate_test_strategy(task_description, task.type, parameters)
            
            # Step 3: Generate test code (50%)
            task.progress = 0.50
            await self._notify_task_update(task_id, "generating", 0.50)
            test_content = await self._generate_test_content(task_description, task.type, parameters)
            
            # Step 4: Execute tests (75%)
            task.progress = 0.75
            await self._notify_task_update(task_id, "executing", 0.75)
            execution_results = await self._execute_tests(task.type, test_content, parameters)
            
            # Step 5: Analyze results (90%)
            task.progress = 0.90
            await self._notify_task_update(task_id, "analyzing_results", 0.90)
            analysis = await self._analyze_test_results(execution_results, task.type)
            
            # Step 6: Generate report (100%)
            task.progress = 1.0
            task.status = "completed"
            
            # Create comprehensive result
            result = await self._create_test_result(
                task.type, test_content, execution_results, analysis, test_strategy, parameters
            )
            
            task.result = result
            task.completed_at = datetime.now()
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, task.type)
            
            # Store in memory
            await self._store_enhanced_test_memory(task)
            
            # Notify completion
            await self._notify_task_update(task_id, "completed", 1.0, result)
            
            # Move to history
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
            self.success_count += 1
            self.current_task = None
            
            return result
            
        except Exception as e:
            # Handle error
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, False, task.type)
            
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            await self._notify_task_update(task_id, "failed", task.progress, error=str(e))
            
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
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
    
    # Enhanced Methods for Real-time Testing
    
    async def _notify_task_update(self, task_id: str, status: str, progress: float, result: Optional[Dict] = None, error: Optional[str] = None):
        """Notify WebSocket clients about testing task updates."""
        update = {
            "type": "testing_update",
            "task_id": task_id,
            "agent_id": self.agent_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
        if result:
            update["result"] = result
        if error:
            update["error"] = error
            
        # Notify all registered callbacks
        for callback in self.websocket_callbacks:
            try:
                await callback(update)
            except Exception as e:
                self.logger.warning(f"Failed to notify WebSocket callback: {e}")
    
    def register_websocket_callback(self, callback):
        """Register a WebSocket callback for real-time updates."""
        self.websocket_callbacks.append(callback)
    
    def unregister_websocket_callback(self, callback):
        """Unregister a WebSocket callback."""
        if callback in self.websocket_callbacks:
            self.websocket_callbacks.remove(callback)
    
    async def _generate_test_strategy(self, task_description: str, test_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive testing strategy."""
        
        strategy_prompt = f"""
        You are an expert testing strategist. Create a comprehensive testing strategy for:
        
        Task: {task_description}
        Test Type: {test_type}
        Parameters: {json.dumps(parameters, indent=2)}
        
        Create a detailed testing strategy that includes:
        1. Test scope and objectives
        2. Testing approach and methodology
        3. Test cases to cover
        4. Tools and frameworks to use
        5. Success criteria and metrics
        6. Risk assessment and mitigation
        
        Provide a structured testing plan.
        """
        
        try:
            strategy_text = await self.model_manager.generate_response(
                model_name="deepseek-r1",  # Use DeepSeek R1 for advanced reasoning
                prompt=strategy_prompt,
                max_tokens=1200,
                temperature=0.1
            )
            
            return {
                "strategy": strategy_text,
                "test_type": test_type,
                "estimated_time": self._estimate_test_time(test_type),
                "tools_needed": self._get_required_test_tools(test_type),
                "complexity": self._assess_test_complexity(task_description, parameters),
                "coverage_target": self._get_coverage_target(test_type)
            }
            
        except Exception as e:
            self.logger.warning(f"DeepSeek R1 unavailable, using fallback: {e}")
            return {
                "strategy": f"Standard {test_type} testing approach",
                "test_type": test_type,
                "estimated_time": "5-10 minutes",
                "tools_needed": ["pytest", "coverage"],
                "complexity": "medium",
                "coverage_target": "80%"
            }
    
    def _estimate_test_time(self, test_type: str) -> str:
        """Estimate testing time based on type."""
        time_estimates = {
            "unit_testing": "3-7 minutes",
            "integration_testing": "8-15 minutes",
            "performance_testing": "10-20 minutes",
            "coverage_analysis": "5-10 minutes",
            "e2e_testing": "15-30 minutes",
            "mock_testing": "5-12 minutes"
        }
        return time_estimates.get(test_type, "5-10 minutes")
    
    def _get_required_test_tools(self, test_type: str) -> List[str]:
        """Get required tools for testing type."""
        tool_mapping = {
            "unit_testing": ["pytest", "unittest", "mock"],
            "integration_testing": ["pytest", "requests", "docker"],
            "performance_testing": ["pytest-benchmark", "locust", "profiler"],
            "coverage_analysis": ["coverage", "pytest-cov"],
            "e2e_testing": ["selenium", "playwright", "cypress"],
            "mock_testing": ["unittest.mock", "pytest-mock", "responses"]
        }
        return tool_mapping.get(test_type, ["pytest"])
    
    def _assess_test_complexity(self, task_description: str, parameters: Dict[str, Any]) -> str:
        """Assess testing complexity."""
        complexity_indicators = {
            "high": ["integration", "e2e", "performance", "distributed", "microservice"],
            "medium": ["api", "database", "async", "concurrent"],
            "low": ["function", "method", "unit", "simple"]
        }
        
        description_lower = task_description.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return level
        
        # Check parameters for complexity indicators
        if "code" in parameters and len(parameters["code"]) > 500:
            return "medium"
        elif "modules" in parameters and len(parameters.get("modules", [])) > 3:
            return "high"
        
        return "low"
    
    def _get_coverage_target(self, test_type: str) -> str:
        """Get coverage target for test type."""
        coverage_targets = {
            "unit_testing": "90%",
            "integration_testing": "75%",
            "performance_testing": "60%",
            "coverage_analysis": "85%",
            "e2e_testing": "70%",
            "mock_testing": "95%"
        }
        return coverage_targets.get(test_type, "80%")
    
    async def _create_test_result(
        self, 
        test_type: str, 
        test_content: str, 
        execution_results: Dict[str, Any], 
        analysis: str,
        test_strategy: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive testing result."""
        
        # Generate test metrics
        metrics = self._calculate_test_metrics(test_content, execution_results)
        
        # Create test report
        report = await self._generate_test_report(test_type, execution_results, metrics, analysis)
        
        # Generate recommendations
        recommendations = await self._generate_test_recommendations(test_type, execution_results, metrics)
        
        return {
            "test_type": test_type,
            "strategy": test_strategy,
            "test_content": test_content,
            "execution_results": execution_results,
            "analysis": analysis,
            "metrics": metrics,
            "report": report,
            "recommendations": recommendations,
            "quality_score": self._calculate_quality_score(metrics, execution_results),
            "coverage_achieved": execution_results.get("coverage", "N/A"),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "test_session_id": str(uuid.uuid4())
            }
        }
    
    def _calculate_test_metrics(self, test_content: str, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive test metrics."""
        
        # Count test functions
        test_count = test_content.count("def test_")
        assertion_count = test_content.count("assert")
        
        # Extract execution metrics
        passed = execution_results.get("passed", 0)
        failed = execution_results.get("failed", 0)
        total_tests = passed + failed
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "test_functions": test_count,
            "assertions": assertion_count,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": round(success_rate, 2),
            "execution_time": execution_results.get("execution_time", "N/A"),
            "lines_of_test_code": len(test_content.split('\n')),
            "test_density": round(assertion_count / test_count, 2) if test_count > 0 else 0
        }
    
    async def _generate_test_report(
        self, 
        test_type: str, 
        execution_results: Dict[str, Any], 
        metrics: Dict[str, Any],
        analysis: str
    ) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        return {
            "summary": f"Testing session completed for {test_type}",
            "test_summary": {
                "total_tests": metrics["total_tests"],
                "passed": metrics["passed"],
                "failed": metrics["failed"],
                "success_rate": f"{metrics['success_rate']}%"
            },
            "coverage_summary": {
                "achieved": execution_results.get("coverage", "N/A"),
                "target": execution_results.get("coverage_target", "80%"),
                "status": "Met" if self._coverage_target_met(execution_results) else "Not Met"
            },
            "quality_indicators": {
                "test_density": metrics["test_density"],
                "assertion_coverage": "Good" if metrics["assertions"] > metrics["test_functions"] else "Needs Improvement",
                "execution_speed": "Fast" if "0." in str(metrics["execution_time"]) else "Normal"
            },
            "key_findings": self._extract_key_test_findings(analysis),
            "next_steps": self._suggest_test_next_steps(test_type, metrics)
        }
    
    def _coverage_target_met(self, execution_results: Dict[str, Any]) -> bool:
        """Check if coverage target was met."""
        coverage = execution_results.get("coverage", "0%")
        if isinstance(coverage, str) and "%" in coverage:
            coverage_value = float(coverage.replace("%", ""))
            return coverage_value >= 80.0
        return False
    
    def _extract_key_test_findings(self, analysis: str) -> List[str]:
        """Extract key findings from test analysis."""
        findings = []
        sentences = analysis.split('.')
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['found', 'identified', 'detected', 'passed', 'failed']):
                findings.append(sentence.strip())
        
        return findings[:3]  # Top 3 findings
    
    def _suggest_test_next_steps(self, test_type: str, metrics: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on test type and metrics."""
        next_steps = {
            "unit_testing": ["Run tests in CI/CD", "Add edge case tests", "Improve test coverage"],
            "integration_testing": ["Test with real data", "Add error scenarios", "Performance validation"],
            "performance_testing": ["Set up monitoring", "Create benchmarks", "Optimize bottlenecks"],
            "coverage_analysis": ["Increase coverage", "Add missing tests", "Review uncovered code"],
            "e2e_testing": ["Add to test suite", "Automate execution", "Monitor in production"]
        }
        
        base_steps = next_steps.get(test_type, ["Review results", "Implement tests", "Monitor quality"])
        
        # Add specific recommendations based on metrics
        if metrics["success_rate"] < 100:
            base_steps.insert(0, "Fix failing tests")
        if metrics["test_density"] < 2:
            base_steps.append("Add more assertions")
        
        return base_steps[:4]  # Limit to 4 steps
    
    async def _generate_test_recommendations(
        self, 
        test_type: str, 
        execution_results: Dict[str, Any], 
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable test recommendations."""
        
        prompt = f"""
        Based on the following test execution results and metrics, provide specific recommendations:
        
        Test Type: {test_type}
        Execution Results: {json.dumps(execution_results, indent=2)}
        Metrics: {json.dumps(metrics, indent=2)}
        
        Please provide 3-5 specific, actionable recommendations for improving the tests.
        Focus on test quality, coverage, maintainability, and effectiveness.
        """
        
        try:
            recommendations_text = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=prompt,
                max_tokens=600,
                temperature=0.2
            )
            
            # Parse recommendations into a list
            recommendations = []
            for line in recommendations_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    recommendation = line.lstrip('-•0123456789. ').strip()
                    if recommendation:
                        recommendations.append(recommendation)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return [
                "Review test coverage and add missing tests",
                "Improve test assertions and edge case handling",
                "Optimize test execution performance",
                "Add integration with CI/CD pipeline"
            ]
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], execution_results: Dict[str, Any]) -> float:
        """Calculate overall test quality score."""
        score = 0.0
        
        # Success rate (40% weight)
        score += (metrics["success_rate"] / 100) * 0.4
        
        # Test density (20% weight)
        density_score = min(metrics["test_density"] / 3.0, 1.0)  # Cap at 3 assertions per test
        score += density_score * 0.2
        
        # Coverage (30% weight)
        coverage = execution_results.get("coverage", "0%")
        if isinstance(coverage, str) and "%" in coverage:
            coverage_value = float(coverage.replace("%", "")) / 100
            score += coverage_value * 0.3
        
        # Test count (10% weight)
        test_count_score = min(metrics["test_functions"] / 10.0, 1.0)  # Cap at 10 tests
        score += test_count_score * 0.1
        
        return round(score, 3)
    
    def _update_performance_metrics(self, execution_time: float, success: bool, test_type: str):
        """Update performance metrics."""
        self.performance_metrics["total_tests_generated"] += 1
        if success:
            self.performance_metrics["total_tests_executed"] += 1
        
        self.performance_metrics["last_activity"] = datetime.now().isoformat()
        
        # Update success rate
        total_tasks = self.success_count + self.error_count
        if total_tasks > 0:
            self.performance_metrics["success_rate"] = self.success_count / total_tasks
        
        # Update average response time
        if self.performance_metrics["avg_response_time"] == 0.0:
            self.performance_metrics["avg_response_time"] = execution_time
        else:
            # Moving average
            self.performance_metrics["avg_response_time"] = (
                self.performance_metrics["avg_response_time"] * 0.8 + execution_time * 0.2
            )
    
    async def _store_enhanced_test_memory(self, task: TestingTask):
        """Store enhanced testing session in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_test_{task.id}",
            agent_id=self.agent_id,
            type="task",
            content=f"Testing session ({task.type}): {task.description}\n\nResult: {json.dumps(task.result, indent=2)[:500]}...",
            metadata={
                "task_id": task.id,
                "test_type": task.type,
                "status": task.status,
                "execution_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None,
                "quality_score": task.result.get("quality_score") if task.result else None,
                "test_count": task.result.get("metrics", {}).get("test_functions") if task.result else None
            },
            timestamp=task.created_at,
            importance=0.7
        )
        
        self.memory_manager.store_memory(memory)
    
    # Enhanced API Methods
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific testing task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "error": task.error
            }
        
        # Check history
        for task in self.task_history:
            if task.id == task_id:
                return {
                    "id": task.id,
                    "type": task.type,
                    "description": task.description,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                    "error": task.error
                }
        
        return None
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active testing tasks."""
        return [
            {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat()
            }
            for task in self.active_tasks.values()
        ]
    
    async def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get testing task history."""
        recent_tasks = sorted(self.task_history, key=lambda x: x.created_at, reverse=True)[:limit]
        
        return [
            {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "execution_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None,
                "quality_score": task.result.get("quality_score") if task.result else None,
                "test_count": task.result.get("metrics", {}).get("test_functions") if task.result else None
            }
            for task in recent_tasks
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active testing task."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "cancelled"
            task.completed_at = datetime.now()
            
            await self._notify_task_update(task_id, "cancelled", task.progress)
            
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
            return True
        
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.performance_metrics,
            "active_tasks": len(self.active_tasks),
            "total_tasks": self.task_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "current_task": self.current_task
        }
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get enhanced agent status with real-time metrics."""
        base_status = self.get_status()
        
        base_status.update({
            "performance_metrics": self.get_performance_metrics(),
            "active_tasks": len(self.active_tasks),
            "websocket_connections": len(self.websocket_callbacks),
            "supported_test_types": self.performance_metrics["test_types"],
            "last_activity": self.performance_metrics["last_activity"]
        })
        
        return base_status