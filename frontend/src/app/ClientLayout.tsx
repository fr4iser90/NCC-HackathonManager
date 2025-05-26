'use client';
import AuthProvider from '@/components/AuthProvider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SessionManager from '@/components/SessionManager';
import Navbar from '@/components/Navbar';
import { ReactNode } from 'react';

export default function ClientLayout({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient();
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <SessionManager />
        <Navbar />
        <main className="flex-grow container mx-auto p-4">{children}</main>
      </QueryClientProvider>
    </AuthProvider>
  );
}
