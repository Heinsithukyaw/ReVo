import React, { useState } from 'react';
import { 
  Menu,
  Search,
  Bell,
  Settings,
  User,
  Sun,
  Moon,
  Wifi,
  WifiOff,
  Activity,
  Sparkles,
  Zap,
  Shield
} from 'lucide-react';

interface GlassmorphismNavbarProps {
  isConnected: boolean;
  systemStatus: any;
  onThemeToggle: () => void;
  currentTheme: string;
}

const GlassmorphismNavbar: React.FC<GlassmorphismNavbarProps> = ({
  isConnected,
  systemStatus,
  onThemeToggle,
  currentTheme
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const notifications = [
    {
      id: 1,
      type: 'success',
      title: 'Code Generator Complete',
      message: 'Successfully generated React component',
      timestamp: '2 minutes ago',
      icon: Sparkles
    },
    {
      id: 2,
      type: 'info',
      title: 'System Update',
      message: 'AI models updated to latest version',
      timestamp: '15 minutes ago',
      icon: Zap
    },
    {
      id: 3,
      type: 'warning',
      title: 'Security Scan',
      message: 'Found 2 potential vulnerabilities',
      timestamp: '1 hour ago',
      icon: Shield
    }
  ];

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-orange-400';
      case 'error': return 'text-red-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <nav className="glass-card border-b border-white/10 px-6 py-4 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        
        {/* Left Section - Logo & Status */}
        <div className="flex items-center gap-6">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-400 to-purple-600 shadow-lg">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div className="hidden md:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                reVoAgent
              </h1>
              <p className="text-xs text-white/60">Glassmorphism Edition</p>
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg glass-subtle ${
              isConnected ? 'ring-1 ring-green-400/30' : 'ring-1 ring-red-400/30'
            }`}>
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-400" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-400" />
              )}
              <span className={`text-sm font-medium ${
                isConnected ? 'text-green-400' : 'text-red-400'
              }`}>
                {isConnected ? 'Live' : 'Offline'}
              </span>
            </div>

            {/* System Status Indicator */}
            {systemStatus && (
              <div className="hidden lg:flex items-center gap-4 px-3 py-1.5 glass-subtle rounded-lg">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  <span className="text-xs text-white/70">
                    CPU: {systemStatus.performance_metrics?.cpu_usage || 24}%
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  <span className="text-xs text-white/70">
                    Memory: {systemStatus.performance_metrics?.memory_usage || 67}%
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                  <span className="text-xs text-white/70">
                    Agents: {systemStatus.active_agents || 3}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
            <input
              type="text"
              placeholder="Search agents, tasks, or documentation..."
              className="glass-input pl-10 w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <div className="absolute top-full left-0 right-0 mt-2 glass-card border border-white/20 rounded-lg shadow-xl z-50">
                <div className="p-4">
                  <div className="text-white/70 text-sm mb-2">Quick Results</div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 p-2 hover:bg-white/10 rounded-lg cursor-pointer">
                      <Sparkles className="w-4 h-4 text-blue-400" />
                      <span className="text-white">Code Generator Agent</span>
                    </div>
                    <div className="flex items-center gap-3 p-2 hover:bg-white/10 rounded-lg cursor-pointer">
                      <Shield className="w-4 h-4 text-orange-400" />
                      <span className="text-white">Security Documentation</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-3">
          
          {/* Mobile Search */}
          <button className="md:hidden glass-button p-2">
            <Search className="w-4 h-4" />
          </button>

          {/* Theme Toggle */}
          <button 
            onClick={onThemeToggle}
            className="glass-button p-2 relative group"
            title="Toggle theme"
          >
            {currentTheme === 'dark' ? (
              <Sun className="w-4 h-4 transition-transform group-hover:rotate-12" />
            ) : (
              <Moon className="w-4 h-4 transition-transform group-hover:-rotate-12" />
            )}
          </button>

          {/* Notifications */}
          <div className="relative">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="glass-button p-2 relative"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              {notifications.length > 0 && (
                <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-xs text-white font-medium">{notifications.length}</span>
                </div>
              )}
            </button>

            {showNotifications && (
              <div className="absolute top-full right-0 mt-2 w-80 glass-card border border-white/20 rounded-xl shadow-xl z-50">
                <div className="p-4 border-b border-white/10">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-white">Notifications</h3>
                    <button className="text-white/60 hover:text-white text-sm">
                      Mark all read
                    </button>
                  </div>
                </div>
                
                <div className="max-h-80 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="p-4 border-b border-white/5 hover:bg-white/5 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg glass-subtle ${getNotificationColor(notification.type)}`}>
                          <notification.icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-white text-sm">{notification.title}</h4>
                          <p className="text-white/70 text-sm mt-1 line-clamp-2">{notification.message}</p>
                          <p className="text-white/50 text-xs mt-2">{notification.timestamp}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="p-3 border-t border-white/10">
                  <button className="w-full text-center text-white/70 hover:text-white text-sm transition-colors">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Settings */}
          <button className="glass-button p-2" title="Settings">
            <Settings className="w-4 h-4" />
          </button>

          {/* User Menu */}
          <div className="relative">
            <button 
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 glass-button px-3 py-2"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="hidden md:block text-white font-medium">Admin</span>
            </button>

            {showUserMenu && (
              <div className="absolute top-full right-0 mt-2 w-56 glass-card border border-white/20 rounded-xl shadow-xl z-50">
                <div className="p-4 border-b border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">Admin User</h4>
                      <p className="text-white/60 text-sm">admin@revoagent.com</p>
                    </div>
                  </div>
                </div>
                
                <div className="p-2">
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-white/10 rounded-lg transition-colors">
                    <User className="w-4 h-4 text-white/70" />
                    <span className="text-white">Profile Settings</span>
                  </button>
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-white/10 rounded-lg transition-colors">
                    <Settings className="w-4 h-4 text-white/70" />
                    <span className="text-white">Preferences</span>
                  </button>
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-white/10 rounded-lg transition-colors">
                    <Activity className="w-4 h-4 text-white/70" />
                    <span className="text-white">Activity Log</span>
                  </button>
                </div>
                
                <div className="p-2 border-t border-white/10">
                  <button className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-white/10 rounded-lg transition-colors text-red-400">
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Search Bar */}
      <div className="md:hidden mt-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
          <input
            type="text"
            placeholder="Search..."
            className="glass-input pl-10 w-full"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Glassmorphism glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
    </nav>
  );
};

export default GlassmorphismNavbar;