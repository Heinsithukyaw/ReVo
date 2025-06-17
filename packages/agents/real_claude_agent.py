#!/usr/bin/env python3
"""
Real Claude Agent Implementation
Specialized AI agent using Claude 3.5 Sonnet for code generation and documentation
"""

import asyncio
import uuid
import time
import logging
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
class CodeGenerationTask:
    """Task for code generation"""
    task_id: str
    title: str
    description: str
    language: str = "python"
    complexity: str = "medium"
    requirements: List[str] = field(default_factory=list)
    context: Optional[str] = None
    deadline: Optional[datetime] = None

@dataclass
class CodeGenerationResult:
    """Result of code generation"""
    task_id: str
    agent_id: str
    code: str
    documentation: str
    tests: Optional[str] = None
    quality_score: float = 0.0
    generation_time: float = 0.0
    cost: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class RealClaudeAgent:
    """Real Claude Agent for code generation and documentation"""
    
    def __init__(self, model_manager: RealModelManager, agent_id: Optional[str] = None):
        self.agent_id = agent_id or f"claude-{uuid.uuid4().hex[:8]}"
        self.model_manager = model_manager
        self.specialties = [
            "python_development",
            "javascript_development", 
            "api_design",
            "code_review",
            "documentation_writing",
            "test_generation",
            "refactoring",
            "debugging"
        ]
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 1.0,
            "average_quality_score": 0.0,
            "average_response_time": 0.0,
            "total_cost": 0.0,
            "lines_of_code_generated": 0
        }
        self.is_busy = False
        self.current_task: Optional[str] = None
        
    async def generate_code(self, task: CodeGenerationTask) -> CodeGenerationResult:
        """Generate code for the given task"""
        start_time = time.time()
        self.is_busy = True
        self.current_task = task.task_id
        
        try:
            logger.info(f"🤖 {self.agent_id} starting code generation: {task.title}")
            
            # Create specialized prompt for code generation
            prompt = self._create_code_generation_prompt(task)
            
            # Generate code using Claude
            request = RealGenerationRequest(
                prompt=prompt,
                model_preference=ModelType.CLAUDE_SONNET,
                max_tokens=2000,
                temperature=0.2,  # Lower temperature for more deterministic code
                system_prompt=self._get_system_prompt(task.language),
                context=task.context,
                task_type="code_generation"
            )
            
            response = await self.model_manager.generate_response(request)
            
            if not response.success:
                raise Exception(response.error_message or "Code generation failed")
            
            # Parse the generated content
            code, documentation, tests = self._parse_generated_content(response.content, task.language)
            
            # Assess code quality
            quality_score = await self._assess_code_quality(code, task)
            
            # Create result
            result = CodeGenerationResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                code=code,
                documentation=documentation,
                tests=tests,
                quality_score=quality_score,
                generation_time=time.time() - start_time,
                cost=response.cost,
                success=True,
                metadata={
                    "model_used": response.model_used.value,
                    "tokens_used": response.tokens_used,
                    "language": task.language,
                    "complexity": task.complexity
                }
            )
            
            # Update performance metrics
            await self._update_performance_metrics(result)
            
            logger.info(f"✅ {self.agent_id} completed code generation (Quality: {quality_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.agent_id} code generation failed: {e}")
            return CodeGenerationResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                code="",
                documentation="",
                quality_score=0.0,
                generation_time=time.time() - start_time,
                cost=0.0,
                success=False,
                error_message=str(e)
            )
        finally:
            self.is_busy = False
            self.current_task = None
    
    def _create_code_generation_prompt(self, task: CodeGenerationTask) -> str:
        """Create specialized prompt for code generation"""
        prompt = f"""
Generate high-quality {task.language} code for the following task:

**Task**: {task.title}
**Description**: {task.description}
**Language**: {task.language}
**Complexity**: {task.complexity}

**Requirements**:
"""
        
        for req in task.requirements:
            prompt += f"- {req}\n"
        
        prompt += f"""

**Instructions**:
1. Write clean, efficient, and well-documented {task.language} code
2. Include comprehensive docstrings/comments
3. Follow best practices and conventions for {task.language}
4. Add proper error handling where appropriate
5. Ensure code is secure and performant
6. Include type hints (if applicable)

**Output Format**:
```{task.language}
# Your code here
```

**Documentation**:
Provide clear documentation explaining:
- What the code does
- How to use it
- Any important considerations
- Example usage

**Tests** (if applicable):
```{task.language}
# Unit tests for the code
```

Please provide complete, production-ready code that addresses all requirements.
"""
        return prompt
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for specific programming language"""
        base_prompt = f"""You are an expert {language} developer with years of experience writing production-quality code. You specialize in:

