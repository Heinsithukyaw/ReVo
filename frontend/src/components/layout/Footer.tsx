import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-white p-4 mt-auto">
      <div className="container mx-auto flex justify-between items-center">
        {/* System Status Bar */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-300">System Online</span>
          </div>
        </div>
        
        {/* Quick Action Shortcuts */}
        <div className="flex items-center space-x-4">
          <button className="text-sm text-gray-300 hover:text-white transition-colors">
            Quick Actions
          </button>
        </div>
        
        {/* Help & Support Links */}
        <div className="flex items-center space-x-4">
          <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
            Help
          </a>
          <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
            Support
          </a>
        </div>
        
        {/* Version & Update Information */}
        <div className="text-sm text-gray-400">
          v1.0.0
        </div>
      </div>
    </footer>
  );
};

export default Footer;