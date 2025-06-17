#!/usr/bin/env python3
"""
Advanced Workflow Engine for reVoAgent
Sophisticated workflow orchestration with visual builder and human-in-the-loop

This module implements an advanced workflow engine featuring:
- Visual workflow builder and designer
- Multi-agent orchestration and coordination
- Human-in-the-loop integration
- Conditional logic and branching
- Real-time execution monitoring
- Workflow templates and reusability
- Event-driven architecture
- Performance optimization
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from collections import defaultdict, deque
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Workflow node types"""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    HUMAN_INPUT = "human_input"
    AI_AGENT = "ai_agent"
    API_CALL = "api_call"
    DATA_TRANSFORM = "data_transform"
    CONDITION = "condition"
    LOOP = "loop"
    DELAY = "delay"
    NOTIFICATION = "notification"

class ExecutionStatus(Enum):
    """Execution status for nodes and workflows"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    SKIPPED = "skipped"

class Priority(Enum):
    """Workflow priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class WorkflowNode:
    """Workflow node definition"""
    node_id: str
    node_type: NodeType
    name: str
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)  # Input node IDs
    outputs: List[str] = field(default_factory=list)  # Output node IDs
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution properties
    timeout: Optional[int] = None  # seconds
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 5  # seconds

@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    node_executions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    error_message: Optional[str] = None
    priority: Priority = Priority.NORMAL
    created_by: Optional[str] = None

@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    version: str
    nodes: Dict[str, WorkflowNode]
    edges: List[Dict[str, str]]  # [{"from": node_id, "to": node_id, "condition": optional}]
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

@dataclass
class HumanTask:
    """Human task for human-in-the-loop workflows"""
    task_id: str
    execution_id: str
    node_id: str
    title: str
    description: str
    form_schema: Dict[str, Any]
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    response_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