- Clean, maintainable code architecture
- Comprehensive documentation and comments
- Robust error handling and edge cases
- Performance optimization
- Security best practices
- Test-driven development
- Code review and refactoring

Always write code that is:
- Readable and well-structured
- Properly documented
- Following language-specific best practices
- Secure and performant
- Easy to test and maintain
"""
        
        language_specific = {
            "python": """
- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Include comprehensive docstrings
- Handle exceptions appropriately
- Use context managers where applicable
- Prefer list comprehensions and generators for efficiency
""",
            "javascript": """
- Follow modern ES6+ standards
- Use const/let instead of var
- Include JSDoc comments
- Handle promises and async/await properly
- Use arrow functions appropriately
- Follow functional programming principles where suitable
""",
            "typescript": """
- Use strict TypeScript configuration
- Define proper interfaces and types
- Leverage TypeScript's type system fully
- Include comprehensive type annotations
- Use generics for reusable code
- Follow TypeScript best practices
""",
            "sql": """
- Write efficient, optimized queries
- Use proper indexing strategies
- Include query comments and explanations
- Handle NULL values appropriately
- Use parameterized queries for security
- Follow database-specific best practices
"""
        }
        
        return base_prompt + language_specific.get(language.lower(), "")
    
    def _parse_generated_content(self, content: str, language: str) -> tuple[str, str, Optional[str]]:
        """Parse generated content into code, documentation, and tests"""
        import re
        
        # Extract code blocks
        code_pattern = rf'```{language}(.*?)```'
        code_matches = re.findall(code_pattern, content, re.DOTALL | re.IGNORECASE)
        
        # Extract main code (first code block)
        main_code = code_matches[0].strip() if code_matches else ""
        
        # Extract tests (look for test-related code blocks)
        tests = None
        for match in code_matches[1:]:
            if any(keyword in match.lower() for keyword in ['test', 'assert', 'unittest', 'pytest']):
                tests = match.strip()
                break
        
        # Extract documentation (text between code blocks or before first code block)
        doc_parts = re.split(rf'```{language}.*?```', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Find the documentation section
        documentation = ""
        for part in doc_parts:
            if any(keyword in part.lower() for keyword in ['documentation', 'usage', 'example', 'how to']):
                documentation = part.strip()
                break
        
        # If no specific documentation found, use the part after the first code block
        if not documentation and len(doc_parts) > 1:
            documentation = doc_parts[1].strip()
        
        # Clean up the extracted content
        main_code = self._clean_code(main_code)
        documentation = self._clean_documentation(documentation)
        if tests:
            tests = self._clean_code(tests)
        
        return main_code, documentation, tests
    
    def _clean_code(self, code: str) -> str:
        """Clean and format code"""
        if not code:
            return ""
        
        # Remove common artifacts
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines at the beginning
            if not cleaned_lines and not line.strip():
                continue
            
            # Remove common comment artifacts
            if line.strip().startswith('# Your code here'):
                continue
            
            cleaned_lines.append(line)
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def _clean_documentation(self, doc: str) -> str:
        """Clean and format documentation"""
        if not doc:
            return ""
        
        # Remove markdown artifacts and clean up
        doc = re.sub(r'\*\*([^*]+)\*\*', r'\1', doc)  # Remove bold markdown
        doc = re.sub(r'\*([^*]+)\*', r'\1', doc)      # Remove italic markdown
        doc = re.sub(r'#+\s*', '', doc)               # Remove headers
        
        # Clean up multiple newlines
        doc = re.sub(r'\n\s*\n\s*\n', '\n\n', doc)
        
        return doc.strip()
    
    async def _assess_code_quality(self, code: str, task: CodeGenerationTask) -> float:
        """Assess the quality of generated code"""
        if not code:
            return 0.0
        
        quality_score = 0.0
        
        # Basic quality checks
        if len(code.strip()) > 10:
            quality_score += 0.2  # Has substantial content
        
        # Language-specific quality checks
        if task.language.lower() == "python":
            quality_score += self._assess_python_quality(code)
        elif task.language.lower() in ["javascript", "typescript"]:
            quality_score += self._assess_js_quality(code)
        else:
            quality_score += 0.3  # Default for other languages
        
        # Documentation quality
        if '"""' in code or "'''" in code or '#' in code:
            quality_score += 0.2  # Has documentation
        
        # Error handling
        if any(keyword in code.lower() for keyword in ['try:', 'except', 'catch', 'error']):
            quality_score += 0.1  # Has error handling
        
        # Function/class structure
        if any(keyword in code for keyword in ['def ', 'class ', 'function']):
            quality_score += 0.2  # Has proper structure
        
        return min(quality_score, 1.0)
    
    def _assess_python_quality(self, code: str) -> float:
        """Assess Python-specific code quality"""
        score = 0.0
        
        # Check for type hints
        if any(hint in code for hint in [': str', ': int', ': float', ': bool', ': List', ': Dict', '-> ']):
            score += 0.1
        
        # Check for docstrings
        if '"""' in code or "'''" in code:
            score += 0.1
        
        # Check for proper imports
        if code.startswith('import ') or code.startswith('from '):
            score += 0.05
        
        # Check for main guard
        if 'if __name__ == "__main__":' in code:
            score += 0.05
        
        return score
    
    def _assess_js_quality(self, code: str) -> float:
        """Assess JavaScript/TypeScript-specific code quality"""
        score = 0.0
        
        # Check for modern syntax
        if any(keyword in code for keyword in ['const ', 'let ', '=>', 'async ', 'await']):
            score += 0.1
        
        # Check for JSDoc comments
        if '/**' in code and '*/' in code:
            score += 0.1
        
        # Check for proper function declarations
        if 'function ' in code or '=>' in code:
            score += 0.1
        
        return score
    
    async def _update_performance_metrics(self, result: CodeGenerationResult):
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
        
        # Update average quality score
        if result.success:
            current_avg_quality = self.performance_metrics["average_quality_score"]
            self.performance_metrics["average_quality_score"] = (
                (current_avg_quality * (tasks_completed - 1) + result.quality_score) / tasks_completed
            )
        
        # Update average response time
        current_avg_time = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg_time * (tasks_completed - 1) + result.generation_time) / tasks_completed
        )
        
        # Count lines of code
        if result.code:
            lines_count = len([line for line in result.code.split('\n') if line.strip()])
            self.performance_metrics["lines_of_code_generated"] += lines_count
    
    async def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Review existing code and provide feedback"""
        prompt = f"""
