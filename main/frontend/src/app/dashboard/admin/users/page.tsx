'use client';

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  UserPlus, 
  Edit2, 
  Trash2, 
  Shield, 
  ShieldAlert, 
  Ban, 
  CheckCircle, 
  Key,
  X,
  Save,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { adminUserService } from '@/services/admin-user.service';
import { UserAdminResponse } from '@/types/api';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export default function UserManagementPage() {
  const [users, setUsers] = useState<UserAdminResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  
  // Modals state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isResetPwdModalOpen, setIsResetPwdModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  
  const [selectedUser, setSelectedUser] = useState<UserAdminResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form forms
  const [editForm, setEditForm] = useState({ full_name: '', is_active: true, is_admin: false });
  const [createForm, setCreateForm] = useState({ email: '', password: '', full_name: '', is_admin: false });
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    loadUsers();
  }, [page, pageSize]);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const data = await adminUserService.listUsers(page, pageSize, search);
      setUsers(data.users);
      setTotal(data.total);
    } catch (error) {
      toast.error('加载用户列表失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadUsers();
  };

  const openEditModal = (user: UserAdminResponse) => {
    setSelectedUser(user);
    setEditForm({
      full_name: user.full_name || '',
      is_active: user.is_active,
      is_admin: user.is_admin
    });
    setIsEditModalOpen(true);
  };

  const openResetPwdModal = (user: UserAdminResponse) => {
    setSelectedUser(user);
    setNewPassword('');
    setIsResetPwdModalOpen(true);
  };

  const openDeleteConfirm = (user: UserAdminResponse) => {
    setSelectedUser(user);
    setIsDeleteConfirmOpen(true);
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    setIsSubmitting(true);
    try {
      await adminUserService.updateUser(selectedUser.id, editForm);
      toast.success('用户信息更新成功');
      setIsEditModalOpen(false);
      loadUsers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '更新失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateUser = async () => {
    setIsSubmitting(true);
    try {
      await adminUserService.createUser(createForm);
      toast.success('用户创建成功');
      setIsCreateModalOpen(false);
      setCreateForm({ email: '', password: '', full_name: '', is_admin: false });
      loadUsers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '创建失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUser || !newPassword) return;
    setIsSubmitting(true);
    try {
      await adminUserService.resetPassword(selectedUser.id, newPassword);
      toast.success('密码重置成功');
      setIsResetPwdModalOpen(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '重置失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    setIsSubmitting(true);
    try {
      await adminUserService.deleteUser(selectedUser.id);
      toast.success('用户已删除');
      setIsDeleteConfirmOpen(false);
      loadUsers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '删除失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">用户管理</h1>
          <p className="text-gray-500 dark:text-gray-400">管理系统用户信息、权限及账号状态。</p>
        </div>
        <button 
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl flex items-center gap-2 transition-all shadow-sm active:scale-95 text-sm font-bold"
        >
          <UserPlus className="w-4 h-4" />
          新增用户
        </button>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-slate-700 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <form onSubmit={handleSearch} className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input 
              type="text" 
              placeholder="搜索邮箱或姓名..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-xl bg-gray-50 dark:bg-slate-900/50 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all dark:text-gray-100"
            />
          </form>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 font-bold uppercase">显示</span>
              <select 
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-lg px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-indigo-500 transition-all dark:text-gray-300"
              >
                <option value={10}>10 条/页</option>
                <option value={20}>20 条/页</option>
                <option value={50}>50 条/页</option>
                <option value={100}>100 条/页</option>
              </select>
            </div>
            
            <div className="flex items-center gap-2">
               <button 
                onClick={() => setPage(p => Math.max(1, p - 1))} 
                disabled={page === 1 || isLoading} 
                className="px-3 py-1.5 border border-gray-200 dark:border-slate-700 rounded-lg disabled:opacity-30 hover:bg-gray-50 dark:hover:bg-slate-700 text-xs font-bold transition-colors flex items-center gap-1 dark:text-gray-300"
              >
                上一页
              </button>
              <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 dark:bg-slate-900/50 rounded-lg border border-gray-100 dark:border-slate-700">
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">{page}</span>
                <span className="text-[10px] text-gray-400 font-medium">/ {Math.ceil(total / pageSize) || 1}</span>
              </div>
               <button 
                onClick={() => setPage(p => p + 1)} 
                disabled={page * pageSize >= total || isLoading} 
                className="px-3 py-1.5 border border-gray-200 dark:border-slate-700 rounded-lg disabled:opacity-30 hover:bg-gray-50 dark:hover:bg-slate-700 text-xs font-bold transition-colors flex items-center gap-1 dark:text-gray-300"
              >
                下一页
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-slate-900/50 text-gray-500 dark:text-gray-400 uppercase text-[10px] font-bold tracking-wider">
              <tr>
                <th className="px-6 py-4">用户信息</th>
                <th className="px-6 py-4">角色</th>
                <th className="px-6 py-4">状态</th>
                <th className="px-6 py-4">创建时间</th>
                <th className="px-6 py-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-slate-700/50">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
                    <span className="text-gray-400">正在获取用户数据...</span>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-10 text-center text-gray-400">未找到匹配的用户</td>
                </tr>
              ) : (
                users.map(user => (
                  <tr key={user.id} className="hover:bg-gray-50/50 dark:hover:bg-slate-700/20 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="font-bold text-gray-900 dark:text-white uppercase tracking-tight">{user.full_name || '未命名'}</span>
                        <span className="text-xs text-gray-400 font-mono">{user.email}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {user.is_admin ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-[10px] font-bold uppercase ring-1 ring-inset ring-indigo-500/20">
                          <Shield className="w-3 h-3" />
                          管理员
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px] font-bold uppercase ring-1 ring-inset ring-slate-400/20">
                          <Users className="w-3 h-3" />
                          用户
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5">
                        <div className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                        <span className={`text-[11px] font-medium ${user.is_active ? 'text-emerald-600' : 'text-gray-400'}`}>
                          {user.is_active ? '激活' : '禁用'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-500 dark:text-gray-400 text-xs font-mono">
                      {format(new Date(user.created_at), 'yyyy-MM-dd', { locale: zhCN })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => openEditModal(user)} title="编辑" className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button onClick={() => openResetPwdModal(user)} title="重置密码" className="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors">
                          <Key className="w-4 h-4" />
                        </button>
                        <button onClick={() => openDeleteConfirm(user)} title="删除" className="p-1.5 text-gray-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-900/20 rounded-lg transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modals are simplified for the sake of presentation, using conditional rendering */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-indigo-500" />
                新增系统用户
              </h3>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">邮箱地址</label>
                <input 
                  type="email" 
                  value={createForm.email}
                  onChange={e => setCreateForm({...createForm, email: e.target.value})}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm dark:text-white"
                  placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">初始密码</label>
                <input 
                  type="password" 
                  value={createForm.password}
                  onChange={e => setCreateForm({...createForm, password: e.target.value})}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm dark:text-white"
                  placeholder="******"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">全名/昵称</label>
                <input 
                  type="text" 
                  value={createForm.full_name}
                  onChange={e => setCreateForm({...createForm, full_name: e.target.value})}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm dark:text-white"
                />
              </div>
              <div className="flex items-center gap-2 pt-2">
                <input 
                  type="checkbox" 
                  id="create-is-admin"
                  className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  checked={createForm.is_admin}
                  onChange={e => setCreateForm({...createForm, is_admin: e.target.checked})}
                />
                <label htmlFor="create-is-admin" className="text-sm font-medium cursor-pointer text-gray-700 dark:text-gray-300">设为管理员</label>
              </div>
            </div>
            <div className="px-6 py-4 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-100 dark:border-slate-700 flex justify-end gap-3 text-sm">
              <button onClick={() => setIsCreateModalOpen(false)} className="px-4 py-2 text-gray-500 font-bold">取消</button>
              <button 
                onClick={handleCreateUser}
                disabled={isSubmitting || !createForm.email || !createForm.password}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                创建用户
              </button>
            </div>
          </div>
        </div>
      )}

      {isEditModalOpen && selectedUser && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-indigo-500" />
                修改用户信息
              </h3>
              <button onClick={() => setIsEditModalOpen(false)} className="text-gray-400 hover:text-gray-600 transition-colors"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">电子邮箱</label>
                <div className="px-4 py-2.5 bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-gray-500 text-sm font-mono">{selectedUser.email}</div>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-gray-500 uppercase mb-1">全名/昵称</label>
                <input 
                  type="text" 
                  value={editForm.full_name}
                  onChange={e => setEditForm({...editForm, full_name: e.target.value})}
                  className="w-full px-4 py-2.5 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-indigo-500 text-sm dark:text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    id="edit-is-admin"
                    className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={editForm.is_admin}
                    onChange={e => setEditForm({...editForm, is_admin: e.target.checked})}
                  />
                  <label htmlFor="edit-is-admin" className="text-sm font-medium cursor-pointer text-gray-700 dark:text-gray-300">管理员权限</label>
                </div>
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    id="edit-is-active"
                    className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={editForm.is_active}
                    onChange={e => setEditForm({...editForm, is_active: e.target.checked})}
                  />
                  <label htmlFor="edit-is-active" className="text-sm font-medium cursor-pointer text-gray-700 dark:text-gray-300">账号生效中</label>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-100 dark:border-slate-700 flex justify-end gap-3 text-sm">
              <button onClick={() => setIsEditModalOpen(false)} className="px-4 py-2 text-gray-500 font-bold">取消</button>
              <button 
                onClick={handleUpdateUser}
                disabled={isSubmitting}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                保存修改
              </button>
            </div>
          </div>
        </div>
      )}

      {isResetPwdModalOpen && selectedUser && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-sm rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95">
            <div className="p-6 space-y-4">
               <div className="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded-2xl flex items-center justify-center mx-auto mb-2">
                <Key className="w-6 h-6" />
              </div>
              <div className="text-center">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">重置登录密码</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  正在为 <b>{selectedUser.email}</b> 设置新密码
                </p>
              </div>
              
              <div>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-900/50 border border-gray-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-amber-500 text-center text-sm font-mono dark:text-white"
                  placeholder="输入新密码"
                  autoFocus
                />
              </div>
              
              <div className="flex gap-3 pt-2">
                <button onClick={() => setIsResetPwdModalOpen(false)} className="flex-1 py-2.5 text-gray-500 text-sm font-bold bg-gray-100 dark:bg-slate-800 rounded-xl">取消</button>
                <button 
                  onClick={handleResetPassword}
                  disabled={isSubmitting || !newPassword}
                  className="flex-1 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                >
                  确认重置
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isDeleteConfirmOpen && selectedUser && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-800 w-full max-w-sm rounded-2xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4">
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">危险操作：删除用户</h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 leading-relaxed">
                确定要彻底删除用户 <b>{selectedUser.email}</b> 吗？<br/>
                此操作将导致该用户的所有资源被永久清空。
              </p>
              <div className="flex gap-3">
                <button onClick={() => setIsDeleteConfirmOpen(false)} className="flex-1 py-2.5 text-gray-500 text-sm font-bold bg-gray-100 dark:bg-slate-800 rounded-xl">放弃</button>
                <button 
                  onClick={handleDeleteUser}
                  disabled={isSubmitting}
                  className="flex-1 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                >
                  核心确认
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
