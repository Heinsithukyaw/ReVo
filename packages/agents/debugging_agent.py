"""Enhanced Debugging Agent for reVoAgent platform."""

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
class DebuggingTask:
    """Represents a debugging task."""
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


class DebuggingAgent(BaseAgent):
    """
    Enhanced Debugging Agent with real-time debugging capabilities.
    
    Features:
    - Real-time error analysis and debugging
    - Interactive debugging sessions
    - Performance profiling and optimization
    - Log analysis with pattern recognition
    - Root cause analysis with AI reasoning
    - WebSocket integration for live updates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks: Dict[str, DebuggingTask] = {}
        self.task_history: List[DebuggingTask] = []
        self.performance_metrics = {
            "total_debugged": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "debug_types": ["error_analysis", "performance_analysis", "log_analysis", "bug_fixing", "test_debugging"],
            "last_activity": None
        }
        self.websocket_callbacks = []
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "advanced error detection, real-time debugging, performance analysis, log analysis, and intelligent root cause investigation"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a debugging task with real-time monitoring."""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = DebuggingTask(
            id=task_id,
            type=self._analyze_debug_task(task_description),
            description=task_description,
            parameters=parameters
        )
        
        self.active_tasks[task_id] = task
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Notify start
            await self._notify_task_update(task_id, "started", 0.0)
            
            # Step 1: Analyze problem (20%)
            task.progress = 0.2
            await self._notify_task_update(task_id, "analyzing", 0.2)
            await asyncio.sleep(0.3)
            
            # Step 2: Generate debugging strategy (40%)
            task.progress = 0.4
            await self._notify_task_update(task_id, "strategizing", 0.4)
            debug_strategy = await self._generate_debug_strategy(task_description, task.type, parameters)
            
            # Step 3: Execute debugging tools (60%)
            task.progress = 0.6
            await self._notify_task_update(task_id, "investigating", 0.6)
            tool_results = await self._execute_debug_tools(task.type, parameters)
            
            # Step 4: Analyze results and generate recommendations (80%)
            task.progress = 0.8
            await self._notify_task_update(task_id, "analyzing_results", 0.8)
            analysis = await self._generate_debug_analysis(task_description, task.type, parameters)
            recommendations = await self._generate_recommendations(analysis, tool_results, task.type)
            
            # Step 5: Generate fixes (100%)
            task.progress = 1.0
            task.status = "completed"
            
            # Create comprehensive result
            result = await self._create_debug_result(
                task.type, analysis, tool_results, recommendations, debug_strategy, parameters
            )
            
            task.result = result
            task.completed_at = datetime.now()
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True)
            
            # Store in memory
            await self._store_enhanced_debug_memory(task)
            
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
            self._update_performance_metrics(execution_time, False)
            
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            await self._notify_task_update(task_id, "failed", task.progress, error=str(e))
            
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
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
    
    # Enhanced Methods for Real-time Debugging
    
    async def _notify_task_update(self, task_id: str, status: str, progress: float, result: Optional[Dict] = None, error: Optional[str] = None):
        """Notify WebSocket clients about debugging task updates."""
        update = {
            "type": "debugging_update",
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
    
    async def _generate_debug_strategy(self, task_description: str, debug_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive debugging strategy."""
        
        strategy_prompt = f"""
        You are an expert debugging strategist. Create a comprehensive debugging strategy for:
        
        Problem: {task_description}
        Debug Type: {debug_type}
        Parameters: {json.dumps(parameters, indent=2)}
        
        Create a step-by-step debugging strategy that includes:
        1. Initial assessment approach
        2. Tools and techniques to use
        3. Data collection methods
        4. Analysis priorities
        5. Verification steps
        
        Provide a structured debugging plan.
        """
        
        try:
            strategy_text = await self.model_manager.generate_response(
                model_name="deepseek-r1",  # Use DeepSeek R1 for advanced reasoning
                prompt=strategy_prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            return {
                "strategy": strategy_text,
                "debug_type": debug_type,
                "estimated_time": self._estimate_debug_time(debug_type),
                "tools_needed": self._get_required_tools(debug_type),
                "complexity": self._assess_complexity(task_description, parameters)
            }
            
        except Exception as e:
            self.logger.warning(f"DeepSeek R1 unavailable, using fallback: {e}")
            return {
                "strategy": f"Standard {debug_type} debugging approach",
                "debug_type": debug_type,
                "estimated_time": "5-10 minutes",
                "tools_needed": ["analysis", "investigation"],
                "complexity": "medium"
            }
    
    def _estimate_debug_time(self, debug_type: str) -> str:
        """Estimate debugging time based on type."""
        time_estimates = {
            "error_analysis": "3-5 minutes",
            "performance_analysis": "5-10 minutes",
            "log_analysis": "2-4 minutes",
            "bug_fixing": "10-15 minutes",
            "test_debugging": "5-8 minutes",
            "memory_analysis": "8-12 minutes"
        }
        return time_estimates.get(debug_type, "5-10 minutes")
    
    def _get_required_tools(self, debug_type: str) -> List[str]:
        """Get required tools for debugging type."""
        tool_mapping = {
            "error_analysis": ["traceback_analyzer", "code_inspector", "error_classifier"],
            "performance_analysis": ["profiler", "memory_analyzer", "cpu_monitor"],
            "log_analysis": ["log_parser", "pattern_matcher", "timeline_analyzer"],
            "bug_fixing": ["code_analyzer", "test_runner", "diff_checker"],
            "test_debugging": ["test_runner", "assertion_analyzer", "mock_inspector"],
            "memory_analysis": ["memory_profiler", "leak_detector", "gc_analyzer"]
        }
        return tool_mapping.get(debug_type, ["general_analyzer"])
    
    def _assess_complexity(self, task_description: str, parameters: Dict[str, Any]) -> str:
        """Assess debugging complexity."""
        complexity_indicators = {
            "high": ["concurrent", "distributed", "race condition", "deadlock", "memory leak"],
            "medium": ["performance", "optimization", "integration", "api"],
            "low": ["syntax", "import", "typo", "simple error"]
        }
        
        description_lower = task_description.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return level
        
        # Check parameters for complexity indicators
        if "code" in parameters and len(parameters["code"]) > 1000:
            return "high"
        elif "traceback" in parameters and len(parameters["traceback"].split('\n')) > 10:
            return "medium"
        
        return "low"
    
    async def _create_debug_result(
        self, 
        debug_type: str, 
        analysis: str, 
        tool_results: Dict[str, Any], 
        recommendations: List[str],
        debug_strategy: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive debugging result."""
        
        # Generate code fixes if applicable
        fixes = await self._generate_code_fixes(debug_type, analysis, parameters)
        
        # Create debugging report
        report = await self._generate_debug_report(debug_type, analysis, recommendations, tool_results)
        
        return {
            "debug_type": debug_type,
            "analysis": analysis,
            "strategy": debug_strategy,
            "tool_results": tool_results,
            "recommendations": recommendations,
            "fixes": fixes,
            "report": report,
            "severity": self._assess_severity(debug_type, analysis),
            "confidence": self._calculate_confidence(tool_results, analysis),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "debug_session_id": str(uuid.uuid4())
            }
        }
    
    async def _generate_code_fixes(self, debug_type: str, analysis: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate code fixes based on analysis."""
        
        if "code" not in parameters:
            return None
        
        fix_prompt = f"""
        Based on the following debugging analysis, generate specific code fixes:
        
        Debug Type: {debug_type}
        Analysis: {analysis}
        
        Original Code:
        ```
        {parameters['code']}
        ```
        
        Provide:
        1. Fixed code with corrections
        2. Explanation of changes made
        3. Prevention strategies
        
        Fixed Code:
        """
        
        try:
            fixed_code = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=fix_prompt,
                max_tokens=1500,
                temperature=0.1
            )
            
            return {
                "original_code": parameters['code'],
                "fixed_code": self._extract_code_from_response(fixed_code),
                "explanation": self._extract_explanation_from_response(fixed_code),
                "changes_made": self._identify_changes(parameters['code'], fixed_code)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate code fixes: {e}")
            return None
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from AI response."""
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else response
    
    def _extract_explanation_from_response(self, response: str) -> str:
        """Extract explanation from AI response."""
        # Simple extraction - look for explanation patterns
        lines = response.split('\n')
        explanation_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['explanation:', 'changes:', 'fix:']):
                explanation_lines.append(line)
        
        return '\n'.join(explanation_lines) if explanation_lines else "Code fixes applied"
    
    def _identify_changes(self, original: str, fixed: str) -> List[str]:
        """Identify changes between original and fixed code."""
        # Simple diff - in production, use proper diff library
        original_lines = original.split('\n')
        fixed_lines = fixed.split('\n')
        
        changes = []
        for i, (orig, fix) in enumerate(zip(original_lines, fixed_lines)):
            if orig != fix:
                changes.append(f"Line {i+1}: {orig} -> {fix}")
        
        return changes[:5]  # Limit to 5 changes
    
    async def _generate_debug_report(
        self, 
        debug_type: str, 
        analysis: str, 
        recommendations: List[str], 
        tool_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive debugging report."""
        
        return {
            "summary": f"Debugging session completed for {debug_type}",
            "findings": self._extract_key_findings(analysis),
            "recommendations_summary": recommendations[:3],
            "tools_used": list(tool_results.keys()),
            "success_indicators": self._identify_success_indicators(tool_results),
            "next_steps": self._suggest_next_steps(debug_type, recommendations)
        }
    
    def _extract_key_findings(self, analysis: str) -> List[str]:
        """Extract key findings from analysis."""
        # Simple extraction - look for key finding patterns
        findings = []
        sentences = analysis.split('.')
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['found', 'identified', 'detected', 'discovered']):
                findings.append(sentence.strip())
        
        return findings[:3]  # Top 3 findings
    
    def _identify_success_indicators(self, tool_results: Dict[str, Any]) -> List[str]:
        """Identify success indicators from tool results."""
        indicators = []
        
        if tool_results:
            indicators.append("Tools executed successfully")
        
        if "error" not in tool_results:
            indicators.append("No tool execution errors")
        
        return indicators
    
    def _suggest_next_steps(self, debug_type: str, recommendations: List[str]) -> List[str]:
        """Suggest next steps based on debug type and recommendations."""
        next_steps = {
            "error_analysis": ["Test the fix", "Monitor for recurrence", "Update error handling"],
            "performance_analysis": ["Implement optimizations", "Set up monitoring", "Benchmark improvements"],
            "log_analysis": ["Improve logging", "Set up alerts", "Monitor patterns"],
            "bug_fixing": ["Run tests", "Code review", "Deploy fix"],
            "test_debugging": ["Fix test", "Run test suite", "Update test documentation"]
        }
        
        return next_steps.get(debug_type, ["Review recommendations", "Implement fixes", "Monitor results"])
    
    def _assess_severity(self, debug_type: str, analysis: str) -> str:
        """Assess severity of the debugging issue."""
        severity_keywords = {
            "critical": ["crash", "failure", "critical", "severe", "fatal"],
            "high": ["error", "exception", "broken", "failing"],
            "medium": ["warning", "performance", "slow", "issue"],
            "low": ["minor", "cosmetic", "improvement", "optimization"]
        }
        
        analysis_lower = analysis.lower()
        
        for severity, keywords in severity_keywords.items():
            if any(keyword in analysis_lower for keyword in keywords):
                return severity
        
        return "medium"
    
    def _calculate_confidence(self, tool_results: Dict[str, Any], analysis: str) -> float:
        """Calculate confidence in debugging results."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on tool results
        if tool_results and "error" not in tool_results:
            confidence += 0.2
        
        # Increase confidence based on analysis quality
        if len(analysis) > 200:  # Detailed analysis
            confidence += 0.2
        
        # Increase confidence if multiple tools were used
        if len(tool_results) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics["total_debugged"] += 1
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
    
    async def _store_enhanced_debug_memory(self, task: DebuggingTask):
        """Store enhanced debugging session in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_debug_{task.id}",
            agent_id=self.agent_id,
            type="task",
            content=f"Debugging session ({task.type}): {task.description}\n\nResult: {json.dumps(task.result, indent=2)[:500]}...",
            metadata={
                "task_id": task.id,
                "debug_type": task.type,
                "status": task.status,
                "execution_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None,
                "severity": task.result.get("severity") if task.result else None,
                "confidence": task.result.get("confidence") if task.result else None
            },
            timestamp=task.created_at,
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
    
    # Enhanced API Methods
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific debugging task."""
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
        """Get all active debugging tasks."""
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
        """Get debugging task history."""
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
                "severity": task.result.get("severity") if task.result else None,
                "confidence": task.result.get("confidence") if task.result else None
            }
            for task in recent_tasks
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active debugging task."""
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
            "supported_debug_types": self.performance_metrics["debug_types"],
            "last_activity": self.performance_metrics["last_activity"]
        })
        
        return base_status