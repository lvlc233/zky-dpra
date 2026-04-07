'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Navbar } from "@/components/layout/Navbar";
import { AdminSidebar } from "@/components/layout/AdminSidebar";
import { useAuth } from '@/components/providers/AuthProvider';
import { useAuthStore } from '@/store/use-auth-store';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoading: authLoading } = useAuth();
  const { isAuthenticated, user } = useAuthStore();
  const router = useRouter();

  React.useEffect(() => {
    if (!authLoading && (!isAuthenticated || user?.email !== 'admin@drap.com')) {
      router.push('/login?redirect=' + encodeURIComponent(window.location.pathname));
    }
  }, [authLoading, isAuthenticated, user, router]);

  if (authLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 font-medium">正在验证权限...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || user?.email !== 'admin@drap.com') {
    return null; // Prevents flashing content while redirecting
  }

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-950 flex flex-col overflow-hidden transition-colors duration-300">
      <Navbar />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <AdminSidebar className="hidden md:flex" />

        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-slate-900/50 p-8 relative">
          <div className="max-w-7xl mx-auto space-y-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
