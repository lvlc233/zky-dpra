'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuthStore } from '@/store/use-auth-store';
import { useRouter, usePathname } from 'next/navigation';
import { logger } from '@/lib/logger';
import { authService } from '@/services/auth.service';
import { useTheme } from '@/components/providers/ThemeProvider';
import { SystemSettings } from '@/types/settings';

interface AuthContextType {
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { login, logout, isAuthenticated, token } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();
  const { setTheme } = useTheme();

  // 1. 监听全局 401 事件
  useEffect(() => {
    const handleUnauthorized = () => {
      logger.warn('Received auth:unauthorized event, logging out', null, 'AuthProvider');
      logout();
      // 可以选择跳转到登录页，或者打开登录模态框
      // router.push('/login'); 
      // 或者不做跳转，只是状态变更，由 UI 反应
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [logout, router]);

  // 2. 初始化检查
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      
      if (storedToken) {
        try {
          // 尝试获取最新的用户信息
          const user = await authService.getCurrentUser();
          login(user, storedToken);
          
          // 如果用户信息中有设置，应用系统主题
          if (user.settings && user.settings.system_settings) {
            const systemSettings = user.settings.system_settings as SystemSettings;
            if (systemSettings.system_colour) {
              setTheme(systemSettings.system_colour);
            }
          }
        } catch (error) {
          logger.warn('Failed to fetch current user with existing token, logging out', error, 'AuthProvider');
          logout();
        }
      } else {
        if (isAuthenticated) {
            logger.warn('State authenticated but no token in localStorage, logging out', null, 'AuthProvider');
            logout();
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, [logout, setTheme]); // Removed isAuthenticated dependency to avoid loop if login updates it

  // 3. 处理 hydration 完成后的状态日志
  useEffect(() => {
    if (!isLoading) {
        logger.debug('Auth State Updated', { isAuthenticated, hasToken: !!token }, 'AuthProvider');
    }
  }, [isAuthenticated, token, isLoading]);

  return (
    <AuthContext.Provider value={{ isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
