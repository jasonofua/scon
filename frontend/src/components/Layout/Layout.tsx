import React, { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  currentPath?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title, currentPath }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-neutral-50">
      <Sidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        currentPath={currentPath}
      />
      
      <div className="lg:pl-72">
        <Header 
          onMenuClick={() => setSidebarOpen(true)} 
          title={title}
        />
        
        <main className="flex-1">
          <div className="h-[calc(100vh-4rem)]">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
