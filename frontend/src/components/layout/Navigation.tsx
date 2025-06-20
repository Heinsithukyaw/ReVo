import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Three-Engine', icon: '🧠' },
    { to: '/agents', label: 'Agents', icon: '🤖' },
    { to: '/chat', label: 'Chat', icon: '💬' },
    { to: '/analytics', label: 'Analytics', icon: '📊' }
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="container mx-auto">
        <div className="flex space-x-0">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `px-6 py-4 text-sm font-medium transition-all duration-200 border-b-2 ${
                  isActive
                    ? 'text-blue-400 border-blue-400 bg-gray-700/50'
                    : 'text-gray-300 border-transparent hover:text-white hover:border-gray-500'
                }`
              }
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;