import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  Send, 
  Bot, 
  User, 
  Copy, 
  RefreshCw,
  Sparkles,
  Loader2
} from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: '1',
      type: 'assistant',
      content: 'Xin chào! Tôi là Robusta AI, trợ lý thông minh chuyên về thông tin khóa học và hỗ trợ các câu hỏi chung. Tôi có thể giúp gì cho bạn hôm nay?',
      timestamp: new Date().toISOString(),
      intent: 'greeting'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { isDark } = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: data.response,
        timestamp: data.timestamp,
        intent: data.intent
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: 'Xin lỗi, tôi gặp lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại.',
        timestamp: new Date().toISOString(),
        intent: 'error',
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: '1',
        type: 'assistant',
        content: 'Đã xóa lịch sử chat! Tôi có thể giúp gì cho bạn hôm nay?',
        timestamp: new Date().toISOString(),
        intent: 'greeting'
      }
    ]);
  };

  const getIntentColor = (intent) => {
    const colors = {
      'course_info': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
      'general_question': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      'greeting': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
      'policy_info': 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
      'other': 'bg-gray-100 text-gray-800 dark:bg-gray-700/20 dark:text-gray-400'
    };
    return colors[intent] || colors['other'];
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Robusta AI Assistant
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Powered by advanced AI models
            </p>
          </div>
        </div>
        
        <button
          onClick={clearChat}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          title="Clear chat"
        >
          <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-4xl ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
                {/* Avatar */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'user' 
                    ? 'bg-blue-500' 
                    : message.isError 
                      ? 'bg-red-500' 
                      : 'bg-gradient-to-r from-green-500 to-blue-500'
                }`}>
                  {message.type === 'user' ? (
                    <User className="w-5 h-5 text-white" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>

                {/* Message Content */}
                <div className={`flex-1 ${message.type === 'user' ? 'mr-3' : 'ml-3'}`}>
                  <div className={`p-4 rounded-2xl ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : message.isError
                        ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
                        : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                  }`}>
                    {/* Intent Badge for Assistant Messages */}
                    {message.type === 'assistant' && message.intent && (
                      <div className="mb-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getIntentColor(message.intent)}`}>
                          <Sparkles className="w-3 h-3 mr-1" />
                          {message.intent.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    )}

                    {/* Message Text */}
                    <div className={`prose prose-sm max-w-none ${
                      message.type === 'user' 
                        ? 'prose-invert' 
                        : isDark 
                          ? 'prose-invert' 
                          : ''
                    }`}>
                      <ReactMarkdown
                        components={{
                          code({ node, inline, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <div className="relative">
                                <div className="flex items-center justify-between bg-gray-800 text-gray-200 px-4 py-2 text-sm rounded-t-lg">
                                  <span>{match[1]}</span>
                                  <button
                                    onClick={() => copyToClipboard(String(children).replace(/\n$/, ''))}
                                    className="text-gray-400 hover:text-white transition-colors"
                                  >
                                    <Copy className="w-4 h-4" />
                                  </button>
                                </div>
                                <SyntaxHighlighter
                                  style={vscDarkPlus}
                                  language={match[1]}
                                  PreTag="div"
                                  className="rounded-t-none"
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              </div>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>

                    {/* Copy Button for Assistant Messages */}
                    {message.type === 'assistant' && (
                      <button
                        onClick={() => copyToClipboard(message.content)}
                        className="mt-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="Copy message"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {/* Timestamp */}
                  <div className={`mt-1 text-xs text-gray-500 ${
                    message.type === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading Indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 rounded-2xl">
                <div className="flex items-center space-x-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span className="text-gray-600 dark:text-gray-400">Thinking...</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-end space-x-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Nhập tin nhắn của bạn... (Enter để gửi, Shift+Enter để xuống dòng)"
              className="w-full px-4 py-3 pr-12 rounded-2xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              rows="1"
              style={{ minHeight: '52px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-2xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
          Robusta AI có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;
