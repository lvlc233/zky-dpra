import request from '@/lib/request';
import { AuthResponse } from '@/types/api';
import { User } from '@/types/models';

const mapUser = (user: User & Record<string, unknown>): User => {
  const mappedId = (user as { user_id?: string }).user_id ?? user.id;
  return {
    ...user,
    id: mappedId,
  };
};

export const authService = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const data = await request.post('/auth/login', { email, password });
    const response = data as AuthResponse & Record<string, unknown> & User;
    if (response.user) {
      return { ...response, user: mapUser(response.user as User) };
    }

    return {
      access_token: response.access_token,
      token_type: (response as { token_type?: string }).token_type ?? 'Bearer',
      user: mapUser(response),
    };
  },

  register: async (email: string, password: string, fullName?: string): Promise<User> => {
    const data = await request.post('/auth/register', { email, password, full_name: fullName });
    return mapUser(data as User);
  },

  getCurrentUser: async (): Promise<User> => {
    const data = await request.get('/users/me');
    return mapUser(data as User);
  },

  updateSettings: async (settings: any): Promise<any> => {
    return request.put('/users/settings', { settings });
  }
};
