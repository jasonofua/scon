import axios from 'axios';
import type { AxiosResponse } from 'axios';
import type { ChatRequest, ChatResponse, SearchResponse, ApiError } from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_VERSION = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    const apiError: ApiError = {
      message: error.response?.data?.detail || error.message || 'An error occurred',
      status_code: error.response?.status || 500,
      request_id: error.response?.data?.request_id,
    };
    return Promise.reject(apiError);
  }
);

// API Service Class
export class ApiService {
  // Health Check
  static async healthCheck(): Promise<any> {
    const response = await api.get('/health');
    return response.data;
  }

  // Chat API
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/chat/', request);
    return response.data;
  }

  // Search API
  static async semanticSearch(
    query: string,
    limit: number = 10,
    documentTypes?: string[]
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
    });
    
    if (documentTypes && documentTypes.length > 0) {
      documentTypes.forEach(type => params.append('document_types', type));
    }

    const response = await api.get(`/search/semantic?${params}`);
    return response.data;
  }

  // Document Management (requires auth)
  static async uploadDocument(
    file: File,
    documentType: string,
    processImmediately: boolean = true
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    formData.append('process_immediately', processImmediately.toString());

    const response = await api.post('/admin/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Session Management
  static async getChatHistory(sessionId: string): Promise<any> {
    const response = await api.get(`/chat/history/${sessionId}`);
    return response.data;
  }

  static async getChatSessions(): Promise<any> {
    const response = await api.get('/chat/sessions');
    return response.data;
  }

  // Feedback
  static async submitFeedback(
    sessionId: string,
    queryId?: number,
    rating?: number,
    feedbackText?: string,
    feedbackType?: string
  ): Promise<any> {
    const response = await api.post('/chat/feedback', {
      session_id: sessionId,
      query_id: queryId,
      rating,
      feedback_text: feedbackText,
      feedback_type: feedbackType,
    });
    return response.data;
  }

  // System Status (admin)
  static async getSystemStatus(): Promise<any> {
    const response = await api.get('/admin/system/status');
    return response.data;
  }

  // Constitution API - Updated to use real uploaded documents
  static async getConstitutionalProvisions(
    chapter?: string,
    section?: string,
    keyword?: string,
    limit: number = 50
  ): Promise<any> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    if (chapter) params.append('chapter', chapter);
    if (section) params.append('section', section);
    if (keyword) params.append('keyword', keyword);

    const response = await api.get(`/documents/constitution?${params}`);
    return response.data;
  }

  static async getConstitutionChapters(): Promise<any> {
    const response = await api.get('/constitution/chapters');
    return response.data;
  }

  static async getConstitutionSection(sectionNumber: string, subsection?: string): Promise<any> {
    const params = new URLSearchParams();
    if (subsection) params.append('subsection', subsection);

    const response = await api.get(`/constitution/section/${sectionNumber}?${params}`);
    return response.data;
  }

  static async getFundamentalRights(): Promise<any> {
    const response = await api.get('/constitution/fundamental-rights');
    return response.data;
  }

  static async searchConstitution(query: string, limit: number = 10): Promise<any> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
    });

    const response = await api.get(`/constitution/search?${params}`);
    return response.data;
  }

  static async getConstitutionStats(): Promise<any> {
    const response = await api.get('/constitution/stats');
    return response.data;
  }

  // Cases API - Updated to use real uploaded documents
  static async getCases(
    year?: number,
    _status?: string,
    search?: string,
    limit: number = 50,
    _offset: number = 0
  ): Promise<any> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    if (year) params.append('year', year.toString());
    if (search) params.append('search', search);

    const response = await api.get(`/documents/cases?${params}`);
    return response.data;
  }

  static async getCase(caseId: string): Promise<any> {
    const response = await api.get(`/cases/${caseId}`);
    return response.data;
  }

  static async getLandmarkCases(): Promise<any> {
    // Use recent judgments as landmark cases since /cases/landmark doesn't exist
    const response = await api.get('/cases/recent/judgments?limit=10');
    return response.data;
  }

  static async getCaseStats(): Promise<any> {
    // Get available years and calculate stats from that since /cases/stats doesn't exist
    try {
      const yearsResponse = await api.get('/cases/years/available');
      const casesResponse = await api.get('/cases/?limit=100');

      const years = yearsResponse.data.available_years || [];
      const cases = casesResponse.data.cases || [];

      return {
        total_cases: cases.length,
        cases_this_year: cases.filter((c: any) =>
          c.judgment_date && new Date(c.judgment_date).getFullYear() === new Date().getFullYear()
        ).length,
        decided_cases: cases.filter((c: any) => c.case_status === 'decided').length,
        pending_cases: cases.filter((c: any) => c.case_status === 'pending').length,
        available_years: years
      };
    } catch (error) {
      console.error('Error calculating case stats:', error);
      return {
        total_cases: 0,
        cases_this_year: 0,
        decided_cases: 0,
        pending_cases: 0,
        available_years: []
      };
    }
  }

  // Judges API - Updated to use real uploaded documents
  static async getJudges(
    status?: string,
    limit: number = 50
  ): Promise<any> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    if (status) {
      params.append('status', status);
    }

    const response = await api.get(`/documents/judges?${params}`);
    return response.data;
  }

  static async getJudge(judgeId: string): Promise<any> {
    const response = await api.get(`/judges/${judgeId}`);
    return response.data;
  }

  static async getChiefJustice(): Promise<any> {
    try {
      const response = await api.get('/judges/chief-justice');
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        // No chief justice found, return null
        return null;
      }
      throw error;
    }
  }

  static async getCourtHierarchy(): Promise<any> {
    // This endpoint doesn't exist yet, return null to indicate no data available
    // The real court hierarchy data is now available in nigeria_court_hierarchy_and_judges.txt
    return null;
  }

  // WebSocket connection helper
  static getWebSocketUrl(sessionId: string, userType: string = 'citizen'): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = API_BASE_URL.replace(/^https?:/, '');
    return `${wsProtocol}${wsHost}${API_VERSION}/chat/ws/${sessionId}?user_type=${userType}`;
  }
}

// Utility functions
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
};

export const formatTimestamp = (timestamp: string | Date): string => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  return date.toLocaleString();
};

export const truncateText = (text: string, maxLength: number = 100): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export default ApiService;
