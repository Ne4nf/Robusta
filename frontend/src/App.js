import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import UploadInterface from './components/UploadInterface';
import Settings from './components/Settings';
import { ThemeProvider } from './hooks/useTheme';
import './styles/globals.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState('chat');

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Close sidebar on mobile when route changes
  useEffect(() => {
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, [currentPage]);

  return (
    <ThemeProvider>
      <Router>
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          {/* Sidebar */}
          <AnimatePresence>
            {(sidebarOpen || window.innerWidth >= 768) && (
              <motion.div
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                exit={{ x: -300 }}
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
                className="fixed inset-y-0 left-0 z-50 w-64 md:relative md:translate-x-0"
              >
                <Sidebar 
                  onNavigate={setCurrentPage}
                  currentPage={currentPage}
                  onClose={() => setSidebarOpen(false)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Overlay for mobile */}
          {sidebarOpen && (
            <div 
              className="fixed inset-0 z-40 bg-black bg-opacity-50 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Main content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header */}
            <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 px-4 py-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={toggleSidebar}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors md:hidden"
                    aria-label="Toggle sidebar"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                  
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm">R</span>
                    </div>
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                      Robusta AI
                    </h1>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="hidden sm:flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span>Online</span>
                  </div>
                </div>
              </div>
            </header>

            {/* Main content area */}
            <main className="flex-1 overflow-hidden">
              <Routes>
                <Route 
                  path="/" 
                  element={
                    <ChatInterface />
                  } 
                />
                <Route 
                  path="/upload" 
                  element={
                    <UploadInterface />
                  } 
                />
                <Route 
                  path="/settings" 
                  element={
                    <Settings />
                  } 
                />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
