// API Response Types
export interface ChatMessage {
  id: number;
  query: string;
  response: string;
  sources: Source[];
  timestamp: string;
  rating?: number;
  feedback?: string;
}

export interface Source {
  document_id: string;
  document_type: string;
  title: string;
  content_snippet: string;
  relevance_score: number;
  url?: string;
}

export interface QuickOption {
  text: string;
  action: string;
  category: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  quick_options: QuickOption[];
  confidence_score: number;
  session_id: string;
  query_id: number;
  response_time: number;
  intent_classification?: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  context?: string;
  user_type?: string;
}

export interface SearchResult {
  id: string;
  text: string;
  score: number;
  document_id: string;
  document_type: string;
  chunk_index: number;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_found: number;
}

// UI State Types
export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  quickOptions?: QuickOption[];
  isLoading?: boolean;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  title: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'citizen' | 'legal_professional' | 'student' | 'admin';
  avatar?: string;
}

// Document Types
export interface Document {
  id: string;
  title: string;
  type: 'constitution' | 'case' | 'procedure' | 'court_info';
  content: string;
  uploadedAt: Date;
  status: 'processing' | 'completed' | 'failed';
  metadata?: Record<string, any>;
}

// Navigation Types
export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  current: boolean;
  badge?: number;
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system';

// Error Types
export interface ApiError {
  message: string;
  status_code: number;
  request_id?: string;
}

// Speech Recognition Types (for Kiosk Mode)
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

export interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

export interface SpeechRecognitionResult {
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

export interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
