"""Debugging agent for reVoAgent platform."""

import uuid
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseAgent
from ..core.memory import MemoryEntry


class DebuggingAgent(BaseAgent):
    """
    Specialized agent for debugging and error analysis.
    
    Capabilities:
    - Error detection and analysis
    - Code debugging and fixing
    - Performance profiling
    - Log analysis
    - Root cause analysis
    """
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "error detection, debugging, performance analysis, log analysis, and root cause investigation"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a debugging task."""
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Analyze the debugging task
            debug_type = self._analyze_debug_task(task_description)
            
            # Execute debugging based on type
            result = await self._execute_debugging(task_description, debug_type, parameters)
            
            # Store debugging session in memory
            await self._store_debug_memory(task_description, result, debug_type)
            
            self.success_count += 1
            self.current_task = None
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.current_task = None
            self.logger.error(f"Debugging task failed: {e}")
            raise
    
    def _analyze_debug_task(self, task_description: str) -> str:
        """Analyze the debugging task to determine the type."""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["error", "exception", "traceback", "crash"]):
            return "error_analysis"
        elif any(keyword in description_lower for keyword in ["slow", "performance", "optimize", "profile"]):
            return "performance_analysis"
        elif any(keyword in description_lower for keyword in ["log", "logging", "logs"]):
            return "log_analysis"
        elif any(keyword in description_lower for keyword in ["bug", "fix", "issue", "problem"]):
            return "bug_fixing"
        elif any(keyword in description_lower for keyword in ["test", "failing", "broken"]):
            return "test_debugging"
        elif any(keyword in description_lower for keyword in ["memory", "leak", "usage"]):
            return "memory_analysis"
        else:
            return "general_debugging"
    
    async def _execute_debugging(
        self,
        task_description: str,
        debug_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute debugging based on the type."""
        
        # Generate debugging analysis using AI
        analysis = await self._generate_debug_analysis(task_description, debug_type, parameters)
        
        # Execute debugging tools if available
        tool_results = await self._execute_debug_tools(debug_type, parameters)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(analysis, tool_results, debug_type)
        
        return {
            "debug_type": debug_type,
            "analysis": analysis,
            "tool_results": tool_results,
            "recommendations": recommendations,
            "task_description": task_description
        }
    
    async def _generate_debug_analysis(
        self,
        task_description: str,
        debug_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate debugging analysis using AI."""
        
        prompt = self._build_debug_prompt(task_description, debug_type, parameters)
        
        analysis = await self.model_manager.generate_response(
            model_name=self.config.model,
            prompt=prompt,
            max_tokens=1500,
            temperature=0.1
        )
        
        return analysis
    
    def _build_debug_prompt(
        self,
        task_description: str,
        debug_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build a debugging analysis prompt."""
        
        prompt_parts = [
            f"You are an expert software debugger and performance analyst.",
            f"Debug type: {debug_type}",
            "",
            "Problem description:",
            task_description,
            "",
        ]
        
        # Add relevant code or error information
        if "code" in parameters:
            prompt_parts.extend([
                "Code to analyze:",
                "```",
                parameters["code"],
                "```",
                ""
            ])
        
        if "error_message" in parameters:
            prompt_parts.extend([
                "Error message:",
                parameters["error_message"],
                ""
            ])
        
        if "traceback" in parameters:
            prompt_parts.extend([
                "Traceback:",
                parameters["traceback"],
                ""
            ])
        
        # Add debug-type specific instructions
        if debug_type == "error_analysis":
            prompt_parts.extend([
                "Please analyze this error and provide:",
                "1. Root cause analysis",
                "2. Explanation of why the error occurred",
                "3. Step-by-step debugging approach",
                "4. Potential fixes with code examples",
                "5. Prevention strategies",
                ""
            ])
        elif debug_type == "performance_analysis":
            prompt_parts.extend([
                "Please analyze the performance issue and provide:",
                "1. Identification of performance bottlenecks",
                "2. Time and space complexity analysis",
                "3. Profiling recommendations",
                "4. Optimization strategies with code examples",
                "5. Best practices for performance",
                ""
            ])
        elif debug_type == "log_analysis":
            prompt_parts.extend([
                "Please analyze the logs and provide:",
                "1. Pattern identification in log entries",
                "2. Error frequency and timing analysis",
                "3. Correlation between different log events",
                "4. Recommendations for log improvements",
                "5. Monitoring and alerting suggestions",
                ""
            ])
        
        prompt_parts.extend([
            "Provide a comprehensive analysis with actionable recommendations."
        ])
        
        return "\n".join(prompt_parts)
    
    async def _execute_debug_tools(self, debug_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute debugging tools based on the debug type."""
        tool_results = {}
        
        try:
            if debug_type == "performance_analysis" and "profiler" in self.config.tools:
                # Use profiler tool
                profiler_result = await self.use_tool("profiler", {
                    "code": parameters.get("code", ""),
                    "function": parameters.get("function", "")
                })
                tool_results["profiler"] = profiler_result
            
            if debug_type == "log_analysis" and "log_analyzer" in self.config.tools:
                # Use log analyzer tool
                log_result = await self.use_tool("log_analyzer", {
                    "log_file": parameters.get("log_file", ""),
                    "pattern": parameters.get("pattern", "")
                })
                tool_results["log_analyzer"] = log_result
            
            if "terminal" in self.config.tools:
                # Use terminal for debugging commands
                terminal_result = await self.use_tool("terminal", {
                    "command": self._get_debug_command(debug_type, parameters)
                })
                tool_results["terminal"] = terminal_result
                
        except Exception as e:
            self.logger.warning(f"Debug tool execution failed: {e}")
            tool_results["error"] = str(e)
        
        return tool_results
    
    def _get_debug_command(self, debug_type: str, parameters: Dict[str, Any]) -> str:
        """Get appropriate debug command for terminal execution."""
        if debug_type == "memory_analysis":
            return "ps aux --sort=-%mem | head -10"
        elif debug_type == "performance_analysis":
            return "top -n 1 -b"
        elif debug_type == "log_analysis":
            log_file = parameters.get("log_file", "/var/log/syslog")
            return f"tail -n 100 {log_file}"
        else:
            return "echo 'Debug command executed'"
    
    async def _generate_recommendations(
        self,
        analysis: str,
        tool_results: Dict[str, Any],
        debug_type: str
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        
        prompt = f"""
        Based on the following debugging analysis and tool results, provide specific, actionable recommendations:
        
        Analysis:
        {analysis}
        
        Tool Results:
        {str(tool_results)}
        
        Debug Type: {debug_type}
        
        Please provide 3-5 specific, actionable recommendations in order of priority.
        Each recommendation should be clear and implementable.
        """
        
        recommendations_text = await self.model_manager.generate_response(
            model_name=self.config.model,
            prompt=prompt,
            max_tokens=800,
            temperature=0.2
        )
        
        # Parse recommendations into a list
        recommendations = []
        for line in recommendations_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                # Clean up the recommendation
                recommendation = line.lstrip('-•0123456789. ').strip()
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    async def _store_debug_memory(
        self,
        task_description: str,
        result: Dict[str, Any],
        debug_type: str
    ) -> None:
        """Store debugging session in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_debug_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="task",
            content=f"Debugging session ({debug_type}): {task_description}\nRecommendations: {'; '.join(result['recommendations'][:2])}",
            metadata={
                "debug_type": debug_type,
                "recommendations_count": len(result["recommendations"]),
                "tools_used": list(result["tool_results"].keys())
            },
            timestamp=datetime.now(),
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
    
    async def analyze_error(self, error_message: str, traceback: str = None, code: str = None) -> Dict[str, Any]:
        """Analyze a specific error."""
        parameters = {"error_message": error_message}
        if traceback:
            parameters["traceback"] = traceback
        if code:
            parameters["code"] = code
        
        return await self.execute_task(f"Analyze error: {error_message}", parameters)
    
    async def profile_performance(self, code: str, function_name: str = None) -> Dict[str, Any]:
        """Profile code performance."""
        parameters = {"code": code}
        if function_name:
            parameters["function"] = function_name
        
        return await self.execute_task(f"Profile performance of code", parameters)
    
    async def analyze_logs(self, log_file: str, pattern: str = None) -> Dict[str, Any]:
        """Analyze log files for issues."""
        parameters = {"log_file": log_file}
        if pattern:
            parameters["pattern"] = pattern
        
        return await self.execute_task(f"Analyze logs in {log_file}", parameters)
    
    async def debug_failing_test(self, test_name: str, test_code: str, error_output: str) -> Dict[str, Any]:
        """Debug a failing test."""
        parameters = {
            "test_name": test_name,
            "code": test_code,
            "error_message": error_output
        }
        
        return await self.execute_task(f"Debug failing test: {test_name}", parameters)