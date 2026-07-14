import React, { useState } from 'react';
import {
  UserIcon,
  DocumentTextIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ClipboardDocumentIcon,
  ShareIcon
} from '@heroicons/react/24/outline';
import {
  HandThumbUpIcon as HandThumbUpSolidIcon,
  HandThumbDownIcon as HandThumbDownSolidIcon
} from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import type { Message, QuickOption } from '../../types';
import { formatTimestamp } from '../../services/api';

interface ChatMessageProps {
  message: Message;
  onQuickOptionClick?: (option: QuickOption) => void;
  onFeedback?: (messageId: string, isPositive: boolean) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  onQuickOptionClick,
  onFeedback 
}) => {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleFeedback = (isPositive: boolean) => {
    const newFeedback = isPositive ? 'positive' : 'negative';
    setFeedback(newFeedback);
    onFeedback?.(message.id, isPositive);
  };

  const isUser = message.type === 'user';

  return (
    <div className={clsx(
      'flex space-x-3 p-4',
      isUser ? 'justify-end' : 'justify-start'
    )}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="h-8 w-8 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">S</span>
          </div>
        </div>
      )}

      <div className={clsx(
        'flex-1 max-w-3xl',
        isUser ? 'flex justify-end' : ''
      )}>
        <div className={clsx(
          'rounded-2xl px-4 py-3 shadow-soft',
          isUser 
            ? 'bg-primary-600 text-white ml-12' 
            : 'bg-white border border-neutral-200'
        )}>
          {/* Message content */}
          <div className={clsx(
            'prose prose-sm max-w-none',
            isUser ? 'prose-invert' : 'prose-neutral'
          )}>
            {isUser ? (
              <p className="mb-0">{message.content}</p>
            ) : (
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="mb-2 last:mb-0 pl-4">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-2 last:mb-0 pl-4">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-neutral-200">
              <h4 className="text-sm font-medium text-neutral-700 mb-2 flex items-center">
                <DocumentTextIcon className="h-4 w-4 mr-1" />
                Sources ({message.sources.length})
              </h4>
              <div className="space-y-2">
                {message.sources.slice(0, 3).map((source, index) => (
                  <div 
                    key={index}
                    className="text-xs bg-neutral-50 rounded-lg p-2 border border-neutral-200"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-neutral-700">{source.title}</span>
                      <span className="text-neutral-500">
                        {(source.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-neutral-600 line-clamp-2">
                      {source.content_snippet}
                    </p>
                    <div className="flex items-center mt-1 text-neutral-500">
                      <span className="capitalize">{source.document_type}</span>
                      {source.url && (
                        <a 
                          href={source.url} 
                          className="ml-2 text-primary-600 hover:text-primary-700"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View Document
                        </a>
                      )}
                    </div>
                  </div>
                ))}
                {message.sources.length > 3 && (
                  <button className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                    View {message.sources.length - 3} more sources
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Quick Options */}
          {!isUser && message.quickOptions && message.quickOptions.length > 0 && (
            <div className="mt-4 pt-3 border-t border-neutral-200">
              <h4 className="text-sm font-medium text-neutral-700 mb-2">
                Quick Actions
              </h4>
              <div className="flex flex-wrap gap-2">
                {message.quickOptions.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => onQuickOptionClick?.(option)}
                    className="text-xs bg-primary-50 text-primary-700 px-3 py-1 rounded-full hover:bg-primary-100 transition-colors duration-200"
                  >
                    {option.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className={clsx(
            'text-xs mt-2 pt-2',
            isUser ? 'text-primary-200' : 'text-neutral-500'
          )}>
            {formatTimestamp(message.timestamp)}
          </div>
        </div>

        {/* Actions for assistant messages */}
        {!isUser && (
          <div className="flex items-center space-x-2 ml-3 mt-2">
            <button
              onClick={handleCopy}
              className="p-1 text-neutral-400 hover:text-neutral-600 transition-colors duration-200"
              title="Copy message"
            >
              <ClipboardDocumentIcon className="h-4 w-4" />
            </button>
            
            <button
              className="p-1 text-neutral-400 hover:text-neutral-600 transition-colors duration-200"
              title="Share message"
            >
              <ShareIcon className="h-4 w-4" />
            </button>

            <div className="flex items-center space-x-1 ml-2">
              <button
                onClick={() => handleFeedback(true)}
                className={clsx(
                  'p-1 transition-colors duration-200',
                  feedback === 'positive' 
                    ? 'text-accent-600' 
                    : 'text-neutral-400 hover:text-accent-600'
                )}
                title="Helpful"
              >
                {feedback === 'positive' ? (
                  <HandThumbUpSolidIcon className="h-4 w-4" />
                ) : (
                  <HandThumbUpIcon className="h-4 w-4" />
                )}
              </button>
              
              <button
                onClick={() => handleFeedback(false)}
                className={clsx(
                  'p-1 transition-colors duration-200',
                  feedback === 'negative' 
                    ? 'text-red-600' 
                    : 'text-neutral-400 hover:text-red-600'
                )}
                title="Not helpful"
              >
                {feedback === 'negative' ? (
                  <HandThumbDownSolidIcon className="h-4 w-4" />
                ) : (
                  <HandThumbDownIcon className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="h-8 w-8 bg-neutral-300 rounded-full flex items-center justify-center">
            <UserIcon className="h-5 w-5 text-neutral-600" />
          </div>
        </div>
      )}

      {/* Copy feedback */}
      {copied && (
        <div className="fixed top-4 right-4 bg-accent-600 text-white px-3 py-2 rounded-lg shadow-lg z-50 animate-fade-in">
          Message copied to clipboard!
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
