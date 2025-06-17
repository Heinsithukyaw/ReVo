"""Code generator agent for reVoAgent platform."""

import uuid
from typing import Dict, Any
from datetime import datetime

from .base import BaseAgent
from ..core.memory import MemoryEntry


class CodeGeneratorAgent(BaseAgent):
    """
    Specialized agent for code generation tasks.
    
    Capabilities:
    - Generate code from natural language descriptions
    - Refactor existing code
    - Add documentation and comments
    - Create unit tests
    - Code optimization
    """
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "code generation, refactoring, documentation, testing, and optimization"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a code generation task."""
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Analyze the task to determine the type of code generation needed
            task_type = self._analyze_task_type(task_description)
            
            # Generate appropriate prompt based on task type
            prompt = self._build_code_generation_prompt(task_description, task_type, parameters)
            
            # Get code generation from model
            generated_code = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=prompt,
                max_tokens=self.config.max_iterations * 50,
                temperature=0.1  # Low temperature for more deterministic code
            )
            
            # Post-process the generated code
            processed_code = self._post_process_code(generated_code, task_type)
            
            # Store the task and result in memory
            await self._store_task_memory(task_description, processed_code, task_type)
            
            # If git tool is available, create a commit
            if "git" in self.config.tools:
                await self._create_git_commit(task_description, processed_code)
            
            self.success_count += 1
            self.current_task = None
            
            return {
                "code": processed_code,
                "task_type": task_type,
                "language": self._detect_language(processed_code),
                "lines_of_code": len(processed_code.split('\n')),
                "description": task_description
            }
            
        except Exception as e:
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