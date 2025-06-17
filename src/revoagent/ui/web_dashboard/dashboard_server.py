"""
Dashboard Server - FastAPI-based Web Dashboard

Integrates xCodeAgent01 frontend capabilities with reVoAgent backend.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from .api_routes import APIRoutes
from .websocket_manager import WebSocketManager

# Import AI components
try:
    from ...ai.model_manager import model_manager
    from ...agents.enhanced_code_generator import enhanced_code_generator
    AI_ENABLED = True
except ImportError as e:
    logging.warning(f"AI components not available: {e}")
    model_manager = None
    enhanced_code_generator = None
    AI_ENABLED = False

logger = logging.getLogger(__name__)


class DashboardServer:
    """Web dashboard server for reVoAgent platform."""
    
    def __init__(self, 
                 agent_framework,
                 host: str = "0.0.0.0",
                 port: int = 12000,
                 static_dir: Optional[Path] = None):
        self.agent_framework = agent_framework
        self.host = host
        self.port = port
        self.static_dir = static_dir or Path(__file__).parent / "static"
        
        # Create FastAPI app
        self.app = FastAPI(
            title="reVoAgent Dashboard",
            description="Agentic AI Coding System Platform Dashboard",
            version="1.0.0"
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.websocket_manager = WebSocketManager()
        self.api_routes = APIRoutes(agent_framework, self.websocket_manager)
        
        # Setup routes
        self._setup_routes()
        self._setup_static_files()
        
        self.server_task: Optional[asyncio.Task] = None
    
    def _setup_routes(self):
        """Setup API routes."""
        # Include API routes
        self.app.include_router(
            self.api_routes.router,
            prefix="/api/v1"
        )
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self.websocket_manager.handle_message(websocket, message)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "reVoAgent Dashboard",
                "version": "1.0.0"
            }
        
        # Root endpoint - serve dashboard
        @self.app.get("/")
        async def dashboard():
            return await self._serve_dashboard()
    
    def _setup_static_files(self):
        """Setup static file serving."""
        # Create static directory if it doesn't exist
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default dashboard if it doesn't exist
        dashboard_file = self.static_dir / "index.html"
        if not dashboard_file.exists():
            self._create_default_dashboard()
        
        # Mount built React assets if they exist
        dist_dir = self.static_dir / "dist"
        if dist_dir.exists():
            # Mount the assets directory
            assets_dir = dist_dir / "assets"
            if assets_dir.exists():
                self.app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            
            # Mount the entire dist directory for other static files
            self.app.mount("/dist", StaticFiles(directory=str(dist_dir)), name="dist")
        
        # Mount static files (fallback)
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
    
    async def _serve_dashboard(self):
        """Serve the main dashboard."""
        # Try built React app first
        react_build_file = self.static_dir / "dist" / "index.html"
        if react_build_file.exists():
            return FileResponse(str(react_build_file))
        
        # Try React dashboard HTML
        react_dashboard_file = self.static_dir / "react_dashboard.html"
        if react_dashboard_file.exists():
            return FileResponse(str(react_dashboard_file))
        
        # Fallback to Vue dashboard
        dashboard_file = self.static_dir / "index.html"
        if dashboard_file.exists():
            return FileResponse(str(dashboard_file))
        else:
            return HTMLResponse(self._get_default_dashboard_html())
    
    def _create_default_dashboard(self):
        """Create default dashboard HTML."""
        dashboard_html = self._get_default_dashboard_html()
        dashboard_file = self.static_dir / "index.html"
        
        with open(dashboard_file, 'w') as f:
            f.write(dashboard_html)
        
        # Create CSS file
        css_file = self.static_dir / "dashboard.css"
        with open(css_file, 'w') as f:
            f.write(self._get_dashboard_css())
        
        # Create JavaScript file
        js_file = self.static_dir / "dashboard.js"
        with open(js_file, 'w') as f:
            f.write(self._get_dashboard_js())
    
    def _get_default_dashboard_html(self) -> str:
        """Get default dashboard HTML following the ASCII wireframe layout."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>reVoAgent Dashboard v1.0 Production</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="/static/dashboard.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50 font-mono">
    <div id="app" class="min-h-screen">
        <!-- Header Bar -->
        <header class="bg-gray-900 text-white border-b border-gray-700">
            <div class="flex items-center justify-between px-4 py-2 text-sm">
                <div class="flex items-center space-x-4">
                    <span class="text-blue-400 font-bold">🚀 reVoAgent</span>
                    <span class="text-gray-300">v1.0 Production</span>
                    <select class="bg-gray-800 text-white px-2 py-1 rounded text-xs">
                        <option>DeepSeek R1 ▼</option>
                        <option>CodeLlama 70B</option>
                        <option>Mistral 7B</option>
                    </select>
                    <span class="text-green-400">OpenHands ✓</span>
                    <div class="flex items-center space-x-1">
                        <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                        <span class="text-green-400">Live</span>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <select class="bg-gray-800 text-white px-2 py-1 rounded text-xs">
                        <option>👤 Admin ▼</option>
                    </select>
                </div>
            </div>
        </header>

        <div class="flex h-screen">
            <!-- Sidebar -->
            <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto">
                <!-- Workspace Section -->
                <div class="p-4 border-b border-gray-200">
                    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">WORKSPACE</h3>
                    <nav class="space-y-1">
                        <a href="#" @click="activeTab = 'dashboard'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'dashboard' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            <span class="mr-2">●</span> Dashboard
                        </a>
                        <a href="#" @click="activeTab = 'projects'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'projects' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Projects <span class="ml-auto text-xs bg-gray-200 px-2 py-1 rounded">[42]</span>
                        </a>
                        <a href="#" @click="activeTab = 'workflows'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'workflows' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Workflows
                        </a>
                        <a href="#" @click="activeTab = 'analytics'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'analytics' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Analytics
                        </a>
                    </nav>
                </div>

                <!-- AI Agents Section -->
                <div class="p-4 border-b border-gray-200">
                    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">AI AGENTS</h3>
                    <nav class="space-y-1">
                        <a href="#" @click="activeTab = 'code-generator'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'code-generator' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            <span class="mr-2">●</span> Enhanced Code Generator
                        </a>
                        <a href="#" @click="activeTab = 'debug-agent'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'debug-agent' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Debug Agent
                        </a>
                        <a href="#" @click="activeTab = 'testing-agent'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'testing-agent' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Testing Agent
                        </a>
                        <a href="#" @click="activeTab = 'deploy-agent'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'deploy-agent' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Deploy Agent
                        </a>
                        <a href="#" @click="activeTab = 'browser-agent'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'browser-agent' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Browser Agent
                        </a>
                    </nav>
                </div>

                <!-- Integrations Section -->
                <div class="p-4 border-b border-gray-200">
                    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">INTEGRATIONS</h3>
                    <nav class="space-y-1">
                        <div class="flex items-center px-2 py-1 text-sm">
                            <span class="text-green-500 mr-2">✓</span> OpenHands
                        </div>
                        <div class="flex items-center px-2 py-1 text-sm">
                            <span class="text-green-500 mr-2">✓</span> vLLM Server
                        </div>
                        <div class="flex items-center px-2 py-1 text-sm">
                            <span class="text-green-500 mr-2">✓</span> Docker Orch
                        </div>
                        <div class="flex items-center px-2 py-1 text-sm">
                            <span class="text-green-500 mr-2">✓</span> All-Hands
                        </div>
                        <div class="flex items-center px-2 py-1 text-sm">
                            <span class="text-green-500 mr-2">✓</span> Monitoring
                        </div>
                    </nav>
                </div>

                <!-- Tools & Config Section -->
                <div class="p-4">
                    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">TOOLS & CONFIG</h3>
                    <nav class="space-y-1">
                        <a href="#" @click="activeTab = 'model-registry'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'model-registry' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Model Registry
                        </a>
                        <a href="#" @click="activeTab = 'settings'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'settings' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Settings
                        </a>
                        <a href="#" @click="activeTab = 'security'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'security' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Security
                        </a>
                        <a href="#" @click="activeTab = 'monitoring'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'monitoring' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Monitoring
                        </a>
                        <a href="#" @click="activeTab = 'resource-mgmt'" 
                           :class="['flex items-center px-2 py-2 text-sm font-medium rounded-md', 
                                   activeTab === 'resource-mgmt' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-50']">
                            Resource Mgmt
                        </a>
                    </nav>
                </div>
            </aside>

            <!-- Main Content Area -->
            <main class="flex-1 overflow-y-auto">
                <!-- Dashboard Tab -->
                <div v-if="activeTab === 'dashboard'" class="p-6">
                    <!-- Revolutionary Platform Header -->
                    <div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg mb-6">
                        <h2 class="text-2xl font-bold mb-2">Revolutionary Agentic Coding Platform</h2>
                        <p class="text-blue-100 mb-4">Zero-cost AI • Multi-platform • Production Ready</p>
                        <div class="flex space-x-6 text-sm">
                            <span class="text-green-300">✓ OpenHands</span>
                            <span class="text-green-300">✓ vLLM</span>
                            <span class="text-green-300">✓ Docker</span>
                            <span class="text-green-300">✓ All-Hands</span>
                            <span class="text-yellow-300">⚠ IDE Plugins</span>
                        </div>
                    </div>

                    <!-- Quick Actions -->
                    <div class="bg-white rounded-lg shadow mb-6 p-6">
                        <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">🚀</div>
                                <h4 class="font-medium">Enhanced Code Gen</h4>
                                <p class="text-sm text-gray-500">OpenHands+vLLM</p>
                            </div>
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">🔄</div>
                                <h4 class="font-medium">Workflow Auto</h4>
                                <p class="text-sm text-gray-500">Parallel Exec</p>
                            </div>
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">🌐</div>
                                <h4 class="font-medium">Browser Agent</h4>
                                <p class="text-sm text-gray-500">Playwright+AI</p>
                            </div>
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">🐛</div>
                                <h4 class="font-medium">Debug & Fix</h4>
                                <p class="text-sm text-gray-500">Auto Issue Resolve</p>
                            </div>
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">📦</div>
                                <h4 class="font-medium">Deploy Pipeline</h4>
                                <p class="text-sm text-gray-500">Docker+K8s+Monitor</p>
                            </div>
                            <div class="text-center p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div class="text-2xl mb-2">🧪</div>
                                <h4 class="font-medium">Test Generation</h4>
                                <p class="text-sm text-gray-500">Comprehensive Tests</p>
                            </div>
                        </div>
                    </div>

                    <!-- System Metrics -->
                    <div class="bg-white rounded-lg shadow mb-6 p-6">
                        <h3 class="text-lg font-semibold mb-4">System Metrics</h3>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <span class="text-gray-500">Tasks:</span>
                                <span class="font-semibold ml-2">{{ stats.tasksCompleted }} (+23%)</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Success:</span>
                                <span class="font-semibold ml-2">{{ stats.successRate }}%</span>
                            </div>
                            <div>
                                <span class="text-gray-500">API Cost:</span>
                                <span class="font-semibold ml-2 text-green-600">$0</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Agents:</span>
                                <span class="font-semibold ml-2">{{ stats.activeAgents }}</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Response:</span>
                                <span class="font-semibold ml-2">{{ stats.responseTime }}ms</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Memory:</span>
                                <span class="font-semibold ml-2">12GB</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Models:</span>
                                <span class="font-semibold ml-2">{{ stats.modelsLoaded }}</span>
                            </div>
                            <div>
                                <span class="text-gray-500">Uptime:</span>
                                <span class="font-semibold ml-2 text-green-600">{{ stats.uptime }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Active Workflows and System Status -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <!-- Active Workflows -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">Active Workflows</h3>
                            <div class="space-y-3">
                                <div v-for="workflow in activeWorkflows" :key="workflow.id" class="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div>
                                        <div class="flex items-center space-x-2">
                                            <span>{{ workflow.icon }}</span>
                                            <span class="font-medium">{{ workflow.name }}</span>
                                            <span class="text-sm text-gray-500">({{ workflow.agents }} agents)</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="mt-4 p-3 bg-blue-50 rounded">
                                    <span class="font-medium">Total Active: {{ totalActiveAgents }} parallel agents</span>
                                </div>
                            </div>
                        </div>

                        <!-- System Status -->
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="text-lg font-semibold mb-4">System Status</h3>
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">CPU Usage:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-blue-600 h-2 rounded-full" :style="{width: systemMetrics.cpu + '%'}"></div>
                                        </div>
                                        <span class="text-sm">{{ systemMetrics.cpu }}%</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">Memory:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-green-600 h-2 rounded-full" :style="{width: systemMetrics.memory + '%'}"></div>
                                        </div>
                                        <span class="text-sm">{{ systemMetrics.memory }}%</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">GPU Memory:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-purple-600 h-2 rounded-full" :style="{width: systemMetrics.gpu + '%'}"></div>
                                        </div>
                                        <span class="text-sm">{{ systemMetrics.gpu }}%</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">Disk I/O:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-yellow-600 h-2 rounded-full" :style="{width: systemMetrics.disk + '%'}"></div>
                                        </div>
                                        <span class="text-sm">{{ systemMetrics.disk }}%</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">Network:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-red-600 h-2 rounded-full" :style="{width: systemMetrics.network + '%'}"></div>
                                        </div>
                                        <span class="text-sm">{{ systemMetrics.network }}%</span>
                                    </div>
                                </div>
                                <div class="flex justify-between items-center">
                                    <span class="text-sm">Models Load:</span>
                                    <div class="flex items-center space-x-2">
                                        <div class="w-24 bg-gray-200 rounded-full h-2">
                                            <div class="bg-indigo-600 h-2 rounded-full" style="width: 80%"></div>
                                        </div>
                                        <span class="text-sm">8/8</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Activity Feed -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4">Recent Activity Feed</h3>
                        <div class="space-y-4">
                            <div v-for="activity in recentActivities" :key="activity.id" class="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded">
                                <div class="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                                <div class="flex-1">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <p class="font-medium">{{ activity.title }}</p>
                                            <p class="text-sm text-gray-500">{{ activity.description }}</p>
                                        </div>
                                        <span class="text-xs text-gray-400">{{ activity.time }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Quick Terminal and Model Selector -->
                    <div class="fixed bottom-4 right-4 flex space-x-2">
                        <button class="bg-gray-800 text-white px-4 py-2 rounded shadow-lg hover:bg-gray-700">
                            ⚡ Quick Terminal
                        </button>
                        <button class="bg-blue-600 text-white px-4 py-2 rounded shadow-lg hover:bg-blue-700">
                            🔧 Model Selector
                        </button>
                    </div>
                </div>

                <!-- Enhanced Code Generator Interface -->
                <div v-if="activeTab === 'code-generator'" class="p-6">
                    <div class="bg-white rounded-lg shadow">
                        <div class="border-b border-gray-200 px-6 py-4">
                            <div class="flex items-center justify-between">
                                <h2 class="text-xl font-semibold">Enhanced Code Generator</h2>
                                <div class="flex items-center space-x-4 text-sm">
                                    <span class="text-blue-600">[DeepSeek R1]</span>
                                    <span class="text-green-600">[OpenHands Mode]</span>
                                    <div class="flex items-center space-x-1">
                                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                                        <span class="text-green-600">Ready</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex">
                            <!-- Left Sidebar -->
                            <div class="w-64 border-r border-gray-200 p-4">
                                <!-- Templates -->
                                <div class="mb-6">
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">TEMPLATES</h3>
                                    <div class="space-y-1">
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">REST API</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Web App</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Microservice</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">ML Pipeline</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">CLI Tool</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Custom</div>
                                    </div>
                                </div>

                                <!-- Models -->
                                <div class="mb-6">
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">MODELS</h3>
                                    <div class="space-y-1">
                                        <div class="flex items-center px-2 py-1 text-sm">
                                            <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                                            DeepSeek R1
                                        </div>
                                        <div class="px-2 py-1 text-sm text-gray-500">CodeLlama 70B</div>
                                        <div class="px-2 py-1 text-sm text-gray-500">Mistral 7B</div>
                                        <div class="px-2 py-1 text-sm text-gray-500">Custom Model</div>
                                    </div>
                                </div>

                                <!-- Quality Metrics -->
                                <div>
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">QUALITY</h3>
                                    <div class="space-y-2 text-sm">
                                        <div class="flex justify-between">
                                            <span>Score:</span>
                                            <span class="font-semibold text-green-600">94%</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span>Security:</span>
                                            <span class="font-semibold text-green-600">A+</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span>Performance:</span>
                                            <span class="font-semibold text-green-600">A</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span>Maintainability:</span>
                                            <span class="font-semibold text-blue-600">A</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Main Content -->
                            <div class="flex-1 p-6">
                                <!-- Task Description -->
                                <div class="mb-6">
                                    <h3 class="text-lg font-semibold mb-3">Task Description</h3>
                                    <textarea 
                                        v-model="codeGenTask"
                                        class="w-full h-24 p-3 border border-gray-300 rounded-lg resize-none"
                                        placeholder="Create a complete e-commerce API with user auth, product catalog, shopping cart, payment integration, and admin dashboard">
                                    </textarea>
                                    
                                    <div class="flex items-center space-x-4 mt-3">
                                        <select class="px-3 py-2 border border-gray-300 rounded">
                                            <option>Python ▼</option>
                                            <option>JavaScript</option>
                                            <option>TypeScript</option>
                                        </select>
                                        <select class="px-3 py-2 border border-gray-300 rounded">
                                            <option>FastAPI ▼</option>
                                            <option>Django</option>
                                            <option>Flask</option>
                                        </select>
                                        <select class="px-3 py-2 border border-gray-300 rounded">
                                            <option>PostgreSQL ▼</option>
                                            <option>MySQL</option>
                                            <option>MongoDB</option>
                                        </select>
                                    </div>
                                    
                                    <div class="flex items-center space-x-4 mt-3">
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Auth
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Tests
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Docs
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Docker
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> CI/CD
                                        </label>
                                    </div>
                                </div>

                                <!-- Generation Progress -->
                                <div class="mb-6">
                                    <h3 class="text-lg font-semibold mb-3">Generation Progress</h3>
                                    <div class="space-y-3">
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm">Phase 1: Architecture Planning</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-32 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-green-600 h-2 rounded-full" style="width: 100%"></div>
                                                </div>
                                                <span class="text-sm">100%</span>
                                            </div>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm">Phase 2: Database Models</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-32 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-green-600 h-2 rounded-full" style="width: 100%"></div>
                                                </div>
                                                <span class="text-sm">100%</span>
                                            </div>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm">Phase 3: API Endpoints</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-32 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-blue-600 h-2 rounded-full" style="width: 75%"></div>
                                                </div>
                                                <span class="text-sm">75%</span>
                                            </div>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm">Phase 4: Authentication</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-32 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-yellow-600 h-2 rounded-full" style="width: 45%"></div>
                                                </div>
                                                <span class="text-sm">45%</span>
                                            </div>
                                        </div>
                                        <div class="flex items-center justify-between">
                                            <span class="text-sm">Phase 5: Tests & Documentation</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-32 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-gray-400 h-2 rounded-full" style="width: 0%"></div>
                                                </div>
                                                <span class="text-sm">0%</span>
                                            </div>
                                        </div>
                                    </div>
                                    <p class="text-sm text-gray-500 mt-3">Estimated completion: 4 minutes</p>
                                </div>

                                <!-- Live Code Preview and File Structure -->
                                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <!-- Live Code Preview -->
                                    <div>
                                        <h3 class="text-lg font-semibold mb-3">Live Code Preview</h3>
                                        <div class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                                            <div># E-commerce API - FastAPI</div>
                                            <div>from fastapi import FastAPI</div>
                                            <div>from fastapi.security import OAuth2</div>
                                            <div></div>
                                            <div>app = FastAPI(</div>
                                            <div>&nbsp;&nbsp;&nbsp;&nbsp;title="E-commerce API",</div>
                                            <div>&nbsp;&nbsp;&nbsp;&nbsp;description="Complete API...",</div>
                                            <div>&nbsp;&nbsp;&nbsp;&nbsp;version="1.0.0"</div>
                                            <div>)</div>
                                        </div>
                                        <div class="flex space-x-2 mt-3">
                                            <button class="bg-blue-600 text-white px-4 py-2 rounded text-sm">Copy Code</button>
                                            <button class="bg-green-600 text-white px-4 py-2 rounded text-sm">Download</button>
                                            <button class="bg-purple-600 text-white px-4 py-2 rounded text-sm">Deploy</button>
                                        </div>
                                    </div>

                                    <!-- File Structure -->
                                    <div>
                                        <h3 class="text-lg font-semibold mb-3">File Structure</h3>
                                        <div class="bg-gray-50 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                                            <div>ecommerce_api/</div>
                                            <div>├── app/</div>
                                            <div>│&nbsp;&nbsp;&nbsp;├── models/</div>
                                            <div>│&nbsp;&nbsp;&nbsp;├── routers/</div>
                                            <div>│&nbsp;&nbsp;&nbsp;├── services/</div>
                                            <div>│&nbsp;&nbsp;&nbsp;└── tests/</div>
                                            <div>├── requirements.txt</div>
                                            <div>├── Dockerfile</div>
                                            <div>├── docker-compose.yml</div>
                                            <div>└── README.md</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Multi-Agent Workflow Orchestration -->
                <div v-if="activeTab === 'workflows'" class="p-6">
                    <div class="bg-white rounded-lg shadow">
                        <div class="border-b border-gray-200 px-6 py-4">
                            <div class="flex items-center justify-between">
                                <h2 class="text-xl font-semibold">Workflow Engine</h2>
                                <div class="flex items-center space-x-4 text-sm">
                                    <span class="text-blue-600">[Parallel Mode]</span>
                                    <span class="text-green-600">[18 Active]</span>
                                    <div class="flex items-center space-x-1">
                                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                                        <span class="text-green-600">Optimized</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-6">
                            <!-- Active Workflow -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold mb-3">Active Workflow: Microservices Architecture</h3>
                                <div class="bg-blue-50 p-4 rounded-lg mb-4">
                                    <div class="flex justify-between items-center text-sm">
                                        <span>Started: 12:34 PM • Estimated: 15 min • Progress: 67%</span>
                                    </div>
                                </div>
                                
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div v-for="agent in workflowAgents" :key="agent.id" class="flex items-center justify-between p-3 border rounded-lg">
                                        <div class="flex items-center space-x-3">
                                            <span>{{ agent.icon }}</span>
                                            <div>
                                                <div class="font-medium text-sm">{{ agent.name }}</div>
                                                <div class="text-xs text-gray-500">{{ agent.task }}</div>
                                            </div>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <div class="w-16 bg-gray-200 rounded-full h-2">
                                                <div class="bg-blue-600 h-2 rounded-full" :style="{width: agent.progress + '%'}"></div>
                                            </div>
                                            <span class="text-xs">{{ agent.progress }}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Resource Allocation and Communication -->
                            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                <!-- Resource Allocation -->
                                <div>
                                    <h3 class="text-lg font-semibold mb-3">Resource Allocation</h3>
                                    <div class="space-y-3">
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">CPU Cores:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-blue-600 h-2 rounded-full" style="width: 80%"></div>
                                                </div>
                                                <span class="text-sm">8/10</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Memory Pool:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-green-600 h-2 rounded-full" style="width: 67%"></div>
                                                </div>
                                                <span class="text-sm">12/18GB</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">GPU Memory:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-purple-600 h-2 rounded-full" style="width: 56%"></div>
                                                </div>
                                                <span class="text-sm">10/18GB</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Model Slots:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-indigo-600 h-2 rounded-full" style="width: 80%"></div>
                                                </div>
                                                <span class="text-sm">8/10</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="mt-4 space-y-2 text-sm">
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span>Dynamic Load Balancing: Active</span>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span>Auto-scaling: Enabled</span>
                                        </div>
                                    </div>
                                </div>

                                <!-- Agent Communication -->
                                <div>
                                    <h3 class="text-lg font-semibold mb-3">Agent Communication</h3>
                                    <div class="space-y-2 text-sm">
                                        <div class="p-2 bg-gray-50 rounded">Agent 1 → Agent 6: Test specs</div>
                                        <div class="p-2 bg-gray-50 rounded">Agent 5 → Agent 7: Build deps</div>
                                        <div class="p-2 bg-gray-50 rounded">Agent 3 → Agent 4: API schema</div>
                                        <div class="p-2 bg-gray-50 rounded">Agent 2 → Agent 8: Endpoints</div>
                                    </div>
                                    <div class="mt-4 space-y-2 text-sm">
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span>Dependency Resolution: Auto</span>
                                        </div>
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span>Error Recovery: Enabled</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Workflow History -->
                            <div>
                                <h3 class="text-lg font-semibold mb-3">Workflow History</h3>
                                <div class="space-y-2">
                                    <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded">
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span class="font-medium">E-commerce Platform (8 agents)</span>
                                        </div>
                                        <div class="text-sm text-gray-500">45 min ago - 100% success</div>
                                    </div>
                                    <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded">
                                        <div class="flex items-center space-x-2">
                                            <span class="text-green-500">✓</span>
                                            <span class="font-medium">Data Analysis Pipeline (12 agents)</span>
                                        </div>
                                        <div class="text-sm text-gray-500">2 hrs ago - 98% success</div>
                                    </div>
                                    <div class="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded">
                                        <div class="flex items-center space-x-2">
                                            <span class="text-yellow-500">⚠</span>
                                            <span class="font-medium">ML Model Training (15 agents)</span>
                                        </div>
                                        <div class="text-sm text-gray-500">6 hrs ago - 94% success</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Model Registry & Management -->
                <div v-if="activeTab === 'model-registry'" class="p-6">
                    <div class="bg-white rounded-lg shadow">
                        <div class="border-b border-gray-200 px-6 py-4">
                            <div class="flex items-center justify-between">
                                <h2 class="text-xl font-semibold">Model Registry & Management</h2>
                                <div class="flex items-center space-x-4 text-sm">
                                    <span class="text-blue-600">[Local]</span>
                                    <span class="text-green-600">[vLLM]</span>
                                    <span class="text-purple-600">[Auto-Optimize]</span>
                                    <div class="flex items-center space-x-1">
                                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                                        <span class="text-green-600">Ready</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex">
                            <!-- Left Sidebar -->
                            <div class="w-64 border-r border-gray-200 p-4">
                                <!-- Categories -->
                                <div class="mb-6">
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">CATEGORIES</h3>
                                    <div class="space-y-1">
                                        <div class="flex items-center px-2 py-1 text-sm bg-blue-100 rounded">
                                            <span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                                            Code Models
                                        </div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Chat Models</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Specialized</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Quantized</div>
                                        <div class="px-2 py-1 text-sm hover:bg-gray-100 rounded cursor-pointer">Custom</div>
                                    </div>
                                </div>

                                <!-- Optimization -->
                                <div class="mb-6">
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">OPTIMIZATION</h3>
                                    <div class="space-y-2 text-sm">
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Auto-Quantize
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> GPU Offload
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Memory Opt
                                        </label>
                                        <label class="flex items-center">
                                            <input type="checkbox" checked class="mr-2"> Load Balance
                                        </label>
                                    </div>
                                </div>

                                <!-- Hardware -->
                                <div>
                                    <h3 class="text-sm font-semibold text-gray-500 uppercase mb-3">HARDWARE</h3>
                                    <div class="space-y-2 text-sm">
                                        <div>GPU: RTX 4090</div>
                                        <div>VRAM: 24GB</div>
                                        <div>RAM: 64GB</div>
                                        <div>CPU: 16 cores</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Main Content -->
                            <div class="flex-1 p-6">
                                <!-- Available Models -->
                                <div class="mb-6">
                                    <h3 class="text-lg font-semibold mb-3">Available Models</h3>
                                    <div class="overflow-x-auto">
                                        <table class="min-w-full divide-y divide-gray-200">
                                            <thead class="bg-gray-50">
                                                <tr>
                                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Size</th>
                                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Performance</th>
                                                </tr>
                                            </thead>
                                            <tbody class="bg-white divide-y divide-gray-200">
                                                <tr v-for="model in models" :key="model.name">
                                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                        {{ model.name }}
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ model.size }}</td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ model.type }}</td>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                                                                      model.status === 'loaded' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800']">
                                                            {{ model.status === 'loaded' ? '✓ Loaded' : '○ Available' }}
                                                        </span>
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <div class="flex items-center space-x-2">
                                                            <div class="w-16 bg-gray-200 rounded-full h-2">
                                                                <div class="bg-blue-600 h-2 rounded-full" :style="{width: model.performance + '%'}"></div>
                                                            </div>
                                                            <span class="text-sm">{{ model.performance }}%</span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                <!-- Model Configuration and Performance -->
                                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <!-- Model Configuration -->
                                    <div>
                                        <h3 class="text-lg font-semibold mb-3">Model Configuration</h3>
                                        <div class="space-y-4">
                                            <div>
                                                <label class="block text-sm font-medium text-gray-700 mb-1">Selected: DeepSeek R1 0528</label>
                                            </div>
                                            <div>
                                                <label class="block text-sm font-medium text-gray-700 mb-1">Quantization</label>
                                                <select class="w-full px-3 py-2 border border-gray-300 rounded">
                                                    <option>4-bit ▼</option>
                                                    <option>8-bit</option>
                                                    <option>16-bit</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label class="block text-sm font-medium text-gray-700 mb-1">Context Length</label>
                                                <select class="w-full px-3 py-2 border border-gray-300 rounded">
                                                    <option>32,768 ▼</option>
                                                    <option>16,384</option>
                                                    <option>8,192</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label class="block text-sm font-medium text-gray-700 mb-1">Temperature: 0.7</label>
                                                <input type="range" min="0" max="1" step="0.1" value="0.7" class="w-full">
                                            </div>
                                            <div>
                                                <label class="block text-sm font-medium text-gray-700 mb-1">Top-p: 0.9</label>
                                                <input type="range" min="0" max="1" step="0.1" value="0.9" class="w-full">
                                            </div>
                                            <div class="flex space-x-2">
                                                <button class="bg-blue-600 text-white px-4 py-2 rounded text-sm">Save Config</button>
                                                <button class="bg-gray-600 text-white px-4 py-2 rounded text-sm">Load Preset</button>
                                                <button class="bg-red-600 text-white px-4 py-2 rounded text-sm">Reset</button>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Performance Metrics -->
                                    <div>
                                        <h3 class="text-lg font-semibold mb-3">Performance Metrics</h3>
                                        <div class="space-y-3">
                                            <div class="flex justify-between">
                                                <span class="text-sm">Tokens/sec:</span>
                                                <span class="font-semibold">2,340</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">Latency:</span>
                                                <span class="font-semibold">847ms</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">Memory Usage:</span>
                                                <span class="font-semibold">18.2GB</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">GPU Util:</span>
                                                <span class="font-semibold">78%</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">CPU Util:</span>
                                                <span class="font-semibold">34%</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">Cache Hit:</span>
                                                <span class="font-semibold text-green-600">89%</span>
                                            </div>
                                            <div class="flex justify-between">
                                                <span class="text-sm">Success Rate:</span>
                                                <span class="font-semibold text-green-600">98.5%</span>
                                            </div>
                                            <div class="mt-4">
                                                <span class="text-sm text-gray-500">Avg Inference: 847ms</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Platform Monitoring -->
                <div v-if="activeTab === 'monitoring'" class="p-6">
                    <div class="bg-white rounded-lg shadow">
                        <div class="border-b border-gray-200 px-6 py-4">
                            <div class="flex items-center justify-between">
                                <h2 class="text-xl font-semibold">Platform Monitoring</h2>
                                <div class="flex items-center space-x-4 text-sm">
                                    <span class="text-blue-600">[Real-time]</span>
                                    <span class="text-green-600">[Grafana]</span>
                                    <span class="text-purple-600">[Prometheus]</span>
                                    <div class="flex items-center space-x-1">
                                        <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                                        <span class="text-green-600">Healthy</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="p-6">
                            <!-- Core Services Status -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold mb-3">Core Services Status</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div v-for="service in coreServices" :key="service.name" class="p-4 border rounded-lg">
                                        <div class="flex items-center justify-between mb-2">
                                            <span class="font-medium">{{ service.name }}</span>
                                            <span :class="['text-sm px-2 py-1 rounded', service.status === 'Running' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800']">
                                                {{ service.status === 'Running' ? '✓ Running' : '✗ Down' }}
                                            </span>
                                        </div>
                                        <div class="text-sm text-gray-500 space-y-1">
                                            <div>Port: {{ service.port }}</div>
                                            <div>{{ service.metric }}: {{ service.value }}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Resource Utilization and Model Performance -->
                            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                <!-- Resource Utilization -->
                                <div>
                                    <h3 class="text-lg font-semibold mb-3">Resource Utilization</h3>
                                    <div class="space-y-3">
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">CPU Usage:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-blue-600 h-2 rounded-full" style="width: 82%"></div>
                                                </div>
                                                <span class="text-sm">82%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Memory:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-green-600 h-2 rounded-full" style="width: 67%"></div>
                                                </div>
                                                <span class="text-sm">67%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">GPU Memory:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-purple-600 h-2 rounded-full" style="width: 56%"></div>
                                                </div>
                                                <span class="text-sm">56%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Disk I/O:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-yellow-600 h-2 rounded-full" style="width: 34%"></div>
                                                </div>
                                                <span class="text-sm">34%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Network:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-red-600 h-2 rounded-full" style="width: 23%"></div>
                                                </div>
                                                <span class="text-sm">23%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Model Memory:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-24 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-indigo-600 h-2 rounded-full" style="width: 80%"></div>
                                                </div>
                                                <span class="text-sm">8/10</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Model Performance -->
                                <div>
                                    <h3 class="text-lg font-semibold mb-3">Model Performance</h3>
                                    <div class="space-y-3">
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">DeepSeek R1:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-16 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-green-600 h-2 rounded-full" style="width: 89%"></div>
                                                </div>
                                                <span class="text-sm">89%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">CodeLlama:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-16 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-blue-600 h-2 rounded-full" style="width: 56%"></div>
                                                </div>
                                                <span class="text-sm">56%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Mistral 7B:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-16 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-yellow-600 h-2 rounded-full" style="width: 45%"></div>
                                                </div>
                                                <span class="text-sm">45%</span>
                                            </div>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="text-sm">Custom Model:</span>
                                            <div class="flex items-center space-x-2">
                                                <div class="w-16 bg-gray-200 rounded-full h-2">
                                                    <div class="bg-gray-400 h-2 rounded-full" style="width: 12%"></div>
                                                </div>
                                                <span class="text-sm">12%</span>
                                            </div>
                                        </div>
                                        <div class="mt-4 text-sm text-gray-500">
                                            Avg Inference: 847ms
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Integration Health -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold mb-3">Integration Health</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div v-for="integration in integrationHealth" :key="integration.name" class="p-4 border rounded-lg">
                                        <div class="flex items-center justify-between mb-2">
                                            <span class="font-medium">{{ integration.name }}</span>
                                            <span class="text-sm px-2 py-1 rounded bg-green-100 text-green-800">
                                                ✓ {{ integration.status }}
                                            </span>
                                        </div>
                                        <div class="text-sm text-gray-500 space-y-1">
                                            <div>Response: {{ integration.response }}ms</div>
                                            <div>Success: {{ integration.success }}%</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Recent Alerts & Events -->
                            <div>
                                <h3 class="text-lg font-semibold mb-3">Recent Alerts & Events</h3>
                                <div class="space-y-2">
                                    <div v-for="alert in recentAlerts" :key="alert.id" class="flex items-center space-x-3 p-3 border rounded-lg">
                                        <div :class="['w-3 h-3 rounded-full', alert.type === 'success' ? 'bg-green-500' : alert.type === 'warning' ? 'bg-yellow-500' : 'bg-red-500']"></div>
                                        <div class="flex-1">
                                            <div class="flex justify-between items-center">
                                                <span class="font-medium">{{ alert.time }} - {{ alert.message }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Other tabs would be implemented similarly -->
                <div v-if="!['dashboard', 'code-generator', 'workflows', 'model-registry', 'monitoring'].includes(activeTab)" class="p-6">
                    <div class="bg-white rounded-lg shadow p-6 text-center">
                        <h2 class="text-xl font-semibold mb-4">{{ getTabName(activeTab) }}</h2>
                        <p class="text-gray-500">This section is under development.</p>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>"""
    
    def _get_dashboard_css(self) -> str:
        """Get dashboard CSS."""
        return """
/* Custom dashboard styles */
.chart-container {
    position: relative;
    height: 300px;
}

.status-indicator {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

.agent-card {
    transition: transform 0.2s;
}

.agent-card:hover {
    transform: translateY(-2px);
}

.workflow-progress {
    background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
}
        """
    
    def _get_dashboard_js(self) -> str:
        """Get dashboard JavaScript."""
        return """
const { createApp } = Vue;

createApp({
    data() {
        return {
            activeTab: 'dashboard',
            tabs: [
                { id: 'dashboard', name: 'Dashboard' },
                { id: 'agents', name: 'Agents' },
                { id: 'workflows', name: 'Workflows' },
                { id: 'models', name: 'Models' }
            ],
            systemStatus: {
                text: 'Online',
                color: 'bg-green-500'
            },
            stats: {
                activeAgents: 0,
                runningWorkflows: 0,
                tasksCompleted: 0,
                modelsLoaded: 0
            },
            agents: [],
            workflows: [],
            models: [],
            websocket: null
        }
    },
    mounted() {
        this.initializeWebSocket();
        this.loadData();
        this.initializeCharts();
    },
    methods: {
        initializeWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.systemStatus = { text: 'Online', color: 'bg-green-500' };
            };
            
            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.systemStatus = { text: 'Offline', color: 'bg-red-500' };
                // Attempt to reconnect
                setTimeout(() => this.initializeWebSocket(), 5000);
            };
        },
        
        handleWebSocketMessage(message) {
            switch (message.type) {
                case 'stats_update':
                    this.stats = message.data;
                    break;
                case 'agent_status':
                    this.updateAgentStatus(message.data);
                    break;
                case 'workflow_update':
                    this.updateWorkflowStatus(message.data);
                    break;
            }
        },
        
        async loadData() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/v1/stats');
                this.stats = await statsResponse.json();
                
                // Load agents
                const agentsResponse = await fetch('/api/v1/agents');
                this.agents = await agentsResponse.json();
                
                // Load workflows
                const workflowsResponse = await fetch('/api/v1/workflows');
                this.workflows = await workflowsResponse.json();
                
                // Load models
                const modelsResponse = await fetch('/api/v1/models');
                this.models = await modelsResponse.json();
                
            } catch (error) {
                console.error('Error loading data:', error);
            }
        },
        
        async refreshData() {
            await this.loadData();
        },
        
        async startAgent(agentId) {
            try {
                await fetch(`/api/v1/agents/${agentId}/start`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error starting agent:', error);
            }
        },
        
        async stopAgent(agentId) {
            try {
                await fetch(`/api/v1/agents/${agentId}/stop`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error stopping agent:', error);
            }
        },
        
        async startWorkflow(workflowId) {
            try {
                await fetch(`/api/v1/workflows/${workflowId}/start`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error starting workflow:', error);
            }
        },
        
        async pauseWorkflow(workflowId) {
            try {
                await fetch(`/api/v1/workflows/${workflowId}/pause`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error pausing workflow:', error);
            }
        },
        
        async cancelWorkflow(workflowId) {
            try {
                await fetch(`/api/v1/workflows/${workflowId}/cancel`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error cancelling workflow:', error);
            }
        },
        
        async loadModel(modelName) {
            try {
                await fetch(`/api/v1/models/${modelName}/load`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error loading model:', error);
            }
        },
        
        async unloadModel(modelName) {
            try {
                await fetch(`/api/v1/models/${modelName}/unload`, { method: 'POST' });
                await this.loadData();
            } catch (error) {
                console.error('Error unloading model:', error);
            }
        },
        
        createWorkflow() {
            // TODO: Implement workflow creation dialog
            alert('Workflow creation coming soon!');
        },
        
        updateAgentStatus(data) {
            const agent = this.agents.find(a => a.id === data.id);
            if (agent) {
                agent.status = data.status;
            }
        },
        
        updateWorkflowStatus(data) {
            const workflow = this.workflows.find(w => w.id === data.id);
            if (workflow) {
                workflow.status = data.status;
                workflow.progress = data.progress;
            }
        },
        
        getWorkflowStatusClass(status) {
            const classes = {
                'pending': 'bg-gray-100 text-gray-800',
                'running': 'bg-blue-100 text-blue-800',
                'paused': 'bg-yellow-100 text-yellow-800',
                'completed': 'bg-green-100 text-green-800',
                'failed': 'bg-red-100 text-red-800',
                'cancelled': 'bg-gray-100 text-gray-800'
            };
            return classes[status] || 'bg-gray-100 text-gray-800';
        },
        
        initializeCharts() {
            // Performance Chart
            const performanceCtx = document.getElementById('performanceChart').getContext('2d');
            new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
                    datasets: [{
                        label: 'CPU Usage (%)',
                        data: [65, 59, 80, 81, 56],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Memory Usage (%)',
                        data: [28, 48, 40, 19, 86],
                        borderColor: 'rgb(16, 185, 129)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
            
            // Activity Chart
            const activityCtx = document.getElementById('activityChart').getContext('2d');
            new Chart(activityCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Code Generation', 'Debugging', 'Testing', 'Deployment'],
                    datasets: [{
                        data: [30, 25, 20, 25],
                        backgroundColor: [
                            'rgb(59, 130, 246)',
                            'rgb(16, 185, 129)',
                            'rgb(245, 158, 11)',
                            'rgb(239, 68, 68)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }
}).mount('#app');
        """
    
    async def start(self):
        """Start the dashboard server."""
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            self.server_task = asyncio.create_task(server.serve())
            logger.info(f"Dashboard server started at http://{self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting dashboard server: {e}")
            return False
    
    async def stop(self):
        """Stop the dashboard server."""
        if self.server_task:
            self.server_task.cancel()
            try:
                await self.server_task
            except asyncio.CancelledError:
                pass
            self.server_task = None
        
        logger.info("Dashboard server stopped")
    
    async def broadcast_update(self, message_type: str, data: Any):
        """Broadcast update to all connected clients."""
        await self.websocket_manager.broadcast({
            "type": message_type,
            "data": data
        })
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}",
            "running": self.server_task is not None and not self.server_task.done()
        }