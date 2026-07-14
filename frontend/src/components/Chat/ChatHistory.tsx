import React, { useState, useEffect } from 'react';
import {
  ChatBubbleLeftRightIcon,
  ClockIcon,
  TrashIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { ApiService, formatTimestamp } from '../../services/api';
import { toast } from 'react-hot-toast';

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messageCount: number;
  isActive?: boolean;
}

interface ChatHistoryProps {
  currentSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  className?: string;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  className = '',
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(true);

  // Load chat sessions on component mount
  useEffect(() => {
    loadChatSessions();
  }, []);

  const loadChatSessions = async () => {
    setIsLoading(true);
    try {
      const response = await ApiService.getChatSessions();
      setSessions(response.sessions || []);
    } catch (error: any) {
      console.error('Failed to load chat sessions:', error);
      toast.error('Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      // TODO: Implement delete session API
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      toast.success('Conversation deleted');
      
      // If deleting current session, start new chat
      if (sessionId === currentSessionId) {
        onNewChat();
      }
    } catch (error: any) {
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete conversation');
    }
  };

  // const generateSessionTitle = (message: string): string => {
  //   // Generate a title from the first message
  //   const words = message.split(' ').slice(0, 6);
  //   return words.join(' ') + (message.split(' ').length > 6 ? '...' : '');
  // };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Mock sessions for demo (remove when API is ready)
  const mockSessions: ChatSession[] = [
    {
      id: 'session_1',
      title: 'Fundamental Rights in Nigeria',
      lastMessage: 'What are the fundamental rights guaranteed by the Nigerian Constitution?',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      messageCount: 8,
      isActive: currentSessionId === 'session_1',
    },
    {
      id: 'session_2',
      title: 'Supreme Court Procedures',
      lastMessage: 'How do I file an appeal to the Supreme Court?',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      messageCount: 12,
      isActive: currentSessionId === 'session_2',
    },
    {
      id: 'session_3',
      title: 'Constitutional Interpretation',
      lastMessage: 'Can you explain the doctrine of separation of powers?',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      messageCount: 6,
      isActive: currentSessionId === 'session_3',
    },
  ];

  const displaySessions = filteredSessions.length > 0 ? filteredSessions : mockSessions;

  return (
    <div className={clsx('bg-white border-r border-neutral-200 flex flex-col', className)}>
      {/* Header */}
      <div className="p-4 border-b border-neutral-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-neutral-900">Chat History</h2>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-neutral-100 rounded transition-colors lg:hidden"
          >
            {isExpanded ? <XMarkIcon className="h-5 w-5" /> : <ChatBubbleLeftRightIcon className="h-5 w-5" />}
          </button>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="w-full btn-primary flex items-center justify-center space-x-2 mb-4"
        >
          <PlusIcon className="h-4 w-4" />
          <span>New Chat</span>
        </button>

        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className={clsx('flex-1 overflow-y-auto custom-scrollbar', !isExpanded && 'hidden lg:block')}>
        {isLoading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto"></div>
            <p className="text-sm text-neutral-500 mt-2">Loading conversations...</p>
          </div>
        ) : displaySessions.length === 0 ? (
          <div className="p-4 text-center">
            <ChatBubbleLeftRightIcon className="h-8 w-8 text-neutral-400 mx-auto mb-2" />
            <p className="text-sm text-neutral-500">No conversations found</p>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {displaySessions.map((session) => (
              <div
                key={session.id}
                onClick={() => onSessionSelect(session.id)}
                className={clsx(
                  'group p-3 rounded-lg cursor-pointer transition-colors duration-200',
                  session.id === currentSessionId
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-neutral-50 border border-transparent'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className={clsx(
                      'text-sm font-medium truncate',
                      session.id === currentSessionId ? 'text-primary-900' : 'text-neutral-900'
                    )}>
                      {session.title}
                    </h3>
                    <p className="text-xs text-neutral-500 mt-1 line-clamp-2">
                      {session.lastMessage}
                    </p>
                    <div className="flex items-center space-x-2 mt-2">
                      <ClockIcon className="h-3 w-3 text-neutral-400" />
                      <span className="text-xs text-neutral-400">
                        {formatTimestamp(session.timestamp)}
                      </span>
                      <span className="text-xs text-neutral-400">
                        • {session.messageCount} messages
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => deleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all duration-200"
                  >
                    <TrashIcon className="h-4 w-4 text-red-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-neutral-200">
        <div className="text-xs text-neutral-500 text-center">
          {displaySessions.length} conversation{displaySessions.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
};

export default ChatHistory;
