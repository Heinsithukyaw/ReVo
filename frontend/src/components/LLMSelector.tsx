import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Cpu, 
  Cloud, 
  DollarSign, 
  Zap, 
  Settings, 
  Key,
  CheckCircle,
  AlertCircle,
  Info,
  RefreshCw,
  TestTube
} from 'lucide-react';
import { llmApi, type LLMProvider, type HardwareInfo } from '../services/llmApi';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Badge,
  Alert,
  AlertDescription,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from './ui';

// Using types from llmApi service

const LLMSelector: React.FC = () => {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [currentProvider, setCurrentProvider] = useState<string | null>(null);
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showApiKeyForm, setShowApiKeyForm] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  useEffect(() => {
    loadProviders();
    loadHardwareInfo();
  }, []);

  const loadProviders = async () => {
    try {
      const data = await llmApi.getProviders();
      setProviders(data.providers || []);
      setCurrentProvider(data.current_provider);
    } catch (error) {
      console.error('Failed to load providers:', error);
      setMessage({ type: 'error', text: 'Failed to load LLM providers' });
    }
  };

  const loadHardwareInfo = async () => {
    try {
      const data = await llmApi.getHardwareInfo();
      setHardwareInfo(data.hardware);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load hardware info:', error);
      setLoading(false);
    }
  };

  const switchProvider = async (providerId: string) => {
    setSwitching(true);
    try {
      const result = await llmApi.switchProvider({ provider: providerId });
      setCurrentProvider(result.current_provider);
      setMessage({ type: 'success', text: result.message });
      await loadProviders(); // Refresh provider list
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to switch provider' });
    } finally {
      setSwitching(false);
    }
  };

  const setApiKey = async (provider: string, apiKey: string) => {
    try {
      const result = await llmApi.setApiKey({ provider, api_key: apiKey });
      setMessage({ type: 'success', text: result.message });
      setShowApiKeyForm(null);
      await loadProviders(); // Refresh provider list
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to set API key' });
    }
  };

  const testProvider = async (providerId: string) => {
    setTesting(providerId);
    try {
      const result = await llmApi.testProvider(providerId);
      setMessage({ 
        type: result.success ? 'success' : 'error', 
        text: `${result.message} (${result.response_time}ms)` 
      });
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to test provider' });
    } finally {
      setTesting(null);
    }
  };

  const getProviderIcon = (provider: LLMProvider) => {
    if (provider.type === 'local') {
      return <Cpu className="h-4 w-4" />;
    }
    return <Cloud className="h-4 w-4" />;
  };

  const getProviderBadge = (provider: LLMProvider) => {
    if (provider.id === currentProvider) {
      return <Badge variant="default" className="bg-green-500">Current</Badge>;
    }
    if (!provider.available) {
      return <Badge variant="secondary">Unavailable</Badge>;
    }
    if (provider.type === 'local') {
      return <Badge variant="outline">Local</Badge>;
    }
    return <Badge variant="outline">API</Badge>;
  };

  const getCostBadge = (cost: number) => {
    if (cost === 0) {
      return <Badge className="bg-green-500">Free</Badge>;
    }
    if (cost < 0.01) {
      return <Badge className="bg-blue-500">Very Low Cost</Badge>;
    }
    if (cost < 0.02) {
      return <Badge className="bg-yellow-500">Low Cost</Badge>;
    }
    return <Badge className="bg-red-500">Higher Cost</Badge>;
  };

  const getHardwareRecommendation = () => {
    if (!hardwareInfo) return null;

    const { cpu_frequency_ghz, ram_gb, optimization_level } = hardwareInfo;

    if (optimization_level === 'low') {
      return {
        type: 'info' as const,
        title: 'Hardware Optimization Active',
        description: `Your system (${cpu_frequency_ghz || 'N/A'}GHz, ${ram_gb.toFixed(1)}GB RAM) is optimized for efficiency. API providers recommended for best performance.`
      };
    }

    return {
      type: 'success' as const,
      title: 'Good Hardware Detected',
      description: `Your system can run local models efficiently. Consider local options for zero-cost operation.`
    };
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-2">Loading LLM providers...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const recommendation = getHardwareRecommendation();

  return (
    <div className="space-y-6">
      {message && (
        <Alert className={message.type === 'error' ? 'border-red-500' : message.type === 'success' ? 'border-green-500' : 'border-blue-500'}>
          {message.type === 'error' ? <AlertCircle className="h-4 w-4" /> : 
           message.type === 'success' ? <CheckCircle className="h-4 w-4" /> : 
           <Info className="h-4 w-4" />}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      {recommendation && (
        <Alert className={recommendation.type === 'info' ? 'border-blue-500' : 'border-green-500'}>
          {recommendation.type === 'info' ? <Info className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
          <AlertDescription>
            <strong>{recommendation.title}:</strong> {recommendation.description}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="providers" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="providers">
            <Brain className="h-4 w-4 mr-2" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="hardware">
            <Cpu className="h-4 w-4 mr-2" />
            Hardware
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Brain className="h-5 w-5 mr-2" />
                Available LLM Providers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {providers.map((provider) => (
                  <Card key={provider.id} className={`transition-all ${provider.id === currentProvider ? 'ring-2 ring-blue-500' : ''}`}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {getProviderIcon(provider)}
                          <div>
                            <h3 className="font-semibold">{provider.name}</h3>
                            <p className="text-sm text-gray-600">{provider.type} provider</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {getCostBadge(provider.cost_per_request)}
                          {getProviderBadge(provider)}
                        </div>
                      </div>
                      
                      <div className="mt-3 flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className="flex items-center">
                            <DollarSign className="h-3 w-3 mr-1" />
                            ${provider.cost_per_request.toFixed(4)}/request
                          </span>
                          {provider.type === 'local' && (
                            <span className="flex items-center">
                              <Zap className="h-3 w-3 mr-1" />
                              Zero cost
                            </span>
                          )}
                        </div>
                        
                        <div className="flex space-x-2">
                          {provider.type === 'api' && !provider.has_api_key && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setShowApiKeyForm(provider.id)}
                            >
                              <Key className="h-3 w-3 mr-1" />
                              Set API Key
                            </Button>
                          )}
                          
                          {provider.available && provider.has_api_key && (
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={testing === provider.id}
                              onClick={() => testProvider(provider.id)}
                            >
                              <TestTube className="h-3 w-3 mr-1" />
                              {testing === provider.id ? 'Testing...' : 'Test'}
                            </Button>
                          )}
                          
                          <Button
                            size="sm"
                            disabled={!provider.available || switching || provider.id === currentProvider}
                            onClick={() => switchProvider(provider.id)}
                          >
                            {switching ? 'Switching...' : 'Use This'}
                          </Button>
                        </div>
                      </div>
                      
                      {!provider.available && (
                        <Alert className="mt-2 border-yellow-500">
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            This provider is not available. {provider.type === 'api' ? 'API key required.' : 'Hardware not compatible.'}
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hardware" className="space-y-4">
          {hardwareInfo && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Cpu className="h-5 w-5 mr-2" />
                  Hardware Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>CPU Cores</Label>
                    <p className="text-lg font-semibold">{hardwareInfo.cpu_cores}</p>
                  </div>
                  <div>
                    <Label>CPU Frequency</Label>
                    <p className="text-lg font-semibold">{hardwareInfo.cpu_frequency_ghz || 'N/A'} GHz</p>
                  </div>
                  <div>
                    <Label>RAM</Label>
                    <p className="text-lg font-semibold">{hardwareInfo.ram_gb.toFixed(1)} GB</p>
                  </div>
                  <div>
                    <Label>GPU</Label>
                    <p className="text-lg font-semibold">
                      {hardwareInfo.has_gpu ? 'Available' : 'None'}
                    </p>
                  </div>
                  <div>
                    <Label>Optimization Level</Label>
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
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                API Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {providers.filter(p => p.type === 'api').map((provider) => (
                  <div key={provider.id} className="flex items-center justify-between p-3 border rounded">
                    <div>
                      <h4 className="font-medium">{provider.name}</h4>
                      <p className="text-sm text-gray-600">
                        {provider.has_api_key ? '✅ API key configured' : '❌ No API key'}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowApiKeyForm(provider.id)}
                    >
                      <Key className="h-3 w-3 mr-1" />
                      {provider.has_api_key ? 'Update' : 'Set'} API Key
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* API Key Form Modal */}
      {showApiKeyForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Set API Key for {showApiKeyForm}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="apiKey">API Key</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="Enter your API key"
                    value={apiKeys[showApiKeyForm] || ''}
                    onChange={(e) => setApiKeys(prev => ({
                      ...prev,
                      [showApiKeyForm]: e.target.value
                    }))}
                  />
                </div>
                <div className="flex space-x-2">
                  <Button
                    onClick={() => {
                      if (apiKeys[showApiKeyForm]) {
                        setApiKey(showApiKeyForm, apiKeys[showApiKeyForm]);
                      }
                    }}
                    disabled={!apiKeys[showApiKeyForm]}
                  >
                    Save
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowApiKeyForm(null)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default LLMSelector;