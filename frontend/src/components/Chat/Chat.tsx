import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ChatHistory from './ChatHistory';
import type { Message, QuickOption, ChatResponse } from '../../types';
import { ApiService, generateSessionId } from '../../services/api';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => generateSessionId());
  const [showHistory, setShowHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: `# Welcome to SCONIA! 🏛️

I'm your Supreme Court of Nigeria Information Assistant. I can help you with:

- **Constitutional Law** - Understanding fundamental rights, constitutional provisions, and interpretations
- **Supreme Court Procedures** - Filing appeals, court processes, and requirements  
- **Case Law** - Finding relevant precedents and landmark decisions
- **Legal Research** - Searching through legal documents and statutes

How can I assist you today?`,
      timestamp: new Date(),
      quickOptions: [
        { text: "Fundamental Rights", action: "query", category: "constitution" },
        { text: "Appeal Process", action: "query", category: "procedure" },
        { text: "Search Cases", action: "search", category: "cases" },
        { text: "Court Information", action: "info", category: "court" }
      ]
    };
    setMessages([welcomeMessage]);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call API
      const response: ChatResponse = await ApiService.sendMessage({
        query: content,
        session_id: sessionId,
        user_type: 'citizen'
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
        quickOptions: response.quick_options,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Show success toast with response time
      toast.success(`Response received in ${response.response_time.toFixed(1)}s`, {
        duration: 2000,
      });

    } catch (error: any) {
      console.error('Chat error:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `I apologize, but I encountered an error while processing your request: ${error.message}. Please try again or rephrase your question.`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
      
      toast.error('Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickOptionClick = (option: QuickOption) => {
    let query = '';
    
    switch (option.text) {
      case 'Fundamental Rights':
        query = 'What are the fundamental rights guaranteed by the Nigerian Constitution?';
        break;
      case 'Appeal Process':
        query = 'How do I file an appeal to the Supreme Court of Nigeria?';
        break;
      case 'Search Cases':
        query = 'Show me landmark constitutional cases from the Supreme Court';
        break;
      case 'Court Information':
        query = 'Tell me about the Supreme Court of Nigeria structure and jurisdiction';
        break;
      default:
        query = option.text;
    }
    
    handleSendMessage(query);
  };

  const handleFeedback = async (_messageId: string, isPositive: boolean) => {
    try {
      await ApiService.submitFeedback(
        sessionId,
        undefined, // query_id
        isPositive ? 5 : 1, // rating
        undefined, // feedback_text
        isPositive ? 'positive' : 'negative'
      );

      toast.success('Thank you for your feedback!', { duration: 2000 });
    } catch (error) {
      console.error('Feedback error:', error);
      toast.error('Failed to submit feedback');
    }
  };

  const handleSessionSelect = async (newSessionId: string) => {
    try {
      setSessionId(newSessionId);
      // Load chat history for the selected session
      const history = await ApiService.getChatHistory(newSessionId);
      // TODO: Convert history to messages format
      setMessages(history.messages || []);
    } catch (error: any) {
      console.error('Failed to load session:', error);
      toast.error('Failed to load conversation');
    }
  };

  const handleNewChat = () => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    setMessages([]);
    // Re-add welcome message
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'assistant',
      content: `# Welcome to SCONIA! 🏛️

I'm your Supreme Court of Nigeria Information Assistant. I can help you with:

- **Constitutional Law** - Understanding fundamental rights, constitutional provisions, and interpretations
- **Supreme Court Procedures** - Filing appeals, court processes, and requirements
- **Case Law** - Finding relevant precedents and landmark decisions
- **Legal Research** - Searching through legal documents and statutes

How can I assist you today?`,
      timestamp: new Date(),
      quickOptions: [
        { text: "Fundamental Rights", action: "query", category: "constitution" },
        { text: "Appeal Process", action: "query", category: "procedure" },
        { text: "Search Cases", action: "search", category: "cases" },
        { text: "Court Information", action: "info", category: "court" }
      ]
    };
    setMessages([welcomeMessage]);
  };

  return (
    <div className="flex h-full bg-neutral-50">
      {/* Chat History Sidebar */}
      <div className={`${showHistory ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden`}>
        <ChatHistory
          currentSessionId={sessionId}
          onSessionSelect={handleSessionSelect}
          onNewChat={handleNewChat}
          className="h-full"
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="flex-shrink-0 bg-white border-b border-neutral-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="p-2 hover:bg-neutral-100 rounded-lg transition-colors lg:hidden"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Legal Assistant Chat</h2>
                <p className="text-sm text-neutral-600">
                  Ask questions about Nigerian constitutional law and Supreme Court procedures
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                <div className="h-2 w-2 bg-accent-500 rounded-full"></div>
                <span className="text-sm text-neutral-600">Online</span>
              </div>
            </div>
          </div>
        </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onQuickOptionClick={handleQuickOptionClick}
              onFeedback={handleFeedback}
            />
          ))}
          
          {/* Loading message */}
          {isLoading && (
            <div className="flex space-x-3 p-4">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">S</span>
                </div>
              </div>
              <div className="flex-1 max-w-3xl">
                <div className="bg-white border border-neutral-200 rounded-2xl px-4 py-3 shadow-soft">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <div className="flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isLoading}
            isLoading={isLoading}
          />
        </div>
      </div>
      </div>
    </div>
  );
};

export default Chat;
