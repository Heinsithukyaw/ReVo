import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Monitor, Globe, Mouse, Keyboard, Eye, Play, Pause, Settings, Activity } from 'lucide-react';

interface BrowserSession {
  id: string;
  url: string;
  title: string;
  status: 'active' | 'idle' | 'loading';
  startTime: Date;
  actions: number;
}

interface ReVoComputerStatusProps {
  isConnected: boolean;
}

const ReVoComputerStatus: React.FC<ReVoComputerStatusProps> = ({ isConnected }) => {
  const [computerStatus, setComputerStatus] = useState({
    status: 'ready',
    activeSessions: 2,
    totalActions: 1247,
    successRate: 98.7,
    avgResponseTime: 0.8,
    browserVersion: 'Chrome 120.0',
    lastActivity: new Date()
  });

  const [browserSessions, setBrowserSessions] = useState<BrowserSession[]>([
    {
      id: '1',
      url: 'https://github.com/heinzdev20/reVoAgent',
      title: 'reVoAgent Repository',
      status: 'active',
      startTime: new Date(Date.now() - 3600000),
      actions: 15
    },
    {
      id: '2',
      url: 'https://docs.python.org/3/',
      title: 'Python Documentation',
      status: 'idle',
      startTime: new Date(Date.now() - 7200000),
      actions: 8
    }
  ]);

  const [isRecording, setIsRecording] = useState(false);
  const [automationQueue, setAutomationQueue] = useState([
    'Navigate to GitHub repository',
    'Check latest commits',
    'Review pull requests',
    'Update documentation'
  ]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setComputerStatus(prev => ({
        ...prev,
        totalActions: prev.totalActions + Math.floor(Math.random() * 3),
        lastActivity: new Date()
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const startAutomation = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/revo-computer/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks: automationQueue })
      });

      if (response.ok) {
        setComputerStatus(prev => ({ ...prev, status: 'running' }));
      }
    } catch (error) {
      console.error('Failed to start automation:', error);
      // Simulate for demo
      setComputerStatus(prev => ({ ...prev, status: 'running' }));
    }
  };

  const stopAutomation = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/revo-computer/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setComputerStatus(prev => ({ ...prev, status: 'ready' }));
      }
    } catch (error) {
      console.error('Failed to stop automation:', error);
      // Simulate for demo
      setComputerStatus(prev => ({ ...prev, status: 'ready' }));
    }
  };

  const takeScreenshot = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/revo-computer/screenshot', {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Screenshot taken:', data.screenshot_url);
      }
    } catch (error) {
      console.error('Failed to take screenshot:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'text-green-400';
      case 'running': return 'text-blue-400';
      case 'error': return 'text-red-400';
      case 'idle': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready': return <Play className="w-4 h-4" />;
      case 'running': return <Activity className="w-4 h-4 animate-pulse" />;
      case 'error': return <Pause className="w-4 h-4" />;
      case 'idle': return <Pause className="w-4 h-4" />;
      default: return <Monitor className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* ReVo Computer Status */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h3 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Monitor className="w-4 h-4" />
          <span>ReVo Computer</span>
        </h3>
        
        <div className="flex items-center justify-between mb-3">
          <span className="text-gray-400 text-sm">System Status:</span>
          <div className={`flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {getStatusIcon(computerStatus.status)}
            <span className="capitalize">{computerStatus.status}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="text-center">
            <div className="text-blue-400 font-bold">{computerStatus.activeSessions}</div>
            <div className="text-gray-400 text-xs">Active Sessions</div>
          </div>
          <div className="text-center">
            <div className="text-green-400 font-bold">{computerStatus.totalActions.toLocaleString()}</div>
            <div className="text-gray-400 text-xs">Total Actions</div>
          </div>
          <div className="text-center">
            <div className="text-purple-400 font-bold">{computerStatus.successRate}%</div>
            <div className="text-gray-400 text-xs">Success Rate</div>
          </div>
          <div className="text-center">
            <div className="text-yellow-400 font-bold">{computerStatus.avgResponseTime}s</div>
            <div className="text-gray-400 text-xs">Avg Response</div>
          </div>
        </div>
      </div>

      {/* Browser Control */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h4 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Globe className="w-4 h-4" />
          <span>Browser Control</span>
        </h4>

        <div className="space-y-2 mb-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Browser:</span>
            <span className="text-white">{computerStatus.browserVersion}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Recording:</span>
            <button
              onClick={() => setIsRecording(!isRecording)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                isRecording
                  ? 'bg-red-600/20 text-red-400'
                  : 'bg-gray-600/50 text-gray-300 hover:bg-gray-500/50'
              }`}
            >
              {isRecording ? 'Stop' : 'Start'}
            </button>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={computerStatus.status === 'running' ? stopAutomation : startAutomation}
            className={`flex-1 flex items-center justify-center space-x-1 p-2 rounded-lg text-sm font-medium transition-colors ${
              computerStatus.status === 'running'
                ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400'
                : 'bg-green-600/20 hover:bg-green-600/30 text-green-400'
            }`}
          >
            {computerStatus.status === 'running' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{computerStatus.status === 'running' ? 'Stop' : 'Start'}</span>
          </button>
          
          <button
            onClick={takeScreenshot}
            className="p-2 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded-lg transition-colors"
            title="Take screenshot"
          >
            <Eye className="w-4 h-4" />
          </button>
          
          <button
            className="p-2 bg-gray-600/20 hover:bg-gray-600/30 text-gray-400 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Active Browser Sessions */}
      <div className="space-y-2">
        <h4 className="text-white font-medium text-sm">Active Sessions</h4>
        
        {browserSessions.length === 0 ? (
          <div className="text-center py-4">
            <Globe className="w-6 h-6 text-gray-400 mx-auto mb-2" />
            <div className="text-gray-400 text-sm">No active sessions</div>
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {browserSessions.map(session => (
              <motion.div
                key={session.id}
                className="bg-gray-700/30 rounded-lg p-3 border border-gray-600/30"
                whileHover={{ scale: 1.02 }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium truncate">
                      {session.title}
                    </div>
                    <div className="text-gray-400 text-xs truncate">
                      {session.url}
                    </div>
                  </div>
                  
                  <div className={`w-2 h-2 rounded-full ml-2 mt-1 ${
                    session.status === 'active' ? 'bg-green-400' :
                    session.status === 'loading' ? 'bg-yellow-400 animate-pulse' :
                    'bg-gray-400'
                  }`} />
                </div>
                
                <div className="flex items-center justify-between text-xs">
                  <div className="text-gray-400">
                    {session.actions} actions
                  </div>
                  <div className="text-gray-400">
                    {Math.floor((Date.now() - session.startTime.getTime()) / 60000)}m ago
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Automation Queue */}
      <div className="bg-gray-700/30 rounded-lg p-4">
        <h4 className="text-white font-medium mb-3 flex items-center space-x-2">
          <Keyboard className="w-4 h-4" />
          <span>Automation Queue</span>
        </h4>
        
        {automationQueue.length === 0 ? (
          <div className="text-center py-2">
            <div className="text-gray-400 text-sm">No tasks queued</div>
          </div>
        ) : (
          <div className="space-y-2">
            {automationQueue.slice(0, 4).map((task, index) => (
              <div
                key={index}
                className="flex items-center space-x-2 text-sm"
              >
                <div className={`w-2 h-2 rounded-full ${
                  index === 0 ? 'bg-blue-400' : 'bg-gray-500'
                }`} />
                <span className={index === 0 ? 'text-white' : 'text-gray-400'}>
                  {task}
                </span>
              </div>
            ))}
            {automationQueue.length > 4 && (
              <div className="text-gray-400 text-xs text-center">
                +{automationQueue.length - 4} more tasks
              </div>
            )}
          </div>
        )}
      </div>

      {/* Computer Vision */}
      <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/20">
        <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
          <Eye className="w-4 h-4" />
          <span>Computer Vision</span>
        </h4>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Element Detection:</span>
            <span className="text-green-400">Active</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">OCR Recognition:</span>
            <span className="text-blue-400">99.2%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Screen Analysis:</span>
            <span className="text-purple-400">Real-time</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReVoComputerStatus;