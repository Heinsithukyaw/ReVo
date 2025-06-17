import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Import glassmorphism components
import GlassmorphismDashboard from './components/glassmorphism/GlassmorphismDashboard';
import GlassmorphismNavbar from './components/glassmorphism/GlassmorphismNavbar';
import GlassmorphismSidebar from './components/glassmorphism/GlassmorphismSidebar';
import AllAgentsInterface from './components/agents/AllAgentsInterface';
import AgentExecutionPanel from './components/agents/AgentExecutionPanel';
import SystemMonitoring from './components/system/SystemMonitoring';
import CostAnalytics from './components/analytics/CostAnalytics';
import EnterpriseSettings from './components/enterprise/EnterpriseSettings';

// Import hooks and services
import { useWebSocket } from './hooks/useWebSocket';
import { useSystemStatus } from './hooks/useSystemStatus';
import { useGlassmorphismTheme } from './hooks/useGlassmorphismTheme';

// Import glassmorphism styles
import './styles/glassmorphism.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentPage, setCurrentPage] = useState('dashboard');
  
  // Initialize glassmorphism theme
  const { theme, toggleTheme } = useGlassmorphismTheme();
  
  // WebSocket connection for real-time updates
  const { 
    isConnected, 
    dashboardData, 
    systemMetrics, 
    agentUpdates 
  } = useWebSocket('ws://localhost:8000/ws/glassmorphism');
  
  // System status monitoring
  const { systemStatus, isLoading: statusLoading } = useSystemStatus();
  
  useEffect(() => {
    // Apply glassmorphism theme to document
    document.documentElement.setAttribute('data-theme', theme);
    document.body.className = `glassmorphism-theme-${theme}`;
  }, [theme]);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <GlassmorphismDashboard
            dashboardData={dashboardData}
            systemMetrics={systemMetrics}
            isConnected={isConnected}
          />
        );
      case 'agents':
        return (
          <AllAgentsInterface
            agentUpdates={agentUpdates}
            onAgentSelect={(agentType) => setCurrentPage(`agent-${agentType}`)}
          />
        );
      case 'monitoring':
        return (
          <SystemMonitoring
            systemStatus={systemStatus}
            systemMetrics={systemMetrics}
            isLoading={statusLoading}
          />
        );
      case 'analytics':
        return (
          <CostAnalytics
            dashboardData={dashboardData}
            systemMetrics={systemMetrics}
          />
        );
      case 'enterprise':
        return (
          <EnterpriseSettings
            systemStatus={systemStatus}
          />
        );
      default:
        // Handle agent-specific pages
        if (currentPage.startsWith('agent-')) {
          const agentType = currentPage.replace('agent-', '');
          return (
            <AgentExecutionPanel
              agentType={agentType}
              onBack={() => setCurrentPage('agents')}
            />
          );
        }
        return <Navigate to="/dashboard" replace />;
    }
  };

  return (
    <div className="glassmorphism-app">
      {/* Glassmorphism Background */}
      <div className="glassmorphism-background">
        <div className="glassmorphism-gradient-1"></div>
        <div className="glassmorphism-gradient-2"></div>
        <div className="glassmorphism-gradient-3"></div>
        <div className="glassmorphism-particles"></div>
      </div>

      {/* Main App Content */}
      <div className="glassmorphism-container">
        {/* Enhanced Navbar */}
        <GlassmorphismNavbar
          isConnected={isConnected}
          systemStatus={systemStatus}
          onThemeToggle={toggleTheme}
          currentTheme={theme}
        />

        <div className="glassmorphism-main">
          {/* Enhanced Sidebar */}
          <GlassmorphismSidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
            systemMetrics={systemMetrics}
          />

          {/* Main Content Area */}
          <main className={`glassmorphism-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
            <div className="glassmorphism-page">
              {renderCurrentPage()}
            </div>
          </main>
        </div>

        {/* Status Indicator */}
        <div className="glassmorphism-status-indicator">
          <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></div>
          <span className="status-text">
            {isConnected ? 'Live Connected' : 'Reconnecting...'}
          </span>
        </div>
      </div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          className: 'glassmorphism-toast',
          duration: 4000,
          style: {
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '16px',
            color: '#fff',
            fontSize: '14px',
          },
        }}
      />
    </div>
  );
}

export default App;