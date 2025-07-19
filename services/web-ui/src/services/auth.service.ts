import { apiClient } from '@/lib/api/client';
import { User, LoginCredentials, RegisterData } from '@/types/auth';

interface LoginResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

interface RegisterResponse {
  message: string;
  userId?: string;
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    // TODO: 실제 API 엔드포인트로 변경
    return apiClient.post<LoginResponse>('/api/auth/login', credentials);
  }
  
  async register(data: RegisterData): Promise<RegisterResponse> {
    // TODO: 실제 API 엔드포인트로 변경
    return apiClient.post<RegisterResponse>('/api/auth/register', data);
  }
  
  async logout(): Promise<void> {
    // TODO: 실제 API 엔드포인트로 변경
    await apiClient.post('/api/auth/logout');
  }
  
  async refreshToken(refreshToken: string): Promise<{ token: string }> {
    // TODO: 실제 API 엔드포인트로 변경
    return apiClient.post<{ token: string }>('/api/auth/refresh', {
      refreshToken,
    });
  }
  
  async getCurrentUser(): Promise<User> {
    // TODO: 실제 API 엔드포인트로 변경
    return apiClient.get<User>('/api/auth/me');
  }
  
  async updateProfile(data: Partial<User>): Promise<User> {
    // TODO: 실제 API 엔드포인트로 변경
    return apiClient.patch<User>('/api/auth/profile', data);
  }
  
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    // TODO: 실제 API 엔드포인트로 변경
    await apiClient.post('/api/auth/change-password', {
      oldPassword,
      newPassword,
    });
  }
}

export const authService = new AuthService();