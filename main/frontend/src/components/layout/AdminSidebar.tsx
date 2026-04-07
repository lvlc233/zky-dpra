'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Database,
  Users,
  Server,
  ChevronRight, 
  ChevronLeft, 
  Shield,
  Activity
} from 'lucide-react';

interface AdminSidebarProps {
  className?: string;
}

export const AdminSidebar: React.FC<AdminSidebarProps> = ({ 
  className
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const navItems = [
    {
      label: '系统监控',
      icon: <Activity className="w-4 h-4" />,
      href: '/dashboard/admin/monitoring',
      isActive: pathname === '/dashboard/admin/monitoring' || pathname === '/dashboard/admin',
    },
    {
      label: '搜索数据源配置',
      icon: <Database className="w-4 h-4" />,
      href: '/dashboard/admin/search-api',
      isActive: pathname === '/dashboard/admin/search-api',
    },
    {
      label: '用户管理',
      icon: <Users className="w-4 h-4" />,
      href: '/dashboard/admin/users',
      isActive: pathname === '/dashboard/admin/users',
    },
    {
      label: '模型与调度策略',
      icon: <Server className="w-4 h-4" />,
      href: '/dashboard/admin/models',
      isActive: pathname === '/dashboard/admin/models',
    }
  ];

  return (
    <aside 
      className={cn(
        "h-full bg-white dark:bg-slate-900 border-r border-gray-100 dark:border-slate-800 flex flex-col transition-all duration-300 relative z-20", 
        isCollapsed ? "w-20" : "w-72",
        className
      )}
    >
      {/* Toggle Button */}
      <button 
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 w-6 h-6 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-full flex items-center justify-center shadow-sm text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 z-50"
      >
        {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>

      {/* Header */}
      <div className={cn("p-4 border-b border-gray-50 dark:border-slate-800 flex items-center gap-3", isCollapsed && "justify-center")}>
        <div className="flex bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 p-2 rounded-xl">
          <Shield className="w-5 h-5 flex-shrink-0" />
        </div>
        {!isCollapsed && (
          <div className="flex flex-col">
            <h2 className="text-sm font-bold text-gray-900 dark:text-gray-100 truncate">控制面板</h2>
            <span className="text-[10px] text-gray-500 dark:text-gray-400">系统管理</span>
          </div>
        )}
      </div>

      {/* Middle Section: Nav */}
      <div className="flex-1 overflow-y-auto p-4">
        {!isCollapsed && <h3 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2 px-2">功能菜单</h3>}

        <div className="space-y-1">
          {navItems.map((item, index) => (
            <Link
              key={index}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 text-sm rounded-xl transition-all duration-200 relative",
                item.isActive
                  ? "bg-indigo-50 text-indigo-900 shadow-sm ring-1 ring-indigo-100 dark:bg-indigo-900/20 dark:text-indigo-300 dark:ring-indigo-800/30 font-medium" 
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-slate-800/50 dark:hover:text-gray-100",
                isCollapsed && "justify-center px-0"
              )}
            >
              <div className={cn(
                "flex-shrink-0 transition-colors", 
                item.isActive ? "text-indigo-600 dark:text-indigo-400" : "text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300"
              )}>
                {item.icon}
              </div>
              
              {!isCollapsed && (
                <span className="flex-1 truncate">{item.label}</span>
              )}
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
};
