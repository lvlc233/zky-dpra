import request from '@/lib/request';
import { UserAdminListResponse, UserAdminResponse } from '@/types/api';

export const adminUserService = {
  /**
   * 获取用户列表 (分页 + 搜索)
   */
  listUsers: async (page: number = 1, size: number = 20, search?: string): Promise<UserAdminListResponse> => {
    const params: any = { page, size };
    if (search) params.search = search;
    const res = await request.get<any>('/admin/users', { params });
    return res;
  },

  /**
   * 创建用户
   */
  createUser: async (data: any): Promise<UserAdminResponse> => {
    return request.post('/admin/users', data);
  },

  /**
   * 更新用户 (全名, 状态, 管理员标识)
   */
  updateUser: async (userId: string, data: any): Promise<UserAdminResponse> => {
    return request.patch(`/admin/users/${userId}`, data);
  },

  /**
   * 重置密码
   */
  resetPassword: async (userId: string, newPassword: string): Promise<boolean> => {
    return request.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword });
  },

  /**
   * 删除用户
   */
  deleteUser: async (userId: string): Promise<boolean> => {
    return request.delete(`/admin/users/${userId}`);
  }
};
