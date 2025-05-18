'use client';

import Link from 'next/link';
import { useSession, signIn, signOut } from 'next-auth/react';

export default function Navbar() {
  const { data: session, status } = useSession();

  return (
    <nav className="bg-slate-800 text-white p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-xl font-bold hover:text-slate-300 transition-colors">
          HackathonPlatform
        </Link>
        <div className="flex items-center space-x-4">
          {status === 'loading' && (
            <p className="text-sm">Loading...</p>
          )}
          {status === 'unauthenticated' && (
            <button
              onClick={() => signIn()} // Redirects to /api/auth/signin by default
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md transition-colors text-sm font-medium"
            >
              Sign In
            </button>
          )}
          {status === 'authenticated' && session?.user && (
            <>
              <span className="text-sm">Welcome, {session.user.name || session.user.email}</span>
              <button
                onClick={() => signOut()} // Redirects to homepage after sign out by default
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors text-sm font-medium"
              >
                Sign Out
              </button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
} 