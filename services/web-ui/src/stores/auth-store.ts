import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthState, LoginCredentials, RegisterData } from '@/types/auth';
import { authService } from '@/services/auth.service';

interface AuthStore extends AuthState {
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  clearError: () => void;
}

// Mock user for development
const mockUser: User = {
  id: '1',
  email: 'admin@riskradar.ai',
  name: '관리자',
  company: 'RiskRadar',
  role: 'admin',
  createdAt: new Date().toISOString(),
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        
        try {
          // TODO: Replace with actual API call
          // Mock login logic
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          if (credentials.email === 'admin@riskradar.ai' && credentials.password === 'password') {
            const mockToken = 'mock-jwt-token-' + Date.now();
            set({
              user: mockUser,
              token: mockToken,
              isAuthenticated: true,
              isLoading: false,
            });
          } else {
            throw new Error('이메일 또는 비밀번호가 올바르지 않습니다.');
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '로그인 중 오류가 발생했습니다.',
            isLoading: false,
          });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });
        
        try {
          // TODO: Replace with actual API call
          // Mock register logic
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Simulate successful registration
          set({ isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '회원가입 중 오류가 발생했습니다.',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
        
        // Clear any stored tokens
        if (typeof window !== 'undefined') {
          localStorage.removeItem('token');
        }
      },

      refreshToken: async () => {
        const { token } = get();
        if (!token) return;
        
        try {
          // TODO: Implement token refresh logic
          // For now, just validate the existing token
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
          // If refresh fails, logout
          get().logout();
        }
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },

      setToken: (token: string | null) => {
        set({ token });
        if (token && typeof window !== 'undefined') {
          localStorage.setItem('token', token);
        }
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => {
        // Use localStorage for persistence
        if (typeof window !== 'undefined') {
          return localStorage;
        }
        // Fallback for SSR
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        };
      }),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);