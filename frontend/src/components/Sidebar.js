import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../hooks/useTheme';
import { 
  MessageCircle, 
  Upload, 
  Settings, 
  Sun, 
  Moon, 
  Plus,
  History,
  FileText,
  Zap
} from 'lucide-react';

const Sidebar = ({ onNavigate, currentPage, onClose }) => {
  const { toggleTheme, isDark } = useTheme();

  const menuItems = [
    {
      id: 'chat',
      label: 'New Chat',
      icon: MessageCircle,
      path: '/'
    },
    {
      id: 'upload',
      label: 'Upload Courses',
      icon: Upload,
      path: '/upload'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      path: '/settings'
    }
  ];

  const recentChats = [
    { id: '1', title: 'Cloud Computing Fundamentals', timestamp: '2 hours ago' },
    { id: '2', title: 'Ansible Automation Training', timestamp: '1 day ago' },
    { id: '3', title: 'Mobile App Development', timestamp: '3 days ago' },
  ];

  const handleNavigation = (item) => {
    onNavigate(item.id);
    if (window.innerWidth < 768) {
      onClose();
    }
  };

  return (
    <motion.div 
      className="h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col"
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      transition={{ type: "spring", damping: 30, stiffness: 300 }}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="font-semibold text-gray-900 dark:text-white">Robusta AI</span>
          </div>
          
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 md:hidden"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button 
          onClick={() => handleNavigation({ id: 'chat' })}
          className="w-full flex items-center space-x-3 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg"
        >
          <Plus className="w-5 h-5" />
          <span className="font-medium">New Chat</span>
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-4 space-y-2">
        {menuItems.slice(1).map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => handleNavigation(item)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive 
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-l-4 border-blue-500' 
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      {/* Recent Chats */}
      <div className="px-4 pb-4">
        <div className="mb-3">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center space-x-2">
            <History className="w-4 h-4" />
            <span>Recent Chats</span>
          </h3>
        </div>
        
        <div className="space-y-1">
          {recentChats.map((chat) => (
            <motion.button
              key={chat.id}
              className="w-full text-left p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
              whileHover={{ x: 4 }}
            >
              <div className="flex items-start space-x-3">
                <FileText className="w-4 h-4 text-gray-400 mt-0.5 group-hover:text-blue-500 transition-colors" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {chat.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {chat.timestamp}
                  </p>
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        {/* Theme Toggle */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-gray-600 dark:text-gray-400">Theme</span>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle theme"
          >
            {isDark ? (
              <Sun className="w-5 h-5 text-yellow-500" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Status */}
        <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-1">
            <Zap className="w-3 h-3 text-green-500" />
            <span>AI Online</span>
          </div>
          <span>•</span>
          <span>v2.0.0</span>
        </div>
      </div>
    </motion.div>
  );
};

export default Sidebar;
