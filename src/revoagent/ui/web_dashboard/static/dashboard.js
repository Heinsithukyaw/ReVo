
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
        