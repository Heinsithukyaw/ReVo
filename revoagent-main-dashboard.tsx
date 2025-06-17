import React, { useState, useEffect } from 'react';
import { 
  Activity, Brain, Zap, Palette, MessageSquare, Settings, 
  Users, Database, Shield, BarChart3, GitBranch, Slack,
  Cpu, HardDrive, Network, TrendingUp, Bell, Play,
  Search, Download, Upload, RefreshCw, Eye, Code,
  Bug, TestTube, Rocket, FileText, Monitor, Lock
} from 'lucide-react';

const ReVoAgentDashboard = () => {
  const [activeEngine, setActiveEngine] = useState('memory');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({
    cpu: 67.8,
    memory: 89.2,
    disk: 34.1,
    network: 56.3,
    activeRequests: 47,
    queueLength: 12,
    responseTime: 0.002,
    uptime: 99.9
  });

  const [engineStatus, setEngineStatus] = useState({
    memory: { status: 'active', entities: 1247893, speed: 95, cost: 0 },
    parallel: { status: 'active', workers: 8, load: 45.2, throughput: 150 },
    creative: { status: 'active', patterns: 15, novelty: 94, innovation: 7.2 }
  });

  const [costSavings, setCostSavings] = useState({
    totalSavings: 2847,
    localProcessing: 94.7,
    cloudFallback: 5.3,
    deepSeekCost: 0,
    openAICost: 12.30,
    llamaCost: 0,
    anthropicCost: 8.70,
    monthlyProjection: 3200
  });

  const agents = {
    codeSpecialists: [
      { id: 'code-analyst', name: 'Code Analyst', icon: Code, status: 'active', tasks: 15 },
      { id: 'debug-detective', name: 'Debug Detective', icon: Bug, status: 'active', tasks: 8 },
      { id: 'security-scanner', name: 'Security Scanner', icon: Shield, status: 'active', tasks: 3 },
      { id: 'perf-optimizer', name: 'Performance Optimizer', icon: TrendingUp, status: 'active', tasks: 5 },
      { id: 'doc-generator', name: 'Documentation Generator', icon: FileText, status: 'idle', tasks: 0 }
    ],
    workflow: [
      { id: 'workflow-manager', name: 'Workflow Manager', icon: GitBranch, status: 'active', tasks: 12 },
      { id: 'devops-integration', name: 'DevOps Integration', icon: Settings, status: 'active', tasks: 7 },
      { id: 'cicd-pipeline', name: 'CI/CD Pipeline', icon: Rocket, status: 'active', tasks: 4 },
      { id: 'test-coordinator', name: 'Testing Coordinator', icon: TestTube, status: 'active', tasks: 9 },
      { id: 'deploy-manager', name: 'Deployment Manager', icon: Upload, status: 'idle', tasks: 0 }
    ],
    knowledge: [
      { id: 'knowledge-coord', name: 'Knowledge Coordinator', icon: Brain, status: 'active', tasks: 23 },
      { id: 'memory-synthesis', name: 'Memory Synthesis', icon: Database, status: 'active', tasks: 18 },
      { id: 'pattern-recognition', name: 'Pattern Recognition', icon: Eye, status: 'active', tasks: 11 },
      { id: 'learning-optimizer', name: 'Learning Optimizer', icon: TrendingUp, status: 'active', tasks: 6 },
      { id: 'context-manager', name: 'Context Manager', icon: RefreshCw, status: 'active', tasks: 14 }
    ],
    communication: [
      { id: 'multi-agent-chat', name: 'Multi-Agent Chat', icon: MessageSquare, status: 'active', tasks: 31 },
      { id: 'slack-integration', name: 'Slack Integration', icon: Slack, status: 'active', tasks: 5 },
      { id: 'github-integration', name: 'GitHub Integration', icon: GitBranch, status: 'active', tasks: 8 },
      { id: 'jira-integration', name: 'JIRA Integration', icon: Users, status: 'active', tasks: 3 },
      { id: 'notification-manager', name: 'Notification Manager', icon: Bell, status: 'active', tasks: 12 }
    ]
  };

  const activeTasks = [
    { id: 1, task: 'Analyzing repository structure', progress: 75, agent: 'code-analyst' },
    { id: 2, task: 'Building deployment pipeline', progress: 45, agent: 'deploy-manager' },
    { id: 3, task: 'Updating memory graph', progress: 88, agent: 'memory-synthesis' },
    { id: 4, task: 'Generating documentation', progress: 32, agent: 'doc-generator' },
    { id: 5, task: 'Running security scan', progress: 67, agent: 'security-scanner' }
  ];

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        cpu: Math.max(30, Math.min(90, prev.cpu + (Math.random() - 0.5) * 5)),
        memory: Math.max(40, Math.min(95, prev.memory + (Math.random() - 0.5) * 3)),
        activeRequests: Math.max(0, prev.activeRequests + Math.floor((Math.random() - 0.5) * 10))
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const EngineStatusCard = ({ engine, data, icon: Icon }) => (
    <div className={`p-6 rounded-2xl backdrop-blur-md border transition-all duration-300 cursor-pointer ${
      activeEngine === engine 
        ? 'bg-blue-500/20 border-blue-400/50 shadow-lg shadow-blue-500/25' 
        : 'bg-white/10 border-white/20 hover:bg-white/15'
    }`}
    onClick={() => setActiveEngine(engine)}>
      <div className="flex items-center gap-3 mb-4">
        <Icon className="w-8 h-8 text-blue-400" />
        <h3 className="text-xl font-bold text-white capitalize">{engine} Engine</h3>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-blue-200">Status:</span>
          <span className="text-green-400 font-semibold">●●● Active</span>
        </div>
        {engine === 'memory' && (
          <>
            <div className="flex justify-between">
              <span className="text-blue-200">Entities:</span>
              <span className="text-white font-mono">{data.entities.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-200">Speed:</span>
              <span className="text-white">&lt;{data.speed}ms</span>
            </div>
          </>
        )}
        {engine === 'parallel' && (
          <>
            <div className="flex justify-between">
              <span className="text-blue-200">Workers:</span>
              <span className="text-white">{data.workers} Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-200">Load:</span>
              <span className="text-white">{data.load}%</span>
            </div>
          </>
        )}
        {engine === 'creative' && (
          <>
            <div className="flex justify-between">
              <span className="text-blue-200">Patterns:</span>
              <span className="text-white">{data.patterns} Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-200">Novelty:</span>
              <span className="text-white">{data.novelty}% Score</span>
            </div>
          </>
        )}
        <div className="flex justify-between">
          <span className="text-blue-200">Cost:</span>
          <span className="text-green-400 font-bold">${data.cost.toFixed(2)}/query</span>
        </div>
      </div>
    </div>
  );

  const AgentCard = ({ agent, category }) => (
    <div 
      className={`p-3 rounded-xl backdrop-blur-md border transition-all duration-200 cursor-pointer ${
        selectedAgent?.id === agent.id 
          ? 'bg-purple-500/20 border-purple-400/50' 
          : 'bg-white/5 border-white/10 hover:bg-white/10'
      }`}
      onClick={() => setSelectedAgent(agent)}
    >
      <div className="flex items-center gap-3">
        <agent.icon className="w-5 h-5 text-purple-400" />
        <div className="flex-1">
          <h4 className="text-white font-medium text-sm">{agent.name}</h4>
          <p className="text-purple-200 text-xs">{agent.tasks} active tasks</p>
        </div>
        <div className={`w-2 h-2 rounded-full ${
          agent.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'
        }`} />
      </div>
    </div>
  );

  const MetricBar = ({ label, value, color = 'blue' }) => (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-blue-200">{label}:</span>
        <span className="text-white font-mono">{value}%</span>
      </div>
      <div className="w-full bg-white/10 rounded-full h-2">
        <div 
          className={`h-2 rounded-full bg-gradient-to-r from-${color}-400 to-${color}-600`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Top Navigation */}
      <div className="bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Rocket className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">reVoAgent</h1>
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">v2.0</span>
            </div>
            <div className="flex items-center gap-6 ml-8">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-sm">Memory: Active</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-sm">Parallel: 10x Performance</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 text-sm">Creative: 94% Novelty</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm font-bold">
              Cost Savings: $0.00
            </div>
            <button className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors">
              <Settings className="w-5 h-5 text-white" />
            </button>
            <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full" />
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Left Sidebar */}
        <div className="w-80 bg-black/20 backdrop-blur-md border-r border-white/10 h-screen overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Dashboard Section */}
            <div>
              <h3 className="text-white font-bold mb-3 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                DASHBOARD
              </h3>
              <div className="space-y-2">
                <button className="w-full text-left p-2 text-blue-200 hover:bg-white/10 rounded-lg transition-colors">
                  Three-Engine Overview
                </button>
                <button className="w-full text-left p-2 text-blue-200 hover:bg-white/10 rounded-lg transition-colors">
                  System Health Monitor
                </button>
                <button className="w-full text-left p-2 text-blue-200 hover:bg-white/10 rounded-lg transition-colors">
                  Cost Optimization Metrics
                </button>
              </div>
            </div>

            {/* AI Agents Hub */}
            <div>
              <h3 className="text-white font-bold mb-3 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" />
                AI AGENTS HUB (20+)
              </h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-purple-300 text-sm font-medium mb-2">Code Specialists</h4>
                  <div className="space-y-1">
                    {agents.codeSpecialists.map(agent => (
                      <AgentCard key={agent.id} agent={agent} category="code" />
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-purple-300 text-sm font-medium mb-2">Development Workflow</h4>
                  <div className="space-y-1">
                    {agents.workflow.map(agent => (
                      <AgentCard key={agent.id} agent={agent} category="workflow" />
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-purple-300 text-sm font-medium mb-2">Knowledge & Memory</h4>
                  <div className="space-y-1">
                    {agents.knowledge.map(agent => (
                      <AgentCard key={agent.id} agent={agent} category="knowledge" />
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-purple-300 text-sm font-medium mb-2">Communication</h4>
                  <div className="space-y-1">
                    {agents.communication.map(agent => (
                      <AgentCard key={agent.id} agent={agent} category="communication" />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Additional Modules */}
            <div className="space-y-3">
              <button className="w-full flex items-center gap-3 p-3 text-white hover:bg-white/10 rounded-lg transition-colors">
                <Database className="w-5 h-5 text-cyan-400" />
                <span>Memory Center</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 text-white hover:bg-white/10 rounded-lg transition-colors">
                <Zap className="w-5 h-5 text-yellow-400" />
                <span>Parallel Processing</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 text-white hover:bg-white/10 rounded-lg transition-colors">
                <Palette className="w-5 h-5 text-pink-400" />
                <span>Creative Innovation Engine</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 text-white hover:bg-white/10 rounded-lg transition-colors">
                <MessageSquare className="w-5 h-5 text-green-400" />
                <span>Multi-Agent Chat</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {/* Three Engine Status Overview */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            <EngineStatusCard 
              engine="memory" 
              data={engineStatus.memory} 
              icon={Brain} 
            />
            <EngineStatusCard 
              engine="parallel" 
              data={engineStatus.parallel} 
              icon={Zap} 
            />
            <EngineStatusCard 
              engine="creative" 
              data={engineStatus.creative} 
              icon={Palette} 
            />
          </div>

          <div className="grid grid-cols-2 gap-6 mb-8">
            {/* System Metrics */}
            <div className="p-6 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
              <h3 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
                <Monitor className="w-6 h-6 text-green-400" />
                Real-Time System Metrics
              </h3>
              <div className="space-y-4">
                <MetricBar label="CPU" value={systemMetrics.cpu} color="blue" />
                <MetricBar label="Memory" value={systemMetrics.memory} color="purple" />
                <MetricBar label="Disk" value={systemMetrics.disk} color="green" />
                <MetricBar label="Network" value={systemMetrics.network} color="yellow" />
              </div>
              <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-white/10">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{systemMetrics.activeRequests}</div>
                  <div className="text-blue-200 text-sm">Active Requests</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{systemMetrics.responseTime}s</div>
                  <div className="text-blue-200 text-sm">Response Time</div>
                </div>
              </div>
            </div>

            {/* Cost Optimization */}
            <div className="p-6 bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-md rounded-2xl border border-green-400/30">
              <h3 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-green-400" />
                Cost Optimization Dashboard
              </h3>
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-green-400">
                  ${costSavings.totalSavings.toLocaleString()}
                </div>
                <div className="text-green-200">Total Savings This Month</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-white/10 rounded-lg">
                  <div className="text-lg font-bold text-white">{costSavings.localProcessing}%</div>
                  <div className="text-green-200 text-sm">Local Processing</div>
                </div>
                <div className="text-center p-3 bg-white/10 rounded-lg">
                  <div className="text-lg font-bold text-white">{costSavings.cloudFallback}%</div>
                  <div className="text-yellow-200 text-sm">Cloud Fallback</div>
                </div>
              </div>
              <div className="mt-4 text-center">
                <div className="text-lg font-bold text-green-400">
                  ${costSavings.monthlyProjection.toLocaleString()} projected savings
                </div>
                <div className="text-green-200 text-sm">vs cloud-only solutions</div>
              </div>
            </div>
          </div>

          {/* Memory & Knowledge Graph */}
          <div className="p-6 bg-gradient-to-br from-purple-500/20 to-blue-500/20 backdrop-blur-md rounded-2xl border border-purple-400/30 mb-8">
            <h3 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
              <Database className="w-6 h-6 text-purple-400" />
              Memory & Knowledge Graph Overview
            </h3>
            <div className="grid grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">1.24M</div>
                <div className="text-purple-200 text-sm">Knowledge Entities</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">3.45M</div>
                <div className="text-blue-200 text-sm">Relationships</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">+2,341</div>
                <div className="text-green-200 text-sm">Daily Growth</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">97.8%</div>
                <div className="text-yellow-200 text-sm">Query Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-400">89</div>
                <div className="text-cyan-200 text-sm">Agent Connections</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-80 bg-black/20 backdrop-blur-md border-l border-white/10 h-screen overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Quick Actions */}
            <div>
              <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                <Play className="w-5 h-5 text-green-400" />
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full p-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Start Multi-Agent Task
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-green-500/20 to-emerald-500/20 hover:from-green-500/30 hover:to-emerald-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Open Agent Chat
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Build New Workflow
                </button>
                <button className="w-full p-3 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 hover:from-yellow-500/30 hover:to-orange-500/30 rounded-lg text-white transition-all duration-200 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Generate Report
                </button>
              </div>
            </div>

            {/* Real-time Notifications */}
            <div>
              <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5 text-blue-400" />
                Live Notifications
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-green-500/20 border border-green-400/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-green-400 text-sm font-medium">Code analysis complete</span>
                  </div>
                </div>
                <div className="p-3 bg-yellow-500/20 border border-yellow-400/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                    <span className="text-yellow-400 text-sm font-medium">Memory sync in progress</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-500/20 border border-blue-400/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full" />
                    <span className="text-blue-400 text-sm font-medium">New pattern discovered</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Tasks */}
            <div>
              <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Active Tasks
              </h3>
              <div className="space-y-3">
                {activeTasks.map(task => (
                  <div key={task.id} className="p-3 bg-white/5 rounded-lg border border-white/10">
                    <div className="text-white text-sm font-medium mb-2">{task.task}</div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex-1 bg-white/10 rounded-full h-1">
                        <div 
                          className="h-1 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full transition-all duration-300"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-purple-300 text-xs">{task.progress}%</span>
                    </div>
                    <div className="text-purple-200 text-xs">Agent: {task.agent}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReVoAgentDashboard;