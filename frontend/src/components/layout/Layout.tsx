import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Navigation from './Navigation';
import Footer from './Footer';

const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      <Header />
      <Navigation />
      <main className="flex-1 container mx-auto">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;