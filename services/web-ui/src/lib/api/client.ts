import { useAuthStore } from '@/stores/auth-store';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

class ApiClient {
  private baseURL: string;
  
  constructor(baseURL: string = '') {
    this.baseURL = baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
  }
  
  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers, ...fetchOptions } = options;
    
    // URL 생성
    const url = new URL(`${this.baseURL}${endpoint}`);
    if (params) {
      Object.keys(params).forEach(key => 
        url.searchParams.append(key, params[key])
      );
    }
    
    // 헤더 설정
    const token = useAuthStore.getState().token;
    const requestHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...headers,
    };
    
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
    
    try {
      const response = await fetch(url.toString(), {
        ...fetchOptions,
        headers: requestHeaders,
      });
      
      // 401 에러 처리
      if (response.status === 401) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }
      
      // 에러 응답 처리
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `HTTP error! status: ${response.status}`);
      }
      
      // 204 No Content 처리
      if (response.status === 204) {
        return {} as T;
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
  
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', params });
  }
  
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// API 인스턴스 생성
export const apiClient = new ApiClient();

// 특정 서비스별 클라이언트
export const authApi = new ApiClient(process.env.NEXT_PUBLIC_AUTH_API_URL);
export const dataApi = new ApiClient(process.env.NEXT_PUBLIC_DATA_API_URL);
export const graphApi = new ApiClient(process.env.NEXT_PUBLIC_GRAPH_API_URL);