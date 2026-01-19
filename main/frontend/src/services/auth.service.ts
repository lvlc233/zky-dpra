import request from '@/lib/request';
import { AuthResponse } from '@/types/api';
import { User } from '@/types/models';

export const authService = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    return request.post('/auth/login', { email, password });
  },

  register: async (email: string, password: string, fullName?: string): Promise<User> => {
    return request.post('/auth/register', { email, password, full_name: fullName });
  },

  getCurrentUser: async (): Promise<User> => {
    return request.get('/users/me');
  },

  updateSettings: async (settings: any): Promise<any> => {
    return request.put('/users/settings', { settings });
  }
};
