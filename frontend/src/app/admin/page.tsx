'use client';

import React from 'react'; // Removed useState, useEffect
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation'; // For potential redirect if not admin though middleware should handle

// No longer need User interface or fetch/delete logic here

type UserWithRole = { role?: string };

export default function AdminPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  // Basic loading and auth check, middleware should be primary guard
  if (status === 'loading') {
    return (
      <div className="container mx-auto py-8 text-center">
        Loading admin dashboard...
      </div>
    );
  }

  if (status === 'unauthenticated') {
    router.push('/auth/signin');
    return (
      <div className="container mx-auto py-8 text-center">
        Redirecting to signin...
      </div>
    ); // Fallback message
  }

  if ((session?.user as UserWithRole)?.role !== 'admin') {
    // This case should ideally be handled by middleware redirecting to an error page or home
    // For now, show access denied, or redirect to an appropriate page
    // router.push('/auth/error?error=AccessDenied');
    return (
      <div className="container mx-auto py-8 text-center text-red-500">
        Access Denied. You do not have admin privileges.
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>
      <p className="mb-4">
        Welcome,{' '}
        <span className="font-semibold">{session?.user?.name || 'Admin'}</span>!
        Your role is:{' '}
        <span className="font-semibold">
          {(session?.user as UserWithRole)?.role}
        </span>
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <Link
          href="/admin/users"
          className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700"
        >
          <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            Manage Users
          </h5>
          <p className="font-normal text-gray-700 dark:text-gray-400">
            View, edit, and delete user accounts.
          </p>
        </Link>
        <Link
          href="/admin/teams"
          className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700"
        >
          <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            Manage Teams
          </h5>
          <p className="font-normal text-gray-700 dark:text-gray-400">
            View, edit, and delete teams.
          </p>
        </Link>
        <Link
          href="/admin/projects"
          className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:hover:bg-gray-700"
        >
          <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
            Manage Projects
          </h5>
          <p className="font-normal text-gray-700 dark:text-gray-400">
            View, edit, and delete projects.
          </p>
        </Link>
        {/* Add Manage Judges card here once ready */}
      </div>

      {/* User Management Table and its logic have been moved to /admin/users/page.tsx */}
      {/* Success/Error messages specific to user table are also moved */}
    </div>
  );
}
