import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';

export function useAuth() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, login, logout, refreshToken } = useAuthStore();

  // Token refresh on mount
  useEffect(() => {
    if (isAuthenticated) {
      refreshToken();
    }
  }, [isAuthenticated, refreshToken]);

  const signIn = async (email: string, password: string) => {
    try {
      await login({ email, password });
      router.push('/');
    } catch (error) {
      // Error is handled in the store
      throw error;
    }
  };

  const signOut = () => {
    logout();
    router.push('/login');
  };

  const requireAuth = () => {
    if (!isAuthenticated && !pathname?.startsWith('/login') && !pathname?.startsWith('/register')) {
      router.push('/login');
    }
  };

  return {
    user,
    isAuthenticated,
    signIn,
    signOut,
    requireAuth,
  };
}