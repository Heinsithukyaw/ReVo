"""
Workflow Engine - Orchestrates Complex Multi-Agent Workflows

Manages workflow definition, execution, and coordination between multiple agents.
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Workflow step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """Types of workflow steps."""
    AGENT_TASK = "agent_task"
    PARALLEL_TASKS = "parallel_tasks"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    HUMAN_INPUT = "human_input"
    TOOL_EXECUTION = "tool_execution"
    INTEGRATION = "integration"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str
    name: str
    step_type: StepType
    agent_type: Optional[str] = None
    instruction: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["step_type"] = self.step_type.value
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create from dictionary."""
        data["step_type"] = StepType(data["step_type"])
        data["status"] = StepStatus(data["status"])
        return cls(**data)


@dataclass
class Workflow:
    """Workflow definition and execution state."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        data["steps"] = [step.to_dict() for step in self.steps]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create from dictionary."""
        data["status"] = WorkflowStatus(data["status"])
        data["steps"] = [WorkflowStep.from_dict(step_data) for step_data in data["steps"]]
        return cls(**data)


class WorkflowEngine:
    """Orchestrates complex multi-agent workflows."""
    
    def __init__(self, agent_framework, storage_path: Optional[Path] = None):
        self.agent_framework = agent_framework
        self.storage_path = storage_path or Path("workflows")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_tasks: Dict[str, asyncio.Task] = {}
        self.step_handlers: Dict[StepType, Callable] = {
            StepType.AGENT_TASK: self._execute_agent_task,
            StepType.PARALLEL_TASKS: self._execute_parallel_tasks,
            StepType.CONDITIONAL: self._execute_conditional,
            StepType.LOOP: self._execute_loop,
            StepType.HUMAN_INPUT: self._execute_human_input,
            StepType.TOOL_EXECUTION: self._execute_tool,
            StepType.INTEGRATION: self._execute_integration
        }
        
        # Event callbacks
        self.on_workflow_started: Optional[Callable] = None
        self.on_workflow_completed: Optional[Callable] = None
        self.on_step_started: Optional[Callable] = None
        self.on_step_completed: Optional[Callable] = None
    
    async def create_workflow(self, 
                            name: str, 
                            description: str,
                            steps: List[Dict[str, Any]],
                            variables: Optional[Dict[str, Any]] = None) -> str:
        """Create a new workflow."""
        workflow_id = str(uuid.uuid4())
        
        # Convert step dictionaries to WorkflowStep objects
        workflow_steps = []
        for step_data in steps:
            if "id" not in step_data:
                step_data["id"] = str(uuid.uuid4())
            workflow_steps.append(WorkflowStep.from_dict(step_data))
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            variables=variables or {}
        )
        
        # Save workflow
        await self._save_workflow(workflow)
        
        logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow_id
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """Start workflow execution."""
        try:
            workflow = await self._load_workflow(workflow_id)
            if not workflow:
                logger.error(f"Workflow {workflow_id} not found")
                return False
            
            if workflow.status != WorkflowStatus.PENDING:
                logger.error(f"Workflow {workflow_id} is not in pending state")
                return False
            
            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = time.time()
            
            # Store active workflow
            self.active_workflows[workflow_id] = workflow
            
            # Start execution task
            task = asyncio.create_task(self._execute_workflow(workflow))
            self.workflow_tasks[workflow_id] = task
            
            # Trigger callback
            if self.on_workflow_started:
                await self.on_workflow_started(workflow)
            
            logger.info(f"Started workflow: {workflow.name} ({workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting workflow {workflow_id}: {e}")
            return False
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause workflow execution."""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.PAUSED
        await self._save_workflow(workflow)
        
        logger.info(f"Paused workflow: {workflow_id}")
        return True
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume paused workflow."""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        if workflow.status != WorkflowStatus.PAUSED:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        await self._save_workflow(workflow)
        
        logger.info(f"Resumed workflow: {workflow_id}")
        return True
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel workflow execution."""
        if workflow_id in self.workflow_tasks:
            self.workflow_tasks[workflow_id].cancel()
            del self.workflow_tasks[workflow_id]
        
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = time.time()
            await self._save_workflow(workflow)
            del self.active_workflows[workflow_id]
        
        logger.info(f"Cancelled workflow: {workflow_id}")
        return True
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status and progress."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            workflow = await self._load_workflow(workflow_id)
        
        if not workflow:
            return None
        
        # Calculate progress
        total_steps = len(workflow.steps)
        completed_steps = len([s for s in workflow.steps if s.status == StepStatus.COMPLETED])
        progress = completed_steps / total_steps if total_steps > 0 else 0
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": progress,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "error_message": workflow.error_message
        }
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        workflows = []
        
        # Add active workflows
        for workflow in self.active_workflows.values():
            status = await self.get_workflow_status(workflow.id)
            if status:
                workflows.append(status)
        
        # Add stored workflows
        for workflow_file in self.storage_path.glob("*.json"):
            workflow_id = workflow_file.stem
            if workflow_id not in self.active_workflows:
                status = await self.get_workflow_status(workflow_id)
                if status:
                    workflows.append(status)
        
        return workflows
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute a workflow."""
        try:
            logger.info(f"Executing workflow: {workflow.name}")
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow.steps)
            
            # Execute steps in dependency order
            executed_steps = set()
            
            while len(executed_steps) < len(workflow.steps):
                # Find steps ready to execute
                ready_steps = []
                for step in workflow.steps:
                    if (step.id not in executed_steps and 
                        step.status == StepStatus.PENDING and
                        all(dep in executed_steps for dep in step.dependencies)):
                        ready_steps.append(step)
                
                if not ready_steps:
                    # Check for deadlock
                    pending_steps = [s for s in workflow.steps if s.status == StepStatus.PENDING]
                    if pending_steps:
                        raise RuntimeError("Workflow deadlock detected")
                    break
                
                # Execute ready steps
                tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(self._execute_step(workflow, step))
                    tasks.append(task)
                
                # Wait for all tasks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    step = ready_steps[i]
                    if isinstance(result, Exception):
                        step.status = StepStatus.FAILED
                        step.error_message = str(result)
                        logger.error(f"Step {step.name} failed: {result}")
                        
                        # Check if workflow should fail
                        if not step.conditions.get("continue_on_failure", False):
                            raise result
                    else:
                        step.status = StepStatus.COMPLETED
                        step.outputs = result or {}
                        
                        # Update workflow variables with step outputs
                        if step.outputs:
                            workflow.variables.update(step.outputs)
                    
                    executed_steps.add(step.id)
                
                # Save progress
                await self._save_workflow(workflow)
                
                # Check if workflow is paused
                while workflow.status == WorkflowStatus.PAUSED:
                    await asyncio.sleep(1)
            
            # Workflow completed successfully
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = time.time()
            
            # Trigger callback
            if self.on_workflow_completed:
                await self.on_workflow_completed(workflow)
            
            logger.info(f"Workflow completed: {workflow.name}")
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            workflow.completed_at = time.time()
            logger.error(f"Workflow failed: {workflow.name} - {e}")
        
        finally:
            # Clean up
            await self._save_workflow(workflow)
            if workflow.id in self.active_workflows:
                del self.active_workflows[workflow.id]
            if workflow.id in self.workflow_tasks:
                del self.workflow_tasks[workflow.id]
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> Optional[Dict[str, Any]]:
        """Execute a single workflow step."""
        try:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()
            
            # Trigger callback
            if self.on_step_started:
                await self.on_step_started(workflow, step)
            
            logger.info(f"Executing step: {step.name}")
            
            # Get step handler
            handler = self.step_handlers.get(step.step_type)
            if not handler:
                raise ValueError(f"No handler for step type: {step.step_type}")
            
            # Execute step with timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    handler(workflow, step),
                    timeout=step.timeout
                )
            else:
                result = await handler(workflow, step)
            
            step.end_time = time.time()
            
            # Trigger callback
            if self.on_step_completed:
                await self.on_step_completed(workflow, step)
            
            logger.info(f"Step completed: {step.name}")
            return result
            
        except Exception as e:
            step.end_time = time.time()
            step.error_message = str(e)
            
            # Retry logic
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING
                logger.warning(f"Step {step.name} failed, retrying ({step.retry_count}/{step.max_retries})")
                await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                return await self._execute_step(workflow, step)
            else:
                logger.error(f"Step {step.name} failed after {step.max_retries} retries: {e}")
                raise
    
    async def _execute_agent_task(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute an agent task step."""
        if not step.agent_type or not step.instruction:
            raise ValueError("Agent task requires agent_type and instruction")
        
        # Resolve variables in instruction
        instruction = self._resolve_variables(step.instruction, workflow.variables)
        
        # Get agent
        agent = await self.agent_framework.get_agent(step.agent_type)
        if not agent:
            raise ValueError(f"Agent {step.agent_type} not found")
        
        # Execute task
        result = await agent.execute_task(instruction, **step.inputs)
        
        return {"result": result}
    
    async def _execute_parallel_tasks(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute parallel tasks."""
        parallel_steps = step.inputs.get("steps", [])
        if not parallel_steps:
            return {}
        
        # Create sub-steps
        tasks = []
        for step_data in parallel_steps:
            sub_step = WorkflowStep.from_dict(step_data)
            task = asyncio.create_task(self._execute_step(workflow, sub_step))
            tasks.append(task)
        
        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        outputs = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                outputs[f"task_{i}_error"] = str(result)
            else:
                outputs[f"task_{i}_result"] = result
        
        return outputs
    
    async def _execute_conditional(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute conditional step."""
        condition = step.conditions.get("condition")
        if not condition:
            raise ValueError("Conditional step requires condition")
        
        # Evaluate condition
        condition_result = self._evaluate_condition(condition, workflow.variables)
        
        if condition_result:
            true_steps = step.inputs.get("true_steps", [])
            for step_data in true_steps:
                sub_step = WorkflowStep.from_dict(step_data)
                await self._execute_step(workflow, sub_step)
        else:
            false_steps = step.inputs.get("false_steps", [])
            for step_data in false_steps:
                sub_step = WorkflowStep.from_dict(step_data)
                await self._execute_step(workflow, sub_step)
        
        return {"condition_result": condition_result}
    
    async def _execute_loop(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute loop step."""
        loop_steps = step.inputs.get("steps", [])
        max_iterations = step.inputs.get("max_iterations", 10)
        condition = step.conditions.get("while_condition")
        
        iteration = 0
        while iteration < max_iterations:
            # Check condition if provided
            if condition and not self._evaluate_condition(condition, workflow.variables):
                break
            
            # Execute loop steps
            for step_data in loop_steps:
                sub_step = WorkflowStep.from_dict(step_data)
                await self._execute_step(workflow, sub_step)
            
            iteration += 1
        
        return {"iterations": iteration}
    
    async def _execute_human_input(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute human input step."""
        prompt = step.inputs.get("prompt", "Please provide input:")
        
        # For now, return a placeholder
        # In a real implementation, this would wait for human input
        logger.info(f"Human input required: {prompt}")
        
        return {"human_input": "placeholder_input"}
    
    async def _execute_tool(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute tool step."""
        tool_name = step.inputs.get("tool_name")
        tool_args = step.inputs.get("tool_args", {})
        
        if not tool_name:
            raise ValueError("Tool execution requires tool_name")
        
        # Get tool from agent framework
        tool = await self.agent_framework.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
        
        # Execute tool
        result = await tool.execute(**tool_args)
        
        return {"tool_result": result}
    
    async def _execute_integration(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """Execute integration step."""
        integration_name = step.inputs.get("integration_name")
        integration_method = step.inputs.get("method")
        integration_args = step.inputs.get("args", {})
        
        if not integration_name or not integration_method:
            raise ValueError("Integration step requires integration_name and method")
        
        # Get integration from agent framework
        integration = await self.agent_framework.get_integration(integration_name)
        if not integration:
            raise ValueError(f"Integration {integration_name} not found")
        
        # Execute integration method
        method = getattr(integration, integration_method, None)
        if not method:
            raise ValueError(f"Method {integration_method} not found in {integration_name}")
        
        result = await method(**integration_args)
        
        return {"integration_result": result}
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps."""
        graph = {}
        for step in steps:
            graph[step.id] = step.dependencies
        return graph
    
    def _resolve_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Resolve variables in text using ${variable} syntax."""
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate a condition string."""
        # Simple condition evaluation
        # In production, use a safer evaluation method
        try:
            # Replace variables
            resolved_condition = self._resolve_variables(condition, variables)
            return eval(resolved_condition)
        except:
            return False
    
    async def _save_workflow(self, workflow: Workflow):
        """Save workflow to storage."""
        workflow_file = self.storage_path / f"{workflow.id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(workflow.to_dict(), f, indent=2)
    
    async def _load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow from storage."""
        workflow_file = self.storage_path / f"{workflow_id}.json"
        if not workflow_file.exists():
            return None
        
        try:
            with open(workflow_file, 'r') as f:
                data = json.load(f)
            return Workflow.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id}: {e}")
            return None
    
    async def shutdown(self):
        """Shutdown the workflow engine."""
        # Cancel all active workflows
        for workflow_id in list(self.workflow_tasks.keys()):
            await self.cancel_workflow(workflow_id)
        
        logger.info("Workflow engine shutdown complete")