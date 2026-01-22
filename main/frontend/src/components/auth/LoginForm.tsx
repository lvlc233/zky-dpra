'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useAuthModal } from './AuthModalContext';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/use-auth-store';

interface LoginFormProps {
  className?: string;
  isModal?: boolean;
}

export const LoginForm: React.FC<LoginFormProps> = ({ className, isModal = false }) => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const { setAuthView, closeAuthModal } = useAuthModal();
  const login = useAuthStore((state) => state.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await authService.login(formData.email, formData.password, formData.rememberMe);
      login(response, response.access_token);
      toast.success('登录成功');
      
      if (isModal) {
        closeAuthModal();
      }
      
      // Navigate to dashboard and refresh server data
      router.push('/dashboard');
      router.refresh();
    } catch (error: any) {
      const errorMessage = error.message || '登录失败，请检查账号密码';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    
    // 如果 input 没有 name 属性，根据 type 推断 (为了兼容旧代码)
    // 但建议所有 input 都加上 name
    const fieldName = name || (type === 'email' ? 'email' : 'password');
    
    setFormData(prev => ({
      ...prev,
      [fieldName]: type === 'checkbox' ? checked : value
    }));
  };

  const handleRegisterClick = (e: React.MouseEvent) => {
    if (isModal) {
      e.preventDefault();
      setAuthView('register');
    }
  };

  const handleForgotPasswordClick = (e: React.MouseEvent) => {
    if (isModal) {
      e.preventDefault();
      setAuthView('forgot-password');
    }
  };

  return (
    <div className={cn("flex flex-col md:flex-row w-full max-w-4xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden", className)}>
      {/* Left: Image Area */}
      <div className="hidden md:flex md:w-1/2 bg-gray-900 relative p-12 flex-col justify-between">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 to-violet-900 opacity-90" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop')] bg-cover bg-center mix-blend-overlay opacity-50" />
        
        <div className="relative z-10">
          <h2 className="text-3xl font-bold text-white mb-4">开始您的科研之旅</h2>
          <p className="text-indigo-100 text-lg leading-relaxed">
            加入 DeepPaper，利用 AI 的力量加速论文阅读与知识发现。
          </p>
        </div>

        <div className="relative z-10 flex gap-2">
            <div className="w-12 h-1 bg-white/20 rounded-full" />
            <div className="w-4 h-1 bg-white/20 rounded-full" />
            <div className="w-4 h-1 bg-white/20 rounded-full" />
        </div>
      </div>

      {/* Right: Form Area */}
      <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center bg-white dark:bg-slate-900">
        <div className="mb-8 text-center md:text-left">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">欢迎回来</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm">请输入您的账号信息以继续</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 ml-1">邮箱地址</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input 
                type="email" 
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="name@example.com"
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:bg-white dark:focus:bg-slate-900 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 ml-1">密码</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
              <input 
                type="password"
                name="password" 
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:bg-white dark:focus:bg-slate-900 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all duration-200 outline-none"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                <input
                    type="checkbox"
                    id="rememberMe"
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleChange}
                    className="w-4 h-4 rounded border-gray-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500 cursor-pointer bg-white dark:bg-slate-800"
                />
                <label htmlFor="rememberMe" className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none">
                    记住我 <span className="text-xs text-gray-400 dark:text-gray-500 ml-0.5">[7天有效]</span>
                </label>
            </div>
            <div className="flex gap-4 text-xs">
                <Link 
                href="/register" 
                onClick={handleRegisterClick}
                className="text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors font-medium"
                >
                注册新账号
                </Link>
                <Link 
                href="/forgot-password" 
                onClick={handleForgotPasswordClick}
                className="text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors font-medium"
                >
                忘记密码？
                </Link>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full h-12 bg-gray-900 hover:bg-gray-800 dark:bg-white dark:text-slate-900 dark:hover:bg-gray-100 text-white rounded-xl font-medium shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-70 disabled:hover:translate-y-0"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <span>登录</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-gray-100 text-center">
          <p className="text-xs text-gray-400">
            登录即代表您同意我们的 <Link href="/terms" className="underline hover:text-gray-600">服务条款</Link> 和 <Link href="/privacy" className="underline hover:text-gray-600">隐私政策</Link>
          </p>
        </div>
      </div>
    </div>
  );
};
