'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { BookOpen, Search, Upload, Bookmark, LogIn, LogOut, User as UserIcon, Shield } from 'lucide-react';
import { useAuthModal } from '@/components/auth/AuthModalContext';
import { useAuthStore } from '@/store/use-auth-store';
import { useUploadStore } from '@/store/upload.store';
import { toast } from 'sonner';

interface NavbarProps {
  className?: string;
  onCollectionsClick?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ className, onCollectionsClick }) => {
  const { openAuthModal } = useAuthModal();
  const { user, isAuthenticated, logout } = useAuthStore();
  const uploadStore = useUploadStore();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleUploadClick = () => {
    uploadStore.open();
  };

  const handleLogout = () => {
    logout();
    toast.success('已退出登录');
  };

  return (
    <header className={cn(
      "w-full h-16 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between px-6 lg:px-12 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 transition-all duration-300 relative", 
      className
    )}>
      {/* Logo Area */}
      <Link href="/" className="flex items-center gap-3 group z-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200 dark:shadow-indigo-900 group-hover:shadow-indigo-300 transition-all duration-300 group-hover:scale-105">
          <BookOpen className="w-5 h-5" />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-gray-100 dark:to-gray-400">
          DeepPaper
        </span>
      </Link>

      {/* Navigation Links - Centered Group */}
      <nav className="hidden md:flex items-center gap-2 p-1 bg-gray-100/50 dark:bg-slate-800/50 rounded-full border border-gray-200/50 dark:border-slate-700/50 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {/* <NavItem href="/dashboard" icon={<Search className="w-4 h-4" />}>搜索论文</NavItem> */}
        <NavItem 
          onClick={handleUploadClick}
          icon={<Upload className="w-4 h-4" />}
        >
          上传论文
        </NavItem>
        <NavItem 
          href={onCollectionsClick ? undefined : "/dashboard"} 
          onClick={onCollectionsClick}
          icon={<Bookmark className="w-4 h-4" />}
        >
          收藏夹
        </NavItem>
        {user?.email === 'admin@drap.com' && (
          <NavItem 
            href="/dashboard/admin" 
            icon={<Shield className="w-4 h-4" />}
          >
            管理员控制台
          </NavItem>
        )}
      </nav>

      {/* Auth Action */}
      <div className="flex-shrink-0 z-10">
        {!mounted ? (
          // Skeleton / Placeholder to prevent hydration mismatch
          <div className="w-24 h-10 rounded-full bg-gray-100 dark:bg-slate-800 animate-pulse" />
        ) : isAuthenticated && user ? (
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center text-indigo-600 dark:text-indigo-300 font-bold overflow-hidden">
                  {user.full_name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
                </div>
                <span className="hidden sm:inline max-w-[150px] truncate">{user.full_name || user.email}</span>
             </div>
             <button 
               onClick={handleLogout}
               className="flex items-center gap-2 px-3 py-2 rounded-full text-gray-500 hover:text-red-600 hover:bg-red-50 dark:text-gray-400 dark:hover:text-red-400 dark:hover:bg-red-900/20 transition-all duration-200"
               title="退出登录"
             >
               <LogOut className="w-4 h-4" />
             </button>
          </div>
        ) : (
          <button 
            onClick={() => openAuthModal('login')}
            className="flex items-center gap-2 h-10 px-6 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-all duration-300 shadow-md hover:shadow-lg active:scale-95"
          >
            <LogIn className="w-4 h-4" />
            <span>登录</span>
          </button>
        )}
      </div>
    </header>
  );
};

const NavItem = ({ href, children, icon, onClick }: { href?: string; children: React.ReactNode; icon?: React.ReactNode; onClick?: () => void }) => {
  if (onClick) {
    return (
      <button 
        onClick={onClick}
        className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-slate-700 hover:shadow-sm transition-all duration-200"
      >
        {icon}
        <span>{children}</span>
      </button>
    );
  }

  return (
    <Link 
      href={href || '#'}
      className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-slate-700 hover:shadow-sm transition-all duration-200"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
