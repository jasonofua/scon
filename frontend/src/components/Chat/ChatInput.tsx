import React, { useState, useRef, useEffect } from 'react';
import { 
  PaperAirplaneIcon,
  PaperClipIcon,
  MicrophoneIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  isLoading?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "Ask me anything about Nigerian law...",
  isLoading = false
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleVoiceRecording = () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false);
      // TODO: Implement speech-to-text
    } else {
      // Start recording
      setIsRecording(true);
      // TODO: Implement speech-to-text
    }
  };

  const suggestedQuestions = [
    "What are the fundamental rights in Nigeria?",
    "How do I file an appeal to the Supreme Court?",
    "What is the procedure for constitutional interpretation?",
    "Tell me about landmark constitutional cases"
  ];

  return (
    <div className="border-t border-neutral-200 bg-white">
      {/* Suggested Questions (show when input is empty) */}
      {!message && !isLoading && (
        <div className="px-4 py-3 border-b border-neutral-100">
          <p className="text-sm text-neutral-600 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setMessage(question)}
                className="text-xs bg-neutral-100 text-neutral-700 px-3 py-1 rounded-full hover:bg-neutral-200 transition-colors duration-200"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4">
        <div className="flex items-end space-x-3">
          {/* Attachment button */}
          <button
            type="button"
            className="flex-shrink-0 p-2 text-neutral-400 hover:text-neutral-600 transition-colors duration-200"
            title="Attach file"
          >
            <PaperClipIcon className="h-5 w-5" />
          </button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || isLoading}
              rows={1}
              className={clsx(
                'w-full resize-none rounded-lg border border-neutral-300 px-4 py-3 pr-12',
                'focus:border-primary-500 focus:ring-primary-500 transition-colors duration-200',
                'placeholder-neutral-500 text-neutral-900',
                'max-h-32 overflow-y-auto custom-scrollbar',
                disabled || isLoading ? 'bg-neutral-100 cursor-not-allowed' : 'bg-white'
              )}
              style={{ minHeight: '48px' }}
            />
            
            {/* Character count */}
            {message.length > 0 && (
              <div className="absolute bottom-1 right-1 text-xs text-neutral-400">
                {message.length}/2000
              </div>
            )}
          </div>

          {/* Voice recording button */}
          <button
            type="button"
            onClick={handleVoiceRecording}
            className={clsx(
              'flex-shrink-0 p-2 transition-colors duration-200',
              isRecording 
                ? 'text-red-600 hover:text-red-700' 
                : 'text-neutral-400 hover:text-neutral-600'
            )}
            title={isRecording ? "Stop recording" : "Voice input"}
          >
            {isRecording ? (
              <StopIcon className="h-5 w-5" />
            ) : (
              <MicrophoneIcon className="h-5 w-5" />
            )}
          </button>

          {/* Send button */}
          <button
            type="submit"
            disabled={!message.trim() || disabled || isLoading}
            className={clsx(
              'flex-shrink-0 p-2 rounded-lg transition-all duration-200',
              message.trim() && !disabled && !isLoading
                ? 'bg-primary-600 text-white hover:bg-primary-700 shadow-soft'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
            )}
            title="Send message"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center justify-center mt-3 text-sm text-neutral-600">
            <div className="typing-indicator mr-2">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
            SCONIA is thinking...
          </div>
        )}

        {/* Input hints */}
        <div className="mt-2 text-xs text-neutral-500 flex items-center justify-between">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>Powered by OpenAI & Qdrant</span>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
