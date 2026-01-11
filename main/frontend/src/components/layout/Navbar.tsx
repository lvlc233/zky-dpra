'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { BookOpen, Search, Upload, Bookmark, LogIn } from 'lucide-react';
import { useAuthModal } from '@/components/auth/AuthModalContext';

interface NavbarProps {
  className?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ className }) => {
  const { openAuthModal } = useAuthModal();

  return (
    <header className={cn(
      "w-full h-16 border-b border-gray-100 flex items-center justify-between px-6 lg:px-12 bg-white/80 backdrop-blur-md sticky top-0 z-50 transition-all duration-300 relative", 
      className
    )}>
      {/* Logo Area */}
      <Link href="/" className="flex items-center gap-3 group z-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200 group-hover:shadow-indigo-300 transition-all duration-300 group-hover:scale-105">
          <BookOpen className="w-5 h-5" />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
          DeepPaper
        </span>
      </Link>

      {/* Navigation Links - Centered Group */}
      <nav className="hidden md:flex items-center gap-2 p-1 bg-gray-100/50 rounded-full border border-gray-200/50 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <NavItem href="#" icon={<Search className="w-4 h-4" />}>搜索论文</NavItem>
        <NavItem href="#" icon={<Upload className="w-4 h-4" />}>上传论文</NavItem>
        <NavItem href="#" icon={<Bookmark className="w-4 h-4" />}>收藏夹</NavItem>
      </nav>

      {/* Auth Action */}
      <div className="flex-shrink-0 z-10">
        <button 
          onClick={() => openAuthModal('login')}
          className="flex items-center gap-2 h-10 px-6 rounded-full bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-all duration-300 shadow-md hover:shadow-lg active:scale-95"
        >
          <LogIn className="w-4 h-4" />
          <span>登录</span>
        </button>
      </div>
    </header>
  );
};

const NavItem = ({ href, children, icon }: { href: string; children: React.ReactNode; icon?: React.ReactNode }) => {
  return (
    <Link 
      href={href}
      className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white hover:shadow-sm transition-all duration-200"
    >
      {icon}
      <span>{children}</span>
    </Link>
  );
}
