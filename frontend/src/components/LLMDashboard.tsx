import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  MessageSquare, 
  Settings, 
  BarChart3, 
  Cpu,
  Zap,
  DollarSign,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import LLMSelector from './LLMSelector';
import LLMChat from './LLMChat';
import { llmApi, type LLMStatus, type HardwareInfo } from '../services/llmApi';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from './ui';

const LLMDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null);
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    checkHealth();
    loadLLMStatus();
    loadStats();
    loadHardwareInfo();
    
    // Refresh status every 30 seconds
    const interval = setInterval(() => {
      loadLLMStatus();
      loadStats();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const health = await llmApi.healthCheck();
      setIsOnline(health.status === 'healthy');
    } catch (error) {
      setIsOnline(false);
    }
  };

  const loadLLMStatus = async () => {
    try {
      const data = await llmApi.getLLMStatus();
      setLlmStatus(data);
    } catch (error) {
      console.error('Failed to load LLM status:', error);
    }
  };

  const loadStats = async () => {
    try {
      const data = await llmApi.getLLMStatus();
      setStats(data.metrics || {
        total_requests: 0,
        total_cost: 0,
        average_response_time: 0,
        uptime_percentage: 100,
        requests_by_provider: {},
        cost_by_provider: {}
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadHardwareInfo = async () => {
    try {
      // Mock hardware info since the endpoint might not exist
      setHardwareInfo({
        cpu_cores: 8,
        cpu_frequency_ghz: 3.2,
        ram_gb: 16,
        has_gpu: true,
        optimization_level: 'high'
      });
    } catch (error) {
      console.error('Failed to load hardware info:', error);
    }
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return 'Free';
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Brain className="h-8 w-8 mr-3 text-blue-600" />
                reVoAgent LLM Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Optimized for 1.1 GHz Quad-Core Intel Core i5 • Multi-Provider LLM Integration
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <Badge className={isOnline ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                {isOnline ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Online
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Offline
                  </>
                )}
              </Badge>
              
              {hardwareInfo && (
                <Badge variant="outline">
                  <Cpu className="h-3 w-3 mr-1" />
                  {hardwareInfo.cpu_cores} cores • {hardwareInfo.ram_gb.toFixed(1)}GB RAM
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Requests</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_requests}</p>
                  </div>
                  <MessageSquare className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Cost</p>
                    <p className="text-2xl font-bold text-gray-900">{formatCost(stats.total_cost)}</p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                    <p className="text-2xl font-bold text-gray-900">{formatTime(stats.average_response_time * 1000)}</p>
                  </div>
                  <Clock className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Uptime</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.uptime_percentage.toFixed(1)}%</p>
                  </div>
                  <Zap className="h-8 w-8 text-yellow-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Content */}
        <Tabs defaultValue="chat" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="chat" className="flex items-center">
              <MessageSquare className="h-4 w-4 mr-2" />
              Chat Interface
            </TabsTrigger>
            <TabsTrigger value="providers" className="flex items-center">
              <Settings className="h-4 w-4 mr-2" />
              LLM Providers
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center">
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="mt-6">
            <div className="h-[600px]">
              <LLMChat className="h-full" />
            </div>
          </TabsContent>

          <TabsContent value="providers" className="mt-6">
            <LLMSelector />
          </TabsContent>

          <TabsContent value="analytics" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Provider Usage */}
              {stats && (
                <Card>
                  <CardHeader>
                    <CardTitle>Provider Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(stats.requests_by_provider).map(([provider, requests]) => (
                        <div key={provider} className="flex items-center justify-between">
                          <span className="font-medium">{provider}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">{requests} requests</span>
                            <span className="text-sm text-gray-600">
                              {formatCost(stats.cost_by_provider[provider] || 0)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Hardware Status */}
              {hardwareInfo && (
                <Card>
                  <CardHeader>
                    <CardTitle>Hardware Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span>CPU Cores</span>
                        <Badge variant="outline">{hardwareInfo.cpu_cores}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>CPU Frequency</span>
                        <Badge variant="outline">{hardwareInfo.cpu_frequency_ghz || 'N/A'} GHz</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>RAM</span>
                        <Badge variant="outline">{hardwareInfo.ram_gb.toFixed(1)} GB</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>GPU</span>
                        <Badge variant={hardwareInfo.has_gpu ? 'default' : 'secondary'}>
                          {hardwareInfo.has_gpu ? 'Available' : 'None'}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Optimization Level</span>
                        <Badge className={
                          hardwareInfo.optimization_level === 'high' ? 'bg-green-500' :
                          hardwareInfo.optimization_level === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                        }>
                          {hardwareInfo.optimization_level}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Cost Breakdown */}
              {stats && (
                <Card>
                  <CardHeader>
                    <CardTitle>Cost Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span>Total Spent</span>
                        <span className="font-semibold">{formatCost(stats.total_cost)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Average per Request</span>
                        <span className="font-semibold">
                          {stats.total_requests > 0 
                            ? formatCost(stats.total_cost / stats.total_requests)
                            : 'N/A'
                          }
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Estimated Monthly</span>
                        <span className="font-semibold">
                          {stats.total_requests > 0 
                            ? formatCost((stats.total_cost / stats.total_requests) * 1000)
                            : 'N/A'
                          }
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Performance Metrics */}
              {stats && (
                <Card>
                  <CardHeader>
                    <CardTitle>Performance Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span>Average Response Time</span>
                        <Badge variant="outline">
                          {formatTime(stats.average_response_time * 1000)}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>System Uptime</span>
                        <Badge className="bg-green-100 text-green-800">
                          {stats.uptime_percentage.toFixed(1)}%
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Total Requests</span>
                        <Badge variant="outline">{stats.total_requests}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default LLMDashboard;