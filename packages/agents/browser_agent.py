"""Browser automation agent for reVoAgent platform."""

import uuid
from typing import Dict, Any, List
from datetime import datetime

from .base import BaseAgent
from ..core.memory import MemoryEntry


class BrowserAgent(BaseAgent):
    """
    Specialized agent for browser automation and web interaction.
    
    Capabilities:
    - Web page navigation and interaction
    - Form filling and submission
    - Data extraction and web scraping
    - Screenshot capture
    - Web testing automation
    """
    
    def get_capabilities(self) -> str:
        """Get agent capabilities description."""
        return "web automation, data extraction, form filling, testing, and screenshot capture"
    
    async def execute_task(self, task_description: str, parameters: Dict[str, Any]) -> Any:
        """Execute a browser automation task."""
        self.current_task = task_description
        self.task_count += 1
        
        try:
            # Analyze the task to determine the type of browser automation needed
            task_type = self._analyze_browser_task(task_description)
            
            # Execute the appropriate browser automation
            result = await self._execute_browser_automation(task_description, task_type, parameters)
            
            # Store the task and result in memory
            await self._store_browser_task_memory(task_description, result, task_type)
            
            self.success_count += 1
            self.current_task = None
            
            return result
            
        except Exception as e:
            self.error_count += 1
            self.current_task = None
            self.logger.error(f"Browser automation task failed: {e}")
            raise
    
    def _analyze_browser_task(self, task_description: str) -> str:
        """Analyze the task description to determine the type of browser automation."""
        description_lower = task_description.lower()
        
        if any(keyword in description_lower for keyword in ["navigate", "go to", "visit", "open"]):
            return "navigation"
        elif any(keyword in description_lower for keyword in ["fill", "form", "input", "submit"]):
            return "form_interaction"
        elif any(keyword in description_lower for keyword in ["extract", "scrape", "get data", "collect"]):
            return "data_extraction"
        elif any(keyword in description_lower for keyword in ["click", "button", "link"]):
            return "element_interaction"
        elif any(keyword in description_lower for keyword in ["screenshot", "capture", "image"]):
            return "screenshot"
        elif any(keyword in description_lower for keyword in ["search", "find", "look for"]):
            return "search"
        elif any(keyword in description_lower for keyword in ["test", "verify", "check"]):
            return "testing"
        else:
            return "general_automation"
    
    async def _execute_browser_automation(
        self,
        task_description: str,
        task_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute browser automation based on task type."""
        
        # Get AI guidance for the automation steps
        automation_plan = await self._generate_automation_plan(task_description, task_type, parameters)
        
        # Execute the automation plan using browser tool
        if "browser" in self.config.tools:
            browser_result = await self._execute_with_browser_tool(automation_plan, parameters)
        else:
            # Fallback to simulated execution
            browser_result = await self._simulate_browser_execution(automation_plan, parameters)
        
        return {
            "task_type": task_type,
            "automation_plan": automation_plan,
            "result": browser_result,
            "success": True,
            "description": task_description
        }
    
    async def _generate_automation_plan(
        self,
        task_description: str,
        task_type: str,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a step-by-step automation plan using AI."""
        
        # Build prompt for automation planning
        prompt = self._build_automation_prompt(task_description, task_type, parameters)
        
        # Get automation plan from model
        plan_response = await self.model_manager.generate_response(
            model_name=self.config.model,
            prompt=prompt,
            max_tokens=1000,
            temperature=0.2
        )
        
        # Parse the response into actionable steps
        return self._parse_automation_plan(plan_response)
    
    def _build_automation_prompt(
        self,
        task_description: str,
        task_type: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Build a prompt for generating browser automation plans."""
        
        prompt_parts = [
            f"You are an expert in web automation and browser testing.",
            f"Task type: {task_type}",
            "",
            "Task description:",
            task_description,
            "",
        ]
        
        if parameters:
            prompt_parts.extend([
                "Additional parameters:",
                str(parameters),
                ""
            ])
        
        # Add task-specific guidance
        if task_type == "navigation":
            prompt_parts.extend([
                "For navigation tasks, provide steps to:",
                "1. Open the browser",
                "2. Navigate to the specified URL",
                "3. Wait for page load",
                "4. Verify successful navigation",
                ""
            ])
        elif task_type == "form_interaction":
            prompt_parts.extend([
                "For form interaction tasks, provide steps to:",
                "1. Locate form elements",
                "2. Fill in required fields",
                "3. Handle dropdowns and checkboxes",
                "4. Submit the form",
                "5. Verify submission success",
                ""
            ])
        elif task_type == "data_extraction":
            prompt_parts.extend([
                "For data extraction tasks, provide steps to:",
                "1. Navigate to the target page",
                "2. Locate data elements using selectors",
                "3. Extract text, attributes, or content",
                "4. Handle pagination if needed",
                "5. Structure and return the data",
                ""
            ])
        
        prompt_parts.extend([
            "Please provide a detailed step-by-step automation plan in the following format:",
            "Step 1: [action] - [description]",
            "Step 2: [action] - [description]",
            "...",
            "",
            "Available actions: navigate, click, fill, extract, wait, screenshot, scroll"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_automation_plan(self, plan_response: str) -> List[Dict[str, Any]]:
        """Parse the AI response into a structured automation plan."""
        steps = []
        lines = plan_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith("Step") and ":" in line:
                # Extract step information
                step_content = line.split(":", 1)[1].strip()
                
                if " - " in step_content:
                    action, description = step_content.split(" - ", 1)
                    action = action.strip().lower()
                    description = description.strip()
                    
                    steps.append({
                        "action": action,
                        "description": description,
                        "parameters": {}
                    })
        
        return steps
    
    async def _execute_with_browser_tool(
        self,
        automation_plan: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute automation plan using the browser tool."""
        results = []
        
        for step in automation_plan:
            try:
                # Prepare parameters for browser tool
                tool_params = {
                    "action": step["action"],
                    "description": step["description"],
                    **step.get("parameters", {}),
                    **parameters
                }
                
                # Execute step using browser tool
                step_result = await self.use_tool("browser", tool_params)
                results.append({
                    "step": step,
                    "result": step_result,
                    "success": True
                })
                
            except Exception as e:
                results.append({
                    "step": step,
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
                self.logger.warning(f"Browser automation step failed: {e}")
        
        return {
            "steps_executed": len(results),
            "successful_steps": len([r for r in results if r["success"]]),
            "results": results
        }
    
    async def _simulate_browser_execution(
        self,
        automation_plan: List[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate browser execution when browser tool is not available."""
        self.logger.info("Browser tool not available, simulating execution")
        
        simulated_results = []
        for step in automation_plan:
            simulated_results.append({
                "step": step,
                "result": f"Simulated execution of {step['action']}: {step['description']}",
                "success": True
            })
        
        return {
            "steps_executed": len(simulated_results),
            "successful_steps": len(simulated_results),
            "results": simulated_results,
            "simulated": True
        }
    
    async def _store_browser_task_memory(
        self,
        task_description: str,
        result: Dict[str, Any],
        task_type: str
    ) -> None:
        """Store the browser automation task in memory."""
        memory = MemoryEntry(
            id=f"{self.agent_id}_browser_{uuid.uuid4()}",
            agent_id=self.agent_id,
            type="task",
            content=f"Browser automation ({task_type}): {task_description}\nResult: {str(result)[:300]}...",
            metadata={
                "task_type": task_type,
                "automation_type": "browser",
                "steps_executed": result.get("steps_executed", 0),
                "success_rate": result.get("successful_steps", 0) / max(result.get("steps_executed", 1), 1)
            },
            timestamp=datetime.now(),
            importance=0.7
        )
        
        self.memory_manager.store_memory(memory)
    
    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a specific URL."""
        return await self.execute_task(f"Navigate to {url}", {"url": url})
    
    async def extract_data_from_page(self, url: str, selectors: List[str]) -> Dict[str, Any]:
        """Extract data from a web page using CSS selectors."""
        task_description = f"Extract data from {url} using selectors: {', '.join(selectors)}"
        return await self.execute_task(task_description, {
            "url": url,
            "selectors": selectors
        })
    
    async def fill_form(self, url: str, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill and submit a form on a web page."""
        task_description = f"Fill and submit form on {url} with data: {list(form_data.keys())}"
        return await self.execute_task(task_description, {
            "url": url,
            "form_data": form_data
        })
    
    async def take_screenshot(self, url: str, filename: str = None) -> Dict[str, Any]:
        """Take a screenshot of a web page."""
        task_description = f"Take screenshot of {url}"
        if filename:
            task_description += f" and save as {filename}"
        
        return await self.execute_task(task_description, {
            "url": url,
            "filename": filename
        })
    
    async def search_web(self, query: str, search_engine: str = "google") -> Dict[str, Any]:
        """Perform a web search and extract results."""
        task_description = f"Search for '{query}' using {search_engine} and extract results"
        return await self.execute_task(task_description, {
            "query": query,
            "search_engine": search_engine
        })