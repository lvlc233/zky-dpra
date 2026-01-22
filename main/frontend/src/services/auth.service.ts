import request from '@/lib/request';
import { LoginResponse, TokenPairResponse } from '@/types/api';
import { User } from '@/types/models';

export const authService = {
  login: async (email: string, password: string, rememberMe: boolean = false): Promise<LoginResponse> => {
    return request.post('/auth/login', { email, password, remember_me: rememberMe });
  },

  register: async (email: string, password: string, fullName: string): Promise<User> => {
    return request.post('/auth/register', { email, password, full_name: fullName });
  },

  refreshToken: async (refreshToken: string): Promise<TokenPairResponse> => {
    return request.get('/auth/refresh', { params: { refresh_token: refreshToken } });
  },

  getCurrentUser: async (): Promise<User> => {
    return request.get('/users/me');
  },

  validateToken: async (): Promise<boolean> => {
    try {
      // 使用 me 接口作为 Token 验证手段
      await request.get('/users/me');
      return true;
    } catch (error) {
      return false;
    }
  }
};