Please review the following {language} code and provide detailed feedback:

```{language}
{code}
```

**Review Criteria**:
1. Code quality and readability
2. Best practices adherence
3. Performance considerations
4. Security issues
5. Potential bugs or edge cases
6. Documentation quality
7. Maintainability

**Output Format**:
- **Overall Score**: X/10
- **Strengths**: List of positive aspects
- **Issues**: List of problems found
- **Recommendations**: Specific improvement suggestions
- **Refactored Code**: Improved version (if needed)
"""
        
        request = RealGenerationRequest(
            prompt=prompt,
            model_preference=ModelType.CLAUDE_SONNET,
            max_tokens=1500,
            temperature=0.3,
            system_prompt=f"You are an expert {language} code reviewer with extensive experience in code quality assessment.",
            task_type="code_review"
        )
        
        response = await self.model_manager.generate_response(request)
        
        return {
            "review": response.content,
            "success": response.success,
            "cost": response.cost,
            "agent_id": self.agent_id
        }
    
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
            "Python development",
            "JavaScript/TypeScript development",
            "API design and implementation",
            "Code review and refactoring",
            "Documentation writing",
            "Unit test generation",
            "Debugging and troubleshooting",
            "Performance optimization",
            "Security best practices"
        ]


# Factory function for easy agent creation
async def create_claude_agent(model_manager: RealModelManager) -> RealClaudeAgent:
    """Create a new Claude agent"""
    agent = RealClaudeAgent(model_manager)
    logger.info(f"🤖 Created Claude agent: {agent.agent_id}")
    return agent


if __name__ == "__main__":
    # Test the Claude agent
    async def test_claude_agent():
        from src.packages.ai.real_model_manager import create_real_model_manager
        
        # Create model manager and agent
        model_manager = await create_real_model_manager()
        agent = await create_claude_agent(model_manager)
        
        # Test code generation
        task = CodeGenerationTask(
            task_id="test_001",
            title="Fibonacci Calculator",
            description="Create a function to calculate Fibonacci numbers efficiently",
            language="python",
            requirements=[
                "Use dynamic programming for efficiency",
                "Include input validation",
                "Add comprehensive docstring",
                "Handle edge cases"
            ]
        )
        
        result = await agent.generate_code(task)
        
        print(f"✅ Code generation result:")
        print(f"📝 Success: {result.success}")
        print(f"🎯 Quality Score: {result.quality_score:.2f}")
        print(f"💰 Cost: ${result.cost:.6f}")
        print(f"⏱️ Time: {result.generation_time:.2f}s")
        print(f"📄 Code:\n{result.code}")
        print(f"📚 Documentation:\n{result.documentation}")
        
        # Test code review
        review_result = await agent.review_code(result.code, "python")
        print(f"📋 Code Review:\n{review_result['review']}")
        
        await model_manager.shutdown()
    
    asyncio.run(test_claude_agent())