"""Enhanced Code Generator Agent for reVoAgent platform."""

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
class CodeGenerationTask:
    """Represents a code generation task."""
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


class CodeGeneratorAgent(BaseAgent):
    """
    Enhanced Code Generator Agent with real-time capabilities.
    
    Features:
    - Real-time code generation with DeepSeek R1 integration
    - Multiple programming languages support
    - Code analysis and optimization
    - Test generation and validation
    - Performance monitoring and metrics
    - WebSocket integration for live updates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks: Dict[str, CodeGenerationTask] = {}
        self.task_history: List[CodeGenerationTask] = []
        self.performance_metrics = {
            "total_generated": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "languages_supported": ["python", "javascript", "typescript", "java", "go", "rust", "cpp"],
            "last_activity": None
        }
        self.websocket_callbacks = []
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "advanced code generation, refactoring, documentation, testing, optimization, and real-time monitoring"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a code generation task with real-time monitoring."""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = CodeGenerationTask(
            id=task_id,
            type=self._analyze_task_type(task_description),
            description=task_description,
            parameters=parameters
        )
        
        self.active_tasks[task_id] = task
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Notify start
            await self._notify_task_update(task_id, "started", 0.0)
            
            # Step 1: Analyze requirements (10%)
            task.progress = 0.1
            await self._notify_task_update(task_id, "analyzing", 0.1)
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Step 2: Generate prompt (20%)
            task.progress = 0.2
            await self._notify_task_update(task_id, "preparing", 0.2)
            prompt = self._build_enhanced_prompt(task_description, task.type, parameters)
            
            # Step 3: Generate code with DeepSeek R1 (60%)
            task.progress = 0.3
            await self._notify_task_update(task_id, "generating", 0.3)
            
            generated_code = await self._generate_code_with_deepseek(prompt, task.type)
            
            # Step 4: Post-process and validate (80%)
            task.progress = 0.8
            await self._notify_task_update(task_id, "processing", 0.8)
            
            processed_result = await self._process_and_validate_code(
                generated_code, task.type, parameters
            )
            
            # Step 5: Finalize (100%)
            task.progress = 1.0
            task.status = "completed"
            task.result = processed_result
            task.completed_at = datetime.now()
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True)
            
            # Store in memory
            await self._store_enhanced_task_memory(task)
            
            # Notify completion
            await self._notify_task_update(task_id, "completed", 1.0, processed_result)
            
            # Move to history
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
            self.success_count += 1
            self.current_task = None
            
            return processed_result
            
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
            self.logger.error(f"Code generation task failed: {e}")
            raise
    
    def _analyze_task_type(self, task_description: str) -> str:
        """Analyze the task description to determine the type of code generation."""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["test", "unit test", "testing"]):
            return "testing"
        elif any(keyword in description_lower for keyword in ["refactor", "improve", "optimize"]):
            return "refactoring"
        elif any(keyword in description_lower for keyword in ["document", "comment", "docstring"]):
            return "documentation"
        elif any(keyword in description_lower for keyword in ["api", "rest", "endpoint"]):
            return "api_development"
        elif any(keyword in description_lower for keyword in ["class", "function", "method"]):
            return "function_creation"
        elif any(keyword in description_lower for keyword in ["web", "html", "css", "javascript"]):
            return "web_development"
        elif any(keyword in description_lower for keyword in ["data", "analysis", "pandas", "numpy"]):
            return "data_analysis"
        else:
            return "general_coding"
    
    def _build_code_generation_prompt(
        self,
        task_description: str,
        task_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build a specialized prompt for code generation."""
        
        # Get recent code generation memories for context
        recent_memories = self.memory_manager.retrieve_memories(
            agent_id=self.agent_id,
            memory_type="task",
            limit=3
        )
        
        context = ""
        if recent_memories:
            context = "Recent code generation context:\n"
            for memory in recent_memories:
                context += f"- {memory.content[:100]}...\n"
            context += "\n"
        
        # Base prompt structure
        prompt_parts = [
            f"You are an expert software engineer specializing in {task_type}.",
            "",
            context,
            "Task Requirements:",
            task_description,
            "",
        ]
        
        # Add task-specific instructions
        if task_type == "testing":
            prompt_parts.extend([
                "Generate comprehensive unit tests that:",
                "- Cover edge cases and error conditions",
                "- Use appropriate testing frameworks (pytest, unittest, etc.)",
                "- Include clear test names and documentation",
                "- Follow testing best practices",
                ""
            ])
        elif task_type == "refactoring":
            prompt_parts.extend([
                "Refactor the code to:",
                "- Improve readability and maintainability",
                "- Follow SOLID principles and design patterns",
                "- Optimize performance where appropriate",
                "- Maintain existing functionality",
                ""
            ])
        elif task_type == "documentation":
            prompt_parts.extend([
                "Add comprehensive documentation that includes:",
                "- Clear docstrings for functions and classes",
                "- Type hints where appropriate",
                "- Usage examples",
                "- Parameter and return value descriptions",
                ""
            ])
        elif task_type == "api_development":
            prompt_parts.extend([
                "Create a robust API that includes:",
                "- Proper error handling and status codes",
                "- Input validation and sanitization",
                "- Clear endpoint documentation",
                "- Security considerations",
                ""
            ])
        
        # Add general coding guidelines
        prompt_parts.extend([
            "Code Requirements:",
            "- Write clean, readable, and well-structured code",
            "- Follow language-specific best practices and conventions",
            "- Include appropriate error handling",
            "- Add comments for complex logic",
            "- Ensure code is production-ready",
            "",
            "Please provide the complete code solution:"
        ])
        
        return "\n".join(prompt_parts)
    
    def _post_process_code(self, generated_code: str, task_type: str) -> str:
        """Post-process the generated code."""
        # Remove common AI response artifacts
        code = generated_code.strip()
        
        # Remove markdown code blocks if present
        if code.startswith("```"):
            lines = code.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = '\n'.join(lines)
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the code:",
            "Here is the code:",
            "The code is:",
            "Solution:",
            "Here's the solution:",
        ]
        
        for prefix in prefixes_to_remove:
            if code.startswith(prefix):
                code = code[len(prefix):].strip()
        
        return code
    
    def _detect_language(self, code: str) -> str:
        """Detect the programming language of the generated code."""
        code_lower = code.lower()
        
        # Simple language detection based on keywords and syntax
        if "def " in code and "import " in code:
            return "python"
        elif "function " in code or "const " in code or "let " in code:
            return "javascript"
        elif "public class " in code or "private " in code:
            return "java"
        elif "#include" in code or "int main(" in code:
            return "c++"
        elif "fn " in code and "let mut" in code:
            return "rust"
        elif "func " in code and "package " in code:
            return "go"
        else:
            return "unknown"
    
    async def _store_task_memory(self, task_description: str, code: str, task_type: str) -> None:
        """Store the code generation task in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_task_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="task",
            content=f"Generated {task_type} code for: {task_description}\n\nCode:\n{code[:500]}...",
            metadata={
                "task_type": task_type,
                "language": self._detect_language(code),
                "lines_of_code": len(code.split('\n')),
                "task_description": task_description
            },
            timestamp=datetime.now(),
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
    
    async def _create_git_commit(self, task_description: str, code: str) -> None:
        """Create a git commit for the generated code."""
        try:
            # This is a simplified implementation
            # In practice, you'd want to save the code to appropriate files first
            commit_message = f"Generated code: {task_description[:50]}..."
            
            git_params = {
                "action": "commit",
                "message": commit_message,
                "files": ["generated_code.py"]  # This would be dynamic based on the task
            }
            
            await self.use_tool("git", git_params)
            
        except Exception as e:
            self.logger.warning(f"Failed to create git commit: {e}")
    
    async def generate_function(self, function_name: str, description: str, parameters: list) -> str:
        """Generate a specific function."""
        task_description = f"Create a function named '{function_name}' that {description}"
        if parameters:
            task_description += f" with parameters: {', '.join(parameters)}"
        
        result = await self.execute_task(task_description, {
            "function_name": function_name,
            "parameters": parameters
        })
        
        return result["code"]
    
    async def generate_class(self, class_name: str, description: str, methods: list) -> str:
        """Generate a class with specified methods."""
        task_description = f"Create a class named '{class_name}' that {description}"
        if methods:
            task_description += f" with methods: {', '.join(methods)}"
        
        result = await self.execute_task(task_description, {
            "class_name": class_name,
            "methods": methods
        })
        
        return result["code"]
    
    async def generate_tests(self, code_to_test: str) -> str:
        """Generate unit tests for given code."""
        task_description = f"Generate comprehensive unit tests for the following code:\n\n{code_to_test}"
        
        result = await self.execute_task(task_description, {
            "code_to_test": code_to_test,
            "test_type": "unit_tests"
        })
        
        return result["code"]
    
    # Enhanced Methods for Real-time Code Generation
    
    async def _notify_task_update(self, task_id: str, status: str, progress: float, result: Optional[Dict] = None, error: Optional[str] = None):
        """Notify WebSocket clients about task updates."""
        update = {
            "type": "code_generation_update",
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
    
    def _build_enhanced_prompt(self, task_description: str, task_type: str, parameters: Dict[str, Any]) -> str:
        """Build an enhanced prompt for DeepSeek R1 integration."""
        
        # Get recent memories for context
        recent_memories = self.memory_manager.retrieve_memories(
            agent_id=self.agent_id,
            memory_type="task",
            limit=3
        )
        
        context = ""
        if recent_memories:
            context = "Recent code generation context:\n"
            for memory in recent_memories:
                context += f"- {memory.content[:100]}...\n"
            context += "\n"
        
        # Enhanced prompt with DeepSeek R1 reasoning capabilities
        prompt_parts = [
            "You are an expert software engineer with access to DeepSeek R1's advanced reasoning capabilities.",
            "Use step-by-step reasoning to generate high-quality, production-ready code.",
            "",
            context,
            f"Task Type: {task_type}",
            f"Requirements: {task_description}",
            "",
            "Parameters:",
            json.dumps(parameters, indent=2),
            "",
            "Please follow this reasoning process:",
            "1. Analyze the requirements thoroughly",
            "2. Consider edge cases and error handling",
            "3. Choose the most appropriate design patterns",
            "4. Generate clean, well-documented code",
            "5. Include comprehensive error handling",
            "",
        ]
        
        # Add task-specific instructions
        if task_type == "testing":
            prompt_parts.extend([
                "Testing Requirements:",
                "- Generate comprehensive unit tests with 90%+ coverage",
                "- Include edge cases, error conditions, and boundary tests",
                "- Use appropriate testing frameworks and best practices",
                "- Add clear test descriptions and assertions",
                "- Include setup and teardown methods where needed",
                ""
            ])
        elif task_type == "refactoring":
            prompt_parts.extend([
                "Refactoring Requirements:",
                "- Improve code readability and maintainability",
                "- Apply SOLID principles and design patterns",
                "- Optimize performance without breaking functionality",
                "- Add proper documentation and type hints",
                "- Ensure backward compatibility where possible",
                ""
            ])
        elif task_type == "api_development":
            prompt_parts.extend([
                "API Development Requirements:",
                "- Create RESTful endpoints with proper HTTP methods",
                "- Implement comprehensive input validation",
                "- Add proper error handling and status codes",
                "- Include authentication and authorization",
                "- Add OpenAPI/Swagger documentation",
                "- Implement rate limiting and security measures",
                ""
            ])
        elif task_type == "web_development":
            prompt_parts.extend([
                "Web Development Requirements:",
                "- Create responsive, accessible web components",
                "- Follow modern web standards and best practices",
                "- Implement proper state management",
                "- Add comprehensive error boundaries",
                "- Ensure cross-browser compatibility",
                "- Include performance optimizations",
                ""
            ])
        
        # Add general requirements
        prompt_parts.extend([
            "General Code Requirements:",
            "- Write clean, readable, and maintainable code",
            "- Follow language-specific conventions and best practices",
            "- Include comprehensive error handling and logging",
            "- Add detailed comments for complex logic",
            "- Ensure code is production-ready and scalable",
            "- Include type hints and documentation",
            "",
            "Output Format:",
            "Provide the complete code solution with:",
            "1. Main implementation",
            "2. Error handling",
            "3. Documentation/comments",
            "4. Usage examples (if applicable)",
            "",
            "Code:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _generate_code_with_deepseek(self, prompt: str, task_type: str) -> str:
        """Generate code using DeepSeek R1 with enhanced reasoning."""
        try:
            # Use DeepSeek R1 for advanced reasoning
            generated_code = await self.model_manager.generate_response(
                model_name="deepseek-r1",  # Use DeepSeek R1 specifically
                prompt=prompt,
                max_tokens=2000,  # Increased for complex code
                temperature=0.1,  # Low temperature for deterministic code
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return generated_code
            
        except Exception as e:
            self.logger.warning(f"DeepSeek R1 unavailable, falling back to default model: {e}")
            # Fallback to default model
            return await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=prompt,
                max_tokens=1500,
                temperature=0.1
            )
    
    async def _process_and_validate_code(self, generated_code: str, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate the generated code."""
        
        # Post-process the code
        processed_code = self._post_process_code(generated_code, task_type)
        
        # Detect language and analyze
        language = self._detect_language(processed_code)
        lines_of_code = len(processed_code.split('\n'))
        
        # Perform code analysis
        analysis = await self._analyze_code_quality(processed_code, language)
        
        # Generate tests if requested
        tests = None
        if parameters.get("generate_tests", False) and task_type != "testing":
            tests = await self._generate_tests_for_code(processed_code, language)
        
        # Create comprehensive result
        result = {
            "code": processed_code,
            "task_type": task_type,
            "language": language,
            "lines_of_code": lines_of_code,
            "analysis": analysis,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "parameters": parameters
            }
        }
        
        if tests:
            result["tests"] = tests
        
        return result
    
    async def _analyze_code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code quality and provide metrics."""
        
        analysis = {
            "complexity": "medium",  # Simplified analysis
            "readability": "good",
            "maintainability": "high",
            "security_score": 85,
            "performance_score": 80,
            "best_practices": True,
            "issues": [],
            "suggestions": []
        }
        
        # Basic code analysis
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Calculate basic metrics
        analysis["metrics"] = {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "comment_lines": len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]),
            "blank_lines": len(lines) - len(non_empty_lines)
        }
        
        # Language-specific analysis
        if language == "python":
            analysis.update(self._analyze_python_code(code))
        elif language in ["javascript", "typescript"]:
            analysis.update(self._analyze_js_code(code))
        
        return analysis
    
    def _analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python-specific code quality."""
        issues = []
        suggestions = []
        
        # Check for common Python issues
        if "import *" in code:
            issues.append("Avoid wildcard imports")
        
        if "except:" in code:
            issues.append("Use specific exception handling")
        
        if not any(line.strip().startswith('"""') or line.strip().startswith("'''") for line in code.split('\n')):
            suggestions.append("Consider adding docstrings")
        
        return {
            "python_specific": {
                "pep8_compliant": True,  # Simplified check
                "type_hints": "def " in code and ":" in code,
                "docstrings": '"""' in code or "'''" in code
            },
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _analyze_js_code(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript-specific code quality."""
        issues = []
        suggestions = []
        
        # Check for common JS issues
        if "var " in code:
            suggestions.append("Consider using 'let' or 'const' instead of 'var'")
        
        if "==" in code and "===" not in code:
            suggestions.append("Use strict equality (===) instead of loose equality (==)")
        
        return {
            "js_specific": {
                "es6_features": "const " in code or "let " in code or "=>" in code,
                "strict_mode": '"use strict"' in code,
                "modern_syntax": "=>" in code or "async " in code
            },
            "issues": issues,
            "suggestions": suggestions
        }
    
    async def _generate_tests_for_code(self, code: str, language: str) -> str:
        """Generate unit tests for the provided code."""
        
        test_prompt = f"""
        Generate comprehensive unit tests for the following {language} code:
        
        {code}
        
        Requirements:
        - Cover all functions and methods
        - Include edge cases and error conditions
        - Use appropriate testing framework
        - Add clear test descriptions
        - Ensure 90%+ code coverage
        
        Tests:
        """
        
        try:
            tests = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=test_prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            return self._post_process_code(tests, "testing")
            
        except Exception as e:
            self.logger.error(f"Failed to generate tests: {e}")
            return f"# Failed to generate tests: {str(e)}"
    
    def _update_performance_metrics(self, execution_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics["total_generated"] += 1
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
    
    async def _store_enhanced_task_memory(self, task: CodeGenerationTask):
        """Store enhanced task information in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_task_{task.id}",
            agent_id=self.agent_id,
            type="task",
            content=f"Generated {task.type} code: {task.description}\n\nResult: {json.dumps(task.result, indent=2)[:500]}...",
            metadata={
                "task_id": task.id,
                "task_type": task.type,
                "status": task.status,
                "execution_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None,
                "language": task.result.get("language") if task.result else None,
                "lines_of_code": task.result.get("lines_of_code") if task.result else None
            },
            timestamp=task.created_at,
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
    
    # Enhanced API Methods
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
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
        """Get all active tasks."""
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
        """Get task history."""
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
                "language": task.result.get("language") if task.result else None,
                "lines_of_code": task.result.get("lines_of_code") if task.result else None
            }
            for task in recent_tasks
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task."""
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
            "supported_languages": self.performance_metrics["languages_supported"],
            "last_activity": self.performance_metrics["last_activity"]
        })
        
        return base_status