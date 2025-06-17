import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  Play, 
  Square, 
  Settings, 
  Download,
  Copy,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Code,
  Bug,
  TestTube,
  Rocket,
  Globe,
  Shield,
  FileText,
  Zap,
  Brain,
  Sparkles,
  Eye,
  Edit3,
  Save
} from 'lucide-react';
import toast from 'react-hot-toast';

interface AgentExecutionPanelProps {
  agentType: string;
  onBack: () => void;
}

const AgentExecutionPanel: React.FC<AgentExecutionPanelProps> = ({
  agentType,
  onBack
}) => {
  const [taskDescription, setTaskDescription] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionHistory, setExecutionHistory] = useState<any[]>([]);
  const [selectedParameters, setSelectedParameters] = useState<any>({});
  const [isPreviewMode, setIsPreviewMode] = useState(false);

  // Agent metadata
  const agentMetadata = {
    code_generator: {
      name: 'Enhanced Code Generator',
      description: 'Generate high-quality code with AI assistance',
      icon: Code,
      color: 'blue',
      hasImplementation: true,
      parameters: {
        language: { type: 'select', options: ['python', 'javascript', 'typescript', 'java', 'go'], default: 'python' },
        framework: { type: 'select', options: ['none', 'react', 'vue', 'express', 'fastapi'], default: 'none' },
        includeTests: { type: 'boolean', default: true },
        codeStyle: { type: 'select', options: ['clean', 'production', 'prototype'], default: 'clean' }
      },
      examples: [
        'Create a REST API for user authentication',
        'Build a React component for data visualization',
        'Generate Python code for machine learning model training'
      ]
    },
    debug_agent: {
      name: 'Debug Detective',
      description: 'Identify and fix code issues automatically',
      icon: Bug,
      color: 'red',
      hasImplementation: true,
      parameters: {
        debugLevel: { type: 'select', options: ['basic', 'detailed', 'comprehensive'], default: 'detailed' },
        includeStackTrace: { type: 'boolean', default: true },
        suggestFixes: { type: 'boolean', default: true },
        analyzePerformance: { type: 'boolean', default: false }
      },
      examples: [
        'Debug this error: TypeError: Cannot read property of undefined',
        'Find performance bottlenecks in my React component',
        'Analyze memory leaks in Node.js application'
      ]
    },
    testing_agent: {
      name: 'Testing Specialist',
      description: 'Generate comprehensive test suites',
      icon: TestTube,
      color: 'green',
      hasImplementation: true,
      parameters: {
        testType: { type: 'select', options: ['unit', 'integration', 'e2e', 'all'], default: 'unit' },
        framework: { type: 'select', options: ['jest', 'mocha', 'pytest', 'cypress'], default: 'jest' },
        coverage: { type: 'select', options: ['basic', 'comprehensive'], default: 'comprehensive' },
        mockingStrategy: { type: 'select', options: ['minimal', 'extensive'], default: 'minimal' }
      },
      examples: [
        'Generate unit tests for my user service class',
        'Create integration tests for payment API',
        'Build e2e tests for user registration flow'
      ]
    },
    deploy_agent: {
      name: 'Deployment Manager',
      description: 'Automate deployment and infrastructure',
      icon: Rocket,
      color: 'purple',
      hasImplementation: true,
      parameters: {
        platform: { type: 'select', options: ['aws', 'gcp', 'azure', 'vercel', 'docker'], default: 'docker' },
        environment: { type: 'select', options: ['development', 'staging', 'production'], default: 'staging' },
        includeMonitoring: { type: 'boolean', default: true },
        autoScale: { type: 'boolean', default: false }
      },
      examples: [
        'Deploy React app to Vercel with CI/CD',
        'Create Docker containerization for Python API',
        'Set up AWS infrastructure with Terraform'
      ]
    },
    browser_agent: {
      name: 'Web Browser Assistant',
      description: 'Automate web interactions and testing',
      icon: Globe,
      color: 'cyan',
      hasImplementation: true,
      parameters: {
        browser: { type: 'select', options: ['chrome', 'firefox', 'safari'], default: 'chrome' },
        mode: { type: 'select', options: ['visible', 'headless'], default: 'visible' },
        waitStrategy: { type: 'select', options: ['fast', 'normal', 'patient'], default: 'normal' },
        screenshotOnError: { type: 'boolean', default: true }
      },
      examples: [
        'Scrape product data from e-commerce website',
        'Automate form submission testing',
        'Monitor website uptime and performance'
      ]
    },
    security_agent: {
      name: 'Security Guardian',
      description: 'Comprehensive security analysis and vulnerability scanning',
      icon: Shield,
      color: 'orange',
      hasImplementation: false, // Missing frontend - we'll implement it now!
      parameters: {
        scanType: { type: 'select', options: ['quick', 'standard', 'comprehensive'], default: 'standard' },
        includeStaticAnalysis: { type: 'boolean', default: true },
        checkCompliance: { type: 'select', options: ['none', 'owasp', 'pci-dss', 'sox'], default: 'owasp' },
        severityThreshold: { type: 'select', options: ['low', 'medium', 'high', 'critical'], default: 'medium' }
      },
      examples: [
        'Scan codebase for security vulnerabilities',
        'Check OWASP Top 10 compliance',
        'Analyze API endpoints for security issues'
      ]
    },
    documentation_agent: {
      name: 'Documentation Master',
      description: 'Generate comprehensive documentation automatically',
      icon: FileText,
      color: 'indigo',
      hasImplementation: false, // Missing frontend - we'll implement it now!
      parameters: {
        docType: { type: 'select', options: ['api', 'readme', 'user-guide', 'technical'], default: 'api' },
        includeExamples: { type: 'boolean', default: true },
        format: { type: 'select', options: ['markdown', 'html', 'pdf'], default: 'markdown' },
        detailLevel: { type: 'select', options: ['brief', 'detailed', 'comprehensive'], default: 'detailed' }
      },
      examples: [
        'Generate API documentation from OpenAPI spec',
        'Create comprehensive README for GitHub project',
        'Build user guide for React component library'
      ]
    },
    performance_optimizer: {
      name: 'Performance Optimizer',
      description: 'Analyze and optimize system performance',
      icon: Zap,
      color: 'yellow',
      hasImplementation: false, // Missing frontend - we'll implement it now!
      parameters: {
        analysisType: { type: 'select', options: ['cpu', 'memory', 'network', 'database', 'all'], default: 'all' },
        optimizationLevel: { type: 'select', options: ['conservative', 'balanced', 'aggressive'], default: 'balanced' },
        includeRecommendations: { type: 'boolean', default: true },
        benchmarkAfter: { type: 'boolean', default: false }
      },
      examples: [
        'Optimize database query performance',
        'Analyze React component rendering performance',
        'Improve API response times'
      ]
    },
    architecture_advisor: {
      name: 'Architecture Advisor',
      description: 'Strategic architecture guidance and system design',
      icon: Brain,
      color: 'pink',
      hasImplementation: false, // Missing frontend - we'll implement it now!
      parameters: {
        projectScale: { type: 'select', options: ['small', 'medium', 'large', 'enterprise'], default: 'medium' },
        architecture: { type: 'select', options: ['monolith', 'microservices', 'serverless', 'hybrid'], default: 'microservices' },
        includeDiagrams: { type: 'boolean', default: true },
        focusArea: { type: 'select', options: ['scalability', 'security', 'performance', 'maintainability'], default: 'scalability' }
      },
      examples: [
        'Design microservices architecture for e-commerce platform',
        'Create scalable data pipeline architecture',
        'Review existing system architecture for improvements'
      ]
    }
  };

  const currentAgent = agentMetadata[agentType as keyof typeof agentMetadata];

  useEffect(() => {
    // Initialize default parameters
    if (currentAgent?.parameters) {
      const defaults: any = {};
      Object.entries(currentAgent.parameters).forEach(([key, param]: [string, any]) => {
        defaults[key] = param.default;
      });
      setSelectedParameters(defaults);
    }
  }, [agentType, currentAgent]);

  const executeAgent = async () => {
    if (!taskDescription.trim()) {
      toast.error('Please provide a task description');
      return;
    }

    setIsExecuting(true);
    
    try {
      // If agent doesn't have implementation, show demo mode
      if (!currentAgent.hasImplementation) {
        // Simulate execution for agents without frontend implementation
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const mockResult = {
          success: true,
          output: `✨ ${currentAgent.name} Analysis Complete!\n\n` +
                  `Task: ${taskDescription}\n\n` +
                  `🎯 Key Findings:\n` +
                  `• Analysis completed successfully\n` +
                  `• Recommendations generated\n` +
                  `• Best practices identified\n\n` +
                  `📋 Next Steps:\n` +
                  `• Review generated recommendations\n` +
                  `• Implement suggested improvements\n` +
                  `• Monitor results\n\n` +
                  `⚠️ Note: This is a demo response. Full functionality coming soon!`,
          metadata: {
            executionTime: '3.2s',
            confidence: 95,
            tokensUsed: 1250,
            cost: 0.00 // Local model - free!
          }
        };
        
        setExecutionResult(mockResult);
        setExecutionHistory(prev => [{
          id: Date.now(),
          timestamp: new Date().toISOString(),
          task: taskDescription,
          result: mockResult,
          parameters: selectedParameters
        }, ...prev]);
        
        toast.success(`${currentAgent.name} executed successfully!`);
      } else {
        // Make actual API call for implemented agents
        const response = await fetch(`/api/agents/${agentType}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            task_description: taskDescription,
            parameters: selectedParameters,
            preferred_provider: 'deepseek_r1'
          })
        });
        
        const result = await response.json();
        
        if (response.ok) {
          // Poll for result
          const pollResult = async (taskId: string) => {
            const statusResponse = await fetch(`/api/agents/tasks/${taskId}`);
            const taskStatus = await statusResponse.json();
            
            if (taskStatus.status === 'completed') {
              setExecutionResult(taskStatus.result);
              setExecutionHistory(prev => [{
                id: Date.now(),
                timestamp: new Date().toISOString(),
                task: taskDescription,
                result: taskStatus.result,
                parameters: selectedParameters
              }, ...prev]);
              toast.success(`${currentAgent.name} completed successfully!`);
            } else if (taskStatus.status === 'failed') {
              toast.error(`Execution failed: ${taskStatus.error}`);
            } else {
              // Still running, poll again
              setTimeout(() => pollResult(taskId), 2000);
            }
          };
          
          pollResult(result.task_id);
        } else {
          throw new Error(result.detail || 'Execution failed');
        }
      }
    } catch (error) {
      console.error('Execution error:', error);
      toast.error('Execution failed. Please try again.');
    } finally {
      setIsExecuting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const downloadResult = () => {
    if (!executionResult) return;
    
    const content = `${currentAgent.name} Execution Result\n` +
                   `Generated: ${new Date().toISOString()}\n` +
                   `Task: ${taskDescription}\n\n` +
                   `${executionResult.output}`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${agentType}_result_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Result downloaded!');
  };

  const renderParameterInput = (key: string, param: any) => {
    const value = selectedParameters[key];
    
    switch (param.type) {
      case 'select':
        return (
          <select
            className="glass-input"
            value={value}
            onChange={(e) => setSelectedParameters(prev => ({ ...prev, [key]: e.target.value }))}
          >
            {param.options.map((option: string) => (
              <option key={option} value={option}>
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </option>
            ))}
          </select>
        );
      case 'boolean':
        return (
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => setSelectedParameters(prev => ({ ...prev, [key]: e.target.checked }))}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-blue-400 focus:ring-blue-400/50"
            />
            <span className="text-white/80">
              {value ? 'Enabled' : 'Disabled'}
            </span>
          </label>
        );
      default:
        return (
          <input
            type="text"
            className="glass-input"
            value={value}
            onChange={(e) => setSelectedParameters(prev => ({ ...prev, [key]: e.target.value }))}
          />
        );
    }
  };

  if (!currentAgent) {
    return (
      <div className="glass-card p-8 text-center">
        <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Agent Not Found</h2>
        <p className="text-white/70 mb-6">The requested agent type "{agentType}" could not be found.</p>
        <button onClick={onBack} className="glass-button primary">
          <ArrowLeft className="w-4 h-4" />
          Back to Agents
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack}
            className="glass-button p-3"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-4">
            <div className={`p-4 rounded-xl bg-gradient-to-br from-${currentAgent.color}-400 to-${currentAgent.color}-600 shadow-lg`}>
              <currentAgent.icon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">{currentAgent.name}</h1>
              <p className="text-white/70">{currentAgent.description}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!currentAgent.hasImplementation && (
            <div className="px-4 py-2 bg-orange-400/20 text-orange-300 rounded-lg border border-orange-400/30">
              🚧 Demo Mode - Full Implementation Coming Soon
            </div>
          )}
          <button className="glass-button">
            <Settings className="w-4 h-4" />
            Settings
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        {/* Input Panel */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Task Description */}
          <div className="glass-card p-6">
            <h2 className="text-xl font-bold text-white mb-4">Task Description</h2>
            
            <div className="space-y-4">
              <textarea
                className="glass-input min-h-32 resize-y"
                placeholder={`Describe what you want ${currentAgent.name} to do...`}
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
              />
              
              {/* Example suggestions */}
              <div className="space-y-2">
                <label className="text-white/70 text-sm font-medium">Quick Examples:</label>
                <div className="flex flex-wrap gap-2">
                  {currentAgent.examples.map((example, index) => (
                    <button
                      key={index}
                      className="px-3 py-1 text-sm glass-subtle text-white/80 rounded-lg hover:bg-white/20 transition-colors"
                      onClick={() => setTaskDescription(example)}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Parameters */}
          {currentAgent.parameters && Object.keys(currentAgent.parameters).length > 0 && (
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(currentAgent.parameters).map(([key, param]: [string, any]) => (
                  <div key={key} className="space-y-2">
                    <label className="text-white/80 font-medium capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </label>
                    {renderParameterInput(key, param)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Execution Controls */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Execute Agent</h2>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={executeAgent}
                  disabled={isExecuting || !taskDescription.trim()}
                  className={`glass-button primary flex items-center gap-2 ${
                    isExecuting ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {isExecuting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Execute Agent
                    </>
                  )}
                </button>
                
                {isExecuting && (
                  <button className="glass-button">
                    <Square className="w-4 h-4" />
                    Stop
                  </button>
                )}
              </div>
            </div>
            
            {isExecuting && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center gap-3 text-white/80">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Agent is processing your request...</span>
                </div>
                <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-500 animate-pulse" />
                </div>
              </div>
            )}
          </div>

          {/* Result Display */}
          {executionResult && (
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white">Execution Result</h2>
                
                <div className="flex items-center gap-3">
                  <button 
                    onClick={() => copyToClipboard(executionResult.output)}
                    className="glass-button"
                  >
                    <Copy className="w-4 h-4" />
                    Copy
                  </button>
                  <button 
                    onClick={downloadResult}
                    className="glass-button"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                  <button 
                    onClick={() => setIsPreviewMode(!isPreviewMode)}
                    className="glass-button"
                  >
                    {isPreviewMode ? <Edit3 className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    {isPreviewMode ? 'Edit' : 'Preview'}
                  </button>
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Result status */}
                <div className="flex items-center gap-3">
                  {executionResult.success ? (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400" />
                  )}
                  <span className={`font-medium ${
                    executionResult.success ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {executionResult.success ? 'Execution Successful' : 'Execution Failed'}
                  </span>
                </div>

                {/* Result content */}
                <div className="relative">
                  {isPreviewMode ? (
                    <div className="glass-subtle p-4 rounded-lg">
                      <pre className="text-white/90 whitespace-pre-wrap text-sm font-mono">
                        {executionResult.output}
                      </pre>
                    </div>
                  ) : (
                    <textarea
                      className="glass-input min-h-64 font-mono text-sm"
                      value={executionResult.output}
                      readOnly
                    />
                  )}
                </div>

                {/* Metadata */}
                {executionResult.metadata && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/10">
                    <div className="text-center">
                      <div className="text-white font-semibold">{executionResult.metadata.executionTime}</div>
                      <div className="text-white/60 text-sm">Execution Time</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{executionResult.metadata.confidence}%</div>
                      <div className="text-white/60 text-sm">Confidence</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-semibold">{executionResult.metadata.tokensUsed}</div>
                      <div className="text-white/60 text-sm">Tokens Used</div>
                    </div>
                    <div className="text-center">
                      <div className="text-green-400 font-semibold">${executionResult.metadata.cost}</div>
                      <div className="text-white/60 text-sm">Cost</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          
          {/* Agent Status */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-bold text-white mb-4">Agent Status</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-white/70">Status</span>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-green-400 font-medium">Active</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-white/70">Implementation</span>
                <span className={`font-medium ${
                  currentAgent.hasImplementation ? 'text-green-400' : 'text-orange-400'
                }`}>
                  {currentAgent.hasImplementation ? '✅ Complete' : '🚧 In Progress'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-white/70">Cost</span>
                <span className="text-green-400 font-medium">FREE</span>
              </div>
            </div>
          </div>

          {/* Execution History */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-bold text-white mb-4">Recent Executions</h3>
            
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {executionHistory.length > 0 ? (
                executionHistory.map((execution) => (
                  <div key={execution.id} className="glass-subtle p-3 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white/80 text-sm font-medium">
                        {new Date(execution.timestamp).toLocaleTimeString()}
                      </span>
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-white/70 text-sm line-clamp-2">
                      {execution.task}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-6">
                  <Clock className="w-8 h-8 text-white/30 mx-auto mb-2" />
                  <p className="text-white/50 text-sm">No recent executions</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
            
            <div className="space-y-3">
              <button className="glass-button w-full justify-start">
                <Sparkles className="w-4 h-4" />
                Generate Example Task
              </button>
              <button className="glass-button w-full justify-start">
                <Save className="w-4 h-4" />
                Save Configuration
              </button>
              <button className="glass-button w-full justify-start">
                <RefreshCw className="w-4 h-4" />
                Reset Parameters
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentExecutionPanel;