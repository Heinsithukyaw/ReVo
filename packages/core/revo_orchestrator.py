"""
ReVo AI Orchestrator - The Brain of the Chat Interface
Advanced orchestration engine with function calling, context awareness, and intelligent dispatching
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages in the chat interface."""
    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"
    SYSTEM = "system"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    WORKFLOW_UPDATE = "workflow_update"
    FUNCTION_CALL = "function_call"
    AGENT_FEEDBACK = "agent_feedback"


@dataclass
class ChatMessage:
    """Chat message structure."""
    id: str
    sender: str  # 'user', 'revo', 'agent'
    content: str
    timestamp: float
    message_type: MessageType = MessageType.TEXT
    agent_name: Optional[str] = None
    engine_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data


@dataclass
class FunctionCall:
    """Function call structure from LLM."""
    name: str
    arguments: Dict[str, Any]
    description: Optional[str] = None


class ReVoOrchestrator:
    """
    The central brain of the ReVo AI Chat Interface.
    Handles message interpretation, context management, and intelligent dispatching.
    """
    
    def __init__(self, 
                 agent_framework=None,
                 workflow_engine=None,
                 perfect_recall_engine=None,
                 creative_engine=None,
                 parallel_mind_engine=None,
                 llm_client=None):
        """
        Initialize the ReVo Orchestrator.
        
        Args:
            agent_framework: The agent management framework
            workflow_engine: Workflow execution engine
            perfect_recall_engine: Memory and context engine
            creative_engine: Creative AI engine for suggestions
            parallel_mind_engine: Parallel task execution engine
            llm_client: LLM client for function calling
        """
        self.agent_framework = agent_framework
        self.workflow_engine = workflow_engine
        self.perfect_recall_engine = perfect_recall_engine
        self.creative_engine = creative_engine
        self.parallel_mind_engine = parallel_mind_engine
        self.llm_client = llm_client
        
        # WebSocket callback for real-time communication
        self.websocket_callback: Optional[Callable] = None
        
        # Active sessions and state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.message_history: List[ChatMessage] = []
        
        # Function calling schema
        self.tools_schema = self._build_tools_schema()
        
        # Command handlers
        self.command_handlers = {
            'help': self._handle_help_command,
            'run': self._handle_run_command,
            'browse': self._handle_browse_command,
            'create_project': self._handle_create_project_command,
            'analyze': self._handle_analyze_command,
            'refactor': self._handle_refactor_command,
            'audit': self._handle_audit_command,
            'workflow': self._handle_workflow_command,
            'status': self._handle_status_command
        }
    
    def set_websocket_callback(self, callback: Callable):
        """Set the WebSocket callback for real-time communication."""
        self.websocket_callback = callback
    
    async def _send_to_client(self, sender: str, content: str, 
                            message_type: MessageType = MessageType.TEXT,
                            agent_name: Optional[str] = None,
                            engine_name: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None):
        """Send a message to the client via WebSocket."""
        if not self.websocket_callback:
            return
        
        message = ChatMessage(
            id=f"{sender}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
            sender=sender,
            content=content,
            timestamp=time.time(),
            message_type=message_type,
            agent_name=agent_name,
            engine_name=engine_name,
            metadata=metadata
        )
        
        self.message_history.append(message)
        
        await self.websocket_callback({
            'type': 'message',
            'data': message.to_dict()
        })
    
    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build the function calling schema for the LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_terminal_command",
                    "description": "Execute a shell command on the local machine.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute."
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory for command execution."
                            }
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "browse_and_extract",
                    "description": "Crawl a URL and extract its content.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to crawl."
                            },
                            "extract_type": {
                                "type": "string",
                                "enum": ["text", "code", "links", "images"],
                                "description": "Type of content to extract."
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_workflow",
                    "description": "Initiate a pre-defined workflow for complex tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow_name": {
                                "type": "string",
                                "description": "The name of the workflow to execute."
                            },
                            "parameters": {
                                "type": "object",
                                "description": "Parameters for the workflow."
                            }
                        },
                        "required": ["workflow_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_code",
                    "description": "Analyze code structure, quality, and provide insights.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file or directory to analyze."
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["structure", "quality", "security", "performance"],
                                "description": "Type of analysis to perform."
                            }
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_creative_suggestions",
                    "description": "Get creative suggestions for code improvements or alternatives.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "Context or code to get suggestions for."
                            },
                            "suggestion_type": {
                                "type": "string",
                                "enum": ["refactor", "optimize", "alternative", "feature"],
                                "description": "Type of suggestions to generate."
                            }
                        },
                        "required": ["context"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "manage_workflow",
                    "description": "Manage workflow execution (start, pause, resume, cancel).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["list", "start", "pause", "resume", "cancel", "status"],
                                "description": "Action to perform on workflows."
                            },
                            "workflow_id": {
                                "type": "string",
                                "description": "ID of the workflow (required for non-list actions)."
                            }
                        },
                        "required": ["action"],
                    },
                },
            }
        ]
    
    async def handle_message(self, message_data: Dict[str, Any], session_id: str = "default"):
        """
        Handle incoming message from the chat interface.
        
        Args:
            message_data: Message data from WebSocket
            session_id: Session identifier for context management
        """
        try:
            content = message_data.get('content', '').strip()
            if not content:
                return
            
            # Store user message
            user_message = ChatMessage(
                id=f"user_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}",
                sender="user",
                content=content,
                timestamp=time.time(),
                message_type=MessageType.TEXT
            )
            self.message_history.append(user_message)
            
            # Check if it's a direct command
            if content.startswith('/'):
                await self._handle_direct_command(content, session_id)
                return
            
            # Use LLM with function calling for intelligent interpretation
            await self._handle_intelligent_message(content, session_id)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_to_client(
                "revo", 
                f"I encountered an error processing your message: {str(e)}", 
                MessageType.ERROR
            )
    
    async def _handle_direct_command(self, content: str, session_id: str):
        """Handle direct slash commands."""
        parts = content[1:].split()
        if not parts:
            await self._send_to_client("revo", "Please specify a command. Type /help for available commands.")
            return
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.command_handlers:
            await self.command_handlers[command](args, session_id)
        else:
            await self._send_to_client(
                "revo", 
                f"Unknown command: /{command}. Type /help for available commands.",
                MessageType.WARNING
            )
    
    async def _handle_intelligent_message(self, content: str, session_id: str):
        """Handle message using LLM with function calling."""
        try:
            # Get context from Perfect Recall Engine
            context_memos = []
            if self.perfect_recall_engine:
                context_memos = await self.perfect_recall_engine.retrieve(content, top_k=3)
            
            context_prompt = ""
            if context_memos:
                context_prompt = "Relevant context from previous interactions:\n" + "\n".join([
                    memo.content for memo in context_memos
                ])
            
            # Prepare messages for LLM
            system_prompt = f"""You are ReVo AI, an expert development assistant. You have access to various tools and can execute complex workflows.

{context_prompt}

Available tools:
- run_terminal_command: Execute shell commands
- browse_and_extract: Extract content from URLs
- execute_workflow: Run predefined workflows
- analyze_code: Analyze code structure and quality
- get_creative_suggestions: Get creative suggestions for improvements
- manage_workflow: Manage workflow execution

Choose the most appropriate tool(s) for the user's request. If no tool is needed, respond conversationally."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
            
            # Add recent conversation history
            for msg in self.message_history[-5:]:  # Last 5 messages for context
                if msg.sender == "user":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.sender in ["revo", "agent"]:
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Call LLM with function calling
            if self.llm_client:
                response = await self._call_llm_with_functions(messages)
                await self._process_llm_response(response, session_id)
            else:
                # Fallback to simple response
                await self._send_to_client(
                    "revo", 
                    "I understand your request, but I need an LLM client to provide intelligent responses."
                )
                
        except Exception as e:
            logger.error(f"Error in intelligent message handling: {e}")
            await self._send_to_client(
                "revo", 
                "I encountered an error processing your request. Please try again.",
                MessageType.ERROR
            )
    
    async def _call_llm_with_functions(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call LLM with function calling capability."""
        if not self.llm_client:
            # Fallback response when no LLM client is available
            return {
                "choices": [{
                    "message": {
                        "content": "I understand your request, but I need an LLM client to provide intelligent responses.",
                        "tool_calls": None
                    }
                }]
            }
        
        try:
            # Call the LLM with function calling
            response = await self.llm_client.chat_completion(
                messages=messages,
                tools=self.tools_schema
            )
            
            # Convert our LLMResponse to OpenAI-compatible format
            tool_calls = None
            if response.function_calls:
                tool_calls = [
                    {
                        "function": {
                            "name": call["name"],
                            "arguments": json.dumps(call["arguments"])
                        }
                    }
                    for call in response.function_calls
                ]
            
            return {
                "choices": [{
                    "message": {
                        "content": response.content,
                        "tool_calls": tool_calls
                    }
                }],
                "usage": {
                    "total_tokens": response.tokens_used
                },
                "model": response.model,
                "provider": response.provider.value,
                "cost": response.cost,
                "response_time": response.response_time
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return error response
            return {
                "choices": [{
                    "message": {
                        "content": f"I encountered an error while processing your request: {str(e)}",
                        "tool_calls": None
                    }
                }]
            }
    
    async def _process_llm_response(self, response: Dict[str, Any], session_id: str):
        """Process LLM response and execute function calls if needed."""
        try:
            choice = response["choices"][0]
            message = choice["message"]
            
            # Check for function calls
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    function_call = tool_call["function"]
                    await self._execute_function_call(
                        function_call["name"],
                        json.loads(function_call["arguments"]),
                        session_id
                    )
            
            # Send text response if available
            if message.get("content"):
                await self._send_to_client("revo", message["content"])
                
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            await self._send_to_client(
                "revo", 
                "I had trouble processing the response. Please try again.",
                MessageType.ERROR
            )
    
    async def _execute_function_call(self, function_name: str, arguments: Dict[str, Any], session_id: str):
        """Execute a function call from the LLM."""
        try:
            await self._send_to_client(
                "revo", 
                f"Executing: {function_name}",
                MessageType.FUNCTION_CALL,
                metadata={"function_name": function_name, "arguments": arguments}
            )
            
            if function_name == "run_terminal_command":
                await self._execute_terminal_command(arguments, session_id)
            elif function_name == "browse_and_extract":
                await self._execute_browse_command(arguments, session_id)
            elif function_name == "execute_workflow":
                await self._execute_workflow_function(arguments, session_id)
            elif function_name == "analyze_code":
                await self._execute_analyze_function(arguments, session_id)
            elif function_name == "get_creative_suggestions":
                await self._execute_creative_function(arguments, session_id)
            elif function_name == "manage_workflow":
                await self._execute_workflow_management(arguments, session_id)
            else:
                await self._send_to_client(
                    "revo", 
                    f"Unknown function: {function_name}",
                    MessageType.ERROR
                )
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            await self._send_to_client(
                "revo", 
                f"Error executing {function_name}: {str(e)}",
                MessageType.ERROR
            )
    
    # Command handlers
    async def _handle_help_command(self, args: List[str], session_id: str):
        """Handle help command."""
        help_text = """
**Available Commands:**

🔧 **Execution Commands:**
• `/run <command>` - Execute a terminal command
• `/browse <url>` - Browse and extract content from a URL

📁 **Project Commands:**
• `/create_project --name <name> --template <template>` - Create a new project
• `/analyze [path]` - Analyze code or project structure

🔍 **Analysis Commands:**
• `/refactor <function_name>` - Get refactoring suggestions
• `/audit [--security] [--performance]` - Run security/performance audit

⚡ **Workflow Commands:**
• `/workflow list` - List all workflows
• `/workflow start <workflow_id>` - Start a workflow
• `/workflow status <workflow_id>` - Get workflow status
• `/status` - Get overall system status

💡 **Tips:**
• You can also chat naturally - I'll understand your intent and use the right tools
• Use Shift+Enter for multi-line input
• Press ↑/↓ to navigate command history
        """
        
        await self._send_to_client("revo", help_text, MessageType.MARKDOWN)
    
    async def _handle_run_command(self, args: List[str], session_id: str):
        """Handle run command."""
        if not args:
            await self._send_to_client("revo", "Please specify a command to run. Usage: /run <command>")
            return
        
        command = " ".join(args)
        await self._execute_terminal_command({"command": command}, session_id)
    
    async def _handle_browse_command(self, args: List[str], session_id: str):
        """Handle browse command."""
        if not args:
            await self._send_to_client("revo", "Please specify a URL to browse. Usage: /browse <url>")
            return
        
        url = args[0]
        await self._execute_browse_command({"url": url}, session_id)
    
    async def _handle_create_project_command(self, args: List[str], session_id: str):
        """Handle create project command."""
        # Parse arguments
        params = {}
        i = 0
        while i < len(args):
            if args[i].startswith('--'):
                key = args[i][2:]
                if i + 1 < len(args) and not args[i + 1].startswith('--'):
                    params[key] = args[i + 1]
                    i += 2
                else:
                    params[key] = True
                    i += 1
            else:
                i += 1
        
        if 'name' not in params:
            await self._send_to_client("revo", "Please specify a project name. Usage: /create_project --name <name> [--template <template>]")
            return
        
        await self._execute_workflow_function({
            "workflow_name": "create_project",
            "parameters": params
        }, session_id)
    
    async def _handle_analyze_command(self, args: List[str], session_id: str):
        """Handle analyze command."""
        path = args[0] if args else "."
        await self._execute_analyze_function({"file_path": path}, session_id)
    
    async def _handle_refactor_command(self, args: List[str], session_id: str):
        """Handle refactor command."""
        if not args:
            await self._send_to_client("revo", "Please specify a function to refactor. Usage: /refactor <function_name>")
            return
        
        function_name = args[0]
        await self._execute_creative_function({
            "context": function_name,
            "suggestion_type": "refactor"
        }, session_id)
    
    async def _handle_audit_command(self, args: List[str], session_id: str):
        """Handle audit command."""
        audit_types = []
        if "--security" in args:
            audit_types.append("security")
        if "--performance" in args:
            audit_types.append("performance")
        
        if not audit_types:
            audit_types = ["security", "performance"]  # Default to both
        
        # Use parallel mind engine for concurrent audits
        if self.parallel_mind_engine and len(audit_types) > 1:
            await self._send_to_client("revo", "Running parallel security and performance audits...", MessageType.SYSTEM)
            # Implementation would use parallel mind engine
        else:
            for audit_type in audit_types:
                await self._execute_analyze_function({
                    "file_path": ".",
                    "analysis_type": audit_type
                }, session_id)
    
    async def _handle_workflow_command(self, args: List[str], session_id: str):
        """Handle workflow command."""
        if not args:
            await self._send_to_client("revo", "Please specify a workflow action. Usage: /workflow <action> [workflow_id]")
            return
        
        action = args[0]
        workflow_id = args[1] if len(args) > 1 else None
        
        await self._execute_workflow_management({
            "action": action,
            "workflow_id": workflow_id
        }, session_id)
    
    async def _handle_status_command(self, args: List[str], session_id: str):
        """Handle status command."""
        await self._execute_workflow_function({
            "workflow_name": "system_status",
            "parameters": {}
        }, session_id)
    
    # Function execution methods
    async def _execute_terminal_command(self, arguments: Dict[str, Any], session_id: str):
        """Execute terminal command."""
        command = arguments.get("command")
        working_dir = arguments.get("working_directory", ".")
        
        await self._send_to_client(
            "agent", 
            f"Executing command: `{command}`",
            MessageType.SYSTEM,
            agent_name="TerminalAgent"
        )
        
        # Here you would integrate with your actual terminal execution
        # For now, simulate the response
        result = f"Command executed: {command}\n(This is a simulated response)"
        
        await self._send_to_client(
            "agent", 
            f"```bash\n{result}\n```",
            MessageType.CODE,
            agent_name="TerminalAgent"
        )
    
    async def _execute_browse_command(self, arguments: Dict[str, Any], session_id: str):
        """Execute browse command."""
        url = arguments.get("url")
        extract_type = arguments.get("extract_type", "text")
        
        await self._send_to_client(
            "agent", 
            f"Browsing URL: {url}",
            MessageType.SYSTEM,
            agent_name="BrowserAgent"
        )
        
        # Simulate browsing result
        result = f"Successfully extracted {extract_type} content from {url}"
        
        await self._send_to_client(
            "agent", 
            result,
            MessageType.TEXT,
            agent_name="BrowserAgent"
        )
    
    async def _execute_workflow_function(self, arguments: Dict[str, Any], session_id: str):
        """Execute workflow."""
        workflow_name = arguments.get("workflow_name")
        parameters = arguments.get("parameters", {})
        
        if self.workflow_engine:
            await self._send_to_client(
                "revo", 
                f"Starting workflow: {workflow_name}",
                MessageType.WORKFLOW_UPDATE
            )
            
            # Here you would integrate with your actual workflow engine
            # For now, simulate workflow execution
            await asyncio.sleep(1)  # Simulate processing time
            
            await self._send_to_client(
                "revo", 
                f"Workflow '{workflow_name}' completed successfully",
                MessageType.SUCCESS
            )
        else:
            await self._send_to_client(
                "revo", 
                "Workflow engine not available",
                MessageType.ERROR
            )
    
    async def _execute_analyze_function(self, arguments: Dict[str, Any], session_id: str):
        """Execute code analysis."""
        file_path = arguments.get("file_path")
        analysis_type = arguments.get("analysis_type", "structure")
        
        await self._send_to_client(
            "agent", 
            f"Analyzing {file_path} for {analysis_type}...",
            MessageType.SYSTEM,
            agent_name="CodeAnalysisAgent"
        )
        
        # Simulate analysis result
        result = f"Analysis complete for {file_path}:\n- Type: {analysis_type}\n- Status: Good\n- Recommendations: None"
        
        await self._send_to_client(
            "agent", 
            result,
            MessageType.TEXT,
            agent_name="CodeAnalysisAgent"
        )
    
    async def _execute_creative_function(self, arguments: Dict[str, Any], session_id: str):
        """Execute creative suggestions."""
        context = arguments.get("context")
        suggestion_type = arguments.get("suggestion_type", "refactor")
        
        if self.creative_engine:
            await self._send_to_client(
                "agent", 
                f"Generating {suggestion_type} suggestions for: {context}",
                MessageType.SYSTEM,
                agent_name="CreativeEngine"
            )
            
            # Simulate creative suggestions
            suggestions = f"Here are some {suggestion_type} suggestions for '{context}':\n1. Improve naming\n2. Extract methods\n3. Add error handling"
            
            await self._send_to_client(
                "agent", 
                suggestions,
                MessageType.TEXT,
                agent_name="CreativeEngine"
            )
        else:
            await self._send_to_client(
                "revo", 
                "Creative engine not available",
                MessageType.ERROR
            )
    
    async def _execute_workflow_management(self, arguments: Dict[str, Any], session_id: str):
        """Execute workflow management."""
        action = arguments.get("action")
        workflow_id = arguments.get("workflow_id")
        
        if self.workflow_engine:
            if action == "list":
                workflows = await self.workflow_engine.list_workflows()
                result = "Active workflows:\n" + "\n".join([
                    f"• {w['name']} ({w['id']}) - {w['status']}" 
                    for w in workflows
                ])
            else:
                result = f"Workflow {action} executed for {workflow_id}"
            
            await self._send_to_client("revo", result, MessageType.TEXT)
        else:
            await self._send_to_client(
                "revo", 
                "Workflow engine not available",
                MessageType.ERROR
            )