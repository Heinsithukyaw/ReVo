"""Enhanced Documentation Agent for reVoAgent platform."""

import uuid
import asyncio
import json
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .base import BaseAgent
from ..core.memory import MemoryEntry


@dataclass
class DocumentationTask:
    """Represents a documentation task."""
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


class DocumentationAgent(BaseAgent):
    """
    Enhanced Documentation Agent with real-time documentation generation.
    
    Features:
    - Real-time API documentation generation
    - Code documentation and comments
    - User guides and tutorials
    - Technical specifications
    - README and project documentation
    - Interactive documentation with examples
    - WebSocket integration for live updates
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_tasks: Dict[str, DocumentationTask] = {}
        self.task_history: List[DocumentationTask] = []
        self.performance_metrics = {
            "total_docs_generated": 0,
            "total_pages_created": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "doc_types": ["api_docs", "code_docs", "user_guides", "technical_specs", "tutorials"],
            "last_activity": None
        }
        self.websocket_callbacks = []
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "advanced documentation generation, API docs, code documentation, user guides, technical specifications, and interactive tutorials"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a documentation task with real-time monitoring."""
        start_time = time.time()
        task_id = str(uuid.uuid4())
        
        # Create task object
        task = DocumentationTask(
            id=task_id,
            type=self._analyze_doc_task(task_description),
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
            task.progress = 0.10
            await self._notify_task_update(task_id, "analyzing", 0.10)
            await asyncio.sleep(0.3)
            
            # Step 2: Generate documentation strategy (25%)
            task.progress = 0.25
            await self._notify_task_update(task_id, "planning", 0.25)
            doc_strategy = await self._generate_doc_strategy(task_description, task.type, parameters)
            
            # Step 3: Extract and analyze content (40%)
            task.progress = 0.40
            await self._notify_task_update(task_id, "extracting", 0.40)
            content_analysis = await self._analyze_content(task.type, parameters)
            
            # Step 4: Generate documentation (70%)
            task.progress = 0.70
            await self._notify_task_update(task_id, "generating", 0.70)
            documentation = await self._generate_documentation(task_description, task.type, parameters, content_analysis)
            
            # Step 5: Format and structure (85%)
            task.progress = 0.85
            await self._notify_task_update(task_id, "formatting", 0.85)
            formatted_docs = await self._format_documentation(documentation, task.type, parameters)
            
            # Step 6: Generate examples and validate (100%)
            task.progress = 1.0
            task.status = "completed"
            
            # Create comprehensive result
            result = await self._create_doc_result(
                task.type, formatted_docs, doc_strategy, content_analysis, parameters
            )
            
            task.result = result
            task.completed_at = datetime.now()
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(execution_time, True, task.type)
            
            # Store in memory
            await self._store_enhanced_doc_memory(task)
            
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
            self.logger.error(f"Documentation task failed: {e}")
            raise
    
    def _analyze_doc_task(self, task_description: str) -> str:
        """Analyze the documentation task to determine the type."""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["api", "endpoint", "swagger", "openapi"]):
            return "api_docs"
        elif any(keyword in description_lower for keyword in ["code", "function", "class", "method", "docstring"]):
            return "code_docs"
        elif any(keyword in description_lower for keyword in ["user guide", "manual", "how to", "tutorial"]):
            return "user_guides"
        elif any(keyword in description_lower for keyword in ["readme", "project", "overview", "getting started"]):
            return "project_docs"
        elif any(keyword in description_lower for keyword in ["technical", "specification", "architecture", "design"]):
            return "technical_specs"
        elif any(keyword in description_lower for keyword in ["install", "setup", "deployment", "configuration"]):
            return "installation_docs"
        elif any(keyword in description_lower for keyword in ["changelog", "release", "version", "history"]):
            return "changelog_docs"
        else:
            return "general_docs"
    
    # Enhanced Methods for Real-time Documentation
    
    async def _notify_task_update(self, task_id: str, status: str, progress: float, result: Optional[Dict] = None, error: Optional[str] = None):
        """Notify WebSocket clients about documentation task updates."""
        update = {
            "type": "documentation_update",
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
    
    async def _generate_doc_strategy(self, task_description: str, doc_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive documentation strategy."""
        
        strategy_prompt = f"""
        You are an expert technical writer and documentation strategist. Create a comprehensive documentation strategy for:
        
        Task: {task_description}
        Documentation Type: {doc_type}
        Parameters: {json.dumps(parameters, indent=2)}
        
        Create a detailed documentation strategy that includes:
        1. Documentation scope and objectives
        2. Target audience and use cases
        3. Content structure and organization
        4. Documentation format and style
        5. Examples and code samples needed
        6. Quality criteria and standards
        
        Provide a structured documentation plan.
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
                "doc_type": doc_type,
                "estimated_time": self._estimate_doc_time(doc_type),
                "tools_needed": self._get_required_doc_tools(doc_type),
                "complexity": self._assess_doc_complexity(task_description, parameters),
                "target_audience": self._identify_target_audience(doc_type)
            }
            
        except Exception as e:
            self.logger.warning(f"DeepSeek R1 unavailable, using fallback: {e}")
            return {
                "strategy": f"Standard {doc_type} documentation approach",
                "doc_type": doc_type,
                "estimated_time": "5-15 minutes",
                "tools_needed": ["markdown", "examples"],
                "complexity": "medium",
                "target_audience": "developers"
            }
    
    def _estimate_doc_time(self, doc_type: str) -> str:
        """Estimate documentation time based on type."""
        time_estimates = {
            "api_docs": "10-20 minutes",
            "code_docs": "5-15 minutes",
            "user_guides": "15-30 minutes",
            "project_docs": "10-25 minutes",
            "technical_specs": "20-40 minutes",
            "installation_docs": "8-18 minutes",
            "changelog_docs": "5-10 minutes"
        }
        return time_estimates.get(doc_type, "10-20 minutes")
    
    def _get_required_doc_tools(self, doc_type: str) -> List[str]:
        """Get required tools for documentation type."""
        tool_mapping = {
            "api_docs": ["swagger", "openapi", "postman", "markdown"],
            "code_docs": ["docstring", "sphinx", "jsdoc", "markdown"],
            "user_guides": ["markdown", "screenshots", "examples"],
            "project_docs": ["markdown", "badges", "diagrams"],
            "technical_specs": ["diagrams", "flowcharts", "markdown"],
            "installation_docs": ["markdown", "code_blocks", "screenshots"],
            "changelog_docs": ["markdown", "versioning", "git_history"]
        }
        return tool_mapping.get(doc_type, ["markdown"])
    
    def _assess_doc_complexity(self, task_description: str, parameters: Dict[str, Any]) -> str:
        """Assess documentation complexity."""
        complexity_indicators = {
            "high": ["architecture", "system design", "integration", "enterprise", "microservices"],
            "medium": ["api", "framework", "library", "service", "application"],
            "low": ["function", "method", "simple", "basic", "getting started"]
        }
        
        description_lower = task_description.lower()
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                return level
        
        # Check parameters for complexity indicators
        if "code" in parameters and len(parameters["code"]) > 1000:
            return "high"
        elif "endpoints" in parameters and len(parameters.get("endpoints", [])) > 10:
            return "high"
        
        return "medium"
    
    def _identify_target_audience(self, doc_type: str) -> str:
        """Identify target audience for documentation type."""
        audience_mapping = {
            "api_docs": "developers and integrators",
            "code_docs": "developers and maintainers",
            "user_guides": "end users and administrators",
            "project_docs": "developers and contributors",
            "technical_specs": "architects and senior developers",
            "installation_docs": "system administrators and developers",
            "changelog_docs": "users and developers"
        }
        return audience_mapping.get(doc_type, "general users")
    
    async def _analyze_content(self, doc_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content to extract documentation elements."""
        
        analysis = {
            "content_type": doc_type,
            "elements_found": [],
            "structure": {},
            "examples_needed": [],
            "complexity_score": 0.5
        }
        
        if "code" in parameters:
            code = parameters["code"]
            analysis["elements_found"].extend(self._extract_code_elements(code))
            analysis["complexity_score"] = self._calculate_code_complexity(code)
        
        if "api_spec" in parameters:
            api_spec = parameters["api_spec"]
            analysis["elements_found"].extend(self._extract_api_elements(api_spec))
        
        if "project_structure" in parameters:
            structure = parameters["project_structure"]
            analysis["structure"] = self._analyze_project_structure(structure)
        
        # Determine examples needed
        analysis["examples_needed"] = self._determine_examples_needed(doc_type, analysis["elements_found"])
        
        return analysis
    
    def _extract_code_elements(self, code: str) -> List[str]:
        """Extract documentation elements from code."""
        elements = []
        
        # Extract functions
        function_pattern = r'def\s+(\w+)\s*\('
        functions = re.findall(function_pattern, code)
        elements.extend([f"function:{func}" for func in functions])
        
        # Extract classes
        class_pattern = r'class\s+(\w+)\s*[\(:]'
        classes = re.findall(class_pattern, code)
        elements.extend([f"class:{cls}" for cls in classes])
        
        # Extract imports
        import_pattern = r'(?:from\s+\w+\s+)?import\s+(\w+)'
        imports = re.findall(import_pattern, code)
        elements.extend([f"import:{imp}" for imp in imports[:5]])  # Limit to 5
        
        return elements
    
    def _extract_api_elements(self, api_spec: Any) -> List[str]:
        """Extract elements from API specification."""
        elements = []
        
        if isinstance(api_spec, dict):
            if "paths" in api_spec:
                for path in api_spec["paths"]:
                    elements.append(f"endpoint:{path}")
            if "components" in api_spec and "schemas" in api_spec["components"]:
                for schema in api_spec["components"]["schemas"]:
                    elements.append(f"schema:{schema}")
        
        return elements
    
    def _analyze_project_structure(self, structure: Any) -> Dict[str, Any]:
        """Analyze project structure for documentation."""
        return {
            "directories": structure.get("directories", []) if isinstance(structure, dict) else [],
            "main_files": structure.get("main_files", []) if isinstance(structure, dict) else [],
            "config_files": structure.get("config_files", []) if isinstance(structure, dict) else []
        }
    
    def _calculate_code_complexity(self, code: str) -> float:
        """Calculate code complexity score."""
        lines = len(code.split('\n'))
        functions = len(re.findall(r'def\s+\w+', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        # Simple complexity calculation
        complexity = min((lines / 100 + functions / 10 + classes / 5) / 3, 1.0)
        return complexity
    
    def _determine_examples_needed(self, doc_type: str, elements: List[str]) -> List[str]:
        """Determine what examples are needed for documentation."""
        examples = []
        
        if doc_type == "api_docs":
            examples.extend(["request_example", "response_example", "error_handling"])
        elif doc_type == "code_docs":
            examples.extend(["usage_example", "parameter_example"])
        elif doc_type == "user_guides":
            examples.extend(["step_by_step", "common_scenarios", "troubleshooting"])
        
        # Add specific examples based on elements found
        for element in elements:
            if element.startswith("function:"):
                examples.append(f"example_for_{element.split(':')[1]}")
            elif element.startswith("endpoint:"):
                examples.append(f"curl_example_for_{element.split(':')[1].replace('/', '_')}")
        
        return examples[:10]  # Limit to 10 examples
    
    async def _generate_documentation(
        self, 
        task_description: str, 
        doc_type: str, 
        parameters: Dict[str, Any], 
        content_analysis: Dict[str, Any]
    ) -> str:
        """Generate the main documentation content."""
        
        doc_prompt = self._build_documentation_prompt(task_description, doc_type, parameters, content_analysis)
        
        try:
            documentation = await self.model_manager.generate_response(
                model_name=self.config.model,
                prompt=doc_prompt,
                max_tokens=3000,
                temperature=0.1
            )
            
            return documentation
            
        except Exception as e:
            self.logger.error(f"Failed to generate documentation: {e}")
            return self._generate_fallback_documentation(doc_type, parameters)
    
    def _build_documentation_prompt(
        self, 
        task_description: str, 
        doc_type: str, 
        parameters: Dict[str, Any], 
        content_analysis: Dict[str, Any]
    ) -> str:
        """Build a comprehensive documentation generation prompt."""
        
        prompt_parts = [
            f"You are an expert technical writer. Generate comprehensive {doc_type} documentation.",
            "",
            f"Task: {task_description}",
            f"Documentation Type: {doc_type}",
            f"Target Audience: {self._identify_target_audience(doc_type)}",
            "",
            "Content Analysis:",
            f"- Elements found: {', '.join(content_analysis.get('elements_found', [])[:10])}",
            f"- Complexity: {content_analysis.get('complexity_score', 0.5):.2f}",
            f"- Examples needed: {', '.join(content_analysis.get('examples_needed', [])[:5])}",
            ""
        ]
        
        # Add specific content based on parameters
        if "code" in parameters:
            prompt_parts.extend([
                "Code to document:",
                "```",
                parameters["code"][:1000],  # Limit code length
                "```",
                ""
            ])
        
        if "api_spec" in parameters:
            prompt_parts.extend([
                "API Specification:",
                str(parameters["api_spec"])[:500],
                ""
            ])
        
        # Add documentation type specific instructions
        if doc_type == "api_docs":
            prompt_parts.extend([
                "Generate API documentation that includes:",
                "1. Overview and purpose",
                "2. Authentication requirements",
                "3. Endpoint descriptions with HTTP methods",
                "4. Request/response examples with JSON",
                "5. Error codes and handling",
                "6. Rate limiting information",
                "7. SDK/client examples",
                ""
            ])
        elif doc_type == "code_docs":
            prompt_parts.extend([
                "Generate code documentation that includes:",
                "1. Module/class overview",
                "2. Function/method descriptions",
                "3. Parameter explanations with types",
                "4. Return value descriptions",
                "5. Usage examples",
                "6. Exception handling",
                "7. Best practices",
                ""
            ])
        elif doc_type == "user_guides":
            prompt_parts.extend([
                "Generate user guide documentation that includes:",
                "1. Introduction and overview",
                "2. Getting started section",
                "3. Step-by-step instructions",
                "4. Common use cases",
                "5. Troubleshooting section",
                "6. FAQ",
                "7. Additional resources",
                ""
            ])
        elif doc_type == "project_docs":
            prompt_parts.extend([
                "Generate project documentation that includes:",
                "1. Project description and purpose",
                "2. Features and capabilities",
                "3. Installation instructions",
                "4. Quick start guide",
                "5. Configuration options",
                "6. Contributing guidelines",
                "7. License and credits",
                ""
            ])
        
        prompt_parts.extend([
            "Use clear, professional language with proper markdown formatting.",
            "Include code examples where appropriate.",
            "Make it comprehensive but easy to understand."
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_documentation(self, doc_type: str, parameters: Dict[str, Any]) -> str:
        """Generate fallback documentation when AI generation fails."""
        
        fallback_docs = {
            "api_docs": f"""# API Documentation

## Overview
This API provides endpoints for {parameters.get('service_name', 'the service')}.

## Authentication
Include your API key in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### GET /api/resource
Retrieve resources from the system.

**Response:**
```json
{{
  "data": [],
  "status": "success"
}}
```

## Error Handling
The API returns standard HTTP status codes and JSON error responses.
""",
            
            "code_docs": f"""# Code Documentation

## Overview
This module provides functionality for {parameters.get('module_name', 'the application')}.

## Functions

### main_function()
Main entry point for the application.

**Parameters:**
- None

**Returns:**
- Success status

**Example:**
```python
result = main_function()
print(result)
```
""",
            
            "user_guides": f"""# User Guide

## Getting Started
Welcome to {parameters.get('product_name', 'the application')}!

## Installation
1. Download the application
2. Follow the setup wizard
3. Configure your preferences

## Basic Usage
1. Open the application
2. Create a new project
3. Start working with your data

## Troubleshooting
If you encounter issues, please check our FAQ or contact support.
"""
        }
        
        return fallback_docs.get(doc_type, "# Documentation\n\nDocumentation content will be generated here.")
    
    async def _format_documentation(self, documentation: str, doc_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Format and structure the documentation."""
        
        # Clean up the documentation
        cleaned_doc = self._clean_documentation(documentation)
        
        # Extract sections
        sections = self._extract_sections(cleaned_doc)
        
        # Generate table of contents
        toc = self._generate_table_of_contents(sections)
        
        # Add metadata
        metadata = {
            "title": self._generate_title(doc_type, parameters),
            "description": self._generate_description(doc_type, parameters),
            "version": parameters.get("version", "1.0.0"),
            "last_updated": datetime.now().isoformat(),
            "doc_type": doc_type
        }
        
        return {
            "content": cleaned_doc,
            "sections": sections,
            "table_of_contents": toc,
            "metadata": metadata,
            "word_count": len(cleaned_doc.split()),
            "estimated_reading_time": self._calculate_reading_time(cleaned_doc)
        }
    
    def _clean_documentation(self, documentation: str) -> str:
        """Clean and format documentation content."""
        # Remove extra whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', documentation)
        
        # Ensure proper markdown formatting
        cleaned = re.sub(r'^(#{1,6})\s*(.+)$', r'\1 \2', cleaned, flags=re.MULTILINE)
        
        # Clean up code blocks
        cleaned = re.sub(r'```(\w+)?\n\n', r'```\1\n', cleaned)
        
        return cleaned.strip()
    
    def _extract_sections(self, documentation: str) -> List[Dict[str, Any]]:
        """Extract sections from documentation."""
        sections = []
        lines = documentation.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content).strip(),
                        "level": current_section.count('#')
                    })
                
                # Start new section
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content).strip(),
                "level": current_section.count('#')
            })
        
        return sections
    
    def _generate_table_of_contents(self, sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate table of contents from sections."""
        toc = []
        
        for section in sections:
            title = section["title"].lstrip('#').strip()
            level = section["level"]
            anchor = title.lower().replace(' ', '-').replace('/', '').replace('(', '').replace(')', '')
            
            toc.append({
                "title": title,
                "anchor": anchor,
                "level": level
            })
        
        return toc
    
    def _generate_title(self, doc_type: str, parameters: Dict[str, Any]) -> str:
        """Generate appropriate title for documentation."""
        title_templates = {
            "api_docs": f"{parameters.get('service_name', 'API')} Documentation",
            "code_docs": f"{parameters.get('module_name', 'Code')} Documentation",
            "user_guides": f"{parameters.get('product_name', 'User')} Guide",
            "project_docs": f"{parameters.get('project_name', 'Project')} README",
            "technical_specs": f"{parameters.get('system_name', 'Technical')} Specification"
        }
        
        return title_templates.get(doc_type, "Documentation")
    
    def _generate_description(self, doc_type: str, parameters: Dict[str, Any]) -> str:
        """Generate description for documentation."""
        descriptions = {
            "api_docs": "Comprehensive API documentation with endpoints, examples, and integration guides.",
            "code_docs": "Detailed code documentation with function descriptions, parameters, and usage examples.",
            "user_guides": "Step-by-step user guide with instructions, examples, and troubleshooting.",
            "project_docs": "Project overview with setup instructions, features, and contribution guidelines.",
            "technical_specs": "Technical specification with architecture details and implementation guidelines."
        }
        
        return descriptions.get(doc_type, "Comprehensive documentation")
    
    def _calculate_reading_time(self, content: str) -> str:
        """Calculate estimated reading time."""
        words = len(content.split())
        minutes = max(1, round(words / 200))  # Average reading speed: 200 words/minute
        
        if minutes == 1:
            return "1 minute"
        else:
            return f"{minutes} minutes"
    
    async def _create_doc_result(
        self, 
        doc_type: str, 
        formatted_docs: Dict[str, Any], 
        doc_strategy: Dict[str, Any],
        content_analysis: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive documentation result."""
        
        # Generate quality metrics
        quality_metrics = self._calculate_doc_quality(formatted_docs, content_analysis)
        
        # Generate recommendations
        recommendations = await self._generate_doc_recommendations(doc_type, quality_metrics, content_analysis)
        
        return {
            "doc_type": doc_type,
            "strategy": doc_strategy,
            "documentation": formatted_docs,
            "content_analysis": content_analysis,
            "quality_metrics": quality_metrics,
            "recommendations": recommendations,
            "export_formats": self._get_export_formats(doc_type),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "doc_session_id": str(uuid.uuid4()),
                "version": "1.0.0"
            }
        }
    
    def _calculate_doc_quality(self, formatted_docs: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate documentation quality metrics."""
        
        content = formatted_docs["content"]
        sections = formatted_docs["sections"]
        
        # Calculate various quality metrics
        completeness = min(len(sections) / 5, 1.0)  # Expect at least 5 sections for completeness
        readability = self._calculate_readability_score(content)
        structure_score = min(len(formatted_docs["table_of_contents"]) / 8, 1.0)  # Good structure has 8+ TOC items
        example_coverage = self._calculate_example_coverage(content, content_analysis)
        
        overall_score = (completeness * 0.3 + readability * 0.25 + structure_score * 0.25 + example_coverage * 0.2)
        
        return {
            "overall_score": round(overall_score, 3),
            "completeness": round(completeness, 3),
            "readability": round(readability, 3),
            "structure_score": round(structure_score, 3),
            "example_coverage": round(example_coverage, 3),
            "word_count": formatted_docs["word_count"],
            "section_count": len(sections),
            "estimated_reading_time": formatted_docs["estimated_reading_time"]
        }
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score based on content analysis."""
        sentences = content.count('.') + content.count('!') + content.count('?')
        words = len(content.split())
        
        if sentences == 0:
            return 0.5
        
        avg_sentence_length = words / sentences
        
        # Good readability: 15-20 words per sentence
        if 15 <= avg_sentence_length <= 20:
            return 1.0
        elif 10 <= avg_sentence_length <= 25:
            return 0.8
        else:
            return 0.6
    
    def _calculate_example_coverage(self, content: str, content_analysis: Dict[str, Any]) -> float:
        """Calculate how well examples cover the documented elements."""
        examples_needed = len(content_analysis.get("examples_needed", []))
        code_blocks = content.count("```")
        
        if examples_needed == 0:
            return 1.0
        
        coverage = min(code_blocks / examples_needed, 1.0)
        return coverage
    
    async def _generate_doc_recommendations(
        self, 
        doc_type: str, 
        quality_metrics: Dict[str, Any], 
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable documentation recommendations."""
        
        recommendations = []
        
        # Quality-based recommendations
        if quality_metrics["completeness"] < 0.8:
            recommendations.append("Add more comprehensive sections to improve completeness")
        
        if quality_metrics["example_coverage"] < 0.7:
            recommendations.append("Include more code examples and practical demonstrations")
        
        if quality_metrics["structure_score"] < 0.7:
            recommendations.append("Improve document structure with better organization and navigation")
        
        # Type-specific recommendations
        if doc_type == "api_docs":
            recommendations.extend([
                "Add interactive API examples with curl commands",
                "Include authentication and error handling examples",
                "Provide SDK examples in multiple languages"
            ])
        elif doc_type == "user_guides":
            recommendations.extend([
                "Add screenshots and visual aids",
                "Include troubleshooting section",
                "Provide step-by-step tutorials"
            ])
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _get_export_formats(self, doc_type: str) -> List[str]:
        """Get available export formats for documentation type."""
        base_formats = ["markdown", "html", "pdf"]
        
        format_mapping = {
            "api_docs": base_formats + ["openapi", "postman"],
            "code_docs": base_formats + ["sphinx", "jsdoc"],
            "user_guides": base_formats + ["docx", "epub"],
            "project_docs": base_formats + ["wiki"],
            "technical_specs": base_formats + ["latex", "docx"]
        }
        
        return format_mapping.get(doc_type, base_formats)
    
    def _update_performance_metrics(self, execution_time: float, success: bool, doc_type: str):
        """Update performance metrics."""
        self.performance_metrics["total_docs_generated"] += 1
        if success:
            self.performance_metrics["total_pages_created"] += 1
        
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
    
    async def _store_enhanced_doc_memory(self, task: DocumentationTask):
        """Store enhanced documentation session in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_doc_{task.id}",
            agent_id=self.agent_id,
            type="task",
            content=f"Documentation session ({task.type}): {task.description}\n\nResult: {json.dumps(task.result, indent=2)[:500]}...",
            metadata={
                "task_id": task.id,
                "doc_type": task.type,
                "status": task.status,
                "execution_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else None,
                "quality_score": task.result.get("quality_metrics", {}).get("overall_score") if task.result else None,
                "word_count": task.result.get("quality_metrics", {}).get("word_count") if task.result else None
            },
            timestamp=task.created_at,
            importance=0.8
        )
        
        self.memory_manager.store_memory(memory)
    
    # Enhanced API Methods
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific documentation task."""
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
        """Get all active documentation tasks."""
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
        """Get documentation task history."""
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
                "quality_score": task.result.get("quality_metrics", {}).get("overall_score") if task.result else None,
                "word_count": task.result.get("quality_metrics", {}).get("word_count") if task.result else None
            }
            for task in recent_tasks
        ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active documentation task."""
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
            "supported_doc_types": self.performance_metrics["doc_types"],
            "last_activity": self.performance_metrics["last_activity"]
        })
        
        return base_status
    
    # Convenience Methods for Different Documentation Types
    
    async def generate_api_documentation(self, api_spec: Dict[str, Any], service_name: str = None) -> Dict[str, Any]:
        """Generate API documentation from specification."""
        return await self.execute_task(
            f"Generate comprehensive API documentation for {service_name or 'service'}",
            {"api_spec": api_spec, "service_name": service_name}
        )
    
    async def generate_code_documentation(self, code: str, module_name: str = None) -> Dict[str, Any]:
        """Generate code documentation from source code."""
        return await self.execute_task(
            f"Generate comprehensive code documentation for {module_name or 'module'}",
            {"code": code, "module_name": module_name}
        )
    
    async def generate_user_guide(self, product_name: str, features: List[str] = None) -> Dict[str, Any]:
        """Generate user guide documentation."""
        return await self.execute_task(
            f"Generate comprehensive user guide for {product_name}",
            {"product_name": product_name, "features": features or []}
        )
    
    async def generate_project_readme(self, project_name: str, description: str, features: List[str] = None) -> Dict[str, Any]:
        """Generate project README documentation."""
        return await self.execute_task(
            f"Generate comprehensive README for {project_name}",
            {"project_name": project_name, "description": description, "features": features or []}
        )
    
    async def generate_technical_specification(self, system_name: str, architecture: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate technical specification documentation."""
        return await self.execute_task(
            f"Generate technical specification for {system_name}",
            {"system_name": system_name, "architecture": architecture or {}}
        )