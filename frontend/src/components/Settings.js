import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { 
  User, 
  Bell, 
  Shield, 
  Database, 
  Cpu, 
  Save,
  RefreshCw,
  Eye,
  EyeOff,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';

const Settings = () => {
  const { toggleTheme, isDark } = useTheme();
  const [settings, setSettings] = useState({
    // User preferences
    username: '',
    email: '',
    notifications: true,
    autoSave: true,
    
    // AI Settings
    model: 'groq',
    maxTokens: 2048,
    temperature: 0.7,
    
    // API Keys (masked for security)
    openaiKey: '',
    groqKey: '',
    geminiKey: '',
    
    // System settings
    logLevel: 'info',
    cacheEnabled: true,
    vectorDbUrl: '',
  });

  const [showApiKeys, setShowApiKeys] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load settings from localStorage or API
    const savedSettings = localStorage.getItem('robustaSettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const handleInputChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      // Save to localStorage (in production, you'd save to your backend)
      localStorage.setItem('robustaSettings', JSON.stringify(settings));
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const resetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      setSettings({
        username: '',
        email: '',
        notifications: true,
        autoSave: true,
        model: 'groq',
        maxTokens: 2048,
        temperature: 0.7,
        openaiKey: '',
        groqKey: '',
        geminiKey: '',
        logLevel: 'info',
        cacheEnabled: true,
        vectorDbUrl: '',
      });
    }
  };

  const SettingSection = ({ icon: Icon, title, children }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
          <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );

  const SettingField = ({ label, description, children }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{description}</p>
      )}
      {children}
    </div>
  );

  return (
    <div className="h-full bg-gray-50 dark:bg-gray-900 p-6 overflow-y-auto scrollbar-thin">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Configure your Robusta AI assistant preferences and system settings.
          </p>
        </div>

        {/* Save/Reset Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <button
              onClick={saveSettings}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : saved ? (
                <Save className="w-4 h-4 mr-2" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Settings'}
            </button>
            
            <button
              onClick={resetSettings}
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Reset to Default
            </button>
          </div>
        </div>

        <div className="space-y-8">
          {/* User Profile */}
          <SettingSection icon={User} title="User Profile">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField label="Username" description="Your display name in the chat">
                <input
                  type="text"
                  value={settings.username}
                  onChange={(e) => handleInputChange('username', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your username"
                />
              </SettingField>
              
              <SettingField label="Email" description="For notifications and account recovery">
                <input
                  type="email"
                  value={settings.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter your email"
                />
              </SettingField>
            </div>
          </SettingSection>

          {/* Preferences */}
          <SettingSection icon={Bell} title="Preferences">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Notifications
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Receive notifications for important updates
                  </p>
                </div>
                <button
                  onClick={() => handleInputChange('notifications', !settings.notifications)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.notifications ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Auto-save conversations
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Automatically save chat history
                  </p>
                </div>
                <button
                  onClick={() => handleInputChange('autoSave', !settings.autoSave)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.autoSave ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Dark Theme
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Use dark mode interface
                  </p>
                </div>
                <button
                  onClick={toggleTheme}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isDark ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isDark ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </SettingSection>

          {/* AI Model Settings */}
          <SettingSection icon={Cpu} title="AI Model Configuration">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField label="Primary Model" description="Choose the default AI model">
                <select
                  value={settings.model}
                  onChange={(e) => handleInputChange('model', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="groq">Groq (Fast)</option>
                  <option value="openai">OpenAI GPT-4</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </SettingField>
              
              <SettingField label="Max Tokens" description="Maximum response length">
                <input
                  type="number"
                  value={settings.maxTokens}
                  onChange={(e) => handleInputChange('maxTokens', parseInt(e.target.value))}
                  min="256"
                  max="4096"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </SettingField>
            </div>
            
            <SettingField label="Temperature" description="Controls randomness (0.0 = focused, 1.0 = creative)">
              <div className="flex items-center space-x-4">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-12">
                  {settings.temperature}
                </span>
              </div>
            </SettingField>
          </SettingSection>

          {/* API Keys */}
          <SettingSection icon={Shield} title="API Configuration">
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    Security Notice
                  </h4>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                    API keys are encrypted and stored securely. Never share your keys with others.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-4">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Show API Keys
              </label>
              <button
                onClick={() => setShowApiKeys(!showApiKeys)}
                className="inline-flex items-center space-x-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
              >
                {showApiKeys ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                <span>{showApiKeys ? 'Hide' : 'Show'}</span>
              </button>
            </div>

            <div className="space-y-4">
              <SettingField label="OpenAI API Key" description="For GPT-4 and other OpenAI models">
                <input
                  type={showApiKeys ? "text" : "password"}
                  value={settings.openaiKey}
                  onChange={(e) => handleInputChange('openaiKey', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={showApiKeys ? "sk-..." : "••••••••••••••••"}
                />
              </SettingField>
              
              <SettingField label="Groq API Key" description="For fast inference with Groq models">
                <input
                  type={showApiKeys ? "text" : "password"}
                  value={settings.groqKey}
                  onChange={(e) => handleInputChange('groqKey', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={showApiKeys ? "gsk_..." : "••••••••••••••••"}
                />
              </SettingField>
              
              <SettingField label="Google Gemini API Key" description="For Google's Gemini models">
                <input
                  type={showApiKeys ? "text" : "password"}
                  value={settings.geminiKey}
                  onChange={(e) => handleInputChange('geminiKey', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={showApiKeys ? "AIza..." : "••••••••••••••••"}
                />
              </SettingField>
            </div>
          </SettingSection>

          {/* System Settings */}
          <SettingSection icon={Database} title="System Configuration">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SettingField label="Log Level" description="System logging verbosity">
                <select
                  value={settings.logLevel}
                  onChange={(e) => handleInputChange('logLevel', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="debug">Debug</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </SettingField>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Enable Caching
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Cache responses for better performance
                  </p>
                </div>
                <button
                  onClick={() => handleInputChange('cacheEnabled', !settings.cacheEnabled)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    settings.cacheEnabled ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      settings.cacheEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
            
            <SettingField label="Vector Database URL" description="Qdrant Cloud endpoint for document search">
              <div className="flex space-x-2">
                <input
                  type="url"
                  value={settings.vectorDbUrl}
                  onChange={(e) => handleInputChange('vectorDbUrl', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://your-cluster.qdrant.io"
                />
                <button
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  title="Test connection"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </SettingField>
          </SettingSection>
        </div>
      </div>
    </div>
  );
};

export default Settings;