class WorkflowNodeExecutor:
    """Base class for workflow node executors"""
    
    async def execute(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow node"""
        raise NotImplementedError

class TaskNodeExecutor(WorkflowNodeExecutor):
    """Executor for task nodes"""
    
    async def execute(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task node"""
        task_type = node.config.get("task_type", "generic")
        
        if task_type == "ai_generation":
            return await self._execute_ai_generation(node, context)
        elif task_type == "data_processing":
            return await self._execute_data_processing(node, context)
        elif task_type == "api_call":
            return await self._execute_api_call(node, context)
        else:
            return await self._execute_generic_task(node, context)
    
    async def _execute_ai_generation(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI generation task"""
        prompt = node.config.get("prompt", "")
        model = node.config.get("model", "default")
        
        # Simulate AI generation
        await asyncio.sleep(1)  # Simulate processing time
        
        return {
            "result": f"AI generated response for: {prompt}",
            "model_used": model,
            "tokens": 150,
            "cost": 0.001
        }
    
    async def _execute_data_processing(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data processing task"""
        operation = node.config.get("operation", "transform")
        input_data = context.get("input_data", {})
        
        # Simulate data processing
        await asyncio.sleep(0.5)
        
        return {
            "processed_data": f"Processed {len(input_data)} items",
            "operation": operation,
            "records_processed": len(input_data)
        }
    
    async def _execute_api_call(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call task"""
        url = node.config.get("url", "")
        method = node.config.get("method", "GET")
        
        # Simulate API call
        await asyncio.sleep(0.8)
        
        return {
            "response": f"API response from {url}",
            "status_code": 200,
            "method": method
        }
    
    async def _execute_generic_task(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic task"""
        await asyncio.sleep(0.3)
        return {"result": f"Task {node.name} completed"}

class DecisionNodeExecutor(WorkflowNodeExecutor):
    """Executor for decision nodes"""
    
    async def execute(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a decision node"""
        condition = node.config.get("condition", "true")
        
        # Evaluate condition (simplified)
        if condition == "true":
            decision = True
        elif condition == "false":
            decision = False
        else:
            # Simple condition evaluation
            decision = self._evaluate_condition(condition, context)
        
        return {
            "decision": decision,
            "condition": condition,
            "next_path": "true" if decision else "false"
        }
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition"""
        # This is a simplified condition evaluator
        # In a real implementation, you'd use a proper expression parser
        try:
            # Replace context variables
            for key, value in context.items():
                condition = condition.replace(f"${key}", str(value))
            
            # Evaluate simple conditions
            if ">" in condition:
                left, right = condition.split(">")
                return float(left.strip()) > float(right.strip())
            elif "<" in condition:
                left, right = condition.split("<")
                return float(left.strip()) < float(right.strip())
            elif "==" in condition:
                left, right = condition.split("==")
                return left.strip() == right.strip()
            else:
                return bool(condition)
        except:
            return False

class HumanInputNodeExecutor(WorkflowNodeExecutor):
    """Executor for human input nodes"""
    
    def __init__(self, workflow_engine):
        self.workflow_engine = workflow_engine
    
    async def execute(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a human input node"""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        execution_id = context.get("execution_id")
        
        # Create human task
        human_task = HumanTask(
            task_id=task_id,
            execution_id=execution_id,
            node_id=node.node_id,
            title=node.config.get("title", node.name),
            description=node.config.get("description", ""),
            form_schema=node.config.get("form_schema", {}),
            assigned_to=node.config.get("assigned_to"),
            due_date=datetime.now(timezone.utc) + timedelta(hours=node.config.get("timeout_hours", 24))
        )
        
        # Store human task
        self.workflow_engine.human_tasks[task_id] = human_task
        
        # Return pending status - execution will resume when human completes task
        return {
            "status": "waiting_for_human",
            "task_id": task_id,
            "assigned_to": human_task.assigned_to
        }

class AdvancedWorkflowEngine:
    """
    Advanced Workflow Engine
    
    Provides sophisticated workflow orchestration with visual builder,
    multi-agent coordination, and human-in-the-loop capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the workflow engine"""
        self.config = config or {}
        
        # Storage
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.human_tasks: Dict[str, HumanTask] = {}
        
        # Execution queue
        self.execution_queue: deque = deque()
        self.running_executions: Dict[str, asyncio.Task] = {}
        
        # Node executors
        self.node_executors = {
            NodeType.TASK: TaskNodeExecutor(),
            NodeType.DECISION: DecisionNodeExecutor(),
            NodeType.HUMAN_INPUT: HumanInputNodeExecutor(self),
        }
        
        # Performance metrics
        self.metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0,
            "active_executions": 0
        }
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("🔄 Advanced Workflow Engine initialized")
    
    async def initialize(self):
        """Async initialization method for compatibility"""
        # Already initialized in __init__, this is for compatibility
        return self

    async def create_workflow(self, name: str, description: str, created_by: Optional[str] = None) -> str:
        """Create a new workflow definition"""
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version="1.0.0",
            nodes={},
            edges=[],
            created_by=created_by
        )
        
        self.workflows[workflow_id] = workflow
        
        await self._emit_event("workflow_created", {
            "workflow_id": workflow_id,
            "name": name,
            "created_by": created_by
        })
        
        logger.info(f"📋 Workflow created: {name} ({workflow_id})")
        return workflow_id

    async def add_node(self, workflow_id: str, node_type: NodeType, name: str, 
                      config: Optional[Dict[str, Any]] = None, 
                      position: Optional[Dict[str, float]] = None) -> str:
        """Add a node to a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        
        node = WorkflowNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            config=config or {},
            position=position or {"x": 0, "y": 0}
        )
        
        self.workflows[workflow_id].nodes[node_id] = node
        
        logger.info(f"➕ Node added to workflow {workflow_id}: {name} ({node_type.value})")
        return node_id

    async def connect_nodes(self, workflow_id: str, from_node_id: str, to_node_id: str, 
                           condition: Optional[str] = None):
        """Connect two nodes in a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        if from_node_id not in workflow.nodes or to_node_id not in workflow.nodes:
            raise ValueError("One or both nodes not found in workflow")
        
        # Add edge
        edge = {"from": from_node_id, "to": to_node_id}
        if condition:
            edge["condition"] = condition
        
        workflow.edges.append(edge)
        
        # Update node connections
        workflow.nodes[from_node_id].outputs.append(to_node_id)
        workflow.nodes[to_node_id].inputs.append(from_node_id)
        
        logger.info(f"🔗 Nodes connected in workflow {workflow_id}: {from_node_id} -> {to_node_id}")

    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None,
                              priority: Priority = Priority.NORMAL, created_by: Optional[str] = None) -> str:
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            input_data=input_data or {},
            priority=priority,
            created_by=created_by
        )
        
        self.executions[execution_id] = execution
        
        # Add to execution queue
        self.execution_queue.append(execution_id)
        
        # Start execution
        task = asyncio.create_task(self._execute_workflow_async(execution_id))
        self.running_executions[execution_id] = task
        
        await self._emit_event("workflow_execution_started", {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "created_by": created_by
        })
        
        logger.info(f"🚀 Workflow execution started: {execution_id}")
        return execution_id

    async def _execute_workflow_async(self, execution_id: str):
        """Execute workflow asynchronously"""
        try:
            execution = self.executions[execution_id]
            workflow = self.workflows[execution.workflow_id]
            
            execution.status = ExecutionStatus.RUNNING
            execution.context = {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "input_data": execution.input_data
            }
            
            self.metrics["active_executions"] += 1
            
            # Find start nodes
            start_nodes = [node for node in workflow.nodes.values() 
                          if node.node_type == NodeType.START or not node.inputs]
            
            if not start_nodes:
                raise ValueError("No start nodes found in workflow")
            
            # Execute workflow using topological execution
            await self._execute_nodes(execution, start_nodes)
            
            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            
            self.metrics["successful_executions"] += 1
            
            await self._emit_event("workflow_execution_completed", {
                "execution_id": execution_id,
                "workflow_id": execution.workflow_id,
                "duration": (execution.completed_at - execution.started_at).total_seconds()
            })
            
            logger.info(f"✅ Workflow execution completed: {execution_id}")
            
        except Exception as e:
            execution = self.executions[execution_id]
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            
            self.metrics["failed_executions"] += 1
            
            await self._emit_event("workflow_execution_failed", {
                "execution_id": execution_id,
                "error": str(e)
            })
            
            logger.error(f"❌ Workflow execution failed: {execution_id} - {e}")
            
        finally:
            self.metrics["active_executions"] -= 1
            self.metrics["total_executions"] += 1
            
            # Remove from running executions
            if execution_id in self.running_executions:
                del self.running_executions[execution_id]

    async def _execute_nodes(self, execution: WorkflowExecution, nodes: List[WorkflowNode]):
        """Execute a list of nodes"""
        workflow = self.workflows[execution.workflow_id]
        
        for node in nodes:
            if execution.status != ExecutionStatus.RUNNING:
                break
            
            try:
                # Execute node
                start_time = time.time()
                result = await self._execute_node(node, execution.context)
                execution_time = time.time() - start_time
                
                # Store node execution result
                execution.node_executions[node.node_id] = {
                    "status": ExecutionStatus.COMPLETED.value,
                    "result": result,
                    "execution_time": execution_time,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Update context with result
                execution.context[f"node_{node.node_id}_result"] = result
                
                # Handle special node types
                if node.node_type == NodeType.HUMAN_INPUT and result.get("status") == "waiting_for_human":
                    # Pause execution for human input
                    execution.status = ExecutionStatus.WAITING
                    return
                
                # Find next nodes to execute
                next_nodes = self._get_next_nodes(workflow, node, result)
                if next_nodes:
                    await self._execute_nodes(execution, next_nodes)
                
            except Exception as e:
                execution.node_executions[node.node_id] = {
                    "status": ExecutionStatus.FAILED.value,
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
                
                if node.retry_count < node.max_retries:
                    node.retry_count += 1
                    await asyncio.sleep(node.retry_delay)
                    # Retry node execution
                    await self._execute_nodes(execution, [node])
                else:
                    raise e

    async def _execute_node(self, node: WorkflowNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node"""
        executor = self.node_executors.get(node.node_type)
        if not executor:
            raise ValueError(f"No executor found for node type: {node.node_type}")
        
        # Apply timeout if specified
        if node.timeout:
            try:
                result = await asyncio.wait_for(
                    executor.execute(node, context),
                    timeout=node.timeout
                )
            except asyncio.TimeoutError:
                raise Exception(f"Node {node.node_id} timed out after {node.timeout} seconds")
        else:
            result = await executor.execute(node, context)
        
        return result

    def _get_next_nodes(self, workflow: WorkflowDefinition, current_node: WorkflowNode, 
                       result: Dict[str, Any]) -> List[WorkflowNode]:
        """Get next nodes to execute based on current node result"""
        next_nodes = []
        
        for edge in workflow.edges:
            if edge["from"] == current_node.node_id:
                # Check condition if present
                if "condition" in edge:
                    condition = edge["condition"]
                    if current_node.node_type == NodeType.DECISION:
                        # For decision nodes, use the decision result
                        if (condition == "true" and result.get("decision")) or \
                           (condition == "false" and not result.get("decision")):
                            next_nodes.append(workflow.nodes[edge["to"]])
                    else:
                        # For other nodes, evaluate condition
                        if self._evaluate_edge_condition(condition, result):
                            next_nodes.append(workflow.nodes[edge["to"]])
                else:
                    # No condition, always follow edge
                    next_nodes.append(workflow.nodes[edge["to"]])
        
        return next_nodes

    def _evaluate_edge_condition(self, condition: str, result: Dict[str, Any]) -> bool:
        """Evaluate edge condition"""
        # Simplified condition evaluation
        # In a real implementation, use a proper expression parser
        try:
            if condition == "success":
                return result.get("status") != "failed"
            elif condition == "failure":
                return result.get("status") == "failed"
            else:
                return True
        except:
            return True

    async def complete_human_task(self, task_id: str, response_data: Dict[str, Any], 
                                 completed_by: Optional[str] = None):
        """Complete a human task and resume workflow execution"""
        if task_id not in self.human_tasks:
            raise ValueError(f"Human task {task_id} not found")
        
        human_task = self.human_tasks[task_id]
        human_task.status = ExecutionStatus.COMPLETED
        human_task.response_data = response_data
        human_task.completed_at = datetime.now(timezone.utc)
        
        # Resume workflow execution
        execution = self.executions[human_task.execution_id]
        if execution.status == ExecutionStatus.WAITING:
            execution.status = ExecutionStatus.RUNNING
            execution.context[f"human_task_{task_id}_response"] = response_data
            
            # Continue execution from the human input node
            workflow = self.workflows[execution.workflow_id]
            human_node = workflow.nodes[human_task.node_id]
            next_nodes = self._get_next_nodes(workflow, human_node, {"status": "completed"})
            
            if next_nodes:
                task = asyncio.create_task(self._execute_nodes(execution, next_nodes))
                self.running_executions[execution.execution_id] = task
        
        await self._emit_event("human_task_completed", {
            "task_id": task_id,
            "execution_id": human_task.execution_id,
            "completed_by": completed_by
        })
        
        logger.info(f"👤 Human task completed: {task_id}")

    async def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow engine metrics"""
        # Calculate average execution time
        completed_executions = [e for e in self.executions.values() 
                              if e.status == ExecutionStatus.COMPLETED and e.completed_at]
        
        if completed_executions:
            total_time = sum((e.completed_at - e.started_at).total_seconds() 
                           for e in completed_executions)
            avg_time = total_time / len(completed_executions)
        else:
            avg_time = 0
        
        self.metrics["average_execution_time"] = avg_time
        
        return {
            "workflows": {
                "total": len(self.workflows),
                "active": sum(1 for w in self.workflows.values() if w.is_active)
            },
            "executions": {
                "total": self.metrics["total_executions"],
                "successful": self.metrics["successful_executions"],
                "failed": self.metrics["failed_executions"],
                "active": self.metrics["active_executions"],
                "success_rate": (self.metrics["successful_executions"] / max(self.metrics["total_executions"], 1)) * 100
            },
            "human_tasks": {
                "total": len(self.human_tasks),
                "pending": sum(1 for t in self.human_tasks.values() if t.status == ExecutionStatus.PENDING),
                "completed": sum(1 for t in self.human_tasks.values() if t.status == ExecutionStatus.COMPLETED)
            },
            "performance": {
                "average_execution_time": avg_time,
                "queue_size": len(self.execution_queue)
            }
        }

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit workflow event"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler"""
        self.event_handlers[event_type].append(handler)

    async def export_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Export workflow definition"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "name": node.name,
                    "description": node.description,
                    "config": node.config,
                    "position": node.position,
                    "metadata": node.metadata
                }
                for node in workflow.nodes.values()
            ],
            "edges": workflow.edges,
            "input_schema": workflow.input_schema,
            "output_schema": workflow.output_schema,
            "metadata": workflow.metadata,
            "created_at": workflow.created_at.isoformat(),
            "created_by": workflow.created_by,
            "tags": workflow.tags
        }

# Example usage and testing
async def main():
    """Example usage of Advanced Workflow Engine"""
    
    print("🔄 Advanced Workflow Engine Demo")
    print("=" * 50)
    
    # Initialize workflow engine
    engine = AdvancedWorkflowEngine()
    
    try:
        # Create a workflow
        workflow_id = await engine.create_workflow(
            name="AI Content Generation Workflow",
            description="Generate and review AI content with human approval",
            created_by="demo_user"
        )
        print(f"✅ Workflow created: {workflow_id}")
        
        # Add nodes
        start_node = await engine.add_node(
            workflow_id, NodeType.START, "Start",
            position={"x": 100, "y": 100}
        )
        
        ai_node = await engine.add_node(
            workflow_id, NodeType.TASK, "Generate Content",
            config={
                "task_type": "ai_generation",
                "prompt": "Write a blog post about AI",
                "model": "gpt-4"
            },
            position={"x": 300, "y": 100}
        )
        
        human_node = await engine.add_node(
            workflow_id, NodeType.HUMAN_INPUT, "Review Content",
            config={
                "title": "Review Generated Content",
                "description": "Please review and approve the AI-generated content",
                "form_schema": {
                    "approved": {"type": "boolean", "label": "Approve content?"},
                    "feedback": {"type": "text", "label": "Feedback (optional)"}
                },
                "timeout_hours": 24
            },
            position={"x": 500, "y": 100}
        )
        
        decision_node = await engine.add_node(
            workflow_id, NodeType.DECISION, "Check Approval",
            config={"condition": "$approved == true"},
            position={"x": 700, "y": 100}
        )
        
        end_node = await engine.add_node(
            workflow_id, NodeType.END, "End",
            position={"x": 900, "y": 100}
        )
        
        # Connect nodes
        await engine.connect_nodes(workflow_id, start_node, ai_node)
        await engine.connect_nodes(workflow_id, ai_node, human_node)
        await engine.connect_nodes(workflow_id, human_node, decision_node)
        await engine.connect_nodes(workflow_id, decision_node, end_node, "true")
        await engine.connect_nodes(workflow_id, decision_node, ai_node, "false")  # Loop back for revision
        
        print("✅ Workflow nodes and connections created")
        
        # Execute workflow
        execution_id = await engine.execute_workflow(
            workflow_id,
            input_data={"topic": "AI in healthcare"},
            created_by="demo_user"
        )
        print(f"✅ Workflow execution started: {execution_id}")
        
        # Wait a bit for execution to progress
        await asyncio.sleep(2)
        
        # Check execution status
        execution = engine.executions[execution_id]
        print(f"✅ Execution status: {execution.status.value}")
        print(f"✅ Nodes executed: {len(execution.node_executions)}")
        
        # Get metrics
        metrics = await engine.get_workflow_metrics()
        print(f"✅ Workflow metrics:")
        print(f"   - Total workflows: {metrics['workflows']['total']}")
        print(f"   - Total executions: {metrics['executions']['total']}")
        print(f"   - Active executions: {metrics['executions']['active']}")
        print(f"   - Human tasks: {metrics['human_tasks']['total']}")
        
        # Export workflow
        exported = await engine.export_workflow(workflow_id)
        print(f"✅ Workflow exported with {len(exported['nodes'])} nodes")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())